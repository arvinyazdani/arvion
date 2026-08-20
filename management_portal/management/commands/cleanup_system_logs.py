from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from management_portal.models import SystemLog


class Command(BaseCommand):
    help = "Delete SystemLog rows older than the configured retention period."

    def add_arguments(self, parser):
        parser.add_argument(
            "--retention-days",
            type=int,
            help="Override SYSTEM_LOG_RETENTION_DAYS for this run.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Maximum rows deleted per transaction (default: 1000).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report eligible rows without deleting them.",
        )

    def handle(self, *args, **options):
        retention_days = options["retention_days"]
        if retention_days is None:
            retention_days = settings.SYSTEM_LOG_RETENTION_DAYS
        batch_size = options["batch_size"]

        if retention_days < 1:
            raise CommandError("retention-days must be at least 1.")
        if not 1 <= batch_size <= 10_000:
            raise CommandError("batch-size must be between 1 and 10000.")

        cutoff = timezone.now() - timedelta(days=retention_days)
        expired_logs = SystemLog.objects.filter(created_at__lt=cutoff)

        if options["dry_run"]:
            eligible_count = expired_logs.count()
            self.stdout.write(
                f"Dry run: {eligible_count} SystemLog row(s) older than "
                f"{retention_days} day(s) are eligible for deletion."
            )
            return

        deleted_count = 0
        while True:
            expired_ids = list(
                expired_logs.order_by("pk").values_list("pk", flat=True)[:batch_size]
            )
            if not expired_ids:
                break
            _, deleted_by_model = SystemLog.objects.filter(pk__in=expired_ids).delete()
            deleted_count += deleted_by_model.get(SystemLog._meta.label, 0)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} SystemLog row(s) older than "
                f"{retention_days} day(s)."
            )
        )
