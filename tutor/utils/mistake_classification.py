"""Deterministic mistake category classification."""

import re
from difflib import SequenceMatcher

MISTAKE_CATEGORY_ARTICLE = "article"
MISTAKE_CATEGORY_PREPOSITION = "preposition"
MISTAKE_CATEGORY_TENSE = "tense"
MISTAKE_CATEGORY_SUBJECT_VERB = "subject_verb_agreement"
MISTAKE_CATEGORY_WORD_ORDER = "word_order"
MISTAKE_CATEGORY_SPELLING = "spelling"
MISTAKE_CATEGORY_SENTENCE_STRUCTURE = "sentence_structure"
MISTAKE_CATEGORY_FRAGMENT = "fragment"
MISTAKE_CATEGORY_RUN_ON = "run_on_sentence"
MISTAKE_CATEGORY_COLLOCATION = "collocation"
MISTAKE_CATEGORY_VOCABULARY = "vocabulary_precision"
MISTAKE_CATEGORY_ACADEMIC_TONE = "academic_tone"
MISTAKE_CATEGORY_DIRECT_TRANSLATION = "direct_translation"
MISTAKE_CATEGORY_SPEAKING_ORG = "speaking_organization"
MISTAKE_CATEGORY_PRONUNCIATION = "pronunciation_fluency"
MISTAKE_CATEGORY_READING = "reading_comprehension"
MISTAKE_CATEGORY_LISTENING = "listening_comprehension"
MISTAKE_CATEGORY_OTHER = "other"

MISTAKE_CATEGORIES = (
    MISTAKE_CATEGORY_ARTICLE,
    MISTAKE_CATEGORY_PREPOSITION,
    MISTAKE_CATEGORY_TENSE,
    MISTAKE_CATEGORY_SUBJECT_VERB,
    MISTAKE_CATEGORY_WORD_ORDER,
    MISTAKE_CATEGORY_SPELLING,
    MISTAKE_CATEGORY_SENTENCE_STRUCTURE,
    MISTAKE_CATEGORY_FRAGMENT,
    MISTAKE_CATEGORY_RUN_ON,
    MISTAKE_CATEGORY_COLLOCATION,
    MISTAKE_CATEGORY_VOCABULARY,
    MISTAKE_CATEGORY_ACADEMIC_TONE,
    MISTAKE_CATEGORY_DIRECT_TRANSLATION,
    MISTAKE_CATEGORY_SPEAKING_ORG,
    MISTAKE_CATEGORY_PRONUNCIATION,
    MISTAKE_CATEGORY_READING,
    MISTAKE_CATEGORY_LISTENING,
    MISTAKE_CATEGORY_OTHER,
)

MISTAKE_CATEGORY_CHOICES = [(value, value.replace("_", " ").title()) for value in MISTAKE_CATEGORIES]

