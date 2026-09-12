import threading
import unittest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from leads.form_draft_service import (
    DraftValidationError,
    delete_draft,
    get_active_draft,
    normalize_fields,
    upsert_active_draft,
)
from leads.models import FormDraft, Lead
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection, DemoTemplate
from services.models import Service

User = get_user_model()


def make_service(*, slug="test-service", is_active=True):
    return Service.objects.create(
        title_fa="خدمت آزمایشی", title_en="Test service", slug=slug,
        short_description_fa="خلاصه", short_description_en="Summary", is_active=is_active,
    )


class FormDraftModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="draft-owner@example.com", email="draft-owner@example.com", password="x", is_active=True,
        )

    def test_only_one_active_draft_per_owner_and_form_type(self):
        FormDraft.objects.create(owner=self.owner, form_type="leads_contact", status="open")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormDraft.objects.create(owner=self.owner, form_type="leads_contact", status="submitting")

    def test_submitted_or_expired_drafts_do_not_conflict_with_a_new_active_one(self):
        FormDraft.objects.create(owner=self.owner, form_type="leads_contact", status="submitted")
        FormDraft.objects.create(owner=self.owner, form_type="leads_contact", status="expired")
        # Neither "submitted" nor "expired" is an active status, so a fresh
        # "open" draft for the same owner+form_type is allowed alongside them.
        FormDraft.objects.create(owner=self.owner, form_type="leads_contact", status="open")
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 3)

    def test_submitted_lead_uses_a_real_foreign_key_and_nulls_on_lead_deletion(self):
        lead = Lead.objects.create(
            name="مشتری آزمایشی", email_or_telegram="draft-lead@example.com",
            message="پیام آزمایشی", privacy_accepted_at=timezone.now(),
        )
        draft = FormDraft.objects.create(
            owner=self.owner, form_type="leads_contact", status="submitted", submitted_lead=lead,
        )
        lead.delete()
        draft.refresh_from_db()
        self.assertIsNone(draft.submitted_lead_id)

    def test_default_expiry_is_about_seven_days_out(self):
        draft = FormDraft.objects.create(owner=self.owner, form_type="leads_contact")
        delta = draft.expires_at - draft.created_at
        self.assertGreater(delta, timedelta(days=6, hours=23))
        self.assertLess(delta, timedelta(days=7, hours=1))

    def test_str_and_repr_never_leak_field_contents(self):
        draft = FormDraft.objects.create(
            owner=self.owner, form_type="leads_contact",
            fields={"budget_range": "under_50"}, demo_snapshot={"brand": "دموی محرمانه"},
        )
        text = str(draft)
        self.assertNotIn("under_50", text)
        self.assertNotIn("دموی محرمانه", text)


class NormalizeFieldsTests(TestCase):
    def test_valid_fields_pass_through_unchanged(self):
        service = make_service()
        cleaned = normalize_fields("leads_contact", {
            "request_type": "webapp", "service_id": service.pk, "budget_range": "50_150",
            "timeline": "one_month", "preferred_contact": "email",
        })
        self.assertEqual(cleaned, {
            "request_type": "webapp", "service_id": service.pk, "budget_range": "50_150",
            "timeline": "one_month", "preferred_contact": "email",
        })

    def test_partial_fields_are_allowed(self):
        cleaned = normalize_fields("leads_contact", {"request_type": "website"})
        self.assertEqual(cleaned, {"request_type": "website"})

    def test_empty_fields_are_allowed(self):
        self.assertEqual(normalize_fields("leads_contact", {}), {})

    def test_each_forbidden_key_is_rejected(self):
        forbidden_samples = {
            "name": "علی", "phone": "09120000000", "email_or_telegram": "a@example.com",
            "business_name": "کسب‌وکار", "website_url": "https://example.com",
            "message": "متن آزاد", "privacy_accept": True,
            "public_token": "00000000-0000-0000-0000-000000000000",
            "session_key": "abc123", "submission_token": "xyz",
        }
        for key, value in forbidden_samples.items():
            with self.assertRaises(DraftValidationError, msg=key):
                normalize_fields("leads_contact", {key: value})

    def test_unrecognized_key_is_rejected(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"totally_made_up_field": "x"})

    def test_invalid_choice_values_are_rejected(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"request_type": "not-a-real-choice"})
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"budget_range": "not-a-real-choice"})
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"timeline": "not-a-real-choice"})
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"preferred_contact": "not-a-real-choice"})

    def test_non_hashable_choice_value_is_rejected_not_crashed(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"budget_range": ["under_50"]})

    def test_inactive_service_is_rejected(self):
        service = make_service(slug="inactive-service", is_active=False)
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"service_id": service.pk})

    def test_nonexistent_service_is_rejected(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"service_id": 999999})

    def test_service_id_null_is_allowed(self):
        self.assertEqual(normalize_fields("leads_contact", {"service_id": None}), {"service_id": None})

    def test_service_id_wrong_type_is_rejected(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"service_id": "1"})
        with self.assertRaises(DraftValidationError):
            normalize_fields("leads_contact", {"service_id": True})

    def test_unsupported_form_type_is_rejected(self):
        with self.assertRaises(DraftValidationError):
            normalize_fields("crm_order", {})


class UpsertActiveDraftTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="upsert-owner@example.com", email="upsert-owner@example.com", password="x", is_active=True,
        )

    def test_valid_draft_creation_for_logged_in_user(self):
        draft = upsert_active_draft(
            owner=self.owner, form_type="leads_contact",
            fields={"request_type": "webapp"}, current_step=1,
        )
        self.assertEqual(draft.owner_id, self.owner.pk)
        self.assertEqual(draft.status, "open")
        self.assertEqual(draft.fields, {"request_type": "webapp"})
        self.assertEqual(draft.current_step, 1)

    def test_anonymous_or_missing_owner_is_rejected(self):
        anonymous = type("Anon", (), {"is_authenticated": False, "pk": None})()
        with self.assertRaises(DraftValidationError):
            upsert_active_draft(owner=None, form_type="leads_contact", fields={})
        with self.assertRaises(DraftValidationError):
            upsert_active_draft(owner=anonymous, form_type="leads_contact", fields={})
        self.assertEqual(FormDraft.objects.count(), 0)

    def test_invalid_current_step_is_rejected(self):
        with self.assertRaises(DraftValidationError):
            upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={}, current_step=3)
        with self.assertRaises(DraftValidationError):
            upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={}, current_step=-1)
        self.assertEqual(FormDraft.objects.count(), 0)

    def test_expires_at_is_extended_by_exactly_seven_days_on_each_valid_save(self):
        first = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        first_expiry = first.expires_at

        second = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "website"})
        self.assertEqual(first.pk, second.pk)
        self.assertGreater(second.expires_at, first_expiry)
        self.assertAlmostEqual(
            (second.expires_at - second.updated_at).total_seconds(), timedelta(days=7).total_seconds(), delta=5,
        )

    def test_repeated_upsert_updates_the_same_row_not_a_second_one(self):
        for step in range(3):
            upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={}, current_step=step)
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 1)
        self.assertEqual(FormDraft.objects.get(owner=self.owner).current_step, 2)

    def test_expired_draft_transitions_to_expired_and_a_fresh_one_is_created(self):
        stale = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        fresh = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "website"})

        self.assertNotEqual(stale.pk, fresh.pk)
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")
        self.assertEqual(fresh.status, "open")
        self.assertEqual(
            FormDraft.objects.filter(owner=self.owner, status__in=FormDraft.ACTIVE_STATUSES).count(), 1,
        )

    def test_get_active_draft_returns_none_for_anonymous_and_none_for_expired(self):
        self.assertIsNone(get_active_draft(None, "leads_contact"))
        draft = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        self.assertEqual(get_active_draft(self.owner, "leads_contact").pk, draft.pk)
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertIsNone(get_active_draft(self.owner, "leads_contact"))
        draft.refresh_from_db()
        self.assertEqual(draft.status, "expired")

    def test_hard_delete_only_removes_the_owning_users_draft(self):
        other = User.objects.create_user(
            username="other-draft-owner@example.com", email="other-draft-owner@example.com", password="x", is_active=True,
        )
        mine = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        theirs = upsert_active_draft(owner=other, form_type="leads_contact", fields={})

        self.assertFalse(delete_draft(self.owner, theirs.pk))
        self.assertTrue(FormDraft.objects.filter(pk=theirs.pk).exists())

        self.assertTrue(delete_draft(self.owner, mine.pk))
        self.assertFalse(FormDraft.objects.filter(pk=mine.pk).exists())
        self.assertTrue(FormDraft.objects.filter(pk=theirs.pk).exists())

    def test_invalid_fields_never_get_persisted(self):
        with self.assertRaises(DraftValidationError):
            upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"name": "علی"})
        self.assertEqual(FormDraft.objects.count(), 0)


