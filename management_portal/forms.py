from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User
from accounts.staff_roles import STAFF_ROLES, group_name, sync_staff_role_groups
from core.form_accessibility import enhance_form_accessibility
from core.sms.backends import normalize_iran_mobile
from .models import CaseActivity, CaseTask, CustomerCase, CustomerContact

ROLE_CHOICES = [(key, value["label_fa"]) for key, value in STAFF_ROLES.items()]

class StaffCreateForm(forms.Form):
    first_name = forms.CharField(label="نام", max_length=150)
    last_name = forms.CharField(label="نام خانوادگی", max_length=150)
    email = forms.EmailField(label="ایمیل کاری")
    password = forms.CharField(label="رمز عبور موقت", widget=forms.PasswordInput, validators=[validate_password])
    roles = forms.MultipleChoiceField(label="مسئولیت‌ها", choices=ROLE_CHOICES, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        labels = {
            "first_name": ("نام", "First name"), "last_name": ("نام خانوادگی", "Last name"),
            "email": ("ایمیل کاری", "Work email"), "password": ("رمز عبور موقت", "Temporary password"),
            "roles": ("مسئولیت‌ها", "Responsibilities"),
        }
        for name, pair in labels.items(): self.fields[name].label = pair[0 if lang == "fa" else 1]
        self.fields["roles"].choices = [(key, value[f"label_{lang}"]) for key, value in STAFF_ROLES.items()]
        enhance_form_accessibility(self, autocomplete={
            "first_name": "given-name", "last_name": "family-name",
            "email": "email", "password": "new-password",
        })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("حسابی با این ایمیل وجود دارد." if self.lang == "fa" else "An account with this email already exists.")
        return email

    def save(self):
        groups = sync_staff_role_groups()
        user = User.objects.create_user(
            username=self.cleaned_data["email"], email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"].strip(), last_name=self.cleaned_data["last_name"].strip(),
            password=self.cleaned_data["password"], is_staff=True, is_active=True, email_verified=True,
        )
        user.groups.set([groups[role] for role in self.cleaned_data["roles"]])
        return user


class StaffRolesForm(forms.Form):
    roles = forms.MultipleChoiceField(label="مسئولیت‌ها", choices=ROLE_CHOICES, widget=forms.CheckboxSelectMultiple, required=False)
    is_staff = forms.BooleanField(label="دسترسی به مرکز مدیریت فعال باشد", required=False)

    def __init__(self, *args, user, lang="fa", **kwargs):
        self.staff_user = user
        initial = kwargs.setdefault("initial", {})
        initial["roles"] = [key for key in STAFF_ROLES if user.groups.filter(name=group_name(key)).exists()]
        initial["is_staff"] = user.is_staff
        super().__init__(*args, **kwargs)
        self.fields["roles"].label = "مسئولیت‌ها" if lang == "fa" else "Responsibilities"
        self.fields["is_staff"].label = "دسترسی به مرکز مدیریت فعال باشد" if lang == "fa" else "Allow access to the management center"
        self.fields["roles"].choices = [(key, value[f"label_{lang}"]) for key, value in STAFF_ROLES.items()]
        enhance_form_accessibility(self)

    def save(self):
        groups = sync_staff_role_groups()
        role_names = [group_name(key) for key in STAFF_ROLES]
        self.staff_user.groups.remove(*self.staff_user.groups.filter(name__in=role_names))
        self.staff_user.groups.add(*[groups[role] for role in self.cleaned_data["roles"]])
        self.staff_user.is_staff = self.cleaned_data["is_staff"]
        self.staff_user.save(update_fields=["is_staff"])
        return self.staff_user


class ManualSMSForm(forms.Form):
    recipients = forms.CharField(
        label="شماره گیرندگان",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "هر شماره در یک خط، یا با ویرگول جدا شود\n0912...\n+989..."}),
        help_text="حداکثر ۲۰ شماره ایرانی؛ قالب‌های 09، +98، 0098 و ارقام فارسی پذیرفته می‌شوند.",
    )
    message = forms.CharField(
        label="متن پیامک",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 7, "placeholder": "متن پیام را بنویسید...", "data-sms-message": ""}),
        help_text="هزینه نهایی بر اساس طول پیام و تعرفه پنل محاسبه می‌شود.",
    )
    confirm = forms.BooleanField(label="شماره‌ها و متن را بررسی کرده‌ام و ارسال واقعی انجام شود")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        if lang == "en":
            self.fields["recipients"].label = "Recipients"
            self.fields["recipients"].help_text = "Up to 20 Iranian mobile numbers; 09, +98 and 0098 formats are accepted."
            self.fields["recipients"].widget.attrs["placeholder"] = "One number per line or comma-separated\n0912...\n+989..."
            self.fields["message"].label = "Message"
            self.fields["message"].help_text = "Final cost depends on message length and provider pricing."
            self.fields["message"].widget.attrs["placeholder"] = "Write the message..."
            self.fields["confirm"].label = "I reviewed the numbers and message and confirm real delivery"
        enhance_form_accessibility(self, autocomplete={"recipients": "off", "message": "off"})

    def clean_recipients(self):
        raw = self.cleaned_data["recipients"]
        values = [item.strip() for item in raw.replace("،", ",").replace(";", ",").replace("\n", ",").split(",") if item.strip()]
        if not values:
            raise forms.ValidationError("حداقل یک شماره وارد کنید." if self.lang == "fa" else "Enter at least one mobile number.")
        if len(values) > 20:
            raise forms.ValidationError("در هر ارسال حداکثر ۲۰ شماره مجاز است." if self.lang == "fa" else "Each delivery can include no more than 20 numbers.")
        normalized, invalid = [], []
        for value in values:
            try:
                mobile = normalize_iran_mobile(value)
            except ValueError:
                invalid.append(value[:24])
                continue
            if mobile not in normalized:
                normalized.append(mobile)
        if invalid:
            prefix = "شماره نامعتبر: " if self.lang == "fa" else "Invalid number: "
            raise forms.ValidationError(prefix + ("، " if self.lang == "fa" else ", ").join(invalid[:5]))
        return normalized

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if not message:
            raise forms.ValidationError("متن پیامک نمی‌تواند خالی باشد." if self.lang == "fa" else "The message cannot be empty.")
        return message


