from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, default="B1")
    goal = models.TextField(blank=True)
    weak_areas = models.JSONField(default=list)
    native_language = models.CharField(max_length=50, default="Persian")

    def __str__(self):
        return f"{self.user.username} ({self.level})"


class LearningGoal(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    entry_level = models.CharField(max_length=20)
    target_level = models.CharField(max_length=40)
    target_toefl_score = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)
    unlocks_after = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unlocked_goals",
    )
    is_default = models.BooleanField(default=False)
    stage_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class UserLearningJourney(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_journey",
    )
    current_goal = models.ForeignKey(
        LearningGoal,
        on_delete=models.PROTECT,
        related_name="active_users",
    )
    stage2_unlocked = models.BooleanField(default=False)
    stage1_completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} → {self.current_goal.slug}"


class PromptTemplate(models.Model):
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    system_prompt = models.TextField()
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("task_type", "provider")

    def __str__(self):
        return self.title


class PracticeSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    track = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.track} ({self.created_at:%Y-%m-%d})"


class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(
        PracticeSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class Mistake(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wrong_text = models.TextField()
    correct_text = models.TextField()
    reason = models.TextField()
    persian_explanation = models.TextField(blank=True)
    review_sentence = models.TextField(blank=True)
    track = models.CharField(max_length=100)
    category = models.CharField(
        max_length=40,
        default="other",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    next_review_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.wrong_text[:30]} → {self.correct_text[:30]}"


class VocabularyItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    word = models.CharField(max_length=200)
    definition = models.TextField()
    example = models.TextField(blank=True)
    persian_meaning = models.TextField(blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    cefr_level = models.CharField(max_length=10, blank=True)
    category = models.CharField(max_length=80, blank=True)
    collocations = models.JSONField(default=list, blank=True)
    shadowing_sentence = models.TextField(blank=True)
    common_mistake = models.TextField(blank=True)
    correction = models.TextField(blank=True)
    ease_factor = models.FloatField(default=2.5)
    interval = models.IntegerField(default=1)
    repetitions = models.IntegerField(default=0)
    next_review_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "word"],
                name="unique_vocab_item_per_user_word",
            )
        ]

    def __str__(self):
        return self.word


class LessonTopic(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=10, default="B1")
    category = models.CharField(max_length=80, default="grammar")
    stage_slug = models.CharField(max_length=80, default="b2_toefl_80", db_index=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class LessonProgress(models.Model):
    STATUS_NOT_STARTED = "not_started"
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, "Not started"),
        (STATUS_STARTED, "Started"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_NEEDS_REVIEW, "Needs review"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.ForeignKey(LessonTopic, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_STARTED,
    )
    last_practiced = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "topic")

    def __str__(self):
        return f"{self.user.username} — {self.topic.title} ({self.status})"


class StudyPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    items = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.username} plan {self.date}"


class DailyProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    minutes_per_track = models.JSONField(default=dict)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        status = "done" if self.completed else "pending"
        return f"{self.user.username} progress {self.date} ({status})"


class ShadowingItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shadowing_items",
    )
    target_text = models.TextField()
    persian_meaning = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.target_text[:60]


class ShadowingAttempt(models.Model):
    item = models.ForeignKey(
        ShadowingItem, on_delete=models.CASCADE, related_name="attempts"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transcript = models.TextField()
    similarity_score = models.PositiveSmallIntegerField(default=0)
    missing_words = models.JSONField(default=list)
    extra_words = models.JSONField(default=list)
    changed_words = models.JSONField(default=list)
    feedback = models.TextField(blank=True)
    persian_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.similarity_score}% on item {self.item_id}"


class ReadingSession(models.Model):
    MODE_GENERATED = "generated"
    MODE_SIMULATION = "simulation"
    MODE_CHOICES = [
        (MODE_GENERATED, "Generated practice"),
        (MODE_SIMULATION, "TOEFL-style simulation"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_sessions",
    )
    title = models.CharField(max_length=300)
    level = models.CharField(max_length=20)
    stage = models.CharField(max_length=40, blank=True)
    lesson_focus = models.CharField(max_length=60, blank=True)
    topic = models.CharField(max_length=60, blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_GENERATED)
    simulation_type = models.CharField(max_length=40, blank=True)
    passage = models.TextField()
    questions_json = models.JSONField(default=list)
    target_vocabulary = models.JSONField(default=list, blank=True)
    estimated_time_minutes = models.PositiveSmallIntegerField(default=15)
    score_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.title[:50]}"


class ReadingQuestionAttempt(models.Model):
    session = models.ForeignKey(
        ReadingSession,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    question_id = models.CharField(max_length=40)
    selected_answer = models.TextField(blank=True)
    correct_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    question_type = models.CharField(max_length=40, blank=True)
    mistake_category = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        status = "correct" if self.is_correct else "wrong"
        return f"{self.session_id} {self.question_id} ({status})"


class ListeningSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listening_sessions",
    )
    title = models.CharField(max_length=300)
    level = models.CharField(max_length=20)
    stage = models.CharField(max_length=40, blank=True)
    listening_type = models.CharField(max_length=40, blank=True)
    topic = models.CharField(max_length=60, blank=True)
    lesson_focus = models.CharField(max_length=60, blank=True)
    transcript = models.TextField()
    questions_json = models.JSONField(default=list)
    target_vocabulary = models.JSONField(default=list, blank=True)
    shadowing_sentences = models.JSONField(default=list, blank=True)
    estimated_duration_seconds = models.PositiveIntegerField(default=180)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.title[:50]}"


class ListeningQuestionAttempt(models.Model):
    session = models.ForeignKey(
        ListeningSession,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    question_id = models.CharField(max_length=40)
    selected_answer = models.TextField(blank=True)
    correct_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    question_type = models.CharField(max_length=40, blank=True)
    mistake_category = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        status = "correct" if self.is_correct else "wrong"
        return f"{self.session_id} {self.question_id} ({status})"


class VocabularySeed(models.Model):
    word = models.CharField(max_length=200)
    lemma = models.CharField(max_length=200, blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    cefr_level = models.CharField(max_length=10, blank=True)
    category = models.CharField(max_length=80, blank=True)
    definition = models.TextField(blank=True)
    persian_meaning = models.TextField(blank=True)
    example = models.TextField(blank=True)
    source = models.CharField(max_length=200, blank=True)
    frequency_rank = models.IntegerField(null=True, blank=True)
    collocations = models.JSONField(default=list, blank=True)
    shadowing_sentence = models.TextField(blank=True)
    common_mistake = models.TextField(blank=True)
    correction = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["frequency_rank", "word"]
        indexes = [
            models.Index(fields=["cefr_level"]),
            models.Index(fields=["category"]),
            models.Index(fields=["word"]),
            models.Index(fields=["approved"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["word", "category", "part_of_speech"],
                name="unique_vocab_seed_word_category_pos",
            )
        ]

    def __str__(self):
        return self.word
