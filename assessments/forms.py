from datetime import datetime, timedelta

from django import forms

from django.utils import timezone

from core.i18n_numbers import normalize_digits

from .models import AttemptResult, ManualPaymentSubmission, Order, SupportTicket


class ManualPaymentSubmissionForm(forms.ModelForm):
    payment_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    payment_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    accept_terms = forms.BooleanField()

    class Meta:
        model = ManualPaymentSubmission
        fields = ("payer_name", "reference_number", "note")
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "fa": ("نام واریزکننده", "شماره پیگیری بانکی", "تاریخ پرداخت", "ساعت پرداخت", "توضیح اختیاری", "شرایط آزمون را خوانده‌ام و می‌پذیرم."),
            "en": ("Payer name", "Bank reference number", "Payment date", "Payment time", "Optional note", "I have read and accept the assessment terms."),
        }["fa" if lang == "fa" else "en"]
        for field, label in zip(("payer_name", "reference_number", "payment_date", "payment_time", "note", "accept_terms"), labels):
            self.fields[field].label = label

    def clean_reference_number(self):
        value = normalize_digits(self.cleaned_data["reference_number"]).strip().replace(" ", "")
        if not value.isalnum() or len(value) < 4:
            raise forms.ValidationError("شماره پیگیری معتبر وارد کنید.")
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_date") and cleaned.get("payment_time"):
            paid_at = timezone.make_aware(
                datetime.combine(cleaned["payment_date"], cleaned["payment_time"]),
                timezone.get_current_timezone(),
            )
            if paid_at > timezone.now() + timedelta(minutes=5):
                self.add_error("payment_time", "زمان پرداخت نمی‌تواند در آینده باشد.")
            elif paid_at < timezone.now() - timedelta(days=30):
                self.add_error("payment_date", "پرداخت‌های قدیمی‌تر از ۳۰ روز را با پشتیبانی پیگیری کنید.")
            cleaned["paid_at"] = paid_at
        return cleaned


class SupportTicketForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = SupportTicket
        fields = ("category", "order", "result", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, user, lang="fa", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["order"].queryset = Order.objects.filter(user=user).select_related("exam")
        self.fields["result"].queryset = AttemptResult.objects.filter(attempt__user=user).select_related("attempt__exam")
        self.fields["order"].label_from_instance = lambda item: f"{item.exam.title_fa if lang == 'fa' else item.exam.title_en} · {str(item.pk)[:8].upper()}"
        self.fields["result"].label_from_instance = lambda item: f"{item.attempt.exam.title_fa if lang == 'fa' else item.attempt.exam.title_en} · {item.percentage:.0f}/100"
        if lang == "fa":
            self.fields["category"].label = "موضوع درخواست"
            self.fields["category"].choices = (("", "انتخاب کنید"), ("payment", "پرداخت"), ("result_review", "بررسی نتیجه"), ("certificate", "گواهی"), ("technical", "مشکل فنی"), ("other", "سایر"))
            self.fields["order"].label = "سفارش مرتبط (اختیاری)"
            self.fields["result"].label = "نتیجه مرتبط (اختیاری)"
            self.fields["subject"].label = "عنوان"
            self.fields["message"].label = "توضیحات کامل"
        else:
            self.fields["category"].label = "Request category"
            self.fields["order"].label = "Related order (optional)"
            self.fields["result"].label = "Related result (optional)"
            self.fields["subject"].label = "Subject"
            self.fields["message"].label = "Full details"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Invalid submission")
        if cleaned.get("order") and cleaned.get("result"):
            raise forms.ValidationError(
                "فقط یکی از سفارش یا نتیجه را انتخاب کنید."
                if self.lang == "fa" else "Choose either an order or a result, not both."
            )
        return cleaned
