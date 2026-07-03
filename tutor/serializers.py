from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    track = serializers.CharField()
    session_id = serializers.IntegerField(required=False, allow_null=True)
    provider = serializers.CharField(required=False, allow_blank=True)
    scenario = serializers.CharField(required=False, allow_blank=True)


class ListeningGenerateSerializer(serializers.Serializer):
    transcript = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)
    transcription_provider = serializers.CharField(required=False, allow_blank=True)


class TTSSerializer(serializers.Serializer):
    text = serializers.CharField()
    provider = serializers.CharField(required=False, allow_blank=True)


class ToeflPromptSerializer(serializers.Serializer):
    task_type = serializers.ChoiceField(choices=["toefl_writing", "toefl_speaking"])
    provider = serializers.CharField(required=False, allow_blank=True)


class VocabCreateSerializer(serializers.Serializer):
    word = serializers.CharField()
    definition = serializers.CharField(required=False, allow_blank=True)
    example = serializers.CharField(required=False, allow_blank=True)
    persian_meaning = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)


class VocabReviewSerializer(serializers.Serializer):
    quality = serializers.IntegerField(min_value=0, max_value=5)


class ReadingAnalyzeSerializer(serializers.Serializer):
    passage = serializers.CharField()
    provider = serializers.CharField(required=False, allow_blank=True)


class ReadingQuizGenerateSerializer(serializers.Serializer):
    passage = serializers.CharField()
    level = serializers.ChoiceField(choices=["B1", "B2", "TOEFL"], default="B1")
    question_focus = serializers.ChoiceField(
        choices=[
            "mixed",
            "main_idea",
            "detail",
            "inference",
            "vocabulary_in_context",
            "sentence_simplification",
        ],
        default="mixed",
    )
    provider = serializers.CharField(required=False, allow_blank=True)


class ReadingQuizSubmitSerializer(serializers.Serializer):
    quiz_id = serializers.CharField()
    answers = serializers.DictField(child=serializers.IntegerField(min_value=0, max_value=3))


class ReadingGenerateSerializer(serializers.Serializer):
    level = serializers.ChoiceField(
        choices=["A2", "B1", "B2", "C1 Academic"],
        default="B1",
    )
    stage = serializers.ChoiceField(
        choices=["b2_toefl_80", "academic_toefl_100"],
        default="b2_toefl_80",
    )
    topic = serializers.ChoiceField(
        choices=[
            "Academic",
            "Science",
            "Health",
            "University Life",
            "Technology",
            "Society",
            "Random",
        ],
        default="Academic",
    )
    lesson_focus = serializers.ChoiceField(
        choices=[
            "current_lesson",
            "articles",
            "prepositions",
            "passive_voice",
            "present_perfect",
            "academic_linking_words",
            "academic_sentence_structure",
            "vocabulary_in_context",
            "none",
        ],
        default="current_lesson",
    )
    question_focus = serializers.ChoiceField(
        choices=[
            "mixed",
            "main_idea",
            "detail",
            "inference",
            "vocabulary_in_context",
            "sentence_function",
            "rhetorical_purpose",
        ],
        default="mixed",
    )
    length = serializers.ChoiceField(
        choices=["short", "medium", "long", "toefl_style"],
        default="medium",
    )
    simulation_type = serializers.ChoiceField(
        choices=["", "complete_the_words", "daily_life_reading", "academic_passage"],
        required=False,
        allow_blank=True,
        default="",
    )
    reading_mode = serializers.ChoiceField(
        choices=["general", "toefl_2026", "classic_toefl"],
        required=False,
        default="general",
    )
    provider = serializers.CharField(required=False, allow_blank=True)


class ReadingSubmitSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    answers = serializers.DictField()


class ListeningQuizGenerateSerializer(serializers.Serializer):
    transcript = serializers.CharField(required=False, allow_blank=True)
    level = serializers.ChoiceField(choices=["B1", "B2", "TOEFL"], default="B1")
    question_focus = serializers.ChoiceField(
        choices=[
            "mixed",
            "main_idea",
            "detail",
            "inference",
            "speaker_purpose",
            "vocabulary_phrase",
        ],
        default="mixed",
    )
    provider = serializers.CharField(required=False, allow_blank=True)
    transcription_provider = serializers.CharField(required=False, allow_blank=True)


class ListeningQuizSubmitSerializer(serializers.Serializer):
    quiz_id = serializers.CharField()
    answers = serializers.DictField(child=serializers.IntegerField(min_value=0, max_value=3))


