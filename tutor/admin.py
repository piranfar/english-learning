from django.contrib import admin

from .models import (
    DailyProgress,
    LessonProgress,
    LessonTopic,
    Message,
    Mistake,
    PracticeSession,
    PromptTemplate,
    ShadowingAttempt,
    ShadowingItem,
    StudyPlan,
    UserProfile,
    VocabularyItem,
    VocabularySeed,
)


@admin.register(LessonTopic)
class LessonTopicAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "level", "category", "order", "is_active")
    list_filter = ("level", "category", "is_active")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "status", "score", "last_practiced")
    list_filter = ("status", "topic")
    search_fields = ("user__username", "topic__title", "notes")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "level", "goal", "native_language", "weak_areas")


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "task_type",
        "provider",
        "model_name",
        "temperature",
        "max_tokens",
        "is_active",
        "updated_at",
    )
    list_filter = ("task_type", "provider", "is_active")
    list_editable = ("model_name", "temperature", "max_tokens", "is_active")
    search_fields = ("title", "task_type", "model_name", "system_prompt")
    ordering = ("task_type", "provider")


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "track", "created_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "content", "created_at")


@admin.register(Mistake)
class MistakeAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "wrong_text",
        "correct_text",
        "track",
        "category",
        "created_at",
        "next_review_date",
    )


@admin.register(VocabularyItem)
class VocabularyItemAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "word",
        "definition",
        "ease_factor",
        "interval",
        "repetitions",
        "next_review_date",
        "created_at",
    )


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "created_at")


@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "completed", "minutes_per_track")


@admin.register(ShadowingItem)
class ShadowingItemAdmin(admin.ModelAdmin):
    list_display = ("target_text", "persian_meaning", "sort_order", "is_active", "user")
    list_filter = ("is_active",)


@admin.register(ShadowingAttempt)
class ShadowingAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "similarity_score", "created_at")


@admin.register(VocabularySeed)
class VocabularySeedAdmin(admin.ModelAdmin):
    list_display = (
        "word",
        "cefr_level",
        "category",
        "part_of_speech",
        "source",
        "approved",
    )
    list_filter = ("cefr_level", "category", "part_of_speech", "source", "approved")
    search_fields = ("word", "definition", "persian_meaning", "example")
    actions = ["mark_approved", "mark_not_approved"]

    @admin.action(description="Mark selected seeds as approved")
    def mark_approved(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} seed(s) marked as approved.")

    @admin.action(description="Mark selected seeds as not approved")
    def mark_not_approved(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} seed(s) marked as not approved.")
