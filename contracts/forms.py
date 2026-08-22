from django import forms
from django.forms import formset_factory

from core.sms.backends import normalize_iran_mobile
from core.form_accessibility import enhance_form_accessibility
from crm_orders.models import CrmOrder
from clinic_orders.models import ClinicOrder
from core.models import CompanyProfile
from .models import ContractProposal
from .questionnaires import normalize_schema


def _specialist_summary(order, language="fa"):
    discovery = order.specialist_discovery if hasattr(order, "specialist_discovery") else None
    if not discovery or discovery.status == "draft" or not discovery.answers:
        return ""
    lines = ["Specialist discovery responses:" if language == "en" else "پاسخ‌های نیازسنجی تخصصی:"]
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
        self.language = language
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
            self.fields["delivery_terms"].help_text = (
                "Example: 8 weeks after the advance payment and required information are received."
            )
            if not self.is_bound and not self.instance.pk:
                self.initial.setdefault("title", "Custom software design and development proposal")
                self.initial.setdefault("payment_terms", "50% at project start and 50% at final delivery")
        choices = [("", "— Manual entry —" if language == "en" else "— انتخاب دستی —")]
        choices += [(f"crm:{item.pk}", f"CRM · {item.tracking_code} · {item.organization_name}") for item in CrmOrder.objects.order_by("-created_at")[:100]]
        clinic_label = "Clinic" if language == "en" else "کلینیک"
        choices += [(f"clinic:{item.pk}", f"{clinic_label} · {item.tracking_code} · {item.clinic_name}") for item in ClinicOrder.objects.order_by("-created_at")[:100]]
        self.fields["needs_assessment"].choices = choices
        enhance_form_accessibility(self, autocomplete={
            "customer_name": "name",
            "customer_phone": "tel",
            "customer_email": "email",
        })

    def _project_title(self, kind, name):
        if self.language == "en":
            prefix = "Enterprise CRM platform" if kind == "crm" else "Clinic platform"
        else:
            prefix = "سامانه CRM سازمانی" if kind == "crm" else "پلتفرم کلینیک"
        return f"{prefix} {name}"

    def _client_details(self, kind, source, name):
        if self.language == "en":
            location = f"Industry: {source.industry}" if kind == "crm" else f"City: {source.city}"
            return (
                f"Organisation: {name}\n{location}\nDiscovery reference: {source.tracking_code}\n"
                f"Success criteria: {source.success_metrics}"
            )
        location = f"صنعت: {source.industry}" if kind == "crm" else f"شهر: {source.city}"
        return (
            f"نام مجموعه: {name}\n{location}\nکد نیازسنجی: {source.tracking_code}\n"
            f"معیارهای موفقیت: {source.success_metrics}"
        )

    def _assessment_payload(self, kind, source):
        name = source.organization_name if kind == "crm" else source.clinic_name
        specialist = _specialist_summary(source, self.language) if kind == "crm" else ""
        return {
            "customer_name": source.contact_name or name,
            "customer_phone": source.phone,
            "customer_email": source.work_email,
            "project_title": self._project_title(kind, name),
            "project_scope": "\n\n".join(filter(None, [
                source.current_process, source.main_pain_points, source.required_integrations,
                source.security_requirements, specialist,
            ])),
            "client_details": self._client_details(kind, source, name),
        }

    @property
    def assessment_data(self):
        data = {}
        for item in CrmOrder.objects.order_by("-created_at")[:100]:
            data[f"crm:{item.pk}"] = self._assessment_payload("crm", item)
        for item in ClinicOrder.objects.order_by("-created_at")[:100]:
            data[f"clinic:{item.pk}"] = self._assessment_payload("clinic", item)
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
        payload = self._assessment_payload(kind, source)
        self.instance.project_title = payload["project_title"]
        self.instance.project_scope = payload["project_scope"]
        self.instance.client_details = payload["client_details"]


class ContractSettingsForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ("legal_name_fa", "brand_name", "registration_number", "national_id", "chief_executive_fa", "phone", "address_fa")
        widgets = {"address_fa": forms.Textarea(attrs={"rows": 4})}
        labels = {"legal_name_fa": "نام حقوقی مجری", "brand_name": "نام برند", "registration_number": "شماره ثبت", "national_id": "شناسه ملی", "chief_executive_fa": "نماینده مجاز", "phone": "تلفن", "address_fa": "نشانی قرارداد"}

    def __init__(self, *args, **kwargs):
        language = kwargs.pop("language", "fa")
        super().__init__(*args, **kwargs)
        if language == "en":
            labels = {
                "legal_name_fa": "Contractor legal name",
                "brand_name": "Brand name",
                "registration_number": "Registration number",
                "national_id": "National ID",
                "chief_executive_fa": "Authorised representative",
                "phone": "Phone",
                "address_fa": "Contract address",
            }
            for name, label in labels.items():
                self.fields[name].label = label
        enhance_form_accessibility(self, autocomplete={
            "legal_name_fa": "organization",
            "brand_name": "organization",
            "phone": "tel",
            "address_fa": "street-address",
        })


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
        self.language = language
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
            raise forms.ValidationError(
                "Enter both a title and text for the new clause."
                if self.language == "en" else
                "برای بند جدید، عنوان و متن را با هم وارد کنید."
            )
        return data


class OtpRequestForm(forms.Form):
    agreement = forms.BooleanField(label="متن و همه بندهای این نسخه را خوانده‌ام و با آن موافقم.")


class OtpVerifyForm(forms.Form):
    code = forms.RegexField(label="کد تأیید شش‌رقمی", regex=r"^\d{6}$", max_length=6, min_length=6)


class ContractAccessForm(forms.Form):
    phone = forms.CharField(
        label="شماره همراه مجاز",
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
    )
    password = forms.CharField(
        label="رمز ورود قرارداد",
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "current-password"}),
        max_length=128,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            return
        errors = self.errors
        for name in ("phone", "password"):
            if name not in errors:
                continue
            field_id = self[name].id_for_label
            self.fields[name].widget.attrs.update({
                "aria-invalid": "true",
                "aria-describedby": f"{field_id}_error",
            })

    def clean_phone(self):
        return normalize_iran_mobile(self.cleaned_data["phone"])


class WorkspaceContractForm(forms.ModelForm):
    """Commercial/private terms edited inside a single customer case."""

    class Meta:
        model = ContractProposal
        fields = (
            "title",
            "project_title",
            "project_scope",
            "amount_irr",
            "payment_terms",
            "delivery_terms",
            "private_terms",
        )
        widgets = {
            "project_scope": forms.Textarea(attrs={"rows": 6}),
            "payment_terms": forms.Textarea(attrs={"rows": 4}),
            "private_terms": forms.Textarea(attrs={"rows": 16}),
        }

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        labels = {
            "title": ("عنوان بسته قرارداد", "Contract package title"),
            "project_title": ("عنوان پروژه", "Project title"),
            "project_scope": ("محدوده و خروجی‌های پروژه", "Project scope and deliverables"),
            "amount_irr": ("مبلغ کل قرارداد (ریال)", "Total contract value (IRR)"),
            "payment_terms": ("روش و مراحل پرداخت", "Payment stages"),
            "delivery_terms": ("زمان و معیار تحویل", "Delivery time and acceptance criteria"),
            "private_terms": ("شرایط خصوصی پیمان", "Project-specific terms"),
        }
        for name, pair in labels.items():
            self.fields[name].label = pair[0 if lang == "fa" else 1]
        self.fields["private_terms"].help_text = (
            "مواد اختصاصی این مشتری، مبلغ، زمان‌بندی، پشتیبانی و استثناها را دقیق بنویسید."
            if lang == "fa" else
            "Record customer-specific clauses, commercial terms, schedule, support and exceptions."
        )
        self.fields["delivery_terms"].help_text = (
            "مثال: ۸ هفته پس از دریافت پیش‌پرداخت و اطلاعات لازم"
            if lang == "fa" else
            "Example: 8 weeks after receiving the advance payment and required information."
        )
        enhance_form_accessibility(self)

    def clean_amount_irr(self):
        value = self.cleaned_data["amount_irr"]
        if value <= 0:
            raise forms.ValidationError(
                "مبلغ قرارداد باید بیشتر از صفر باشد."
                if self.lang == "fa" else
                "The contract value must be greater than zero."
            )
        return value


