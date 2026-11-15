"""Rank historical tickets and suggest a triage action."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from history import filter_history, load_replay, replay_parser
from model_review import review


LINK_SCORE = 0.45
REVIEW_SCORE = 0.25


def ticket_text(ticket):
    return f"{ticket['title']} {ticket['symptom_summary']}"


def retrieve(feedback, candidates):
    """Return up to three earlier tickets with positive similarity scores."""
    eligible = filter_history(candidates, feedback["created_at"])
    if not eligible:
        return []

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([ticket_text(ticket) for ticket in eligible])
    query = vectorizer.transform([ticket_text(feedback)])
    scores = cosine_similarity(query, matrix)[0]
    ranked = sorted(zip(eligible, scores), key=lambda match: -match[1])
    return [(ticket, float(score)) for ticket, score in ranked[:3] if score > 0]


def baseline_action(feedback, matches):
    """Return the suggested action and any ticket number to link."""
    if matches:
        ticket, score = matches[0]
        version = feedback["vscode_version"]
        if score >= LINK_SCORE and version and version == ticket["vscode_version"]:
            return "link_existing", ticket["issue_number"]
        if score >= REVIEW_SCORE:
            return "request_info", None
    if feedback["repro_steps"]:
        return "create_new", None
    return "request_info", None


def validate_action(action, link, matches):
    """Validate the suggestion and resolve any link against the retrieved tickets."""
    if action == "link_existing":
        for ticket, _ in matches:
            if ticket["issue_number"] == link:
                return ticket["source_url"]
        raise ValueError("linked issue must be among the retrieved candidates")
    if action not in ("request_info", "create_new") or link is not None:
        raise ValueError("invalid action or unexpected linked issue")
    return None


def main():
    parser = replay_parser(__doc__)
    parser.add_argument("--online", action="store_true", help="ask the Gemini model")
    args = parser.parse_args()
    feedback, candidates = load_replay(parser, args.issue_number)
    matches = retrieve(feedback, candidates)
    try:
        if args.online:
            model, result = review(feedback, matches)
            action, link = result["action"], result["linked_issue_number"]
        else:
            action, link = baseline_action(feedback, matches)
        source = validate_action(action, link, matches)
    except (RuntimeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")

    print(f"mode: online ({model})" if args.online else "mode: offline (TF-IDF + rules)")
    print(f"feedback: #{feedback['issue_number']}  {feedback['source_url']}")
    print(f"reported: {feedback['symptom_summary']}")
    for ticket, score in matches:
        print(f"#{ticket['issue_number']}  {score:.3f}  {ticket['source_url']}")
    if matches and not args.online:
        top_ticket, _ = matches[0]
        print(f"top candidate symptom: {top_ticket['symptom_summary']}")
        print("VS Code versions (feedback / top candidate): "
              f"{feedback['vscode_version'] or 'unknown'} / "
              f"{top_ticket['vscode_version'] or 'unknown'}")
    detail = f" #{link}" if link is not None else ""
    label = "model" if args.online else "baseline"
    print(f"{label}: {action}{detail}")
    if source:
        print(f"linked issue: {source}")
    if args.online:
        for number, observation, url in result["evidence"]:
            print(f"evidence: #{number}  {observation}  {url}")
        for question in result["follow_up_questions"]:
            print(f"follow-up: {question}")
    elif action == "request_info":
        print("follow-up: Can you see the characters you type in the terminal?")
        print("follow-up: What output or error appears when opening it or after pressing Enter?")
    print("validation: passed")


if __name__ == "__main__":
    main()
