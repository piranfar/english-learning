from django.db import migrations


def seed_writing_edit_generate_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_tools import WRITING_TOOLS_TEMPLATES

    for template in WRITING_TOOLS_TEMPLATES:
        if template["task_type"] != "writing_edit_generate":
            continue
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0023_update_writing_edit_language_level_prompt"),
    ]

    operations = [
        migrations.RunPython(seed_writing_edit_generate_prompts, migrations.RunPython.noop),
    ]
