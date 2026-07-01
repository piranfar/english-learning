from django.db import migrations


def seed_gemini_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    from tutor.prompt_defaults import GEMINI_DEFAULT_TEMPLATES

    for template in GEMINI_DEFAULT_TEMPLATES:
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

    gemini_model = "gemini-2.0-flash"
    for src in PromptTemplate.objects.filter(provider="openai"):
        title = src.title.replace("(OpenAI)", "(Gemini)")
        if title == src.title and "(Gemini)" not in title:
            title = f"{src.title} (Gemini)"
        PromptTemplate.objects.update_or_create(
            task_type=src.task_type,
            provider="gemini",
            defaults={
                "title": title,
                "model_name": gemini_model,
                "system_prompt": src.system_prompt,
                "temperature": src.temperature,
                "max_tokens": src.max_tokens,
                "is_active": src.is_active,
            },
        )


def unseed_gemini_prompts(apps, schema_editor):
    PromptTemplate = apps.get_model("tutor", "PromptTemplate")
    PromptTemplate.objects.filter(provider="gemini").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tutor", "0032_listening_sessions"),
    ]

    operations = [
        migrations.RunPython(seed_gemini_prompts, unseed_gemini_prompts),
    ]
