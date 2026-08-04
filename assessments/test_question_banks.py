from django.core.management.base import CommandError
from django.test import SimpleTestCase

from .management.commands.seed_assessment_banks import validate_bank
from .question_banks.english import QUESTIONS, SECTIONS


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
