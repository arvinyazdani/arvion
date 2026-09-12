import threading
import unittest
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from leads.form_draft_service import (
    DraftValidationError,
    attach_demo_snapshot,
    clear_demo_snapshot,
    delete_draft,
    ensure_active_draft,
    ensure_active_draft_with_demo_snapshot,
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

        # get_active_draft is read-only: an expired row is simply not
        # returned, but its status/updated_at are never touched by the
        # read itself — only a locked write path (upsert_active_draft, or
        # a future cleanup job) may transition it to "expired".
        stale_updated_at = FormDraft.objects.get(pk=draft.pk).updated_at
        self.assertIsNone(get_active_draft(self.owner, "leads_contact"))
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")
        self.assertEqual(draft.updated_at, stale_updated_at)

    def test_get_active_draft_issues_no_writes_and_no_row_lock(self):
        """Direct proof that get_active_draft is a plain SELECT: no UPDATE
        statement is issued, and it never calls select_for_update."""
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})

        with mock.patch(
            "django.db.models.QuerySet.select_for_update",
            side_effect=AssertionError("get_active_draft must never call select_for_update"),
        ):
            with CaptureQueriesContext(connection) as ctx:
                get_active_draft(self.owner, "leads_contact")

        statements = [q["sql"].strip().upper() for q in ctx.captured_queries]
        self.assertTrue(statements, "expected at least one SELECT query")
        for sql in statements:
            self.assertFalse(sql.startswith("UPDATE"), sql)
            self.assertFalse(sql.startswith("INSERT"), sql)
            self.assertFalse(sql.startswith("DELETE"), sql)

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

    def test_upsert_never_accepts_a_raw_demo_snapshot_argument(self):
        # There is no longer any keyword through which a caller can pass an
        # arbitrary snapshot dict straight through to the database.
        with self.assertRaises(TypeError):
            upsert_active_draft(
                owner=self.owner, form_type="leads_contact", fields={},
                demo_snapshot={"session_key": "leaked"},
            )
        self.assertEqual(FormDraft.objects.count(), 0)

    def test_retention_constant_has_a_single_source(self):
        from leads import form_draft_service
        from leads.models import form_draft as form_draft_model

        self.assertIs(form_draft_service.DRAFT_RETENTION_DAYS, form_draft_model.DRAFT_RETENTION_DAYS)


class EnsureActiveDraftTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ensure-owner@example.com", email="ensure-owner@example.com", password="x", is_active=True,
        )
        self.template = DemoTemplate.objects.create(
            slug="ensure-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        self.selection = DemoSelection.objects.create(
            template=self.template, session_key="ensure-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

    def test_ensure_creates_an_empty_draft_when_none_exists(self):
        draft = ensure_active_draft(owner=self.owner, form_type="leads_contact")
        self.assertEqual(draft.fields, {})
        self.assertEqual(draft.current_step, 0)
        self.assertEqual(draft.demo_snapshot, {})
        self.assertEqual(draft.status, "open")

    def test_ensure_returns_the_existing_draft_unmodified(self):
        original = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=1)
        attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        before = FormDraft.objects.get(pk=original.pk)

        returned = ensure_active_draft(owner=self.owner, form_type="leads_contact")

        self.assertEqual(returned.pk, original.pk)
        self.assertEqual(returned.fields, before.fields)
        self.assertEqual(returned.current_step, before.current_step)
        self.assertEqual(returned.demo_snapshot, before.demo_snapshot)

    def test_repeated_ensure_never_creates_a_second_draft(self):
        for _ in range(3):
            ensure_active_draft(owner=self.owner, form_type="leads_contact")
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 1)

    def test_ensure_expires_a_stale_draft_and_creates_a_fresh_one(self):
        stale = ensure_active_draft(owner=self.owner, form_type="leads_contact")
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        fresh = ensure_active_draft(owner=self.owner, form_type="leads_contact")

        self.assertNotEqual(stale.pk, fresh.pk)
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")
        self.assertEqual(fresh.status, "open")

    def test_ensure_rejects_anonymous_owner(self):
        anonymous = type("Anon", (), {"is_authenticated": False, "pk": None})()
        with self.assertRaises(DraftValidationError):
            ensure_active_draft(owner=anonymous, form_type="leads_contact")
        self.assertEqual(FormDraft.objects.count(), 0)


