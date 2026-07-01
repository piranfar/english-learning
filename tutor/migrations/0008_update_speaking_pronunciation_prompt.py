from django.db import migrations


def update_speaking_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.speaking_coach import SPEAKING_COACH_SYSTEM_PROMPT

    PromptTemplate.objects.filter(task_type="speaking_coach").update(
        system_prompt=SPEAKING_COACH_SYSTEM_PROMPT
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0007_seed_listening_speaking_toefl_prompts"),
    ]

    operations = [
        migrations.RunPython(update_speaking_prompts, migrations.RunPython.noop),
    ]
