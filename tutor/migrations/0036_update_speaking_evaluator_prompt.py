from django.db import migrations


def update_speaking_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.speaking_coach import SPEAKING_COACH_SYSTEM_PROMPT

    PromptTemplate.objects.filter(task_type="speaking_coach").update(
        system_prompt=SPEAKING_COACH_SYSTEM_PROMPT,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0035_fix_stage2_topic_slugs"),
    ]

    operations = [
        migrations.RunPython(update_speaking_prompts, migrations.RunPython.noop),
    ]
