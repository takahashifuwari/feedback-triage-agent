import subprocess
import sys
import unittest
from pathlib import Path

from triage import retrieve, validate_action


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


class OfflineDemoTest(unittest.TestCase):
    def test_main_case_runs_from_the_terminal(self):
        script = Path(__file__).resolve().parents[1] / "triage.py"
        output = subprocess.check_output([sys.executable, str(script), "293585"], text=True)

        self.assertIn("mode: offline", output)
        self.assertIn("#288707  ", output)
        self.assertIn("baseline: request_info", output)
        self.assertIn("validation: passed", output)

    def test_link_comes_from_a_retrieved_ticket(self):
        url = "https://github.com/microsoft/vscode/issues/288707"
        matches = [({"issue_number": 288707, "source_url": url}, 0.5)]
        self.assertEqual(validate_action("link_existing", 288707, matches), url)
        with self.assertRaises(ValueError):
            validate_action("link_existing", 293585, matches)

    def test_invalid_action_and_unexpected_reference_are_rejected(self):
        for action, link in (("unknown", None), ("request_info", 288707)):
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_action(action, link, [])
