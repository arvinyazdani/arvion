from pathlib import Path

from django.test import TestCase
from django.utils import timezone, translation

from accounts.models import User
from assessments.models import Exam, ManualPaymentSubmission, Order
from projects.models import Project
from services.models import Service


STATIC_V2 = Path(__file__).resolve().parent / "static" / "management_portal" / "v2"
CONTRACT_STATIC = Path(__file__).resolve().parent.parent / "contracts" / "static" / "contracts"


class ManagementActionSafetyPresentationTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate)
        self.manager = User.objects.create_superuser(
            username="action-safety-root",
            email="action-safety-root@example.com",
            password="safe-password",
        )
        self.client.force_login(self.manager)

    def test_project_and_service_controls_have_localized_status_names_and_unpublish_confirmation(self):
        Project.objects.create(
            title_fa="پروژه فروش",
            title_en="Sales project",
            slug="sales-project-action-safety",
            is_active=True,
        )
        Service.objects.create(
            title_fa="خدمت تحلیل",
            title_en="Analysis service",
            slug="analysis-service-action-safety",
            short_description_fa="خلاصه",
            short_description_en="Summary",
            is_active=False,
        )

        fa = self.client.get("/fa/management/content/")
        self.assertContains(fa, "در حال نمایش در سایت")
        self.assertContains(fa, "از سایت پنهان است")
        self.assertContains(fa, "پنهان‌کردن از سایت")
        self.assertContains(fa, "نمایش در سایت")
        self.assertContains(fa, "پروژه «پروژه فروش» از سایت پنهان شود؟")
        self.assertContains(fa, 'aria-label="پنهان‌کردن پروژه پروژه فروش از سایت"')
        self.assertNotContains(fa, ">✓<")
        self.assertNotContains(fa, ">○<")

        en = self.client.get("/en/management/content/")
        self.assertContains(en, "Visible on site")
        self.assertContains(en, "Hidden from site")
        self.assertContains(en, "Hide from site")
        self.assertContains(en, "Show on site")
        self.assertContains(en, "Hide project “Sales project” from the site?")
        self.assertContains(en, 'aria-label="Hide project Sales project from site"')
        self.assertNotContains(en, "در حال نمایش در سایت")

    def test_account_and_payment_actions_confirm_with_identifying_context_in_both_languages(self):
        customer = User.objects.create_user(
            username="customer-action-safety",
            email="customer-action@example.com",
            mobile="09121234567",
            first_name="مینا",
            last_name="رضایی",
            password="safe-password",
            is_active=False,
            mobile_verified_at=timezone.now(),
        )
        exam = Exam.objects.create(
            slug="action-safety-exam",
            title_fa="آزمون مدیریت",
            title_en="Management assessment",
            description_fa="شرح",
            description_en="Description",
            language_mode="bilingual",
            price_irr=750_000,
        )
        order = Order.objects.create(
            user=customer,
            exam=exam,
            subtotal_irr=750_000,
            amount_irr=750_000,
            gateway="card_transfer",
        )
        ManualPaymentSubmission.objects.create(
            order=order,
            payer_name="مینا رضایی",
            reference_number="PAY-SAFE-750",
            paid_at=timezone.now(),
        )

        fa = self.client.get("/fa/management/approvals/")
        self.assertContains(fa, "09121234567")
        self.assertContains(fa, "حساب مینا رضایی با ایمیل customer-action@example.com فعال شود؟")
        self.assertContains(fa, "درخواست حساب مینا رضایی با ایمیل customer-action@example.com رد شود؟")
        self.assertContains(fa, "رسید PAY-SAFE-750 به نام مینا رضایی با مبلغ 750000 ریال تأیید شود؟")
        self.assertContains(fa, "این اقدام دسترسی آزمون آزمون مدیریت را برای customer-action@example.com صادر می‌کند.")
        self.assertContains(fa, 'aria-label="رد رسید PAY-SAFE-750 متعلق به مینا رضایی"')
        self.assertContains(fa, 'for="review-note-')

        en = self.client.get("/en/management/approvals/")
        self.assertContains(en, "Activate the account for مینا رضایی (customer-action@example.com)?")
        self.assertContains(en, "Reject the account request for مینا رضایی (customer-action@example.com)?")
        self.assertContains(en, "Approve receipt PAY-SAFE-750 from مینا رضایی for 750000 IRR?")
        self.assertContains(en, "This grants customer-action@example.com access to Management assessment.")
        self.assertContains(en, 'aria-label="Approve receipt PAY-SAFE-750 and grant access to customer-action@example.com"')
        self.assertNotContains(en, "منتظر تصمیم مدیر")

    def test_sensitive_get_requests_do_not_mutate_account_or_payment(self):
        customer = User.objects.create_user(
            username="get-safe-customer",
            email="get-safe@example.com",
            password="safe-password",
            is_active=False,
            mobile_verified_at=timezone.now(),
        )

        response = self.client.get(f"/fa/management/approvals/accounts/{customer.pk}/approve/")

        self.assertEqual(response.status_code, 405)
        customer.refresh_from_db()
        self.assertFalse(customer.is_active)


class ManagementActionSafetyStaticTests(TestCase):
    def test_custom_confirmation_preserves_submitter_and_avoids_browser_native_confirm(self):
        script = (STATIC_V2 / "management.js").read_text(encoding="utf-8")
        self.assertIn("event.submitter", script)
        self.assertIn("confirmationDialog.showModal()", script)
        self.assertIn("submission.form.requestSubmit(submission.submitter || undefined)", script)
        self.assertIn('form.dataset.submitting = "true"', script)
        self.assertNotIn("window.confirm(", script)
        self.assertIn('form[data-notification-action]', script)
        self.assertIn('"X-Requested-With": "XMLHttpRequest"', script)
        self.assertIn("HTMLFormElement.prototype.submit.call(form)", script)
        self.assertIn("updateQueueAfterRemoval(card)", script)

        contract_script = (CONTRACT_STATIC / "manager-contracts.js").read_text(encoding="utf-8")
        self.assertNotIn("window.confirm(", contract_script)
        self.assertNotIn('addEventListener("submit"', contract_script)

    def test_action_controls_and_confirmation_dialog_meet_touch_target_contract(self):
        approvals_css = (STATIC_V2 / "approvals.css").read_text(encoding="utf-8")
        shared_css = (STATIC_V2 / "management.css").read_text(encoding="utf-8")
        self.assertIn(".m-confirm-dialog", shared_css)
        self.assertNotIn(".m-confirm-dialog", approvals_css)
        self.assertIn("min-height: 44px", approvals_css)
        self.assertIn("min-height:46px", shared_css)
        self.assertIn("@media (forced-colors: active)", approvals_css)

    def test_shared_management_assets_cover_contract_confirmation_actions(self):
        base = (
            STATIC_V2.parent.parent.parent
            / "templates"
            / "management_portal"
            / "v2"
            / "base.html"
        ).read_text(encoding="utf-8")
        contract_detail = (
            CONTRACT_STATIC.parent.parent
            / "templates"
            / "contracts"
            / "proposal_detail_v2.html"
        ).read_text(encoding="utf-8")
        self.assertIn("management.css' %}?v=15", base)
        self.assertIn("management.js' %}?v=10", base)
        self.assertIn("data-confirm=", contract_detail)
