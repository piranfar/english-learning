from django.db import migrations


def update_speaking_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.speaking_coach import SPEAKING_COACH_TEMPLATES

    for template in SPEAKING_COACH_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0028_update_writing_coach_revision_prompts"),
    ]

    operations = [
        migrations.RunPython(update_speaking_coach_prompts, migrations.RunPython.noop),
    ]
