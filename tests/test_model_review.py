import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from triage import main


class ModelReviewTest(unittest.TestCase):
    def run_online(self, result, finish_reason="STOP"):
        response = {
            "modelVersion": "test-model",
            "candidates": [{
                "finishReason": finish_reason,
                "content": {"parts": [
                    {"text": "Internal thought", "thought": True},
                    {"text": json.dumps(result)},
                ]},
            }],
        }
        output = io.StringIO()
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": ""}),
            patch("sys.argv", ["triage.py", "293585", "--online"]),
            patch("model_review.urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as call,
            redirect_stdout(output),
        ):
            main()
        return output.getvalue(), call.call_args.args[0]

    def test_model_questions_and_local_evidence_link(self):
        question = "Can you see the typed characters before pressing Enter?"
        result = {
            "action": "request_info",
            "linked_issue_number": None,
            "evidence": [{"issue_number": 288707, "observation": "Keystrokes are invisible."}],
            "follow_up_questions": [question],
        }
        output, request = self.run_online(result)
        payload = json.loads(request.data)
        context = json.loads(payload["contents"][0]["parts"][0]["text"])
        tickets = [context["feedback"], *context["candidates"]]
        self.assertEqual(set(context), {"feedback", "candidates"})
        self.assertEqual([ticket["issue_number"] for ticket in tickets],
                         [293585, 288707, 285493, 224582])
        self.assertTrue(all("source_url" not in ticket for ticket in tickets))
        self.assertNotIn("expected_action", request.data.decode())
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/"
                         "v1beta/models/gemini-3.5-flash-lite:generateContent")
        config = payload["generationConfig"]
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertIn("linked_issue_number", config["responseJsonSchema"]["required"])
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
        for result, finish_reason in (
            (dict(valid, linked_issue_number=303202), "STOP"),
            (dict(valid, evidence=[{"issue_number": 303202, "observation": "Outside candidate list."}]), "STOP"),
            (dict(valid, action="request_info", linked_issue_number=None), "STOP"),
            (valid, "MAX_TOKENS"),
        ):
            with self.subTest(result=result, finish_reason=finish_reason), patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.run_online(result, finish_reason)
                self.assertEqual(error.exception.code, 1)
