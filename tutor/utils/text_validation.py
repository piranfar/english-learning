"""Lightweight checks for learner writing and mistake text."""

import re
from collections import Counter

# Common English words learners are likely to use in practice.
COMMON_ENGLISH_WORDS = frozenset(
    """
    a an the and or but so because if when while as at by for from in into of on to with
    i you he she it we they my your his her our their me him us them this that these those
    is am are was were be been being have has had do does did can could will would should may might
    go goes went going get got make makes made take takes took see saw know knew think thought
    like likes liked want wants wanted need needs needed use uses used work works worked live lives
    good better best bad new old big small long short high low many much more most some any every
    all not no yes very really also just only even still already again then there here where
    who what which how why up down out over under about after before during through between
    agree agreed best regard regards book study studying school spring weather happy energy
    """.split()
)

_VOWEL_RE = re.compile(r"[aeiouAEIOU]")
_WORD_RE = re.compile(r"[a-zA-Z']+")
_CONSONANT_RUN_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{5,}")


def _normalize_words(value: str) -> list[str]:
    return [word.lower().strip("'") for word in _WORD_RE.findall(value or "")]


def _letter_ratio(value: str) -> float:
    letters = sum(1 for char in value if char.isalpha())
    return letters / max(len(value), 1)


def _is_keyboard_smash_word(word: str) -> bool:
    if len(word) <= 2:
        return False
    if not _VOWEL_RE.search(word) and len(word) >= 4:
        return True
    if _CONSONANT_RUN_RE.search(word):
        return True
    vowels = len(_VOWEL_RE.findall(word))
    return len(word) >= 4 and vowels / len(word) < 0.15


def _is_gibberish_word(word: str) -> bool:
    if word in COMMON_ENGLISH_WORDS or len(word) <= 2:
        return False
    if _is_keyboard_smash_word(word):
        return True
    vowels = len(_VOWEL_RE.findall(word))
    if len(word) <= 3 and vowels == 0:
        return True
    if len(word) == 3 and vowels <= 1 and word not in COMMON_ENGLISH_WORDS:
        return True
    return False


def _is_repetitive_tokens(words: list[str]) -> bool:
    if len(words) < 3:
        return False
    counts = Counter(words)
    _word, top_count = counts.most_common(1)[0]
    if top_count / len(words) > 0.5:
        return True
    if len(words) >= 4 and len(set(words)) / len(words) < 0.5:
        return True
    return False


def _word_is_plausible(word: str) -> bool:
    if not word:
        return False
    if len(word) == 1 and word in {"a", "i"}:
        return True
    if word in COMMON_ENGLISH_WORDS:
        return True
    if len(word) <= 20 and _VOWEL_RE.search(word) and not _is_keyboard_smash_word(word):
        return True
    return False


def is_meaningful_learner_text(value: str) -> bool:
    """Return True when text looks like a real learner mistake or answer."""
    cleaned = (value or "").strip()
    if not cleaned:
        return False

    if not _WORD_RE.search(cleaned):
        return False

    if _letter_ratio(cleaned) < 0.5:
        return False

    words = _normalize_words(cleaned)
    if not words:
        return False

    if _is_repetitive_tokens(words):
        return False

    smash_words = [word for word in words if _is_keyboard_smash_word(word)]
    gibberish_words = [word for word in words if _is_gibberish_word(word)]
    if smash_words and len(smash_words) >= max(1, len(words) // 2):
        return False
    if gibberish_words and len(gibberish_words) >= max(1, len(words) // 2):
        return False

    known_words = sum(1 for word in words if word in COMMON_ENGLISH_WORDS)
    plausible_words = sum(1 for word in words if _word_is_plausible(word))

    if len(words) >= 3 and known_words == 0 and all(len(word) <= 5 for word in words):
        return False

    # Short learner mistakes: allow typos and brief phrases.
    if len(words) <= 4 or len(cleaned) <= 40:
        if gibberish_words and len(gibberish_words) == len(words):
            return False
        return plausible_words >= 1

    vowel_words = sum(1 for word in words if _VOWEL_RE.search(word))
    if vowel_words / len(words) < 0.6:
        return False

    real_words = [word for word in words if len(word) >= 2]
    if len(real_words) < 2:
        return plausible_words >= 1

    if known_words >= 1:
        return True

    if len(words) >= 5 and known_words == 0:
        return False

    return plausible_words / len(words) >= 0.5


def is_meaningful_mistake(wrong_text: str, correct_text: str = "") -> bool:
    """Validate the core fields stored on a Mistake record."""
    if not is_meaningful_learner_text(wrong_text):
        return False

    correct = (correct_text or "").strip()
    if correct and not is_meaningful_learner_text(correct):
        return False

    return True


def is_meaningful_writing_text(value: str) -> bool:
    """Stricter check for full paragraphs submitted for editing."""
    cleaned = (value or "").strip()
    if len(cleaned) < 10:
        return False

    words = _normalize_words(cleaned)
    if len(words) < 3:
        return False

    real_words = [word for word in words if len(word) >= 2]
    if len(real_words) < 2:
        return False

    if _letter_ratio(cleaned) < 0.55:
        return False

    known_words = sum(1 for word in real_words if word in COMMON_ENGLISH_WORDS)
    if known_words < 2:
        return False

    if _is_repetitive_tokens(real_words):
        return False

    vowel_words = sum(1 for word in real_words if _VOWEL_RE.search(word))
    if vowel_words / len(real_words) < 0.6:
        return False

    return True
