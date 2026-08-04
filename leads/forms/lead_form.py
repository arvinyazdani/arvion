from django import forms
from leads.models import Lead

class LeadForm(forms.ModelForm):
    """
    فرم ثبت درخواست (Lead) — برای صفحه تماس با ما
    """

    def __init__(self, *args, **kwargs):
        lang = kwargs.pop("lang", "fa")
        super().__init__(*args, **kwargs)
        if lang == 'fa':
            self.fields['name'].label = "نام شما"
            self.fields['email_or_telegram'].label = "ایمیل یا تلگرام"
            self.fields['phone'].label = "شماره تماس"
            self.fields['request_type'].label = "نوع درخواست"
            self.fields['message'].label = "متن پیام"

            self.fields['name'].widget.attrs['placeholder'] = "مثلاً: علی احمدی"
            self.fields['email_or_telegram'].widget.attrs['placeholder'] = "ایمیل یا آیدی تلگرام"
            self.fields['phone'].widget.attrs['placeholder'] = "شماره تماس (اختیاری)"
            self.fields['message'].widget.attrs['placeholder'] = "متن پیام خود را وارد کنید"
            self.fields['request_type'].choices = [
                ("project", "درخواست پروژه"),
                ("training", "درخواست آموزش"),
                ("other", "سایر"),
            ]
        else:
            self.fields['name'].label = "Your Name"
            self.fields['email_or_telegram'].label = "Email or Telegram"
            self.fields['phone'].label = "Phone Number"
            self.fields['request_type'].label = "Request Type"
            self.fields['message'].label = "Message"

            self.fields['name'].widget.attrs['placeholder'] = "e.g. Ali Ahmadi"
            self.fields['email_or_telegram'].widget.attrs['placeholder'] = "Email or Telegram handle"
            self.fields['phone'].widget.attrs['placeholder'] = "Phone number (optional)"
            self.fields['message'].widget.attrs['placeholder'] = "Write your message here..."
            self.fields['request_type'].choices = [
                ("project", "Project request"),
                ("training", "Training request"),
                ("other", "Other"),
            ]

    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Invalid submission.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 12:
            raise forms.ValidationError("پیام باید حداقل ۱۲ کاراکتر باشد.")
        return message

    class Meta:
        model = Lead
        fields = ["name", "email_or_telegram", "phone", "request_type", "message", "website"]
        widgets = {
            "request_type": forms.Select(attrs={"class": "form-select"}),
        }
