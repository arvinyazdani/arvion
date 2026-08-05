from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("assessments", "0012_attemptresult_report_email_sent_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("payment", "Payment"), ("result_review", "Result review"), ("certificate", "Certificate"), ("technical", "Technical"), ("other", "Other")], max_length=20)),
                ("subject", models.CharField(max_length=180)),
                ("message", models.TextField()),
                ("status", models.CharField(choices=[("open", "Open"), ("in_review", "In review"), ("resolved", "Resolved"), ("closed", "Closed")], db_index=True, default="open", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="support_tickets", to="assessments.order")),
                ("result", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="support_tickets", to="assessments.attemptresult")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assessment_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
