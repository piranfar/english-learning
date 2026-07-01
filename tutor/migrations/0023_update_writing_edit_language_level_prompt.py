from django.db import migrations


def update_writing_edit_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_tools import WRITING_EDIT_COACH_PROMPT

    for provider in ("ollama", "openai", "anthropic"):
        PromptTemplate.objects.filter(
            task_type="writing_edit_coach",
            provider=provider,
        ).update(system_prompt=WRITING_EDIT_COACH_PROMPT)


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0022_update_paraphrase_language_level"),
    ]

    operations = [
        migrations.RunPython(update_writing_edit_prompts, migrations.RunPython.noop),
    ]
