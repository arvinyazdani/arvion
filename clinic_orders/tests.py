from django.contrib.auth.models import Group
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils import translation

from accounts.models import User
from .forms import ClinicOrderForm
from .models import ClinicOrder
from .text_export import render_clinic_order_text


def valid_payload():
    return {
        "clinic_name": "کلینیک نمونه آفتاب", "clinic_type": "medical", "city": "تهران", "branch_count": "2", "specialties": "داخلی، تغذیه و آموزش سلامت", "practitioner_count": "8", "website": "", "contact_name": "علی احمدی", "job_title": "مدیر کلینیک", "work_email": "clinic@example.com", "phone": "۰۹۱۲۱۲۳۴۵۶۷",
        "primary_goals": ["appointments", "payments", "education", "webinars"], "target_audiences": ["patients", "families"], "current_channels": ["phone", "messenger"], "current_process": "مراجع تلفنی درخواست نوبت می‌دهد و پذیرش زمان آزاد پزشک را دستی بررسی می‌کند.", "main_pain_points": "تماس‌های زیاد، خطای ثبت زمان، پرداخت نامشخص و پراکندگی محتوای آموزشی داریم.", "success_metrics": "کاهش تماس پذیرش، افزایش نوبت قطعی و رشد مشاهده محتوای آموزشی.",
        "visit_modes": ["in_person", "video"], "schedule_model": "practitioner", "appointment_rules": "هر خدمت مدت مشخص دارد و لغو تا بیست‌وچهار ساعت قبل مجاز است.", "intake_requirements": "نام، شماره تماس، انتخاب خدمت و پذیرش قوانین", "reminder_channels": ["sms", "email"], "waitlist_requirement": "yes", "practitioner_features": ["profile", "schedule", "services", "leave"], "patient_account_features": ["booking", "payments", "history", "content", "webinars"],
        "payment_methods": ["online", "onsite"], "pricing_model": "doctor", "insurance_requirement": "info", "cancellation_refund_rules": "لغو تا بیست‌وچهار ساعت قبل با بازپرداخت کامل و پس از آن با بررسی مدیر انجام می‌شود.", "financial_documents": ["receipt", "discount", "refund", "reports"],
        "content_types": ["articles", "audio", "video", "faq"], "content_access": "mixed", "publishing_workflow": "متخصص محتوا را آماده می‌کند و مدیر علمی پیش از انتشار آن را بازبینی و تأیید می‌کند.", "media_requirements": "ویدیوهای حداکثر یک ساعت و فایل صوتی با امکان ادامه پخش", "webinar_features": ["landing", "capacity", "payment", "reminder", "external", "recording"], "webinar_platform": "external", "expected_live_attendees": "200",
        "system_roles": ["owner", "reception", "doctor", "content", "finance", "patient"], "record_scope": "intake", "notification_channels": ["sms", "email"], "integration_types": ["sms", "payment", "webinar", "video"], "required_integrations": "درگاه ایرانی، پیامک و سرویس وبینار", "migration_sources": "حدود صد مقاله و فایل رسانه‌ای موجود", "security_requirements": "دسترسی نقش‌محور، ثبت فعالیت مدیران، رضایت‌نامه و نسخه پشتیبان رمزنگاری‌شده لازم است.", "hosting_preference": "iran_cloud",
        "delivery_strategy": "phased", "requested_services": ["discovery", "design", "development", "infrastructure", "training", "support"], "budget_range": "300_600", "expected_timeline": "4_6", "decision_process": "مدیر کلینیک و مسئول علمی پس از بررسی پیشنهاد فنی و مالی تصمیم نهایی را می‌گیرند.", "additional_notes": "نسخه موبایل واکنش‌گرا اولویت دارد.", "privacy_accept": "on", "company_fax": "",
    }


class ClinicOrderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("fa")

    def test_wizard_is_public_and_has_five_accessible_steps(self):
        response = self.client.get(reverse("clinic_orders:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CLINIC WEBSITE DISCOVERY")
        self.assertContains(response, 'data-wizard="clinic-order"', html=False)
        self.assertContains(response, "ادامه")
        self.assertContains(response, "clinic-wizard.css")
        self.assertContains(response, "crm-options")
        self.assertContains(response, 'aria-label="مراحل نیازسنجی کلینیک"', html=False)
        self.assertEqual(response.content.decode().count("data-step-indicator="), 6)

    def test_english_url_redirects_to_persian_until_form_copy_is_translated(self):
        response = self.client.get("/en/clinic-order/")
        self.assertRedirects(response, "/fa/clinic-order/", fetch_redirect_response=False)

    def test_valid_submission_persists_and_returns_tracking_code(self):
        response = self.client.post(reverse("clinic_orders:create"), valid_payload(), follow=True)
        order = ClinicOrder.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.tracking_code)
        self.assertEqual(order.phone, "09121234567")
        self.assertEqual(order.content_types, ["articles", "audio", "video", "faq"])
        self.assertEqual(len(mail.outbox), 1)

    def test_text_export_translates_choices(self):
        form = ClinicOrderForm(valid_payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        report = render_clinic_order_text(order)
        self.assertIn("گزارش کامل نیازسنجی وب‌سایت کلینیک آرویون", report)
        self.assertIn("مقاله، فایل و دوره صوتی، ویدیو و دوره آموزشی", report)
        self.assertNotIn("['articles'", report)

    def test_short_rules_are_rejected_on_correct_step(self):
        payload = valid_payload()
        payload["appointment_rules"] = "نوبت ثابت"
        response = self.client.post(reverse("clinic_orders:create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ClinicOrder.objects.exists())
        self.assertContains(response, 'data-error-step="4"', html=False)
        self.assertContains(response, 'aria-invalid="true"', html=False)
        self.assertContains(response, 'href="#id_appointment_rules"', html=False)

    def test_checkbox_groups_have_accessible_group_semantics(self):
        response = self.client.get(reverse("clinic_orders:create"))
        self.assertContains(response, '<fieldset class="field crm-options" data-field-name="primary_goals" aria-required="true">', html=False)
        self.assertContains(response, "<legend>هدف‌های اصلی پروژه", html=False)

    def test_internal_webinar_requires_capacity(self):
        payload = valid_payload()
        payload["webinar_platform"] = "internal"
        payload["expected_live_attendees"] = ""
        form = ClinicOrderForm(payload)
        self.assertFalse(form.is_valid())
        self.assertIn("expected_live_attendees", form.errors)

    def test_admin_can_download_complete_text(self):
        form = ClinicOrderForm(valid_payload())
        self.assertTrue(form.is_valid())
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        admin = User.objects.create_superuser(username="owner@example.com", email="owner@example.com", password="safe-password-42")
        self.client.force_login(admin)
        response = self.client.get(reverse("admin:clinic_orders_clinicorder_download_text", args=(order.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(order.clinic_name, response.content.decode("utf-8-sig"))

    def test_sales_role_receives_clinic_order_permissions(self):
        call_command("setup_staff_roles", verbosity=0)
        group = Group.objects.get(name="rvion_sales")
        self.assertTrue(group.permissions.filter(codename="view_clinicorder").exists())
        self.assertTrue(group.permissions.filter(codename="change_clinicorder").exists())
        self.assertFalse(group.permissions.filter(codename="delete_clinicorder").exists())