class EnsureActiveDraftWithDemoSnapshotTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ensure-attach-owner@example.com", email="ensure-attach-owner@example.com",
            password="x", is_active=True,
        )
        self.other = User.objects.create_user(
            username="ensure-attach-other@example.com", email="ensure-attach-other@example.com",
            password="x", is_active=True,
        )
        self.template = DemoTemplate.objects.create(
            slug="ensure-attach-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        self.selection = DemoSelection.objects.create(
            template=self.template, session_key="ensure-attach-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

    def test_creates_a_draft_with_the_snapshot_when_none_existed(self):
        draft = ensure_active_draft_with_demo_snapshot(
            owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
        )
        self.assertEqual(draft.demo_snapshot, build_demo_selection_snapshot(self.selection))
        self.assertEqual(draft.fields, {})
        self.assertEqual(draft.current_step, 0)
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 1)

    def test_never_raises_no_active_draft_unlike_attach_demo_snapshot(self):
        # attach_demo_snapshot would reject with no_active_draft here since
        # no draft exists yet; the combined ensure+attach must not.
        draft = ensure_active_draft_with_demo_snapshot(
            owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
        )
        self.assertIsNotNone(draft)

    def test_preserves_fields_and_current_step_on_an_existing_draft(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=2)

        draft = ensure_active_draft_with_demo_snapshot(
            owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
        )

        self.assertEqual(draft.fields, {"request_type": "webapp"})
        self.assertEqual(draft.current_step, 2)
        self.assertEqual(draft.demo_snapshot, build_demo_selection_snapshot(self.selection))

    def test_repeated_calls_are_idempotent_and_never_create_a_second_draft(self):
        for _ in range(3):
            ensure_active_draft_with_demo_snapshot(
                owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
            )
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 1)

    def test_rejects_an_unsaved_or_deleted_demo_selection_without_writing(self):
        stale_pk = self.selection.pk
        DemoSelection.objects.filter(pk=stale_pk).delete()
        with self.assertRaises(DraftValidationError) as ctx:
            ensure_active_draft_with_demo_snapshot(
                owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
            )
        self.assertEqual(ctx.exception.code, "invalid_demo_selection")
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 0)

    def test_never_touches_another_owners_draft(self):
        other_draft = ensure_active_draft(owner=self.other, form_type="leads_contact")
        ensure_active_draft_with_demo_snapshot(
            owner=self.owner, form_type="leads_contact", demo_selection=self.selection,
        )
        other_draft.refresh_from_db()
        self.assertEqual(other_draft.demo_snapshot, {})