class DemoSnapshotExtractionTests(TestCase):
    """The neutral projects.demo_snapshots.build_demo_selection_snapshot
    must be byte-for-byte compatible with the private helper it replaced
    in management_portal.cases."""

    def test_snapshot_shape_and_values_match_the_original_helper(self):
        template = DemoTemplate.objects.create(
            slug="snapshot-extraction-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="snapshot-test-session",
            selections={"theme": "sage", "personality": "luxury", "brand": "کافه رویا", "features": ["booking", "catalog"]},
        )

        snapshot = build_demo_selection_snapshot(selection)

        self.assertEqual(snapshot, {
            "template_title_fa": "دموی فروشگاهی",
            "template_title_en": "Storefront demo",
            "category_fa": "فروشگاه اینترنتی",
            "category_en": "E-commerce",
            "brand": "کافه رویا",
            "theme_fa": "سبز آرام",
            "theme_en": "Calm sage",
            "personality_fa": "لوکس",
            "personality_en": "Luxury",
            "features_fa": ["رزرو / نوبت‌دهی", "کاتالوگ و محصول"],
            "features_en": ["Booking", "Catalogue"],
            "demo_template_slug": "snapshot-extraction-demo",
        })

    def test_snapshot_never_contains_forbidden_tokens(self):
        template = DemoTemplate.objects.create(
            slug="snapshot-token-check-demo", category="clinic",
            title_fa="دمو", title_en="Demo", tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند", fictional_brand_en="Brand", style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="a-very-secret-session-key",
            selections={"theme": "warm", "personality": "minimal", "features": []},
        )
        snapshot = build_demo_selection_snapshot(selection)
        serialized = str(snapshot)
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn("a-very-secret-session-key", serialized)
        self.assertNotIn("public_token", serialized)
        self.assertNotIn("session_key", serialized)
        self.assertNotIn("submission_token", serialized)

    def test_malformed_selection_data_does_not_crash_the_snapshot_builder(self):
        template = DemoTemplate.objects.create(
            slug="snapshot-malformed-demo", category="clinic",
            title_fa="دمو", title_en="Demo", tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند", fictional_brand_en="Brand", style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="malformed-session",
            selections={"theme": ["not", "a", "string"], "personality": 12345, "features": "not-a-list", "brand": 999},
        )
        snapshot = build_demo_selection_snapshot(selection)
        self.assertEqual(snapshot["features_fa"], [])
        self.assertEqual(snapshot["features_en"], [])
        self.assertEqual(snapshot["brand"], "برند")  # falls back to the template's own brand


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "Genuine row-lock concurrency can only be demonstrated on a real database engine; skipped on SQLite.",
)
class FormDraftPostgresRaceTests(TransactionTestCase):
    def test_concurrent_upserts_converge_to_one_active_draft(self):
        owner = User.objects.create_user(
            username="draft-race@example.com", email="draft-race@example.com", password="x", is_active=True,
        )
        barrier = threading.Barrier(4)
        errors = []

        def attempt(step):
            try:
                barrier.wait(timeout=5)
                upsert_active_draft(
                    owner=owner, form_type="leads_contact",
                    fields={"request_type": "webapp"}, current_step=step,
                )
            except Exception as exc:  # pragma: no cover - surfaced via errors list
                errors.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt, args=(step,)) for step in (0, 1, 2, 0)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")
        self.assertEqual(errors, [])
        self.assertEqual(FormDraft.objects.filter(owner=owner).count(), 1)
        self.assertEqual(FormDraft.objects.filter(owner=owner, status__in=FormDraft.ACTIVE_STATUSES).count(), 1)

    def test_conditional_unique_constraint_holds_under_concurrent_inserts(self):
        """Direct proof of the DB-level backstop (not just the service's own
        locking): two raw concurrent inserts attempting to create a second
        *active* row for the same owner+form_type must not both succeed."""
        owner = User.objects.create_user(
            username="constraint-race@example.com", email="constraint-race@example.com", password="x", is_active=True,
        )
        barrier = threading.Barrier(2)
        results = []

        def attempt():
            try:
                barrier.wait(timeout=5)
                with transaction.atomic():
                    FormDraft.objects.create(owner=owner, form_type="leads_contact", status="open")
                results.append("ok")
            except IntegrityError:
                results.append("blocked")
            except Exception as exc:  # pragma: no cover
                results.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")
        self.assertEqual(sorted(str(r) for r in results), ["blocked", "ok"])
        self.assertEqual(FormDraft.objects.filter(owner=owner).count(), 1)
