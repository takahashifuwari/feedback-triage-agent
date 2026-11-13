"""Select the historical candidates visible when a feedback was filed."""

import argparse
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar


Candidate = TypeVar("Candidate", bound=Mapping[str, object])
ROOT = Path(__file__).resolve().parent


def _parse_created_at(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("created_at must be a timestamp string with a timezone")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    timestamp = datetime.fromisoformat(value)
    if timestamp.utcoffset() is None:
        raise ValueError("created_at must include a timezone")
    return timestamp.astimezone(timezone.utc)


def filter_history(
    candidates: Iterable[Candidate], feedback_created_at: str
) -> list[Candidate]:
    """Return earlier candidates in their input order."""
    cutoff = _parse_created_at(feedback_created_at)
    return [
        candidate
        for candidate in candidates
        if _parse_created_at(candidate["created_at"]) < cutoff
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_number", type=int, help="issue number from dev_queries.json")
    args = parser.parse_args()

    queries = json.loads((ROOT / "eval" / "dev_queries.json").read_text(encoding="utf-8"))
    query = next(
        (record for record in queries if record["issue_number"] == args.issue_number),
        None,
    )
    if query is None:
        parser.error(f"no development feedback found for #{args.issue_number}")

    candidates = json.loads((ROOT / "data" / "seed_issues.json").read_text(encoding="utf-8"))
    visible = filter_history(candidates, query["created_at"])
    print(f"#{args.issue_number} ({query['created_at']}): {len(visible)}/{len(candidates)} eligible")
    for candidate in visible:
        print(f"#{candidate['issue_number']}  {candidate['source_url']}")


if __name__ == "__main__":
    main()
