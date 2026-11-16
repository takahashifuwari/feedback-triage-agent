import unittest

from evaluate import load_json, predict, score, summarize


class FrozenHoldoutTest(unittest.TestCase):
    def test_offline_quality_does_not_regress(self):
        queries = load_json("eval/holdout_queries.json")
        history = load_json("data/seed_issues.json") + load_json("eval/holdout_history.json")
        expected = {row["issue_number"]: row for row in load_json("eval/holdout_expected.json")}
        cases = score(predict(queries, history, online=False), expected)
        metrics = summarize(cases)

        self.assertEqual(metrics["completed"], {"count": 12, "total": 12})
        self.assertEqual(metrics["reference_top1"], {"count": 4, "total": 4})
        self.assertEqual(metrics["false_links"], {"count": 0, "total": 8})
        self.assertGreaterEqual(metrics["action_accuracy"]["count"], 4)
