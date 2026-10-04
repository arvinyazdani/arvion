from django.db import migrations


def add_jewelry_demo(apps, schema_editor):
    DemoTemplate = apps.get_model("projects", "DemoTemplate")
    DemoTemplate.objects.get_or_create(
        slug="sarvin-atelier",
        defaults={
            "category": "jewelry",
            "title_fa": "گالری طلا و جواهر",
            "title_en": "Jewellery atelier",
            "tagline_fa": "هر قطعه، داستانی برای ماندن.",
            "tagline_en": "A keepsake with a story of its own.",
            "fictional_brand_fa": "سروین",
            "fictional_brand_en": "SARVIN ATELIER",
            "style_key": "luxury",
            "default_features": ["payment", "catalog", "booking", "membership"],
            "display_order": 110,
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("projects", "0007_add_jewelry_category")]

    operations = [migrations.RunPython(add_jewelry_demo, migrations.RunPython.noop)]
