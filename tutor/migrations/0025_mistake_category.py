from django.db import migrations, models

from tutor.utils.mistake_classification import classify_mistake


def backfill_mistake_categories(apps, schema_editor):
    Mistake = apps.get_model("tutor", "Mistake")
    for mistake in Mistake.objects.all().iterator():
        mistake.category = classify_mistake(
            mistake.wrong_text,
            mistake.correct_text,
            mistake.reason,
            mistake.track,
        )
        mistake.save(update_fields=["category"])


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0024_seed_writing_edit_generate_prompt"),
    ]

    operations = [
        migrations.AddField(
            model_name="mistake",
            name="category",
            field=models.CharField(db_index=True, default="other", max_length=40),
        ),
        migrations.RunPython(backfill_mistake_categories, migrations.RunPython.noop),
    ]
