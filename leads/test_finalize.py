"""V2.1-D: atomic, non-duplicating FormDraft->Lead conversion on the final
leads-contact submission. Covers `leads.form_draft_service.
finalize_form_draft_to_lead` directly, the full HTTP flow through
`LeadCreateView`, and — for genuine locking/rollback evidence — real
PostgreSQL concurrency and injected-transaction-error tests."""

import threading
import unittest
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from leads.form_draft_service import (
    ForeignSubmissionTokenError,
    InvalidSubmissionTokenError,
    NewLeadRateLimitedError,
    SubmissionConflictError,
    attach_demo_snapshot,
    finalize_form_draft_to_lead,
    save_draft_fields,
)
from leads.forms import LeadForm
from leads.models import FormDraft, Lead
from projects.models import DemoSelection, DemoTemplate

User = get_user_model()

CONTACT_URL = reverse("leads:contact")


def make_customer(suffix="a"):
    return User.objects.create_user(
        username=f"finalize-customer-{suffix}@example.com", email=f"finalize-customer-{suffix}@example.com",
        password="x", is_active=True,
    )


def make_staff(suffix="a"):
    return User.objects.create_user(
        username=f"finalize-staff-{suffix}@example.com", email=f"finalize-staff-{suffix}@example.com",
        password="x", is_active=True, is_staff=True,
    )


def valid_payload(**overrides):
    payload = {
        "name": "آروین یزدانی", "business_name": "کسب‌وکار تست", "email_or_telegram": "test@example.com",
        "phone": "", "request_type": "webapp", "service": "", "website_url": "",
        "budget_range": "50_150", "timeline": "one_three", "preferred_contact": "email",
        "message": "این یک پیام تست معتبر برای ساخت پلتفرم است.", "privacy_accept": "on", "website": "",
    }
    payload.update(overrides)
    return payload


def bound_valid_form(**overrides):
    form = LeadForm(data=valid_payload(**overrides), lang="fa")
    assert form.is_valid(), form.errors
    return form


def make_demo_selection(suffix="a"):
    template = DemoTemplate.objects.create(
        slug=f"finalize-demo-identity-{suffix}", category="ecommerce", title_fa="دموی هویت",
        title_en="Identity demo", tagline_fa="x", tagline_en="y", fictional_brand_fa="ب",
        fictional_brand_en="B", style_key="minimal",
    )
    return DemoSelection.objects.create(
        template=template, session_key=f"finalize-identity-session-{suffix}",
        selections={"theme": "warm", "personality": "minimal", "features": ["blog"]},
    )


def always_allow():
    return True


def never_allow():
    return False


