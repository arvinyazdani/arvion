import os
from datetime import timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from management_portal.backups import find_backup_inventory
from management_portal.models import ManagementNotification


class BackupInventoryTests(SimpleTestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "backups"
        (self.root / "daily").mkdir(parents=True)

    def create_backup(self, relative_path, *, age_hours=0, content=b"backup"):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        modified = (timezone.now() - timedelta(hours=age_hours)).timestamp()
        os.utime(path, (modified, modified))
        return path

    def test_daily_is_preferred_and_history_includes_release_snapshots_only(self):
        daily = self.create_backup("daily/postgres-20260820-023000.dump", age_hours=12)
        pre_release = self.create_backup("pre-release-20260821-010000.dump", age_hours=1)
        self.create_backup("daily/nested/postgres-ignored.dump", age_hours=0)
        self.create_backup("unrelated.dump", age_hours=0)
        symlink = self.root / "daily" / "postgres-symlink.dump"
        try:
            symlink.symlink_to(pre_release)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")

        inventory = find_backup_inventory(self.root)

        self.assertEqual(inventory.preferred.path, daily)
        self.assertEqual({item.name for item in inventory.history}, {daily.name, pre_release.name})
        self.assertEqual([item.source for item in inventory.daily], ["daily"])
        self.assertEqual([item.source for item in inventory.pre_release], ["pre_release"])

    def test_symlinked_daily_directory_is_ignored_and_release_snapshot_is_fallback(self):
        pre_release = self.create_backup("pre-release-20260821-010000.dump")
        external = self.root / "external"
        external.mkdir()
        (external / "postgres-external.dump").write_bytes(b"external")
        daily = self.root / "daily"
        daily.rmdir()
        try:
            daily.symlink_to(external, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")

        inventory = find_backup_inventory(self.root)

        self.assertEqual(inventory.daily, ())
        self.assertEqual(inventory.preferred.path, pre_release)


class BackupIntegrationTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate)
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "backups"
        (self.root / "daily").mkdir(parents=True)

    def create_backup(self, relative_path, *, age_hours=0):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"database backup")
        modified = (timezone.now() - timedelta(hours=age_hours)).timestamp()
        os.utime(path, (modified, modified))
        return path

    @override_settings(OPERATIONS_BACKUP_MAX_AGE_HOURS=26, OPERATIONS_DISK_ALERT_PERCENT=101)
    def test_health_check_does_not_allow_fresh_release_snapshot_to_mask_stale_daily_backup(self):
        daily = self.create_backup("daily/postgres-stale.dump", age_hours=30)
        self.create_backup("pre-release-fresh.dump", age_hours=1)

        with override_settings(CRM_BACKUP_DIR=self.root):
            call_command("check_operations_health", stdout=StringIO())

        alert = ManagementNotification.objects.get(source_key="health:backup")
        self.assertIn(daily.name, alert.description)
        self.assertEqual(alert.status, "unread")

    @override_settings(OPERATIONS_BACKUP_MAX_AGE_HOURS=26)
    def test_management_display_prefers_daily_and_lists_pre_release_history(self):
        daily = self.create_backup("daily/postgres-primary.dump", age_hours=12)
        for number in range(9):
            self.create_backup(f"daily/postgres-history-{number}.dump", age_hours=13 + number)
        pre_release = self.create_backup("pre-release-history.dump", age_hours=100)
        root = User.objects.create_superuser(
            username="backup-root", email="backup-root@example.com", password="safe-password",
        )
        self.client.force_login(root)

        with override_settings(CRM_BACKUP_DIR=self.root):
            response = self.client.get(reverse("management_portal:crm_workspace"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["backup_status"]["name"], daily.name)
        self.assertEqual(response.context["backup_status"]["source"], "daily")
        self.assertContains(response, "آخرین بکاپ روزانه")
        self.assertContains(response, daily.name)
        self.assertContains(response, pre_release.name)
        self.assertLessEqual(len(response.context["backup_status"]["history"]), 8)

    @override_settings(OPERATIONS_BACKUP_MAX_AGE_HOURS=26)
    def test_management_display_falls_back_to_pre_release_snapshot(self):
        pre_release = self.create_backup("pre-release-only.dump", age_hours=2)
        root = User.objects.create_superuser(
            username="fallback-root", email="fallback-root@example.com", password="safe-password",
        )
        self.client.force_login(root)

        with override_settings(CRM_BACKUP_DIR=self.root):
            response = self.client.get(reverse("management_portal:crm_workspace"))

        self.assertEqual(response.context["backup_status"]["name"], pre_release.name)
        self.assertEqual(response.context["backup_status"]["source"], "pre_release")
        self.assertContains(response, "آخرین نسخه پشتیبان پیش از انتشار")
