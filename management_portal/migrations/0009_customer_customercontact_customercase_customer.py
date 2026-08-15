from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _value(value):
    return (value or "").strip()


def migrate_cases_to_customers(apps, schema_editor):
    Customer = apps.get_model("management_portal", "Customer")
    CustomerContact = apps.get_model("management_portal", "CustomerContact")
    CustomerCase = apps.get_model("management_portal", "CustomerCase")
    User = apps.get_model("accounts", "User")

    for case in CustomerCase.objects.filter(customer__isnull=True).iterator():
        name, phone, email, contact_name = _value(case.customer_name), _value(case.phone), _value(case.email).lower(), _value(case.contact_name)
        customer = Customer.objects.filter(name__iexact=name).filter(phone=phone).filter(email__iexact=email).first()
        if customer is None:
            customer = Customer.objects.create(name=name or contact_name or case.code, kind="company", phone=phone, email=email)
        case.customer_id = customer.pk
        case.save(update_fields=("customer",))
        if not (contact_name or phone or email):
            continue
        user = None
        if email:
            user = User.objects.filter(email__iexact=email, is_staff=False).first()
        if user is None and phone:
            user = User.objects.filter(mobile=phone, is_staff=False).first()
        contact, created = CustomerContact.objects.get_or_create(
            customer=customer, name=contact_name or name or "مخاطب اصلی", phone=phone, email=email,
            defaults={"user": user, "is_primary": not CustomerContact.objects.filter(customer=customer, is_primary=True).exists()},
        )
        if user and contact.user_id is None:
            contact.user_id = user.pk
            contact.save(update_fields=("user",))


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0008_backfill_case_related_documents"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=180)),
                ("kind", models.CharField(choices=[("company", "شرکت"), ("person", "شخص")], db_index=True, default="company", max_length=12)),
                ("phone", models.CharField(blank=True, db_index=True, max_length=24)),
                ("email", models.EmailField(blank=True, db_index=True, max_length=254)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
            ],
            options={"ordering": ("name", "pk")},
        ),
        migrations.CreateModel(
            name="CustomerContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=140)),
                ("role", models.CharField(blank=True, max_length=120)),
                ("phone", models.CharField(blank=True, db_index=True, max_length=24)),
                ("email", models.EmailField(blank=True, db_index=True, max_length=254)),
                ("is_primary", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="management_portal.customer")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="customer_contact_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-is_primary", "name", "pk")},
        ),
        migrations.AddField(model_name="customercase", name="customer", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cases", to="management_portal.customer")),
        migrations.AddConstraint(model_name="customercontact", constraint=models.UniqueConstraint(fields=("customer", "phone", "email", "name"), name="unique_customer_contact_identity")),
        migrations.RunPython(migrate_cases_to_customers, migrations.RunPython.noop),
    ]
