from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("contracts", "0005_contractproposal_crm_order")]
    operations = [
        migrations.AddField(model_name="contractproposal", name="general_terms", field=models.TextField(blank=True)),
        migrations.AddField(model_name="contractproposal", name="private_terms", field=models.TextField(blank=True)),
        migrations.AddField(model_name="contractproposal", name="room_progress", field=models.JSONField(blank=True, default=dict)),
    ]
