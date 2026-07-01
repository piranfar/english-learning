from django.db import migrations


def seed_writing_tools_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_tools import WRITING_TOOLS_TEMPLATES

    for template in WRITING_TOOLS_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0017_update_writing_coach_prompt"),
    ]

    operations = [
        migrations.RunPython(seed_writing_tools_prompts, migrations.RunPython.noop),
    ]
