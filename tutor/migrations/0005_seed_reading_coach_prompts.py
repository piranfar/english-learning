from django.db import migrations


def seed_reading_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.reading_coach import READING_COACH_TEMPLATES

    for template in READING_COACH_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


def unseed_reading_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(task_type="reading_coach").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0003_seed_writing_vocab_prompts"),
    ]

    operations = [
        migrations.RunPython(seed_reading_coach_prompts, unseed_reading_coach_prompts),
    ]