class GeneralTermsRevisionForm(forms.Form):
    title = forms.CharField(label="عنوان نسخه", max_length=200, initial="شرایط عمومی پیمان")
    body = forms.CharField(label="متن شرایط عمومی", widget=forms.Textarea(attrs={"rows": 24}), max_length=100_000)
    change_note = forms.CharField(label="شرح تغییر این نسخه", widget=forms.Textarea(attrs={"rows": 3}), max_length=240, required=False)
    confirm = forms.BooleanField(label="می‌دانم این نسخه فقط به پرونده‌های منتشرنشده آینده اعمال می‌شود.")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        if lang == "en":
            self.fields["title"].label = "Version title"
            self.fields["body"].label = "General terms"
            self.fields["change_note"].label = "Change note"
            self.fields["confirm"].label = "I understand this revision only applies to future, unpublished workspaces."
        enhance_form_accessibility(self)


QUESTION_TYPE_CHOICES = (
    ("long_text", "پاسخ تشریحی"),
    ("short_text", "پاسخ کوتاه"),
    ("single_choice", "تک‌گزینه‌ای"),
    ("multiple_choice", "چندگزینه‌ای"),
    ("yes_no", "بله / خیر"),
    ("number", "عدد"),
    ("date", "تاریخ"),
)


class QuestionnaireRowForm(forms.Form):
    section_key = forms.CharField(widget=forms.HiddenInput, required=False, max_length=64)
    question_key = forms.CharField(widget=forms.HiddenInput, required=False, max_length=64)
    section_title = forms.CharField(label="عنوان بخش", max_length=180)
    section_description = forms.CharField(label="توضیح کوتاه بخش", max_length=800, required=False)
    question_label = forms.CharField(label="متن سؤال", max_length=500)
    help_text = forms.CharField(
        label="راهنما و نمونه پاسخ",
        max_length=1200,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    placeholder = forms.CharField(
        label="نمونه داخل کادر پاسخ",
        max_length=300,
        required=False,
        help_text="نمونه کوتاهی بنویسید که نوع پاسخ مناسب را نشان دهد؛ پاسخ مشتری نیست.",
    )
    answer_type = forms.ChoiceField(label="نوع پاسخ", choices=QUESTION_TYPE_CHOICES)
    choices = forms.CharField(
        label="گزینه‌ها",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "هر گزینه در یک خط"}),
        help_text="فقط برای سؤال تک‌گزینه‌ای یا چندگزینه‌ای؛ هر گزینه را در یک خط بنویسید.",
    )
    required = forms.BooleanField(label="پاسخ الزامی باشد", required=False, initial=True)

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        if lang == "en":
            labels = {
                "section_title": "Section title", "section_description": "Short section description",
                "question_label": "Question", "help_text": "Guidance and example",
                "placeholder": "Answer placeholder", "answer_type": "Answer type",
                "choices": "Choices", "required": "Response is required",
            }
            for name, label in labels.items():
                self.fields[name].label = label
            self.fields["answer_type"].choices = (
                ("long_text", "Long response"), ("short_text", "Short response"),
                ("single_choice", "Single choice"), ("multiple_choice", "Multiple choice"),
                ("yes_no", "Yes / no"), ("number", "Number"), ("date", "Date"),
            )
            self.fields["choices"].help_text = "For choice questions only; enter one choice per line."
            self.fields["choices"].widget.attrs["placeholder"] = "One choice per line"
            self.fields["placeholder"].help_text = "A short example that demonstrates the expected response; it is not the customer's answer."
        enhance_form_accessibility(self)

    def clean_choices(self):
        raw = self.cleaned_data.get("choices", "")
        return [line.strip() for line in raw.replace("،", "\n").splitlines() if line.strip()]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("answer_type") in {"single_choice", "multiple_choice"} and len(cleaned.get("choices") or []) < 2:
            self.add_error(
                "choices",
                "حداقل دو گزینه بنویسید." if self.lang == "fa" else "Enter at least two choices.",
            )
        return cleaned


