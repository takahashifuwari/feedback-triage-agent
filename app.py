"""Single-page interface for the VS Code feedback triage workflow."""

import json
from datetime import datetime, timezone

import streamlit as st

from history import ROOT
from triage import triage_feedback


ACTIONS = {
    "link_existing": "Link to an existing issue",
    "request_info": "Ask for more information",
    "create_new": "Suggest a new issue",
}
MODES = ("Offline rules", "Gemini")


def custom_feedback(title, summary, version, steps):
    return {
        "issue_number": 0,
        "title": title.strip(),
        "symptom_summary": summary.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vscode_version": version.strip() or None,
        "repro_steps": [line.strip() for line in steps.splitlines() if line.strip()],
        "os_version": None,
        "shell": None,
        "error_message": None,
        "source_url": None,
    }


def show_result(feedback, result, mode):
    with st.container(border=True):
        st.caption(f"MODE  ·  {result['model'] or mode}")
        st.subheader(ACTIONS[result["action"]])
        st.text(feedback["title"])
        if result["link"]:
            st.markdown(f"[Open linked issue #{result['linked_issue_number']}]({result['link']})")
        if result["questions"]:
            st.markdown("**Follow-up questions**")
            for index, question in enumerate(result["questions"], 1):
                st.text(f"{index}. {question}")
        if result["evidence"]:
            with st.expander("Model evidence", expanded=True):
                for number, observation, url in result["evidence"]:
                    if url:
                        st.markdown(f"[Issue #{number}]({url})")
                    else:
                        st.markdown("**Submitted feedback**")
                    st.text(observation)

    st.subheader("Similar issues")
    if not result["matches"]:
        st.caption("No earlier issues with matching terms were found.")
    for ticket, score in result["matches"]:
        with st.container(border=True):
            st.markdown(f"[#{ticket['issue_number']}]({ticket['source_url']}) · `{score:.3f}`")
            st.text(ticket["title"])
            st.text(ticket["symptom_summary"])
            st.caption(f"VS Code {ticket['vscode_version'] or 'version unknown'}")


def main():
    st.set_page_config(page_title="Feedback triage", layout="wide")
    st.markdown("""
        <style>
        .block-container {max-width: 72rem; padding-top: 3.2rem;}
        [data-testid="stText"] {white-space: pre-wrap; overflow-wrap: anywhere;}
        @media (max-width: 680px) {
            .block-container {padding-left: 1rem; padding-right: 1rem;}
            [data-testid="stHorizontalBlock"] {flex-direction: column;}
            [data-testid="stColumn"] {width: 100%; flex: 1 1 auto;}
        }
        </style>
        """, unsafe_allow_html=True)
    st.title("Feedback triage")
    st.caption("VS Code integrated terminal")
    st.divider()

    samples = {
        row["issue_number"]: row
        for row in json.loads((ROOT / "eval/dev_queries.json").read_text(encoding="utf-8"))
    }
    intake, results = st.columns([1, 1.2], gap="large")
    with intake:
        st.subheader("Feedback")
        source = st.radio("Feedback source", ("Example", "New feedback"), horizontal=True)
        example = source == "Example"
        if example:
            number = st.selectbox("Example issue", samples, format_func=lambda n: f"#{n}")
        with st.form("triage"):
            if example:
                feedback = samples[number]
                st.caption("Submitted feedback")
                st.text(feedback["title"])
                st.text(feedback["symptom_summary"])
                st.markdown(f"[Open original feedback]({feedback['source_url']})")
            else:
                title = st.text_input("Title")
                summary = st.text_area("What happened?", help="Use English for the current issue library.")
                version = st.text_input("VS Code version (optional)")
                steps = st.text_area("Steps to reproduce (optional)", placeholder="One step per line")
            mode = st.radio("Review mode", MODES, horizontal=True)
            submitted = st.form_submit_button("Run triage", type="primary")

    selection = (source, number if example else None)
    with results:
        st.subheader("Triage result")
        if submitted:
            st.session_state.pop("triage_result", None)
            if not example:
                feedback = custom_feedback(title, summary, version, steps)
            if not feedback["title"] or not feedback["symptom_summary"]:
                st.error("Enter a title and describe what happened.")
            else:
                candidates = json.loads((ROOT / "data/seed_issues.json").read_text(encoding="utf-8"))
                try:
                    with st.spinner("Reviewing feedback…"):
                        result = triage_feedback(feedback, candidates, online=mode == "Gemini")
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))
                else:
                    st.session_state.triage_result = selection, feedback, result, mode
        previous = st.session_state.get("triage_result")
        if previous and previous[0] == selection:
            show_result(*previous[1:])
        elif not submitted:
            with st.container(border=True):
                st.write("Run triage to see a suggested action and the similar issues behind it.")


if __name__ == "__main__":
    main()
