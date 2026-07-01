from django.db import migrations


def seed_grammar_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.grammar_coach import GRAMMAR_COACH_TEMPLATES

    for template in GRAMMAR_COACH_TEMPLATES:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


def unseed_grammar_coach_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(task_type="grammar_coach").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_grammar_coach_prompts, unseed_grammar_coach_prompts),
    ]
