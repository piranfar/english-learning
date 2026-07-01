from django.db import migrations, models
import django.db.models.deletion


def seed_reading_generate_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompts.reading_coach import READING_GENERATE_TEMPLATES, READING_SIMULATION_TEMPLATES

    for template in [*READING_GENERATE_TEMPLATES, *READING_SIMULATION_TEMPLATES]:
        PromptTemplate.objects.update_or_create(
            task_type=template["task_type"],
            provider=template["provider"],
            defaults={
                "title": template["title"],
                "model_name": template["model_name"],
                "system_prompt": template["system_prompt"],
                "temperature": template["temperature"],
                "max_tokens": template["max_tokens"],
                "is_active": template["is_active"],
            },
        )


def unseed_reading_generate_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(task_type__in=["reading_generate", "reading_simulation"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0030_learning_journey"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReadingSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=300)),
                ("level", models.CharField(max_length=20)),
                ("stage", models.CharField(blank=True, max_length=40)),
                ("lesson_focus", models.CharField(blank=True, max_length=60)),
                ("topic", models.CharField(blank=True, max_length=60)),
                (
                    "mode",
                    models.CharField(
                        choices=[("generated", "Generated practice"), ("simulation", "TOEFL-style simulation")],
                        default="generated",
                        max_length=20,
                    ),
                ),
                ("simulation_type", models.CharField(blank=True, max_length=40)),
                ("passage", models.TextField()),
                ("questions_json", models.JSONField(default=list)),
                ("target_vocabulary", models.JSONField(blank=True, default=list)),
                ("estimated_time_minutes", models.PositiveSmallIntegerField(default=15)),
                ("score_percent", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reading_sessions",
                        to="auth.user",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ReadingQuestionAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_id", models.CharField(max_length=40)),
                ("selected_answer", models.TextField(blank=True)),
                ("correct_answer", models.TextField()),
                ("is_correct", models.BooleanField(default=False)),
                ("question_type", models.CharField(blank=True, max_length=40)),
                ("mistake_category", models.CharField(blank=True, max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="tutor.readingsession",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.RunPython(seed_reading_generate_prompts, unseed_reading_generate_prompts),
    ]
