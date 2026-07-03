"""Static multiple-choice question bank for grammar lesson quizzes."""

from __future__ import annotations

from tutor.models import LessonTopic

Question = dict


def _q(qid: str, question: str, options: list[str], correct_index: int, explanation: str) -> Question:
    return {
        "id": qid,
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "explanation": explanation,
    }


# Shared quiz sets keyed by template id
_QUIZ_SETS: dict[str, list[Question]] = {
    "present_simple": [
        _q(
            "q1",
            "Which sentence uses the present simple correctly?",
            [
                "She go to the library every week.",
                "She goes to the library every week.",
                "She is going to the library every week.",
                "She going to the library every week.",
            ],
            1,
            "Use present simple (base + -s for he/she/it) for habits and routines.",
        ),
        _q(
            "q2",
            "Choose the correct negative present simple form.",
            [
                "He don't like coffee.",
                "He doesn't likes coffee.",
                "He doesn't like coffee.",
                "He not like coffee.",
            ],
            2,
            "Negative present simple: do/does + not + base verb.",
        ),
        _q(
            "q3",
            "Which question is correct in the present simple?",
            [
                "Do she work here?",
                "Does she works here?",
                "Does she work here?",
                "Is she work here?",
            ],
            2,
            "Questions: Do/Does + subject + base verb.",
        ),
        _q(
            "q4",
            "Which sentence describes a general fact?",
            [
                "Water is boiling now.",
                "Water boils at 100°C.",
                "Water was boiling at 100°C.",
                "Water has boiled at 100°C.",
            ],
            1,
            "Present simple expresses facts and general truths.",
        ),
    ],
    "present_continuous": [
        _q(
            "q1",
            "Which sentence describes an action happening now?",
            [
                "I study for the exam now.",
                "I am studying for the exam now.",
                "I studied for the exam now.",
                "I have studied for the exam now.",
            ],
            1,
            "Present continuous: am/is/are + verb-ing for actions in progress.",
        ),
        _q(
            "q2",
            "Choose the correct form.",
            [
                "She is work on her essay.",
                "She is working on her essay.",
                "She working on her essay.",
                "She are working on her essay.",
            ],
            1,
            "Use am/is/are + verb-ing.",
        ),
        _q(
            "q3",
            "Which sentence is correct?",
            [
                "They are not understanding the lecture right now.",
                "They don't understanding the lecture right now.",
                "They not are understanding the lecture right now.",
                "They aren't understand the lecture right now.",
            ],
            0,
            "Negative: am/is/are + not + verb-ing.",
        ),
        _q(
            "q4",
            "Which time expression fits present continuous best?",
            [
                "every day",
                "usually",
                "at the moment",
                "never",
            ],
            2,
            "'At the moment' signals a temporary action in progress.",
        ),
    ],
    "present_perfect": [
        _q(
            "q1",
            "Which sentence uses the present perfect correctly?",
            [
                "I have finished my homework yesterday.",
                "I have finished my homework.",
                "I finished have my homework.",
                "I am have finished my homework.",
            ],
            1,
            "Present perfect: have/has + past participle; often no specific past time.",
        ),
        _q(
            "q2",
            "Choose the best sentence for life experience.",
            [
                "I visited London in 2019.",
                "I have visited London twice.",
                "I am visiting London twice.",
                "I visit London twice.",
            ],
            1,
            "Present perfect often describes experience without a finished past time.",
        ),
        _q(
            "q3",
            "Which question is correct?",
            [
                "Did you ever been to Canada?",
                "Have you ever been to Canada?",
                "Are you ever been to Canada?",
                "Do you ever been to Canada?",
            ],
            1,
            "Experience questions: Have you ever + past participle?",
        ),
        _q(
            "q4",
            "Which sentence shows a recent result?",
            [
                "I lost my keys yesterday.",
                "I have lost my keys, so I can't get in.",
                "I was losing my keys.",
                "I lose my keys.",
            ],
            1,
            "Present perfect connects a past action to a present result.",
        ),
    ],
    "past_simple": [
        _q(
            "q1",
            "Which sentence uses the past simple correctly?",
            [
                "She go to class yesterday.",
                "She went to class yesterday.",
                "She has went to class yesterday.",
                "She was go to class yesterday.",
            ],
            1,
            "Past simple for finished actions at a specific past time.",
        ),
        _q(
            "q2",
            "Choose the correct negative form.",
            [
                "They didn't went home.",
                "They didn't go home.",
                "They don't went home.",
                "They not go home.",
            ],
            1,
            "Negative past simple: did not + base verb.",
        ),
        _q(
            "q3",
            "Which time marker fits past simple?",
            [
                "now",
                "already",
                "last night",
                "since 2020",
            ],
            2,
            "'Last night' is a finished past time expression.",
        ),
        _q(
            "q4",
            "Which question is correct?",
            [
                "Did he finished the report?",
                "Did he finish the report?",
                "Has he finish the report?",
                "Does he finished the report?",
            ],
            1,
            "Past simple questions: Did + subject + base verb.",
        ),
    ],
    "articles": [
        _q(
            "q1",
            "Choose the correct article: ___ university near my house is new.",
            ["A", "An", "The", "No article"],
            0,
            "Use 'a' before consonant sounds; 'university' starts with /j/ (y sound).",
        ),
        _q(
            "q2",
            "Choose the correct article: I saw ___ owl in the tree.",
            ["a", "an", "the", "—"],
            1,
            "Use 'an' before vowel sounds.",
        ),
        _q(
            "q3",
            "Which sentence is correct?",
            [
                "Sun is bright today.",
                "The sun is bright today.",
                "A sun is bright today.",
                "An sun is bright today.",
            ],
            1,
            "Use 'the' for unique or known things (the sun).",
        ),
        _q(
            "q4",
            "Choose the correct sentence.",
            [
                "She is best student in the class.",
                "She is the best student in the class.",
                "She is a best student in class.",
                "She is best student in class.",
            ],
            1,
            "Superlatives usually take 'the'.",
        ),
    ],
    "prepositions": [
        _q(
            "q1",
            "Choose the correct preposition: The meeting is ___ Monday.",
            ["in", "on", "at", "by"],
            1,
            "Use 'on' for days.",
        ),
        _q(
            "q2",
            "Choose the correct preposition: She was born ___ 2005.",
            ["on", "at", "in", "by"],
            2,
            "Use 'in' for years and longer periods.",
        ),
        _q(
            "q3",
            "Choose the correct preposition: I'll meet you ___ the library.",
            ["in", "on", "at", "to"],
            2,
            "Use 'at' for specific locations/points.",
        ),
        _q(
            "q4",
            "Which sentence is correct?",
            [
                "I study in the morning.",
                "I study on the morning.",
                "I study at the morning.",
                "I study by the morning.",
            ],
            0,
            "Use 'in' with parts of the day like 'the morning'.",
        ),
    ],
    "modals": [
        _q(
            "q1",
            "Choose the best modal for strong obligation.",
            [
                "You should wear a seatbelt.",
                "You must wear a seatbelt.",
                "You can wear a seatbelt.",
                "You might wear a seatbelt.",
            ],
            1,
            "'Must' expresses strong obligation or rules.",
        ),
        _q(
            "q2",
            "Which sentence gives advice?",
            [
                "You must see a doctor.",
                "You should see a doctor.",
                "You can see a doctor.",
                "You will see a doctor.",
            ],
            1,
            "'Should' is common for advice.",
        ),
        _q(
            "q3",
            "Choose the correct form.",
            [
                "He must to study harder.",
                "He must study harder.",
                "He must studying harder.",
                "He must studies harder.",
            ],
            1,
            "Modals are followed by the base verb without 'to'.",
        ),
        _q(
            "q4",
            "Which sentence expresses permission?",
            [
                "You must leave now.",
                "You should leave now.",
                "You can leave now.",
                "You have leave now.",
            ],
            2,
            "'Can' often expresses permission.",
        ),
    ],
    "passive": [
        _q(
            "q1",
            "Choose the correct passive sentence.",
            [
                "The experiment conducted by the team.",
                "The experiment was conducted by the team.",
                "The experiment is conduct by the team.",
                "The experiment was conduct by the team.",
            ],
            1,
            "Passive: be + past participle.",
        ),
        _q(
            "q2",
            "Which sentence is passive?",
            [
                "The researchers analyzed the data.",
                "The data was analyzed by the researchers.",
                "The researchers are analyzing the data.",
                "The researchers have analyzed the data.",
            ],
            1,
            "Passive focuses on the object receiving the action.",
        ),
        _q(
            "q3",
            "Choose the correct form.",
            [
                "English is speak all over the world.",
                "English is spoken all over the world.",
                "English is speaking all over the world.",
                "English spoken all over the world.",
            ],
            1,
            "Use past participle after 'is/am/are'.",
        ),
        _q(
            "q4",
            "Why is passive common in academic writing?",
            [
                "It sounds informal.",
                "It focuses on the action rather than the agent.",
                "It always uses future tense.",
                "It avoids verbs.",
            ],
            1,
            "Passive emphasizes results, methods, or objects.",
        ),
    ],
    "conditionals": [
        _q(
            "q1",
            "Choose the correct first conditional.",
            [
                "If it will rain, we stay home.",
                "If it rains, we will stay home.",
                "If it rained, we will stay home.",
                "If it rains, we stayed home.",
            ],
            1,
            "First conditional: If + present, will + base verb.",
        ),
        _q(
            "q2",
            "Choose the correct second conditional.",
            [
                "If I have more time, I travel more.",
                "If I had more time, I would travel more.",
                "If I had more time, I will travel more.",
                "If I have more time, I would travel more.",
            ],
            1,
            "Second conditional: If + past, would + base verb.",
        ),
        _q(
            "q3",
            "Which sentence is unreal/hypothetical?",
            [
                "If water reaches 100°C, it boils.",
                "If I were you, I would rest.",
                "If she studies, she passes.",
                "If they arrive late, they miss the intro.",
            ],
            1,
            "Second conditional expresses unreal or unlikely situations.",
        ),
        _q(
            "q4",
            "Choose the correct zero conditional.",
            [
                "If you heat ice, it melts.",
                "If you heated ice, it melts.",
                "If you heat ice, it would melt.",
                "If you will heat ice, it melts.",
            ],
            0,
            "Zero conditional: If + present, present (general truths).",
        ),
    ],
    "relative_clauses": [
        _q(
            "q1",
            "Choose the correct relative clause.",
            [
                "The student which sits near me is friendly.",
                "The student who sits near me is friendly.",
                "The student who sitting near me is friendly.",
                "The student who sit near me is friendly.",
            ],
            1,
            "Use 'who' for people with a full clause.",
        ),
        _q(
            "q2",
            "Which sentence is correct?",
            [
                "The book who I borrowed is useful.",
                "The book that I borrowed is useful.",
                "The book that I borrowed it is useful.",
                "The book which I borrowed it is useful.",
            ],
            1,
            "Use 'that/which' for things; avoid doubling the object.",
        ),
        _q(
            "q3",
            "Choose the correct non-defining for people.",
            [
                "My brother, that lives in Tehran, is a doctor.",
                "My brother, who lives in Tehran, is a doctor.",
                "My brother who lives in Tehran, is a doctor.",
                "My brother, which lives in Tehran, is a doctor.",
            ],
            1,
            "Non-defining clauses use 'who' for people and commas.",
        ),
        _q(
            "q4",
            "What is a defining relative clause?",
            [
                "It adds extra non-essential information.",
                "It identifies which person or thing you mean.",
                "It always uses 'who'.",
                "It never uses commas.",
            ],
            1,
            "Defining clauses are essential to identify the noun.",
        ),
    ],
    "gerunds_infinitives": [
        _q(
            "q1",
            "Choose the correct form after 'enjoy'.",
            [
                "I enjoy to read.",
                "I enjoy reading.",
                "I enjoy read.",
                "I enjoy for reading.",
            ],
            1,
            "'Enjoy' is followed by a gerund (-ing).",
        ),
        _q(
            "q2",
            "Choose the correct form after 'want'.",
            [
                "She wants studying abroad.",
                "She wants study abroad.",
                "She wants to study abroad.",
                "She wants for study abroad.",
            ],
            2,
            "'Want' is followed by to + base verb.",
        ),
        _q(
            "q3",
            "Which sentence is correct?",
            [
                "He decided leaving early.",
                "He decided to leave early.",
                "He decided leave early.",
                "He decided for leave early.",
            ],
            1,
            "'Decide' takes an infinitive.",
        ),
        _q(
            "q4",
            "Choose the correct form after 'avoid'.",
            [
                "Try to avoid to make mistakes.",
                "Try to avoid making mistakes.",
                "Try to avoid make mistakes.",
                "Try avoiding make mistakes.",
            ],
            1,
            "'Avoid' is followed by a gerund.",
        ),
    ],
    "academic_writing": [
        _q(
            "q1",
            "Which linker shows contrast?",
            ["Therefore", "However", "Moreover", "Similarly"],
            1,
            "'However' introduces contrast.",
        ),
        _q(
            "q2",
            "Which sentence has the clearest topic sentence?",
            [
                "Many things are important in essays.",
                "A strong topic sentence states the main idea of the paragraph.",
                "Essays are hard and long.",
                "Students write many essays.",
            ],
            1,
            "A topic sentence should clearly state the paragraph's main idea.",
        ),
        _q(
            "q3",
            "Choose the best academic phrase for adding a point.",
            ["On the other hand", "In addition", "Although", "Despite"],
            1,
            "'In addition' adds supporting information.",
        ),
        _q(
            "q4",
            "Which revision improves clarity?",
            [
                "The research, it shows that practice helps.",
                "The research shows that practice helps.",
                "Research showing that practice helps it.",
                "The research shows practice helping it.",
            ],
            1,
            "Remove unnecessary words and repeated subjects.",
        ),
    ],
    "toefl_reading": [
        _q(
            "q1",
            "A main-idea question usually asks you to find…",
            [
                "one vocabulary word",
                "the central point of the passage",
                "the author's birth year",
                "a minor detail in paragraph 3",
            ],
            1,
            "Main idea = the passage's central point.",
        ),
        _q(
            "q2",
            "For an inference question, you should…",
            [
                "copy a sentence word for word",
                "use information in the text to reach a logical conclusion",
                "ignore the passage",
                "choose the longest answer",
            ],
            1,
            "Inference requires logical conclusions from stated information.",
        ),
        _q(
            "q3",
            "A detail question requires you to…",
            [
                "guess the author's opinion",
                "locate specific information stated in the text",
                "summarize the whole passage",
                "translate the passage",
            ],
            1,
            "Detail questions test whether you found explicit information.",
        ),
        _q(
            "q4",
            "Vocabulary-in-context questions ask you to…",
            [
                "memorize every dictionary definition",
                "use surrounding clues to determine word meaning",
                "ignore context",
                "change the word to Persian",
            ],
            1,
            "Context clues help determine meaning in academic texts.",
        ),
    ],
    "generic_grammar": [
        _q(
            "q1",
            "Which sentence is grammatically correct in academic English?",
            [
                "The results shows a clear trend.",
                "The results show a clear trend.",
                "The results showing a clear trend.",
                "The results show a clearly trend.",
            ],
            1,
            "Plural subject 'results' needs base verb 'show'.",
        ),
        _q(
            "q2",
            "Choose the best formal sentence.",
            [
                "Kids gotta study more.",
                "Children must study more regularly.",
                "Children must to study more regularly.",
                "Children must studying more regularly.",
            ],
            1,
            "Academic English prefers formal vocabulary and correct modal use.",
        ),
        _q(
            "q3",
            "Which sentence has correct word order?",
            [
                "Always she is late.",
                "She always is late.",
                "She is always late.",
                "She is late always.",
            ],
            2,
            "Adverbs of frequency usually go before the main verb (except 'be').",
        ),
        _q(
            "q4",
            "Which revision fixes subject–verb agreement?",
            [
                "Each of the students have a notebook.",
                "Each of the students has a notebook.",
                "Each of the students having a notebook.",
                "Each of the students have an notebook.",
            ],
            1,
            "'Each' is singular, so use 'has'.",
        ),
    ],
}

