"""Bilingual label tables for demo templates and selections.

Shared by the public demo gallery/configurator (`projects.views.projects`)
and the staff management dashboard (`management_portal.views`) so both stay
consistent without either importing the other's view-layer internals.
"""

CATEGORY_LABELS_EN = {
    "ecommerce": "E-commerce", "restaurant": "Restaurant & cafe",
    "portfolio": "Portfolio", "corporate": "Corporate website",
    "clinic": "Clinic", "education": "Education & webinar",
    "jewelry": "Jewellery boutique",
}


CATEGORY_FEATURE_KEYS = {
    "ecommerce": ("payment", "catalog", "membership", "blog", "multilingual"),
    "restaurant": ("booking", "catalog", "payment", "blog"),
    "portfolio": ("blog", "multilingual", "booking"),
    "corporate": ("booking", "blog", "multilingual", "membership"),
    "clinic": ("booking", "payment", "blog", "membership"),
    "education": ("membership", "payment", "blog", "multilingual"),
    "jewelry": ("payment", "catalog", "booking", "membership"),
}

CATEGORY_FEATURE_LABELS = {
    "fa": {
        "ecommerce": {"catalog": "محصول، دسته‌بندی و فیلتر", "membership": "باشگاه مشتریان"},
        "restaurant": {"booking": "رزرو میز", "catalog": "منو و دسته‌بندی غذا"},
        "portfolio": {"blog": "مطالعات موردی", "booking": "فرم همکاری"},
        "corporate": {"booking": "درخواست مشاوره", "membership": "پنل مشتریان"},
        "clinic": {"booking": "نوبت‌دهی", "membership": "پنل مراجعه‌کننده"},
        "education": {"membership": "پنل هنرجو و دوره", "blog": "مقاله و محتوای آموزشی"},
        "jewelry": {"catalog": "کالکشن و جزئیات عیار", "booking": "مشاوره و سفارش سفارشی", "membership": "پیگیری سفارش"},
    },
    "en": {
        "ecommerce": {"catalog": "Products, categories and filters", "membership": "Customer club"},
        "restaurant": {"booking": "Table reservations", "catalog": "Menus and food categories"},
        "portfolio": {"blog": "Case studies", "booking": "Enquiry form"},
        "corporate": {"booking": "Consultation requests", "membership": "Client area"},
        "clinic": {"booking": "Appointment booking", "membership": "Patient portal"},
        "education": {"membership": "Learner and course area", "blog": "Learning articles"},
        "jewelry": {"catalog": "Collections and material details", "booking": "Consultation and custom orders", "membership": "Order progress"},
    },
}


def demo_config_labels(lang, category=None):
    fa = lang == "fa"
    return {
        "themes": [("warm", "گرم و نارنجی"), ("midnight", "تیره و حرفه‌ای"), ("sage", "سبز آرام"), ("plum", "ارغوانی خلاق"), ("gold", "طلایی"), ("custom", "رنگ دلخواه")]
        if fa else [("warm", "Warm orange"), ("midnight", "Professional dark"), ("sage", "Calm sage"), ("plum", "Creative plum"), ("gold", "Gold"), ("custom", "Custom colour")],
        "personalities": [("minimal", "مینیمال"), ("modern", "مدرن"), ("editorial", "محتوامحور"), ("luxury", "لوکس"), ("bold", "پر انرژی"), ("industrial", "صنعتی")]
        if fa else [("minimal", "Minimal"), ("modern", "Modern"), ("editorial", "Editorial"), ("luxury", "Luxury"), ("bold", "Bold"), ("industrial", "Industrial")],
        "features": _category_features(lang, category),
    }


def _category_features(lang, category):
    fa = lang == "fa"
    base = {
        "payment": "پرداخت آنلاین" if fa else "Online payments",
        "booking": "رزرو / نوبت‌دهی" if fa else "Booking",
        "catalog": "کاتالوگ و محصول" if fa else "Catalogue",
        "blog": "مقاله و محتوا" if fa else "Content",
        "membership": "عضویت و پنل مشتری" if fa else "Member area",
        "multilingual": "چندزبانه" if fa else "Multilingual",
    }
    lang_key = "fa" if fa else "en"
    labels = CATEGORY_FEATURE_LABELS.get(lang_key, {}).get(category, {})
    keys = CATEGORY_FEATURE_KEYS.get(category, tuple(base))
    return [(key, labels.get(key, base[key])) for key in keys]