class FinalizeFormDraftToLeadTests(TestCase):
    """Direct, service-level tests — no HTTP, no rate limiter/cache
    concerns beyond the `allow_new_lead` callable's own return value."""

    def setUp(self):
        cache.clear()

    def test_valid_submission_with_existing_active_draft(self):
        customer = make_customer()
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=1, expected_revision=0,
        )
        initial_revision = draft.revision
        form = bound_valid_form()

        lead, created = finalize_form_draft_to_lead(
            owner=customer, form=form, final_submission_token="tok-existing-draft",
            demo_selection=None, allow_new_lead=always_allow,
        )

        self.assertTrue(created)
        self.assertEqual(Lead.objects.count(), 1)
        draft.refresh_from_db()
        self.assertEqual(draft.status, "submitted")
        self.assertEqual(draft.submitted_lead_id, lead.pk)
        self.assertEqual(draft.submission_token, "tok-existing-draft")
        # Two real content changes (submitting, then submitted) — exactly
        # the model's own "revision bumps once per real change" contract.
        self.assertEqual(draft.revision, initial_revision + 2)
        self.assertEqual(lead.name, "آروین یزدانی")
        self.assertEqual(lead.request_type, "webapp")

    def test_valid_submission_without_any_prior_draft(self):
        customer = make_customer()
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)
        form = bound_valid_form(request_type="ecommerce")

        lead, created = finalize_form_draft_to_lead(
            owner=customer, form=form, final_submission_token="tok-no-prior-draft",
            demo_selection=None, allow_new_lead=always_allow,
        )

        self.assertTrue(created)
        draft = FormDraft.objects.get(owner=customer)
        self.assertEqual(draft.status, "submitted")
        self.assertEqual(draft.submitted_lead_id, lead.pk)
        self.assertEqual(draft.revision, 2)  # created at 1, +1 for the submitted transition
        self.assertEqual(draft.fields, {
            "request_type": "ecommerce", "budget_range": "50_150",
            "timeline": "one_three", "preferred_contact": "email",
        })

    # Note: an invalid form is never passed to this service at all —
    # form_valid() only calls it after form.is_valid() already returned
    # True. That boundary lives in Django's own FormView machinery, not
    # here, and is covered at the view level instead — see
    # LeadCreateViewAuthenticatedFinalizeTests.test_invalid_form_creates_no_lead_and_leaves_draft_open.

    def test_sequential_replay_same_token_same_content_returns_existing_lead(self):
        customer = make_customer()
        form1 = bound_valid_form()
        lead1, created1 = finalize_form_draft_to_lead(
            owner=customer, form=form1, final_submission_token="tok-replay-same",
            demo_selection=None, allow_new_lead=always_allow,
        )
        self.assertTrue(created1)

        form2 = bound_valid_form()  # a fresh, identically-valid form instance — mirrors a real resubmit
        lead2, created2 = finalize_form_draft_to_lead(
            owner=customer, form=form2, final_submission_token="tok-replay-same",
            demo_selection=None, allow_new_lead=never_allow,  # must never even be consulted
        )

        self.assertFalse(created2)
        self.assertEqual(lead1.pk, lead2.pk)
        self.assertEqual(Lead.objects.count(), 1)
        draft = FormDraft.objects.get(owner=customer)
        self.assertEqual(draft.status, "submitted")

    def test_sequential_replay_same_token_different_content_is_a_conflict(self):
        customer = make_customer()
        form1 = bound_valid_form()
        lead1, _ = finalize_form_draft_to_lead(
            owner=customer, form=form1, final_submission_token="tok-replay-diff",
            demo_selection=None, allow_new_lead=always_allow,
        )

        form2 = bound_valid_form(name="نام دیگر")
        with self.assertRaises(SubmissionConflictError):
            finalize_form_draft_to_lead(
                owner=customer, form=form2, final_submission_token="tok-replay-diff",
                demo_selection=None, allow_new_lead=always_allow,
            )

        self.assertEqual(Lead.objects.count(), 1)
        lead1.refresh_from_db()
        self.assertEqual(lead1.name, "آروین یزدانی")  # untouched

    def test_two_different_tokens_create_two_separate_leads(self):
        customer = make_customer()
        lead1, created1 = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(request_type="webapp"), final_submission_token="tok-one",
            demo_selection=None, allow_new_lead=always_allow,
        )
        lead2, created2 = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(request_type="ecommerce"), final_submission_token="tok-two",
            demo_selection=None, allow_new_lead=always_allow,
        )

        self.assertTrue(created1)
        self.assertTrue(created2)
        self.assertNotEqual(lead1.pk, lead2.pk)
        self.assertEqual(Lead.objects.count(), 2)
        self.assertEqual(FormDraft.objects.filter(owner=customer, status="submitted").count(), 2)

    def test_token_belonging_to_another_owner_is_rejected_neutrally(self):
        owner_a = make_customer(suffix="a")
        owner_b = make_customer(suffix="b")
        finalize_form_draft_to_lead(
            owner=owner_a, form=bound_valid_form(), final_submission_token="tok-owner-a",
            demo_selection=None, allow_new_lead=always_allow,
        )

        with self.assertRaises(ForeignSubmissionTokenError) as ctx:
            finalize_form_draft_to_lead(
                owner=owner_b, form=bound_valid_form(), final_submission_token="tok-owner-a",
                demo_selection=None, allow_new_lead=always_allow,
            )
        # Never a distinct message/behavior from an unknown token —
        # ForeignSubmissionTokenError IS-A InvalidSubmissionTokenError.
        self.assertIsInstance(ctx.exception, InvalidSubmissionTokenError)
        self.assertEqual(Lead.objects.filter().count(), 1)  # only owner_a's
        self.assertEqual(FormDraft.objects.filter(owner=owner_b).count(), 0)

    def test_unknown_token_and_foreign_token_raise_the_same_error_type(self):
        owner_a = make_customer(suffix="unk-a")
        owner_b = make_customer(suffix="unk-b")
        finalize_form_draft_to_lead(
            owner=owner_a, form=bound_valid_form(), final_submission_token="tok-real",
            demo_selection=None, allow_new_lead=always_allow,
        )
        with self.assertRaises(InvalidSubmissionTokenError):
            finalize_form_draft_to_lead(
                owner=owner_b, form=bound_valid_form(), final_submission_token="tok-real",
                demo_selection=None, allow_new_lead=always_allow,
            )

    def test_blank_empty_or_oversized_token_is_rejected(self):
        customer = make_customer()
        for bad_token in ("", "   ", "x" * 65):
            with self.assertRaises(InvalidSubmissionTokenError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token=bad_token,
                    demo_selection=None, allow_new_lead=always_allow,
                )
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)

    def test_expired_draft_is_never_reused_a_fresh_one_is_created(self):
        customer = make_customer()
        stale, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=0, expected_revision=0,
        )
        FormDraft.objects.filter(pk=stale.pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        lead, created = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(), final_submission_token="tok-expired",
            demo_selection=None, allow_new_lead=always_allow,
        )

        self.assertTrue(created)
        stale.refresh_from_db()
        self.assertEqual(stale.status, "expired")
        self.assertIsNone(stale.submitted_lead_id)
        self.assertIsNone(stale.submission_token)
        fresh = FormDraft.objects.get(owner=customer, status="submitted")
        self.assertEqual(fresh.submitted_lead_id, lead.pk)

    def test_deleted_or_never_created_draft_still_succeeds(self):
        customer = make_customer()
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)
        lead, created = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(), final_submission_token="tok-no-draft-ever",
            demo_selection=None, allow_new_lead=always_allow,
        )
        self.assertTrue(created)
        self.assertEqual(FormDraft.objects.get(owner=customer).submitted_lead_id, lead.pk)

    def test_new_lead_rate_limited_raises_and_writes_nothing(self):
        customer = make_customer()
        with self.assertRaises(NewLeadRateLimitedError):
            finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-rate-limited",
                demo_selection=None, allow_new_lead=never_allow,
            )
        self.assertEqual(Lead.objects.count(), 0)
        # The submitting-transition itself IS allowed to happen before the
        # rate-limit check (see the module docstring) — but nothing is left
        # half-submitted, since the whole thing shares one outer
        # transaction: an uncaught NewLeadRateLimitedError still rolls the
        # entire attempt back, submitting-transition included.
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)

    def test_replay_never_consults_the_rate_limiter(self):
        customer = make_customer()
        lead1, _ = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(), final_submission_token="tok-replay-no-limit",
            demo_selection=None, allow_new_lead=always_allow,
        )
        # allow_new_lead=never_allow proves the replay path never calls it.
        lead2, created2 = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(), final_submission_token="tok-replay-no-limit",
            demo_selection=None, allow_new_lead=never_allow,
        )
        self.assertFalse(created2)
        self.assertEqual(lead1.pk, lead2.pk)

    def test_owner_a_cannot_consume_or_affect_owner_bs_draft(self):
        owner_a = make_customer(suffix="own-a")
        owner_b = make_customer(suffix="own-b")
        draft_b, _ = save_draft_fields(
            owner=owner_b, form_type="leads_contact", fields={"request_type": "support"},
            current_step=0, expected_revision=0,
        )
        lead_a, created_a = finalize_form_draft_to_lead(
            owner=owner_a, form=bound_valid_form(), final_submission_token="tok-own-a",
            demo_selection=None, allow_new_lead=always_allow,
        )
        self.assertTrue(created_a)
        draft_b.refresh_from_db()
        self.assertEqual(draft_b.status, "open")
        self.assertIsNone(draft_b.submitted_lead_id)
        self.assertIsNone(draft_b.submission_token)

    def test_demo_snapshot_is_preserved_and_never_used_to_rebuild_a_live_fk(self):
        template = DemoTemplate.objects.create(
            slug="finalize-demo", category="ecommerce", title_fa="دموی نهایی", title_en="Finalize demo",
            tagline_fa="x", tagline_en="y", fictional_brand_fa="ب", fictional_brand_en="B", style_key="minimal",
        )
        customer = make_customer()
        selection = DemoSelection.objects.create(
            template=template, session_key="finalize-demo-session",
            selections={"theme": "warm", "personality": "minimal", "features": ["blog"]},
        )
        save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "ecommerce"},
            current_step=0, expected_revision=0,
        )
        draft = attach_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)
        snapshot_before = dict(draft.demo_snapshot)

        # demo_selection passed in is the caller's own, already-authorized
        # resolution (mirrors _session_demo_selection) — never derived from
        # the frozen snapshot.
        lead, created = finalize_form_draft_to_lead(
            owner=customer, form=bound_valid_form(), final_submission_token="tok-demo",
            demo_selection=selection, allow_new_lead=always_allow,
        )

        self.assertTrue(created)
        self.assertEqual(lead.demo_selection_id, selection.pk)
        draft.refresh_from_db()
        self.assertEqual(draft.demo_snapshot, snapshot_before)  # untouched, still frozen
        self.assertNotIn("session_key", str(draft.demo_snapshot))
        self.assertNotIn("public_token", str(draft.demo_snapshot))

    def test_replay_with_the_same_demo_selection_is_recognized_as_the_same_submission(self):
        customer = make_customer(suffix="demo-replay-same")
        selection = make_demo_selection(suffix="same")
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            lead1, created1 = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-same",
                demo_selection=selection, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        with self.captureOnCommitCallbacks(execute=True):
            lead2, created2 = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-same",
                demo_selection=selection, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(lead1.pk, lead2.pk)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(calls, [lead1.pk])  # the replay never re-notifies

    def test_replay_with_a_different_demo_selection_is_a_conflict_not_a_replay(self):
        customer = make_customer(suffix="demo-replay-diff")
        selection_a = make_demo_selection(suffix="diff-a")
        selection_b = make_demo_selection(suffix="diff-b")
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            lead1, _ = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-diff",
                demo_selection=selection_a, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        draft_before = FormDraft.objects.get(owner=customer).revision
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(SubmissionConflictError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-diff",
                    demo_selection=selection_b, allow_new_lead=always_allow,
                    on_created=lambda lead: calls.append(lead.pk),
                )
        self.assertEqual(Lead.objects.count(), 1)
        lead1.refresh_from_db()
        self.assertEqual(lead1.demo_selection_id, selection_a.pk)
        self.assertEqual(FormDraft.objects.get(owner=customer).revision, draft_before)
        self.assertEqual(calls, [lead1.pk])  # only the genuine creation ever notified

    def test_replay_that_removes_a_previously_attached_demo_selection_is_a_conflict(self):
        customer = make_customer(suffix="demo-replay-remove")
        selection = make_demo_selection(suffix="remove")
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            lead1, _ = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-remove",
                demo_selection=selection, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        draft_before = FormDraft.objects.get(owner=customer).revision
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(SubmissionConflictError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-remove",
                    demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
                )
        self.assertEqual(Lead.objects.count(), 1)
        lead1.refresh_from_db()
        self.assertEqual(lead1.demo_selection_id, selection.pk)
        self.assertEqual(FormDraft.objects.get(owner=customer).revision, draft_before)
        self.assertEqual(calls, [lead1.pk])

    def test_replay_that_adds_a_demo_selection_to_a_lead_that_had_none_is_a_conflict(self):
        customer = make_customer(suffix="demo-replay-add")
        selection = make_demo_selection(suffix="add")
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            lead1, _ = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-add",
                demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        draft_before = FormDraft.objects.get(owner=customer).revision
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(SubmissionConflictError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-demo-replay-add",
                    demo_selection=selection, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
                )
        self.assertEqual(Lead.objects.count(), 1)
        lead1.refresh_from_db()
        self.assertIsNone(lead1.demo_selection_id)
        self.assertEqual(FormDraft.objects.get(owner=customer).revision, draft_before)
        self.assertEqual(calls, [lead1.pk])

    def test_on_created_fires_exactly_once_only_after_commit(self):
        # transaction.on_commit callbacks never actually run inside a plain
        # TestCase (each test's own wrapping transaction is rolled back,
        # never committed) — captureOnCommitCallbacks(execute=True) is
        # Django's own supported way to prove a callback was correctly
        # *registered* for on-commit execution and run it as if a real
        # commit had happened.
        customer = make_customer()
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            lead, created = finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-on-commit",
                demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        self.assertTrue(created)
        self.assertEqual(calls, [lead.pk])

    def test_on_created_never_fires_on_a_replay(self):
        customer = make_customer()
        with self.captureOnCommitCallbacks(execute=True):
            finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-replay-no-notify",
                demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: None,
            )
        calls = []
        with self.captureOnCommitCallbacks(execute=True):
            finalize_form_draft_to_lead(
                owner=customer, form=bound_valid_form(), final_submission_token="tok-replay-no-notify",
                demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
            )
        self.assertEqual(calls, [])

    def test_on_created_never_fires_on_rollback(self):
        customer = make_customer()
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=0, expected_revision=0,
        )
        calls = []
        call_count = {"n": 0}
        original_save = FormDraft.save

        def flaky_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated failure between Lead creation and the submitted transition")
            return original_save(self, *args, **kwargs)

        with mock.patch.object(FormDraft, "save", flaky_save):
            with self.assertRaises(RuntimeError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-rollback-notify",
                    demo_selection=None, allow_new_lead=always_allow, on_created=lambda lead: calls.append(lead.pk),
                )

        self.assertEqual(calls, [])
        self.assertEqual(Lead.objects.count(), 0)
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")
        self.assertIsNone(draft.submission_token)