# Map lesson slugs to quiz template sets
_SLUG_TEMPLATE: dict[str, str] = {
    "present-simple": "present_simple",
    "present-continuous": "present_continuous",
    "present-perfect": "present_perfect",
    "present-perfect-continuous": "present_perfect",
    "past-simple": "past_simple",
    "past-continuous": "past_simple",
    "past-perfect": "past_simple",
    "past-perfect-continuous": "past_simple",
    "future-simple-with-will": "present_simple",
    "future-with-going-to-planned-future": "present_continuous",
    "future-continuous": "present_continuous",
    "future-perfect-and-future-perfect-continuous": "present_perfect",
    "articles-a-an-the": "articles",
    "countable-and-uncountable-nouns": "articles",
    "prepositions-of-time-and-place": "prepositions",
    "subject-verb-agreement": "generic_grammar",
    "modal-verbs": "modals",
    "modal-verbs-should-must-have-to": "modals",
    "used-to-be-used-to-get-used-to": "modals",
    "passive-voice": "passive",
    "conditionals-type-0-1-2": "conditionals",
    "conditionals-type-3-and-mixed-conditionals": "conditionals",
    "gerunds-and-infinitives": "gerunds_infinitives",
    "relative-clauses": "relative_clauses",
    "comparatives-and-superlatives": "generic_grammar",
    "academic-linking-words": "academic_writing",
    "academic-sentence-structure": "academic_writing",
    "complex-sentences": "academic_writing",
    "common-persian-speaker-grammar-mistakes": "generic_grammar",
    "common-learner-mistakes": "generic_grammar",
    "paragraph-organization": "academic_writing",
    "paraphrasing-and-summarizing": "academic_writing",
    "opinion-and-argument-structure": "academic_writing",
    "cause-effect-and-contrast-language": "academic_writing",
    "toefl-reading-question-types": "toefl_reading",
    "toefl-listening-question-types": "toefl_reading",
    "toefl-speaking-structure": "academic_writing",
    "toefl-independent-speaking": "academic_writing",
    "toefl-integrated-speaking": "academic_writing",
    "toefl-writing-structure": "academic_writing",
    "toefl-integrated-writing": "academic_writing",
    "toefl-integrated-writing-stage2": "academic_writing",
    "integrated-b2-toefl-80-readiness-practice": "generic_grammar",
    "present-simple-vs-present-continuous": "present_continuous",
    "past-simple-vs-present-perfect": "present_perfect",
}