QuestionnaireRowFormSet = formset_factory(
    QuestionnaireRowForm,
    extra=0,
    min_num=1,
    max_num=120,
    validate_min=True,
    validate_max=True,
    can_delete=True,
)


def questionnaire_rows_from_schema(schema):
    rows = []
    for section in normalize_schema(schema):
        for question in section["questions"]:
            rows.append({
                "section_key": section["key"],
                "question_key": question["key"],
                "section_title": section["title"],
                "section_description": section["description"],
                "question_label": question["label"],
                "help_text": question["help_text"],
                "placeholder": question["placeholder"],
                "answer_type": question["type"],
                "choices": "\n".join(question["choices"]),
                "required": question["required"],
            })
    return rows


def questionnaire_schema_from_formset(formset):
    if not formset.is_valid():
        raise ValueError("The formset must be valid before building a schema.")
    sections = []
    current = None
    used_section_keys = set()
    used_question_keys = {}
    for row_index, row in enumerate(formset.cleaned_data, 1):
        if not row or row.get("DELETE"):
            continue
        section_title = row["section_title"].strip()
        if current is None or current["title"] != section_title:
            raw_section_key = row.get("section_key", "").strip()
            section_key = raw_section_key if raw_section_key and raw_section_key not in used_section_keys else f"section_{len(sections) + 1}"
            used_section_keys.add(section_key)
            used_question_keys[section_key] = set()
            current = {
                "key": section_key,
                "title": section_title,
                "description": row.get("section_description", "").strip(),
                "questions": [],
            }
            sections.append(current)
        raw_question_key = row.get("question_key", "").strip()
        question_key = raw_question_key if raw_question_key and raw_question_key not in used_question_keys[current["key"]] else f"question_{row_index}"
        used_question_keys[current["key"]].add(question_key)
        current["questions"].append({
            "key": question_key,
            "label": row["question_label"].strip(),
            "help_text": row.get("help_text", "").strip(),
            "type": row["answer_type"],
            "required": bool(row.get("required")),
            "choices": row.get("choices") or [],
            "placeholder": row.get("placeholder", "").strip(),
        })
    return normalize_schema(sections)


