from uuid import UUID

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
from projects.models import DemoSelection


def _session_demo_selection(request):
    """Return a selected demo only when its public token is well formed and session-bound."""
    token = request.GET.get("demo", "")
    if not token:
        return None
    try:
        UUID(token)
    except (TypeError, ValueError, AttributeError):
        return None
    return DemoSelection.objects.select_related("template").filter(
        public_token=token,
        session_key=request.session.session_key,
    ).first()


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
        selection = _session_demo_selection(self.request)
        if selection:
            initial["request_type"] = {
                "ecommerce": "ecommerce", "restaurant": "website", "portfolio": "website",
                "corporate": "website", "clinic": "webapp", "education": "webapp",
            }.get(selection.template.category, "consultation")
            initial["message"] = (
                f"نمونه انتخاب‌شده: {selection.template.title_fa}\n"
                f"سبک: {selection.selections.get('personality', '—')} · رنگ: {selection.selections.get('theme', '—')}\n"
                "هدف و جزئیات پروژه را اینجا کامل می‌کنم: "
            ) if self.lang == "fa" else (
                f"Selected demo: {selection.template.title_en}\n"
                "Project goals and details: "
            )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # A `demo` token in the URL that cannot be resolved for this session —
        # wrong session, wrong device, expired, or simply invalid — must not
        # block or explain itself (that would leak whether the token exists
        # at all); it just surfaces a neutral, non-blocking notice.
        selection = _session_demo_selection(self.request)
        if self.request.GET.get("demo", "") and not selection:
            context["demo_link_invalid"] = True
        elif selection:
            # Non-secret display data only — never public_token or
            # session_key — so the client-side draft can keep a same-device
            # pointer to this exact demo without needing to hold onto the
            # URL itself (see wizard-engine.js's dedicated demo context).
            context["demo_context"] = {
                "label": selection.template.title_fa if self.lang == "fa" else selection.template.title_en,
            }
        return context

    def form_valid(self, form):
        client_ip = self.request.META.get("REMOTE_ADDR", "unknown")
        limit_key = f"lead-submit:{client_ip}"
        if not cache.add(limit_key, True, settings.LEAD_RATE_LIMIT_SECONDS):
            form.add_error(None, "لطفاً کمی صبر کنید و دوباره تلاش کنید." if self.lang == "fa" else "Please wait before submitting another enquiry.")
            return self.form_invalid(form)
        lead = form.save(commit=False)
        selection = _session_demo_selection(self.request)
        if selection:
            lead.demo_selection = selection
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
