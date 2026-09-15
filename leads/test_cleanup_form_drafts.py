"""V2.1-E1: `cleanup_form_drafts` — safe, batch-safe deletion of already-
`expired`, unconnected FormDraft rows past the retention window. Never
touches an open/submitting/submitted draft, a draft attached to a
submitted Lead, or a draft still carrying a submission_token, regardless
of age. Dry-run by default; --apply is required to actually delete.

Deliberately does not touch `leads.form_draft_service` or `FormDraft`'s
own lifecycle transitions — this only removes rows that are already in
their terminal "expired" state."""

from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from leads.models import FormDraft, Lead

User = get_user_model()


def make_customer(suffix="a"):
    return User.objects.create_user(
        username=f"cleanup-draft-owner-{suffix}@example.com", email=f"cleanup-draft-owner-{suffix}@example.com",
        password="x", is_active=True,
    )


def make_lead(suffix="a"):
    return Lead.objects.create(
        name="مشتری تست", email_or_telegram=f"cleanup-lead-{suffix}@example.com", phone="09120000000",
        message="این یک پیام تست معتبر برای پاک‌سازی است.", privacy_accepted_at=timezone.now(),
    )


class CleanupFormDraftsCommandTests(TestCase):
    def _make_draft(self, *, owner=None, suffix="a", status="expired", age_days=40,
                     submitted_lead=None, submission_token=None):
        owner = owner or make_customer(suffix=suffix)
        draft = FormDraft.objects.create(
            owner=owner, form_type="leads_contact", fields={}, current_step=0, status=status,
            submitted_lead=submitted_lead, submission_token=submission_token,
        )
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() - timedelta(days=age_days))
        draft.refresh_from_db()
        return draft

    def test_dry_run_reports_count_and_deletes_nothing(self):
        eligible = self._make_draft(suffix="dry")
        out = StringIO()

        call_command("cleanup_form_drafts", stdout=out)

        self.assertIn("1", out.getvalue())
        self.assertTrue(FormDraft.objects.filter(pk=eligible.pk).exists())

    def test_apply_deletes_only_the_record_matching_all_four_conditions(self):
        eligible = self._make_draft(suffix="apply-eligible")
        not_expired_status = self._make_draft(suffix="apply-open", status="open")
        with_lead = self._make_draft(suffix="apply-lead", submitted_lead=make_lead("apply"))
        with_token = self._make_draft(suffix="apply-token", submission_token="tok-apply-keep")

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        self.assertFalse(FormDraft.objects.filter(pk=eligible.pk).exists())
        self.assertTrue(FormDraft.objects.filter(pk=not_expired_status.pk).exists())
        self.assertTrue(FormDraft.objects.filter(pk=with_lead.pk).exists())
        self.assertTrue(FormDraft.objects.filter(pk=with_token.pk).exists())

    def test_freshly_expired_draft_is_not_deleted(self):
        fresh = self._make_draft(suffix="fresh", age_days=1)

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=fresh.pk).exists())

    def test_open_submitting_submitted_are_never_deleted_even_if_very_old(self):
        drafts = [
            self._make_draft(suffix="old-open", status="open", age_days=365),
            self._make_draft(suffix="old-submitting", status="submitting", age_days=365),
            self._make_draft(suffix="old-submitted", status="submitted", age_days=365),
        ]

        out = StringIO()
        call_command("cleanup_form_drafts", stdout=out)
        self.assertIn("0", out.getvalue())

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        for draft in drafts:
            self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_draft_attached_to_a_submitted_lead_is_never_deleted(self):
        lead = make_lead("attached")
        draft = self._make_draft(suffix="attached", submitted_lead=lead, age_days=365)

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())
        self.assertTrue(Lead.objects.filter(pk=lead.pk).exists())

    def test_draft_with_a_submission_token_is_never_deleted(self):
        draft = self._make_draft(suffix="token", submission_token="tok-keep-forever", age_days=365)

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_small_batch_size_processes_multiple_batches_correctly(self):
        eligible = [self._make_draft(suffix=f"batch-{i}") for i in range(5)]

        call_command("cleanup_form_drafts", "--apply", "--batch-size", "2", stdout=StringIO())

        for draft in eligible:
            self.assertFalse(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_zero_or_negative_older_than_days_is_rejected_without_writing(self):
        draft = self._make_draft(suffix="reject-days")

        with self.assertRaises(CommandError):
            call_command("cleanup_form_drafts", "--older-than-days", "0", "--apply", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("cleanup_form_drafts", "--older-than-days", "-5", "--apply", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_zero_or_negative_batch_size_is_rejected_without_writing(self):
        draft = self._make_draft(suffix="reject-batch")

        with self.assertRaises(CommandError):
            call_command("cleanup_form_drafts", "--batch-size", "0", "--apply", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("cleanup_form_drafts", "--batch-size", "-1", "--apply", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_a_record_that_becomes_ineligible_between_selection_and_deletion_survives(self):
        # Simulates a genuine concurrent change landing in the exact window
        # between the batch's id-selection query and its delete query,
        # proving the delete re-applies the full eligibility filter rather
        # than trusting pk__in alone.
        draft = self._make_draft(suffix="race")
        original_filter = FormDraft.objects.filter

        def filter_side_effect(*args, **kwargs):
            if kwargs.get("pk__in") == [draft.pk]:
                FormDraft.objects.filter(pk=draft.pk).update(status="open")
            return original_filter(*args, **kwargs)

        with mock.patch.object(FormDraft.objects, "filter", side_effect=filter_side_effect):
            call_command("cleanup_form_drafts", "--apply", "--batch-size", "1", stdout=StringIO())

        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())
        draft.refresh_from_db()
        self.assertEqual(draft.status, "open")

    def test_output_never_contains_private_or_identifying_information(self):
        owner = make_customer(suffix="privacy")
        draft = self._make_draft(
            owner=owner, suffix="privacy", submission_token=None,
        )
        FormDraft.objects.filter(pk=draft.pk).update(
            fields={"request_type": "webapp", "budget_range": "50_150"},
        )
        out = StringIO()

        call_command("cleanup_form_drafts", stdout=out)
        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())
        content = out.getvalue()

        # Bare numeric ids are deliberately not substring-checked here: a
        # small owner/draft pk can collide harmlessly with unrelated
        # output (e.g. the printed count or the default retention days) —
        # the same reasoning already established in leads.test_finalize /
        # leads.test_contact_server_draft_ui. The command's own output
        # design never includes a per-row identifier at all; the checks
        # below cover every value shape it could otherwise leak.
        self.assertNotIn(owner.email, content)
        self.assertNotIn("webapp", content)
        self.assertNotIn("50_150", content)
        self.assertNotIn("demo_snapshot", content)
        self.assertNotIn("submission_token", content)
        self.assertNotIn("submitted_lead", content)

    def test_deleting_form_drafts_never_cascades_to_leads_or_users(self):
        owner = make_customer(suffix="cascade")
        unrelated_lead = make_lead("cascade-unrelated")
        eligible = self._make_draft(owner=owner, suffix="cascade")

        call_command("cleanup_form_drafts", "--apply", stdout=StringIO())

        self.assertFalse(FormDraft.objects.filter(pk=eligible.pk).exists())
        self.assertTrue(User.objects.filter(pk=owner.pk).exists())
        self.assertTrue(Lead.objects.filter(pk=unrelated_lead.pk).exists())
