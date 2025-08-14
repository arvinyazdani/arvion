# leads/views/contact.py
# فرم کلاسی با ارسال AJAX (HTMX) و پیام موفقیت
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.shortcuts import render
from leads.forms import LeadForm

# نمایش فرم تماس و ثبت Lead
class LeadCreateView(FormView):
    """
    صفحه‌ی تماس: ثبت Lead و ارسال نوتیف (در dev به console).
    """
    template_name = "leads/contact.html"
    form_class = LeadForm
    def get_success_url(self):
        lang = self.request.GET.get("lang", "fa")
        return f"/contact/?lang={lang}&submitted=1"

    def form_valid(self, form):
        lead = form.save()
        # ایمیل کنسولی در محیط dev (شماره تلفن هم اضافه شد)
        send_mail(
            subject="New Lead — Arvion",
            message=(
                f"Name: {lead.name}\n"
                f"Email/Telegram: {lead.email_or_telegram}\n"
                f"Phone: {lead.phone}\n"
                f"Type: {lead.request_type}\n"
                f"Message:\n{lead.message}"
            ),
            from_email=None,
            recipient_list=["owner@example.com"],
        )
        # اگر HTMX باشه، پارتشیال موفقیت برگردون
        if self.request.headers.get("HX-Request"):
            return render(self.request, "leads/_thanks_partial.html")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "fa")  # پیش‌فرض: فارسی
        context["lang"] = lang
        return context