from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from contracts.models import ContractProposal, ContractReview, ContractRoomAcknowledgement
from contracts.services import add_default_clauses, publish_version
from django.utils import timezone


class ContractWorkflowTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(username="contract-root", email="contracts@example.com", password="safe-password")
        self.proposal = ContractProposal.objects.create(
            customer_name="مشتری نمونه", customer_phone="989120373271", project_title="سامانه نمونه",
            project_scope="تحلیل و توسعه نسخه اول", amount_irr=1_000_000_000,
            delivery_terms="۸ هفته", created_by=self.root,
        )
        add_default_clauses(self.proposal)

    def grant_contract_access(self, version):
        session = self.client.session
        session[f"contract-access:{version.pk}"] = self.proposal.customer_phone
        session.save()

    def test_public_link_is_hidden_before_publish(self):
        response = self.client.get(reverse("contracts:contract_document", args=[self.proposal.token]))
        self.assertEqual(response.status_code, 404)

    def test_proposal_form_can_prefill_from_crm_assessment(self):
        crm = CrmOrder.objects.create(
            organization_name="شرکت نمونه", industry="فناوری", organization_size="under_10",
            contact_name="علی نمونه", job_title="مدیر", work_email="ali@example.com", phone="09120373271",
            primary_goals=[], departments=[], customer_types=[], lead_sources=[], crm_user_count="1_5",
            current_process="فرآیند فعلی", current_data_sources=[], main_pain_points="پیگیری دستی",
            success_metrics="کاهش زمان پاسخ", required_capabilities=[], customer_data_fields=[], reminder_types=[],
            notification_channels=[], critical_workflows="", correspondence_features=[], ai_use_cases=[],
            reporting_priorities=[], system_roles=[], reports_needed="", permission_requirements="", budget_range="estimate",
            expected_timeline="1_2", decision_process="مدیرعامل", privacy_accepted_at=timezone.now(),
        )
        self.client.force_login(self.root)
        response = self.client.post(reverse("contracts:proposal_create"), {
            "needs_assessment": f"crm:{crm.pk}", "title": "پیشنهاد CRM", "customer_name": "x",
            "customer_phone": "09120373271", "customer_email": "x@example.com", "client_details": "",
            "project_title": "x", "project_scope": "x", "amount_irr": "1000000",
            "payment_terms": "۵۰/۵۰", "delivery_terms": "۸ هفته",
        })
        self.assertEqual(response.status_code, 302)
        proposal = ContractProposal.objects.latest("created_at")
        self.assertEqual(proposal.customer_name, "علی نمونه")
        self.assertIn("فرآیند فعلی", proposal.project_scope)

    def test_management_contract_routes_use_new_shell(self):
        self.client.force_login(self.root)
        listing = self.client.get(reverse("management_portal:contract_list"))
        self.assertContains(listing, "پیشنهادهای قرارداد")
        self.assertContains(listing, self.proposal.project_title)
        self.assertNotContains(listing, 'href="/admin/')
        detail = self.client.get(reverse("management_portal:contract_detail", args=[self.proposal.pk]))
        self.assertContains(detail, "مدیریت بندها")
        self.assertContains(detail, reverse("management_portal:contract_clauses", args=[self.proposal.pk]))

    def test_specialist_discovery_is_included_in_contract_scope(self):
        crm = CrmOrder.objects.create(
            organization_name="نور بینان", industry="تجهیزات", organization_size="under_10",
            contact_name="مدیر پروژه", job_title="مدیر", work_email="manager@example.com", phone="09120373271",
            crm_user_count="1_5", current_process="فرآیند اولیه", main_pain_points="پیگیری دستی",
            success_metrics="کاهش زمان", critical_workflows="فروش", reports_needed="", permission_requirements="",
            budget_range="estimate", expected_timeline="1_2", decision_process="مدیرعامل", privacy_accepted_at=timezone.now(),
        )
        CrmSpecialistDiscovery.objects.create(order=crm, status="submitted", answers={"نقش‌های واقعی": ["فروش", "مدیر سیستم"]})
        self.client.force_login(self.root)
        response = self.client.post(reverse("management_portal:contract_create"), {
            "needs_assessment": f"crm:{crm.pk}", "title": "پیشنهاد CRM", "customer_name": "x",
            "customer_phone": "09120373271", "customer_email": "x@example.com", "client_details": "",
            "project_title": "x", "project_scope": "x", "amount_irr": "1000000", "payment_terms": "۵۰/۵۰", "delivery_terms": "۸ هفته",
        })
        self.assertEqual(response.status_code, 302)
        proposal = ContractProposal.objects.latest("created_at")
        self.assertIn("نیازسنجی تخصصی", proposal.project_scope)
        self.assertIn("مدیر سیستم", proposal.project_scope)

    def test_publish_creates_immutable_snapshot_and_public_noindex_page(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        original = version.snapshot["project_scope"]
        self.proposal.project_scope = "متن تغییر یافته"
        self.proposal.save()
        version.refresh_from_db()
        self.assertEqual(version.snapshot["project_scope"], original)
        response = self.client.get(reverse("contracts:contract_document", args=[self.proposal.token]))
        self.assertContains(response, "noindex,nofollow,noarchive")
        self.assertContains(response, "پیشنهاد همکاری سامانه نمونه | آرویون")
        self.assertContains(response, "share-contract-v1.png")
        self.assertContains(response, "سامانه نمونه")
        self.assertNotContains(response, "متن تغییر یافته")

    def test_customer_can_reject_clause_only_with_reason_and_suggest_clause(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        accepted = [str(item["id"]) for item in version.snapshot["clauses"]][1:]
        url = reverse("contracts:contract_document", args=[self.proposal.token])
        invalid = self.client.post(url, {"accepted_clauses": accepted, "suggested_clause": "بند پیشنهادی"})
        self.assertContains(invalid, "برای بندهای مورد تأیید نبود")
        valid = self.client.post(url, {"accepted_clauses": accepted, "rejection_notes": "این بند نیازمند مذاکره است.", "suggested_clause": "بند پیشنهادی"})
        self.assertRedirects(valid, url)
        review = ContractReview.objects.get(version=version)
        self.assertEqual(review.suggested_clause, "بند پیشنهادی")
        self.assertEqual(len(review.rejected_clause_ids), 1)

    @override_settings(CONTRACT_ACCESS_PASSWORD="test-contract-password")
    def test_phone_access_requires_matching_number_and_password(self):
        version = publish_version(self.proposal, self.root)
        url = reverse("contracts:contract_access", args=[self.proposal.token])
        self.assertRedirects(self.client.get(reverse("contracts:public_contract", args=[self.proposal.token])), url)
        invalid = self.client.post(url, {"phone": "09120000000", "password": "test-contract-password"})
        self.assertContains(invalid, "شماره همراه یا رمز ورود صحیح نیست")
        response = self.client.post(url, {"phone": "09120373271", "password": "test-contract-password"})
        self.assertRedirects(response, reverse("contracts:public_contract", args=[self.proposal.token]))

    def test_non_superuser_cannot_manage_contracts(self):
        staff = User.objects.create_user(username="staff-c", email="staff-c@example.com", password="safe-password", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("contracts:proposal_list")).status_code, 403)

    def test_manager_can_disable_and_add_clause_without_mutating_old_version(self):
        first = publish_version(self.proposal, self.root)
        old_count = len(first.snapshot["clauses"])
        self.client.force_login(self.root)
        kept = [str(item.pk) for item in self.proposal.clauses.all()[1:]]
        response = self.client.post(reverse("contracts:proposal_clauses", args=[self.proposal.pk]), {
            "enabled_clauses": kept, "custom_title": "بند اختصاصی", "custom_body": "متن بند اختصاصی",
        })
        self.assertRedirects(response, reverse("contracts:proposal_detail", args=[self.proposal.pk]))
        first.refresh_from_db()
        self.assertEqual(len(first.snapshot["clauses"]), old_count)
        second = publish_version(self.proposal, self.root)
        self.assertEqual(len(second.snapshot["clauses"]), old_count)
        self.assertEqual(second.snapshot["clauses"][-1]["title"], "بند اختصاصی")

    @override_settings(SMS_BACKEND="core.sms.backends.ConsoleSMSBackend")
    @patch("contracts.views.secrets.randbelow", return_value=123456)
    def test_otp_acceptance_is_hashed_single_use_and_bound_to_version(self, _random):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")
        ContractReview.objects.create(
            version=version,
            accepted_clause_ids=[str(item["id"]) for item in version.snapshot["clauses"]],
            rejected_clause_ids=[],
        )
        request_url = reverse("contracts:contract_request_otp", args=[self.proposal.token])
        accept_url = reverse("contracts:contract_accept", args=[self.proposal.token])
        response = self.client.post(request_url, {"agreement": "on"})
        self.assertRedirects(response, accept_url)
        challenge = version.otp_challenges.get()
        self.assertNotIn("123456", challenge.code_hash)
        verify_url = reverse("contracts:contract_verify_otp", args=[self.proposal.token])
        self.client.post(verify_url, {"code": "123456"})
        challenge.refresh_from_db()
        self.proposal.refresh_from_db()
        self.assertIsNotNone(challenge.used_at)
        self.assertEqual(self.proposal.status, "accepted")
        self.assertEqual(version.acceptance.verified_phone, self.proposal.customer_phone)
        second = self.client.post(verify_url, {"code": "123456"})
        self.assertRedirects(second, accept_url)
        self.assertEqual(version.otp_challenges.filter(used_at__isnull=False).count(), 1)
