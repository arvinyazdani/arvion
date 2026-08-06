from django.db import migrations, models


def create_company_profile(apps, schema_editor):
    CompanyProfile = apps.get_model("core", "CompanyProfile")
    CompanyProfile.objects.create(
        legal_name_fa="آروین توسعه تجارت هوشمند",
        legal_name_en="Arvin Intelligent Trade Development",
        company_type_fa="با مسئولیت محدود",
        brand_name="Rvion",
        registration_number="675342",
        national_id="14015444540",
        established_date_fa="1405/04/24",
        chief_executive_fa="آروین یزدانی",
        chief_executive_en="Arvin Yazdani",
        phone="09333021100",
        postal_code="1683445995",
        address_fa="تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        address_en="Unit 1, First Floor, No. 1, Nilforoushan St., North Narmak, Tehran, Iran",
        domain="rvin-tech.com",
        support_hours_fa="روزهای کاری، ساعت ۸ تا ۱۸",
        support_hours_en="Business days, 08:00–18:00 Tehran time",
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0002_page_body_en_page_body_fa_page_title_en_and_more")]
    operations = [
        migrations.CreateModel(
            name="CompanyProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("legal_name_fa", models.CharField(max_length=180)),
                ("legal_name_en", models.CharField(max_length=180)),
                ("company_type_fa", models.CharField(default="با مسئولیت محدود", max_length=80)),
                ("brand_name", models.CharField(default="Rvion", max_length=80)),
                ("registration_number", models.CharField(max_length=30)),
                ("national_id", models.CharField(max_length=30)),
                ("established_date_fa", models.CharField(max_length=20)),
                ("chief_executive_fa", models.CharField(max_length=120)),
                ("chief_executive_en", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("postal_code", models.CharField(max_length=20)),
                ("address_fa", models.TextField()),
                ("address_en", models.TextField()),
                ("domain", models.CharField(default="rvin-tech.com", max_length=120)),
                ("support_hours_fa", models.CharField(max_length=180)),
                ("support_hours_en", models.CharField(max_length=180)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Company profile", "verbose_name_plural": "Company profile"},
        ),
        migrations.RunPython(create_company_profile, migrations.RunPython.noop),
    ]