class WorkspaceAccessForm(forms.Form):
    authorized_phone = forms.CharField(
        label="شماره مجاز برای ورود",
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
    )
    delivery_target = forms.ChoiceField(
        label="اطلاعات ورود به کجا ارسال شود؟",
        choices=(("same", "همین شماره مجاز"), ("other", "شماره دیگری")),
        widget=forms.RadioSelect,
        initial="same",
    )
    recipient_phone = forms.CharField(
        label="شماره دریافت‌کننده پیامک",
        required=False,
        max_length=24,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
    )
    password = forms.CharField(
        label="رمز اختصاصی",
        required=False,
        min_length=12,
        max_length=128,
        widget=forms.PasswordInput(render_value=True, attrs={"autocomplete": "new-password"}),
        help_text="اگر خالی بگذارید، آرویون یک رمز قوی و یک‌بارنمایش می‌سازد.",
    )
    expires_in_days = forms.ChoiceField(
        label="اعتبار دسترسی",
        choices=(("14", "۱۴ روز"), ("30", "۳۰ روز"), ("90", "۹۰ روز"), ("", "بدون تاریخ انقضا")),
        initial="30",
        required=False,
    )
    send_now = forms.BooleanField(label="بعد از ساخت، لینک و اطلاعات ورود پیامک شود", required=False, initial=True)
    confirm = forms.BooleanField(label="شماره‌ها، دسترسی و محرمانگی اطلاعات را بررسی کرده‌ام.")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        if lang == "en":
            labels = {
                "authorized_phone": "Authorised sign-in phone",
                "delivery_target": "Where should credentials be sent?",
                "recipient_phone": "SMS recipient",
                "password": "Private password",
                "expires_in_days": "Access lifetime",
                "send_now": "Send the link and credentials after creation",
                "confirm": "I reviewed the numbers, access and confidentiality implications.",
            }
            for name, label in labels.items():
                self.fields[name].label = label
            self.fields["delivery_target"].choices = (("same", "The authorised phone"), ("other", "A different phone"))
            self.fields["expires_in_days"].choices = (("14", "14 days"), ("30", "30 days"), ("90", "90 days"), ("", "No expiry"))
            self.fields["password"].help_text = "Leave blank to generate a strong password shown only once."
        enhance_form_accessibility(self, autocomplete={
            "authorized_phone": "tel", "recipient_phone": "tel", "password": "new-password",
        })

    def clean_authorized_phone(self):
        return normalize_iran_mobile(self.cleaned_data["authorized_phone"])

    def clean_recipient_phone(self):
        value = self.cleaned_data.get("recipient_phone", "").strip()
        return normalize_iran_mobile(value) if value else ""

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("delivery_target") == "other" and not cleaned.get("recipient_phone"):
            self.add_error(
                "recipient_phone",
                "شماره دریافت‌کننده را وارد کنید." if self.lang == "fa" else "Enter the recipient phone.",
            )
        if cleaned.get("delivery_target") == "same":
            cleaned["recipient_phone"] = cleaned.get("authorized_phone", "")
        return cleaned


class DynamicQuestionnaireSectionForm(forms.Form):
    def __init__(self, *args, section, **kwargs):
        self.section = section
        super().__init__(*args, **kwargs)
        for question in section["questions"]:
            common = {
                "label": question["label"],
                "help_text": question["help_text"],
                "required": question["required"],
            }
            attrs = {"data-autosave-field": question["key"]}
            if question.get("placeholder"):
                attrs["placeholder"] = question["placeholder"]
            answer_type = question["type"]
            if answer_type == "long_text":
                field = forms.CharField(widget=forms.Textarea(attrs={**attrs, "rows": 5}), max_length=8000, **common)
            elif answer_type == "single_choice":
                field = forms.ChoiceField(choices=[("", "انتخاب کنید…"), *[(item, item) for item in question["choices"]]], widget=forms.RadioSelect(attrs=attrs), **common)
            elif answer_type == "multiple_choice":
                field = forms.MultipleChoiceField(choices=[(item, item) for item in question["choices"]], widget=forms.CheckboxSelectMultiple(attrs=attrs), **common)
            elif answer_type == "yes_no":
                field = forms.ChoiceField(choices=(("", "انتخاب کنید…"), ("yes", "بله"), ("no", "خیر")), widget=forms.RadioSelect(attrs=attrs), **common)
            elif answer_type == "number":
                field = forms.CharField(widget=forms.NumberInput(attrs={**attrs, "inputmode": "decimal"}), max_length=500, **common)
            elif answer_type == "date":
                field = forms.CharField(widget=forms.DateInput(attrs={**attrs, "type": "date"}), max_length=10, **common)
            else:
                field = forms.CharField(widget=forms.TextInput(attrs=attrs), max_length=500, **common)
            self.fields[question["key"]] = field
        enhance_form_accessibility(self)
