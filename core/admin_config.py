"""Persian, task-oriented navigation for Django admin."""
from types import MethodType

from django.contrib import admin


MODEL_NAMES = {
    "User": "کاربران و حساب‌ها", "Group": "نقش‌های دسترسی",
    "Manual payment submission": "واریزهای کارت‌به‌کارت", "Order": "سفارش‌های آزمون",
    "Payment transaction": "تراکنش‌های پرداخت", "Exam entitlement": "دسترسی‌های آزمون",
    "Exam": "آزمون‌ها", "Attempt": "دفعات اجرای آزمون", "Attempt result": "نتایج آزمون",
    "Support ticket": "درخواست‌های پشتیبانی", "Certificate": "گواهی‌ها",
    "Question": "سؤال‌ها", "Skill": "مهارت‌ها", "Exam version": "نسخه‌های آزمون",
    "Exam section": "بخش‌های آزمون", "Integrity event": "رویدادهای نظارتی",
    "Lead": "درخواست‌های همکاری", "Crm order": "سفارش‌های CRM",
    "Service": "خدمات", "Project": "نمونه‌کارها", "Post": "مقاله‌ها",
    "Company profile": "اطلاعات شرکت", "Page": "صفحات ثابت",
    "Traffic day": "آمار روزانه", "Active visitor": "کاربران آنلاین",
    "Daily visitor": "شناسه‌های بازدید روزانه",
}

CATEGORIES = (
    ("کاربران و دسترسی‌ها", {"accounts", "auth"}),
    ("پرداخت، آزمون و پشتیبانی", {"assessments"}),
    ("فروش، سفارش و CRM", {"leads", "crm_orders"}),
    ("محتوا و معرفی خدمات", {"services", "projects", "blog", "core"}),
    ("آمار و پایش", {"traffic"}),
)


def _persian_app_list(site, request, app_label=None):
    app_dict = site._build_app_dict(request, app_label)
    for app in app_dict.values():
        for model in app["models"]:
            model["name"] = MODEL_NAMES.get(model["name"], model["name"])
    if app_label:
        return sorted(app_dict.values(), key=lambda item: item["name"])
    grouped = []
    consumed = set()
    for title, labels in CATEGORIES:
        models = []
        for label in labels:
            if label in app_dict:
                consumed.add(label)
                models.extend(app_dict[label]["models"])
        if models:
            grouped.append({"name": title, "app_label": "group", "app_url": "", "has_module_perms": True,
                            "models": sorted(models, key=lambda item: item["name"])})
    grouped.extend(app for label, app in app_dict.items() if label not in consumed)
    return grouped


admin.site.site_header = "مدیریت رویون"
admin.site.site_title = "پنل مدیریت رویون"
admin.site.index_title = "مدیریت سریع عملیات"
admin.site.get_app_list = MethodType(_persian_app_list, admin.site)
