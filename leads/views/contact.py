# leads/views/contact.py
# فرم کلاسی با ارسال AJAX (HTMX) و پیام موفقیت
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.shortcuts import render
from leads.forms import LeadForm

class LeadCreateView(FormView):
    """
    صفحه‌ی تماس: ثبت Lead و ارسال نوتیف (در dev به console).
    """
    template_name = "leads/contact.html"
    form_class = LeadForm
    success_url = reverse_lazy("leads:thanks")

    def form_valid(self, form):
        lead = form.save()
        # ایمیل کنسولی در محیط dev
        send_mail(
            subject="New Lead — Arvion",
            message=(
                f"Name: {lead.name}\nContact: {lead.email_or_telegram}\n"
                f"Type: {lead.request_type}\nMessage:\n{lead.message}"
            ),
            from_email=None,
            recipient_list=["owner@example.com"],
        )
        # اگر HTMX باشه، پارتشیال موفقیت برگردون
        if self.request.headers.get("HX-Request"):
            return render(self.request, "leads/_thanks_partial.html")
        return super().form_valid(form)

class LeadThanksView(TemplateView):
    """صفحه‌ی تشکر بعد از ارسال فرم (Fallback غیر HTMX)."""
    template_name = "leads/thanks.html"