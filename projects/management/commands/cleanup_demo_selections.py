from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from projects.models import DemoSelection

DEFAULT_RETENTION_DAYS = 30
DEFAULT_BATCH_SIZE = 500


class Command(BaseCommand):
    help = (
        "Delete DemoSelection rows that were never attached to a Lead and have "
        "had no activity for at least the retention window. Dry-run by "
        "default; pass --apply to actually delete."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days", type=int, default=DEFAULT_RETENTION_DAYS,
            help=f"Retention window in days (default: {DEFAULT_RETENTION_DAYS}).",
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

        # A selection is only eligible once it is BOTH unattached to any real
        # request (`leads__isnull=True` — reverse of Lead.demo_selection,
        # the only foreign key onto this model anywhere in the project) and
        # stale (no activity, i.e. `updated_at`, within the retention
        # window). Filtering on `updated_at` rather than `created_at` avoids
        # deleting a selection someone is still actively reconfiguring.
        def eligible_queryset():
            return DemoSelection.objects.filter(leads__isnull=True, updated_at__lt=cutoff)

        if not options["apply"]:
            count = eligible_queryset().count()
            self.stdout.write(
                f"Dry run: {count} unattached DemoSelection row(s) older than "
                f"{older_than_days} day(s) are eligible for deletion. "
                "Re-run with --apply to delete them."
            )
            return

        deleted_total = 0
        while True:
            batch_ids = list(eligible_queryset().order_by("pk").values_list("pk", flat=True)[:batch_size])
            if not batch_ids:
                break
            # Re-apply the full eligibility filter at delete time (not just
            # pk__in) so a selection that gets attached to a Lead between
            # the id lookup above and this delete is never removed.
            with transaction.atomic():
                _, deleted_by_model = DemoSelection.objects.filter(
                    pk__in=batch_ids, leads__isnull=True, updated_at__lt=cutoff,
                ).delete()
            deleted_total += deleted_by_model.get(DemoSelection._meta.label, 0)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_total} unattached DemoSelection row(s) older than "
                f"{older_than_days} day(s)."
            )
        )
