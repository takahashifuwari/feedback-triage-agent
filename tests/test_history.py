import json
import unittest
from pathlib import Path

from history import filter_history


ROOT = Path(__file__).resolve().parents[1]


class FilterHistoryTest(unittest.TestCase):
    def test_only_strictly_earlier_candidates_are_kept(self):
        cutoff = "2026-02-07T05:39:17Z"
        earlier = {"issue_number": 1, "created_at": "2026-02-07T05:39:16Z"}
        same = {"issue_number": 2, "created_at": cutoff}
        later = {"issue_number": 3, "created_at": "2026-02-07T05:39:18Z"}

        self.assertEqual(filter_history([later, same, earlier], cutoff), [earlier])

    def test_offsets_are_compared_by_instant(self):
        cutoff = "2026-02-07T05:39:17Z"
        earlier = {"created_at": "2026-02-07T13:39:16+08:00"}
        same = {"created_at": "2026-02-07T13:39:17+08:00"}

        self.assertEqual(filter_history([same, earlier], cutoff), [earlier])

    def test_no_candidates_returns_empty_list(self):
        self.assertEqual(filter_history([], "2026-02-07T05:39:17Z"), [])

    def test_invalid_or_timezone_missing_timestamp_is_rejected(self):
        for value in ("2026-02-07T05:39:17", "not a timestamp"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                filter_history([{"created_at": value}], "2026-02-07T05:39:17Z")
        with self.assertRaises(ValueError):
            filter_history([], "2026-02-07T05:39:17")

    def test_public_replays_exclude_later_related_issues(self):
        candidates = json.loads(
            (ROOT / "data" / "seed_issues.json").read_text(encoding="utf-8")
        )
        queries = json.loads(
            (ROOT / "eval" / "dev_queries.json").read_text(encoding="utf-8")
        )
        by_id = {query["issue_number"]: query["created_at"] for query in queries}
        for query, older, later in (
            (293585, 288707, 303202),
            (237688, 227137, 239917),
        ):
            with self.subTest(query=query):
                visible = filter_history(candidates, by_id[query])
                numbers = {candidate["issue_number"] for candidate in visible}
                self.assertIn(older, numbers)
                self.assertNotIn(later, numbers)


if __name__ == "__main__":
    unittest.main()
