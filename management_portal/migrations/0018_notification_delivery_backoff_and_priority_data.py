from django.db import migrations, models


def backfill_priorities(apps, schema_editor):
    notification = apps.get_model("management_portal", "ManagementNotification")
    notification.objects.filter(category="payments").update(priority="critical")
    notification.objects.filter(category__in=("contracts", "support")).update(priority="high")


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0017_managementnotification_priority_and_more")]

    operations = [
        migrations.AddField(
            model_name="notificationreceipt", name="push_attempt_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="notificationreceipt", name="push_retry_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="notificationreceipt", name="sms_attempt_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="notificationreceipt", name="sms_retry_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_priorities, migrations.RunPython.noop),
    ]
