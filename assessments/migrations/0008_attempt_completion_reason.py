from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("assessments", "0007_certificate_holder_name")]

    operations = [
        migrations.AddField(
            model_name="attempt",
            name="completion_reason",
            field=models.CharField(
                blank=True,
                choices=[("manual", "Manual submission"), ("timeout", "Time expired")],
                max_length=10,
            ),
        ),
    ]
