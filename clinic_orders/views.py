from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView, FormView

from accounts.security import client_address, normalized_fingerprint
from core.views.lang import LanguageViewMixin
from .forms import ClinicOrderForm
from .models import ClinicOrder


@method_decorator(never_cache, name="dispatch")
class ClinicOrderCreateView(LanguageViewMixin, FormView):
    template_name = "clinic_orders/order_wizard.html"
    form_class = ClinicOrderForm
    field_steps = {
        **dict.fromkeys(("clinic_name", "clinic_type", "city", "branch_count", "specialties", "practitioner_count", "website", "contact_name", "job_title", "work_email", "phone"), 1),
        **dict.fromkeys(("primary_goals", "target_audiences", "current_channels", "current_process", "main_pain_points", "success_metrics"), 2),
        **dict.fromkeys(("hosting_preference", "delivery_strategy", "budget_range", "expected_timeline"), 3),
        **dict.fromkeys(("visit_modes", "schedule_model", "appointment_rules", "intake_requirements", "reminder_channels", "waitlist_requirement", "practitioner_features", "patient_account_features"), 4),
        **dict.fromkeys(("payment_methods", "pricing_model", "insurance_requirement", "cancellation_refund_rules", "financial_documents"), 5),
        **dict.fromkeys(("content_types", "content_access", "publishing_workflow", "media_requirements", "webinar_features", "webinar_platform", "expected_live_attendees", "system_roles", "record_scope", "notification_channels", "integration_types", "required_integrations", "migration_sources", "security_requirements", "requested_services", "decision_process", "additional_notes", "privacy_accept"), 6),
    }

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "LANGUAGE_CODE", "fa") == "en":
            return redirect("/fa/clinic-order/")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        fields = [name for name in form.errors if name != "__all__"]
        step = min((self.field_steps.get(name, 1) for name in fields), default=1)
        return self.render_to_response(self.get_context_data(form=form, error_step=step, error_count=sum(len(e) for e in form.errors.values())))

    def form_valid(self, form):
        key = f"clinic-order:{normalized_fingerprint(client_address(self.request))}"
        if not cache.add(key, True, 300):
            form.add_error(None, "درخواست دیگری به‌تازگی ثبت شده است؛ لطفاً پنج دقیقه بعد تلاش کنید.")
            return self.form_invalid(form)
        order = form.save(commit=False)
        order.privacy_accepted_at = timezone.now()
        order.save()
        self.order = order
        send_mail(
            f"New clinic website discovery [{order.tracking_code}]",
            f"Clinic: {order.clinic_name}\nContact: {order.contact_name}\nEmail: {order.work_email}\nPhone: {order.phone}\nBudget: {order.budget_range}\nTimeline: {order.expected_timeline}",
            None, [settings.CONTACT_NOTIFICATION_EMAIL], fail_silently=True,
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("clinic_orders:thanks", kwargs={"code": self.order.tracking_code})


@method_decorator(never_cache, name="dispatch")
class ClinicOrderThanksView(LanguageViewMixin, DetailView):
    model = ClinicOrder
    template_name = "clinic_orders/thanks.html"
    context_object_name = "clinic_order"
    slug_field = "tracking_code"
    slug_url_kwarg = "code"
