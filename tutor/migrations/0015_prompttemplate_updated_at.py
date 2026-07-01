from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0014_update_grammar_coach_prompt"),
    ]

    operations = [
        migrations.AddField(
            model_name="prompttemplate",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterUniqueTogether(
            name="prompttemplate",
            unique_together={("task_type", "provider")},
        ),
    ]
