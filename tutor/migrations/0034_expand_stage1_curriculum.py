from django.db import migrations


def expand_stage1_curriculum(apps, schema_editor):
    LearningGoal = apps.get_model("tutor", "LearningGoal")
    LessonTopic = apps.get_model("tutor", "LessonTopic")

    from tutor.learning_journey import (
        STAGE1_CATEGORIES,
        STAGE1_CURRICULUM,
        STAGE1_LEVELS,
        STAGE1_SLUG,
        _slugify_title,
    )

    LearningGoal.objects.filter(slug=STAGE1_SLUG).update(
        name="Stage 1: B1 → B2 Academic English / TOEFL 80+",
        description=(
            "B1 grammar foundation (12 tenses), core accuracy, B2 academic sentence control, "
            "and TOEFL 80+ readiness practice."
        ),
    )

    active_slugs = set()
    for order, ((title, description), category, level) in enumerate(
        zip(STAGE1_CURRICULUM, STAGE1_CATEGORIES, STAGE1_LEVELS, strict=True),
        start=1,
    ):
        slug = _slugify_title(title)
        active_slugs.add(slug)
        LessonTopic.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": description,
                "stage_slug": STAGE1_SLUG,
                "category": category,
                "level": level,
                "order": order,
                "is_active": True,
            },
        )

    LessonTopic.objects.filter(stage_slug=STAGE1_SLUG).exclude(slug__in=active_slugs).update(
        is_active=False
    )


def revert_stage1_curriculum(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0033_seed_gemini_prompts"),
    ]

    operations = [
        migrations.RunPython(expand_stage1_curriculum, revert_stage1_curriculum),
    ]
