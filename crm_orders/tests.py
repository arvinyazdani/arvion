from django.contrib.auth.models import Group
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils import translation

from accounts.models import User
from .forms import CrmOrderForm
from .models import CrmOrder, CrmSpecialistDiscovery
from .specialist import SECTIONS
from .text_export import render_crm_order_text


def valid_payload():
    return {
        "organization_name": "سازمان نمونه", "industry": "توزیع و فروش", "organization_size": "31_100",
        "website": "https://example.com", "contact_name": "علی احمدی", "job_title": "مدیر تحول دیجیتال",
        "work_email": "ali@example.com", "phone": "۰۹۱۲۱۲۳۴۵۶۷",
        "primary_goals": ["sales", "service"], "departments": ["sales", "support", "management"],
        "customer_types": ["people", "businesses"], "lead_sources": ["digital", "referral"],
        "crm_user_count": "16_30", "current_data_sources": ["excel", "business_software"],
        "current_process": "اطلاعات مشتری بین فایل‌های اکسل و تماس‌های تیم توزیع شده است.",
        "main_pain_points": "پیگیری‌ها فراموش می‌شوند، گزارش دقیق نداریم و سابقه مشتری پراکنده است.",
        "success_metrics": "کاهش زمان پاسخ و افزایش نرخ تبدیل فرصت به قرارداد.",
        "required_capabilities": ["customer_360", "pipeline", "tasks", "reports"],
        "customer_data_fields": ["identity", "source", "interactions", "contracts"],
        "assignment_model": "yes", "reminder_types": ["call", "meeting", "contract"],
        "notification_channels": ["in_app", "email"], "correspondence_features": [],
        "ai_use_cases": ["consult"], "reporting_priorities": ["sales", "performance"],
        "system_roles": ["executive", "sales_manager", "sales", "support"],
        "critical_workflows": "سرنخ وارد می‌شود، ارزیابی و تخصیص می‌گیرد، پیشنهاد صادر و سپس قرارداد ثبت می‌شود.",
        "reports_needed": "نرخ تبدیل، زمان پاسخ، ارزش pipeline و عملکرد کارشناسان.",
        "permission_requirements": "کارشناس فقط مشتریان خود و مدیر همه تیم را ببیند.",
        "current_tools": "Excel و نرم‌افزار حسابداری", "devices": ["desktop", "mobile"],
        "mobile_requirement": "responsive", "integration_types": ["website", "accounting"],
        "required_integrations": "وب‌سایت و حسابداری", "migration_types": ["excel"],
        "migration_sources": "سه فایل Excel و دفترچه مشتریان", "approximate_record_count": "25000",
        "hosting_preference": "unsure", "audit_requirement": "all",
        "security_requirements": "ثبت تاریخچه تغییرات و دسترسی نقش‌محور.",
        "delivery_strategy": "phased", "requested_services": ["process", "design_delivery", "training_docs", "support_growth"],
        "budget_range": "250_500", "expected_timeline": "2_4",
        "decision_process": "مدیرعامل و مدیر فروش پس از دریافت پیشنهاد فنی و مالی تصمیم می‌گیرند.",
        "additional_notes": "اجرای مرحله‌ای ترجیح داده می‌شود.", "privacy_accept": "on", "company_fax": "",
    }


class CrmOrderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("fa")

    def test_wizard_is_separate_public_flow_with_accessible_steps(self):
        response = self.client.get(reverse("crm_orders:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نیازسنجی تخصصی CRM سازمانی")
        self.assertContains(response, 'data-wizard="crm-order"', html=False)
        self.assertContains(response, 'aria-label="مراحل سفارش"')

    def test_english_url_redirects_to_persian_until_form_copy_is_translated(self):
        response = self.client.get("/en/crm-order/")
        self.assertRedirects(response, "/fa/crm-order/", fetch_redirect_response=False)

    def test_create_invalid_form_and_thanks_are_never_cached(self):
        create_response = self.client.get(reverse("crm_orders:create"))
        invalid_payload = valid_payload()
        invalid_payload["critical_workflows"] = "کوتاه"
        invalid_response = self.client.post(reverse("crm_orders:create"), invalid_payload)

        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        CrmSpecialistDiscovery.objects.create(order=order)
        thanks_response = self.client.get(
            reverse("crm_orders:thanks", args=[order.tracking_code]),
        )

        for response in (create_response, invalid_response, thanks_response):
            cache_control = response.headers.get("Cache-Control", "")
            self.assertIn("no-store", cache_control)
            self.assertIn("private", cache_control)

    def test_valid_submission_persists_structured_discovery_and_emails_team(self):
        response = self.client.post(reverse("crm_orders:create"), valid_payload(), follow=True)
        order = CrmOrder.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.tracking_code)
        self.assertEqual(order.primary_goals, ["sales", "service"])
        self.assertEqual(order.customer_types, ["people", "businesses"])
        self.assertEqual(order.integration_types, ["website", "accounting"])
        self.assertEqual(order.phone, "09121234567")
        self.assertIsNotNone(order.privacy_accepted_at)
        discovery = CrmSpecialistDiscovery.objects.get(order=order)
        self.assertContains(response, reverse("crm_orders:specialist", args=[discovery.token]))
        self.assertEqual(len(mail.outbox), 1)

    def test_specialist_form_uses_private_token_not_tracking_code(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        discovery = CrmSpecialistDiscovery.objects.create(order=order)

        self.assertEqual(
            self.client.get(reverse("crm_orders:specialist", args=[order.tracking_code])).status_code,
            404,
        )
        response = self.client.get(reverse("crm_orders:specialist", args=[discovery.token]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response.headers["Cache-Control"])

    def test_staff_session_keeps_customer_specialist_token_urls_working(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        discovery = CrmSpecialistDiscovery.objects.create(order=order)
        manager = User.objects.create_superuser(
            username="specialist-link-manager",
            email="specialist-link-manager@example.com",
            password="safe-password",
        )
        self.client.force_login(manager)

        wizard = self.client.get(reverse("crm_orders:specialist", args=[discovery.token]))
        done = self.client.get(reverse("crm_orders:specialist_done", args=[discovery.token]))

        self.assertEqual(wizard.status_code, 200)
        self.assertEqual(done.status_code, 200)
        self.assertContains(wizard, order.organization_name)
        self.assertContains(done, order.organization_name)

    def test_specialist_flow_has_v3_navigation_progress_and_accessible_errors(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        discovery = CrmSpecialistDiscovery.objects.create(order=order)

        first_response = self.client.get(
            reverse("crm_orders:specialist", args=[discovery.token]),
        )
        self.assertContains(first_response, "core/css/tokens.css")
        self.assertContains(first_response, "core/css/components.css")
        self.assertContains(first_response, "crm_orders/specialist.js")
        self.assertContains(first_response, 'role="progressbar"', html=False)
        self.assertContains(first_response, "مرحله ۱ از ۹")
        self.assertNotContains(first_response, "بخش قبل")

        second_key = SECTIONS[1][0]
        second_response = self.client.get(
            reverse("crm_orders:specialist_section", args=[discovery.token, second_key]),
        )
        expected_previous = reverse(
            "crm_orders:specialist_section",
            args=[discovery.token, SECTIONS[0][0]],
        )
        self.assertContains(second_response, f'href="{expected_previous}"', html=False)
        self.assertContains(second_response, "بخش قبل")

        invalid_response = self.client.post(
            reverse("crm_orders:specialist", args=[discovery.token]),
            {question_key: "کوتاه" for question_key, *_ in SECTIONS[0][3]},
        )
        first_question_key = SECTIONS[0][3][0][0]
        self.assertContains(invalid_response, 'data-error-summary', html=False)
        self.assertContains(invalid_response, f'id="id_{first_question_key}-errors"', html=False)
        self.assertContains(invalid_response, 'aria-invalid="true"', html=False)
        self.assertContains(
            invalid_response,
            f'aria-describedby="id_{first_question_key}-help id_{first_question_key}-errors"',
            html=False,
        )
        done_response = self.client.get(
            reverse("crm_orders:specialist_done", args=[discovery.token]),
        )
        self.assertContains(done_response, "core/css/tokens.css")
        self.assertContains(done_response, "core/css/components.css")
        self.assertContains(done_response, "crm_orders/specialist.js")
        self.assertContains(done_response, 'data-copy-status', html=False)

    def test_specialist_cannot_submit_by_skipping_to_last_section(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        discovery = CrmSpecialistDiscovery.objects.create(order=order)
        last_key, _title, _description, questions = SECTIONS[-1]
        payload = {key: "پاسخ معتبر و کامل برای این پرسش" for key, _question, _help in questions}

        response = self.client.post(
            reverse("crm_orders:specialist_section", args=[discovery.token, last_key]),
            payload,
        )

        discovery.refresh_from_db()
        self.assertEqual(discovery.status, "draft")
        self.assertRedirects(
            response,
            reverse("crm_orders:specialist_section", args=[discovery.token, SECTIONS[0][0]]),
        )

    def test_complete_text_report_translates_structured_answers(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        report = render_crm_order_text(order)
        self.assertIn("گزارش کامل نیازسنجی CRM آرویون", report)
        self.assertIn("هدف‌های اصلی CRM: مدیریت فرآیند فروش، خدمات، پشتیبانی و شکایت", report)
        self.assertIn("اتصال‌های موردنیاز: وب‌سایت، حسابداری، انبار یا ERP", report)
        self.assertIn("سه فایل Excel و دفترچه مشتریان", report)
        self.assertNotIn("['sales', 'service']", report)

    def test_admin_can_download_single_crm_text_report(self):
        form = CrmOrderForm(valid_payload())
        self.assertTrue(form.is_valid())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        admin_user = User.objects.create_superuser(
            username="owner@example.com", email="owner@example.com", password="safe-admin-password-42"
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:crm_orders_crmorder_download_text", args=(order.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn(f'filename="crm-{order.tracking_code}.txt"', response["Content-Disposition"])
        self.assertIn(order.organization_name, response.content.decode("utf-8-sig"))

    def test_short_architecture_answers_are_rejected_server_side(self):
        payload = valid_payload()
        payload["critical_workflows"] = "فروش"
        response = self.client.post(reverse("crm_orders:create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "critical_workflows", "لطفاً حداقل ۲۰ کاراکتر توضیح دهید.")
        self.assertFalse(CrmOrder.objects.exists())
        self.assertContains(response, "فرم هنوز ثبت نشده است")
        self.assertContains(response, 'data-error-step="4"', html=False)
        self.assertContains(response, 'aria-invalid="true"', html=False)
        self.assertContains(response, 'aria-describedby="id_critical_workflows-help id_critical_workflows-errors"', html=False)
        self.assertContains(response, 'href="#id_critical_workflows"', html=False)

    def test_checkbox_groups_have_accessible_group_semantics(self):
        response = self.client.get(reverse("crm_orders:create"))
        self.assertContains(response, '<fieldset class="field crm-options" data-field-name="primary_goals" aria-required="true">', html=False)
        self.assertContains(response, "<legend>هدف‌های اصلی CRM", html=False)

    def test_browser_receives_same_minimum_length_as_server(self):
        response = self.client.get(reverse("crm_orders:create"))
        for field_name in ("current_process", "main_pain_points", "critical_workflows", "decision_process"):
            self.assertContains(response, f'name="{field_name}"', html=False)
        self.assertEqual(response.context["form"].fields["current_process"].widget.attrs["minlength"], 20)

    def test_honeypot_rejects_bot_submission(self):
        payload = valid_payload()
        payload["company_fax"] = "spam"
        form = CrmOrderForm(payload)
        self.assertFalse(form.is_valid())
        self.assertIn("company_fax", form.errors)

    def test_mutually_exclusive_none_options_are_rejected(self):
        payload = valid_payload()
        payload["migration_types"] = ["none", "excel"]
        form = CrmOrderForm(payload)
        self.assertFalse(form.is_valid())
        self.assertIn("migration_types", form.errors)

    def test_correspondence_and_ai_are_optional_discovery_inputs(self):
        payload = valid_payload()
        payload["required_capabilities"] = ["customer_360", "correspondence"]
        payload["correspondence_features"] = ["incoming", "numbering_routing", "deadline_approval"]
        payload["ai_use_cases"] = ["writing", "summary"]
        form = CrmOrderForm(payload)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_sales_role_receives_crm_order_permissions(self):
        call_command("setup_staff_roles", verbosity=0)
        group = Group.objects.get(name="rvion_sales")
        self.assertTrue(group.permissions.filter(codename="view_crmorder").exists())
        self.assertTrue(group.permissions.filter(codename="change_crmorder").exists())
        self.assertFalse(group.permissions.filter(codename="delete_crmorder").exists())

    def test_specialist_discovery_excludes_accounting_integration_questions(self):
        section_keys = [key for key, *_ in SECTIONS]
        question_text = " ".join(question for _, _, _, questions in SECTIONS for _, question, _ in questions)
        self.assertNotIn("integrations", section_keys)
        self.assertNotIn("هلو", question_text)
        self.assertNotIn("حسابداری", question_text)
