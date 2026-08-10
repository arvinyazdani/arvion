from django.db import migrations, models


def update_company_domain(apps, schema_editor):
    CompanyProfile = apps.get_model("core", "CompanyProfile")
    CompanyProfile.objects.filter(domain="rvin-tech.com").update(domain="rvionai.com")


def restore_company_domain(apps, schema_editor):
    CompanyProfile = apps.get_model("core", "CompanyProfile")
    CompanyProfile.objects.filter(domain="rvionai.com").update(domain="rvin-tech.com")


class Migration(migrations.Migration):
    dependencies = [("core", "0003_companyprofile")]

    operations = [
        migrations.AlterField(
            model_name="companyprofile",
            name="domain",
            field=models.CharField(default="rvionai.com", max_length=120),
        ),
        migrations.RunPython(update_company_domain, restore_company_domain),
    ]
