from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView

from accounts.security import client_address, normalized_fingerprint
from core.views.lang import LanguageViewMixin
from .forms import CrmOrderForm
from .models import CrmOrder, CrmSpecialistDiscovery
from .specialist import SECTIONS
from .specialist_forms import SpecialistDiscoveryForm
from django.shortcuts import get_object_or_404, render


class CrmOrderCreateView(LanguageViewMixin, FormView):
    template_name = "crm_orders/order_wizard.html"
    form_class = CrmOrderForm

    field_steps = {
        **dict.fromkeys(("organization_name", "industry", "organization_size", "website", "contact_name", "job_title", "work_email", "phone"), 1),
        **dict.fromkeys(("primary_goals", "departments", "customer_types", "lead_sources", "crm_user_count", "current_data_sources", "current_tools", "current_process", "main_pain_points", "success_metrics"), 2),
        **dict.fromkeys(("delivery_strategy", "budget_range", "expected_timeline"), 3),
        **dict.fromkeys(("required_capabilities", "assignment_model", "notification_channels", "critical_workflows", "correspondence_features", "ai_use_cases", "reports_needed", "permission_requirements"), 4),
        **dict.fromkeys(("mobile_requirement", "hosting_preference", "integration_types", "required_integrations", "migration_types", "migration_sources", "approximate_record_count", "audit_requirement", "security_requirements", "requested_services", "decision_process", "additional_notes", "privacy_accept"), 5),
    }

    def form_invalid(self, form):
        error_fields = [name for name in form.errors if name != "__all__"]
        error_step = min((self.field_steps.get(name, 1) for name in error_fields), default=1)
        return self.render_to_response(self.get_context_data(
            form=form, error_count=sum(len(errors) for errors in form.errors.values()), error_step=error_step,
        ))

    def form_valid(self, form):
        key = f"crm-order:{normalized_fingerprint(client_address(self.request))}"
        if not cache.add(key, True, 300):
            form.add_error(None, "درخواست دیگری به‌تازگی ثبت شده است؛ لطفاً پنج دقیقه بعد تلاش کنید.")
            return self.form_invalid(form)
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        self.order = order
        send_mail(
            f"New CRM discovery [{order.tracking_code}]",
            f"Organization: {order.organization_name}\nContact: {order.contact_name}\nEmail: {order.work_email}\nPhone: {order.phone}\nBudget: {order.budget_range}\nTimeline: {order.expected_timeline}",
            None, [settings.CONTACT_NOTIFICATION_EMAIL], fail_silently=True,
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("crm_orders:thanks", kwargs={"code": self.order.tracking_code})


class CrmOrderThanksView(LanguageViewMixin, DetailView):
    model = CrmOrder
    template_name = "crm_orders/thanks.html"
    context_object_name = "crm_order"
    slug_field = "tracking_code"
    slug_url_kwarg = "code"


def specialist_discovery(request, code, section=None):
    order = get_object_or_404(CrmOrder, tracking_code=code)
    room_token = request.GET.get("room", "")
    room_proposal = None
    if room_token:
        from contracts.models import ContractProposal
        room_proposal = get_object_or_404(ContractProposal, token=room_token, crm_order=order)
        room_version = room_proposal.versions.filter(number=room_proposal.current_version).first()
        if not room_version or request.session.get(f"contract-access:{room_version.pk}") != room_proposal.customer_phone:
            return redirect("contracts:contract_access", token=room_token)
    discovery, _ = CrmSpecialistDiscovery.objects.get_or_create(order=order)
    keys = [item[0] for item in SECTIONS]
    section = section or keys[0]
    if section not in keys:
        return redirect("crm_orders:specialist", code=code)
    index = keys.index(section)
    form = SpecialistDiscoveryForm(request.POST or None, section_key=section, initial=discovery.answers.get(section, {}))
    if request.method == "POST" and form.is_valid():
        answers = dict(discovery.answers)
        answers[section] = form.cleaned_data
        discovery.answers = answers
        if index == len(keys) - 1:
            discovery.status = "submitted"
            discovery.save(update_fields=["answers", "status", "updated_at"])
            if room_proposal:
                return redirect("contracts:public_contract", token=room_token)
            return redirect("crm_orders:specialist_done", code=code)
        discovery.save(update_fields=["answers", "updated_at"])
        url = reverse("crm_orders:specialist_section", kwargs={"code": code, "section": keys[index + 1]})
        return redirect(f"{url}?room={room_token}" if room_token else url)
    return render(request, "crm_orders/specialist_wizard.html", {"order": order, "discovery": discovery, "form": form, "section": next(item for item in SECTIONS if item[0] == section), "sections": SECTIONS, "index": index, "total": len(keys), "room_proposal": room_proposal})


def specialist_done(request, code):
    order = get_object_or_404(CrmOrder, tracking_code=code)
    discovery = get_object_or_404(CrmSpecialistDiscovery, order=order)
    return render(request, "crm_orders/specialist_done.html", {"order": order, "discovery": discovery})
