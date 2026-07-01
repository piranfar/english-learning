from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tutor.models import LessonTopic

DEFAULT_TOPICS = [
    (
        "Present simple vs present continuous",
        "Compare habits and facts with actions happening now. Common B1 confusion for Persian speakers.",
    ),
    (
        "Past simple vs present perfect",
        "Finished past time vs connection to now. Essential for academic writing and TOEFL.",
    ),
    (
        "Articles: a/an/the",
        "When to use indefinite and definite articles — a frequent Persian-speaker challenge.",
    ),
    (
        "Prepositions of time and place",
        "In, on, at and related prepositions for time expressions and locations.",
    ),
    (
        "Modal verbs: should, must, have to",
        "Advice, obligation, and necessity in academic and everyday English.",
    ),
    (
        "Conditionals type 0/1/2",
        "Real and unreal conditionals for hypotheses, advice, and academic argument.",
    ),
    (
        "Used to / be used to / get used to",
        "Past habits vs familiarity — often mixed up by Persian speakers.",
    ),
    (
        "Passive voice",
        "Academic passive structures for reports, research summaries, and TOEFL tasks.",
    ),
    (
        "Relative clauses",
        "Defining and non-defining clauses with who, which, that, and whose.",
    ),
    (
        "Gerunds and infinitives",
        "Verb patterns after common verbs and prepositions.",
    ),
    (
        "Comparatives and superlatives",
        "Comparing ideas clearly in essays and spoken responses.",
    ),
    (
        "Academic linking words",
        "However, therefore, moreover, and other connectors for B1–B2 writing.",
    ),
    (
        "Academic sentence structure",
        "Complex sentences, subordination, and clarity for university-style English.",
    ),
    (
        "Common Persian-speaker grammar mistakes",
        "Targeted review of article, preposition, tense, and word-order errors.",
    ),
]


class Command(BaseCommand):
    help = "Seed default B1 grammar lesson topics."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for order, (title, description) in enumerate(DEFAULT_TOPICS, start=1):
            slug = slugify(title)
            _topic, was_created = LessonTopic.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "level": "B1",
                    "category": "grammar",
                    "description": description,
                    "order": order,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Lesson topics seeded. Created {created}, updated {updated}."
            )
        )
