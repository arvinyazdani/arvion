from datetime import datetime, timedelta
from pathlib import Path
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from management_portal.models import ManagementNotification
from management_portal.notifications import create_receipts
from management_portal.backups import find_backup_inventory


class Command(BaseCommand):
    help = "Check operational disk, database and backup freshness and publish actionable inbox alerts."

    def handle(self, *args, **options):
        connection.ensure_connection()
        app_dir = Path("/srv/arvion") if Path("/srv/arvion").exists() else Path(settings.BASE_DIR)
        usage = shutil.disk_usage(app_dir)
        used_percent = round((usage.used / usage.total) * 100)
        backup_dir = Path(getattr(settings, "CRM_BACKUP_DIR", app_dir / "backups"))
        latest = find_backup_inventory(backup_dir).preferred
        now = timezone.now()
        backup_stale = not latest or datetime_from_timestamp(latest.modified_timestamp) < now - timedelta(hours=settings.OPERATIONS_BACKUP_MAX_AGE_HOURS)
        checks = [
            ("health:disk", used_percent >= settings.OPERATIONS_DISK_ALERT_PERCENT, "فضای دیسک سرور نیازمند رسیدگی است", f"مصرف دیسک: {used_percent}%", "support"),
            ("health:backup", backup_stale, "نسخه پشتیبان تازه پیدا نشد", f"آخرین backup: {latest.name if latest else 'وجود ندارد'}", "support"),
        ]
        created = 0
        for source_key, failed, title, description, category in checks:
            if not failed:
                ManagementNotification.objects.filter(source_key=source_key, status__in=("unread", "read")).update(status="resolved", resolved_at=now)
                continue
            notification, was_created = ManagementNotification.objects.get_or_create(source_key=source_key, defaults={"category": category, "title": title, "description": description, "target_url": "/fa/management/crm/", "role": "", "due_at": now})
            if was_created:
                create_receipts(notification)
                created += 1
        self.stdout.write(self.style.SUCCESS(f"operations health checked; {created} alert(s) created"))


def datetime_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
