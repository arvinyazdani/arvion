from django import forms

from core.i18n_numbers import normalize_digits
from .models import ClinicOrder


GOALS = [("appointments", "نوبت‌دهی و کاهش تماس تلفنی"), ("payments", "پرداخت آنلاین و قطعی‌شدن نوبت"), ("brand", "معرفی پزشکان و اعتمادسازی"), ("education", "آموزش بیمار با مقاله، صدا و ویدیو"), ("webinars", "برگزاری و فروش وبینار"), ("operations", "کاهش کار دستی پذیرش"), ("growth", "جذب و بازگشت مراجعه‌کننده"), ("reports", "گزارش مدیریتی")]
AUDIENCES = [("patients", "مراجعان و بیماران"), ("families", "خانواده یا همراه بیمار"), ("professionals", "پزشکان و متخصصان"), ("organizations", "سازمان‌ها و شرکت‌ها"), ("international", "مراجعان خارج از ایران")]
CURRENT_CHANNELS = [("phone", "تلفن و پذیرش"), ("messenger", "واتساپ یا پیام‌رسان"), ("social", "شبکه اجتماعی"), ("website", "وب‌سایت فعلی"), ("software", "نرم‌افزار کلینیک"), ("in_person", "مراجعه حضوری")]
VISIT_MODES = [("in_person", "حضوری"), ("video", "مشاوره ویدیویی"), ("phone", "مشاوره تلفنی"), ("home", "ویزیت در منزل"), ("group", "جلسه یا کلاس گروهی")]
REMINDERS = [("sms", "پیامک"), ("email", "ایمیل"), ("whatsapp", "واتساپ"), ("push", "اعلان وب‌اپ"), ("none", "فعلاً بدون اعلان")]
PRACTITIONER_FEATURES = [("profile", "پروفایل، تخصص و سوابق"), ("schedule", "تقویم کاری مستقل"), ("services", "خدمت، مدت و قیمت اختصاصی"), ("leave", "مرخصی و زمان مسدود"), ("secretary", "منشی یا اپراتور اختصاصی"), ("reports", "گزارش نوبت و درآمد")]
PATIENT_FEATURES = [("booking", "رزرو، جابه‌جایی و لغو نوبت"), ("payments", "پرداخت‌ها و رسیدها"), ("history", "تاریخچه نوبت‌ها"), ("forms", "فرم‌های پیش از مراجعه"), ("content", "محتوای خریداری‌شده یا اختصاصی"), ("webinars", "وبینارها و فایل ضبط‌شده"), ("documents", "دریافت فایل یا نسخه غیرتشخیصی")]
PAYMENTS = [("online", "درگاه آنلاین"), ("card", "کارت‌به‌کارت با تأیید مدیر"), ("onsite", "پرداخت در محل"), ("wallet", "کیف پول یا اعتبار"), ("installment", "پرداخت مرحله‌ای"), ("free", "خدمت یا محتوای رایگان")]
FINANCIAL_DOCS = [("receipt", "رسید پرداخت"), ("invoice", "فاکتور"), ("discount", "کد تخفیف"), ("refund", "ثبت استرداد"), ("settlement", "تسویه پزشک یا مدرس"), ("reports", "گزارش مالی")]
CONTENT_TYPES = [("articles", "مقاله"), ("audio", "فایل و دوره صوتی"), ("video", "ویدیو و دوره آموزشی"), ("download", "فایل قابل دانلود"), ("podcast", "پادکست"), ("faq", "پرسش‌های متداول"), ("newsletter", "خبرنامه")]
WEBINARS = [("landing", "صفحه معرفی و مدرس"), ("capacity", "ظرفیت و فهرست انتظار"), ("payment", "ثبت‌نام و پرداخت"), ("reminder", "یادآوری خودکار"), ("live", "پخش زنده داخل سایت"), ("external", "اتصال به سرویس وبینار"), ("recording", "فروش یا نمایش فایل ضبط‌شده"), ("attendance", "حضور و گواهی")]
ROLES = [("owner", "مدیر کلینیک"), ("reception", "پذیرش و منشی"), ("doctor", "پزشک یا درمانگر"), ("content", "مدیر محتوا"), ("finance", "مالی"), ("webinar", "مدیر وبینار"), ("patient", "مراجع")]
INTEGRATIONS = [("sms", "سامانه پیامک"), ("payment", "درگاه پرداخت"), ("webinar", "سرویس وبینار یا ویدیوکنفرانس"), ("video", "میزبانی ویدیو"), ("clinic_software", "نرم‌افزار کلینیک"), ("accounting", "حسابداری"), ("calendar", "تقویم"), ("analytics", "آمار و تبلیغات"), ("none", "فعلاً اتصال دیگری نداریم")]
SERVICES = [("discovery", "تحلیل فرآیند و تجربه کاربر"), ("design", "طراحی UI/UX"), ("development", "توسعه کامل Django"), ("content", "ورود محتوای اولیه"), ("migration", "انتقال داده"), ("infrastructure", "سرور، دامنه، پشتیبان‌گیری"), ("training", "آموزش مدیران و مستندات"), ("support", "پشتیبانی و توسعه بعدی")]


