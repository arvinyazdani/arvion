from django.template import Context, Template
from django.test import SimpleTestCase


class ManagementPresentationTranslationTests(SimpleTestCase):
    def render(self, source, **context):
        return Template("{% load management_i18n %}" + source).render(Context(context))

    def test_system_notification_vocabulary_is_english_in_english_workspace(self):
        rendered = self.render(
            "{{ title|management_notification_title:lang }} / "
            "{{ description|management_notification_description:lang }}",
            title="تأیید پرداخت از مهلت عبور کرده است",
            description="شماره پیگیری: ABC-120",
            lang="en",
        )
        self.assertEqual(rendered, "Payment review is overdue / Reference: ABC-120")

    def test_followup_and_campaign_audit_vocabulary_is_localized(self):
        from .customer_analytics import EVENT_CATEGORY_LABELS
        from .models import CustomerEvent
        self.assertEqual(set(EVENT_CATEGORY_LABELS), {code for code, _ in CustomerEvent.CATEGORIES})
        for code, fa, en in (
            ("followup_task_created", "ساخت وظیفه پیگیری", "Follow-up task created"),
            ("followup_task_status", "تغییر وضعیت وظیفه پیگیری", "Follow-up task status changed"),
            ("sms_campaign_started", "آغاز ارسال کمپین پیامکی", "SMS campaign started"),
        ):
            for lang, expected in (("fa", fa), ("en", en)):
                with self.subTest(code=code, lang=lang):
                    self.assertEqual(self.render("{{ action|management_audit_action:lang }}", action=code, lang=lang), expected)
        self.assertEqual(self.render("{{ target|management_target_type:lang }}", target="case_task", lang="fa"), "وظیفه پرونده")

    def test_audit_codes_and_generated_summary_are_readable_in_english(self):
        rendered = self.render(
            "{{ action|management_audit_action:lang }} / "
            "{{ summary|management_audit_summary:lang }} / "
            "{{ target|management_target_type:lang }}",
            action="payment_approve",
            summary="رسید PAY-7: approved",
            target="manual_payment",
            lang="en",
        )
        self.assertEqual(rendered, "Payment approved / Receipt PAY-7: approved / Payment receipt")

    def test_persian_workspace_keeps_evidence_exactly_as_stored(self):
        rendered = self.render(
            "{{ title|management_notification_title:lang }} / "
            "{{ action|management_audit_action:lang }} / "
            "{{ target|management_target_type:lang }} / "
            "{{ summary|management_audit_summary:lang }}",
            title="قرارداد تأیید شد",
            action="payment_approve",
            target="manual_payment",
            summary="رسید PAY-7: approved",
            lang="fa",
        )
        self.assertEqual(rendered, "قرارداد تأیید شد / تأیید پرداخت / رسید پرداخت / رسید PAY-7: تأییدشده")

    def test_known_case_system_copy_is_translated_but_customer_text_is_not(self):
        rendered = self.render(
            "{{ system|management_case_text:lang }} / {{ dynamic|management_case_text:lang }} / "
            "{{ customer|management_case_text:lang }}",
            system="پرونده مشتری ساخته شد",
            dynamic="پیش‌نویس قرارداد: سامانه فروش",
            customer="مشتری متن آزاد فارسی وارد کرده است",
            lang="en",
        )
        self.assertEqual(
            rendered,
            "Customer case created / Contract draft: سامانه فروش / مشتری متن آزاد فارسی وارد کرده است",
        )
