from django.db import migrations


def seed_paraphrase_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_paraphrase import WRITING_PARAPHRASE_TEMPLATES

    for template in WRITING_PARAPHRASE_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0020_update_writing_edit_prompt"),
    ]

    operations = [
        migrations.RunPython(seed_paraphrase_prompts, migrations.RunPython.noop),
    ]