_ARTICLE_WRONG_RE = re.compile(
    r"\b(an [bcdfghjklmnpqrstvwxyz]|a [aeiou]|the a |the an )\w*",
    re.IGNORECASE,
)
_SUBJECT_VERB_WRONG_RE = re.compile(
    r"\b("
    r"which|who|that|he|she|it|each|every|everyone|somebody|nobody|either|neither|none"
    r")\s+\w+\s+(make|go|do|have|was|were|is|are|does|don't|doesn't)\b",
    re.IGNORECASE,
)
_MISSING_LINKING_VERB_RE = re.compile(
    r"\b(favorite|hobby|job|goal|plan|dream|reason|problem|idea)\s+\w+ing\b",
    re.IGNORECASE,
)


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def _looks_like_spelling_error(wrong: str, correct: str, reason: str) -> bool:
    if re.search(r"spell|spelling|typo|misspell|letter order|double letter", reason, re.I):
        return True

    wrong_words = wrong.split()
    correct_words = correct.split()
    if len(wrong_words) == 1 and len(correct_words) == 1:
        left, right = wrong_words[0], correct_words[0]
        if left.lower() != right.lower() and _similarity(left, right) >= 0.65:
            return True

    if wrong_words and correct_words and len(wrong_words) == len(correct_words):
        pairs = zip(wrong_words, correct_words, strict=False)
        spelling_pairs = [
            1
            for left, right in pairs
            if left.lower() != right.lower() and _similarity(left, right) >= 0.65
        ]
        if spelling_pairs and len(spelling_pairs) >= max(1, len(wrong_words) // 2):
            return True

    return False


def classify_mistake(
    wrong: str,
    correct: str = "",
    reason: str = "",
    source_track: str = "",
) -> str:
    """Classify a mistake using keyword and pattern rules."""
    wrong = (wrong or "").strip()
    correct = (correct or "").strip()
    reason = (reason or "").strip()
    track = (source_track or "").strip().lower()
    blob = f"{wrong} {correct} {reason}".lower()

    if track == "vocab_quiz":
        return MISTAKE_CATEGORY_VOCABULARY

    if re.search(r"subject.?verb|subject-verb|trans|verb agreement|singular/plural|third person", blob):
        return MISTAKE_CATEGORY_SUBJECT_VERB

    if _SUBJECT_VERB_WRONG_RE.search(wrong):
        return MISTAKE_CATEGORY_SUBJECT_VERB

    if re.search(r"article|missing article|add article|use (a|an|the)\b|article error", blob):
        return MISTAKE_CATEGORY_ARTICLE

    if _ARTICLE_WRONG_RE.search(wrong):
        return MISTAKE_CATEGORY_ARTICLE

    if re.search(r"preposition|wrong preposition|in/on/at error|prepositional phrase", blob):
        return MISTAKE_CATEGORY_PREPOSITION

    if re.search(r"tense|past tense|present tense|future tense|verb tense|irregular verb", blob):
        return MISTAKE_CATEGORY_TENSE

    if re.search(r"word order|inverted order|adjective order|adverb placement", blob):
        return MISTAKE_CATEGORY_WORD_ORDER

    if _looks_like_spelling_error(wrong, correct, reason):
        return MISTAKE_CATEGORY_SPELLING

    if re.search(r"run-on|run on sentence|comma splice|fused sentence", blob):
        return MISTAKE_CATEGORY_RUN_ON

    if re.search(r"fragment|incomplete sentence|missing subject|missing verb", blob):
        return MISTAKE_CATEGORY_FRAGMENT

    if re.search(
        r"sentence structure|awkward sentence|combine sentences|clause|missing linking verb",
        blob,
    ):
        return MISTAKE_CATEGORY_SENTENCE_STRUCTURE

    if _MISSING_LINKING_VERB_RE.search(wrong):
        return MISTAKE_CATEGORY_SENTENCE_STRUCTURE

    if re.search(r"collocation|natural wording|word combination|fixed phrase", blob):
        return MISTAKE_CATEGORY_COLLOCATION

    if re.search(
        r"word choice|vocabulary|precise meaning|synonym|definition|natural wording",
        blob,
    ):
        return MISTAKE_CATEGORY_VOCABULARY

    if re.search(r"academic tone|formal tone|register|scholarly|thesis|cohesion", blob):
        return MISTAKE_CATEGORY_ACADEMIC_TONE

    if re.search(r"direct translation|persian structure|calque|literal translation", blob):
        return MISTAKE_CATEGORY_DIRECT_TRANSLATION

    if re.search(r"organization|structure your answer|clear main point|speaking outline", blob):
        return MISTAKE_CATEGORY_SPEAKING_ORG

    if re.search(r"pronunciation|fluency|intonation|stress pattern|connected speech", blob):
        return MISTAKE_CATEGORY_PRONUNCIATION

    if track == "reading_coach" and re.search(r"comprehension|main idea|inference|detail", blob):
        return MISTAKE_CATEGORY_READING

    if track == "listening_coach" and re.search(r"comprehension|main idea|inference|detail", blob):
        return MISTAKE_CATEGORY_LISTENING

    if track == "reading_coach":
        return MISTAKE_CATEGORY_READING

    if track == "listening_coach":
        return MISTAKE_CATEGORY_LISTENING

    if track == "speaking_coach":
        return MISTAKE_CATEGORY_SPEAKING_ORG

    return MISTAKE_CATEGORY_OTHER
