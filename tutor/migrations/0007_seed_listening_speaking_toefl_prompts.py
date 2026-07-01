from django.db import migrations


def seed_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.listening_coach import LISTENING_COACH_TEMPLATES
    from tutor.prompts.speaking_coach import SPEAKING_COACH_TEMPLATES
    from tutor.prompts.toefl import TOEFL_TEMPLATES

    for template in [
        *LISTENING_COACH_TEMPLATES,
        *SPEAKING_COACH_TEMPLATES,
        *TOEFL_TEMPLATES,
    ]:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults=template,
        )


def unseed_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(
        task_type__in=[
            "listening_coach",
            "speaking_coach",
            "toefl_writing",
            "toefl_speaking",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0006_studyplan_dailyprogress"),
    ]

    operations = [
        migrations.RunPython(seed_prompts, unseed_prompts),
    ]
