from django import forms

from core.i18n_numbers import normalize_digits
from core.form_accessibility import enhance_form_accessibility
from .models import CrmOrder


GOALS = [
    ("customer_records", "ثبت و یکپارچه‌سازی اطلاعات مشتری"), ("followups", "جلوگیری از فراموش‌شدن پیگیری"),
    ("sales", "مدیریت فرآیند فروش"), ("service", "خدمات، پشتیبانی و شکایت"),
    ("correspondence", "مکاتبات و نامه‌های اداری"), ("performance", "ارزیابی عملکرد کارکنان"),
    ("reports", "گزارش مدیریتی"), ("automation", "اتوماسیون فرآیندهای داخلی"),
]
DEPARTMENTS = [
    ("sales", "فروش"), ("marketing", "بازاریابی"), ("support", "پشتیبانی"),
    ("management", "مدیریت"), ("finance", "مالی"), ("operations", "عملیات"),
]
CAPABILITIES = [
    ("customer_360", "پرونده یکپارچه مشتری"), ("pipeline", "قیف فروش و فرصت‌ها"),
    ("tasks", "وظایف، یادآوری و SLA"), ("tickets", "تیکت و خدمات مشتری"),
    ("automation", "اتوماسیون گردش‌کار"), ("reports", "داشبورد و گزارش مدیریتی"),
    ("products", "محصولات و خدمات"), ("quotation", "استعلام، پیشنهاد و پیش‌فاکتور"),
    ("orders", "سفارش و پرداخت"), ("correspondence", "دبیرخانه و مکاتبات"),
    ("documents", "قرارداد، اسناد و بایگانی"), ("portal", "پرتال مشتری یا نماینده"),
]

CURRENT_DATA_SOURCES = [("paper", "کاغذ و فرم دستی"), ("excel", "Excel"), ("business_software", "حسابداری یا نرم‌افزار سازمانی"), ("crm", "CRM یا سیستم اختصاصی"), ("messenger", "پیام‌رسان و اطلاعات کارکنان"), ("none", "روش مشخصی نداریم")]
CUSTOMER_TYPES = [("people", "اشخاص حقیقی"), ("businesses", "شرکت‌ها و سازمان‌ها"), ("agents", "نمایندگان فروش"), ("suppliers", "تأمین‌کنندگان"), ("government", "مشتریان دولتی"), ("international", "مشتریان خارجی")]
LEAD_SOURCES = [("phone", "تماس تلفنی"), ("digital", "وب‌سایت و شبکه‌های اجتماعی"), ("ads", "تبلیغات"), ("referral", "معرفی مشتریان"), ("in_person", "مراجعه، نمایشگاه و رویداد"), ("sales_team", "بازاریاب و فروش")]
NOTIFICATIONS = [("in_app", "داخل سامانه"), ("sms", "پیامک"), ("email", "ایمیل"), ("whatsapp", "واتساپ"), ("push", "Push notification"), ("unsure", "نیازمند بررسی")]
CORRESPONDENCE = [("incoming", "نامه‌های ورودی"), ("outgoing_internal", "نامه خروجی و داخلی"), ("numbering_routing", "شماره‌گذاری، ارجاع و پیگیری"), ("archive", "ضمیمه، بایگانی و جست‌وجو"), ("deadline_approval", "مهلت پاسخ و تأیید مدیر")]
AI_USES = [("none", "فعلاً نیاز نداریم"), ("consult", "نیازمند مشاوره"), ("writing", "نگارش، اصلاح و پیشنهاد پاسخ"), ("summary", "خلاصه‌سازی و استخراج از سند"), ("search", "جست‌وجوی هوشمند"), ("analytics", "تحلیل فروش و پیشنهاد پیگیری")]
INTEGRATIONS = [("website", "وب‌سایت"), ("accounting", "حسابداری، انبار یا ERP"), ("messaging", "SMS، ایمیل یا واتساپ"), ("telephony", "تلفن سازمانی"), ("payment", "درگاه پرداخت"), ("workforce", "حضور و غیاب یا منابع انسانی"), ("ai", "API هوش مصنوعی"), ("none", "اتصال دیگری نداریم")]
MIGRATIONS = [("none", "داده‌ای منتقل نمی‌شود"), ("excel", "Excel"), ("legacy", "نرم‌افزار قبلی"), ("documents", "فایل و سند"), ("multiple", "چند منبع")]
SERVICES = [("process", "تحلیل فرآیندها"), ("design_delivery", "طراحی، پیاده‌سازی و استقرار"), ("data", "پاک‌سازی و ورود داده اولیه"), ("training_docs", "آموزش و مستندات"), ("support_growth", "پشتیبانی و توسعه بعدی"), ("infrastructure", "سرور، دامنه و backup")]


