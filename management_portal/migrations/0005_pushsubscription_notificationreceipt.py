from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def backfill_seen_receipts(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Notification = apps.get_model("management_portal", "ManagementNotification")
    Receipt = apps.get_model("management_portal", "NotificationReceipt")
    now = timezone.now()
    rows = []
    for item in Notification.objects.all().iterator():
        users = User.objects.filter(is_staff=True, is_active=True)
        users = users.filter(models.Q(groups__name=f"rvion_{item.role}") | models.Q(is_superuser=True)) if item.role else users.filter(is_superuser=True)
        for user in users.distinct():
            rows.append(Receipt(user_id=user.pk, notification_id=item.pk, seen_at=now, push_sent_at=now))
    Receipt.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0004_operationalaudit")]
    operations = [
        migrations.CreateModel(name="PushSubscription", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("endpoint", models.URLField(max_length=1000, unique=True)), ("p256dh", models.CharField(max_length=255)), ("auth", models.CharField(max_length=255)), ("user_agent", models.CharField(blank=True, max_length=240)), ("is_active", models.BooleanField(db_index=True, default=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_subscriptions", to=settings.AUTH_USER_MODEL))]),
        migrations.CreateModel(name="NotificationReceipt", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("seen_at", models.DateTimeField(blank=True, db_index=True, null=True)), ("push_sent_at", models.DateTimeField(blank=True, null=True)), ("sms_sent_at", models.DateTimeField(blank=True, null=True)), ("last_reminded_at", models.DateTimeField(blank=True, null=True)), ("last_error", models.CharField(blank=True, max_length=240)), ("notification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to="management_portal.managementnotification")), ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_receipts", to=settings.AUTH_USER_MODEL))], options={"constraints": [models.UniqueConstraint(fields=("user", "notification"), name="unique_user_notification_receipt")]}),
        migrations.RunPython(backfill_seen_receipts, migrations.RunPython.noop),
    ]
