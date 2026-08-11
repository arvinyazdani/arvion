from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User
from accounts.staff_roles import STAFF_ROLES, group_name, sync_staff_role_groups


ROLE_CHOICES = [(key, value["label_fa"]) for key, value in STAFF_ROLES.items()]


class StaffCreateForm(forms.Form):
    first_name = forms.CharField(label="نام", max_length=150)
    last_name = forms.CharField(label="نام خانوادگی", max_length=150)
    email = forms.EmailField(label="ایمیل کاری")
    password = forms.CharField(label="رمز عبور موقت", widget=forms.PasswordInput, validators=[validate_password])
    roles = forms.MultipleChoiceField(label="مسئولیت‌ها", choices=ROLE_CHOICES, widget=forms.CheckboxSelectMultiple)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("حسابی با این ایمیل وجود دارد.")
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

    def __init__(self, *args, user, **kwargs):
        self.staff_user = user
        initial = kwargs.setdefault("initial", {})
        initial["roles"] = [key for key in STAFF_ROLES if user.groups.filter(name=group_name(key)).exists()]
        initial["is_staff"] = user.is_staff
        super().__init__(*args, **kwargs)

    def save(self):
        groups = sync_staff_role_groups()
        role_names = [group_name(key) for key in STAFF_ROLES]
        self.staff_user.groups.remove(*self.staff_user.groups.filter(name__in=role_names))
        self.staff_user.groups.add(*[groups[role] for role in self.cleaned_data["roles"]])
        self.staff_user.is_staff = self.cleaned_data["is_staff"]
        self.staff_user.save(update_fields=["is_staff"])
        return self.staff_user
