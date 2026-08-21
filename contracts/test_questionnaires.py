from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from crm_orders.specialist import SECTIONS

from .questionnaires import (
    clean_answer,
    clean_section_answers,
    completion,
    normalize_schema,
    schema_from_legacy_sections,
)


class QuestionnaireSchemaTests(SimpleTestCase):
    def setUp(self):
        self.schema = [
            {
                "key": "goals",
                "title": "هدف پروژه",
                "description": "نتیجه مورد انتظار را روشن کنید.",
                "questions": [
                    {
                        "key": "main_goal",
                        "label": "مهم‌ترین هدف چیست؟",
                        "help_text": "یک خروجی قابل سنجش بنویسید.",
                        "type": "long_text",
                        "required": True,
                        "choices": [],
                    },
                    {
                        "key": "channels",
                        "label": "کانال‌ها",
                        "help_text": "",
                        "type": "multiple_choice",
                        "required": False,
                        "choices": ["وب", "موبایل"],
                    },
                ],
            }
        ]

    def test_schema_is_normalized_and_unknown_answer_type_is_rejected(self):
        self.assertEqual(normalize_schema(self.schema)[0]["questions"][0]["type"], "long_text")
        broken = [dict(self.schema[0], questions=[dict(self.schema[0]["questions"][0], type="file")])]
        with self.assertRaises(ValidationError):
            normalize_schema(broken)

    def test_duplicate_question_keys_are_rejected_inside_a_section(self):
        duplicate = [{
            **self.schema[0],
            "questions": [
                self.schema[0]["questions"][0],
                dict(self.schema[0]["questions"][0]),
            ],
        }]
        with self.assertRaises(ValidationError):
            normalize_schema(duplicate)

    def test_partial_save_accepts_blank_but_submission_requires_answer(self):
        question = normalize_schema(self.schema)[0]["questions"][0]
        self.assertEqual(clean_answer(question, "", enforce_required=False), "")
        with self.assertRaises(ValidationError):
            clean_answer(question, "", enforce_required=True)

    def test_choices_are_whitelisted(self):
        question = normalize_schema(self.schema)[0]["questions"][1]
        self.assertEqual(clean_answer(question, ["وب"], enforce_required=True), ["وب"])
        with self.assertRaises(ValidationError):
            clean_answer(question, ["غیرمجاز"], enforce_required=True)

    def test_completion_is_computed_from_required_schema_not_status(self):
        incomplete = completion(self.schema, {"goals": {"main_goal": "", "channels": []}})
        self.assertFalse(incomplete["is_complete"])
        cleaned = clean_section_answers(
            self.schema,
            "goals",
            {"main_goal": "کاهش زمان پاسخ‌گویی به کمتر از یک ساعت", "channels": ["وب"]},
        )
        complete = completion(self.schema, {"goals": cleaned})
        self.assertTrue(complete["is_complete"])
        self.assertEqual(complete["percent"], 100)

    def test_noorbinan_schema_keeps_existing_section_and_question_keys(self):
        schema = schema_from_legacy_sections(SECTIONS)
        self.assertEqual(schema[0]["key"], SECTIONS[0][0])
        self.assertEqual(schema[0]["questions"][0]["key"], SECTIONS[0][3][0][0])
        self.assertNotIn("accounting", {section["key"] for section in schema})
