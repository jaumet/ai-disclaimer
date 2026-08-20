import re


# Conservative signals: comments are flagged for a human, never rejected automatically.
REVIEW_TERMS = (
    "fuck", "fucking", "fucked", "shit", "asshole", "bitch", "bastard",
    "puta", "puto", "mierda", "gilipollas", "cabrón", "cabron",
    "merda", "imbècil", "imbecil",
)
REVIEW_RE = re.compile(r"\b(?:" + "|".join(re.escape(term) for term in REVIEW_TERMS) + r")\b", re.IGNORECASE)
URL_RE = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
REPEATED_RE = re.compile(r"(.)\1{9,}", re.IGNORECASE)


def review_comment(comment):
    """Return (needs_review, reason) without preventing the submission."""
    text = (comment or "").strip()
    if not text:
        return False, ""
    if REVIEW_RE.search(text):
        return True, "Potentially offensive wording"
    if len(URL_RE.findall(text)) >= 3:
        return True, "Possible link spam"
    if REPEATED_RE.search(text):
        return True, "Suspicious repeated characters"
    letters = [character for character in text if character.isalpha()]
    if len(letters) >= 30 and sum(character.isupper() for character in letters) / len(letters) > 0.85:
        return True, "Excessive uppercase text"
    return False, ""
