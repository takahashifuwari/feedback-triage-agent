import unittest

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
