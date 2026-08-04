from django.core.management.base import CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from .management.commands.seed_assessment_banks import validate_bank
from .question_banks.english import QUESTIONS, SECTIONS
from .question_banks.python_django import QUESTIONS as PYTHON_QUESTIONS, SECTIONS as PYTHON_SECTIONS
from .templatetags.assessment_extras import inline_code
from .models import Exam


class EnglishQuestionBankTests(SimpleTestCase):
    def test_bank_has_exactly_fifty_valid_questions(self):
        self.assertEqual(len(QUESTIONS), 50)
        validate_bank(QUESTIONS, SECTIONS)

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
    def test_bank_has_exactly_fifty_valid_questions(self):
        self.assertEqual(len(PYTHON_QUESTIONS), 50)
        validate_bank(PYTHON_QUESTIONS, PYTHON_SECTIONS)

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
