from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from core.views.lang import LanguageViewMixin

from .models import Attempt, AttemptQuestion, AttemptResult, Certificate, Choice, Exam, ExamEntitlement, IntegrityEvent, Order
from .services import ExamContentError, expire_if_needed, score_attempt, start_attempt, verify_sandbox_payment


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


class StartAttemptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        entitlement = get_object_or_404(ExamEntitlement, pk=pk, user=request.user)
        lang = request.GET.get("lang", "fa")
        if not request.user.email_verified:
            messages.error(request, "برای شروع آزمون باید ایمیل شما تأیید شده باشد.")
            return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
        try:
            attempt, _ = start_attempt(entitlement.pk, request.user)
        except ExamContentError:
            messages.error(request, "محتوای این آزمون هنوز آماده انتشار نیست." if lang == "fa" else "This assessment is not ready yet.")
            return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
        return redirect(f"{attempt.get_absolute_url()}?lang={lang}")


class AttemptView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    model = Attempt
    template_name = "assessments/attempt.html"
    context_object_name = "attempt"

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).select_related("exam", "version")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        expire_if_needed(attempt)
        if attempt.status != "in_progress":
            context["attempt_closed"] = True
            return context
        try:
            position = int(self.request.GET.get("q", attempt.current_position))
        except (TypeError, ValueError):
            position = attempt.current_position
        position = max(1, min(position, attempt.exam.question_count))
        item = get_object_or_404(
            AttemptQuestion.objects.select_related("question", "question__section", "selected_choice"),
            attempt=attempt,
            position=position,
        )
        choices = {choice.id: choice for choice in Choice.objects.filter(question=item.question)}
        context.update({
            "item": item,
            "ordered_choices": [choices[choice_id] for choice_id in item.choice_order],
            "position": position,
            "progress_percent": round(position / attempt.exam.question_count * 100),
            "previous_position": position - 1 if position > 1 else None,
            "next_position": position + 1 if position < attempt.exam.question_count else None,
            "answered_count": attempt.attempt_questions.filter(selected_choice__isnull=False).count(),
        })
        if attempt.current_position != position:
            attempt.current_position = position
            attempt.save(update_fields=["current_position", "updated_at"])
        return context


class SaveAnswerView(LoginRequiredMixin, View):
    def post(self, request, pk, item_pk):
        attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        if expire_if_needed(attempt) or attempt.status != "in_progress":
            return JsonResponse({"ok": False, "reason": "attempt_closed"}, status=409)
        item = get_object_or_404(AttemptQuestion, pk=item_pk, attempt=attempt)
        choice = get_object_or_404(Choice, pk=request.POST.get("choice"), question=item.question)
        item.selected_choice = choice
        item.answered_at = timezone.now()
        item.save(update_fields=["selected_choice", "answered_at"])
        return JsonResponse({"ok": True, "answered": attempt.attempt_questions.filter(selected_choice__isnull=False).count()})


class IntegrityEventView(LoginRequiredMixin, View):
    allowed_events = {"tab_hidden": 2, "window_blur": 1, "copy": 1, "paste": 1}
    deduction_limits = {"tab_hidden": 5, "window_blur": 5, "copy": 3, "paste": 3}

    @transaction.atomic
    def post(self, request, pk):
        attempt = get_object_or_404(
            Attempt.objects.select_for_update(), pk=pk, user=request.user, status="in_progress"
        )
        event_type = request.POST.get("event_type")
        if event_type not in self.allowed_events:
            return JsonResponse({"ok": False}, status=400)
        recent = IntegrityEvent.objects.filter(
            attempt=attempt, event_type=event_type,
            created_at__gte=timezone.now() - timedelta(seconds=10),
        ).exists()
        if recent:
            return JsonResponse({"ok": True, "deduplicated": True, "integrity_score": attempt.integrity_score})
        prior_count = IntegrityEvent.objects.filter(attempt=attempt, event_type=event_type).count()
        IntegrityEvent.objects.create(attempt=attempt, event_type=event_type)
        if prior_count < self.deduction_limits[event_type]:
            attempt.integrity_score = max(0, attempt.integrity_score - self.allowed_events[event_type])
            attempt.save(update_fields=["integrity_score", "updated_at"])
        return JsonResponse({"ok": True, "integrity_score": attempt.integrity_score})


class FinishAttemptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        lang = request.GET.get("lang", "fa")
        if attempt.status == "in_progress":
            attempt.status = "submitted"
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["status", "submitted_at", "updated_at"])
            result, _ = score_attempt(attempt.pk)
            messages.success(request, "آزمون با موفقیت تصحیح شد." if lang == "fa" else "Your assessment has been scored.")
            return redirect(f"{reverse('assessments:result', kwargs={'pk': result.pk})}?lang={lang}")
        if hasattr(attempt, "result"):
            return redirect(f"{reverse('assessments:result', kwargs={'pk': attempt.result.pk})}?lang={lang}")
        return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")


class ResultView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    model = AttemptResult
    template_name = "assessments/result.html"
    context_object_name = "result"

    def get_queryset(self):
        return AttemptResult.objects.filter(attempt__user=self.request.user).select_related(
            "attempt__exam", "certificate"
        ).prefetch_related("skill_results__skill")


class CertificateView(LanguageViewMixin, DetailView):
    model = Certificate
    template_name = "assessments/certificate.html"
    context_object_name = "certificate"
    slug_field = "verification_code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return Certificate.objects.filter(is_revoked=False).select_related(
            "result__attempt__user", "result__attempt__exam"
        )
