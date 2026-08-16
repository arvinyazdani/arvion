from django.db import migrations


def create_customer_records_for_orders(apps, schema_editor):
    Customer = apps.get_model("management_portal", "Customer")
    CustomerContact = apps.get_model("management_portal", "CustomerContact")
    Order = apps.get_model("assessments", "Order")
    for order in Order.objects.filter(customer__isnull=True).select_related("user").iterator():
        user = order.user
        customer = Customer.objects.filter(email__iexact=user.email).first()
        if customer is None and user.mobile:
            customer = Customer.objects.filter(phone=user.mobile).first()
        if customer is None:
            name = (f"{user.first_name} {user.last_name}").strip() or user.email
            customer = Customer.objects.create(name=name, kind="person", phone=user.mobile or "", email=user.email)
        CustomerContact.objects.get_or_create(
            customer=customer, user_id=user.pk,
            defaults={"name": (f"{user.first_name} {user.last_name}").strip() or user.email, "phone": user.mobile or "", "email": user.email, "is_primary": not CustomerContact.objects.filter(customer=customer, is_primary=True).exists()},
        )
        order.customer_id = customer.pk
        order.save(update_fields=("customer",))


class Migration(migrations.Migration):
    dependencies = [("assessments", "0016_order_customer")]
    operations = [migrations.RunPython(create_customer_records_for_orders, migrations.RunPython.noop)]