class FinalizeRollbackTests(TestCase):
    """SQLite-level proof of the Python-side rollback contract (mocked
    exception, not a real database-level error — see
    FinalizeRealTransactionErrorRecoveryTests below for that)."""

    def test_error_between_lead_creation_and_submitted_transition_rolls_back_everything(self):
        customer = make_customer()
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=0, expected_revision=0,
        )
        initial_revision = draft.revision
        call_count = {"n": 0}
        original_save = FormDraft.save

        def flaky_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:  # the "submitted" write, right after Lead creation
                raise RuntimeError("simulated failure")
            return original_save(self, *args, **kwargs)

        with mock.patch.object(FormDraft, "save", flaky_save):
            with self.assertRaises(RuntimeError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-rollback",
                    demo_selection=None, allow_new_lead=always_allow,
                )

        self.assertEqual(Lead.objects.count(), 0)
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")
        self.assertEqual(draft.revision, initial_revision)  # the submitting-transition rolled back too
        self.assertIsNone(draft.submission_token)
        self.assertIsNone(draft.submitted_lead_id)

    def test_outer_transaction_still_usable_after_a_handled_rollback(self):
        # Standing in for ATOMIC_REQUESTS: the caller's own outer
        # transaction.atomic() must remain fully usable after this
        # function raises and its own transaction rolls back.
        customer = make_customer()
        with self.assertRaises(NewLeadRateLimitedError):
            with transaction.atomic():
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-outer-usable",
                    demo_selection=None, allow_new_lead=never_allow,
                )
        # A plain, unrelated query must still work — the connection was
        # never left poisoned.
        self.assertEqual(Lead.objects.count(), 0)
        self.assertTrue(User.objects.filter(pk=customer.pk).exists())


