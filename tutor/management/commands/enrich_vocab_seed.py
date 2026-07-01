from django.core.management.base import BaseCommand, CommandError

from tutor.models import VocabularySeed
from tutor.services import (
    build_vocab_enrichment_prompt,
    generate_from_template,
    parse_vocab_enrichment_json,
)
from tutor.vocab_import import parse_collocations


class Command(BaseCommand):
    help = "AI-enrich VocabularySeed rows with missing fields via Django provider layer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--category",
            type=str,
            required=True,
            help="Category key to enrich (e.g. toefl_academic)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of seeds to enrich (default 20)",
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="",
            help="Optional AI provider override",
        )
        parser.add_argument(
            "--auto-approve",
            action="store_true",
            help="Mark enriched seeds as approved=True (default: approved=False)",
        )

    def handle(self, *args, **options):
        category = options["category"].strip()
        limit = max(1, options["limit"])
        provider = options.get("provider") or None

        queryset = VocabularySeed.objects.filter(is_active=True, category=category).order_by(
            "frequency_rank", "word"
        )

        candidates = []
        for seed in queryset:
            if self._needs_enrichment(seed):
                candidates.append(seed)
            if len(candidates) >= limit:
                break

        if not candidates:
            self.stdout.write(
                self.style.WARNING(f"No seeds needing enrichment in category '{category}'.")
            )
            return

        enriched = 0
        failed = 0

        for seed in candidates:
            prompt = build_vocab_enrichment_prompt(seed)
            try:
                raw = generate_from_template("vocab_builder", prompt, provider=provider)
                data = parse_vocab_enrichment_json(raw)
            except (ValueError, RuntimeError) as exc:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed '{seed.word}': {exc}")
                )
                continue

            seed.definition = (data.get("definition") or seed.definition or "").strip()
            seed.persian_meaning = (
                data.get("persian_meaning") or seed.persian_meaning or ""
            ).strip()
            seed.example = (data.get("example") or seed.example or "").strip()
            collocations = data.get("collocations") or []
            if isinstance(collocations, list):
                seed.collocations = [str(c).strip() for c in collocations if str(c).strip()]
            elif isinstance(collocations, str):
                seed.collocations = parse_collocations(collocations)
            seed.shadowing_sentence = (
                data.get("shadowing_sentence") or seed.shadowing_sentence or ""
            ).strip()
            seed.common_mistake = (
                data.get("common_mistake") or seed.common_mistake or ""
            ).strip()
            seed.correction = (data.get("correction") or seed.correction or "").strip()
            seed.approved = bool(options["auto_approve"])
            seed.save()
            enriched += 1
            self.stdout.write(self.style.SUCCESS(f"Enriched: {seed.word}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Enriched {enriched}, failed {failed} in category '{category}'."
            )
        )

    def _needs_enrichment(self, seed: VocabularySeed) -> bool:
        return not all(
            [
                seed.definition,
                seed.example,
                seed.persian_meaning,
                seed.collocations,
                seed.shadowing_sentence,
            ]
        )
