# leads/views/contact.py
# فرم کلاسی با ارسال AJAX (HTMX) و پیام موفقیت
from django.views.generic import FormView
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.contrib import messages
from leads.forms import LeadForm
from core.views.lang import LanguageViewMixin

# نمایش فرم تماس و ثبت Lead
class LeadCreateView(LanguageViewMixin, FormView):
    """
    صفحه‌ی تماس: ثبت Lead و ارسال نوتیف (در dev به console).
    """
    template_name = "leads/contact.html"
    form_class = LeadForm
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def get_success_url(self):
        lang = self.request.GET.get("lang", "fa")
        return f"/contact/?lang={lang}&submitted=1"

    def form_valid(self, form):
        client_ip = self.request.META.get("REMOTE_ADDR", "unknown")
        limit_key = f"lead-submit:{client_ip}"
        if not cache.add(limit_key, True, settings.LEAD_RATE_LIMIT_SECONDS):
            form.add_error(None, "لطفاً کمی صبر کنید و دوباره تلاش کنید.")
            return self.form_invalid(form)
        lead = form.save()
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
            recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
            fail_silently=True,
        )
        messages.success(self.request, "پیام شما با موفقیت ثبت شد." if self.lang == "fa" else "Your message was sent successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
