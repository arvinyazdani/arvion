from django.db import migrations, models
import django.db.models.deletion


def link_order_customers(apps, schema_editor):
    Customer = apps.get_model("management_portal", "Customer")
    CustomerContact = apps.get_model("management_portal", "CustomerContact")
    Order = apps.get_model("assessments", "Order")
    for order in Order.objects.filter(customer__isnull=True).select_related("user").iterator():
        customer_id = CustomerContact.objects.filter(user_id=order.user_id).values_list("customer_id", flat=True).first()
        if customer_id is None:
            customer_id = Customer.objects.filter(email__iexact=order.user.email).values_list("pk", flat=True).first()
        if customer_id is None and order.user.mobile:
            customer_id = Customer.objects.filter(phone=order.user.mobile).values_list("pk", flat=True).first()
        if customer_id:
            order.customer_id = customer_id
            order.save(update_fields=("customer",))


class Migration(migrations.Migration):
    dependencies = [("assessments", "0015_manualpaymentsubmission"), ("management_portal", "0009_customer_customercontact_customercase_customer")]
    operations = [
        migrations.AddField(model_name="order", name="customer", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assessment_orders", to="management_portal.customer")),
        migrations.RunPython(link_order_customers, migrations.RunPython.noop),
    ]
