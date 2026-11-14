import unittest

from triage import retrieve


class RetrievalTest(unittest.TestCase):
    def test_later_ticket_cannot_change_results_or_scores(self):
        query = {
            "created_at": "2026-02-02T00:00:00Z",
            "title": "Terminal repeats output",
            "symptom_summary": "Output lines repeat after resizing",
        }
        earlier = [
            dict(query, created_at="2026-02-01T00:00:00Z", title="Terminal resize"),
            dict(query, created_at="2026-02-01T00:00:00Z", title="Output display"),
        ]
        later = dict(query, created_at="2026-02-03T00:00:00Z")

        self.assertEqual(retrieve(query, earlier + [later]), retrieve(query, earlier))
