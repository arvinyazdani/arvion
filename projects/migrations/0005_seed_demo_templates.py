from django.db import migrations


DEMOS = (
    ("nava-market", "ecommerce", "فروشگاه مینیمال", "Minimal storefront", "فروش آرام و متمرکز روی محصول.", "A calm product-first storefront.", "بازار ناوا", "NAVA MARKET", "minimal", ["payment", "catalog"], 10),
    ("orbit-shop", "ecommerce", "فروشگاه پرانرژی", "Bold commerce", "کاتالوگ سریع برای محصول‌های شاخص.", "A fast catalogue for standout products.", "اوربیت شاپ", "ORBIT SHOP", "bold", ["payment", "catalog", "membership"], 20),
    ("saffron-table", "restaurant", "منوی رستوران", "Restaurant menu", "منوی دیجیتال با حس گرم و اشتهابرانگیز.", "A warm, appetite-led digital menu.", "سفره زعفران", "SAFFRON TABLE", "editorial", ["catalog", "booking"], 30),
    ("mora-cafe", "restaurant", "کافه و رزرو", "Cafe and reservations", "یک تجربه صمیمی برای منو، رویداد و رزرو.", "A friendly home for menus, events and bookings.", "کافه مورا", "MORA CAFE", "minimal", ["booking", "blog"], 40),
    ("linea-studio", "portfolio", "استودیوی خلاق", "Creative studio", "نمونه‌کارهایی که داستان هر پروژه را تعریف می‌کنند.", "Work that tells the story behind every project.", "استودیو لینیا", "LINEA STUDIO", "editorial", ["blog", "multilingual"], 50),
    ("atlas-profile", "portfolio", "پورتفولیو شخصی", "Personal portfolio", "معرفی شفاف مهارت، تجربه و راه تماس.", "A clear home for expertise, work and contact.", "اطلس دیزاین", "ATLAS DESIGN", "luxury", ["blog", "multilingual"], 60),
    ("parsa-advisory", "corporate", "شرکت خدمات حرفه‌ای", "Professional services", "اعتمادسازی، خدمات و مسیر ساده تماس.", "Trust, services and a direct contact path.", "مشاوران پارسا", "PARSA ADVISORY", "minimal", ["blog", "multilingual"], 70),
    ("northline-group", "corporate", "برند شرکتی", "Corporate brand", "هویت جسور برای معرفی تیم و راهکارها.", "A bold identity for teams and solutions.", "گروه نورث‌لاین", "NORTHLINE GROUP", "bold", ["blog", "membership"], 80),
    ("roshna-clinic", "clinic", "کلینیک و نوبت‌دهی", "Clinic and booking", "نوبت‌دهی، معرفی پزشک و محتوای آگاه‌کننده.", "Bookings, practitioners and helpful content.", "کلینیک روشنا", "ROSHNA CLINIC", "sage", ["booking", "payment", "blog"], 90),
    ("ariana-academy", "education", "آکادمی و وبینار", "Academy and webinars", "دوره، مسیر یادگیری و تجربه عضویت.", "Courses, learning journeys and membership.", "آکادمی آریانا", "ARIANA ACADEMY", "plum", ["membership", "payment", "blog"], 100),
)


def seed_demos(apps, schema_editor):
    DemoTemplate = apps.get_model("projects", "DemoTemplate")
    for slug, category, title_fa, title_en, tagline_fa, tagline_en, brand_fa, brand_en, style_key, features, order in DEMOS:
        DemoTemplate.objects.update_or_create(
            slug=slug,
            defaults={
                "category": category, "title_fa": title_fa, "title_en": title_en,
                "tagline_fa": tagline_fa, "tagline_en": tagline_en,
                "fictional_brand_fa": brand_fa, "fictional_brand_en": brand_en,
                "style_key": style_key, "default_features": features,
                "display_order": order, "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("projects", "0004_demotemplate_demoselection")]
    operations = [migrations.RunPython(seed_demos, migrations.RunPython.noop)]
