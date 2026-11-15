import os
import unittest
from unittest.mock import patch
from urllib.error import URLError

from streamlit.testing.v1 import AppTest

from history import ROOT


class AppTestCase(unittest.TestCase):
    def test_offline_example_displays_suggestion_and_source(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertIn("Ask for more information", [item.value for item in app.subheader])
        self.assertIn(
            "[#288707](https://github.com/microsoft/vscode/issues/288707) · `0.467`",
            [item.value for item in app.markdown],
        )

        app.selectbox[0].select(237688).run()
        self.assertNotIn("Ask for more information", [item.value for item in app.subheader])

    def test_handoff_edits_persist_until_a_new_run(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.button[0].click().run()

        draft = app.text_area(key="handoff_draft")
        self.assertIn("Suggested action: Ask for more information", draft.value)
        self.assertIn("Candidate #288707: https://github.com/microsoft/vscode/issues/288707", draft.value)
        original = draft.value
        draft.set_value("Reviewed handoff").run()
        self.assertEqual(app.text_area(key="handoff_draft").value, "Reviewed handoff")

        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area(key="handoff_draft").value, original)

    def test_gemini_failure_can_retry_the_submitted_feedback_offline(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.radio[0].set_value("New feedback").run()
        app.text_input[0].set_value("Integrated terminal is blank")
        app.text_area[0].set_value("The terminal opens but commands give no output.")
        app.radio[1].set_value("Gemini")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), patch(
            "model_review.urlopen", side_effect=URLError("test connection failure")
        ) as request:
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn("Gemini review failed.", app.error[0].value)
            self.assertEqual(app.button[1].label, "Run offline rules")
            app.button[1].click().run()
            request.assert_called_once()

        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertIn("MODE  ·  Offline rules", [item.value for item in app.caption])
        self.assertIn("Feedback: Integrated terminal is blank", app.text_area(key="handoff_draft").value)

    def test_no_matches_are_shown_in_result_and_handoff(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.radio[0].set_value("New feedback").run()
        app.text_input[0].set_value("Vexing quokka")
        app.text_area[0].set_value("Magenta saxophone.")
        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertIn("No matching earlier issues", app.info[0].value)
        self.assertIn("Candidates: no matching earlier issues", app.text_area(key="handoff_draft").value)
