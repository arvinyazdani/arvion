from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("contracts", "0007_contractroomacknowledgement_and_more")]

    operations = [
        migrations.AddField(
            model_name="contractacceptance",
            name="discovery_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="contractacceptance",
            name="evidence_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
