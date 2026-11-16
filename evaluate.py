"""Replay the frozen holdout and score offline rules or Gemini decisions."""

import argparse
import json
import os
import sys
from pathlib import Path

from sklearn import __version__ as sklearn_version

from history import ROOT
from triage import retrieve, triage_feedback


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def predict(queries, candidates, online):
    predictions = []
    for index, feedback in enumerate(queries, 1):
        number = feedback["issue_number"]
        if online:
            print(f"[{index}/{len(queries)}] #{number}", file=sys.stderr, flush=True)
        try:
            result = triage_feedback(feedback, candidates, online=online)
            error = None
        except (RuntimeError, ValueError) as exc:
            result = {"matches": retrieve(feedback, candidates)}
            error = str(exc)
        predictions.append({
            "issue_number": number,
            "action": result.get("action"),
            "linked_issue_number": result.get("linked_issue_number"),
            "model": result.get("model"),
            "matches": [
                {"issue_number": ticket["issue_number"], "score": score}
                for ticket, score in result["matches"]
            ],
            "questions": result.get("questions", []),
            "evidence": result.get("evidence", []),
            "error": error,
        })
    return predictions


def score(predictions, expected):
    cases = []
    for prediction in predictions:
        answer = expected[prediction["issue_number"]]
        action = answer["expected_action"]
        target = answer["reference_duplicate_issue_number"]
        rank = next(
            (i for i, match in enumerate(prediction["matches"], 1) if match["issue_number"] == target),
            None,
        )
        if prediction["error"] is not None:
            failure = "execution"
        elif target is not None and rank is None:
            failure = "retrieval"
        elif prediction["action"] != action or prediction["linked_issue_number"] != target:
            failure = "decision"
        else:
            failure = None
        cases.append({
            **prediction,
            "expected_action": action,
            "reference_duplicate_issue_number": target,
            "reference_rank": rank,
            "reference_questions": answer["follow_up_questions"],
            "failure_stage": failure,
        })
    return cases


def tally(cases, condition):
    return {"count": sum(1 for case in cases if condition(case)), "total": len(cases)}


def summarize(cases):
    completed = [case for case in cases if case["error"] is None]
    references = [case for case in cases if case["reference_duplicate_issue_number"] is not None]
    links = [case for case in completed if case["expected_action"] == "link_existing"]
    other_actions = [case for case in completed if case["expected_action"] != "link_existing"]
    return {
        "completed": {"count": len(completed), "total": len(cases)},
        "action_accuracy": tally(completed, lambda case: case["action"] == case["expected_action"]),
        "reference_top1": tally(references, lambda case: case["reference_rank"] == 1),
        "reference_top3": tally(references, lambda case: case["reference_rank"] is not None),
        "correct_links": tally(links, lambda case: case["failure_stage"] is None),
        "false_links": tally(other_actions, lambda case: case["action"] == "link_existing"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="ask Gemini on each feedback")
    parser.add_argument("--output", type=Path, help="write the full JSON report here")
    args = parser.parse_args()
    if args.online and not os.getenv("GEMINI_API_KEY"):
        parser.error("set GEMINI_API_KEY before running --online")

    queries = load_json("eval/holdout_queries.json")
    candidates = load_json("data/seed_issues.json") + load_json("eval/holdout_history.json")
    predictions = predict(queries, candidates, args.online)
    expected = {row["issue_number"]: row for row in load_json("eval/holdout_expected.json")}
    cases = score(predictions, expected)
    report = {
        "mode": "gemini" if args.online else "offline",
        "python_version": sys.version.split()[0],
        "scikit_learn_version": sklearn_version,
        "history_size": len(candidates),
        "metrics": summarize(cases),
        "cases": cases,
    }
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(content + "\n", encoding="utf-8")
        print(json.dumps(report["metrics"], indent=2))
        print(f"Report: {args.output}")
    else:
        print(content)
    return int(any(case["error"] is not None for case in cases))


if __name__ == "__main__":
    raise SystemExit(main())
