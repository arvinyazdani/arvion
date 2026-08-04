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

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

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
