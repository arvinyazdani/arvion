from django import forms

from core.sms.backends import normalize_iran_mobile
from crm_orders.models import CrmOrder
from clinic_orders.models import ClinicOrder
from core.models import CompanyProfile
from .models import ContractProposal


def _specialist_summary(order):
    discovery = order.specialist_discovery if hasattr(order, "specialist_discovery") else None
    if not discovery or discovery.status == "draft" or not discovery.answers:
        return ""
    lines = ["پاسخ‌های نیازسنجی تخصصی:"]
    for key, value in discovery.answers.items():
        if value not in (None, "", [], {}):
            rendered = "، ".join(map(str, value)) if isinstance(value, list) else str(value)
            lines.append(f"- {key}: {rendered}")
    return "\n".join(lines)


class ProposalForm(forms.ModelForm):
    needs_assessment = forms.ChoiceField(label="منبع نیازسنجی", required=False, choices=())

    class Meta:
        model = ContractProposal
        fields = ("needs_assessment", "title", "customer_name", "customer_phone", "customer_email", "client_details", "project_title", "project_scope", "amount_irr", "payment_terms", "delivery_terms", "general_terms", "private_terms")
        widgets = {"client_details": forms.Textarea(attrs={"rows": 3}), "project_scope": forms.Textarea(attrs={"rows": 6}), "payment_terms": forms.Textarea(attrs={"rows": 3}), "general_terms": forms.Textarea(attrs={"rows": 10}), "private_terms": forms.Textarea(attrs={"rows": 10})}
        labels = {
            "title": "عنوان قرارداد", "customer_name": "نام مشتری", "customer_phone": "شماره موبایل مشتری",
            "customer_email": "ایمیل مشتری", "client_details": "اطلاعات تکمیلی مشتری", "project_title": "عنوان پروژه",
            "project_scope": "محدوده و شرح پروژه", "amount_irr": "مبلغ قرارداد (ریال)", "payment_terms": "شرایط پرداخت",
            "delivery_terms": "زمان و شرایط تحویل",
            "general_terms": "شرایط عمومی پیمان", "private_terms": "شرایط خصوصی پیمان",
        }

    def clean_customer_phone(self):
        return normalize_iran_mobile(self.cleaned_data["customer_phone"])

    def __init__(self, *args, **kwargs):
        language = kwargs.pop("language", "fa")
        super().__init__(*args, **kwargs)
        if language == "en":
            labels = {
                "needs_assessment": "Discovery source", "title": "Contract title", "customer_name": "Customer name",
                "customer_phone": "Customer mobile", "customer_email": "Customer email", "client_details": "Customer details",
                "project_title": "Project title", "project_scope": "Project scope", "amount_irr": "Contract amount (IRR)",
                "payment_terms": "Payment terms", "delivery_terms": "Delivery terms",
                "general_terms": "General terms", "private_terms": "Private terms",
            }
            for name, label in labels.items():
                self.fields[name].label = label
        choices = [("", "— Manual entry —" if language == "en" else "— انتخاب دستی —")]
        choices += [(f"crm:{item.pk}", f"CRM · {item.tracking_code} · {item.organization_name}") for item in CrmOrder.objects.order_by("-created_at")[:100]]
        clinic_label = "Clinic" if language == "en" else "کلینیک"
        choices += [(f"clinic:{item.pk}", f"{clinic_label} · {item.tracking_code} · {item.clinic_name}") for item in ClinicOrder.objects.order_by("-created_at")[:100]]
        self.fields["needs_assessment"].choices = choices

    @property
    def assessment_data(self):
        data = {}
        for item in CrmOrder.objects.order_by("-created_at")[:100]:
            data[f"crm:{item.pk}"] = {"customer_name": item.contact_name or item.organization_name, "customer_phone": item.phone, "customer_email": item.work_email, "project_title": f"سامانه CRM سازمانی {item.organization_name}", "project_scope": "\n\n".join(filter(None, [item.current_process, item.main_pain_points, item.required_integrations, item.security_requirements, _specialist_summary(item)])), "client_details": f"نام مجموعه: {item.organization_name}\nصنعت: {item.industry}\nکد نیازسنجی: {item.tracking_code}\nمعیارهای موفقیت: {item.success_metrics}"}
        for item in ClinicOrder.objects.order_by("-created_at")[:100]:
            data[f"clinic:{item.pk}"] = {"customer_name": item.contact_name or item.clinic_name, "customer_phone": item.phone, "customer_email": item.work_email, "project_title": f"پلتفرم کلینیک {item.clinic_name}", "project_scope": "\n".join(filter(None, [item.current_process, item.main_pain_points, item.required_integrations, item.security_requirements])), "client_details": f"نام مجموعه: {item.clinic_name}\nشهر: {item.city}\nکد نیازسنجی: {item.tracking_code}\nمعیارهای موفقیت: {item.success_metrics}"}
        return data

    def apply_assessment(self):
        value = self.cleaned_data.get("needs_assessment", "")
        if not value:
            return
        kind, pk = value.split(":", 1)
        source = CrmOrder.objects.get(pk=pk) if kind == "crm" else ClinicOrder.objects.get(pk=pk)
        self.instance.customer_name = source.contact_name or (source.organization_name if kind == "crm" else source.clinic_name)
        self.instance.customer_phone = normalize_iran_mobile(source.phone)
        self.instance.customer_email = source.work_email
        name = source.organization_name if kind == "crm" else source.clinic_name
        self.instance.project_title = f"{'سامانه CRM سازمانی' if kind == 'crm' else 'پلتفرم کلینیک'} {name}"
        specialist = _specialist_summary(source) if kind == "crm" else ""
        self.instance.project_scope = "\n\n".join(filter(None, [source.current_process, source.main_pain_points, source.required_integrations, source.security_requirements, specialist]))
        location = f"صنعت: {source.industry}" if kind == "crm" else f"شهر: {source.city}"
        self.instance.client_details = f"نام مجموعه: {name}\n{location}\nکد نیازسنجی: {source.tracking_code}\nمعیارهای موفقیت: {source.success_metrics}"


class ContractSettingsForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ("legal_name_fa", "brand_name", "registration_number", "national_id", "chief_executive_fa", "phone", "address_fa")
        widgets = {"address_fa": forms.Textarea(attrs={"rows": 4})}
        labels = {"legal_name_fa": "نام حقوقی مجری", "brand_name": "نام برند", "registration_number": "شماره ثبت", "national_id": "شناسه ملی", "chief_executive_fa": "نماینده مجاز", "phone": "تلفن", "address_fa": "نشانی قرارداد"}


class ContractReviewForm(forms.Form):
    accepted_clauses = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)
    rejection_notes = forms.CharField(label="دلیل یا توضیح بندهای مورد تأیید نبود", widget=forms.Textarea(attrs={"rows": 4}), required=False, max_length=2000)
    suggested_clause = forms.CharField(label="پیشنهاد بند جدید", widget=forms.Textarea(attrs={"rows": 4}), required=False, max_length=2000)

    def __init__(self, *args, version, **kwargs):
        self.version = version
        super().__init__(*args, **kwargs)
        clauses = version.snapshot["clauses"]
        self.fields["accepted_clauses"].choices = [(str(item["id"]), item["title"]) for item in clauses]
        self.initial.setdefault("accepted_clauses", [str(item["id"]) for item in clauses])

    def clean(self):
        data = super().clean()
        all_ids = {str(item["id"]) for item in self.version.snapshot["clauses"]}
        accepted = set(data.get("accepted_clauses", []))
        if accepted != all_ids and not data.get("rejection_notes", "").strip():
            self.add_error("rejection_notes", "برای بندهای مورد تأیید نبود، توضیح کوتاهی بنویسید.")
        return data


class ClauseSelectionForm(forms.Form):
    enabled_clauses = forms.MultipleChoiceField(label="بندهای فعال", widget=forms.CheckboxSelectMultiple, required=False)
    custom_title = forms.CharField(label="عنوان بند جدید", max_length=180, required=False)
    custom_body = forms.CharField(label="متن بند جدید", widget=forms.Textarea(attrs={"rows": 4}), required=False)

    def __init__(self, *args, proposal, **kwargs):
        self.proposal = proposal
        language = kwargs.pop("language", "fa")
        super().__init__(*args, **kwargs)
        if language == "en":
            self.fields["enabled_clauses"].label = "Enabled clauses"
            self.fields["custom_title"].label = "New clause title"
            self.fields["custom_body"].label = "New clause text"
        clauses = proposal.clauses.all()
        self.fields["enabled_clauses"].choices = [(str(item.pk), item.title) for item in clauses]
        self.initial.setdefault("enabled_clauses", [str(item.pk) for item in clauses if item.is_enabled])

    def clean(self):
        data = super().clean()
        if bool(data.get("custom_title", "").strip()) != bool(data.get("custom_body", "").strip()):
            raise forms.ValidationError("برای بند جدید، عنوان و متن را با هم وارد کنید.")
        return data


class OtpRequestForm(forms.Form):
    agreement = forms.BooleanField(label="متن و همه بندهای این نسخه را خوانده‌ام و با آن موافقم.")


class OtpVerifyForm(forms.Form):
    code = forms.RegexField(label="کد تأیید شش‌رقمی", regex=r"^\d{6}$", max_length=6, min_length=6)


class ContractAccessForm(forms.Form):
    phone = forms.CharField(label="شماره همراه مجاز", max_length=24)
    password = forms.CharField(label="رمز ورود قرارداد", widget=forms.PasswordInput(render_value=False), max_length=128)

    def clean_phone(self):
        return normalize_iran_mobile(self.cleaned_data["phone"])
