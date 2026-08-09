from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from traffic.models import ActiveVisitor, DailyVisitor


class Command(BaseCommand):
    help = "Delete expired pseudonymous visitor records while retaining aggregate daily totals."

    def handle(self, *args, **options):
        daily, _ = DailyVisitor.objects.filter(date__lt=timezone.localdate() - timedelta(days=30)).delete()
        active, _ = ActiveVisitor.objects.filter(last_seen__lt=timezone.now() - timedelta(hours=24)).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {daily} daily and {active} active visitor records."))
