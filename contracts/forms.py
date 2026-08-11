from django import forms

from core.sms.backends import normalize_iran_mobile
from .models import ContractProposal


class ProposalForm(forms.ModelForm):
    class Meta:
        model = ContractProposal
        fields = ("title", "customer_name", "customer_phone", "customer_email", "client_details", "project_title", "project_scope", "amount_irr", "payment_terms", "delivery_terms")
        widgets = {"client_details": forms.Textarea(attrs={"rows": 3}), "project_scope": forms.Textarea(attrs={"rows": 6}), "payment_terms": forms.Textarea(attrs={"rows": 3})}

    def clean_customer_phone(self):
        return normalize_iran_mobile(self.cleaned_data["customer_phone"])


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
        super().__init__(*args, **kwargs)
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
