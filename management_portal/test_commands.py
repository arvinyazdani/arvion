from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from management_portal.models import SystemLog


class CleanupSystemLogsCommandTests(TestCase):
    def create_log(self, *, age_days):
        system_log = SystemLog.objects.create(
            level="error",
            category="server",
            message_fa=f"لاگ {age_days} روزه",
        )
        SystemLog.objects.filter(pk=system_log.pk).update(
            created_at=timezone.now() - timedelta(days=age_days)
        )
        return system_log

    @override_settings(SYSTEM_LOG_RETENTION_DAYS=30)
    def test_deletes_only_logs_older_than_configured_retention_in_batches(self):
        expired = self.create_log(age_days=31)
        recent = self.create_log(age_days=29)
        stdout = StringIO()

        call_command("cleanup_system_logs", batch_size=1, stdout=stdout)

        self.assertFalse(SystemLog.objects.filter(pk=expired.pk).exists())
        self.assertTrue(SystemLog.objects.filter(pk=recent.pk).exists())
        self.assertIn("Deleted 1 SystemLog row(s) older than 30 day(s).", stdout.getvalue())

    @override_settings(SYSTEM_LOG_RETENTION_DAYS=30)
    def test_dry_run_reports_without_deleting(self):
        expired = self.create_log(age_days=31)
        stdout = StringIO()

        call_command("cleanup_system_logs", dry_run=True, stdout=stdout)

        self.assertTrue(SystemLog.objects.filter(pk=expired.pk).exists())
        self.assertIn("Dry run: 1 SystemLog row(s)", stdout.getvalue())

    def test_explicit_retention_override_is_used(self):
        expired_for_override = self.create_log(age_days=8)

        call_command("cleanup_system_logs", retention_days=7, stdout=StringIO())

        self.assertFalse(SystemLog.objects.filter(pk=expired_for_override.pk).exists())

    def test_rejects_unsafe_retention_and_batch_values(self):
        with self.assertRaisesMessage(CommandError, "retention-days must be at least 1"):
            call_command("cleanup_system_logs", retention_days=0, stdout=StringIO())
        with self.assertRaisesMessage(CommandError, "batch-size must be between 1 and 10000"):
            call_command("cleanup_system_logs", batch_size=0, stdout=StringIO())
