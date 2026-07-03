from django.conf import settings
from django.db import migrations, models


def seed_task_provider_settings(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    TaskProviderSetting = apps.get_model("tutor", "TaskProviderSetting")

    default = getattr(settings, "DEFAULT_AI_PROVIDER", "ollama").lower().strip()
    reading_default = getattr(settings, "READING_AI_PROVIDER", "openai").lower().strip()

    task_types = (
        PromptTemplate.objects.values_list("task_type", flat=True).distinct().order_by("task_type")
    )
    for task_type in task_types:
        preferred = reading_default if str(task_type).startswith("reading_") else default
        active_providers = list(
            PromptTemplate.objects.filter(task_type=task_type, is_active=True)
            .order_by("provider")
            .values_list("provider", flat=True)
        )
        provider = preferred if preferred in active_providers else (
            active_providers[0] if active_providers else preferred
        )
        TaskProviderSetting.objects.update_or_create(
            task_type=task_type,
            defaults={"provider": provider},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("tutor", "0038_grammar_coach_followup_prompt"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskProviderSetting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("task_type", models.CharField(max_length=100, unique=True)),
                ("provider", models.CharField(max_length=50)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["task_type"],
            },
        ),
        migrations.RunPython(seed_task_provider_settings, migrations.RunPython.noop),
    ]
