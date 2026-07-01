from datetime import date

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from tutor.analytics import get_progress_analytics
from tutor.listening_practice import (
    gather_listening_context,
    generate_listening_practice,
    score_listening_session,
)
from tutor.reading_practice import (
    gather_reading_context,
    generate_reading_practice,
    score_reading_session,
)
from tutor.throttling import AIUserRateThrottle
from tutor.utils.provider_access import resolve_user_provider
from tutor.utils.uploads import AudioUploadTooLarge, validate_audio_upload
from tutor.dashboard_coach import build_coach_focus, progress_by_skill
from tutor.learning_journey import (
    STAGE1_MODULES,
    STAGE1_SLUG,
    STAGE2_SLUG,
    build_journey_summary,
    build_readiness_report,
    ensure_user_on_accessible_goal,
    get_or_create_journey,
    topic_is_locked,
)
from tutor.permissions import IsStaffUser
from tutor.prompt_defaults import PROVIDER_NOTES, get_default_template
from tutor.ai.ollama_client import fetch_ollama_tags, missing_recommended_models
from tutor.plan import (
    calculate_streak,
    count_due_reviewable_mistakes,
    due_vocab_queryset,
    empty_plan_response,
    filter_reviewable_plan_items,
    generate_today_plan,
    get_today_plan,
    plan_response_payload,
    sync_progress_completion,
    update_plan_item,
)
from tutor.srs import sm2
from tutor.shadowing import compare_shadowing
from tutor.transcription.factory import transcribe
from tutor.services.lesson_recommendation import (
    GRAMMAR_TRACK,
    build_starter_message,
    build_yesterday_summary,
    get_lesson_recommendation,
    mistake_to_review_item,
    recent_mistakes,
    topic_to_dict,
)
from tutor.vocab_constants import DECK_CATEGORIES, VOCAB_CATEGORY_LABELS
from tutor.voice import synthesize_speech, transcribe_audio

from tutor.models import (
    LessonProgress,
    LessonTopic,
    Mistake,
    PracticeSession,
    PromptTemplate,
    ReadingSession,
    ShadowingAttempt,
    ShadowingItem,
    VocabularyItem,
    VocabularySeed,
)
from .serializers import (
    AdminPromptUpdateSerializer,
    ChatRequestSerializer,
    LessonCompleteSerializer,
    LessonStartSerializer,
    ListeningGenerateSerializer,
    ListeningPracticeGenerateSerializer,
    ListeningPracticeSubmitSerializer,
    ListeningQuizGenerateSerializer,
    ListeningQuizSubmitSerializer,
    PlanItemUpdateSerializer,
    ReadingAnalyzeSerializer,
    ReadingGenerateSerializer,
    ReadingQuizGenerateSerializer,
    ReadingQuizSubmitSerializer,
    ReadingSubmitSerializer,
    ShadowingAttemptSerializer,
    ToeflPromptSerializer,
    TTSSerializer,
    VocabAddRandomSerializer,
    VocabCreateSerializer,
    VocabQuizMistakeSerializer,
    VocabReviewSerializer,
    WritingEditSerializer,
    WritingEditGenerateSerializer,
    WritingRevisionCompareSerializer,
    ParaphraseGenerateSerializer,
    ParaphraseCheckSerializer,
)
from .services import (
    analyze_listening,
    analyze_reading,
    generate_listening_quiz,
    generate_reading_quiz,
    score_listening_quiz,
    score_reading_quiz,
    format_speaking_evaluation_message,
    generate_from_template,
    get_user_profile,
    parse_vocab_json,
    run_task,
    run_writing_edit,
    run_writing_edit_generate,
    run_paraphrase_generate,
    run_paraphrase_check,
    run_writing_revision_compare,
)
from tutor.prompts.toefl import (
    TOEFL_SPEAKING_PROMPT_REQUEST,
    TOEFL_WRITING_PROMPT_REQUEST,
)


def lesson_progress_to_dict(progress: LessonProgress) -> dict:
    return {
        "topic_id": progress.topic_id,
        "status": progress.status,
        "score": progress.score,
        "notes": progress.notes,
        "last_practiced": (
            progress.last_practiced.isoformat() if progress.last_practiced else None
        ),
    }


def mark_lesson_started(user, topic: LessonTopic) -> LessonProgress:
    progress, created = LessonProgress.objects.get_or_create(
        user=user,
        topic=topic,
        defaults={"status": LessonProgress.STATUS_STARTED},
    )
    if not created and progress.status in {
        LessonProgress.STATUS_NOT_STARTED,
        LessonProgress.STATUS_COMPLETED,
    }:
        progress.status = LessonProgress.STATUS_STARTED
    progress.last_practiced = timezone.now()
    progress.save(update_fields=["status", "last_practiced"])
    return progress


def build_topic_starter_message(user, topic: LessonTopic) -> str:
    review_items = [
        mistake_to_review_item(mistake)
        for mistake in recent_mistakes(user, days=7, limit=3)
    ]
    return build_starter_message(
        topic,
        build_yesterday_summary(user),
        review_items,
    )


