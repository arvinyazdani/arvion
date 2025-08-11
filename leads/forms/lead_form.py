# leads/forms/lead_form.py
from django import forms
from leads.models import Lead

class LeadForm(forms.ModelForm):
    """
    فرم ثبت درخواست (Lead) — برای صفحه Contact
    """
    class Meta:
        model = Lead
        fields = ["name", "email_or_telegram", "request_type", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }
        