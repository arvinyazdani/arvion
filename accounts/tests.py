import re
from io import StringIO
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from assessments.models import Attempt, AttemptResult, Exam, ExamEntitlement, ExamVersion, Order, PaymentTransaction


User = get_user_model()


class StaffRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_staff_roles", stdout=StringIO())

    def make_staff(self, role):
        user = User.objects.create_user(
            username=f"{role}@example.com", email=f"{role}@example.com",
            password="safe-staff-password-42", is_active=True,
        )
        call_command(
            "setup_staff_roles", email=user.email, role=role, stdout=StringIO()
        )
        user.refresh_from_db()
        return user

    def test_setup_command_is_idempotent_and_creates_expected_roles(self):
        call_command("setup_staff_roles", stdout=StringIO())
        self.assertEqual(
            set(Group.objects.filter(name__startswith="rvion_").values_list("name", flat=True)),
            {"rvion_sales", "rvion_assessments", "rvion_support", "rvion_content", "rvion_analytics"},
        )

    def test_roles_follow_least_privilege_boundaries(self):
        sales = self.make_staff("sales")
        self.assertTrue(sales.has_perm("leads.view_lead"))
        self.assertTrue(sales.has_perm("leads.change_lead"))
        self.assertFalse(sales.has_perm("leads.delete_lead"))
        self.assertFalse(sales.has_perm("blog.view_post"))

        support = self.make_staff("support")
        self.assertTrue(support.has_perm("assessments.change_supportticket"))
        self.assertTrue(support.has_perm("assessments.view_order"))
        self.assertFalse(support.has_perm("assessments.change_order"))

        assessment = self.make_staff("assessments")
        self.assertTrue(assessment.has_perm("assessments.change_question"))
        self.assertTrue(assessment.has_perm("assessments.view_paymenttransaction"))
        self.assertFalse(assessment.has_perm("accounts.view_user"))

        content = self.make_staff("content")
        self.assertTrue(content.has_perm("blog.change_post"))
        self.assertTrue(content.has_perm("services.change_service"))
        self.assertFalse(content.has_perm("blog.delete_post"))
        self.assertFalse(content.has_perm("leads.view_lead"))

    def test_sales_dashboard_and_admin_hide_other_departments(self):
        sales = self.make_staff("sales")
        self.client.force_login(sales)

        dashboard = self.client.get(reverse("admin_operations"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "درخواست‌های جدید")
        self.assertNotContains(dashboard, "پیش‌نویس محتوا")
        self.assertNotContains(dashboard, "سفارش‌های معلق")
        self.assertEqual(self.client.get(reverse("admin:leads_lead_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:blog_post_changelist")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:accounts_user_changelist")).status_code, 403)

    def test_non_staff_cannot_open_operations_dashboard(self):
        user = User.objects.create_user(
            username="customer@example.com", email="customer@example.com",
            password="customer-password-42", is_active=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("admin_operations"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_superuser_sees_persian_task_groups_and_can_assign_ready_role(self):
        admin_user = User.objects.create_superuser(
            username="owner@example.com", email="owner@example.com", password="owner-safe-password-42"
        )
        colleague = User.objects.create_user(
            username="staff@example.com", email="staff@example.com", password="staff-safe-password-42",
            is_active=True,
        )
        self.client.force_login(admin_user)
        index = self.client.get(reverse("admin:index"))
        self.assertContains(index, "کاربران و دسترسی‌ها")
        self.assertContains(index, "پرداخت، آزمون و پشتیبانی")
        response = self.client.post(reverse("admin:accounts_user_changelist"), {
            "action": "assign_assessment_role", "_selected_action": [colleague.pk], "index": "0",
        }, follow=True)
        self.assertContains(response, "نقش «آزمون و پرداخت»")
        colleague.refresh_from_db()
        self.assertTrue(colleague.is_staff)
        self.assertTrue(colleague.groups.filter(name="rvion_assessments").exists())

    def test_admin_is_forced_to_persian_even_with_english_browser(self):
        response = self.client.get(reverse("admin:login"), HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, "fa")
        self.assertContains(response, "نام کاربری")


class AccountFlowTests(TestCase):
    def setUp(self):
        cache.clear()

    def registration_payload(self):
        return {
            "first_name": "Arvin",
            "last_name": "Yazdani",
            "email": "ARVIN@example.com",
            "mobile": "09120373271",
            "password1": "A-secure-test-password-42",
            "password2": "A-secure-test-password-42",
        }

    def test_registration_creates_inactive_user_and_sends_sms_verification(self):
        response = self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        self.assertRedirects(response, reverse("accounts:verify_phone") + "?lang=en")
        user = User.objects.get(email="arvin@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(user.username, user.email)
        self.assertEqual(user.mobile, "989120373271")
        self.assertEqual(user.phone_verifications.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(MANUAL_ACCOUNT_APPROVAL=True)
    def test_sms_verification_supersedes_manual_account_approval(self):
        response = self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload(), follow=True)
        user = User.objects.get(email="arvin@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, "Enter the code we texted you")

    def test_registration_requires_first_and_last_name(self):
        payload = self.registration_payload()
        payload["first_name"] = ""
        payload["last_name"] = ""
        response = self.client.post(reverse("accounts:register") + "?lang=en", payload)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "first_name", "This field is required.")
        self.assertFormError(response.context["form"], "last_name", "This field is required.")
        self.assertFalse(User.objects.filter(email="arvin@example.com").exists())

    def test_registration_rejects_common_gmail_domain_typo(self):
        payload = self.registration_payload()
        payload["email"] = "ali@gmail.con"
        response = self.client.post("/fa/account/register/", payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["email"],
            ["پسوند ایمیل اشتباه است؛ منظورتان gmail.com است؟"],
        )
        self.assertFalse(User.objects.filter(email="ali@gmail.con").exists())

    def test_auth_forms_are_not_cached(self):
        for name in ("accounts:register", "accounts:login"):
            response = self.client.get(reverse(name))
            self.assertIn("no-cache", response.headers["Cache-Control"])

    def test_expired_csrf_returns_actionable_persian_page(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            "/fa/account/login/",
            {"username": "user@example.com", "password": "irrelevant"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "صفحه ورود نیاز به تازه‌سازی دارد", status_code=403)
        self.assertEqual(response.headers["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0")

    def test_user_can_complete_certificate_identity(self):
        user = User.objects.create_user(
            username="legacy@example.com", email="legacy@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile_identity") + "?lang=en",
            {"first_name": "  Legacy ", "last_name": " User  Name "},
        )

        self.assertRedirects(response, reverse("accounts:dashboard") + "?lang=en")
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Legacy")
        self.assertEqual(user.last_name, "User Name")

    @patch("accounts.services.send_otp", return_value=SimpleNamespace(reference="test-ref"))
    def test_phone_verification_activates_and_logs_user_in(self, mocked_send):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        code = mocked_send.call_args.args[1]
        response = self.client.post(reverse("accounts:verify_phone") + "?lang=en", {"code": code})
        user = User.objects.get(email="arvin@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertIsNotNone(user.mobile_verified_at)
        self.assertRedirects(response, reverse("accounts:dashboard") + "?lang=en")

    def test_unverified_user_cannot_log_in(self):
        self.client.post(reverse("accounts:register"), self.registration_payload())
        response = self.client.post(reverse("accounts:login"), {"username": "arvin@example.com", "password": "A-secure-test-password-42"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(AUTH_LOGIN_ATTEMPTS=2, AUTH_LOGIN_WINDOW_SECONDS=60)
    def test_login_is_temporarily_blocked_after_repeated_failures(self):
        user = User.objects.create_user(
            username="verified@example.com", email="verified@example.com",
            password="A-secure-test-password-42", is_active=True, email_verified=True,
        )
        url = reverse("accounts:login") + "?lang=en"
        for _ in range(2):
            response = self.client.post(url, {"username": user.email, "password": "wrong-password"})
            self.assertEqual(response.status_code, 200)

        blocked = self.client.post(url, {"username": user.email, "password": "A-secure-test-password-42"})

        self.assertEqual(blocked.status_code, 200)
        self.assertContains(blocked, "Too many sign-in attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(AUTH_LOGIN_ATTEMPTS=3, AUTH_LOGIN_WINDOW_SECONDS=60)
    def test_successful_login_clears_failure_counter(self):
        user = User.objects.create_user(
            username="success@example.com", email="success@example.com",
            password="A-secure-test-password-42", is_active=True, email_verified=True,
        )
        url = reverse("accounts:login") + "?lang=en"
        self.client.post(url, {"username": user.email, "password": "wrong-password"})

        response = self.client.post(url, {"username": user.email, "password": "A-secure-test-password-42"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_unverified_user_can_request_a_fresh_sms_after_cooldown(self):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        user = User.objects.get(email="arvin@example.com")
        challenge = user.phone_verifications.first()
        challenge.resend_available_at = timezone.now() - timedelta(seconds=1)
        challenge.save(update_fields=["resend_available_at"])

        response = self.client.post(reverse("accounts:verify_phone") + "?lang=en", {"action": "resend"})

        self.assertRedirects(response, reverse("accounts:verify_phone") + "?lang=en")
        self.assertEqual(user.phone_verifications.count(), 2)

    def test_resend_is_disabled_during_two_minute_cooldown(self):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        user = User.objects.get(email="arvin@example.com")
        response = self.client.post(reverse("accounts:verify_phone") + "?lang=en", {"action": "resend"}, follow=True)
        self.assertEqual(user.phone_verifications.count(), 1)
        self.assertContains(response, "Wait until the timer finishes")

    @patch("accounts.services.send_otp", return_value=SimpleNamespace(reference="test-ref"))
    def test_wrong_code_has_five_attempt_limit_and_clear_hint(self, mocked_send):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        url = reverse("accounts:verify_phone") + "?lang=en"
        for remaining in range(4, -1, -1):
            response = self.client.post(url, {"code": "000000"})
            self.assertContains(response, f"{remaining} attempts remain")
        response = self.client.post(url, {"code": mocked_send.call_args.args[1]})
        self.assertContains(response, "Too many attempts")
        self.assertFalse(User.objects.get(email="arvin@example.com").is_active)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_dashboard_language_follows_url_prefix_not_saved_preference(self):
        user = User.objects.create_user(
            username="language@example.com", email="language@example.com",
            password="test-password-42", is_active=True, email_verified=True,
            preferred_language="fa",
        )
        self.client.force_login(user)

        english = self.client.get("/en/account/dashboard/")

        self.assertEqual(english.status_code, 200)
        self.assertEqual(english.context["lang"], "en")
        self.assertContains(english, "Hello, language@example.com")
        self.assertContains(english, 'href="/fa/account/dashboard/"', html=False)
        self.assertContains(english, "Purchase history & receipts")
        self.assertNotContains(english, "خرید و پشتیبانی")

    def test_dashboard_has_mobile_safe_account_structure(self):
        user = User.objects.create_user(
            username="very-long-customer-address@example.com",
            email="very-long-customer-address@example.com",
            password="test-password-42", is_active=True, email_verified=True,
        )
        self.client.force_login(user)
        response = self.client.get("/fa/account/dashboard/")
        self.assertContains(response, 'class="account-language-switch"', html=False)
        self.assertContains(response, 'class="account-email" dir="ltr"', html=False)
        self.assertContains(response, 'class="dashboard-account-links"', html=False)

    def create_result(self, user, exam, version, number):
        order = Order.objects.create(user=user, exam=exam, amount_irr=500_000, status="paid")
        entitlement = ExamEntitlement.objects.create(
            user=user, exam=exam, order=order, attempts_remaining=0,
        )
        attempt = Attempt.objects.create(
            user=user, exam=exam, version=version, entitlement=entitlement,
            status="completed", completion_reason="manual", integrity_score=100 - number,
        )
        return AttemptResult.objects.create(
            attempt=attempt, correct_count=40, incorrect_count=10, unanswered_count=0,
            percentage=80, level_code="advanced", level_title_fa="پیشرفته",
            level_title_en="Advanced", summary_fa="خلاصه", summary_en="Summary",
        )

    def test_results_history_requires_login(self):
        response = self.client.get(reverse("accounts:results_history"))
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('accounts:results_history')}"
        )

    def test_results_history_only_exposes_signed_in_users_results(self):
        owner = User.objects.create_user(
            username="owner@example.com", email="owner@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        stranger = User.objects.create_user(
            username="stranger@example.com", email="stranger@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="history-exam", title_fa="آزمون مالک", title_en="Owner assessment",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        other_exam = Exam.objects.create(
            slug="private-exam", title_fa="نتیجه خصوصی دیگری", title_en="Someone else's result",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        version = ExamVersion.objects.create(exam=exam, version=1, is_published=True)
        other_version = ExamVersion.objects.create(exam=other_exam, version=1, is_published=True)
        owner_result = self.create_result(owner, exam, version, 1)
        self.create_result(stranger, other_exam, other_version, 2)
        self.client.force_login(owner)

        response = self.client.get(reverse("accounts:results_history") + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["results"]), [owner_result])
        self.assertContains(response, "آزمون مالک")
        self.assertNotContains(response, "نتیجه خصوصی دیگری")
        self.assertContains(response, reverse("assessments:result", args=[owner_result.pk]))

    def test_results_history_is_paginated(self):
        user = User.objects.create_user(
            username="archive@example.com", email="archive@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="archive-exam", title_fa="آرشیو", title_en="Archive",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        version = ExamVersion.objects.create(exam=exam, version=1, is_published=True)
        for number in range(11):
            self.create_result(user, exam, version, number)
        self.client.force_login(user)

        first_page = self.client.get(reverse("accounts:results_history") + "?lang=en")
        second_page = self.client.get(reverse("accounts:results_history") + "?lang=en&page=2")

        self.assertEqual(len(first_page.context["results"]), 10)
        self.assertEqual(len(second_page.context["results"]), 1)
        self.assertContains(first_page, "Page 1 of 2")

    def test_orders_history_requires_login(self):
        response = self.client.get(reverse("accounts:orders_history"))
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('accounts:orders_history')}"
        )

    def test_orders_history_only_exposes_signed_in_users_orders(self):
        owner = User.objects.create_user(
            username="buyer@example.com", email="buyer@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        stranger = User.objects.create_user(
            username="other-buyer@example.com", email="other-buyer@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        owner_exam = Exam.objects.create(
            slug="buyer-exam", title_fa="خرید مالک", title_en="Buyer's assessment",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        private_exam = Exam.objects.create(
            slug="other-buyer-exam", title_fa="خرید خصوصی دیگری", title_en="Another private purchase",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        owner_order = Order.objects.create(
            user=owner, exam=owner_exam, amount_irr=500_000, status="paid", gateway="sandbox",
            paid_at=timezone.now(), terms_version="2026-08-05", terms_accepted_at=timezone.now(),
        )
        Order.objects.create(
            user=stranger, exam=private_exam, amount_irr=900_000, status="paid",
        )
        self.client.force_login(owner)

        response = self.client.get(reverse("accounts:orders_history") + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["orders"]), [owner_order])
        self.assertContains(response, "خرید مالک")
        self.assertContains(response, "500000")
        self.assertContains(response, "2026-08-05")
        self.assertNotContains(response, "خرید خصوصی دیگری")

    def test_orders_history_is_paginated(self):
        user = User.objects.create_user(
            username="orders@example.com", email="orders@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="orders-exam", title_fa="خریدها", title_en="Purchases",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        for _ in range(11):
            Order.objects.create(user=user, exam=exam, amount_irr=500_000, status="paid")
        self.client.force_login(user)

        first_page = self.client.get(reverse("accounts:orders_history") + "?lang=en")
        second_page = self.client.get(reverse("accounts:orders_history") + "?lang=en&page=2")

        self.assertEqual(len(first_page.context["orders"]), 10)
        self.assertEqual(len(second_page.context["orders"]), 1)
        self.assertContains(first_page, "Page 1 of 2")

    def test_payment_receipt_is_private_and_shows_verified_transaction(self):
        owner = User.objects.create_user(
            username="receipt@example.com", email="receipt@example.com", password="test-password-42",
            first_name="Receipt", last_name="Owner", is_active=True, email_verified=True,
        )
        stranger = User.objects.create_user(
            username="receipt-stranger@example.com", email="receipt-stranger@example.com",
            password="test-password-42", is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="receipt-exam", title_fa="آزمون رسید", title_en="Receipt assessment",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        order = Order.objects.create(
            user=owner, exam=exam, amount_irr=500_000, status="paid", gateway="sandbox",
            paid_at=timezone.now(), terms_version="2026-08-05", terms_accepted_at=timezone.now(),
        )
        PaymentTransaction.objects.create(
            order=order, gateway="sandbox", external_id="SANDBOX-VERIFIED-001",
            amount_irr=500_000, status="verified", verified_at=timezone.now(),
        )
        url = reverse("accounts:payment_receipt", args=[order.pk]) + "?lang=en"

        self.client.force_login(stranger)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(owner)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Receipt Owner")
        self.assertContains(response, "SANDBOX-VERIFIED-001")
        self.assertContains(response, str(order.pk))
        self.assertContains(response, "not an official tax invoice")

    def test_pending_order_has_no_payment_receipt(self):
        user = User.objects.create_user(
            username="pending-receipt@example.com", email="pending-receipt@example.com",
            password="test-password-42", is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="pending-receipt-exam", title_fa="در انتظار", title_en="Pending",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        order = Order.objects.create(user=user, exam=exam, amount_irr=500_000, status="pending")
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:payment_receipt", args=[order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_password_reset_changes_password_and_preserves_language(self):
        user = User.objects.create_user(
            username="reset@example.com", email="reset@example.com", password="old-password-42",
            first_name="Reset", last_name="User", is_active=True, email_verified=True,
        )
        request = self.client.post(
            reverse("accounts:password_reset") + "?lang=en", {"email": user.email}
        )
        self.assertRedirects(request, reverse("accounts:password_reset_done") + "?lang=en")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Reset your Rvion password")
        self.assertIn("?lang=en", mail.outbox[0].body)
        reset_url = re.search(r"http://testserver([^\s]+)", mail.outbox[0].body).group(1)
        confirm = self.client.get(reset_url, follow=True)
        self.assertEqual(confirm.status_code, 200)
        self.assertContains(confirm, "Choose a new password")
        confirm_url = confirm.redirect_chain[-1][0]

        completed = self.client.post(confirm_url, {
            "new_password1": "A-new-secure-password-84",
            "new_password2": "A-new-secure-password-84",
        })

        self.assertRedirects(completed, reverse("accounts:password_reset_complete") + "?lang=en")
        user.refresh_from_db()
        self.assertTrue(user.check_password("A-new-secure-password-84"))

    def test_password_reset_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("accounts:password_reset") + "?lang=en", {"email": "unknown@example.com"}
        )

        self.assertRedirects(response, reverse("accounts:password_reset_done") + "?lang=en")
        self.assertEqual(len(mail.outbox), 0)
        done = self.client.get(response.url)
        self.assertContains(done, "If an active account exists")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(username="arvin@example.com", email="arvin@example.com", password="test")
        response = self.client.post(reverse("accounts:register"), self.registration_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="arvin@example.com").count(), 1)

    def test_dashboard_groups_multiple_attempts_for_same_exam(self):
        user = User.objects.create_user(
            username="group@example.com", email="group@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="grouped-exam", title_fa="آزمون گروه‌بندی", title_en="Grouped exam",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        for _ in range(2):
            order = Order.objects.create(user=user, exam=exam, amount_irr=500_000, status="paid")
            ExamEntitlement.objects.create(user=user, exam=exam, order=order, attempts_remaining=1)
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.content.decode().count("آزمون گروه‌بندی"), 1)
        self.assertEqual(response.context["assessment_groups"][0]["ready"], 2)
