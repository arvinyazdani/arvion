from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("contracts", "0004_contractotpchallenge_purpose"), ("crm_orders", "0003_crmspecialistdiscovery")]
    operations = [migrations.AddField(model_name="contractproposal", name="crm_order", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="contract_proposals", to="crm_orders.crmorder"))]
