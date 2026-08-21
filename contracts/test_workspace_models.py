from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import User

from .models import (
    ContractProposal,
    GeneralTermsTemplate,
    GeneralTermsVersion,
    RoomAccessGrant,
    RoomDelivery,
    RoomEvent,
    SpecialistAssignment,
    SpecialistFormTemplate,
    SpecialistFormTemplateVersion,
)


def valid_schema():
    return [
        {
            "key": "business",
            "title": "شناخت کسب‌وکار",
            "description": "فرآیند واقعی را توضیح دهید.",
            "questions": [
                {
                    "key": "workflow",
                    "label": "فرآیند فعلی شما چگونه است؟",
                    "help_text": "با یک نمونه واقعی توضیح دهید.",
                    "type": "long_text",
                    "required": True,
                    "choices": [],
                    "placeholder": "مثال واقعی…",
                }
            ],
        }
    ]


class WorkspaceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="workspace-root",
            email="workspace@example.com",
            password="safe-password",
        )
        self.general_template = GeneralTermsTemplate.objects.create(
            name="شرایط عمومی آزمون",
            slug="workspace-general-test",
        )
        self.general_version = GeneralTermsVersion.objects.create(
            template=self.general_template,
            number=1,
            title="شرایط عمومی",
            body="ماده ۱ ـ متن معتبر شرایط عمومی",
            created_by=self.user,
        )
        self.general_template.current_version = self.general_version
        self.general_template.full_clean()
        self.general_template.save(update_fields=("current_version", "updated_at"))
        self.form_template = SpecialistFormTemplate.objects.create(
            name="نیازسنجی آزمون",
            slug="workspace-specialist-test",
            service_kind="crm",
        )
        self.form_version = SpecialistFormTemplateVersion.objects.create(
            template=self.form_template,
            number=1,
            schema=valid_schema(),
            created_by=self.user,
        )
        self.form_template.current_version = self.form_version
        self.form_template.full_clean()
        self.form_template.save(update_fields=("current_version", "updated_at"))
        self.proposal = ContractProposal.objects.create(
            customer_name="مشتری آزمون",
            customer_phone="989120000001",
            project_title="پروژه آزمون",
            project_scope="دامنه پروژه",
            amount_irr=10_000_000,
            delivery_terms="چهار هفته",
            general_terms_version=self.general_version,
            created_by=self.user,
        )

    def test_published_specialist_schema_is_normalized_and_immutable(self):
        self.assertEqual(self.form_version.schema[0]["questions"][0]["type"], "long_text")
        self.assertEqual(len(self.form_version.schema_hash), 64)
        original_hash = self.form_version.schema_hash

        self.form_version.schema[0]["questions"][0]["label"] = "متن تغییرکرده"
        with self.assertRaisesMessage(ValidationError, "تغییرپذیر نیست"):
            self.form_version.save()
        self.form_version.refresh_from_db()
        self.assertEqual(self.form_version.schema_hash, original_hash)

    def test_general_terms_version_is_immutable(self):
        original_hash = self.general_version.content_hash
        self.general_version.body = "متن متفاوت"
        with self.assertRaisesMessage(ValidationError, "تغییرپذیر نیست"):
            self.general_version.save()
        self.general_version.refresh_from_db()
        self.assertEqual(self.general_version.content_hash, original_hash)

    def test_template_rejects_a_current_version_from_another_template(self):
        other = SpecialistFormTemplate.objects.create(
            name="فرم دیگر",
            slug="workspace-specialist-other",
        )
        other.current_version = self.form_version
        with self.assertRaises(ValidationError):
            other.full_clean()

    def test_room_password_is_strong_hashed_and_never_stored_raw(self):
        grant = RoomAccessGrant(
            proposal=self.proposal,
            authorized_phone="989120000001",
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            grant.set_password("short-pass")

        raw_password = "Rvn-Client-2026!"
        grant.set_password(raw_password)
        grant.full_clean()
        grant.save()
        self.assertNotEqual(grant.password_hash, raw_password)
        self.assertTrue(grant.check_password(raw_password))
        self.assertFalse(grant.check_password("wrong-password"))
        self.assertTrue(grant.is_available)

        grant.expires_at = timezone.now() - timedelta(seconds=1)
        self.assertFalse(grant.is_available)

    def test_only_one_active_credential_per_phone_is_valid(self):
        first = RoomAccessGrant(
            proposal=self.proposal,
            authorized_phone="989120000001",
            credential_version=1,
        )
        first.set_password("First-secret-2026")
        first.save()
        second = RoomAccessGrant(
            proposal=self.proposal,
            authorized_phone="989120000001",
            credential_version=2,
        )
        second.set_password("Second-secret-2026")
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_assignment_state_must_be_json_objects(self):
        assignment = SpecialistAssignment(
            proposal=self.proposal,
            version=self.form_version,
            answers=[],
            progress={},
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_delivery_and_event_reject_cross_proposal_links(self):
        grant = RoomAccessGrant(
            proposal=self.proposal,
            authorized_phone="989120000001",
        )
        grant.set_password("Customer-secret-2026")
        grant.save()
        assignment = SpecialistAssignment.objects.create(
            proposal=self.proposal,
            version=self.form_version,
        )
        other_proposal = ContractProposal.objects.create(
            customer_name="مشتری دوم",
            customer_phone="989120000002",
            project_title="پروژه دوم",
            project_scope="دامنه دوم",
            amount_irr=20_000_000,
            delivery_terms="پنج هفته",
            general_terms_version=self.general_version,
            created_by=self.user,
        )

        delivery = RoomDelivery(
            proposal=other_proposal,
            access_grant=grant,
            recipient_phone="989120000002",
        )
        with self.assertRaises(ValidationError):
            delivery.full_clean()

        event = RoomEvent(
            proposal=other_proposal,
            access_grant=grant,
            assignment=assignment,
            event_type="form_saved",
        )
        with self.assertRaises(ValidationError):
            event.full_clean()


class WorkspaceFoundationMigrationTests(TransactionTestCase):
    migrate_from = ("contracts", "0008_contractacceptance_evidence")
    migrate_to = ("contracts", "0009_generaltermstemplate_roomaccessgrant_and_more")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        other_leaves = [target for target in executor.loader.graph.leaf_nodes() if target[0] != "contracts"]
        from_targets = [self.migrate_from, *other_leaves]
        executor.migrate(from_targets)
        old_apps = executor.loader.project_state(from_targets).apps
        self._seed_legacy_records(old_apps)

        executor = MigrationExecutor(connection)
        other_leaves = [target for target in executor.loader.graph.leaf_nodes() if target[0] != "contracts"]
        to_targets = [self.migrate_to, *other_leaves]
        executor.migrate(to_targets)
        self.apps = executor.loader.project_state(to_targets).apps

    def tearDown(self):
        # Leave the shared test database at the repository's current migration
        # leaves so other tests never observe the historical state.
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _seed_legacy_records(self, apps):
        User = apps.get_model("accounts", "User")
        Customer = apps.get_model("management_portal", "Customer")
        CustomerCase = apps.get_model("management_portal", "CustomerCase")
        CrmOrder = apps.get_model("crm_orders", "CrmOrder")
        CrmSpecialistDiscovery = apps.get_model("crm_orders", "CrmSpecialistDiscovery")
        ContractProposal = apps.get_model("contracts", "ContractProposal")
        ContentType = apps.get_model("contenttypes", "ContentType")

        user = User.objects.create(
            username="legacy-contract-admin",
            email="legacy-contract@example.com",
            password="not-used-in-migration",
            is_staff=True,
        )
        customer = Customer.objects.create(
            name="شرکت دقیق",
            phone="989120000010",
            email="exact@example.com",
        )
        crm = CrmOrder.objects.create(
            organization_name="شرکت دقیق",
            industry="تجهیزات پزشکی",
            organization_size="under_10",
            contact_name="مدیر پروژه",
            job_title="مدیر",
            work_email="exact@example.com",
            phone="989120000010",
            crm_user_count="1_5",
            current_process="فرآیند فعلی",
            main_pain_points="پیگیری دستی",
            success_metrics="کاهش زمان پاسخ",
            critical_workflows="فروش",
            reports_needed="گزارش فروش",
            permission_requirements="سطوح دسترسی",
            hosting_preference="cloud",
            budget_range="estimate",
            expected_timeline="1_2",
            decision_process="مدیرعامل",
            privacy_accepted_at=timezone.now(),
        )
        crm_content_type, _ = ContentType.objects.get_or_create(
            app_label="crm_orders",
            model="crmorder",
        )
        case = CustomerCase.objects.create(
            customer=customer,
            kind="crm",
            customer_name=customer.name,
            contact_name="مدیر پروژه",
            phone=customer.phone,
            email=customer.email,
            source_content_type=crm_content_type,
            source_object_id=crm.pk,
        )
        answers = {"users_access": {"roles": "مدیر و کارشناس فروش"}}
        CrmSpecialistDiscovery.objects.create(
            order=crm,
            answers=answers,
            status="submitted",
        )
        linked = ContractProposal.objects.create(
            customer=customer,
            crm_order=crm,
            customer_name=customer.name,
            customer_phone=customer.phone,
            customer_email=customer.email,
            project_title="CRM دقیق",
            project_scope="دامنه قطعی",
            amount_irr=500_000_000,
            delivery_terms="هشت هفته",
            general_terms="ماده ۱ ـ متن عمومی حفظ‌شده",
            created_by=user,
        )
        unrelated = ContractProposal.objects.create(
            customer_name=customer.name,
            customer_phone="989120000099",
            project_title="نام مشابه بدون منبع",
            project_scope="نباید به پرونده وصل شود",
            amount_irr=100_000_000,
            delivery_terms="چهار هفته",
            created_by=user,
        )
        self.linked_id = linked.pk
        self.unrelated_id = unrelated.pk
        self.case_id = case.pk
        self.answers = answers

    def test_migration_preserves_exact_links_terms_and_specialist_draft(self):
        ContractProposal = self.apps.get_model("contracts", "ContractProposal")
        SpecialistAssignment = self.apps.get_model("contracts", "SpecialistAssignment")
        SpecialistFormTemplate = self.apps.get_model("contracts", "SpecialistFormTemplate")
        RoomAccessGrant = self.apps.get_model("contracts", "RoomAccessGrant")

        linked = ContractProposal.objects.get(pk=self.linked_id)
        unrelated = ContractProposal.objects.get(pk=self.unrelated_id)
        self.assertEqual(linked.customer_case_id, self.case_id)
        self.assertIsNone(unrelated.customer_case_id)
        self.assertEqual(linked.general_terms_version.body, "ماده ۱ ـ متن عمومی حفظ‌شده")
        self.assertIsNotNone(linked.last_activity_at)

        assignment = SpecialistAssignment.objects.get(proposal_id=linked.pk)
        self.assertEqual(assignment.answers, self.answers)
        self.assertEqual(assignment.status, "submitted")
        self.assertEqual(assignment.revision, 1)
        self.assertIsNotNone(assignment.last_saved_at)
        self.assertEqual(assignment.version.template.slug, "crm-enterprise-noorbinan")
        self.assertIsInstance(assignment.version.schema, list)
        self.assertEqual(
            SpecialistFormTemplate.objects.get(slug="crm-enterprise-noorbinan").current_version_id,
            assignment.version_id,
        )

        # Legacy rooms deliberately stay on the fallback access mechanism until
        # an administrator creates a per-customer credential.
        self.assertFalse(RoomAccessGrant.objects.exists())
