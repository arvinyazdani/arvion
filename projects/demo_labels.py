"""Bilingual label tables for demo templates and selections.

Shared by the public demo gallery/configurator (`projects.views.projects`)
and the staff management dashboard (`management_portal.views`) so both stay
consistent without either importing the other's view-layer internals.
"""

CATEGORY_LABELS_EN = {
    "ecommerce": "E-commerce", "restaurant": "Restaurant & cafe",
    "portfolio": "Portfolio", "corporate": "Corporate website",
    "clinic": "Clinic", "education": "Education & webinar",
}


def demo_config_labels(lang):
    fa = lang == "fa"
    return {
        "themes": [("warm", "گرم و نارنجی"), ("midnight", "تیره و حرفه‌ای"), ("sage", "سبز آرام"), ("plum", "ارغوانی خلاق"), ("custom", "رنگ دلخواه")]
        if fa else [("warm", "Warm orange"), ("midnight", "Professional dark"), ("sage", "Calm sage"), ("plum", "Creative plum"), ("custom", "Custom colour")],
        "personalities": [("minimal", "مینیمال"), ("editorial", "محتوامحور"), ("luxury", "لوکس"), ("bold", "پر انرژی")]
        if fa else [("minimal", "Minimal"), ("editorial", "Editorial"), ("luxury", "Luxury"), ("bold", "Bold")],
        "features": [("payment", "پرداخت آنلاین"), ("booking", "رزرو / نوبت‌دهی"), ("catalog", "کاتالوگ و محصول"), ("blog", "مقاله و محتوا"), ("membership", "عضویت و پنل مشتری"), ("multilingual", "چندزبانه")]
        if fa else [("payment", "Online payments"), ("booking", "Booking"), ("catalog", "Catalogue"), ("blog", "Content"), ("membership", "Member area"), ("multilingual", "Multilingual")],
    }