def _read_validated_audio(uploaded_file):
    """Validate size then read audio bytes; return (bytes, error_response)."""
    try:
        validate_audio_upload(uploaded_file)
    except AudioUploadTooLarge as exc:
        return None, Response(
            {"detail": str(exc)},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    return uploaded_file.read(), None


class PromptsListView(APIView):
    def get(self, request):
        prompts = PromptTemplate.objects.filter(is_active=True).order_by(
            "task_type", "provider"
        )
        prompt_rows = [
            {
                "id": prompt.id,
                "title": prompt.title,
                "task_type": prompt.task_type,
                "provider": prompt.provider,
                "model_name": prompt.model_name,
                "temperature": prompt.temperature,
                "max_tokens": prompt.max_tokens,
                "is_active": prompt.is_active,
            }
            for prompt in prompts
        ]
        return Response(
            {
                "prompts": prompt_rows,
                "task_types": sorted({prompt.task_type for prompt in prompts}),
                "providers": sorted({prompt.provider for prompt in prompts}),
            }
        )


def prompt_admin_dict(prompt: PromptTemplate) -> dict:
    return {
        "id": prompt.id,
        "title": prompt.title,
        "task_type": prompt.task_type,
        "provider": prompt.provider,
        "provider_note": PROVIDER_NOTES.get(prompt.provider, ""),
        "model_name": prompt.model_name,
        "system_prompt": prompt.system_prompt,
        "temperature": prompt.temperature,
        "max_tokens": prompt.max_tokens,
        "is_active": prompt.is_active,
        "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
        "is_empty": not (prompt.system_prompt or "").strip(),
    }


class AdminPromptsListView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        prompts = PromptTemplate.objects.all().order_by("task_type", "provider")
        return Response(
            {
                "prompts": [prompt_admin_dict(p) for p in prompts],
                "provider_notes": PROVIDER_NOTES,
            }
        )


class AdminPromptDetailView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request, prompt_id):
        prompt = get_object_or_404(PromptTemplate, id=prompt_id)
        return Response(prompt_admin_dict(prompt))

    def patch(self, request, prompt_id):
        prompt = get_object_or_404(PromptTemplate, id=prompt_id)
        serializer = AdminPromptUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(prompt, field, value)
        prompt.save()

        return Response(prompt_admin_dict(prompt))


