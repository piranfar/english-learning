from django.db import migrations


def seed_reading_quiz_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.reading_coach import READING_QUIZ_TEMPLATES

    for template in READING_QUIZ_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0025_mistake_category"),
    ]

    operations = [
        migrations.RunPython(seed_reading_quiz_prompts, migrations.RunPython.noop),
    ]