class FinalizeIntegrityErrorRecoveryTests(TestCase):
    """Deterministic, SQLite-level branch coverage for the
    `except IntegrityError` recovery block in `finalize_form_draft_to_lead`
    — a genuine, PostgreSQL-forced unique-constraint collision under real
    concurrency is separately proven by
    `FinalizeFormDraftPostgresUniqueCollisionTests` below; these tests only
    prove the *recovery logic itself* takes the right branch once an
    IntegrityError has already happened, for each of the four cases the
    corrective phase specified."""

    def test_no_record_for_this_owner_after_the_collision_is_an_invalid_token_not_a_conflict(self):
        # Simulates the real cross-owner race: the row that actually won
        # the unique constraint belongs to someone else, so a lookup
        # scoped to *this* owner finds nothing at all.
        customer = make_customer(suffix="integrity-none")
        with mock.patch.object(FormDraft.objects, "create", side_effect=IntegrityError("unique violation")):
            with self.assertRaises(InvalidSubmissionTokenError):
                finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-integrity-none",
                    demo_selection=None, allow_new_lead=always_allow,
                )
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)

    def _patched_top_level_lookup_miss(self, token):
        """Returns a context manager that makes only the *very first*,
        token-only `FormDraft.objects.filter(submission_token=...)` lookup
        return nothing — simulating a genuine race where that read ran
        before a same-owner leftover row (created below, ahead of time)
        had committed — while leaving every other `.filter(...)` call
        (including the recovery lookup, which is always scoped by owner
        and form_type too) running for real against the database."""
        original_filter = FormDraft.objects.filter

        def filter_side_effect(*args, **kwargs):
            if set(kwargs) == {"submission_token"} and kwargs["submission_token"] == token:
                return FormDraft.objects.none()
            return original_filter(*args, **kwargs)

        return mock.patch.object(FormDraft.objects, "filter", side_effect=filter_side_effect)

    def test_a_recovered_record_that_never_reached_submitted_is_a_safe_conflict(self):
        customer = make_customer(suffix="integrity-unsubmitted")
        token = "tok-integrity-unsubmitted"
        # Deliberately NOT "open"/"submitting" (ACTIVE_STATUSES): a
        # leftover in either of those would be picked up and resumed by
        # `_get_active_draft_locked` itself, never reaching the `.create()`
        # call this test forces to fail — "expired" isolates the branch
        # under test (a record that never reached "submitted", found only
        # via the token-scoped recovery lookup after a real collision).
        leftover = FormDraft.objects.create(
            owner=customer, form_type="leads_contact", fields={}, current_step=0, status="expired",
            submission_token=token, expires_at=timezone.now() + timedelta(days=7),
        )
        with mock.patch.object(FormDraft.objects, "create", side_effect=IntegrityError("unique violation")):
            with self._patched_top_level_lookup_miss(token):
                with self.assertRaises(SubmissionConflictError):
                    finalize_form_draft_to_lead(
                        owner=customer, form=bound_valid_form(), final_submission_token=token,
                        demo_selection=None, allow_new_lead=always_allow,
                    )
        self.assertEqual(Lead.objects.count(), 0)
        leftover.refresh_from_db()
        self.assertIsNone(leftover.submitted_lead_id)

    def test_a_recovered_record_with_matching_content_and_demo_is_a_valid_replay(self):
        customer = make_customer(suffix="integrity-match")
        token = "tok-integrity-match"
        selection = make_demo_selection(suffix="integrity-match")
        lead = bound_valid_form().save(commit=False)
        lead.demo_selection = selection
        lead.privacy_accepted_at = timezone.now()
        lead.save()
        leftover = FormDraft.objects.create(
            owner=customer, form_type="leads_contact", fields={}, current_step=0, status="submitted",
            submission_token=token, submitted_lead=lead, expires_at=timezone.now() + timedelta(days=7),
        )
        with mock.patch.object(FormDraft.objects, "create", side_effect=IntegrityError("unique violation")):
            with self._patched_top_level_lookup_miss(token):
                result_lead, created = finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token=token,
                    demo_selection=selection, allow_new_lead=always_allow,
                )
        self.assertFalse(created)
        self.assertEqual(result_lead.pk, lead.pk)
        self.assertEqual(Lead.objects.count(), 1)
        leftover.refresh_from_db()
        self.assertEqual(leftover.status, "submitted")

    def test_a_recovered_record_with_different_content_is_a_conflict(self):
        customer = make_customer(suffix="integrity-diff")
        token = "tok-integrity-diff"
        lead = bound_valid_form(request_type="webapp").save(commit=False)
        lead.privacy_accepted_at = timezone.now()
        lead.save()
        leftover = FormDraft.objects.create(
            owner=customer, form_type="leads_contact", fields={}, current_step=0, status="submitted",
            submission_token=token, submitted_lead=lead, expires_at=timezone.now() + timedelta(days=7),
        )
        with mock.patch.object(FormDraft.objects, "create", side_effect=IntegrityError("unique violation")):
            with self._patched_top_level_lookup_miss(token):
                with self.assertRaises(SubmissionConflictError):
                    finalize_form_draft_to_lead(
                        owner=customer, form=bound_valid_form(request_type="ecommerce"),
                        final_submission_token=token, demo_selection=None, allow_new_lead=always_allow,
                    )
        self.assertEqual(Lead.objects.count(), 1)
        lead.refresh_from_db()
        self.assertEqual(lead.request_type, "webapp")


