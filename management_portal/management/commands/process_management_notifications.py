from django.core.management.base import BaseCommand
from management_portal.notifications import process_notifications


class Command(BaseCommand):
    help = "Send new management push alerts, urgent SMS, and hourly unseen reminders."

    def handle(self, *args, **options):
        result = process_notifications()
        self.stdout.write(" ".join(f"{key}={value}" for key, value in result.items()))
