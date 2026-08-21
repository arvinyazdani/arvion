from django.contrib.contenttypes.models import ContentType
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from leads.models import Lead

from .cases import resolve_customer
from .models import CaseDocument, CaseDocumentRevision, Customer, CustomerCase


def create_lead(*, name, business_name, phone, email, message="شرح اولیه"):
    return Lead.objects.create(
        name=name,
        business_name=business_name,
        email_or_telegram=email,
        phone=phone,
        request_type="webapp",
        budget_range="unsure",
        timeline="flexible",
        preferred_contact="phone",
        message=message,
        privacy_accepted_at=timezone.now(),
    )


def case_for(lead):
    return CustomerCase.objects.get(
        source_content_type=ContentType.objects.get_for_model(lead),
        source_object_id=lead.pk,
    )


class CustomerCaseSyncTests(TestCase):
    def test_equal_display_names_with_different_identifiers_do_not_merge(self):
        first = create_lead(
            name="مدیر اول",
            business_name="شرکت هم‌نام",
            phone="09120000031",
            email="first@example.com",
        )
        second = create_lead(
            name="مدیر دوم",
            business_name="شرکت هم‌نام",
            phone="09120000032",
            email="second@example.com",
        )

        self.assertNotEqual(case_for(first).customer_id, case_for(second).customer_id)
        self.assertEqual(Customer.objects.filter(name="شرکت هم‌نام").count(), 2)

    def test_iranian_phone_variants_resolve_to_one_customer(self):
        first = resolve_customer(
            customer_name="مشتری شماره‌دار",
            contact_name="مخاطب اول",
            phone="۰۹۱۲ ۰۰۰ ۰۰۴۱",
            email="",
        )
        second = resolve_customer(
            customer_name="نام نمایشی تازه",
            contact_name="مخاطب دوم",
            phone="+98 912 000 0041",
            email="",
        )

        self.assertEqual(first.pk, second.pk)
        first.refresh_from_db()
        self.assertEqual(first.phone, "989120000041")
        self.assertEqual(first.contacts.count(), 1)

    def test_every_distinct_base_form_snapshot_is_preserved(self):
        lead = create_lead(
            name="مدیر پروژه",
            business_name="شرکت نسخه‌دار",
            phone="09120000051",
            email="versions@example.com",
            message="شرح نسخه اول",
        )
        document = CaseDocument.objects.get(
            case=case_for(lead),
            kind="initial",
        )
        self.assertEqual(document.revisions.count(), 1)
        first_checksum = document.checksum

        lead.message = "شرح نسخه دوم"
        lead.save(update_fields=("message",))
        document.refresh_from_db()

        self.assertNotEqual(document.checksum, first_checksum)
        self.assertEqual(document.revisions.count(), 2)
        messages = {
            revision.snapshot["message"] for revision in document.revisions.all()
        }
        self.assertEqual(messages, {"شرح نسخه اول", "شرح نسخه دوم"})

        lead.save(update_fields=("message",))
        self.assertEqual(document.revisions.count(), 2)

    def test_revision_history_prevents_accidental_document_deletion(self):
        lead = create_lead(
            name="مدیر",
            business_name="شرکت محفوظ",
            phone="09120000061",
            email="protected@example.com",
        )
        document = CaseDocument.objects.get(case=case_for(lead))
        self.assertTrue(CaseDocumentRevision.objects.filter(document=document).exists())

        with self.assertRaises(ProtectedError):
            document.delete()
