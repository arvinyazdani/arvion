from django.db import migrations, models
import django.db.models.deletion


def link_contract_customers(apps, schema_editor):
    Customer = apps.get_model("management_portal", "Customer")
    ContractProposal = apps.get_model("contracts", "ContractProposal")
    for contract in ContractProposal.objects.filter(customer__isnull=True).iterator():
        customer = Customer.objects.filter(phone=contract.customer_phone).first() if contract.customer_phone else None
        if customer is None and contract.customer_email:
            customer = Customer.objects.filter(email__iexact=contract.customer_email).first()
        if customer is None:
            customer = Customer.objects.filter(name__iexact=contract.customer_name).first()
        if customer:
            contract.customer_id = customer.pk
            contract.save(update_fields=("customer",))


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0009_customer_customercontact_customercase_customer"), ("contracts", "0002_contractotpchallenge_contractacceptance")]
    operations = [
        migrations.AddField(model_name="contractproposal", name="customer", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="contracts", to="management_portal.customer")),
        migrations.RunPython(link_contract_customers, migrations.RunPython.noop),
    ]
