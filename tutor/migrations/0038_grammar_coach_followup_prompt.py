from django.db import migrations


def update_grammar_coach_followup_prompt(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.grammar_coach import GRAMMAR_COACH_TEMPLATES

    for template in GRAMMAR_COACH_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0037_lesson_quiz_questions"),
    ]

    operations = [
        migrations.RunPython(update_grammar_coach_followup_prompt, migrations.RunPython.noop),
    ]
