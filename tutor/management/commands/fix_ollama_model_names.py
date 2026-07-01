from django.conf import settings
from django.core.management.base import BaseCommand

from tutor.ai.ollama_config import (
    LEGACY_MODEL_RENAMES,
    LIGHT_OLLAMA_TASKS,
    MAIN_OLLAMA_TASKS,
)
from tutor.models import PromptTemplate


class Command(BaseCommand):
    help = "Fix Ollama PromptTemplate model_name values to match installed tagged models."

    def handle(self, *args, **options):
        changed = 0

        for prompt in PromptTemplate.objects.filter(provider="ollama"):
            original = prompt.model_name
            updated = LEGACY_MODEL_RENAMES.get(original, original)

            if prompt.task_type in MAIN_OLLAMA_TASKS:
                updated = settings.DEFAULT_OLLAMA_MODEL
            elif prompt.task_type in LIGHT_OLLAMA_TASKS:
                updated = settings.FAST_OLLAMA_MODEL

            if updated != original:
                prompt.model_name = updated
                prompt.save(update_fields=["model_name"])
                changed += 1
                self.stdout.write(
                    f"Updated {prompt.task_type} ({prompt.title}): "
                    f"{original!r} -> {updated!r}"
                )

        self.stdout.write(self.style.SUCCESS(f"Done. Changed {changed} row(s)."))
        self.stdout.write("")
        self.stdout.write("Current Ollama PromptTemplate rows:")
        for prompt in PromptTemplate.objects.filter(provider="ollama").order_by(
            "task_type", "title"
        ):
            active = "active" if prompt.is_active else "inactive"
            self.stdout.write(
                f"  {prompt.task_type}\t{prompt.title}\t{prompt.model_name}\t{active}"
            )
