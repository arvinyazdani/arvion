from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from contracts.models import ContractProposal, GeneralTermsVersion, RoomAccessGrant, RoomDelivery
from contracts.workspace_services import (
    create_access_grant,
    create_specialist_template_version,
    ensure_case_workspace,
)
from core.sms.backends import SMSResult

from .models import CaseDocument, CaseDocumentRevision, Customer, CustomerCase, OperationalAudit


SCHEMA = [{
    "key": "goals",
    "title": "اهداف پروژه",
    "description": "نتیجه مورد انتظار",
    "questions": [{
        "key": "main_goal", "label": "هدف اصلی چیست؟",
        "help_text": "یک مثال واقعی بنویسید.", "type": "long_text",
        "required": True, "choices": [], "placeholder": "مثلاً…",
    }],
}]


class CustomerWorkspaceManagementTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_superuser(
            username="workspace-admin", email="workspace-admin@example.com",
            password="safe-test-password",
        )
        self.customer = Customer.objects.create(
            name="شرکت یکپارچه", phone="09120000021", email="client@example.com",
        )
        self.case = CustomerCase.objects.create(
            customer=self.customer, kind="crm", customer_name=self.customer.name,
            contact_name="مدیر پروژه", phone=self.customer.phone,
            email=self.customer.email, summary="سامانه فروش یکپارچه",
        )
        self.client.force_login(self.manager)

    def test_all_staff_can_open_list_while_anonymous_user_is_redirected(self):
        staff = User.objects.create_user(
            username="workspace-staff", email="staff@example.com",
            password="safe-test-password", is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("management_portal:workspace_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.name)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("management_portal:workspace_list")).status_code, 302)

    def test_case_workspace_is_created_once_from_management_flow(self):
        url = reverse("management_portal:workspace_create", args=[self.case.pk])
        self.client.post(url)
        self.client.post(url)
        proposal = ContractProposal.objects.get(customer_case=self.case)
        self.assertEqual(ContractProposal.objects.filter(customer_case=self.case).count(), 1)
        self.assertEqual(proposal.customer, self.customer)
        self.assertTrue(proposal.general_terms_version_id)
        self.assertTrue(OperationalAudit.objects.filter(action="workspace_created").exists())

    def test_detail_displays_archived_snapshot_and_revision_count(self):
        document = CaseDocument.objects.create(
            case=self.case, kind="initial", title="نیازسنجی پایه",
            snapshot={"organization": "شرکت یکپارچه", "needs": {"goal": "فروش سریع‌تر"}},
            checksum="a" * 64,
        )
        CaseDocumentRevision.objects.create(
            document=document, title=document.title, snapshot=document.snapshot,
            checksum=document.checksum,
        )
        ensure_case_workspace(case=self.case, actor=self.manager)
        response = self.client.get(reverse("management_portal:workspace_detail", args=[self.case.pk]))
        self.assertContains(response, "فروش سریع‌تر")
        self.assertContains(response, "1 نسخه")

    def test_contract_form_saves_private_and_commercial_terms(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.manager)
        response = self.client.post(
            reverse("management_portal:workspace_contract_save", args=[self.case.pk]),
            {
                "proposal_id": proposal.pk,
                "title": "بسته قرارداد CRM",
                "project_title": "CRM فروش",
                "project_scope": "مدیریت سرنخ و گزارش",
                "amount_irr": "150000000",
                "payment_terms": "نیمی آغاز، نیمی تحویل",
                "delivery_terms": "هشت هفته",
                "private_terms": "شرایط خصوصی دقیق مشتری",
            },
        )
        self.assertRedirects(
            response,
            reverse("management_portal:workspace_detail", args=[self.case.pk]),
            fetch_redirect_response=False,
        )
        proposal.refresh_from_db()
        self.assertEqual(proposal.amount_irr, 150_000_000)
        self.assertEqual(proposal.private_terms, "شرایط خصوصی دقیق مشتری")

    def test_questionnaire_builder_creates_versioned_assignment(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.manager)
        response = self.client.post(
            reverse("management_portal:workspace_questionnaire", args=[self.case.pk]),
            {
                "template_name": "نیازسنجی CRM شرکت یکپارچه",
                "change_note": "نسخه اول",
                "questions-TOTAL_FORMS": "1", "questions-INITIAL_FORMS": "0",
                "questions-MIN_NUM_FORMS": "1", "questions-MAX_NUM_FORMS": "120",
                "questions-0-section_key": "goals",
                "questions-0-question_key": "main_goal",
                "questions-0-section_title": "اهداف پروژه",
                "questions-0-section_description": "نتیجه مورد انتظار",
                "questions-0-question_label": "هدف اصلی چیست؟",
                "questions-0-help_text": "یک مثال واقعی بنویسید.",
                "questions-0-placeholder": "مثلاً کاهش زمان پاسخ",
                "questions-0-answer_type": "long_text",
                "questions-0-choices": "",
                "questions-0-required": "on",
            },
        )
        self.assertRedirects(response, reverse("management_portal:workspace_detail", args=[self.case.pk]))
        proposal.refresh_from_db()
        self.assertEqual(proposal.specialist_assignment.version.schema[0]["questions"][0]["key"], "main_goal")

    def test_general_terms_revision_does_not_mutate_existing_workspace(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.manager)
        original_id = proposal.general_terms_version_id
        response = self.client.post(reverse("management_portal:workspace_general_terms"), {
            "title": "شرایط عمومی پیمان نسخه تازه",
            "body": "ماده ۱ ـ متن نسخه تازه و مستقل",
            "change_note": "اصلاح آزمایشی",
            "confirm": "on",
        })
        self.assertRedirects(response, reverse("management_portal:workspace_general_terms"))
        proposal.refresh_from_db()
        self.assertEqual(proposal.general_terms_version_id, original_id)
        self.assertNotEqual(GeneralTermsVersion.objects.order_by("-created_at").first().pk, original_id)

    @patch("contracts.workspace_services.send_sms")
    def test_access_can_be_sent_to_a_different_recipient_and_secret_is_shown_once(self, send_sms_mock):
        send_sms_mock.return_value = SMSResult(provider="test", reference="sms-100")
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.manager)
        url = reverse("management_portal:workspace_access_create", args=[self.case.pk])
        response = self.client.post(url, {
            "proposal_id": proposal.pk,
            "authorized_phone": "09120000021",
            "delivery_target": "other",
            "recipient_phone": "09350000031",
            "password": "Strong-Workspace-2026!",
            "expires_in_days": "30",
            "send_now": "on", "confirm": "on",
        })
        self.assertRedirects(
            response,
            reverse("management_portal:workspace_detail", args=[self.case.pk]),
            fetch_redirect_response=False,
        )
        grant = RoomAccessGrant.objects.get(proposal=proposal, is_active=True)
        self.assertTrue(grant.check_password("Strong-Workspace-2026!"))
        self.assertEqual(RoomDelivery.objects.get(proposal=proposal).recipient_phone, "989350000031")
        first = self.client.get(reverse("management_portal:workspace_detail", args=[self.case.pk]))
        self.assertContains(first, "Strong-Workspace-2026!")
        second = self.client.get(reverse("management_portal:workspace_detail", args=[self.case.pk]))
        self.assertNotContains(second, "Strong-Workspace-2026!")

    def test_publish_reports_missing_steps_then_locks_complete_version(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.manager)
        publish_url = reverse("management_portal:workspace_publish", args=[self.case.pk])
        missing = self.client.post(publish_url, {"proposal_id": proposal.pk}, follow=True)
        self.assertContains(missing, "فرم تخصصی این پرونده")
        create_specialist_template_version(proposal=proposal, schema=SCHEMA, actor=self.manager)
        proposal.private_terms = "شرایط خصوصی کامل"
        proposal.amount_irr = 100_000_000
        proposal.save(update_fields=("private_terms", "amount_irr", "updated_at"))
        create_access_grant(
            proposal=proposal, authorized_phone=self.case.phone,
            raw_password="Strong-Workspace-2026!", actor=self.manager,
        )
        published = self.client.post(publish_url, {"proposal_id": proposal.pk})
        self.assertRedirects(published, reverse("management_portal:workspace_detail", args=[self.case.pk]))
        proposal.refresh_from_db()
        self.case.refresh_from_db()
        self.assertEqual(proposal.status, "sent")
        self.assertGreater(proposal.current_version, 0)
        self.assertEqual(self.case.stage, "proposal")
