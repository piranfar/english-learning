from datetime import date, timedelta


def sm2(
    ease_factor: float,
    interval: int,
    repetitions: int,
    quality: int,
    review_date: date | None = None,
) -> tuple[float, int, int, date]:
    """
    Standard SM-2 spaced repetition algorithm.

    quality: 0-5 (0 = complete blackout, 5 = perfect recall)
  Returns updated (ease_factor, interval, repetitions, next_review_date).
    """
    if quality < 0 or quality > 5:
        raise ValueError("quality must be between 0 and 5")

    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1

        ease_factor = ease_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        if ease_factor < 1.3:
            ease_factor = 1.3

    base_date = review_date or date.today()
    next_review_date = base_date + timedelta(days=interval)
    return ease_factor, interval, repetitions, next_review_date
