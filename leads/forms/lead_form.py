from django import forms

from core.form_accessibility import enhance_form_accessibility
from core.i18n_numbers import normalize_digits
from leads.models import Lead
from services.models import Service


class LeadForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    privacy_accept = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        lang = kwargs.pop("lang", "fa")
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        self.fields["service"].required = False
        self.fields["service"].label_from_instance = lambda service: service.title_fa if lang == "fa" else service.title_en
        if lang == "fa":
            labels = {
                "request_type": "چه کمکی نیاز دارید؟", "service": "خدمت موردنظر", "business_name": "نام کسب‌وکار یا شرکت",
                "website_url": "وب‌سایت فعلی", "budget_range": "بودجه تقریبی", "timeline": "زمان مورد انتظار",
                "message": "مسئله، هدف و امکانات موردنیاز", "name": "نام و نام خانوادگی", "phone": "شماره تماس",
                "email_or_telegram": "ایمیل یا شناسه تلگرام", "preferred_contact": "روش ارتباط ترجیحی",
                "privacy_accept": "حریم خصوصی را خوانده‌ام و با تماس شرکت برای پیگیری این درخواست موافقم.",
            }
            choices = {
                "request_type": [("consultation", "مشاوره اولیه"), ("website", "وب‌سایت شرکتی"), ("webapp", "وب‌اپلیکیشن اختصاصی"), ("ecommerce", "فروشگاه و تجارت آنلاین"), ("support", "پشتیبانی و بهینه‌سازی"), ("training", "آموزش"), ("other", "سایر")],
                "budget_range": [("unsure", "هنوز مطمئن نیستم"), ("under_50", "کمتر از ۵۰ میلیون تومان"), ("50_150", "۵۰ تا ۱۵۰ میلیون تومان"), ("150_500", "۱۵۰ تا ۵۰۰ میلیون تومان"), ("over_500", "بیش از ۵۰۰ میلیون تومان")],
                "timeline": [("flexible", "زمان‌بندی منعطف"), ("one_month", "کمتر از یک ماه"), ("one_three", "یک تا سه ماه"), ("over_three", "بیش از سه ماه")],
                "preferred_contact": [("phone", "تماس تلفنی"), ("email", "ایمیل"), ("telegram", "تلگرام")],
            }
            placeholders = {"name": "مثلاً علی احمدی", "business_name": "اختیاری", "website_url": "https://example.com", "phone": "مثلاً ۰۹۱۲۱۲۳۴۵۶۷", "email_or_telegram": "name@example.com یا @username", "message": "کسب‌وکار، مسئله اصلی و نتیجه‌ای که انتظار دارید را توضیح دهید…"}
        else:
            labels = {
                "request_type": "What do you need?", "service": "Preferred service", "business_name": "Business or company name",
                "website_url": "Current website", "budget_range": "Estimated budget", "timeline": "Expected timeline",
                "message": "Problem, goal and required features", "name": "Full name", "phone": "Phone number",
                "email_or_telegram": "Email or Telegram", "preferred_contact": "Preferred contact method",
                "privacy_accept": "I have read the privacy policy and agree to be contacted about this enquiry.",
            }
            choices = {}
            placeholders = {"name": "e.g. Alex Morgan", "business_name": "Optional", "website_url": "https://example.com", "phone": "+1…", "email_or_telegram": "name@example.com or @username", "message": "Describe your business, the main problem and the result you expect…"}
        for name, label in labels.items():
            self.fields[name].label = label
        for name, options in choices.items():
            self.fields[name].choices = options
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs["placeholder"] = placeholder
        enhance_form_accessibility(self, autocomplete={
            "business_name": "organization", "website_url": "url", "name": "name",
            "phone": "tel", "email_or_telegram": "email",
        })

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Invalid submission.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 20:
            raise forms.ValidationError("توضیحات باید حداقل ۲۰ کاراکتر باشد." if self.lang == "fa" else "Please provide at least 20 characters.")
        return message

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        return normalize_digits(phone).strip() if phone else phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("preferred_contact") == "phone" and not cleaned.get("phone"):
            self.add_error("phone", "برای تماس تلفنی، شماره تماس لازم است." if self.lang == "fa" else "A phone number is required for phone contact.")
        return cleaned

    class Meta:
        model = Lead
        fields = [
            "request_type", "service", "business_name", "website_url", "budget_range", "timeline", "message",
            "name", "phone", "email_or_telegram", "preferred_contact", "privacy_accept", "website",
        ]
        widgets = {
            "request_type": forms.Select(), "service": forms.Select(), "budget_range": forms.Select(),
            "timeline": forms.Select(), "preferred_contact": forms.Select(), "message": forms.Textarea(attrs={"rows": 5}),
        }
