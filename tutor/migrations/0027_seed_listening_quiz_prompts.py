from django.db import migrations


def seed_listening_quiz_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.listening_coach import LISTENING_QUIZ_TEMPLATES

    for template in LISTENING_QUIZ_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0026_seed_reading_quiz_prompts"),
    ]

    operations = [
        migrations.RunPython(seed_listening_quiz_prompts, migrations.RunPython.noop),
    ]
