from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("assessments", "0011_order_confirmation_email_sent_at")]

    operations = [
        migrations.AddField(
            model_name="attemptresult",
            name="report_email_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
