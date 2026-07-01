import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tutor.vocab_import import CSV_COLUMNS, import_vocab_csv


class Command(BaseCommand):
    help = "Import vocabulary seed rows from a curated CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            type=str,
            help="Path to CSV file",
        )
        parser.add_argument(
            "--file",
            dest="csv_file",
            type=str,
            help="Path to CSV file (alternative to positional argument)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse the file and report counts without saving.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing fields when duplicate word+category+part_of_speech is found.",
        )

    def handle(self, *args, **options):
        csv_path = options.get("csv_file") or options.get("csv_path")
        if not csv_path:
            raise CommandError(
                "Provide a CSV path: import_vocab_seed path/to/file.csv "
                "or import_vocab_seed --file path/to/file.csv"
            )

        path = Path(csv_path).expanduser()
        if not path.exists():
            raise CommandError(f"CSV file not found: {path}")

        try:
            created, updated, skipped = import_vocab_csv(
                path,
                dry_run=options["dry_run"],
                overwrite=options["overwrite"],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run complete. Would create {created}, update {updated}, skip {skipped}."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Created {created}, updated {updated}, skipped {skipped}."
            )
        )
        self.stdout.write(f"Expected columns: {', '.join(CSV_COLUMNS)}")
