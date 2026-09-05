from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.form_accessibility import enhance_form_accessibility
from core.sms.backends import normalize_iran_mobile

from .models import User


class RegistrationForm(UserCreationForm):
    mobile = forms.CharField(max_length=20)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "mobile")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        labels = {
            "fa": {"first_name": "نام", "last_name": "نام خانوادگی", "email": "ایمیل", "mobile": "شماره موبایل", "password1": "رمز عبور", "password2": "تکرار رمز عبور"},
            "en": {"first_name": "First name", "last_name": "Last name", "email": "Email", "mobile": "Mobile number", "password1": "Password", "password2": "Confirm password"},
        }[lang]
        for name, label in labels.items():
            self.fields[name].label = label
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["mobile"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "dir": "ltr", "placeholder": "09121234567"})
        self.fields["mobile"].help_text = "شماره‌ای را وارد کنید که اکنون به آن دسترسی دارید." if lang == "fa" else "Use a mobile number you can access now."
        enhance_form_accessibility(self, autocomplete={
            "first_name": "given-name", "last_name": "family-name", "email": "email",
            "mobile": "tel", "password1": "new-password", "password2": "new-password",
        })

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split())

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split())

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        domain = email.rsplit("@", 1)[-1]
        if domain == "gmail.con":
            message = (
                "پسوند ایمیل اشتباه است؛ منظورتان gmail.com است؟"
                if self.lang == "fa" else
                "The email domain looks mistyped; did you mean gmail.com?"
            )
            raise forms.ValidationError(message, code="mistyped_email_domain")
        existing = User.objects.filter(email__iexact=email).first()
        if existing and (existing.is_staff or existing.is_superuser):
            raise forms.ValidationError(
                "این حساب فقط توسط مدیر ارشد قابل بازیابی است."
                if self.lang == "fa" else "This account can only be recovered by a super administrator."
            )
        if existing and existing.is_active:
            raise forms.ValidationError(
                "این ایمیل قبلاً ثبت شده است؛ از صفحه ورود استفاده کنید."
                if self.lang == "fa" else "This email is already registered. Please sign in."
            )
        self.resume_user = existing
        return email

    def clean_mobile(self):
        try:
            mobile = normalize_iran_mobile(self.cleaned_data["mobile"])
        except ValueError:
            raise forms.ValidationError(
                "شماره موبایل معتبر نیست؛ مانند 09121234567 وارد کنید."
                if self.lang == "fa" else "Enter a valid Iranian mobile number, such as 09121234567."
            )
        existing = User.objects.filter(mobile=mobile).first()
        if existing and (existing.is_staff or existing.is_superuser):
            raise forms.ValidationError(
                "این شماره به حساب مدیریتی متصل است."
                if self.lang == "fa" else "This number belongs to a management account."
            )
        if existing and existing.is_active:
            raise forms.ValidationError(
                "این شماره قبلاً ثبت شده است؛ از صفحه ورود استفاده کنید."
                if self.lang == "fa" else "This number is already registered. Please sign in."
            )
        if existing:
            email = self.cleaned_data.get("email", "")
            if existing.email.casefold() != email.casefold():
                raise forms.ValidationError(
                    "این شماره به حساب دیگری متصل است؛ با پشتیبانی تماس بگیرید."
                    if self.lang == "fa" else "This number belongs to another account. Contact support."
                )
            self.resume_user = existing
        return mobile

    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        if getattr(self, "resume_user", None):
            exclude.update(["email", "mobile", "username"])
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as error:
            self._update_errors(error)

    def clean(self):
        cleaned = super().clean()
        existing = getattr(self, "resume_user", None)
        password = cleaned.get("password1")
        if existing:
            # `is_active=False` is also used for administrative suspension.  A
            # public signup may only resume an account left by the retired OTP
            # flow, never an arbitrary deactivated customer account.
            resumable = (
                existing.last_login is None
                and existing.phone_verifications.filter(used_at__isnull=True).exists()
                and not existing.assessment_orders.exists()
                and not existing.exam_attempts.exists()
            )
            if not resumable:
                raise forms.ValidationError(
                    "این حساب قابل فعال‌سازی از ثبت‌نام نیست؛ وارد شوید، رمز را بازیابی کنید یا با پشتیبانی تماس بگیرید."
                    if self.lang == "fa" else
                    "This account cannot be reactivated through signup. Sign in, reset the password, or contact support.",
                    code="account_not_resumable",
                )
        if existing and password and not existing.check_password(password):
            raise forms.ValidationError(
                "برای بازیابی ثبت‌نام نیمه‌تمام، همان رمز عبور قبلی را وارد کنید؛ در صورت فراموشی از بازیابی رمز استفاده کنید."
                if self.lang == "fa" else
                "To recover an interrupted registration, enter the existing password or use password recovery.",
                code="legacy_account_password_mismatch",
            )
        return cleaned

    def save(self, commit=True):
        user = getattr(self, "resume_user", None) or super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = user.email
        user.mobile = self.cleaned_data["mobile"]
        user.preferred_language = self.lang
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if not getattr(self, "resume_user", None):
            user.set_password(self.cleaned_data["password1"])
        # Signup no longer waits on an SMS code: the account is usable immediately.
        user.is_active = True
        if commit:
            user.save()
        return user


class PhoneVerificationForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=6)

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["code"].label = "کد تأیید ۶ رقمی" if lang == "fa" else "6-digit verification code"
        self.fields["code"].widget.attrs.update({
            "inputmode": "numeric", "autocomplete": "one-time-code", "pattern": "[0-9۰-۹]{6}",
            "dir": "ltr", "placeholder": "------", "class": "otp-input",
        })
        enhance_form_accessibility(self, autocomplete={"code": "one-time-code"})

    def clean_code(self):
        import unicodedata
        value = "".join(str(unicodedata.digit(ch)) for ch in self.cleaned_data["code"] if ch.isdecimal())
        if len(value) != 6:
            raise forms.ValidationError("کد باید دقیقاً ۶ رقم باشد." if self.lang == "fa" else "The code must contain exactly 6 digits.")
        return value


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField()

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ایمیل" if lang == "fa" else "Email"
        self.fields["password"].label = "رمز عبور" if lang == "fa" else "Password"
        enhance_form_accessibility(self, autocomplete={"username": "email", "password": "current-password"})


class ResendVerificationForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "ایمیل" if lang == "fa" else "Email"
        enhance_form_accessibility(self, autocomplete={"email": "email"})

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class ProfileIdentityForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "نام" if lang == "fa" else "First name"
        self.fields["last_name"].label = "نام خانوادگی" if lang == "fa" else "Last name"
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        enhance_form_accessibility(self, autocomplete={"first_name": "given-name", "last_name": "family-name"})

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split())

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split())
