import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from triage import main


class ModelReviewTest(unittest.TestCase):
    def run_online(self, result, status="completed"):
        response = {
            "status": status,
            "model": "test-model",
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": json.dumps(result)},
            ]}],
        }
        output = io.StringIO()
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}),
            patch("sys.argv", ["triage.py", "293585", "--online"]),
            patch("model_review.urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as call,
            redirect_stdout(output),
        ):
            main()
        return output.getvalue(), json.loads(call.call_args.args[0].data)

    def test_model_questions_and_local_evidence_link(self):
        question = "Can you see the typed characters before pressing Enter?"
        result = {
            "action": "request_info",
            "linked_issue_number": None,
            "evidence": [{"issue_number": 288707, "observation": "Keystrokes are invisible."}],
            "follow_up_questions": [question],
        }
        output, payload = self.run_online(result)
        context = json.loads(payload["input"])
        tickets = [context["feedback"], *context["candidates"]]
        self.assertEqual(set(context), {"feedback", "candidates"})
        self.assertEqual([ticket["issue_number"] for ticket in tickets],
                         [293585, 288707, 285493, 224582])
        self.assertTrue(all("source_url" not in ticket for ticket in tickets))
        self.assertNotIn("expected_action", payload["input"])
        self.assertFalse(payload["store"])
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertEqual(payload["model"], "test-model")
        self.assertIn("mode: online (test-model)", output)
        self.assertIn("model: request_info", output)
        self.assertIn(f"follow-up: {question}", output)
        self.assertIn("evidence: #288707  Keystrokes are invisible.  "
                      "https://github.com/microsoft/vscode/issues/288707", output)
        self.assertIn("validation: passed", output)

    def test_model_can_select_second_candidate(self):
        result = {
            "action": "link_existing",
            "linked_issue_number": 285493,
            "evidence": [{"issue_number": 285493, "observation": "Candidate observation."}],
            "follow_up_questions": [],
        }
        output, _ = self.run_online(result)
        self.assertIn("linked issue: https://github.com/microsoft/vscode/issues/285493", output)

    def test_bad_output_stops_online_command(self):
        valid = {
            "action": "link_existing",
            "linked_issue_number": 285493,
            "evidence": [{"issue_number": 285493, "observation": "Candidate observation."}],
            "follow_up_questions": [],
        }
        for result, status in (
            (dict(valid, linked_issue_number=303202), "completed"),
            (dict(valid, evidence=[{"issue_number": 303202, "observation": "Outside candidate list."}]), "completed"),
            (dict(valid, action="request_info", linked_issue_number=None), "completed"),
            (valid, "incomplete"),
        ):
            with self.subTest(result=result, status=status), patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.run_online(result, status)
                self.assertEqual(error.exception.code, 1)