class LeadCreateViewAuthenticatedFinalizeTests(TestCase):
    def setUp(self):
        cache.clear()

    def _get_token(self, client, lang="fa"):
        response = client.get(CONTACT_URL + f"?lang={lang}")
        content = response.content.decode()
        marker = 'name="final_submission_token" value="'
        start = content.index(marker) + len(marker)
        end = content.index('"', start)
        return content[start:end]

    def test_authenticated_customer_valid_submission_creates_one_lead_and_submits_draft(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=2, expected_revision=0,
        )
        token = self._get_token(client)

        with self.captureOnCommitCallbacks(execute=True):
            response = client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))

        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")
        self.assertEqual(Lead.objects.count(), 1)
        draft = FormDraft.objects.get(owner=customer)
        self.assertEqual(draft.status, "submitted")
        self.assertEqual(draft.submitted_lead_id, lead.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(lead.tracking_code, mail.outbox[0].subject)

    def test_invalid_form_creates_no_lead_and_leaves_draft_open(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=2, expected_revision=0,
        )
        initial_revision = draft.revision
        token = self._get_token(client)
        payload = valid_payload(final_submission_token=token)
        payload.pop("privacy_accept")  # a real validation failure

        response = client.post(CONTACT_URL + "?lang=fa", payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")
        self.assertEqual(draft.revision, initial_revision)
        self.assertIsNone(draft.submission_token)

    def test_resubmitting_the_same_request_returns_the_same_thanks_page(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        payload = valid_payload(final_submission_token=token)

        with self.captureOnCommitCallbacks(execute=True):
            response1 = client.post(CONTACT_URL + "?lang=fa", payload)
        lead1 = Lead.objects.get()
        with self.captureOnCommitCallbacks(execute=True):
            response2 = client.post(CONTACT_URL + "?lang=fa", payload)

        self.assertEqual(Lead.objects.count(), 1)
        self.assertRedirects(response1, reverse("leads:thanks", args=[lead1.tracking_code]) + "?lang=fa")
        self.assertRedirects(response2, reverse("leads:thanks", args=[lead1.tracking_code]) + "?lang=fa")
        self.assertEqual(len(mail.outbox), 1)  # never a second notification

    def test_resubmitting_the_same_token_with_different_content_is_a_safe_conflict(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))
        self.assertEqual(Lead.objects.count(), 1)

        response = client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token, name="یک نام متفاوت"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertContains(response, "قبلاً با اطلاعات دیگری ثبت شده")

    def test_a_new_token_and_a_new_submission_create_a_second_lead(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token1 = self._get_token(client)
        client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token1, request_type="webapp"))
        self.assertEqual(Lead.objects.count(), 1)

        # Isolates "two different tokens are two different submissions"
        # from the pre-existing, unrelated, still-active IP rate limiter —
        # a real second submission this soon would otherwise be correctly
        # rejected by that limiter, which is a separate concern already
        # covered by its own tests below.
        cache.clear()
        token2 = self._get_token(client)
        self.assertNotEqual(token1, token2)
        client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token2, request_type="ecommerce"))

        self.assertEqual(Lead.objects.count(), 2)

    def test_token_from_a_different_owner_is_rejected_neutrally(self):
        owner_a = make_customer(suffix="view-a")
        owner_b = make_customer(suffix="view-b")
        client_a = Client()
        client_a.force_login(owner_a)
        token_a = self._get_token(client_a)
        # owner_a must actually claim the token first — an unused token
        # belongs to no one yet, so it is not "foreign" to anybody.
        client_a.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token_a))
        self.assertEqual(Lead.objects.count(), 1)

        client_b = Client()
        client_b.force_login(owner_b)
        response = client_b.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token_a))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(FormDraft.objects.filter(owner=owner_b).count(), 0)

    def test_missing_blank_or_oversized_token_is_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        for bad_token in ("", "x" * 65):
            response = client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=bad_token))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    def test_expired_and_deleted_and_no_draft_all_still_succeed_explicitly(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        # No draft at all yet.
        token = self._get_token(client)
        response = client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))
        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")

        # Guest/staff paths never touch a draft — smoke-checked separately below.
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 1)

    def test_returning_to_the_form_does_not_show_the_submitted_draft_as_continuable(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))
        self.assertEqual(Lead.objects.count(), 1)

        response = client.get(CONTACT_URL + "?lang=fa")

        self.assertNotContains(response, "پیش‌نویس ذخیره‌شده در حساب شما پیدا شد")

    def test_no_forbidden_token_anywhere_in_json_api_log_or_email(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        with self.captureOnCommitCallbacks(execute=True):
            client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))
        draft = FormDraft.objects.get(owner=customer)
        self.assertEqual(draft.submission_token, token)

        draft_json = client.get(reverse("leads:draft")).json()
        self.assertEqual(draft_json, {"draft": None})  # submitted, so no longer "active"
        self.assertNotIn("submission_token", str(draft_json))

        email_body = mail.outbox[0].body + mail.outbox[0].subject
        self.assertNotIn(token, email_body)
        self.assertNotIn("submission_token", email_body)

    def test_validation_rerender_keeps_typed_values_and_the_same_token(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        payload = valid_payload(final_submission_token=token, preferred_contact="phone", phone="")

        response = client.post(CONTACT_URL + "?lang=fa", payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)
        content = response.content.decode()
        self.assertIn(f'value="{token}"', content)
        self.assertContains(response, "آروین یزدانی")

    def test_fa_and_en_error_messages_are_language_specific(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        token = self._get_token(client)
        client.post(CONTACT_URL + "?lang=fa", valid_payload(final_submission_token=token))

        response_en = client.post(CONTACT_URL + "?lang=en", valid_payload(final_submission_token=token, name="Someone else"))
        self.assertContains(response_en, "already recorded with different information")
        self.assertNotContains(response_en, "قبلاً با اطلاعات دیگری ثبت شده")


class FinalizeGuestStaffSuperuserUnaffectedTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_guest_submission_unaffected_no_draft_no_token_field(self):
        client = Client()
        response = client.post(CONTACT_URL + "?lang=fa", valid_payload())
        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")
        self.assertEqual(FormDraft.objects.count(), 0)

        page = client.get(CONTACT_URL + "?lang=fa")
        self.assertNotContains(page, "final_submission_token")

    def test_staff_submission_unaffected_no_draft_no_token_field(self):
        staff = make_staff()
        client = Client()
        client.force_login(staff)
        response = client.post(CONTACT_URL + "?lang=fa", valid_payload())
        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")
        self.assertEqual(FormDraft.objects.count(), 0)

        page = client.get(CONTACT_URL + "?lang=fa")
        self.assertNotContains(page, "final_submission_token")

    def test_superuser_submission_unaffected_no_draft_no_token_field(self):
        superuser = User.objects.create_superuser(
            username="finalize-superuser@example.com", email="finalize-superuser@example.com", password="x",
        )
        client = Client()
        client.force_login(superuser)
        response = client.post(CONTACT_URL + "?lang=fa", valid_payload())
        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")
        self.assertEqual(FormDraft.objects.count(), 0)


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "Genuine row-lock concurrency can only be demonstrated on a real database engine; skipped on SQLite.",
)
class FinalizeFormDraftPostgresConcurrencyTests(TransactionTestCase):
    def test_two_truly_concurrent_submissions_with_the_same_token_converge_to_one_lead(self):
        customer = User.objects.create_user(
            username="finalize-race@example.com", email="finalize-race@example.com", password="x", is_active=True,
        )
        save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=2, expected_revision=0,
        )
        barrier = threading.Barrier(2)
        outcomes = []

        def attempt():
            try:
                barrier.wait(timeout=5)
                lead, created = finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(), final_submission_token="tok-real-race",
                    demo_selection=None, allow_new_lead=always_allow,
                )
                outcomes.append(("ok", lead.pk, created))
            except Exception as exc:
                outcomes.append(("error", exc, None))
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        for t in threads:
            self.assertFalse(t.is_alive(), "a thread is still running — possible deadlock or hang")

        errors = [o for o in outcomes if o[0] == "error"]
        self.assertEqual(errors, [], errors)
        self.assertEqual(len(outcomes), 2)
        lead_pks = {o[1] for o in outcomes}
        self.assertEqual(len(lead_pks), 1, "both threads must resolve to the exact same Lead")
        created_flags = sorted(o[2] for o in outcomes)
        self.assertEqual(created_flags, [False, True], "exactly one thread creates, the other replays")
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(FormDraft.objects.filter(owner=customer, status="submitted").count(), 1)

    def test_two_different_real_tokens_from_two_real_submissions_create_two_leads(self):
        customer = User.objects.create_user(
            username="finalize-two-real@example.com", email="finalize-two-real@example.com",
            password="x", is_active=True,
        )
        barrier = threading.Barrier(2)
        outcomes = []

        def attempt(token, request_type):
            try:
                barrier.wait(timeout=5)
                lead, created = finalize_form_draft_to_lead(
                    owner=customer, form=bound_valid_form(request_type=request_type), final_submission_token=token,
                    demo_selection=None, allow_new_lead=always_allow,
                )
                outcomes.append(("ok", lead.pk, created))
            except Exception as exc:
                outcomes.append(("error", exc, None))
            finally:
                connection.close()

        threads = [
            threading.Thread(target=attempt, args=("tok-real-a", "webapp")),
            threading.Thread(target=attempt, args=("tok-real-b", "ecommerce")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        errors = [o for o in outcomes if o[0] == "error"]
        self.assertEqual(errors, [], errors)
        self.assertEqual({o[1] for o in outcomes}.__len__(), 2, "two distinct real submissions must never collapse")
        self.assertEqual(Lead.objects.count(), 2)


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "A genuine unique-constraint collision under real concurrency can only be forced and "
    "observed on a real database engine — skipped on SQLite.",
)
class FinalizeFormDraftPostgresUniqueCollisionTests(TransactionTestCase):
    """Proves the `except IntegrityError` branch on a real, PostgreSQL-
    forced unique-constraint violation — not a mocked exception (see
    FinalizeIntegrityErrorRecoveryTests above for that). Two different
    owners race the exact same token; a barrier placed only at the real
    `FormDraft.objects.create(...)` insert call guarantees both threads
    have already completed their own (independent, unlocked — different
    owners are never serialized by the owner-row lock) initial token
    lookup before either attempts to insert, so both inserts genuinely
    reach the database and PostgreSQL itself decides the one winner."""

    def test_two_different_owners_racing_the_same_token_hit_a_real_unique_collision(self):
        owner_a = User.objects.create_user(
            username="finalize-collision-a@example.com", email="finalize-collision-a@example.com",
            password="x", is_active=True,
        )
        owner_b = User.objects.create_user(
            username="finalize-collision-b@example.com", email="finalize-collision-b@example.com",
            password="x", is_active=True,
        )
        token = "tok-real-unique-collision"
        barrier = threading.Barrier(2)
        original_create = FormDraft.objects.create
        outcomes = []

        def barrier_create(*args, **kwargs):
            # The barrier only synchronizes both threads at the exact
            # insert call site — the insert itself, and any IntegrityError
            # it raises, are real, unmodified PostgreSQL behavior.
            barrier.wait(timeout=5)
            return original_create(*args, **kwargs)

        def attempt(owner):
            try:
                lead, created = finalize_form_draft_to_lead(
                    owner=owner, form=bound_valid_form(), final_submission_token=token,
                    demo_selection=None, allow_new_lead=always_allow,
                )
                outcomes.append({"result": "ok", "owner_pk": owner.pk, "lead_pk": lead.pk, "created": created})
            except Exception as exc:
                try:
                    healthy_after = User.objects.filter(pk=owner.pk).exists()
                except Exception:
                    healthy_after = False
                outcomes.append(
                    {"result": "error", "owner_pk": owner.pk, "exc": exc, "healthy_after": healthy_after}
                )
            finally:
                connection.close()

        with mock.patch.object(FormDraft.objects, "create", side_effect=barrier_create):
            threads = [
                threading.Thread(target=attempt, args=(owner_a,)),
                threading.Thread(target=attempt, args=(owner_b,)),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)
        for t in threads:
            self.assertFalse(t.is_alive(), "a thread is still running — possible deadlock or hang")

        self.assertEqual(len(outcomes), 2)
        oks = [o for o in outcomes if o["result"] == "ok"]
        errors = [o for o in outcomes if o["result"] == "error"]
        self.assertEqual(len(oks), 1, outcomes)
        self.assertEqual(len(errors), 1, outcomes)
        self.assertIsInstance(errors[0]["exc"], InvalidSubmissionTokenError)

        # Exactly one Lead and one token-bearing FormDraft in the whole
        # database — the loser wrote nothing.
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(FormDraft.objects.filter(submission_token=token).count(), 1)
        winner_owner_pk = oks[0]["owner_pk"]
        loser_owner_pk = errors[0]["owner_pk"]
        self.assertNotEqual(winner_owner_pk, loser_owner_pk)
        winning_draft = FormDraft.objects.get(submission_token=token)
        self.assertEqual(winning_draft.owner_id, winner_owner_pk)
        self.assertEqual(FormDraft.objects.filter(owner_id=loser_owner_pk).count(), 0)

        # The loser's own connection/transaction is fully usable again
        # immediately after IntegrityError was handled.
        self.assertTrue(errors[0]["healthy_after"])
        with transaction.atomic():
            self.assertTrue(User.objects.filter(pk=loser_owner_pk).exists())


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "A genuine database-level transaction abort inside an outer ATOMIC_REQUESTS-style "
    "transaction can only be forced and observed on a real database engine — skipped on SQLite.",
)
class FinalizeRealTransactionErrorRecoveryTests(TransactionTestCase):
    """A mocked Python exception (FinalizeRollbackTests above) proves our
    own exception handling works, but never touches the database — it is
    not evidence about PostgreSQL's own transaction-abort semantics. This
    forces a real, server-rejected statement at the exact same call site
    and proves the outer transaction survives."""

    def test_real_postgresql_error_between_lead_creation_and_submitted_write_rolls_back_and_leaves_outer_transaction_usable(self):
        customer = User.objects.create_user(
            username="finalize-real-error@example.com", email="finalize-real-error@example.com",
            password="x", is_active=True,
        )
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=0, expected_revision=0,
        )
        initial_revision = draft.revision

        call_count = {"n": 0}
        original_save = FormDraft.save

        def flaky_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1/0")
            return original_save(self, *args, **kwargs)

        # Stands in for Django's own ATOMIC_REQUESTS per-request wrapping.
        with transaction.atomic():
            with mock.patch.object(FormDraft, "save", flaky_save):
                with self.assertRaises(Exception):
                    finalize_form_draft_to_lead(
                        owner=customer, form=bound_valid_form(), final_submission_token="tok-real-rollback",
                        demo_selection=None, allow_new_lead=always_allow,
                    )
            # Still inside the SAME outer transaction: a real, healthy
            # query must succeed here — proving the inner failure did not
            # poison it.
            self.assertTrue(User.objects.filter(pk=customer.pk).exists())
            self.assertEqual(Lead.objects.filter().count(), 0)

        self.assertEqual(Lead.objects.count(), 0)
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")
        self.assertEqual(draft.revision, initial_revision)
        self.assertIsNone(draft.submission_token)
