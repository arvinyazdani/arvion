from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from leads.models import FormDraft

DEFAULT_RETENTION_DAYS = 30
DEFAULT_BATCH_SIZE = 500


class Command(BaseCommand):
    help = (
        "Delete FormDraft rows that are already expired, unconnected to any "
        "submitted Lead or idempotency token, and past the retention window. "
        "Dry-run by default; pass --apply to actually delete. Never touches "
        "an open/submitting/submitted draft, a draft attached to a Lead, or "
        "a draft still carrying a submission_token, regardless of age."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days", type=int, default=DEFAULT_RETENTION_DAYS,
            help=f"Retention window in days, measured against expires_at (default: {DEFAULT_RETENTION_DAYS}).",
        )
        parser.add_argument(
            "--apply", action="store_true",
            help="Actually delete the eligible rows. Without this flag, the command only reports a count.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
            help=f"Maximum rows deleted per batch (default: {DEFAULT_BATCH_SIZE}).",
        )

    def handle(self, *args, **options):
        older_than_days = options["older_than_days"]
        batch_size = options["batch_size"]

        if older_than_days <= 0:
            raise CommandError("--older-than-days must be a positive integer.")
        if batch_size <= 0:
            raise CommandError("--batch-size must be a positive integer.")

        cutoff = timezone.now() - timedelta(days=older_than_days)

        # A draft is only eligible when ALL four hold at once: it has
        # already transitioned to "expired" (never "open"/"submitting"/
        # "submitted", regardless of age); its own expires_at is older than
        # the retention cutoff (an expired-but-recent draft is kept a
        # while longer, e.g. for support/debugging); it was never attached
        # to a submitted Lead; and it never carries a submission_token —
        # both of the last two guard the V2.1-D idempotency contract, since
        # a token or a submitted_lead is exactly what a sequential retry
        # would need to find to recognize its own prior submission.
        def eligible_queryset():
            return FormDraft.objects.filter(
                status="expired", expires_at__lt=cutoff,
                submitted_lead__isnull=True, submission_token__isnull=True,
            )

        # Deliberately described in plain, human-readable terms rather than
        # by field name: this text reaches an operator's terminal/log, and
        # must never resemble the internal schema (no mention of
        # "submission_token"/"submitted_lead" by name, no ids, no owner or
        # draft content of any kind — only the aggregate policy and count).
        policy = (
            f"already expired, unlinked to any completed enquiry, not part of an "
            f"in-progress submission attempt, and expired more than {older_than_days} day(s) ago"
        )

        if not options["apply"]:
            count = eligible_queryset().count()
            self.stdout.write(
                f"Dry run: {count} FormDraft row(s) match the deletion policy ({policy}). "
                "Re-run with --apply to delete them."
            )
            return

        deleted_total = 0
        while True:
            batch_ids = list(eligible_queryset().order_by("pk").values_list("pk", flat=True)[:batch_size])
            if not batch_ids:
                break
            # Re-apply the full eligibility filter at delete time (never
            # just pk__in) so a draft that stopped being eligible between
            # the id lookup above and this delete — reopened, submitted,
            # attached to a Lead, or given a token — is never removed.
            with transaction.atomic():
                _, deleted_by_model = FormDraft.objects.filter(
                    pk__in=batch_ids, status="expired", expires_at__lt=cutoff,
                    submitted_lead__isnull=True, submission_token__isnull=True,
                ).delete()
            deleted_total += deleted_by_model.get(FormDraft._meta.label, 0)

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_total} FormDraft row(s) matching the deletion policy ({policy}).")
        )
