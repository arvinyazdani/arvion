"""Persian, task-oriented navigation for Django admin."""
from types import MethodType

from django.contrib import admin
from django.apps import apps


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

FIELD_NAMES = {
    "email": "ایمیل", "email_verified": "ایمیل/هویت تأییدشده", "verification_sent_at": "زمان ارسال تأییدیه",
    "verification_email_count": "تعداد ارسال تأییدیه", "preferred_language": "زبان ترجیحی", "slug": "نامک",
    "title_fa": "عنوان فارسی", "title_en": "عنوان انگلیسی", "description_fa": "توضیحات فارسی",
    "description_en": "توضیحات انگلیسی", "language_mode": "زبان آزمون", "question_count": "تعداد سؤال",
    "duration_minutes": "زمان آزمون (دقیقه)", "price_irr": "قیمت (ریال)", "is_active": "فعال",
    "display_order": "ترتیب نمایش", "created_at": "زمان ثبت", "updated_at": "آخرین تغییر",
    "user": "کاربر", "exam": "آزمون", "subtotal_irr": "مبلغ اولیه (ریال)", "discount_irr": "تخفیف (ریال)",
    "discount_percent": "درصد تخفیف", "amount_irr": "مبلغ نهایی (ریال)", "status": "وضعیت",
    "gateway": "روش پرداخت", "terms_version": "نسخه قوانین", "terms_accepted_at": "زمان پذیرش قوانین",
    "paid_at": "زمان پرداخت", "confirmation_email_sent_at": "زمان ارسال تأیید پرداخت", "order": "سفارش",
    "external_id": "شناسه تراکنش", "raw_response": "پاسخ خام درگاه", "verified_at": "زمان تأیید",
    "payer_name": "نام واریزکننده", "reference_number": "شماره پیگیری", "note": "توضیحات مشتری",
    "reviewed_by": "بررسی‌کننده", "reviewed_at": "زمان بررسی", "review_note": "یادداشت بررسی",
    "attempts_remaining": "دفعات باقی‌مانده", "expires_at": "زمان انقضا", "code": "کد", "version": "نسخه",
    "is_published": "منتشرشده", "published_at": "زمان انتشار", "section": "بخش", "skill": "مهارت",
    "prompt_fa": "صورت سؤال فارسی", "prompt_en": "صورت سؤال انگلیسی", "question_type": "نوع سؤال",
    "subskill": "زیرمهارت", "content_group": "گروه محتوایی", "difficulty": "درجه سختی", "weight": "وزن",
    "suggested_seconds": "زمان پیشنهادی (ثانیه)", "audio_path": "فایل صوتی", "transcript": "متن فایل صوتی",
    "max_plays": "حداکثر پخش", "explanation_fa": "توضیح پاسخ فارسی", "explanation_en": "توضیح پاسخ انگلیسی",
    "source_reference": "منبع", "review_notes": "یادداشت بازبینی", "exposure_count": "تعداد نمایش",
    "correct_response_count": "پاسخ صحیح", "last_reviewed_at": "آخرین بازبینی", "attempt": "اجرای آزمون",
    "completion_reason": "علت پایان", "started_at": "زمان شروع", "submitted_at": "زمان ارسال",
    "current_position": "موقعیت فعلی", "integrity_score": "امتیاز سلامت", "event_type": "نوع رویداد",
    "metadata": "اطلاعات فنی", "correct_count": "پاسخ صحیح", "incorrect_count": "پاسخ غلط",
    "unanswered_count": "بدون پاسخ", "percentage": "درصد", "level_code": "کد سطح", "generated_at": "زمان تولید",
    "holder_name": "نام دارنده", "verification_code": "کد اعتبارسنجی", "issued_at": "زمان صدور",
    "is_revoked": "باطل‌شده", "category": "دسته‌بندی", "subject": "موضوع", "message": "پیام",
    "tracking_code": "کد پیگیری", "name": "نام", "business_name": "نام کسب‌وکار", "phone": "تلفن",
    "website": "وب‌سایت", "website_url": "نشانی وب‌سایت", "service": "خدمت", "request_type": "نوع درخواست",
    "budget_range": "بازه بودجه", "timeline": "زمان مورد انتظار", "preferred_contact": "روش تماس",
    "privacy_accepted_at": "زمان پذیرش حریم خصوصی", "is_reviewed": "بررسی‌شده", "organization_name": "نام سازمان",
    "industry": "حوزه فعالیت", "organization_size": "اندازه سازمان", "contact_name": "نام رابط", "job_title": "سمت",
    "work_email": "ایمیل کاری", "primary_goals": "هدف‌های اصلی", "departments": "واحدها", "customer_types": "نوع مشتریان",
    "lead_sources": "منابع جذب", "crm_user_count": "تعداد کاربران CRM", "current_process": "فرآیند فعلی",
    "current_data_sources": "منابع داده فعلی", "main_pain_points": "مشکلات اصلی", "success_metrics": "معیارهای موفقیت",
    "required_capabilities": "قابلیت‌های ضروری", "critical_workflows": "گردش‌کارهای حیاتی", "reports_needed": "گزارش‌های ضروری",
    "permission_requirements": "نیازهای دسترسی", "current_tools": "ابزارهای فعلی", "required_integrations": "اتصال‌های ضروری",
    "migration_sources": "منابع مهاجرت داده", "approximate_record_count": "تعداد تقریبی رکورد", "hosting_preference": "نوع میزبانی",
    "security_requirements": "الزامات امنیتی", "delivery_strategy": "روش اجرا", "requested_services": "خدمات درخواستی",
    "expected_timeline": "زمان مورد انتظار", "decision_process": "فرآیند تصمیم‌گیری", "additional_notes": "توضیحات تکمیلی",
    "internal_notes": "یادداشت داخلی", "date": "تاریخ", "page_views": "نمایش صفحه", "unique_visitors": "بازدیدکننده یکتا",
    "visitor_hash": "شناسه ناشناس", "last_seen": "آخرین فعالیت", "path": "صفحه", "is_authenticated": "واردشده به حساب",
}

MODEL_NAMES_BY_CLASS = {key.lower().replace(" ", ""): value for key, value in MODEL_NAMES.items()}

for app_config in apps.get_app_configs():
    if app_config.label not in {"accounts", "assessments", "core", "blog", "projects", "services", "leads", "crm_orders", "traffic"}:
        continue
    for model in app_config.get_models():
        translated_model = MODEL_NAMES_BY_CLASS.get(model.__name__.lower())
        if translated_model:
            model._meta.verbose_name = translated_model
            model._meta.verbose_name_plural = translated_model
        for field in model._meta.fields:
            if field.name in FIELD_NAMES:
                field.verbose_name = FIELD_NAMES[field.name]

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