class ListeningPracticeGenerateSerializer(serializers.Serializer):
    level = serializers.ChoiceField(
        choices=["A2", "B1", "B2", "C1 Academic"],
        default="B1",
    )
    stage = serializers.ChoiceField(
        choices=["b2_toefl_80", "academic_toefl_100"],
        default="b2_toefl_80",
    )
    listening_type = serializers.ChoiceField(
        choices=[
            "academic_mini_lecture",
            "campus_conversation",
            "daily_academic_life",
            "toefl_style_lecture",
            "toefl_style_conversation",
        ],
        default="academic_mini_lecture",
    )
    topic = serializers.ChoiceField(
        choices=[
            "Science",
            "Health",
            "University Life",
            "Technology",
            "Society",
            "Academic Skills",
            "Random",
        ],
        default="Random",
    )
    lesson_focus = serializers.ChoiceField(
        choices=[
            "current_lesson",
            "articles",
            "prepositions",
            "passive_voice",
            "present_perfect",
            "academic_linking_words",
            "academic_vocabulary",
            "none",
        ],
        default="current_lesson",
    )
    length = serializers.ChoiceField(
        choices=["short", "medium", "toefl_style"],
        default="medium",
    )
    speed = serializers.ChoiceField(
        choices=["slow", "normal", "toefl_like"],
        default="normal",
    )
    provider = serializers.CharField(required=False, allow_blank=True)


class ListeningPracticeSubmitSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    answers = serializers.DictField()


from tutor.utils.text_validation import is_meaningful_writing_text


class WritingEditSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True)
    edit_strength = serializers.CharField(required=False, default="standard")
    target_style = serializers.CharField(required=False, default="simple_american_english")
    language_level = serializers.CharField(required=False, default="normal")
    ai_provider = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)

    def validate_text(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError(
                "Please write or paste a paragraph first."
            )
        if not is_meaningful_writing_text(cleaned):
            raise serializers.ValidationError(
                "Please generate or paste a real English paragraph first."
            )
        return cleaned


class WritingRevisionCompareSerializer(serializers.Serializer):
    original_answer = serializers.CharField()
    revised_answer = serializers.CharField()
    prompt = serializers.CharField(required=False, allow_blank=True, default="")
    provider = serializers.CharField(required=False, allow_blank=True)

    def validate_original_answer(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Original answer is required.")
        return cleaned

    def validate_revised_answer(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Revised answer is required.")
        return cleaned


class WritingEditGenerateSerializer(serializers.Serializer):
    target_style = serializers.CharField(required=False, default="simple_american_english")
    language_level = serializers.CharField(required=False, default="normal")
    ai_provider = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)


class ParaphraseGenerateSerializer(serializers.Serializer):
    target_level = serializers.CharField(required=False, default="simple_american_english")
    difficulty = serializers.CharField(required=False, default="easy")
    text_type = serializers.CharField(required=False, default="one_sentence")
    language_level = serializers.CharField(required=False, default="normal")
    ai_provider = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)


class ParaphraseCheckSerializer(serializers.Serializer):
    target_level = serializers.CharField(required=False, default="simple_american_english")
    language_level = serializers.CharField(required=False, default="normal")
    original_text = serializers.CharField(allow_blank=True)
    learner_paraphrase = serializers.CharField(allow_blank=True)
    ai_provider = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)

    def validate_original_text(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError(
                "Please generate or enter original text first."
            )
        return cleaned

    def validate_learner_paraphrase(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError(
                "Please write your paraphrase first."
            )
        return cleaned


class PlanItemUpdateSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    completed = serializers.BooleanField()


class LessonStartSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    provider = serializers.CharField(required=False, allow_blank=True, default="ollama")


class LessonCompleteSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    score = serializers.IntegerField(min_value=0, max_value=100, default=80)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class LessonQuizSubmitSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    answers = serializers.DictField(child=serializers.IntegerField())


class AdminPromptUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    system_prompt = serializers.CharField(required=False, allow_blank=True)
    model_name = serializers.CharField(required=False)
    temperature = serializers.FloatField(required=False)
    max_tokens = serializers.IntegerField(required=False, min_value=1)
    is_active = serializers.BooleanField(required=False)


class ShadowingAttemptSerializer(serializers.Serializer):
    transcript = serializers.CharField()


class ShadowingFromSentencesSerializer(serializers.Serializer):
    sentences = serializers.ListField(
        child=serializers.CharField(max_length=500),
        min_length=1,
        max_length=8,
    )


class VocabQuizMistakeSerializer(serializers.Serializer):
    word = serializers.CharField()
    wrong_answer = serializers.CharField(required=False, allow_blank=True, default="")
    meaning_en = serializers.CharField(required=False, allow_blank=True, default="")
    meaning_fa = serializers.CharField(required=False, allow_blank=True, default="")
    example = serializers.CharField(required=False, allow_blank=True, default="")
    quiz_mode = serializers.CharField(required=False, allow_blank=True, default="")


class VocabAddRandomSerializer(serializers.Serializer):
    category = serializers.CharField()
    count = serializers.IntegerField(min_value=1, max_value=50, default=10)
    cefr_level = serializers.CharField(required=False, allow_blank=True)
