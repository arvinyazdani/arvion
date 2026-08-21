from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from core.sms.backends import SMSDeliveryError, SMSResult
from management_portal.models import CaseActivity, Customer, CustomerCase

from .models import RoomDelivery, RoomEvent, SpecialistAssignment
from .services import proposal_snapshot
from .workspace_services import (
    create_access_grant,
    create_general_terms_version,
    create_specialist_template_version,
    current_general_terms,
    ensure_case_workspace,
    generate_access_password,
    publish_customer_workspace,
    revoke_access_grant,
    send_workspace_access,
    workspace_progress,
)


def workspace_schema():
    return [
        {
            "key": "goals",
            "title": "هدف‌های پروژه",
            "description": "نتیجه مورد انتظار را مشخص کنید.",
            "questions": [
                {
                    "key": "primary_goal",
                    "label": "مهم‌ترین نتیجه چیست؟",
                    "help_text": "با یک مثال واقعی پاسخ دهید.",
                    "type": "long_text",
                    "required": True,
                    "choices": [],
                    "placeholder": "مثال واقعی…",
                }
            ],
        }
    ]


class WorkspaceServiceTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_superuser(
            username="workspace-manager",
            email="workspace-manager@example.com",
            password="safe-test-password",
        )
        self.customer = Customer.objects.create(
            name="شرکت نمونه",
            phone="09120000011",
            email="customer@example.com",
        )
        self.case = CustomerCase.objects.create(
            customer=self.customer,
            kind="general",
            customer_name=self.customer.name,
            contact_name="مدیر پروژه",
            phone="۰۹۱۲۰۰۰۰۰۱۱",
            email=self.customer.email,
            summary="ساخت سامانه اختصاصی فروش",
        )

    def _workspace_with_questionnaire(self):
        proposal, _created = ensure_case_workspace(case=self.case, actor=self.actor)
        assignment = create_specialist_template_version(
            proposal=proposal,
            schema=workspace_schema(),
            actor=self.actor,
        )
        proposal.private_terms = "شرایط خصوصی معتبر و دقیق این پروژه"
        proposal.amount_irr = 120_000_000
        proposal.save(update_fields=("private_terms", "amount_irr", "updated_at"))
        return proposal, assignment

    def test_workspace_creation_is_idempotent_and_uses_versioned_general_terms(self):
        first, created = ensure_case_workspace(case=self.case, actor=self.actor)
        second, second_created = ensure_case_workspace(case=self.case, actor=self.actor)

        self.assertTrue(created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.customer_case, self.case)
        self.assertEqual(first.customer, self.customer)
        self.assertEqual(first.customer_phone, "989120000011")
        self.assertEqual(first.general_terms, first.general_terms_version.body)
        self.assertTrue(first.clauses.exists())
        self.assertTrue(
            RoomEvent.objects.filter(proposal=first, event_type="workspace_created").exists()
        )
        self.assertTrue(
            CaseActivity.objects.filter(case=self.case, title="فضای اختصاصی مشتری ساخته شد").exists()
        )

    def test_general_terms_revision_switches_current_without_mutating_old_version(self):
        first = create_general_terms_version(body="ماده ۱ ـ نسخه اول", actor=self.actor)
        second = create_general_terms_version(
            body="ماده ۱ ـ نسخه دوم",
            actor=self.actor,
            change_note="اصلاح متن",
        )

        self.assertEqual(second.number, first.number + 1)
        self.assertEqual(current_general_terms(), second)
        first.refresh_from_db()
        self.assertEqual(first.body, "ماده ۱ ـ نسخه اول")

    def test_questionnaire_replacement_is_blocked_after_customer_answer(self):
        proposal, assignment = self._workspace_with_questionnaire()
        assignment.answers = {"goals": {"primary_goal": "نمونه پاسخ کامل مشتری"}}
        assignment.save(update_fields=("answers", "updated_at"))

        with self.assertRaisesMessage(ValidationError, "دارای پاسخ مشتری"):
            create_specialist_template_version(
                proposal=proposal,
                schema=workspace_schema(),
                actor=self.actor,
            )

    def test_generated_password_is_strong_and_rotation_revokes_previous_grant(self):
        proposal, _assignment = self._workspace_with_questionnaire()
        first_password = generate_access_password()
        first = create_access_grant(
            proposal=proposal,
            authorized_phone="09120000011",
            raw_password=first_password,
            actor=self.actor,
        )
        second_password = generate_access_password()
        second = create_access_grant(
            proposal=proposal,
            authorized_phone="+989120000011",
            raw_password=second_password,
            actor=self.actor,
        )

        first.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertIsNotNone(first.revoked_at)
        self.assertEqual(second.credential_version, 2)
        self.assertTrue(second.check_password(second_password))
        self.assertNotIn(second_password, second.password_hash)
        self.assertEqual(
            list(
                RoomEvent.objects.filter(proposal=proposal).values_list(
                    "event_type", flat=True
                )
            )[:2],
            ["access_rotated", "access_created"],
        )

        revoke_access_grant(grant=second, actor=self.actor)
        second.refresh_from_db()
        self.assertFalse(second.is_active)

    @patch("contracts.workspace_services.send_sms")
    def test_delivery_recipient_can_differ_from_authorized_phone(self, send_sms_mock):
        send_sms_mock.return_value = SMSResult(provider="test", reference="sms-42")
        proposal, _assignment = self._workspace_with_questionnaire()
        raw_password = "Strong-Room-2026!"
        grant = create_access_grant(
            proposal=proposal,
            authorized_phone="09120000011",
            raw_password=raw_password,
            actor=self.actor,
        )

        delivery = send_workspace_access(
            proposal=proposal,
            grant=grant,
            recipient_phone="09350000022",
            raw_password=raw_password,
            actor=self.actor,
            absolute_base="https://rvionai.com",
        )

        self.assertEqual(delivery.status, "sent")
        self.assertEqual(delivery.recipient_phone, "989350000022")
        self.assertNotEqual(delivery.recipient_phone, grant.authorized_phone)
        self.assertEqual(delivery.provider_reference, "sms-42")
        sent_to, sent_text = send_sms_mock.call_args.args
        self.assertEqual(sent_to, "989350000022")
        self.assertIn("09120000011", sent_text)
        self.assertIn(raw_password, sent_text)
        self.assertFalse(
            RoomDelivery.objects.filter(error_message__contains=raw_password).exists()
        )

    @patch("contracts.workspace_services.send_sms")
    def test_failed_delivery_is_audited_without_revoking_access(self, send_sms_mock):
        send_sms_mock.side_effect = SMSDeliveryError("provider unavailable")
        proposal, _assignment = self._workspace_with_questionnaire()
        grant = create_access_grant(
            proposal=proposal,
            authorized_phone="09120000011",
            raw_password="Strong-Room-2026!",
            actor=self.actor,
        )

        delivery = send_workspace_access(
            proposal=proposal,
            grant=grant,
            recipient_phone="09120000011",
            raw_password="Strong-Room-2026!",
            actor=self.actor,
            absolute_base="https://rvionai.com",
        )

        self.assertEqual(delivery.status, "failed")
        grant.refresh_from_db()
        self.assertTrue(grant.is_active)
        self.assertTrue(
            RoomEvent.objects.filter(proposal=proposal, event_type="delivery_failed").exists()
        )

    def test_publish_freezes_general_terms_and_questionnaire_schema(self):
        proposal, assignment = self._workspace_with_questionnaire()
        create_access_grant(
            proposal=proposal,
            authorized_phone="09120000011",
            raw_password="Strong-Room-2026!",
            actor=self.actor,
        )

        version = publish_customer_workspace(proposal=proposal, actor=self.actor)
        snapshot = proposal_snapshot(proposal)

        self.assertEqual(version.snapshot["customer_case_id"], self.case.pk)
        self.assertEqual(
            version.snapshot["general_terms_source"]["content_hash"],
            proposal.general_terms_version.content_hash,
        )
        self.assertEqual(
            version.snapshot["specialist_questionnaire"]["schema_hash"],
            assignment.version.schema_hash,
        )
        self.assertEqual(
            version.snapshot["specialist_questionnaire"]["schema"],
            workspace_schema(),
        )
        self.assertEqual(snapshot["specialist_questionnaire"]["assignment_id"], assignment.pk)

    def test_publish_requires_form_private_terms_and_active_access(self):
        proposal, _created = ensure_case_workspace(case=self.case, actor=self.actor)
        with self.assertRaisesMessage(ValidationError, "فرم تخصصی"):
            publish_customer_workspace(proposal=proposal, actor=self.actor)

        create_specialist_template_version(
            proposal=proposal,
            schema=workspace_schema(),
            actor=self.actor,
        )
        with self.assertRaisesMessage(ValidationError, "شرایط خصوصی"):
            publish_customer_workspace(proposal=proposal, actor=self.actor)

        proposal.private_terms = "شرایط خصوصی"
        proposal.save(update_fields=("private_terms", "updated_at"))
        with self.assertRaisesMessage(ValidationError, "دسترسی فعال"):
            publish_customer_workspace(proposal=proposal, actor=self.actor)

    def test_workspace_progress_is_derived_from_actual_answers(self):
        proposal, assignment = self._workspace_with_questionnaire()
        self.assertEqual(workspace_progress(proposal)["percent"], 0)

        assignment.answers = {"goals": {"primary_goal": "افزایش نرخ تبدیل فروش"}}
        assignment.status = "submitted"
        assignment.save(update_fields=("answers", "status", "updated_at"))

        result = workspace_progress(proposal)
        self.assertTrue(result["specialist"]["is_complete"])
        self.assertEqual(result["completed_steps"], 1)
        self.assertEqual(result["percent"], 25)