class OpaqueValidationErrorTests(TestCase):
    """No DraftValidationError raised anywhere in this service may repeat
    a caller-supplied value or an arbitrary caller-supplied key name back
    in its message — both may be attacker-controlled payload content."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="opaque-owner@example.com", email="opaque-owner@example.com", password="x", is_active=True,
        )

    def test_invalid_choice_error_never_contains_the_submitted_value(self):
        secret_value = "super-secret-injected-choice-<script>alert(1)</script>"
        with self.assertRaises(DraftValidationError) as ctx:
            normalize_fields("leads_contact", {"budget_range": secret_value})
        self.assertNotIn(secret_value, str(ctx.exception))

    def test_unknown_key_error_never_contains_the_submitted_key_name_or_value(self):
        secret_key = "attacker_controlled_field_name_xyz"
        secret_value = "attacker-controlled-value-123"
        with self.assertRaises(DraftValidationError) as ctx:
            normalize_fields("leads_contact", {secret_key: secret_value})
        message = str(ctx.exception)
        self.assertNotIn(secret_key, message)
        self.assertNotIn(secret_value, message)

    def test_forbidden_key_error_never_contains_the_key_name_or_value(self):
        with self.assertRaises(DraftValidationError) as ctx:
            normalize_fields("leads_contact", {"session_key": "abc123secret"})
        message = str(ctx.exception)
        self.assertNotIn("abc123secret", message)

    def test_invalid_current_step_error_never_contains_the_submitted_value(self):
        with self.assertRaises(DraftValidationError) as ctx:
            upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={}, current_step=999999)
        self.assertNotIn("999999", str(ctx.exception))

    def test_malformed_and_very_large_payload_is_rejected_without_crashing(self):
        huge_value = "x" * 200_000
        mixed_type_payload = {1: "int-key", ("tuple", "key"): "tuple-key", huge_value: "huge-key"}
        # Dict keys are always hashable in Python, so no key-hashing crash
        # is possible here; the assertion is that normalize_fields rejects
        # cleanly (no TypeError from sorting/formatting mixed key types,
        # no unbounded string ever echoed back).
        with self.assertRaises(DraftValidationError) as ctx:
            normalize_fields("leads_contact", mixed_type_payload)
        message = str(ctx.exception)
        self.assertNotIn(huge_value, message)
        self.assertLess(len(message), 500)

    def test_invalid_demo_selection_error_is_generic(self):
        with self.assertRaises(DraftValidationError) as ctx:
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection={"brand": "fake"})
        message = str(ctx.exception)
        self.assertNotIn("fake", message)


class DemoSnapshotAttachClearTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="snap-owner@example.com", email="snap-owner@example.com", password="x", is_active=True,
        )
        self.other = User.objects.create_user(
            username="snap-other@example.com", email="snap-other@example.com", password="x", is_active=True,
        )
        self.template = DemoTemplate.objects.create(
            slug="attach-clear-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        self.selection = DemoSelection.objects.create(
            template=self.template, session_key="attach-clear-session",
            selections={"theme": "sage", "personality": "luxury", "brand": "کافه رویا", "features": ["booking"]},
        )

    def test_attach_demo_snapshot_builds_it_from_a_real_demo_selection(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        draft = attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        self.assertEqual(draft.demo_snapshot, build_demo_selection_snapshot(self.selection))
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "attach-clear-demo")

    def test_attach_demo_snapshot_rejects_a_dict_or_arbitrary_object(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        forbidden_payload = {
            "template_title_fa": "x", "template_title_en": "x", "category_fa": "x", "category_en": "x",
            "brand": "x", "theme_fa": "x", "theme_en": "x", "personality_fa": "x", "personality_en": "x",
            "features_fa": [], "features_en": [], "demo_template_slug": "x",
            "public_token": "should-never-be-storable", "session_key": "should-never-be-storable",
        }
        with self.assertRaises(DraftValidationError):
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=forbidden_payload)
        with self.assertRaises(DraftValidationError):
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=None)
        with self.assertRaises(DraftValidationError):
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=DemoSelection(template=self.template, session_key="unsaved"))
        draft = get_active_draft(self.owner, "leads_contact")
        self.assertEqual(draft.demo_snapshot, {})

    def test_attach_demo_snapshot_requires_an_existing_active_draft(self):
        with self.assertRaises(DraftValidationError):
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        self.assertEqual(FormDraft.objects.filter(owner=self.owner).count(), 0)

    def test_plain_field_upsert_preserves_an_existing_snapshot(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)

        updated = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "website"})

        self.assertEqual(updated.demo_snapshot, build_demo_selection_snapshot(self.selection))
        self.assertEqual(updated.fields, {"request_type": "website"})

    def test_clear_demo_snapshot_removes_only_the_snapshot(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=1)
        attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)

        cleared = clear_demo_snapshot(owner=self.owner, form_type="leads_contact")

        self.assertEqual(cleared.demo_snapshot, {})
        self.assertEqual(cleared.fields, {"request_type": "webapp"})
        self.assertEqual(cleared.current_step, 1)

    def test_attach_and_clear_never_touch_another_owners_draft(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        other_draft = upsert_active_draft(owner=self.other, form_type="leads_contact", fields={"request_type": "webapp"})
        attach_demo_snapshot(owner=self.other, form_type="leads_contact", demo_selection=self.selection)

        # Attaching/clearing for `self.owner` can only ever reach their own
        # active draft — the query inside attach/clear is always scoped to
        # the locked owner row, so there is no id/token a caller could pass
        # to reach someone else's draft.
        attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        clear_demo_snapshot(owner=self.owner, form_type="leads_contact")

        other_draft.refresh_from_db()
        self.assertEqual(other_draft.demo_snapshot, build_demo_selection_snapshot(self.selection))

    def test_attach_demo_snapshot_extends_expires_at_by_seven_days(self):
        draft = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=1)
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() + timedelta(days=1))

        updated = attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)

        self.assertAlmostEqual(
            (updated.expires_at - timezone.now()).total_seconds(), timedelta(days=7).total_seconds(), delta=5,
        )
        self.assertEqual(updated.fields, {"request_type": "webapp"})
        self.assertEqual(updated.current_step, 1)

    def test_clear_demo_snapshot_extends_expires_at_by_seven_days(self):
        draft = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=2)
        attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() + timedelta(hours=2))

        updated = clear_demo_snapshot(owner=self.owner, form_type="leads_contact")

        self.assertAlmostEqual(
            (updated.expires_at - timezone.now()).total_seconds(), timedelta(days=7).total_seconds(), delta=5,
        )
        self.assertEqual(updated.fields, {"request_type": "webapp"})
        self.assertEqual(updated.current_step, 2)

    def test_attach_on_an_expired_draft_rejects_but_still_commits_the_expiry(self):
        """Regression proof for the rollback bug this corrective phase
        fixes: raising DraftValidationError from inside the same
        transaction.atomic() block that just expired a stale draft would
        roll that expiry back out too. It must not."""
        stale = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        with self.assertRaises(DraftValidationError) as ctx:
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        self.assertEqual(ctx.exception.code, "no_active_draft")

        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")

    def test_clear_on_an_expired_draft_rejects_but_still_commits_the_expiry(self):
        stale = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        with self.assertRaises(DraftValidationError) as ctx:
            clear_demo_snapshot(owner=self.owner, form_type="leads_contact")
        self.assertEqual(ctx.exception.code, "no_active_draft")

        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")

    def test_expired_draft_is_never_revived_by_attach_or_clear(self):
        stale = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        with self.assertRaises(DraftValidationError):
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        with self.assertRaises(DraftValidationError):
            clear_demo_snapshot(owner=self.owner, form_type="leads_contact")

        self.assertEqual(
            FormDraft.objects.filter(owner=self.owner, status__in=FormDraft.ACTIVE_STATUSES).count(), 0,
        )
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")

    def test_upsert_still_creates_a_fresh_draft_after_expiry(self):
        stale = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        fresh = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "website"})

        self.assertNotEqual(stale.pk, fresh.pk)
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")
        self.assertEqual(fresh.status, "open")

    def test_attach_ignores_an_in_memory_mutation_of_the_demo_selection(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        original_snapshot = build_demo_selection_snapshot(self.selection)

        # Mutate the in-memory instance's selections without saving —
        # simulating a caller that hands in a locally-tampered object.
        self.selection.selections = {
            "theme": "warm", "personality": "minimal", "brand": "injected-brand", "features": ["support"],
        }

        draft = attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)

        self.assertEqual(draft.demo_snapshot, original_snapshot)
        self.assertNotEqual(draft.demo_snapshot["brand"], "injected-brand")

    def test_attach_rejects_a_demo_selection_whose_row_no_longer_exists(self):
        upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={})
        stale_pk = self.selection.pk
        # Delete via a fresh queryset so the in-memory `self.selection`
        # object keeps its pk attribute set (Django only nulls the pk on
        # the exact instance .delete() is called on), matching a caller
        # that holds a reference to a row deleted by someone else.
        DemoSelection.objects.filter(pk=stale_pk).delete()

        with self.assertRaises(DraftValidationError) as ctx:
            attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
        self.assertEqual(ctx.exception.code, "invalid_demo_selection")

        draft = get_active_draft(self.owner, "leads_contact")
        self.assertEqual(draft.demo_snapshot, {})

    def test_invalid_snapshot_values_are_rejected_and_leave_the_draft_untouched(self):
        draft = upsert_active_draft(owner=self.owner, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=1)
        original_expires_at = draft.expires_at

        base = build_demo_selection_snapshot(self.selection)
        malformed_variants = [
            {**base, "brand": 12345},  # wrong type
            {**base, "brand": "x" * 10_000},  # far past the length cap
            {**base, "features_fa": "not-a-list"},  # wrong type
            {**base, "features_fa": [1, 2]},  # non-string members
            {**base, "features_fa": ["a"], "features_en": ["a", "b"]},  # mismatched counts
            {**base, "theme_fa": ["nested", "list"]},  # nested structure
            {**base, "personality_fa": True},  # bool, not str
        ]
        for bad_snapshot in malformed_variants:
            with mock.patch(
                "leads.form_draft_service.build_demo_selection_snapshot", return_value=bad_snapshot,
            ):
                with self.assertRaises(DraftValidationError) as ctx:
                    attach_demo_snapshot(owner=self.owner, form_type="leads_contact", demo_selection=self.selection)
                self.assertEqual(ctx.exception.code, "invalid_snapshot_shape")
                self.assertNotIn("12345", str(ctx.exception))
                self.assertNotIn("injected", str(ctx.exception))

        draft.refresh_from_db()
        self.assertEqual(draft.fields, {"request_type": "webapp"})
        self.assertEqual(draft.current_step, 1)
        self.assertEqual(draft.demo_snapshot, {})
        self.assertEqual(draft.expires_at, original_expires_at)


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

    def test_concurrent_expired_read_cannot_clobber_a_racing_renewal(self):
        """Regression proof for the write-on-read bug this corrective phase
        fixes: a get_active_draft call racing a real renewal of the same
        stale row must never re-expire the freshly renewed draft. Since
        get_active_draft is now strictly read-only, this is no longer even
        structurally possible — this test proves it empirically on a real
        database rather than only by code inspection."""
        owner = User.objects.create_user(
            username="expiry-race@example.com", email="expiry-race@example.com", password="x", is_active=True,
        )
        stale = upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        barrier = threading.Barrier(2)
        errors = []

        def reader():
            try:
                barrier.wait(timeout=5)
                for _ in range(20):
                    get_active_draft(owner, "leads_contact")
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connection.close()

        def renewer():
            try:
                barrier.wait(timeout=5)
                upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "website"})
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=reader), threading.Thread(target=renewer)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")
        self.assertEqual(errors, [])

        active = FormDraft.objects.filter(owner=owner, status__in=FormDraft.ACTIVE_STATUSES)
        self.assertEqual(active.count(), 1)
        survivor = active.get()
        self.assertEqual(survivor.status, "open")
        self.assertGreater(survivor.expires_at, timezone.now())
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")

    def test_concurrent_attach_and_upsert_on_an_active_draft_both_apply(self):
        """The owner-row lock shared by upsert_active_draft and
        attach_demo_snapshot must serialize them against each other too,
        not just against other upserts: both writers touch disjoint
        columns (fields/current_step vs. demo_snapshot), so both must
        survive regardless of which one the lock lets through first."""
        owner = User.objects.create_user(
            username="attach-upsert-race@example.com", email="attach-upsert-race@example.com",
            password="x", is_active=True,
        )
        template = DemoTemplate.objects.create(
            slug="race-attach-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="race-attach-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "webapp"})

        barrier = threading.Barrier(2)
        errors = []

        def upserter():
            try:
                barrier.wait(timeout=5)
                upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "website"}, current_step=1)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connection.close()

        def attacher():
            try:
                barrier.wait(timeout=5)
                attach_demo_snapshot(owner=owner, form_type="leads_contact", demo_selection=selection)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=upserter), threading.Thread(target=attacher)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")
        self.assertEqual(errors, [])

        self.assertEqual(FormDraft.objects.filter(owner=owner).count(), 1)
        survivor = FormDraft.objects.get(owner=owner)
        self.assertEqual(survivor.fields, {"request_type": "website"})
        self.assertEqual(survivor.current_step, 1)
        self.assertEqual(survivor.demo_snapshot, build_demo_selection_snapshot(selection))

    def test_concurrent_upsert_and_attach_around_expiry_never_double_expires_or_revives(self):
        """A stale draft racing between a renewing upsert and an attach
        attempt must converge cleanly regardless of which one the owner-row
        lock admits first: exactly one row ever transitions to "expired",
        exactly one active draft survives, and attach never revives an
        expired row. The attach thread may legitimately fail with
        DraftValidationError(code="no_active_draft") if it loses the race —
        that is not a bug, just the other valid outcome."""
        owner = User.objects.create_user(
            username="expire-attach-race@example.com", email="expire-attach-race@example.com",
            password="x", is_active=True,
        )
        template = DemoTemplate.objects.create(
            slug="race-expire-attach-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="race-expire-attach-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        stale = upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "webapp"})
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        barrier = threading.Barrier(2)
        outcomes = []

        def renewer():
            try:
                barrier.wait(timeout=5)
                upsert_active_draft(owner=owner, form_type="leads_contact", fields={"request_type": "website"})
                outcomes.append("upsert_ok")
            except Exception as exc:  # pragma: no cover
                outcomes.append(exc)
            finally:
                connection.close()

        def attacher():
            try:
                barrier.wait(timeout=5)
                attach_demo_snapshot(owner=owner, form_type="leads_contact", demo_selection=selection)
                outcomes.append("attach_ok")
            except DraftValidationError as exc:
                outcomes.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=renewer), threading.Thread(target=attacher)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")

        # The upsert side must always succeed; the attach side either
        # succeeds (if it ran after the renewal) or fails with exactly
        # "no_active_draft" (if it ran against the still-stale row) — no
        # other exception is acceptable.
        self.assertIn("upsert_ok", outcomes)
        for outcome in outcomes:
            if outcome != "upsert_ok" and outcome != "attach_ok":
                self.assertIsInstance(outcome, DraftValidationError)
                self.assertEqual(outcome.code, "no_active_draft")

        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")
        active = FormDraft.objects.filter(owner=owner, status__in=FormDraft.ACTIVE_STATUSES)
        self.assertEqual(active.count(), 1)
        self.assertEqual(FormDraft.objects.filter(owner=owner, status="expired").count(), 1)

    def test_concurrent_ensure_and_attach_converge_to_one_draft_with_the_snapshot(self):
        """Simulates two near-simultaneous logins for the same account both
        carrying the same pending demo selection (e.g. a double-tab submit)
        — the atomic ensure+attach combo must converge to exactly one
        active draft holding the snapshot, never two competing rows and
        never a lost snapshot."""
        owner = User.objects.create_user(
            username="ensure-attach-race@example.com", email="ensure-attach-race@example.com",
            password="x", is_active=True,
        )
        template = DemoTemplate.objects.create(
            slug="race-ensure-attach-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="race-ensure-attach-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

        barrier = threading.Barrier(2)
        errors = []

        def attempt():
            try:
                barrier.wait(timeout=5)
                ensure_active_draft_with_demo_snapshot(
                    owner=owner, form_type="leads_contact", demo_selection=selection,
                )
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")
        self.assertEqual(errors, [])

        self.assertEqual(FormDraft.objects.filter(owner=owner).count(), 1)
        survivor = FormDraft.objects.get(owner=owner)
        self.assertEqual(survivor.demo_snapshot, build_demo_selection_snapshot(selection))
        self.assertEqual(survivor.status, "open")
