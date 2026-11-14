"""Rank historical tickets and suggest an offline triage action."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from history import filter_history, load_replay


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


def main():
    feedback, candidates = load_replay(__doc__)
    matches = retrieve(feedback, candidates)
    for ticket, score in matches:
        print(f"#{ticket['issue_number']}  {score:.3f}  {ticket['source_url']}")
    action, link = baseline_action(feedback, matches)
    detail = f" #{link}" if link is not None else ""
    print(f"baseline: {action}{detail}")


if __name__ == "__main__":
    main()
