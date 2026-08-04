from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from core.views.lang import LanguageViewMixin

from .models import Exam, Order
from .services import verify_sandbox_payment


class ExamListView(LanguageViewMixin, ListView):
    model = Exam
    template_name = "assessments/list.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(is_active=True)


class ExamDetailView(LanguageViewMixin, DetailView):
    model = Exam
    template_name = "assessments/detail.html"
    context_object_name = "exam"

    def get_queryset(self):
        return Exam.objects.filter(is_active=True)


class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request, slug):
        exam = get_object_or_404(Exam, slug=slug, is_active=True)
        since = timezone.now() - timedelta(hours=24)
        recent_count = Order.objects.filter(
            user=request.user,
            exam=exam,
            created_at__gte=since,
            status__in=("pending", "paid"),
        ).count()
        if recent_count >= settings.ASSESSMENT_ATTEMPTS_PER_DAY:
            messages.error(request, "سقف خرید روزانه این آزمون تکمیل شده است.")
            return redirect(f"{exam.get_absolute_url()}?lang={request.GET.get('lang', 'fa')}")
        order = Order.objects.create(
            user=request.user,
            exam=exam,
            amount_irr=exam.price_irr,
            gateway=settings.PAYMENT_GATEWAY,
        )
        return redirect(f"{reverse('assessments:checkout', kwargs={'pk': order.pk})}?lang={request.GET.get('lang', 'fa')}")


class CheckoutView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    model = Order
    template_name = "assessments/checkout.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("exam")


class SandboxPayView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not settings.DEBUG or settings.PAYMENT_GATEWAY != "sandbox":
            raise Http404
        order = get_object_or_404(Order, pk=pk, user=request.user)
        order, created = verify_sandbox_payment(order.pk)
        lang = request.GET.get("lang", "fa")
        if created:
            messages.success(request, "پرداخت آزمایشی تأیید و مجوز آزمون صادر شد." if lang == "fa" else "Test payment verified and access granted.")
        return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
