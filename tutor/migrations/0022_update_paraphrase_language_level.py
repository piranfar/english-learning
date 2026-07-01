from django.db import migrations


def update_paraphrase_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_paraphrase import (
        WRITING_PARAPHRASE_CHECK_SYSTEM,
        WRITING_PARAPHRASE_GENERATE_SYSTEM,
    )

    PromptTemplate.objects.filter(task_type="writing_paraphrase_generate").update(
        system_prompt=WRITING_PARAPHRASE_GENERATE_SYSTEM
    )
    PromptTemplate.objects.filter(task_type="writing_paraphrase_check").update(
        system_prompt=WRITING_PARAPHRASE_CHECK_SYSTEM
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0021_seed_paraphrase_practice_prompts"),
    ]

    operations = [
        migrations.RunPython(update_paraphrase_prompts, migrations.RunPython.noop),
    ]
