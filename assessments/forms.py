from django import forms

from .models import AttemptResult, Order, SupportTicket


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
