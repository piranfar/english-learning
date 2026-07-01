from django.core.management import call_command
from django.core.management.base import BaseCommand
from pathlib import Path

from django.conf import settings


class Command(BaseCommand):
    help = "Load the curated starter vocabulary CSV (data/vocab/starter_500.csv)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing seed fields on duplicate rows.",
        )

    def handle(self, *args, **options):
        csv_path = Path(settings.BASE_DIR) / "data" / "vocab" / "starter_500.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Starter CSV not found: {csv_path}")

        cmd_args = ["--file", str(csv_path)]
        if options["overwrite"]:
            cmd_args.append("--overwrite")

        call_command("import_vocab_seed", *cmd_args)
        self.stdout.write(
            self.style.SUCCESS(f"Starter vocabulary loaded from {csv_path.name}.")
        )
