from django import forms

from core.i18n_numbers import normalize_digits
from .models import CrmOrder


GOALS = [
    ("sales", "مدیریت فروش و فرصت‌ها"), ("service", "خدمات و پشتیبانی مشتری"),
    ("marketing", "بازاریابی و کمپین‌ها"), ("partner", "مدیریت نمایندگان و شرکا"),
    ("operations", "فرآیندهای عملیاتی مرتبط با مشتری"),
]
DEPARTMENTS = [
    ("sales", "فروش"), ("marketing", "بازاریابی"), ("support", "پشتیبانی"),
    ("management", "مدیریت"), ("finance", "مالی"), ("operations", "عملیات"),
]
CAPABILITIES = [
    ("customer_360", "پرونده یکپارچه مشتری"), ("pipeline", "قیف فروش و فرصت‌ها"),
    ("tasks", "وظایف، یادآوری و SLA"), ("tickets", "تیکت و خدمات مشتری"),
    ("automation", "اتوماسیون گردش‌کار"), ("reports", "داشبورد و گزارش مدیریتی"),
    ("campaigns", "کمپین و بخش‌بندی"), ("mobile", "دسترسی موبایل"),
    ("portal", "پرتال مشتری یا نماینده"), ("documents", "پیشنهاد، قرارداد و اسناد"),
]


class CrmOrderForm(forms.ModelForm):
    primary_goals = forms.MultipleChoiceField(choices=GOALS, widget=forms.CheckboxSelectMultiple)
    departments = forms.MultipleChoiceField(choices=DEPARTMENTS, widget=forms.CheckboxSelectMultiple)
    required_capabilities = forms.MultipleChoiceField(choices=CAPABILITIES, widget=forms.CheckboxSelectMultiple)
    privacy_accept = forms.BooleanField(label="حریم خصوصی را خوانده‌ام و با تماس برای تحلیل این سفارش موافقم.")
    company_fax = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = CrmOrder
        exclude = ("tracking_code", "privacy_accepted_at", "status", "internal_notes", "created_at")
        widgets = {
            "current_process": forms.Textarea(attrs={"rows": 4}),
            "main_pain_points": forms.Textarea(attrs={"rows": 4}),
            "success_metrics": forms.Textarea(attrs={"rows": 3}),
            "critical_workflows": forms.Textarea(attrs={"rows": 5}),
            "reports_needed": forms.Textarea(attrs={"rows": 3}),
            "permission_requirements": forms.Textarea(attrs={"rows": 3}),
            "current_tools": forms.Textarea(attrs={"rows": 2}),
            "required_integrations": forms.Textarea(attrs={"rows": 3}),
            "migration_sources": forms.Textarea(attrs={"rows": 3}),
            "security_requirements": forms.Textarea(attrs={"rows": 3}),
            "decision_process": forms.Textarea(attrs={"rows": 3}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "organization_name": "نام سازمان", "industry": "حوزه فعالیت", "organization_size": "تعداد کارکنان سازمان",
            "website": "وب‌سایت", "contact_name": "نام فرد پاسخ‌گو", "job_title": "سمت سازمانی",
            "work_email": "ایمیل کاری", "phone": "شماره تماس", "primary_goals": "هدف‌های اصلی CRM",
            "departments": "واحدهای استفاده‌کننده", "crm_user_count": "تعداد کاربران CRM",
            "current_process": "فرآیند فعلی جذب تا نگهداری مشتری چگونه است؟",
            "main_pain_points": "سه مشکل اصلی فرآیند فعلی چیست؟", "success_metrics": "موفقیت CRM را با چه شاخص‌هایی می‌سنجید؟",
            "required_capabilities": "قابلیت‌های ضروری", "critical_workflows": "گردش‌کارهای حیاتی را مرحله‌به‌مرحله توضیح دهید",
            "reports_needed": "گزارش‌ها و شاخص‌های مدیریتی ضروری", "permission_requirements": "نقش‌ها و محدودیت‌های دسترسی",
            "current_tools": "ابزارهای فعلی", "required_integrations": "سیستم‌های نیازمند اتصال",
            "migration_sources": "منابع داده‌ای که باید منتقل شوند", "approximate_record_count": "تعداد تقریبی رکوردها",
            "hosting_preference": "ترجیح میزبانی", "security_requirements": "الزامات امنیتی، قانونی یا ممیزی",
            "budget_range": "بازه بودجه", "expected_timeline": "زمان مورد انتظار",
            "decision_process": "تصمیم‌گیرندگان و فرآیند تأیید پروژه", "additional_notes": "نکات تکمیلی",
        }
        for name, label in labels.items():
            self.fields[name].label = label
        self.fields["website"].required = False
        self.fields["approximate_record_count"].required = False
        for name in ("current_tools", "required_integrations", "migration_sources", "security_requirements", "additional_notes"):
            self.fields[name].required = False

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
        return cleaned
