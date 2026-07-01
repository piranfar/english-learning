import csv
import json
from pathlib import Path

from tutor.models import VocabularySeed

CSV_COLUMNS = [
    "word",
    "lemma",
    "part_of_speech",
    "cefr_level",
    "category",
    "definition",
    "persian_meaning",
    "example",
    "source",
    "frequency_rank",
    "collocations",
    "shadowing_sentence",
    "common_mistake",
    "correction",
    "notes",
    "approved",
]

REQUIRED_COLUMNS = ["word", "category", "part_of_speech"]


def parse_bool(value: str, default: bool = False) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "y"}


def parse_collocations(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in text.split("|") if part.strip()]


def row_to_payload(row: dict) -> dict | None:
    word = (row.get("word") or "").strip()
    if not word:
        return None

    category = (row.get("category") or "").strip()
    part_of_speech = (row.get("part_of_speech") or "").strip()
    frequency_raw = (row.get("frequency_rank") or "").strip()
    frequency_rank = int(frequency_raw) if frequency_raw else None

    return {
        "word": word,
        "lemma": (row.get("lemma") or word).strip(),
        "part_of_speech": part_of_speech,
        "cefr_level": (row.get("cefr_level") or "").strip(),
        "category": category,
        "definition": (row.get("definition") or "").strip(),
        "persian_meaning": (row.get("persian_meaning") or "").strip(),
        "example": (row.get("example") or "").strip(),
        "source": (row.get("source") or "").strip(),
        "frequency_rank": frequency_rank,
        "collocations": parse_collocations(row.get("collocations") or ""),
        "shadowing_sentence": (row.get("shadowing_sentence") or "").strip(),
        "common_mistake": (row.get("common_mistake") or "").strip(),
        "correction": (row.get("correction") or "").strip(),
        "notes": (row.get("notes") or "").strip(),
        "approved": parse_bool(row.get("approved") or "", default=False),
        "is_active": True,
    }


def find_seed(word: str, category: str, part_of_speech: str) -> VocabularySeed | None:
    return VocabularySeed.objects.filter(
        word=word,
        category=category,
        part_of_speech=part_of_speech,
    ).first()


def merge_seed_fields(existing: VocabularySeed, payload: dict, overwrite: bool) -> bool:
    changed = False
    for field, value in payload.items():
        if field in {"word", "is_active"}:
            continue
        current = getattr(existing, field)
        if overwrite:
            if current != value:
                setattr(existing, field, value)
                changed = True
        elif value and (current in (None, "", [], {}) or current is False):
            setattr(existing, field, value)
            changed = True
    if changed:
        existing.save()
    return changed


def import_vocab_csv(
    csv_path: Path,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> tuple[int, int, int]:
    created = 0
    updated = 0
    skipped = 0

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        for row in reader:
            payload = row_to_payload(row)
            if payload is None:
                skipped += 1
                continue

            if dry_run:
                existing = find_seed(
                    payload["word"], payload["category"], payload["part_of_speech"]
                )
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            existing = find_seed(
                payload["word"], payload["category"], payload["part_of_speech"]
            )
            if existing:
                if merge_seed_fields(existing, payload, overwrite):
                    updated += 1
                else:
                    skipped += 1
            else:
                VocabularySeed.objects.create(**payload)
                created += 1

    return created, updated, skipped
