from django.db import migrations


def deactivate_demo_services(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    pairs = (
        ("آموزش خصوصی Django", "Private Django Training"),
        ("پیاده‌سازی وب‌اپ", "Web App Implementation"),
    )
    for title_fa, title_en in pairs:
        Service.objects.filter(title_fa=title_fa, title_en=title_en).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("services", "0004_service_sales_content")]
    operations = [migrations.RunPython(deactivate_demo_services, migrations.RunPython.noop)]