def _bank_questions_for_topic(topic: LessonTopic) -> list[Question]:
    template_key = _SLUG_TEMPLATE.get(topic.slug)
    if not template_key:
        title = (topic.title or "").lower()
        if "article" in title:
            template_key = "articles"
        elif "preposition" in title:
            template_key = "prepositions"
        elif "passive" in title:
            template_key = "passive"
        elif "conditional" in title:
            template_key = "conditionals"
        elif "relative" in title:
            template_key = "relative_clauses"
        elif "gerund" in title or "infinitive" in title:
            template_key = "gerunds_infinitives"
        elif "toefl" in title and "reading" in title:
            template_key = "toefl_reading"
        elif topic.category in ("writing", "reading", "listening", "speaking"):
            template_key = "academic_writing"
        else:
            template_key = "generic_grammar"

    return [dict(item) for item in _QUIZ_SETS[template_key]]


def questions_for_topic(topic: LessonTopic) -> list[Question]:
    """Return four MCQ items for a lesson topic."""
    if topic.quiz_questions_json:
        return list(topic.quiz_questions_json)
    return _bank_questions_for_topic(topic)


def populate_all_topic_quizzes(*, force: bool = False) -> int:
    """Persist quiz questions onto all active lesson topics."""
    updated = 0
    for topic in LessonTopic.objects.filter(is_active=True):
        if topic.quiz_questions_json and not force:
            continue
        topic.quiz_questions_json = _bank_questions_for_topic(topic)
        topic.save(update_fields=["quiz_questions_json"])
        updated += 1
    return updated


def public_question(item: Question) -> dict:
    return {
        "id": item["id"],
        "question": item["question"],
        "options": item["options"],
    }
