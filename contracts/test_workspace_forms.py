from django.test import SimpleTestCase

from .forms import (
    DynamicQuestionnaireSectionForm,
    QuestionnaireRowFormSet,
    WorkspaceAccessForm,
    questionnaire_rows_from_schema,
    questionnaire_schema_from_formset,
)


def form_schema():
    return [
        {
            "key": "operations",
            "title": "فرآیندها",
            "description": "فرآیند واقعی را شرح دهید.",
            "questions": [
                {
                    "key": "workflow",
                    "label": "فرآیند اصلی چیست؟",
                    "help_text": "با یک مثال توضیح دهید.",
                    "type": "long_text",
                    "required": True,
                    "choices": [],
                    "placeholder": "مثال واقعی…",
                },
                {
                    "key": "priority",
                    "label": "اولویت را انتخاب کنید.",
                    "help_text": "نزدیک‌ترین گزینه را انتخاب کنید.",
                    "type": "single_choice",
                    "required": True,
                    "choices": ["فوری", "عادی"],
                    "placeholder": "",
                },
            ],
        }
    ]


class WorkspaceFormTests(SimpleTestCase):
    def test_access_form_normalizes_login_and_separate_delivery_phone(self):
        form = WorkspaceAccessForm(
            data={
                "authorized_phone": "۰۹۱۲ ۰۰۰ ۰۰۷۱",
                "delivery_target": "other",
                "recipient_phone": "+98 935 000 0072",
                "password": "Customer-Room-2026!",
                "expires_in_days": "30",
                "send_now": "on",
                "confirm": "on",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["authorized_phone"], "989120000071")
        self.assertEqual(form.cleaned_data["recipient_phone"], "989350000072")

    def test_access_form_requires_recipient_when_delivery_target_differs(self):
        form = WorkspaceAccessForm(
            data={
                "authorized_phone": "09120000071",
                "delivery_target": "other",
                "recipient_phone": "",
                "expires_in_days": "30",
                "confirm": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("recipient_phone", form.errors)

    def test_builder_round_trip_preserves_frozen_schema(self):
        initial = questionnaire_rows_from_schema(form_schema())
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "120",
        }
        for index, row in enumerate(initial):
            for key, value in row.items():
                data[f"form-{index}-{key}"] = value
            if row["required"]:
                data[f"form-{index}-required"] = "on"
        formset = QuestionnaireRowFormSet(data=data, form_kwargs={"lang": "fa"})

        self.assertTrue(formset.is_valid(), formset.errors)
        self.assertEqual(questionnaire_schema_from_formset(formset), form_schema())

    def test_builder_rejects_choice_question_without_two_choices(self):
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "120",
            "form-0-section_title": "بخش",
            "form-0-question_label": "یک گزینه را انتخاب کنید",
            "form-0-answer_type": "single_choice",
            "form-0-choices": "فقط یک گزینه",
            "form-0-required": "on",
        }
        formset = QuestionnaireRowFormSet(data=data, form_kwargs={"lang": "fa"})

        self.assertFalse(formset.is_valid())
        self.assertIn("حداقل دو گزینه", str(formset.errors))

    def test_dynamic_questionnaire_rejects_unapproved_choice(self):
        section = form_schema()[0]
        form = DynamicQuestionnaireSectionForm(
            data={"workflow": "شرح کامل فرآیند جاری", "priority": "گزینه جعلی"},
            section=section,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)
