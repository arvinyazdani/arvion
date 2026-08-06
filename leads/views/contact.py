from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView

from core.views.lang import LanguageViewMixin
from leads.forms import LeadForm
from leads.models import Lead
from services.models import Service


class LeadCreateView(LanguageViewMixin, FormView):
    template_name = "leads/contact.html"
    form_class = LeadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        service_slug = self.request.GET.get("service", "")
        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service:
            initial["service"] = service
            initial["request_type"] = {
                "corporate-website-design": "website", "custom-web-application": "webapp",
                "ecommerce-platform": "ecommerce", "maintenance-and-growth": "support",
            }.get(service.slug, "consultation")
        return initial

    def form_valid(self, form):
        client_ip = self.request.META.get("REMOTE_ADDR", "unknown")
        limit_key = f"lead-submit:{client_ip}"
        if not cache.add(limit_key, True, settings.LEAD_RATE_LIMIT_SECONDS):
            form.add_error(None, "لطفاً کمی صبر کنید و دوباره تلاش کنید." if self.lang == "fa" else "Please wait before submitting another enquiry.")
            return self.form_invalid(form)
        lead = form.save(commit=False)
        lead.privacy_accepted_at = timezone.now()
        lead.save()
        self.lead = lead
        send_mail(
            subject=f"New Rvion enquiry [{lead.tracking_code}]",
            message=(
                f"Reference: {lead.tracking_code}\nName: {lead.name}\nBusiness: {lead.business_name or '-'}\n"
                f"Contact: {lead.email_or_telegram}\nPhone: {lead.phone or '-'}\nPreferred: {lead.preferred_contact}\n"
                f"Type: {lead.request_type}\nService: {lead.service or '-'}\nBudget: {lead.budget_range}\n"
                f"Timeline: {lead.timeline}\nWebsite: {lead.website_url or '-'}\n\n{lead.message}"
            ),
            from_email=None,
            recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
            fail_silently=True,
        )
        messages.success(self.request, "درخواست شما با موفقیت ثبت شد." if self.lang == "fa" else "Your enquiry was submitted successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return f"{reverse('leads:thanks', kwargs={'code': self.lead.tracking_code})}?lang={self.lang}"


class LeadThanksView(LanguageViewMixin, DetailView):
    model = Lead
    template_name = "leads/thanks.html"
    context_object_name = "lead"
    slug_field = "tracking_code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return Lead.objects.select_related("service")
