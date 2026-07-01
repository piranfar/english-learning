from django.db import migrations


def seed_writing_lessons_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_lessons import WRITING_LESSONS_TEMPLATES

    for template in WRITING_LESSONS_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0018_seed_writing_tools_prompts"),
    ]

    operations = [
        migrations.RunPython(seed_writing_lessons_prompts, migrations.RunPython.noop),
    ]
