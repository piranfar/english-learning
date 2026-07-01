from django.db import migrations


def seed_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.writing_coach import (
        VOCAB_BUILDER_TEMPLATES,
        WRITING_COACH_TEMPLATES,
    )

    for template in [*WRITING_COACH_TEMPLATES, *VOCAB_BUILDER_TEMPLATES]:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


def unseed_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(
        task_type__in=["writing_coach", "vocab_builder"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0002_seed_grammar_coach_prompts"),
    ]

    operations = [
        migrations.RunPython(seed_prompts, unseed_prompts),
    ]
