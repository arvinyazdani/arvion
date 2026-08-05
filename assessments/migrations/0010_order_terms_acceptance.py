from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("assessments", "0009_unique_pending_order")]

    operations = [
        migrations.AddField(
            model_name="order", name="terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order", name="terms_version",
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