class CustomerMessageForm(forms.Form):
    recipient = forms.CharField(label="شماره گیرنده", max_length=20)
    message = forms.CharField(
        label="متن پیام",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "پیام پیگیری را بنویسید..."}),
    )
    confirm = forms.BooleanField(label="شماره و متن را بررسی کرده‌ام")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        if lang == "en":
            self.fields["recipient"].label = "Recipient"
            self.fields["message"].label = "Message"
            self.fields["message"].widget.attrs["placeholder"] = "Write a follow-up message..."
            self.fields["confirm"].label = "I reviewed the number and message"
        enhance_form_accessibility(self, autocomplete={"recipient": "tel", "message": "off"})

    def clean_recipient(self):
        try:
            return normalize_iran_mobile(self.cleaned_data["recipient"])
        except ValueError as exc:
            raise forms.ValidationError("شماره موبایل معتبر نیست." if self.lang == "fa" else "Enter a valid mobile number.") from exc

    def clean_message(self):
        value = self.cleaned_data["message"].strip()
        if not value:
            raise forms.ValidationError("متن پیام نمی‌تواند خالی باشد." if self.lang == "fa" else "Message cannot be empty.")
        return value


class CustomerCaseForm(forms.ModelForm):
    tags = forms.CharField(required=False)
    class Meta:
        model = CustomerCase
        fields = ("stage", "priority", "owner", "next_follow_up_at", "tags", "summary")
        widgets = {"next_follow_up_at": forms.DateTimeInput(attrs={"type": "datetime-local"}), "summary": forms.Textarea(attrs={"rows": 5}), "tags": forms.TextInput(attrs={"placeholder": "فروش، مهم، قرارداد"})}

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs); self.lang = lang
        if self.instance and self.instance.pk: self.initial["tags"] = "، ".join(self.instance.tags)
        self.fields["owner"].queryset = User.objects.filter(is_staff=True, is_active=True).order_by("first_name", "email")
        labels = {"stage": ("مرحله پرونده", "Case stage"), "priority": ("اولویت", "Priority"), "owner": ("مسئول پرونده", "Case owner"), "next_follow_up_at": ("پیگیری بعدی", "Next follow-up"), "tags": ("برچسب‌ها", "Tags"), "summary": ("خلاصه مدیریتی", "Management summary")}
        for name, pair in labels.items(): self.fields[name].label = pair[0 if lang == "fa" else 1]
        if lang == "en":
            self.fields["stage"].choices = (("new", "New"), ("discovery", "Discovery"), ("qualified", "Qualified"), ("proposal", "Proposal / contract"), ("won", "Won"), ("lost", "Closed"))
            self.fields["priority"].choices = (("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent"))

    def clean_tags(self):
        value = self.cleaned_data["tags"]
        if isinstance(value, list): return value
        return [item.strip() for item in str(value).replace("،", ",").split(",") if item.strip()][:20]


class CaseTaskForm(forms.ModelForm):
    class Meta:
        model = CaseTask
        fields = ("title", "description", "priority", "assigned_to", "due_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 3}), "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True, is_active=True)
        labels = {"title": ("عنوان وظیفه", "Task title"), "description": ("توضیحات", "Description"), "priority": ("اولویت", "Priority"), "assigned_to": ("مسئول", "Assignee"), "due_at": ("مهلت", "Due date")}
        for name, pair in labels.items(): self.fields[name].label = pair[0 if lang == "fa" else 1]
        if lang == "en": self.fields["priority"].choices = (("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent"))


class CaseActivityForm(forms.ModelForm):
    class Meta:
        model = CaseActivity
        fields = ("kind", "title", "body")
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        labels = {"kind": ("نوع فعالیت", "Activity type"), "title": ("عنوان", "Title"), "body": ("شرح", "Details")}
        for name, pair in labels.items(): self.fields[name].label = pair[0 if lang == "fa" else 1]
        if lang == "en": self.fields["kind"].choices = (("note", "Note"), ("call", "Call"), ("message", "Message"), ("meeting", "Meeting"))


class CustomerContactForm(forms.ModelForm):
    class Meta:
        model = CustomerContact
        fields = ("name", "role", "phone", "email", "user", "is_primary")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(is_staff=False, is_active=True).order_by("email")
        labels = {
            "name": ("نام مخاطب", "Contact name"), "role": ("سمت در شرکت", "Role at company"),
            "phone": ("شماره تماس", "Phone"), "email": ("ایمیل", "Email"),
            "user": ("حساب کاربری متصل", "Linked site account"), "is_primary": ("مخاطب اصلی", "Primary contact"),
        }
        for name, pair in labels.items():
            self.fields[name].label = pair[0 if lang == "fa" else 1]
        enhance_form_accessibility(self, autocomplete={
            "name": "name", "role": "organization-title", "phone": "tel", "email": "email",
        })

    def clean(self):
        cleaned = super().clean()
        user = cleaned.get("user")
        if user:
            cleaned["email"] = cleaned.get("email") or user.email
            cleaned["phone"] = cleaned.get("phone") or user.mobile or ""
        return cleaned
