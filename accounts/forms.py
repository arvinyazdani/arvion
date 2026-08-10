from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        labels = {
            "fa": {"first_name": "نام", "last_name": "نام خانوادگی", "email": "ایمیل", "password1": "رمز عبور", "password2": "تکرار رمز عبور"},
            "en": {"first_name": "First name", "last_name": "Last name", "email": "Email", "password1": "Password", "password2": "Confirm password"},
        }[lang]
        for name, label in labels.items():
            self.fields[name].label = label
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

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
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = user.email
        user.preferred_language = self.lang
        user.is_active = False
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField()

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ایمیل" if lang == "fa" else "Email"
        self.fields["password"].label = "رمز عبور" if lang == "fa" else "Password"


class ResendVerificationForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "ایمیل" if lang == "fa" else "Email"

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

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split())

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split())