class CrmOrderForm(forms.ModelForm):
    primary_goals = forms.MultipleChoiceField(choices=GOALS, widget=forms.CheckboxSelectMultiple)
    departments = forms.MultipleChoiceField(choices=DEPARTMENTS, widget=forms.CheckboxSelectMultiple)
    required_capabilities = forms.MultipleChoiceField(choices=CAPABILITIES, widget=forms.CheckboxSelectMultiple)
    current_data_sources = forms.MultipleChoiceField(choices=CURRENT_DATA_SOURCES, widget=forms.CheckboxSelectMultiple)
    customer_types = forms.MultipleChoiceField(choices=CUSTOMER_TYPES, widget=forms.CheckboxSelectMultiple)
    lead_sources = forms.MultipleChoiceField(choices=LEAD_SOURCES, widget=forms.CheckboxSelectMultiple, required=False)
    notification_channels = forms.MultipleChoiceField(choices=NOTIFICATIONS, widget=forms.CheckboxSelectMultiple, required=False)
    correspondence_features = forms.MultipleChoiceField(choices=CORRESPONDENCE, widget=forms.CheckboxSelectMultiple, required=False)
    ai_use_cases = forms.MultipleChoiceField(choices=AI_USES, widget=forms.CheckboxSelectMultiple, required=False)
    integration_types = forms.MultipleChoiceField(choices=INTEGRATIONS, widget=forms.CheckboxSelectMultiple, required=False)
    migration_types = forms.MultipleChoiceField(choices=MIGRATIONS, widget=forms.CheckboxSelectMultiple)
    requested_services = forms.MultipleChoiceField(choices=SERVICES, widget=forms.CheckboxSelectMultiple)
    assignment_model = forms.ChoiceField(choices=[("yes", "بله، مالک مشخص"), ("conditional", "در بعضی موارد"), ("no", "خیر"), ("unsure", "هنوز مشخص نیست")])
    mobile_requirement = forms.ChoiceField(choices=[("responsive", "وب واکنش‌گرا کافی است"), ("android", "اپ Android"), ("ios", "اپ iOS"), ("both", "Android و iOS"), ("consult", "نیازمند مشاوره")])
    audit_requirement = forms.ChoiceField(choices=[("all", "ثبت همه تغییرات"), ("important", "فقط عملیات مهم"), ("none", "لازم نیست"), ("unsure", "هنوز مشخص نیست")])
    delivery_strategy = forms.ChoiceField(choices=[("mvp", "نسخه اولیه ضروری"), ("full", "اجرای کامل"), ("phased", "اجرای مرحله‌ای"), ("consult", "نیازمند پیشنهاد مجری")])
    privacy_accept = forms.BooleanField(label="حریم خصوصی را خوانده‌ام و با تماس برای تحلیل این سفارش موافقم.")
    company_fax = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = CrmOrder
        exclude = (
            "tracking_code", "privacy_accepted_at", "status", "internal_notes", "created_at",
            "customer_data_fields", "reminder_types", "reporting_priorities", "system_roles", "devices",
        )
        widgets = {
            "current_process": forms.Textarea(attrs={"rows": 4, "minlength": 20}),
            "main_pain_points": forms.Textarea(attrs={"rows": 4, "minlength": 20}),
            "success_metrics": forms.Textarea(attrs={"rows": 3}),
            "critical_workflows": forms.Textarea(attrs={"rows": 5, "minlength": 20}),
            "reports_needed": forms.Textarea(attrs={"rows": 3}),
            "permission_requirements": forms.Textarea(attrs={"rows": 3}),
            "current_tools": forms.Textarea(attrs={"rows": 2}),
            "required_integrations": forms.Textarea(attrs={"rows": 3}),
            "migration_sources": forms.Textarea(attrs={"rows": 3}),
            "security_requirements": forms.Textarea(attrs={"rows": 3}),
            "decision_process": forms.Textarea(attrs={"rows": 3, "minlength": 20}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "organization_name": "نام سازمان", "industry": "حوزه فعالیت", "organization_size": "تعداد کارکنان سازمان",
            "website": "وب‌سایت", "contact_name": "نام فرد پاسخ‌گو", "job_title": "سمت سازمانی",
            "work_email": "ایمیل کاری", "phone": "شماره تماس", "primary_goals": "هدف‌های اصلی CRM",
            "departments": "واحدهای استفاده‌کننده", "crm_user_count": "تعداد کاربران CRM",
            "customer_types": "گروه‌های مشتری", "lead_sources": "کانال‌های جذب مشتری", "current_data_sources": "اطلاعات فعلی کجا نگهداری می‌شود؟",
            "current_process": "فرآیند فعلی جذب تا نگهداری مشتری چگونه است؟",
            "main_pain_points": "سه مشکل اصلی فرآیند فعلی چیست؟", "success_metrics": "موفقیت CRM را با چه شاخص‌هایی می‌سنجید؟",
            "required_capabilities": "قابلیت‌های ضروری", "critical_workflows": "گردش‌کارهای حیاتی را مرحله‌به‌مرحله توضیح دهید",
            "customer_data_fields": "داده‌های ضروری پرونده مشتری", "assignment_model": "آیا هر مشتری مالک یا واحد مشخص دارد؟",
            "reminder_types": "موارد نیازمند یادآوری", "notification_channels": "کانال اعلان ترجیحی",
            "correspondence_features": "دامنه دبیرخانه و مکاتبات", "ai_use_cases": "کاربردهای احتمالی هوش مصنوعی",
            "reporting_priorities": "گزارش‌های اولویت‌دار", "system_roles": "نقش‌های اصلی سامانه",
            "reports_needed": "گزارش‌ها و شاخص‌های مدیریتی ضروری", "permission_requirements": "نقش‌ها و محدودیت‌های دسترسی",
            "current_tools": "ابزارهای فعلی", "required_integrations": "سیستم‌های نیازمند اتصال",
            "devices": "دستگاه‌های مورد استفاده", "mobile_requirement": "نیاز به اپ مستقل",
            "integration_types": "اتصال‌های موردنیاز", "migration_types": "نوع مهاجرت داده",
            "migration_sources": "منابع داده‌ای که باید منتقل شوند", "approximate_record_count": "تعداد تقریبی رکوردها",
            "hosting_preference": "نحوه دسترسی به سامانه", "audit_requirement": "ثبت سابقه فعالیت کاربران", "security_requirements": "الزامات امنیتی یا قانونی دیگر",
            "delivery_strategy": "اولویت روش اجرا", "requested_services": "خدمات موردنیاز از مجری",
            "budget_range": "بازه بودجه", "expected_timeline": "زمان مورد انتظار",
            "decision_process": "تصمیم‌گیرندگان و فرآیند تأیید پروژه", "additional_notes": "نکات تکمیلی",
        }
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label
        self.fields["website"].required = False
        self.fields["approximate_record_count"].required = False
        for name in ("current_tools", "required_integrations", "migration_sources", "security_requirements", "additional_notes", "reports_needed", "permission_requirements"):
            self.fields[name].required = False

        self.fields["current_tools"].help_text = "نام ابزار یا سیستم اختصاصی را فقط اگر در گزینه‌ها نبود بنویسید."
        self.fields["required_integrations"].help_text = "نام محصول، نسخه یا API مشخص را در صورت اطلاع بنویسید."
        self.fields["migration_sources"].help_text = "نام فایل یا نرم‌افزار و وضعیت کیفیت داده را بنویسید."
        self.fields["ai_use_cases"].help_text = "انتخاب AI به معنی پیشنهاد قطعی آن نیست؛ هزینه، محرمانگی و دقت در جلسه بررسی می‌شود."
        for name in ("current_process", "main_pain_points", "critical_workflows", "decision_process"):
            self.fields[name].help_text = "حداقل ۲۰ کاراکتر؛ یک توضیح کوتاه و واقعی کافی است."
        self.fields["phone"].widget.attrs["inputmode"] = "tel"
        enhance_form_accessibility(self, autocomplete={
            "organization_name": "organization", "website": "url", "contact_name": "name",
            "job_title": "organization-title", "work_email": "email", "phone": "tel",
        })

    def clean_company_fax(self):
        if self.cleaned_data.get("company_fax"):
            raise forms.ValidationError("ارسال نامعتبر است.")
        return ""

    def clean_phone(self):
        phone = normalize_digits(self.cleaned_data["phone"]).strip()
        if len(phone) < 8:
            raise forms.ValidationError("شماره تماس کامل وارد کنید.")
        return phone

    def clean_approximate_record_count(self):
        value = self.cleaned_data.get("approximate_record_count")
        if value is not None and value > 100_000_000:
            raise forms.ValidationError("برای حجم بالاتر، مقدار تقریبی را در توضیحات مهاجرت بنویسید.")
        return value

    def clean(self):
        cleaned = super().clean()
        for field in ("current_process", "main_pain_points", "critical_workflows", "decision_process"):
            value = (cleaned.get(field) or "").strip()
            if value and len(value) < 20:
                self.add_error(field, "لطفاً حداقل ۲۰ کاراکتر توضیح دهید.")
        migration_types = set(cleaned.get("migration_types") or ())
        if "none" in migration_types and len(migration_types) > 1:
            self.add_error("migration_types", "«داده‌ای منتقل نمی‌شود» را همراه منبع دیگر انتخاب نکنید.")
        integrations = set(cleaned.get("integration_types") or ())
        if "none" in integrations and len(integrations) > 1:
            self.add_error("integration_types", "«اتصال دیگری نداریم» را همراه اتصال دیگر انتخاب نکنید.")
        ai_uses = set(cleaned.get("ai_use_cases") or ())
        if "none" in ai_uses and len(ai_uses) > 1:
            self.add_error("ai_use_cases", "«فعلاً نیاز نداریم» را همراه کاربرد دیگر انتخاب نکنید.")
        return cleaned