class AdminPromptResetView(APIView):
    permission_classes = [IsStaffUser]

    def post(self, request, prompt_id):
        prompt = get_object_or_404(PromptTemplate, id=prompt_id)
        default = get_default_template(prompt.task_type, prompt.provider)
        if default is None:
            return Response(
                {"detail": "No default template found for this task and provider."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt.title = default.get("title", prompt.title)
        prompt.system_prompt = default.get("system_prompt", "")
        prompt.model_name = default.get("model_name", prompt.model_name)
        prompt.temperature = default.get("temperature", prompt.temperature)
        prompt.max_tokens = default.get("max_tokens", prompt.max_tokens)
        prompt.is_active = default.get("is_active", True)
        prompt.save()

        return Response(prompt_admin_dict(prompt))


class OllamaStatusView(APIView):
    def get(self, request):
        host = settings.OLLAMA_HOST.rstrip("/")
        ok, models, error = fetch_ollama_tags()
        payload = {
            "host": host,
            "ok": ok,
            "models": models if ok else [],
            "missing_recommended_models": missing_recommended_models(models) if ok else [],
        }
        if not ok:
            payload["error"] = error
        return Response(payload)


class MistakesListView(APIView):
    def get(self, request):
        mistakes = Mistake.objects.filter(user=request.user).order_by("-created_at")
        return Response(
            {
                "mistakes": [
                    mistake_to_dict(mistake)
                    for mistake in mistakes
                ]
            }
        )


VOCAB_QUIZ_TRACK = "vocab_quiz"


def mistake_to_dict(mistake: Mistake) -> dict:
    return {
        "id": mistake.id,
        "wrong_text": mistake.wrong_text,
        "correct_text": mistake.correct_text,
        "reason": mistake.reason,
        "persian_explanation": mistake.persian_explanation,
        "review_sentence": mistake.review_sentence,
        "track": mistake.track,
        "category": mistake.category,
        "created_at": mistake.created_at.isoformat(),
        "next_review_date": (
            mistake.next_review_date.isoformat()
            if mistake.next_review_date
            else None
        ),
    }


class VocabQuizMistakeView(APIView):
    """Record a vocabulary quiz wrong answer as a reviewable mistake."""

    def post(self, request):
        serializer = VocabQuizMistakeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        word = serializer.validated_data["word"].strip()
        wrong_answer = (serializer.validated_data.get("wrong_answer") or "").strip()
        meaning_en = (serializer.validated_data.get("meaning_en") or "").strip()
        meaning_fa = (serializer.validated_data.get("meaning_fa") or "").strip()
        example = (serializer.validated_data.get("example") or "").strip()
        quiz_mode = (serializer.validated_data.get("quiz_mode") or "").strip()
        today = date.today()

        from tutor.utils.text_validation import is_meaningful_learner_text, is_meaningful_mistake

        if not is_meaningful_learner_text(word):
            return Response(
                {"detail": "Word does not look like meaningful learner text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        wrong_text = wrong_answer or f"Missed vocabulary word: {word}"
        if not is_meaningful_mistake(wrong_text, word):
            return Response(
                {"detail": "Answer does not look like meaningful learner text."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason_parts = [meaning_en] if meaning_en else []
        if quiz_mode:
            reason_parts.append(f"Quiz: {quiz_mode.replace('_', ' ')}")
        reason = " · ".join(reason_parts) or "Vocabulary quiz practice"

        from tutor.utils.mistake_classification import classify_mistake

        category = classify_mistake(wrong_text, word, reason, VOCAB_QUIZ_TRACK)

        existing = (
            Mistake.objects.filter(
                user=request.user,
                track=VOCAB_QUIZ_TRACK,
                correct_text__iexact=word,
            )
            .order_by("-created_at")
            .first()
        )

        if existing:
            existing.wrong_text = wrong_text
            existing.reason = reason
            existing.category = category
            if meaning_fa:
                existing.persian_explanation = meaning_fa
            if example:
                existing.review_sentence = example
            existing.next_review_date = today
            existing.save(
                update_fields=[
                    "wrong_text",
                    "reason",
                    "category",
                    "persian_explanation",
                    "review_sentence",
                    "next_review_date",
                ]
            )
            mistake = existing
            created = False
        else:
            mistake = Mistake.objects.create(
                user=request.user,
                track=VOCAB_QUIZ_TRACK,
                wrong_text=wrong_text,
                correct_text=word,
                reason=reason,
                category=category,
                persian_explanation=meaning_fa,
                review_sentence=example,
                next_review_date=today,
            )
            created = True

        return Response(
            {**mistake_to_dict(mistake), "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ChatView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        track = serializer.validated_data["track"]
        session_id = serializer.validated_data.get("session_id")
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))
        scenario = serializer.validated_data.get("scenario") or None

        user = request.user

        if session_id:
            try:
                session = PracticeSession.objects.get(id=session_id, user=user)
            except PracticeSession.DoesNotExist:
                return Response(
                    {"detail": "Session not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            session = PracticeSession.objects.create(user=user, track=track)

        try:
            result = run_task(
                track, message, user, session, provider=provider, scenario=scenario
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "reply": result["reply"],
                "corrections": result["corrections"],
                "toefl_feedback": result.get("toefl_feedback"),
                "speaking_feedback": result.get("speaking_feedback"),
                "writing_feedback": result.get("writing_feedback"),
                "session_id": session.id,
            },
            status=status.HTTP_200_OK,
        )


class LessonRecommendationView(APIView):
    def get(self, request):
        return Response(get_lesson_recommendation(request.user))


class LessonTopicsView(APIView):
    def get(self, request):
        ensure_user_on_accessible_goal(request.user)
        journey = get_or_create_journey(request.user)
        topics = LessonTopic.objects.filter(is_active=True).order_by("order", "id")
        progress_rows = {
            row.topic_id: row
            for row in LessonProgress.objects.filter(
                user=request.user,
                topic__in=topics,
            )
        }

        def serialize_topic(topic):
            locked = topic_is_locked(request.user, topic)
            return {
                **topic_to_dict(topic),
                "status": (
                    progress_rows[topic.id].status
                    if topic.id in progress_rows
                    else LessonProgress.STATUS_NOT_STARTED
                ),
                "score": (
                    progress_rows[topic.id].score
                    if topic.id in progress_rows
                    else 0
                ),
                "locked": locked,
            }

        stage1_topics = [serialize_topic(t) for t in topics if t.stage_slug == STAGE1_SLUG]
        stage2_topics = [serialize_topic(t) for t in topics if t.stage_slug == STAGE2_SLUG]

        return Response(
            {
                "current_stage": journey.current_goal.stage_number,
                "current_goal_slug": journey.current_goal.slug,
                "stage2_unlocked": journey.stage2_unlocked,
                "topics": [serialize_topic(topic) for topic in topics],
                "stages": [
                    {
                        "slug": STAGE1_SLUG,
                        "title": "Stage 1: B1 → B2 Academic English / TOEFL 80+",
                        "locked": False,
                        "topics": stage1_topics,
                        "modules": STAGE1_MODULES,
                    },
                    {
                        "slug": STAGE2_SLUG,
                        "title": "Stage 2: Academic English / TOEFL 100+",
                        "locked": not journey.stage2_unlocked,
                        "topics": stage2_topics,
                    },
                ],
            }
        )


class LessonStartRecommendedView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = LessonStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        topic = get_object_or_404(
            LessonTopic,
            id=serializer.validated_data["topic_id"],
            is_active=True,
        )
        if topic_is_locked(user, topic):
            return Response(
                {"detail": "Stage 2 lessons unlock after TOEFL 80+ readiness."},
                status=status.HTTP_403_FORBIDDEN,
            )
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))

        session = PracticeSession.objects.create(user=user, track=GRAMMAR_TRACK)
        mark_lesson_started(user, topic)
        starter_message = build_topic_starter_message(user, topic)

        try:
            result = run_task(
                GRAMMAR_TRACK,
                starter_message,
                user,
                session,
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "session_id": session.id,
                "reply": result["reply"],
                "corrections": result.get("corrections", []),
                "topic": topic_to_dict(topic),
                "starter_message": starter_message,
            },
            status=status.HTTP_201_CREATED,
        )


class LessonCompleteView(APIView):
    def post(self, request):
        serializer = LessonCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic = get_object_or_404(
            LessonTopic,
            id=serializer.validated_data["topic_id"],
            is_active=True,
        )
        score = serializer.validated_data["score"]
        notes = serializer.validated_data.get("notes") or ""

        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user,
            topic=topic,
            defaults={"status": LessonProgress.STATUS_STARTED},
        )
        progress.score = score
        progress.notes = notes
        progress.last_practiced = timezone.now()
        progress.status = (
            LessonProgress.STATUS_COMPLETED
            if score >= 70
            else LessonProgress.STATUS_NEEDS_REVIEW
        )
        progress.save()

        return Response(
            {
                "topic": topic_to_dict(topic),
                "progress": lesson_progress_to_dict(progress),
            }
        )


class ReadingAnalyzeView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ReadingAnalyzeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        passage = serializer.validated_data["passage"].strip()
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))

        if not passage:
            return Response(
                {"detail": "passage is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analysis = analyze_reading(passage, provider=provider)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            from tutor.reading_ai_service import friendly_reading_error

            return Response(
                {"detail": friendly_reading_error(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"analysis": analysis})


class ReadingQuizGenerateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ReadingQuizGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        passage = serializer.validated_data["passage"].strip()
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))
        level = serializer.validated_data.get("level") or "B1"
        question_focus = serializer.validated_data.get("question_focus") or "mixed"

        if not passage:
            return Response(
                {"detail": "passage is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quiz = generate_reading_quiz(
                request.user,
                passage,
                level=level,
                question_focus=question_focus,
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"quiz": quiz})


class ReadingQuizSubmitView(APIView):
    def post(self, request):
        serializer = ReadingQuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = score_reading_quiz(
                request.user,
                serializer.validated_data["quiz_id"],
                serializer.validated_data["answers"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class ReadingContextView(APIView):
    def get(self, request):
        context = gather_reading_context(request.user)
        return Response({"context": context})


class ReadingGenerateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ReadingGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from tutor.reading_ai_service import (
            ReadingNotConfiguredError,
            friendly_reading_error,
            resolve_reading_provider,
        )

        provider = resolve_reading_provider(
            resolve_user_provider(request, data.get("provider"))
        )
        simulation_type = (data.get("simulation_type") or "").strip()
        reading_mode = (data.get("reading_mode") or "general").strip()
        if reading_mode == "toefl_2026" and not simulation_type:
            simulation_type = "academic_passage"
        mode = (
            ReadingSession.MODE_SIMULATION
            if reading_mode in ("toefl_2026", "classic_toefl") or simulation_type
            else ReadingSession.MODE_GENERATED
        )

        try:
            session = generate_reading_practice(
                request.user,
                level=data.get("level") or "B1",
                stage=data.get("stage") or "b2_toefl_80",
                topic=data.get("topic") or "Academic",
                lesson_focus=data.get("lesson_focus") or "current_lesson",
                question_focus=data.get("question_focus") or "mixed",
                length=data.get("length") or "medium",
                provider=provider,
                mode=mode,
                simulation_type=simulation_type,
                reading_mode=reading_mode,
            )
        except ReadingNotConfiguredError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": friendly_reading_error(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            return Response(
                {"detail": friendly_reading_error(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"session": session})


class ReadingSubmitView(APIView):
    def post(self, request):
        serializer = ReadingSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = score_reading_session(
                request.user,
                serializer.validated_data["session_id"],
                serializer.validated_data["answers"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class WritingEditView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = WritingEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data["text"]
        edit_strength = serializer.validated_data.get("edit_strength") or "standard"
        target_style = serializer.validated_data.get("target_style") or "simple_american_english"
        provider = resolve_user_provider(
            request,
            serializer.validated_data.get("ai_provider")
            or serializer.validated_data.get("provider"),
        )

        try:
            result = run_writing_edit(
                text=text,
                edit_strength=edit_strength,
                target_style=target_style,
                language_level=serializer.validated_data.get("language_level") or "normal",
                user=request.user,
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"edit_result": result})


class WritingRevisionCompareView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = WritingRevisionCompareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))

        try:
            result = run_writing_revision_compare(
                original_answer=serializer.validated_data["original_answer"],
                revised_answer=serializer.validated_data["revised_answer"],
                prompt=serializer.validated_data.get("prompt") or "",
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result)


class WritingEditGenerateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = WritingEditGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = resolve_user_provider(
            request,
            serializer.validated_data.get("ai_provider")
            or serializer.validated_data.get("provider"),
        )

        try:
            result = run_writing_edit_generate(
                target_style=serializer.validated_data.get("target_style")
                or "simple_american_english",
                language_level=serializer.validated_data.get("language_level") or "normal",
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result)


class ParaphraseGenerateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ParaphraseGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = resolve_user_provider(
            request,
            serializer.validated_data.get("ai_provider")
            or serializer.validated_data.get("provider"),
        )

        try:
            result = run_paraphrase_generate(
                target_level=serializer.validated_data.get("target_level")
                or "simple_american_english",
                difficulty=serializer.validated_data.get("difficulty") or "easy",
                text_type=serializer.validated_data.get("text_type") or "one_sentence",
                language_level=serializer.validated_data.get("language_level") or "normal",
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result)


class ParaphraseCheckView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ParaphraseCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = resolve_user_provider(
            request,
            serializer.validated_data.get("ai_provider")
            or serializer.validated_data.get("provider"),
        )

        try:
            result = run_paraphrase_check(
                target_level=serializer.validated_data.get("target_level")
                or "simple_american_english",
                original_text=serializer.validated_data["original_text"],
                learner_paraphrase=serializer.validated_data["learner_paraphrase"],
                language_level=serializer.validated_data.get("language_level") or "normal",
                user=request.user,
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result)


class ListeningGenerateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        provider = resolve_user_provider(request, request.data.get("provider"))
        transcription_provider = resolve_user_provider(
            request, request.data.get("transcription_provider")
        )
        transcript = ""

        if request.FILES.get("audio"):
            audio = request.FILES["audio"]
            audio_bytes, error_response = _read_validated_audio(audio)
            if error_response is not None:
                return error_response
            try:
                transcript = transcribe_audio(
                    audio_bytes,
                    audio.name,
                    provider=transcription_provider,
                )
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except RuntimeError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
        else:
            serializer = ListeningGenerateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            provider = resolve_user_provider(
                request, serializer.validated_data.get("provider") or provider
            )
            transcription_provider = resolve_user_provider(
                request,
                serializer.validated_data.get("transcription_provider")
                or transcription_provider,
            )
            transcript = (serializer.validated_data.get("transcript") or "").strip()

        if not transcript:
            return Response(
                {"detail": "transcript or audio is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analysis = analyze_listening(transcript, provider=provider)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"transcript": transcript, "analysis": analysis})


class ListeningQuizGenerateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        provider = resolve_user_provider(request, request.data.get("provider"))
        transcription_provider = resolve_user_provider(
            request, request.data.get("transcription_provider")
        )
        level = request.data.get("level") or "B1"
        question_focus = request.data.get("question_focus") or "mixed"
        transcript = ""

        try:
            if request.FILES.get("audio"):
                audio = request.FILES["audio"]
                audio_bytes, error_response = _read_validated_audio(audio)
                if error_response is not None:
                    return error_response
                quiz = generate_listening_quiz(
                    request.user,
                    audio_bytes=audio_bytes,
                    audio_name=audio.name,
                    transcription_provider=transcription_provider,
                    provider=provider,
                    level=level,
                    question_focus=question_focus,
                )
            else:
                serializer = ListeningQuizGenerateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                provider = resolve_user_provider(
                    request, serializer.validated_data.get("provider") or provider
                )
                transcription_provider = resolve_user_provider(
                    request,
                    serializer.validated_data.get("transcription_provider")
                    or transcription_provider,
                )
                transcript = (serializer.validated_data.get("transcript") or "").strip()
                quiz = generate_listening_quiz(
                    request.user,
                    transcript=transcript,
                    transcription_provider=transcription_provider,
                    provider=provider,
                    level=serializer.validated_data.get("level") or level,
                    question_focus=serializer.validated_data.get("question_focus")
                    or question_focus,
                )
        except ValueError as exc:
            detail = str(exc)
            if "transcrib" in detail.lower() or "speech" in detail.lower():
                return Response({"detail": f"STT failed: {detail}"}, status=status.HTTP_400_BAD_REQUEST)
            if "parse" in detail.lower() or "quiz" in detail.lower():
                return Response(
                    {"detail": f"Quiz generation failed: {detail}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            detail = str(exc)
            if "transcrib" in detail.lower() or "whisper" in detail.lower():
                return Response({"detail": f"STT failed: {detail}"}, status=status.HTTP_502_BAD_GATEWAY)
            return Response(
                {"detail": f"Quiz generation failed: {detail}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"quiz": quiz})


class ListeningQuizSubmitView(APIView):
    def post(self, request):
        serializer = ListeningQuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = score_listening_quiz(
                request.user,
                serializer.validated_data["quiz_id"],
                serializer.validated_data["answers"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class ListeningPracticeContextView(APIView):
    def get(self, request):
        context = gather_listening_context(request.user)
        return Response({"context": context})


class ListeningPracticeGenerateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ListeningPracticeGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = resolve_user_provider(request, data.get("provider"))

        try:
            session = generate_listening_practice(
                request.user,
                level=data.get("level") or "B1",
                stage=data.get("stage") or "b2_toefl_80",
                listening_type=data.get("listening_type") or "academic_mini_lecture",
                topic=data.get("topic") or "Random",
                lesson_focus=data.get("lesson_focus") or "current_lesson",
                length=data.get("length") or "medium",
                speed=data.get("speed") or "normal",
                provider=provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"session": session})


class ListeningPracticeSubmitView(APIView):
    def post(self, request):
        serializer = ListeningPracticeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = score_listening_session(
                request.user,
                serializer.validated_data["session_id"],
                serializer.validated_data["answers"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class TranscribeView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        audio = request.FILES.get("audio")
        if not audio:
            return Response(
                {"detail": "audio file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        audio_bytes, error_response = _read_validated_audio(audio)
        if error_response is not None:
            return error_response

        provider = resolve_user_provider(request, request.data.get("provider"))
        try:
            text = transcribe(audio_bytes, audio.name, provider=provider)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"transcript": text, "text": text})


class SpeakingAttemptAudioView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        audio = request.FILES.get("audio")
        if not audio:
            return Response(
                {"detail": "audio file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scenario = (request.data.get("scenario") or request.data.get("task_type") or "daily conversation").strip()
        session_id = request.data.get("session_id")
        provider = resolve_user_provider(request, request.data.get("provider"))
        transcription_provider = resolve_user_provider(
            request, request.data.get("transcription_provider")
        )
        level = (request.data.get("level") or "normal").strip()
        evaluation_mode = (request.data.get("evaluation_mode") or "normal").strip()
        task_type = (request.data.get("task_type") or scenario).strip()
        task_title = (request.data.get("task_title") or "").strip()
        task_prompt = (request.data.get("task_prompt") or "").strip()
        article_text = (request.data.get("article_text") or "").strip()
        evaluation_focus = (request.data.get("evaluation_focus") or "").strip()
        prep_time = request.data.get("prep_time")
        speak_time = request.data.get("speak_time") or request.data.get("speaking_time")
        duration = request.data.get("duration")
        user = request.user

        audio_bytes, error_response = _read_validated_audio(audio)
        if error_response is not None:
            return error_response

        from tutor.speaking_evaluation import resolve_transcription_model

        try:
            transcript = transcribe(
                audio_bytes,
                audio.name,
                provider=transcription_provider,
                model=resolve_transcription_model(evaluation_mode),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if session_id:
            try:
                session = PracticeSession.objects.get(
                    id=session_id, user=user, track="speaking_coach"
                )
            except PracticeSession.DoesNotExist:
                return Response(
                    {"detail": "Session not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            session = PracticeSession.objects.create(user=user, track="speaking_coach")

        eval_message = transcript
        if task_prompt or task_title:
            try:
                speak_seconds = int(speak_time) if speak_time is not None else None
            except (TypeError, ValueError):
                speak_seconds = None
            try:
                prep_seconds = int(prep_time) if prep_time is not None else None
            except (TypeError, ValueError):
                prep_seconds = None
            eval_message = format_speaking_evaluation_message(
                level=level,
                task_type=task_type,
                task_title=task_title or task_type,
                task_prompt=task_prompt or f"Scenario: {scenario}",
                student_answer=transcript,
                input_mode="voice",
                article_text=article_text,
                evaluation_focus=[
                    part.strip()
                    for part in evaluation_focus.split(",")
                    if part.strip()
                ]
                or None,
                evaluation_mode=evaluation_mode,
                speaking_time=speak_seconds,
                prep_time=prep_seconds,
            )

        from tutor.speaking_evaluation import run_speaking_evaluation

        try:
            result = run_speaking_evaluation(
                user=user,
                session=session,
                eval_message=eval_message,
                provider=provider,
                scenario=task_type or scenario,
                evaluation_mode=evaluation_mode,
                input_mode="voice",
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "transcript": transcript,
                "reply": result["reply"],
                "corrections": result["corrections"],
                "speaking_feedback": result.get("speaking_feedback"),
                "session_id": session.id,
                "attempt_metadata": {
                    "prompt": task_prompt or task_title,
                    "mode": evaluation_mode,
                    "practice_type": task_type,
                    "prep_time": prep_time,
                    "speaking_time": speak_time,
                    "duration": duration,
                },
            }
        )


def shadowing_item_to_dict(item: ShadowingItem) -> dict:
    return {
        "id": item.id,
        "target_text": item.target_text,
        "persian_meaning": item.persian_meaning,
        "sort_order": item.sort_order,
    }


def save_shadowing_attempt(user, item: ShadowingItem, comparison: dict) -> ShadowingAttempt:
    return ShadowingAttempt.objects.create(
        item=item,
        user=user,
        transcript=comparison["transcript"],
        similarity_score=comparison["similarity_score"],
        missing_words=comparison["missing_words"],
        extra_words=comparison["extra_words"],
        changed_words=comparison["changed_words"],
        feedback=comparison["feedback"],
        persian_feedback=comparison["persian_feedback"],
    )


class ShadowingItemsListView(APIView):
    def get(self, request):
        from django.db.models import Q

        items = ShadowingItem.objects.filter(
            Q(user=request.user) | Q(user__isnull=True),
            is_active=True,
        ).order_by("sort_order", "id")
        return Response({"items": [shadowing_item_to_dict(item) for item in items]})


class ShadowingAttemptView(APIView):
    def post(self, request, item_id):
        serializer = ShadowingAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item = get_object_or_404(
            ShadowingItem,
            id=item_id,
            is_active=True,
        )
        if item.user_id and item.user_id != request.user.id:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        transcript = serializer.validated_data["transcript"].strip()
        if not transcript:
            return Response(
                {"detail": "transcript is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comparison = compare_shadowing(
            item.target_text,
            transcript,
            input_mode="typed",
        )
        save_shadowing_attempt(request.user, item, comparison)
        return Response(comparison)


class ShadowingAttemptAudioView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [AIUserRateThrottle]

    def post(self, request, item_id):
        audio = request.FILES.get("audio")
        if not audio:
            return Response(
                {"detail": "audio file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(
            ShadowingItem,
            id=item_id,
            is_active=True,
        )
        if item.user_id and item.user_id != request.user.id:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        transcription_provider = resolve_user_provider(
            request, request.data.get("transcription_provider")
        )
        audio_bytes, error_response = _read_validated_audio(audio)
        if error_response is not None:
            return error_response
        try:
            transcript = transcribe(
                audio_bytes,
                audio.name,
                provider=transcription_provider,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            duration_raw = request.data.get("duration") or request.data.get("duration_seconds")
            duration_seconds = float(duration_raw) if duration_raw not in (None, "") else None
        except (TypeError, ValueError):
            duration_seconds = None

        comparison = compare_shadowing(
            item.target_text,
            transcript,
            input_mode="voice",
            duration_seconds=duration_seconds,
        )
        save_shadowing_attempt(request.user, item, comparison)
        return Response(comparison)


class TTSView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = TTSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data["text"].strip()
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))

        if not text:
            return Response(
                {"detail": "text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            audio_bytes = synthesize_speech(text, provider=provider)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return HttpResponse(audio_bytes, content_type="audio/mpeg")


class ToeflPromptView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = ToeflPromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task_type = serializer.validated_data["task_type"]
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))
        prompt_request = (
            TOEFL_WRITING_PROMPT_REQUEST
            if task_type == "toefl_writing"
            else TOEFL_SPEAKING_PROMPT_REQUEST
        )

        try:
            prompt = generate_from_template(task_type, prompt_request, provider=provider)
        except (ValueError, RuntimeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"prompt": prompt.strip()})


class AnalyticsProgressView(APIView):
    def get(self, request):
        return Response(get_progress_analytics(request.user))


def vocab_to_dict(item: VocabularyItem) -> dict:
    return {
        "id": item.id,
        "word": item.word,
        "definition": item.definition,
        "example": item.example,
        "persian_meaning": item.persian_meaning,
        "part_of_speech": item.part_of_speech,
        "cefr_level": item.cefr_level,
        "category": item.category,
        "collocations": item.collocations or [],
        "shadowing_sentence": item.shadowing_sentence,
        "common_mistake": item.common_mistake,
        "correction": item.correction,
        "ease_factor": item.ease_factor,
        "interval": item.interval,
        "repetitions": item.repetitions,
        "next_review_date": item.next_review_date.isoformat(),
        "created_at": item.created_at.isoformat(),
    }


def seed_extra_fields(seed: VocabularySeed) -> dict:
    return {
        "collocations": seed.collocations or [],
        "shadowing_sentence": seed.shadowing_sentence,
        "common_mistake": seed.common_mistake,
        "correction": seed.correction,
        "approved": seed.approved,
    }


def create_vocab_item_from_seed(user, seed: VocabularySeed) -> tuple[VocabularyItem, bool]:
    existing = VocabularyItem.objects.filter(user=user, word__iexact=seed.word).first()
    if existing:
        return existing, False

    item = VocabularyItem.objects.create(
        user=user,
        word=seed.word,
        definition=seed.definition or seed.word,
        example=seed.example,
        persian_meaning=seed.persian_meaning,
        part_of_speech=seed.part_of_speech,
        cefr_level=seed.cefr_level,
        category=seed.category,
        collocations=list(seed.collocations or []),
        shadowing_sentence=seed.shadowing_sentence,
        common_mistake=seed.common_mistake,
        correction=seed.correction,
        next_review_date=date.today(),
    )
    return item, True


class VocabListCreateView(APIView):
    throttle_classes = [AIUserRateThrottle]

    def post(self, request):
        serializer = VocabCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        word = serializer.validated_data["word"].strip()
        definition = serializer.validated_data.get("definition", "").strip()
        example = serializer.validated_data.get("example", "").strip()
        persian_meaning = serializer.validated_data.get("persian_meaning", "").strip()
        provider = resolve_user_provider(request, serializer.validated_data.get("provider"))

        if not word:
            return Response(
                {"detail": "word is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        if not definition:
            try:
                raw = generate_from_template("vocab_builder", word, provider=provider)
                vocab_data = parse_vocab_json(raw)
            except (ValueError, RuntimeError) as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

            definition = (vocab_data.get("definition") or "").strip()
            example = example or (vocab_data.get("example") or "").strip()
            persian_meaning = persian_meaning or (
                vocab_data.get("persian_meaning") or ""
            ).strip()

        if not definition:
            return Response(
                {"detail": "definition is required or could not be generated"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if VocabularyItem.objects.filter(user=user, word__iexact=word).exists():
            existing = VocabularyItem.objects.get(user=user, word__iexact=word)
            return Response(
                {**vocab_to_dict(existing), "created": False, "already_exists": True},
                status=status.HTTP_200_OK,
            )

        item = VocabularyItem.objects.create(
            user=user,
            word=word,
            definition=definition,
            example=example,
            persian_meaning=persian_meaning,
            next_review_date=date.today(),
        )
        return Response(
            {**vocab_to_dict(item), "created": True, "already_exists": False},
            status=status.HTTP_201_CREATED,
        )


def vocab_seed_to_dict(seed: VocabularySeed) -> dict:
    return {
        "id": seed.id,
        "word": seed.word,
        "lemma": seed.lemma,
        "part_of_speech": seed.part_of_speech,
        "cefr_level": seed.cefr_level,
        "category": seed.category,
        "definition": seed.definition,
        "persian_meaning": seed.persian_meaning,
        "example": seed.example,
        "source": seed.source,
        "frequency_rank": seed.frequency_rank,
        **seed_extra_fields(seed),
    }


def filter_seeds_for_user(queryset, user, approved_param: str | None):
    if user.is_staff and approved_param is not None:
        normalized = approved_param.lower().strip()
        if normalized in {"true", "1", "yes"}:
            return queryset.filter(approved=True)
        if normalized in {"false", "0", "no"}:
            return queryset.filter(approved=False)
        if normalized == "all":
            return queryset
    return queryset.filter(approved=True)


class VocabSeedsListView(APIView):
    def get(self, request):
        queryset = VocabularySeed.objects.filter(is_active=True)

        cefr_level = (request.query_params.get("cefr_level") or "").strip()
        category = (request.query_params.get("category") or "").strip()
        search = (request.query_params.get("search") or "").strip()
        approved_param = request.query_params.get("approved")
        random_order = (request.query_params.get("random") or "").lower() in {
            "true",
            "1",
            "yes",
        }

        try:
            limit = int(request.query_params.get("limit") or 200)
        except ValueError:
            limit = 200
        limit = max(1, min(limit, 500))

        queryset = filter_seeds_for_user(queryset, request.user, approved_param)

        if cefr_level:
            queryset = queryset.filter(cefr_level__iexact=cefr_level)
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(word__icontains=search)

        if random_order:
            seeds = list(queryset.order_by("?")[:limit])
        else:
            seeds = list(queryset.order_by("frequency_rank", "word")[:limit])

        return Response({"seeds": [vocab_seed_to_dict(seed) for seed in seeds]})


class VocabCategoryStatsView(APIView):
    def get(self, request):
        user = request.user
        stats = []
        for category in DECK_CATEGORIES:
            label = VOCAB_CATEGORY_LABELS.get(category, category)
            base = VocabularySeed.objects.filter(is_active=True, category=category)
            stats.append(
                {
                    "category": category,
                    "label": label,
                    "total": base.count(),
                    "approved": base.filter(approved=True).count(),
                    "personal_cards": VocabularyItem.objects.filter(
                        user=user, category=category
                    ).count(),
                }
            )
        return Response(stats)


class VocabAddRandomFromCategoryView(APIView):
    def post(self, request):
        serializer = VocabAddRandomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = serializer.validated_data["category"].strip()
        count = serializer.validated_data["count"]
        cefr_level = (serializer.validated_data.get("cefr_level") or "").strip()
        user = request.user

        existing_words = VocabularyItem.objects.filter(user=user).values_list(
            "word", flat=True
        )
        queryset = VocabularySeed.objects.filter(
            is_active=True,
            approved=True,
            category=category,
        ).exclude(word__in=existing_words)

        if cefr_level:
            queryset = queryset.filter(cefr_level__iexact=cefr_level)

        seeds = list(queryset.order_by("?")[:count])
        created_items = []
        for seed in seeds:
            item, created = create_vocab_item_from_seed(user, seed)
            if created:
                created_items.append(vocab_to_dict(item))

        return Response(
            {
                "category": category,
                "requested": count,
                "created_count": len(created_items),
                "items": created_items,
            }
        )


class VocabCategoriesView(APIView):
    def get(self, request):
        categories = []
        for key, label in VOCAB_CATEGORY_LABELS.items():
            if key == "shadowing_sentences":
                continue
            base = VocabularySeed.objects.filter(is_active=True, category=key)
            categories.append(
                {
                    "key": key,
                    "label": label,
                    "count": base.filter(approved=True).count(),
                    "total": base.count(),
                }
            )
        return Response(categories)


class VocabFromSeedView(APIView):
    def post(self, request, seed_id):
        seed = get_object_or_404(VocabularySeed, id=seed_id, is_active=True)
        if not request.user.is_staff and not seed.approved:
            return Response(
                {"detail": "This vocabulary seed is not approved yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        item, created = create_vocab_item_from_seed(request.user, seed)
        return Response(
            {
                **vocab_to_dict(item),
                "created": created,
                "already_exists": not created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class VocabDueView(APIView):
    def get(self, request):
        items = due_vocab_queryset(request.user).order_by(
            "next_review_date", "created_at"
        )
        return Response({"items": [vocab_to_dict(item) for item in items]})


class VocabReviewView(APIView):
    def post(self, request, item_id):
        serializer = VocabReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        item = get_object_or_404(VocabularyItem, id=item_id, user=user)
        quality = serializer.validated_data["quality"]

        ease_factor, interval, repetitions, next_review_date = sm2(
            item.ease_factor,
            item.interval,
            item.repetitions,
            quality,
        )

        item.ease_factor = ease_factor
        item.interval = interval
        item.repetitions = repetitions
        item.next_review_date = next_review_date
        item.save()

        return Response(vocab_to_dict(item))


class PlanTodayView(APIView):
    def get(self, request):
        today = date.today()
        plan, progress = get_today_plan(request.user, today)
        if plan is None:
            return Response(empty_plan_response(request.user, today))
        return Response(plan_response_payload(plan, progress, request.user, today))

    def post(self, request):
        serializer = PlanItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = date.today()
        plan, progress = get_today_plan(user, today)
        if plan is None:
            return Response(
                {"detail": "No plan for today. Generate a plan first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            plan = update_plan_item(
                plan,
                serializer.validated_data["item_id"],
                serializer.validated_data["completed"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        progress = sync_progress_completion(plan, progress)
        return Response(plan_response_payload(plan, progress, user, today))


class PlanGenerateView(APIView):
    def post(self, request):
        today = date.today()
        try:
            plan, progress = generate_today_plan(request.user, today)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            plan_response_payload(plan, progress, request.user, today),
            status=status.HTTP_201_CREATED,
        )


class ReadinessView(APIView):
    def get(self, request):
        ensure_user_on_accessible_goal(request.user)
        return Response(build_readiness_report(request.user))


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        profile = get_user_profile(user)
        today = date.today()
        plan, progress = get_today_plan(user, today)

        vocab_due = due_vocab_queryset(user, today).count()
        mistakes_due = count_due_reviewable_mistakes(user, today)

        if plan is not None:
            plan_items = filter_reviewable_plan_items(plan.items, user)
            completed_count = sum(1 for item in plan_items if item.get("completed"))
            plan_summary = {
                "exists": True,
                "date": plan.date.isoformat(),
                "completed_count": completed_count,
                "total_count": len(plan_items),
                "completed": progress.completed,
                "minutes_per_track": progress.minutes_per_track,
                "progress_by_skill": progress_by_skill(progress.minutes_per_track or {}),
            }
        else:
            plan_summary = {
                "exists": False,
                "date": today.isoformat(),
                "completed_count": 0,
                "total_count": 0,
                "completed": False,
                "minutes_per_track": {},
                "progress_by_skill": [],
            }

        analytics = get_progress_analytics(user, today)
        coach_focus = build_coach_focus(
            user,
            today,
            plan_summary,
            profile,
            vocab_due,
            mistakes_due,
            plan=plan,
        )

        return Response(
            {
                "profile": {
                    "level": profile.level,
                    "goal": profile.goal,
                    "weak_areas": profile.weak_areas,
                    "native_language": profile.native_language,
                },
                "journey": build_journey_summary(user),
                "plan_summary": plan_summary,
                "coach_focus": coach_focus,
                "streak": calculate_streak(user, today),
                "vocab_due": vocab_due,
                "mistakes_due": mistakes_due,
                "analytics": analytics,
            }
        )
