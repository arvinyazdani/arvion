from django.core.management.base import CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from .management.commands.seed_assessment_banks import validate_bank
from .question_banks.english import QUESTIONS, SECTIONS
from .question_banks.python_django import QUESTIONS as PYTHON_QUESTIONS, SECTIONS as PYTHON_SECTIONS
from .templatetags.assessment_extras import inline_code
from .models import Exam, ExamEntitlement, ExamVersion, Order
from .services import start_attempt


class EnglishQuestionBankTests(SimpleTestCase):
    def test_bank_has_exactly_one_hundred_sixty_eight_valid_questions(self):
        self.assertEqual(len(QUESTIONS), 168)
        validate_bank(QUESTIONS, SECTIONS)

    def test_text_only_blueprint_selects_fifty_questions(self):
        self.assertEqual(sum(section[4] for section in SECTIONS), 50)

    def test_writing_objective_has_twenty_longer_items(self):
        writing = [question for question in QUESTIONS if question["section"] == "writing-objective"]
        self.assertEqual(len(writing), 20)
        self.assertTrue(all(question["question_type"] == "writing_objective" for question in writing))
        self.assertTrue(all(question["suggested_seconds"] >= 180 for question in writing))

    def test_every_question_has_one_answer_key_and_explanation(self):
        for question in QUESTIONS:
            self.assertEqual(len(question["choices"]), 4)
            self.assertTrue(question["choices"][0])
            self.assertTrue(question["explanation"])

    def test_validator_rejects_duplicate_choices(self):
        invalid = [{"section": "only", "choices": ("a", "a", "b", "c"), "difficulty": 1}]
        with self.assertRaises(CommandError):
            validate_bank(invalid, (("only", "بخش", "Section", 1),))


class PythonQuestionBankTests(SimpleTestCase):
    def test_bank_has_exactly_two_hundred_valid_questions(self):
        self.assertEqual(len(PYTHON_QUESTIONS), 200)
        validate_bank(PYTHON_QUESTIONS, PYTHON_SECTIONS)

    def test_exam_blueprint_selects_fifty_questions_from_seven_sections(self):
        self.assertEqual(len(PYTHON_SECTIONS), 7)
        self.assertEqual(sum(section[4] for section in PYTHON_SECTIONS), 50)

    def test_every_question_has_complete_explanations_and_unique_prompts(self):
        prompts_fa = [question["prompt_fa"].strip().casefold() for question in PYTHON_QUESTIONS]
        prompts_en = [question["prompt_en"].strip().casefold() for question in PYTHON_QUESTIONS]
        self.assertEqual(len(set(prompts_fa)), 200)
        self.assertEqual(len(set(prompts_en)), 200)
        for question in PYTHON_QUESTIONS:
            self.assertTrue(question["explanation_fa"])
            self.assertTrue(question["explanation_en"])
            self.assertEqual(len(question["choice_explanations_fa"]), 4)
            self.assertEqual(len(question["choice_explanations_en"]), 4)

    def test_every_prompt_is_bilingual(self):
        for question in PYTHON_QUESTIONS:
            self.assertTrue(question["prompt_fa"])
            self.assertTrue(question["prompt_en"])
            self.assertNotEqual(question["prompt_fa"], question["prompt_en"])

    def test_inline_code_keeps_ascii_and_escapes_question_html(self):
        rendered = str(inline_code('مقدار `<x 1>` <script>bad</script>'))
        self.assertIn('data-ascii', rendered)
        self.assertIn('&lt;x 1&gt;', rendered)
        self.assertNotIn('<script>', rendered)


class BenchmarkCommandTests(TestCase):
    def test_benchmark_rolls_back_all_synthetic_data(self):
        call_command("benchmark_assessment_engine", attempts=2, verbosity=0)
        self.assertFalse(Exam.objects.filter(slug="benchmark-50").exists())
        self.assertFalse(get_user_model().objects.filter(email="benchmark@local.invalid").exists())


class PublishedPythonBankTests(TestCase):
    def test_version_two_publishes_and_builds_a_balanced_fifty_question_attempt(self):
        english_exam = Exam.objects.create(
            slug="english-placement-a1-c1", title_fa="انگلیسی", title_en="English",
            description_fa="توضیح", description_en="Description", language_mode="en",
            question_count=50,
        )
        python_exam = Exam.objects.create(
            slug="python-django-professional", title_fa="پایتون", title_en="Python",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
            question_count=50,
        )
        call_command("seed_assessment_banks", verbosity=0)
        english_exam.refresh_from_db()
        english_version = ExamVersion.objects.get(exam=english_exam, version=2, is_published=True)
        self.assertEqual(english_exam.duration_minutes, 75)
        self.assertEqual(english_version.questions.count(), 168)
        self.assertEqual(english_version.sections.get(code="writing-objective").question_count, 5)
        version = ExamVersion.objects.get(exam=python_exam, version=2, is_published=True)
        self.assertEqual(version.questions.count(), 200)
        self.assertEqual(sum(section.question_count for section in version.sections.all()), 50)
        user = get_user_model().objects.create_user(
            username="bank-test@example.com", email="bank-test@example.com", password="test",
        )
        order = Order.objects.create(user=user, exam=python_exam, amount_irr=500_000, status="paid")
        entitlement = ExamEntitlement.objects.create(
            user=user, exam=python_exam, order=order, attempts_remaining=1,
        )
        attempt, _ = start_attempt(entitlement.pk, user)
        self.assertEqual(attempt.version, version)
        self.assertEqual(attempt.attempt_questions.count(), 50)
        for section in version.sections.all():
            rows = attempt.attempt_questions.filter(question__section=section)
            self.assertEqual(rows.count(), section.question_count)
            actual = {}
            for difficulty in rows.values_list("question__difficulty", flat=True):
                actual[str(difficulty)] = actual.get(str(difficulty), 0) + 1
            self.assertEqual(actual, section.difficulty_distribution)
