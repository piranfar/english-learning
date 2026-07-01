from django.db import migrations


def update_writing_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_coach import WRITING_COACH_TEMPLATES
    from tutor.prompts.toefl import TOEFL_TEMPLATES

    toefl_writing_templates = [
        template for template in TOEFL_TEMPLATES if template["task_type"] == "toefl_writing"
    ]

    for template in WRITING_COACH_TEMPLATES + toefl_writing_templates:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0016_update_speaking_coach_prompt"),
    ]

    operations = [
        migrations.RunPython(update_writing_coach_prompts, migrations.RunPython.noop),
    ]
