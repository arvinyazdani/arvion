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
from .models import CrmOrder


class CrmOrderCreateView(LanguageViewMixin, FormView):
    template_name = "crm_orders/order_wizard.html"
    form_class = CrmOrderForm

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
