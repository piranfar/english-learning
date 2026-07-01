import re
import difflib


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", (text or "").lower())


def _estimate_pace_score(target_tokens: list[str], spoken_tokens: list[str], duration_seconds: float | None) -> int | None:
    if not duration_seconds or duration_seconds <= 0 or not spoken_tokens:
        return None
    wpm = len(spoken_tokens) / (duration_seconds / 60)
    target_wpm = max(len(target_tokens) * 2.2, 80)
    ratio = wpm / target_wpm if target_wpm else 1
    if 0.75 <= ratio <= 1.35:
        return 85
    if 0.55 <= ratio <= 1.6:
        return 70
    if 0.4 <= ratio <= 2.0:
        return 55
    return 40


def compare_shadowing(
    target_text: str,
    transcript: str,
    *,
    input_mode: str = "voice",
    duration_seconds: float | None = None,
) -> dict:
    target_tokens = tokenize(target_text)
    spoken_tokens = tokenize(transcript)

    matcher = difflib.SequenceMatcher(None, target_tokens, spoken_tokens)
    similarity_score = int(round(matcher.ratio() * 100))

    missing_words: list[str] = []
    extra_words: list[str] = []
    changed_words: list[dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            missing_words.extend(target_tokens[i1:i2])
        elif tag == "insert":
            extra_words.extend(spoken_tokens[j1:j2])
        elif tag == "replace":
            expected = target_tokens[i1:i2]
            spoken = spoken_tokens[j1:j2]
            pair_count = min(len(expected), len(spoken))
            for index in range(pair_count):
                changed_words.append(
                    {"expected": expected[index], "spoken": spoken[index]}
                )
            if len(expected) > pair_count:
                missing_words.extend(expected[pair_count:])
            if len(spoken) > pair_count:
                extra_words.extend(spoken[pair_count:])

    feedback, persian_feedback = build_shadowing_feedback(
        similarity_score, missing_words, extra_words, changed_words
    )

    word_accuracy = similarity_score
    fluency = max(0, min(100, word_accuracy - min(len(extra_words), 6) * 4))
    pace = _estimate_pace_score(target_tokens, spoken_tokens, duration_seconds)
    pronunciation_clarity = word_accuracy if input_mode == "voice" else None
    intonation = None if input_mode == "typed" else max(0, min(100, fluency - 5))

    retry_instruction = _build_retry_instruction(missing_words, changed_words, similarity_score)
    next_drill = _build_next_drill(target_text, missing_words, changed_words)

    structured = {
        "target_sentence": target_text,
        "transcript": transcript,
        "overall_score": word_accuracy,
        "word_accuracy": word_accuracy,
        "fluency": fluency,
        "pace": pace,
        "pronunciation_clarity": pronunciation_clarity,
        "intonation": intonation,
        "missing_words": missing_words,
        "changed_words": changed_words,
        "extra_words": extra_words,
        "feedback": feedback,
        "retry_instruction": retry_instruction,
        "next_drill": next_drill,
        "input_mode": input_mode,
    }

    return {
        "target_text": target_text,
        "transcript": transcript,
        "similarity_score": similarity_score,
        "missing_words": missing_words,
        "extra_words": extra_words,
        "changed_words": changed_words,
        "feedback": feedback,
        "persian_feedback": persian_feedback,
        **structured,
    }


def _build_retry_instruction(
    missing_words: list[str],
    changed_words: list[dict],
    score: int,
) -> str:
    if score >= 90:
        return "Excellent match. Try the next sentence at normal speaking speed."
    if missing_words:
        return f"Retry slowly and include: {', '.join(missing_words[:4])}."
    if changed_words:
        sample = changed_words[0]
        return f"Retry and say '{sample['expected']}' instead of '{sample['spoken']}'."
    return "Listen to the target sentence, then shadow it in smaller chunks."


def _build_next_drill(
    target_text: str,
    missing_words: list[str],
    changed_words: list[dict],
) -> dict:
    if missing_words:
        return {
            "title": "Fill the missing words",
            "instruction": f"Say the sentence again, focusing on: {', '.join(missing_words[:3])}.",
            "target": "word accuracy",
        }
    if changed_words:
        pair = changed_words[0]
        return {
            "title": "Fix one changed word",
            "instruction": f"Repeat the sentence using '{pair['expected']}' clearly.",
            "target": "pronunciation clarity",
        }
    return {
        "title": "Smooth shadowing",
        "instruction": f"Say this sentence three times with steady rhythm: {target_text}",
        "target": "fluency and pace",
    }


def build_shadowing_feedback(
    score: int,
    missing_words: list[str],
    extra_words: list[str],
    changed_words: list[dict],
) -> tuple[str, str]:
    if score >= 90:
        feedback = "Excellent shadowing. Your words match the target very well."
        persian = "عالی بود! تلفظ و ریتم شما با جمله هدف خیلی نزدیک بود."
    elif score >= 70:
        feedback = "Good attempt. Focus on the missed or changed words and try again."
        persian = "خوب بود. روی کلماتی که جا افتاده یا فرق داشت تمرکز کن و دوباره بگو."
    elif score >= 50:
        feedback = "Keep practicing. Read the target sentence aloud slowly, then shadow again."
        persian = "ادامه بده. اول جمله را آهسته بخوان، بعد دوباره shadowing کن."
    else:
        feedback = "Try listening to the target sentence first, then repeat it in smaller chunks."
        persian = "اول جمله را بشناس، بعد آن را تکه‌تکه تکرار کن."

    details = []
    if missing_words:
        details.append(f"Missing: {', '.join(missing_words[:8])}")
    if extra_words:
        details.append(f"Extra: {', '.join(extra_words[:8])}")
    if changed_words:
        sample = changed_words[:3]
        details.append(
            "Changed: "
            + "; ".join(
                f"{item['expected']}→{item['spoken']}" for item in sample
            )
        )

    if details:
        feedback = f"{feedback} {' | '.join(details)}"

    return feedback, persian
