from django.db import migrations, models


def populate_lesson_quizzes(apps, schema_editor):
    from tutor.lesson_quiz_bank import populate_all_topic_quizzes

    populate_all_topic_quizzes()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0036_update_speaking_evaluator_prompt"),
    ]

    operations = [
        migrations.AddField(
            model_name="lessontopic",
            name="quiz_questions_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(populate_lesson_quizzes, migrations.RunPython.noop),
    ]
