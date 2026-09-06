from django.db import migrations, models


def migrate_notification_lifecycle(apps, schema_editor):
    Notification = apps.get_model("management_portal", "ManagementNotification")
    Receipt = apps.get_model("management_portal", "NotificationReceipt")

    for notification in Notification.objects.exclude(snoozed_until=None).iterator():
        Receipt.objects.filter(notification_id=notification.pk).update(
            snoozed_until=notification.snoozed_until,
        )

    informational_prefixes = (
        "user:",
        "payment-auto-approved:",
        "contract-acceptance:",
        "assessment-result:",
    )
    informational_ids = []
    for notification in Notification.objects.all().only("pk", "source_key").iterator():
        if notification.source_key.startswith(informational_prefixes):
            informational_ids.append(notification.pk)
    if informational_ids:
        Notification.objects.filter(pk__in=informational_ids).update(
            requires_action=False,
            due_at=None,
        )
    # Older releases created a second SLA notification for work that already
    # had its own due date. Preserve the audit history, but remove those
    # duplicate cards from the active inbox.
    Notification.objects.filter(source_key__startswith="sla:").update(status="resolved")


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0018_notification_delivery_backoff_and_priority_data")]

    operations = [
        migrations.AddField(
            model_name="managementnotification",
            name="requires_action",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name="notificationreceipt",
            name="dismissed_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="notificationreceipt",
            name="snoozed_until",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(migrate_notification_lifecycle, migrations.RunPython.noop),
        migrations.RemoveField(model_name="managementnotification", name="snoozed_until"),
        migrations.AlterField(
            model_name="managementnotification",
            name="category",
            field=models.CharField(
                choices=[("accounts", "حساب‌ها"), ("sales", "فروش و سفارش"), ("payments", "پرداخت"), ("assessments", "آزمون‌ها"), ("support", "پشتیبانی"), ("contracts", "قرارداد")],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