class ClinicOrderForm(forms.ModelForm):
    primary_goals = forms.MultipleChoiceField(choices=GOALS, widget=forms.CheckboxSelectMultiple)
    target_audiences = forms.MultipleChoiceField(choices=AUDIENCES, widget=forms.CheckboxSelectMultiple)
    current_channels = forms.MultipleChoiceField(choices=CURRENT_CHANNELS, widget=forms.CheckboxSelectMultiple)
    visit_modes = forms.MultipleChoiceField(choices=VISIT_MODES, widget=forms.CheckboxSelectMultiple)
    reminder_channels = forms.MultipleChoiceField(choices=REMINDERS, widget=forms.CheckboxSelectMultiple)
    practitioner_features = forms.MultipleChoiceField(choices=PRACTITIONER_FEATURES, widget=forms.CheckboxSelectMultiple)
    patient_account_features = forms.MultipleChoiceField(choices=PATIENT_FEATURES, widget=forms.CheckboxSelectMultiple)
    payment_methods = forms.MultipleChoiceField(choices=PAYMENTS, widget=forms.CheckboxSelectMultiple)
    financial_documents = forms.MultipleChoiceField(choices=FINANCIAL_DOCS, widget=forms.CheckboxSelectMultiple)
    content_types = forms.MultipleChoiceField(choices=CONTENT_TYPES, widget=forms.CheckboxSelectMultiple)
    webinar_features = forms.MultipleChoiceField(choices=WEBINARS, widget=forms.CheckboxSelectMultiple)
    system_roles = forms.MultipleChoiceField(choices=ROLES, widget=forms.CheckboxSelectMultiple)
    notification_channels = forms.MultipleChoiceField(choices=REMINDERS, widget=forms.CheckboxSelectMultiple, required=False)
    integration_types = forms.MultipleChoiceField(choices=INTEGRATIONS, widget=forms.CheckboxSelectMultiple)
    requested_services = forms.MultipleChoiceField(choices=SERVICES, widget=forms.CheckboxSelectMultiple)
    clinic_type = forms.ChoiceField(choices=[("medical", "پزشکی یا درمانی"), ("dental", "دندان‌پزشکی"), ("psychology", "روان‌شناسی و مشاوره"), ("beauty", "زیبایی و پوست"), ("rehab", "توان‌بخشی"), ("nutrition", "تغذیه و سبک زندگی"), ("education", "آموزش سلامت"), ("other", "سایر")])
    schedule_model = forms.ChoiceField(choices=[("fixed", "بازه‌های ثابت"), ("service", "بر اساس نوع خدمت"), ("practitioner", "تقویم مستقل هر متخصص"), ("resource", "متخصص همراه اتاق یا تجهیز"), ("request", "درخواست نوبت و تأیید پذیرش")])
    waitlist_requirement = forms.ChoiceField(choices=[("yes", "بله، جایگزینی خودکار یا دستی"), ("manual", "فقط فهرست انتظار دستی"), ("no", "خیر"), ("unsure", "نیازمند بررسی")])
    pricing_model = forms.ChoiceField(choices=[("fixed", "قیمت ثابت هر خدمت"), ("doctor", "متفاوت برای هر متخصص"), ("duration", "بر اساس مدت جلسه"), ("package", "پکیج یا چندجلسه‌ای"), ("deposit", "بیعانه و تسویه بعدی"), ("quote", "قیمت پس از بررسی")])
    insurance_requirement = forms.ChoiceField(choices=[("none", "بدون بیمه"), ("info", "فقط دریافت اطلاعات بیمه"), ("documents", "دریافت مدارک و گزارش"), ("integration", "اتصال یا استعلام بیمه"), ("unsure", "نیازمند بررسی")])
    content_access = forms.ChoiceField(choices=[("public", "همه محتوا عمومی"), ("mixed", "ترکیب رایگان و پولی"), ("members", "فقط کاربران عضو"), ("purchase", "خرید تکی یا دوره‌ای"), ("prescribed", "اختصاص محتوا توسط متخصص")])
    webinar_platform = forms.ChoiceField(choices=[("internal", "پخش داخل سایت"), ("external", "اتصال به سرویس بیرونی"), ("both", "هر دو"), ("unsure", "نیازمند پیشنهاد")])
    record_scope = forms.ChoiceField(choices=[("booking", "فقط حساب، نوبت و پرداخت"), ("intake", "فرم‌های اولیه و رضایت‌نامه"), ("documents", "فایل‌ها و مدارک محدود"), ("clinical", "پرونده بالینی و یادداشت درمان"), ("integration", "اتصال به پرونده سامانه موجود")])
    hosting_preference = forms.ChoiceField(choices=[("iran_cloud", "ابر ایران"), ("dedicated", "سرور اختصاصی"), ("on_premise", "داخل کلینیک"), ("unsure", "نیازمند پیشنهاد")])
    delivery_strategy = forms.ChoiceField(choices=[("mvp", "نسخه اولیه ضروری"), ("phased", "اجرای مرحله‌ای"), ("full", "اجرای کامل"), ("consult", "نیازمند پیشنهاد مجری")])
    privacy_accept = forms.BooleanField(label="حریم خصوصی را خوانده‌ام و با تماس برای تحلیل این درخواست موافقم.")
    company_fax = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ClinicOrder
        exclude = ("tracking_code", "privacy_accepted_at", "status", "internal_notes", "created_at")
        widgets = {name: forms.Textarea(attrs={"rows": 3}) for name in ("specialties", "current_process", "main_pain_points", "success_metrics", "appointment_rules", "intake_requirements", "cancellation_refund_rules", "publishing_workflow", "media_requirements", "required_integrations", "migration_sources", "security_requirements", "decision_process", "additional_notes")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "clinic_name": "نام کلینیک یا مجموعه", "clinic_type": "نوع فعالیت", "city": "شهر فعالیت", "branch_count": "تعداد شعب", "specialties": "تخصص‌ها و خدمات اصلی", "practitioner_count": "تعداد پزشکان، درمانگران یا مدرسان", "website": "وب‌سایت فعلی", "contact_name": "نام فرد پاسخ‌گو", "job_title": "سمت", "work_email": "ایمیل", "phone": "شماره تماس",
            "primary_goals": "هدف‌های اصلی پروژه", "target_audiences": "مخاطبان اصلی", "current_channels": "کانال‌های فعلی دریافت نوبت و ارتباط", "current_process": "فرآیند فعلی از درخواست تا مراجعه و پیگیری چگونه است؟", "main_pain_points": "مشکل‌های اصلی وضعیت فعلی چیست؟", "success_metrics": "موفقیت سایت را با چه شاخص‌هایی می‌سنجید؟",
            "visit_modes": "انواع نوبت و جلسه", "schedule_model": "مدل زمان‌بندی", "appointment_rules": "مدت خدمات، فاصله نوبت‌ها، ظرفیت، تعطیلی و قواعد جابه‌جایی را توضیح دهید", "intake_requirements": "پیش از قطعی‌شدن نوبت چه اطلاعات یا فرم‌هایی لازم است؟", "reminder_channels": "روش یادآوری نوبت", "waitlist_requirement": "نیاز به فهرست انتظار", "practitioner_features": "امکانات موردنیاز متخصص", "patient_account_features": "امکانات حساب مراجعه‌کننده",
            "payment_methods": "روش‌های پرداخت", "pricing_model": "مدل قیمت‌گذاری", "insurance_requirement": "نیاز مرتبط با بیمه", "cancellation_refund_rules": "قواعد لغو، تأخیر، عدم مراجعه و بازپرداخت", "financial_documents": "خروجی‌ها و عملیات مالی",
            "content_types": "انواع محتوای آموزشی", "content_access": "مدل دسترسی به محتوا", "publishing_workflow": "چه کسانی محتوا را تولید، بررسی و منتشر می‌کنند؟", "media_requirements": "حجم تقریبی، مدت فایل‌ها، دانلودپذیری و حفاظت صوت/ویدیو", "webinar_features": "امکانات وبینار", "webinar_platform": "روش برگزاری وبینار", "expected_live_attendees": "حداکثر شرکت‌کننده هم‌زمان",
            "system_roles": "نقش‌های سامانه", "record_scope": "دامنه اطلاعات مراجعه‌کننده", "notification_channels": "کانال‌های اعلان عمومی سامانه", "integration_types": "اتصال‌های موردنیاز", "required_integrations": "نام سرویس‌ها یا نرم‌افزارهای مشخص", "migration_sources": "چه داده یا محتوایی باید منتقل شود؟", "security_requirements": "الزامات محرمانگی، رضایت‌نامه، ثبت فعالیت و نگهداری داده", "hosting_preference": "ترجیح میزبانی",
            "delivery_strategy": "روش اجرای ترجیحی", "requested_services": "خدمات موردنیاز از مجری", "budget_range": "بازه بودجه", "expected_timeline": "زمان مورد انتظار", "decision_process": "تصمیم‌گیرندگان و فرآیند تأیید پروژه", "additional_notes": "نکات تکمیلی",
        }
        for name, label in labels.items():
            self.fields[name].label = label
        for name in ("website", "intake_requirements", "media_requirements", "expected_live_attendees", "notification_channels", "required_integrations", "migration_sources", "additional_notes"):
            self.fields[name].required = False
        for name in ("current_process", "main_pain_points", "appointment_rules", "cancellation_refund_rules", "publishing_workflow", "security_requirements", "decision_process"):
            self.fields[name].widget.attrs["minlength"] = 20
            self.fields[name].help_text = "حداقل ۲۰ کاراکتر؛ فرآیند یا قاعده واقعی را کوتاه توضیح دهید."
        self.fields["record_scope"].help_text = "این پرسش‌نامه محل ثبت اطلاعات واقعی بیمار نیست؛ فقط دامنه سامانه را مشخص کنید."

    def clean_company_fax(self):
        if self.cleaned_data.get("company_fax"):
            raise forms.ValidationError("ارسال نامعتبر است.")
        return ""

    def clean_phone(self):
        phone = normalize_digits(self.cleaned_data["phone"]).strip()
        if len(phone) < 8:
            raise forms.ValidationError("شماره تماس کامل وارد کنید.")
        return phone

    def clean(self):
        cleaned = super().clean()
        for name in ("current_process", "main_pain_points", "appointment_rules", "cancellation_refund_rules", "publishing_workflow", "security_requirements", "decision_process"):
            value = (cleaned.get(name) or "").strip()
            if value and len(value) < 20:
                self.add_error(name, "لطفاً حداقل ۲۰ کاراکتر توضیح دهید.")
        for name in ("reminder_channels", "integration_types"):
            values = set(cleaned.get(name) or ())
            if "none" in values and len(values) > 1:
                self.add_error(name, "گزینه «هیچ‌کدام» را همراه گزینه دیگری انتخاب نکنید.")
        if cleaned.get("webinar_platform") == "internal" and not cleaned.get("expected_live_attendees"):
            self.add_error("expected_live_attendees", "برای برآورد پخش داخل سایت، ظرفیت تقریبی را وارد کنید.")
        return cleaned
