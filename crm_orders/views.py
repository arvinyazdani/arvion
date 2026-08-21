from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, FormView
from django.views.decorators.cache import never_cache

from accounts.security import client_address, normalized_fingerprint
from core.i18n_numbers import persian_digits
from core.views.lang import LanguageViewMixin
from .forms import CrmOrderForm
from .models import CrmOrder, CrmSpecialistDiscovery
from .specialist import SECTIONS, is_specialist_discovery_complete
from .specialist_forms import SpecialistDiscoveryForm
from django.shortcuts import get_object_or_404, render


@method_decorator(never_cache, name="dispatch")
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

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "LANGUAGE_CODE", "fa") == "en":
            return redirect("/fa/crm-order/")
        return super().dispatch(request, *args, **kwargs)

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


@method_decorator(never_cache, name="dispatch")
class CrmOrderThanksView(LanguageViewMixin, DetailView):
    model = CrmOrder
    template_name = "crm_orders/thanks.html"
    context_object_name = "crm_order"
    slug_field = "tracking_code"
    slug_url_kwarg = "code"


@never_cache
def specialist_discovery(request, code, section=None):
    room_token = request.GET.get("room", "")
    room_proposal = None
    if room_token:
        from contracts.models import ContractProposal
        order = get_object_or_404(CrmOrder, tracking_code=code)
        room_proposal = get_object_or_404(ContractProposal, token=room_token, crm_order=order)
        room_version = room_proposal.versions.filter(number=room_proposal.current_version).first()
        expected_phone = (room_version.snapshot or {}).get("customer_phone", room_proposal.customer_phone) if room_version else ""
        if not room_version or request.session.get(f"contract-access:{room_version.pk}") != expected_phone:
            return redirect("contracts:contract_access", token=room_token)
        discovery, _ = CrmSpecialistDiscovery.objects.get_or_create(order=order)
    else:
        # A staff session must not change the meaning of a customer-facing
        # token URL. Resolve the private token first, then allow authorized
        # staff to use the internal tracking code as a fallback.
        discovery = (
            CrmSpecialistDiscovery.objects.select_related("order")
            .filter(token=code)
            .first()
        )
        if discovery:
            order = discovery.order
        elif request.user.is_authenticated and request.user.is_staff and (
            request.user.is_superuser or request.user.has_perm("crm_orders.view_crmorder")
        ):
            order = get_object_or_404(CrmOrder, tracking_code=code)
            discovery, _ = CrmSpecialistDiscovery.objects.get_or_create(order=order)
        else:
            discovery = get_object_or_404(
                CrmSpecialistDiscovery.objects.select_related("order"), token=code,
            )
            order = discovery.order
    keys = [item[0] for item in SECTIONS]
    section = section or keys[0]
    if section not in keys:
        return redirect("crm_orders:specialist", code=code)
    index = keys.index(section)
    form = SpecialistDiscoveryForm(request.POST or None, section_key=section, initial=discovery.answers.get(section, {}))
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            # Use the same proposal -> discovery lock order as final contract
            # acceptance.  This prevents a last-millisecond answer edit from
            # racing with the evidence snapshot recorded on acceptance.
            from contracts.models import ContractProposal
            linked_proposals = list(
                ContractProposal.objects.select_for_update()
                .filter(crm_order=order)
                .order_by("pk")
            )
            if any(item.status == "accepted" for item in linked_proposals):
                raise PermissionDenied
            locked = CrmSpecialistDiscovery.objects.select_for_update().get(pk=discovery.pk)
            answers = dict(locked.answers)
            answers[section] = form.cleaned_data
            locked.answers = answers
            update_fields = ["answers", "updated_at"]
            completed = is_specialist_discovery_complete(locked)
            if completed:
                locked.status = "submitted"
                update_fields.insert(1, "status")
            elif locked.status != "draft":
                locked.status = "draft"
                update_fields.insert(1, "status")
            locked.save(update_fields=update_fields)
            discovery = locked
        if completed:
            if room_proposal:
                return redirect("contracts:public_contract", token=room_token)
            return redirect("crm_orders:specialist_done", code=code)
        next_key = keys[index + 1] if index < len(keys) - 1 else next(
            key for key in keys if key not in discovery.answers or not discovery.answers[key]
        )
        url = reverse("crm_orders:specialist_section", kwargs={"code": code, "section": next_key})
        return redirect(f"{url}?room={room_token}" if room_token else url)
    previous_url = ""
    if index:
        previous_url = reverse(
            "crm_orders:specialist_section",
            kwargs={"code": code, "section": keys[index - 1]},
        )
        if room_token:
            previous_url = f"{previous_url}?room={room_token}"
    section_steps = [
        {
            "key": item[0],
            "title": item[1],
            "number": persian_digits(step_index + 1),
            "state": "active" if step_index == index else "done" if step_index < index else "upcoming",
        }
        for step_index, item in enumerate(SECTIONS)
    ]
    return render(
        request,
        "crm_orders/specialist_wizard.html",
        {
            "order": order,
            "discovery": discovery,
            "form": form,
            "section": next(item for item in SECTIONS if item[0] == section),
            "sections": SECTIONS,
            "section_steps": section_steps,
            "index": index,
            "total": len(keys),
            "current_step": persian_digits(index + 1),
            "total_steps": persian_digits(len(keys)),
            "previous_url": previous_url,
            "room_proposal": room_proposal,
        },
    )


@never_cache
def specialist_done(request, code):
    discovery = (
        CrmSpecialistDiscovery.objects.select_related("order")
        .filter(token=code)
        .first()
    )
    if discovery:
        order = discovery.order
    elif request.user.is_authenticated and request.user.is_staff and (
        request.user.is_superuser or request.user.has_perm("crm_orders.view_crmorder")
    ):
        order = get_object_or_404(CrmOrder, tracking_code=code)
        discovery = get_object_or_404(CrmSpecialistDiscovery, order=order)
    else:
        discovery = get_object_or_404(
            CrmSpecialistDiscovery.objects.select_related("order"), token=code,
        )
        order = discovery.order
    return render(request, "crm_orders/specialist_done.html", {"order": order, "discovery": discovery})
