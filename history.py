"""Select the historical candidates visible when a feedback was filed."""

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _parse_created_at(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    return timestamp


def filter_history(candidates, feedback_created_at):
    """Return earlier candidates in their input order."""
    cutoff = _parse_created_at(feedback_created_at)
    return [row for row in candidates if _parse_created_at(row["created_at"]) < cutoff]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_number", type=int, help="issue number from dev_queries.json")
    issue_number = parser.parse_args().issue_number

    queries = json.loads((ROOT / "eval" / "dev_queries.json").read_text(encoding="utf-8"))
    query = next((row for row in queries if row["issue_number"] == issue_number), None)
    if query is None:
        parser.error(f"no development feedback found for #{issue_number}")

    candidates = json.loads((ROOT / "data" / "seed_issues.json").read_text(encoding="utf-8"))
    cutoff = query["created_at"]
    visible = filter_history(candidates, cutoff)
    print(f"#{issue_number} ({cutoff}): {len(visible)}/{len(candidates)} eligible")
    for candidate in visible:
        print(f"#{candidate['issue_number']}  {candidate['source_url']}")


if __name__ == "__main__":
    main()
