from django.db import migrations


def seed_stage2_topics(apps, schema_editor):
    LessonTopic = apps.get_model("tutor", "LessonTopic")

    from tutor.learning_journey import (
        STAGE2_CATEGORIES,
        STAGE2_CURRICULUM,
        STAGE2_LEVELS,
        STAGE2_SLUG,
        _slugify_title,
    )

    for order, ((title, description), category, level) in enumerate(
        zip(STAGE2_CURRICULUM, STAGE2_CATEGORIES, STAGE2_LEVELS, strict=True),
        start=1,
    ):
        slug = _slugify_title(title, stage_slug=STAGE2_SLUG)
        LessonTopic.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": description,
                "stage_slug": STAGE2_SLUG,
                "category": category,
                "level": level,
                "order": order,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0034_expand_stage1_curriculum"),
    ]

    operations = [
        migrations.RunPython(seed_stage2_topics, migrations.RunPython.noop),
    ]
