from django.db import migrations, models
import django.db.models.deletion


def seed_goals_and_curriculum(apps, schema_editor):
    LearningGoal = apps.get_model("tutor", "LearningGoal")
    LessonTopic = apps.get_model("tutor", "LessonTopic")

    from tutor.learning_journey import (
        STAGE1_CURRICULUM,
        STAGE1_CATEGORIES,
        STAGE1_LEVELS,
        STAGE1_SLUG,
        STAGE2_CURRICULUM,
        STAGE2_CATEGORIES,
        STAGE2_LEVELS,
        STAGE2_SLUG,
        _slugify_title,
    )

    goal1, _ = LearningGoal.objects.update_or_create(
        slug=STAGE1_SLUG,
        defaults={
            "name": "B2 Academic English / TOEFL 80+ Readiness",
            "description": (
                "Build B2 academic English ability and TOEFL 80+ readiness through "
                "grammar accuracy, academic vocabulary, reading, listening, speaking, "
                "writing, and mistake repair."
            ),
            "entry_level": "B1",
            "target_level": "B2",
            "target_toefl_score": 80,
            "order": 1,
            "is_default": True,
            "stage_number": 1,
        },
    )
    LearningGoal.objects.update_or_create(
        slug=STAGE2_SLUG,
        defaults={
            "name": "Full Academic English / TOEFL 100+ Readiness",
            "description": (
                "Advanced academic English and TOEFL 100+ preparation with high-level "
                "reading, lecture listening, integrated writing, fluent speaking, and "
                "advanced academic vocabulary."
            ),
            "entry_level": "B2",
            "target_level": "C1 Academic",
            "target_toefl_score": 100,
            "order": 2,
            "is_default": False,
            "stage_number": 2,
            "unlocks_after": goal1,
        },
    )

    for order, ((title, description), category, level) in enumerate(
        zip(STAGE1_CURRICULUM, STAGE1_CATEGORIES, STAGE1_LEVELS, strict=True),
        start=1,
    ):
        slug = _slugify_title(title)
        if title == "Common learner mistakes":
            slug = "common-persian-speaker-grammar-mistakes"
        if title == "Modal verbs":
            slug = "modal-verbs-should-must-have-to"
        if title == "Conditionals 0/1/2":
            slug = "conditionals-type-0-1-2"
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

    for order, ((title, description), category, level) in enumerate(
        zip(STAGE2_CURRICULUM, STAGE2_CATEGORIES, STAGE2_LEVELS, strict=True),
        start=1,
    ):
        LessonTopic.objects.update_or_create(
            slug=_slugify_title(title),
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
        ("tutor", "0029_update_speaking_coach_prompt"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearningGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(unique=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("entry_level", models.CharField(max_length=20)),
                ("target_level", models.CharField(max_length=40)),
                ("target_toefl_score", models.PositiveIntegerField()),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_default", models.BooleanField(default=False)),
                ("stage_number", models.PositiveSmallIntegerField(default=1)),
                (
                    "unlocks_after",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="unlocked_goals",
                        to="tutor.learninggoal",
                    ),
                ),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.AddField(
            model_name="lessontopic",
            name="stage_slug",
            field=models.CharField(db_index=True, default="b2_toefl_80", max_length=80),
        ),
        migrations.CreateModel(
            name="UserLearningJourney",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage2_unlocked", models.BooleanField(default=False)),
                ("stage1_completed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "current_goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="active_users",
                        to="tutor.learninggoal",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learning_journey",
                        to="auth.user",
                    ),
                ),
            ],
        ),
        migrations.RunPython(seed_goals_and_curriculum, migrations.RunPython.noop),
    ]
