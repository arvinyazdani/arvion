from datetime import timedelta
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from core.i18n_numbers import normalize_digits
from core.views.lang import LanguageViewMixin
from management_portal.models import Customer, CustomerContact

from .emails import send_payment_confirmation_email, send_result_ready_email
from .forms import FinishAttemptForm, ManualPaymentSubmissionForm, SupportTicketForm
from .integrity import assess_event
from .models import Attempt, AttemptQuestion, AttemptResult, Certificate, Choice, Exam, ExamEntitlement, IntegrityEvent, ManualPaymentSubmission, Order, SupportTicket
from .services import AttemptLimitError, ExamContentError, finalize_expired_attempt, score_attempt, start_attempt, verify_sandbox_payment


logger = logging.getLogger(__name__)


def _customer_for_user(user):
    customer = CustomerContact.objects.filter(user=user).values_list("customer", flat=True).first()
    if customer:
        return Customer.objects.get(pk=customer)
    customer = Customer.objects.filter(email__iexact=user.email).first()
    if customer is None and user.mobile:
        customer = Customer.objects.filter(phone=user.mobile).first()
    if customer is None:
        customer = Customer.objects.create(name=user.get_full_name() or user.email, kind="person", phone=user.mobile or "", email=user.email)
    CustomerContact.objects.get_or_create(customer=customer, user=user, defaults={"name": user.get_full_name() or user.email, "phone": user.mobile or "", "email": user.email, "is_primary": not customer.contacts.filter(is_primary=True).exists()})
    return customer


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


class AssessmentTermsView(LanguageViewMixin, TemplateView):
    template_name = "assessments/terms.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["terms_version"] = settings.ASSESSMENT_TERMS_VERSION
        return context


class SupportTicketCreateView(LanguageViewMixin, LoginRequiredMixin, FormView):
    template_name = "assessments/support_form.html"
    form_class = SupportTicketForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user, "lang": self.lang})
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial.update({key: self.request.GET.get(key) for key in ("order", "result") if self.request.GET.get(key)})
        return initial

    def form_valid(self, form):
        recent_count = SupportTicket.objects.filter(
            user=self.request.user,
            created_at__gte=timezone.now() - timedelta(hours=1),
        ).count()
        if recent_count >= settings.ASSESSMENT_SUPPORT_TICKETS_PER_HOUR:
            messages.error(
                self.request,
                "تعداد درخواست‌های پشتیبانی شما در این ساعت به سقف مجاز رسیده است."
                if self.lang == "fa" else "You have reached the hourly support request limit.",
            )
            return redirect(f"{reverse('assessments:support_history')}?lang={self.lang}")
        ticket = form.save(commit=False)
        ticket.user = self.request.user
        ticket.save()
        subject = f"[Rvion Support #{ticket.pk}] {ticket.subject}"
        body = f"User: {ticket.user.email}\nCategory: {ticket.category}\nOrder: {ticket.order_id or '-'}\nResult: {ticket.result_id or '-'}\n\n{ticket.message}"
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFICATION_EMAIL])
        except Exception:
            logger.exception("Support notification email failed for ticket %s", ticket.pk)
        messages.success(self.request, "درخواست پشتیبانی ثبت شد." if self.lang == "fa" else "Your support request was submitted.")
        return redirect(f"{reverse('assessments:support_history')}?lang={self.lang}")


class SupportTicketListView(LanguageViewMixin, LoginRequiredMixin, ListView):
    template_name = "assessments/support_history.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).select_related("order__exam", "result__attempt__exam")


class CreateOrderView(LoginRequiredMixin, View):
    def get(self, request, slug):
        """Recover safely from legacy login redirects to this POST-only action."""
        exam = get_object_or_404(Exam, slug=slug, is_active=True)
        lang = request.GET.get("lang", "fa")
        messages.info(
            request,
            "برای ادامه خرید، دکمه خرید آزمون را بزنید."
            if lang == "fa" else
            "Select the assessment purchase button to continue.",
        )
        return redirect(f"{reverse('assessments:detail', kwargs={'slug': exam.slug})}?lang={lang}")

    def post(self, request, slug):
        exam = get_object_or_404(Exam, slug=slug, is_active=True)
        is_free = settings.ASSESSMENT_FREE_CHECKOUT
        customer = _customer_for_user(request.user)
        order, created = Order.objects.get_or_create(
            user=request.user, exam=exam, status="pending",
            defaults={
                "customer": customer,
                "subtotal_irr": exam.price_irr,
                "discount_irr": exam.price_irr if is_free else 0,
                "discount_percent": 100 if is_free else 0,
                "amount_irr": 0 if is_free else exam.price_irr,
                "gateway": "free" if is_free else settings.PAYMENT_GATEWAY,
            },
        )
        if order.customer_id is None:
            order.customer = customer
            order.save(update_fields=["customer", "updated_at"])
        if is_free and order.status == "pending" and (
            order.amount_irr or order.discount_percent != 100 or order.subtotal_irr != exam.price_irr
        ):
            order.subtotal_irr = exam.price_irr
            order.discount_irr = exam.price_irr
            order.discount_percent = 100
            order.amount_irr = 0
            order.gateway = "free"
            order.save(update_fields=["subtotal_irr", "discount_irr", "discount_percent", "amount_irr", "gateway", "updated_at"])
        elif (
            not is_free
            and not created
            and order.terms_accepted_at is None
            and not ManualPaymentSubmission.objects.filter(order=order).exists()
            and (
                order.subtotal_irr != exam.price_irr
                or order.amount_irr != exam.price_irr
                or order.discount_irr
                or order.discount_percent
                or order.gateway != settings.PAYMENT_GATEWAY
            )
        ):
            # An abandoned cart is not a price commitment. Refresh only orders
            # that have neither accepted terms nor submitted payment evidence.
            order.subtotal_irr = exam.price_irr
            order.discount_irr = 0
            order.discount_percent = 0
            order.amount_irr = exam.price_irr
            order.gateway = settings.PAYMENT_GATEWAY
            order.save(update_fields=["subtotal_irr", "discount_irr", "discount_percent", "amount_irr", "gateway", "updated_at"])
        return redirect(f"{reverse('assessments:checkout', kwargs={'pk': order.pk})}?lang={request.GET.get('lang', 'fa')}")


class CheckoutView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    model = Order
    template_name = "assessments/checkout.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("exam", "manual_payment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = getattr(self.object, "manual_payment", None)
        auto_approve_seconds = 0
        if submission and submission.status == "pending":
            deadline = submission.updated_at + timedelta(seconds=settings.PAYMENT_AUTO_APPROVE_SECONDS)
            auto_approve_seconds = max(0, int((deadline - timezone.now()).total_seconds()))
        context.update({
            "manual_payment_form": ManualPaymentSubmissionForm(
                instance=submission if submission and submission.status == "rejected" else None,
                lang=self.lang,
            ),
            "card_payment_number": settings.CARD_PAYMENT_NUMBER,
            "card_payment_holder": settings.CARD_PAYMENT_HOLDER,
            "payment_auto_approve_seconds": auto_approve_seconds,
        })
        return context


class ManualPaymentSubmitView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        lang = request.GET.get("lang", "fa")
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=pk, user=request.user, status="pending", gateway="card_transfer",
        )
        existing = ManualPaymentSubmission.objects.select_for_update().filter(order=order).first()
        if existing and existing.status != "rejected":
            messages.info(request, "اطلاعات پرداخت این سفارش قبلاً ثبت شده است." if lang == "fa" else "Payment details were already submitted.")
            return redirect(f"{reverse('assessments:checkout', kwargs={'pk': order.pk})}?lang={lang}")
        form = ManualPaymentSubmissionForm(
            request.POST, instance=existing if existing else None, lang=lang,
        )
        if not form.is_valid():
            messages.error(request, "اطلاعات پرداخت را اصلاح کنید." if lang == "fa" else "Please correct the payment details.")
            view = CheckoutView()
            view.setup(request, pk=pk)
            view.object = order
            view.lang = lang
            context = view.get_context_data(object=order)
            context["manual_payment_form"] = form
            return view.render_to_response(context)
        order.terms_version = settings.ASSESSMENT_TERMS_VERSION
        order.terms_accepted_at = timezone.now()
        order.save(update_fields=["terms_version", "terms_accepted_at", "updated_at"])
        submission = form.save(commit=False)
        submission.order = order
        submission.paid_at = form.cleaned_data["paid_at"]
        # A rejected receipt is edited in place (the one-to-one relation is
        # audit-preserving) and explicitly returned to the pending queue.
        submission.status = "pending"
        submission.reviewed_by = None
        submission.reviewed_at = None
        submission.review_note = ""
        submission.save()
        try:
            send_mail(
                f"[Rvion] پرداخت کارت‌به‌کارت جدید {str(order.pk)[:8]}",
                f"سفارش: {order.pk}\nکاربر: {order.user.email}\nمبلغ: {order.amount_irr:,} ریال\nپیگیری: {submission.reference_number}\nزمان اعلامی: {submission.paid_at}\n\nبرای بررسی وارد داشبورد مدیریت شوید.",
                settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFICATION_EMAIL],
            )
        except Exception:
            logger.exception("Manual payment notification failed for order %s", order.pk)
        messages.success(
            request,
            ("اطلاعات اصلاح‌شده واریز دوباره برای بررسی ارسال شد." if existing else "اطلاعات واریز ثبت شد؛ مدیر تا ۳ دقیقه فرصت بررسی دارد و سپس سیستم دسترسی را خودکار فعال می‌کند.")
            if lang == "fa" else
            ("Your corrected payment details were resubmitted for review." if existing else "Payment details were submitted. A manager has three minutes to review them, then access is activated automatically."),
        )
        return redirect(f"{reverse('assessments:checkout', kwargs={'pk': order.pk})}?lang={lang}")


class ManualPaymentStatusView(LoginRequiredMixin, View):
    """Return the signed-in customer's card-transfer review state."""

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("manual_payment"),
            pk=pk, user=request.user, gateway="card_transfer",
        )
        submission = getattr(order, "manual_payment", None)
        if order.status == "paid":
            state = "approved"
        elif submission and submission.status == "rejected":
            state = "rejected"
        else:
            state = "pending"
        response = JsonResponse({
            "state": state,
            "ready": state == "approved",
            "auto_approve_seconds": max(
                0,
                int((submission.updated_at + timedelta(seconds=settings.PAYMENT_AUTO_APPROVE_SECONDS) - timezone.now()).total_seconds()),
            ) if submission and state == "pending" else 0,
            "redirect_url": f"{reverse('accounts:dashboard')}?lang={request.GET.get('lang', 'fa')}"
            if state == "approved" else "",
        })
        response["Cache-Control"] = "no-store, private"
        return response


class SandboxPayView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not settings.DEBUG or settings.PAYMENT_GATEWAY != "sandbox":
            raise Http404
        order = get_object_or_404(Order, pk=pk, user=request.user)
        lang = request.GET.get("lang", "fa")
        if request.POST.get("accept_terms") != "yes":
            messages.error(
                request,
                "برای ادامه باید شرایط آزمون را بپذیرید."
                if lang == "fa" else "You must accept the assessment terms to continue.",
            )
            return redirect(f"{reverse('assessments:checkout', kwargs={'pk': order.pk})}?lang={lang}")
        if order.status == "pending":
            order.terms_version = settings.ASSESSMENT_TERMS_VERSION
            order.terms_accepted_at = timezone.now()
            order.save(update_fields=["terms_version", "terms_accepted_at", "updated_at"])
        order, created = verify_sandbox_payment(order.pk)
        send_payment_confirmation_email(order, request, lang)
        if created:
            if order.gateway == "free":
                messages.success(
                    request,
                    "تخفیف ۱۰۰٪ اعمال و دسترسی آزمون فعال شد."
                    if lang == "fa" else "The 100% discount was applied and assessment access is active.",
                )
            else:
                messages.success(request, "پرداخت آزمایشی تأیید و مجوز آزمون صادر شد." if lang == "fa" else "Test payment verified and access granted.")
        return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")


class StartAttemptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        entitlement = get_object_or_404(ExamEntitlement, pk=pk, user=request.user)
        lang = request.GET.get("lang", "fa")
        if not request.user.email_verified:
            messages.error(
                request,
                "برای شروع آزمون باید ایمیل شما تأیید شده باشد."
                if lang == "fa" else "Verify your email before starting the assessment.",
            )
            return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
        if not request.user.first_name.strip() or not request.user.last_name.strip():
            messages.error(
                request,
                "پیش از شروع، نام و نام خانوادگی دارنده گواهی را کامل کنید."
                if lang == "fa" else "Complete the certificate holder name before starting.",
            )
            return redirect(f"{reverse('accounts:profile_identity')}?lang={lang}")
        try:
            attempt, _ = start_attempt(entitlement.pk, request.user)
        except AttemptLimitError:
            messages.error(
                request,
                f"سقف {settings.ASSESSMENT_ATTEMPTS_PER_DAY} بار شروع این آزمون در ۲۴ ساعت تکمیل شده است."
                if lang == "fa" else f"The limit of {settings.ASSESSMENT_ATTEMPTS_PER_DAY} starts for this assessment within 24 hours has been reached.",
            )
            return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
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

    def get(self, request, *args, **kwargs):
        attempt = self.get_object()
        result = finalize_expired_attempt(attempt.pk)
        if result:
            return redirect(f"{reverse('assessments:result', kwargs={'pk': result.pk})}?lang={self.lang}")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
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
        question_snapshot = item.question_snapshot if isinstance(item.question_snapshot, dict) else {}
        choices_snapshot = item.choices_snapshot if isinstance(item.choices_snapshot, list) else []
        choices = {
            str(choice.get("id")): choice
            for choice in choices_snapshot
            if isinstance(choice, dict) and choice.get("id") is not None
        }
        ordered_choices = [
            choices[str(choice_id)]
            for choice_id in item.choice_order
            if str(choice_id) in choices
        ]
        context.update({
            "item": item,
            "question_snapshot": question_snapshot,
            "ordered_choices": ordered_choices,
            "snapshot_error": not question_snapshot or len(ordered_choices) != len(item.choice_order),
            "position": position,
            "progress_percent": round(position / attempt.exam.question_count * 100),
            "previous_position": position - 1 if position > 1 else None,
            "next_position": position + 1 if position < attempt.exam.question_count else None,
            "answered_count": attempt.attempt_questions.filter(
                Q(selected_choice_snapshot_id__isnull=False) | Q(selected_choice__isnull=False)
            ).count(),
        })
        now = timezone.now()
        item.first_seen_at = item.first_seen_at or now
        item.last_seen_at = now
        item.visit_count += 1
        item.save(update_fields=("first_seen_at", "last_seen_at", "visit_count"))
        if attempt.current_position != position:
            attempt.current_position = position
            attempt.save(update_fields=["current_position", "updated_at"])
        return context


class AttemptReviewView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    model = Attempt
    template_name = "assessments/attempt_review.html"
    context_object_name = "attempt"

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).select_related("exam", "version")

    def get(self, request, *args, **kwargs):
        attempt = self.get_object()
        result = finalize_expired_attempt(attempt.pk)
        if result:
            return redirect(f"{reverse('assessments:result', kwargs={'pk': result.pk})}?lang={self.lang}")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        if attempt.status != "in_progress":
            context["attempt_closed"] = True
            return context
        items = list(attempt.attempt_questions.only(
            "position", "selected_choice_id", "selected_choice_snapshot_id",
        ))
        answered_count = sum(item.effective_selected_choice_id is not None for item in items)
        context.update({
            "items": items,
            "answered_count": answered_count,
            "unanswered_count": len(items) - answered_count,
            "finish_form": FinishAttemptForm(lang=self.lang),
        })
        return context


class SaveAnswerView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk, item_pk):
        attempt = get_object_or_404(
            Attempt.objects.select_for_update(), pk=pk, user=request.user,
        )
        result = finalize_expired_attempt(attempt.pk)
        if result or attempt.status != "in_progress":
            return JsonResponse({
                "ok": False, "reason": "attempt_closed",
                "result_url": reverse("assessments:result", kwargs={"pk": result.pk}) if result else "",
            }, status=409)
        item = get_object_or_404(
            AttemptQuestion.objects.select_for_update(), pk=item_pk, attempt=attempt,
        )
        choice_id = request.POST.get("choice")
        allowed_choice_ids = {
            str(choice.get("id"))
            for choice in item.choices_snapshot
            if isinstance(choice, dict) and choice.get("id") is not None
        }
        if choice_id not in allowed_choice_ids:
            raise Http404
        choice = Choice.objects.filter(pk=choice_id, question_id=item.question_id).first()
        previous_choice_id = item.effective_selected_choice_id
        item.selected_choice_snapshot_id = int(choice_id)
        item.selected_choice = choice
        item.answered_at = timezone.now()
        if previous_choice_id is not None and previous_choice_id != int(choice_id):
            item.answer_change_count += 1
        try:
            active_seconds = max(0, min(int(request.POST.get("active_seconds", 0)), 900))
        except (TypeError, ValueError):
            active_seconds = 0
        item.active_seconds += active_seconds
        item.last_seen_at = timezone.now()
        item.save(update_fields=[
            "selected_choice_snapshot_id", "selected_choice", "answered_at",
            "answer_change_count", "active_seconds", "last_seen_at",
        ])
        answered_count = attempt.attempt_questions.filter(
            Q(selected_choice_snapshot_id__isnull=False) | Q(selected_choice__isnull=False)
        ).count()
        return JsonResponse({"ok": True, "answered": answered_count})


class AudioPlayView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk, item_pk):
        owned_attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        if finalize_expired_attempt(owned_attempt.pk):
            return JsonResponse({"ok": False, "reason": "attempt_closed"}, status=409)
        attempt = get_object_or_404(
            Attempt.objects.select_for_update(), pk=pk, user=request.user, status="in_progress",
        )
        item = get_object_or_404(
            AttemptQuestion.objects.select_for_update(),
            pk=item_pk, attempt=attempt,
        )
        snapshot = item.question_snapshot if isinstance(item.question_snapshot, dict) else {}
        max_plays = int(snapshot.get("max_plays") or 0)
        if not snapshot.get("audio_path") or max_plays < 1:
            return JsonResponse({"ok": False, "reason": "not_audio_question"}, status=400)
        if item.audio_play_count >= max_plays:
            return JsonResponse({"ok": False, "reason": "play_limit", "remaining": 0}, status=429)
        item.audio_play_count += 1
        item.save(update_fields=["audio_play_count"])
        return JsonResponse({"ok": True, "remaining": max_plays - item.audio_play_count})


class IntegrityEventView(LoginRequiredMixin, View):
    allowed_events = {"visibility_hidden", "visibility_returned", "copy", "paste"}

    @transaction.atomic
    def post(self, request, pk):
        owned_attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        if finalize_expired_attempt(owned_attempt.pk):
            return JsonResponse({"ok": False, "reason": "attempt_closed"}, status=409)
        attempt = get_object_or_404(
            Attempt.objects.select_for_update(), pk=pk, user=request.user, status="in_progress"
        )
        event_type = request.POST.get("event_type")
        if event_type not in self.allowed_events:
            return JsonResponse({"ok": False}, status=400)
        item = None
        item_pk = request.POST.get("item_id", "")
        if item_pk:
            item = get_object_or_404(AttemptQuestion, pk=item_pk, attempt=attempt)
        try:
            duration_ms = max(0, min(int(request.POST.get("duration_ms", 0)), 900_000))
        except (TypeError, ValueError):
            duration_ms = 0
        now = timezone.now()
        if event_type in {"copy", "paste"}:
            recent = IntegrityEvent.objects.filter(
                attempt=attempt, event_type=event_type, attempt_question=item,
                created_at__gte=now - timedelta(seconds=3),
            ).exists()
            if recent:
                return JsonResponse({"ok": True, "deduplicated": True, "integrity_score": attempt.integrity_score})
        if event_type == "visibility_hidden":
            latest = IntegrityEvent.objects.filter(attempt=attempt).order_by("-created_at").first()
            if latest and latest.event_type == "visibility_hidden":
                return JsonResponse({"ok": True, "deduplicated": True, "integrity_score": attempt.integrity_score})
        if event_type == "visibility_returned":
            last_return = IntegrityEvent.objects.filter(attempt=attempt, event_type="visibility_returned").order_by("-created_at").first()
            hidden = IntegrityEvent.objects.filter(attempt=attempt, event_type="visibility_hidden")
            if last_return:
                hidden = hidden.filter(created_at__gt=last_return.created_at)
            hidden = hidden.order_by("-created_at").first()
            if not hidden:
                return JsonResponse({"ok": False, "reason": "missing_hidden_event"}, status=409)
            duration_ms = min(int((now - hidden.created_at).total_seconds() * 1000), 900_000)
            item = hidden.attempt_question or item
        assessment = assess_event(event_type, duration_ms)
        IntegrityEvent.objects.create(
            attempt=attempt,
            attempt_question=item,
            event_type=event_type,
            duration_ms=duration_ms,
            metadata={"risk_points": assessment.points, "severity": assessment.severity},
        )
        if assessment.points:
            attempt.integrity_score = max(0, attempt.integrity_score - assessment.points)
            attempt.save(update_fields=["integrity_score", "updated_at"])
        return JsonResponse({"ok": True, "integrity_score": attempt.integrity_score, "risk_points": assessment.points})


class FinishAttemptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
        lang = request.GET.get("lang", "fa")
        expired_result = finalize_expired_attempt(attempt.pk)
        if expired_result:
            return redirect(f"{reverse('assessments:result', kwargs={'pk': expired_result.pk})}?lang={lang}")
        if attempt.status == "in_progress":
            form = FinishAttemptForm(request.POST, lang=lang)
            if not form.is_valid():
                messages.error(
                    request,
                    "برای ثبت نهایی، ابتدا گزینه تأیید را علامت بزنید."
                    if lang == "fa"
                    else "Confirm that you are ready before submitting the assessment.",
                )
                return redirect(
                    f"{reverse('assessments:attempt_review', kwargs={'pk': attempt.pk})}?lang={lang}"
                )
            attempt.status = "submitted"
            attempt.completion_reason = "manual"
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["status", "completion_reason", "submitted_at", "updated_at"])
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = context["lang"]
        send_result_ready_email(self.object, self.request, lang)
        rows = self.object.attempt.attempt_questions.select_related(
            "question__section", "question__skill", "selected_choice"
        ).prefetch_related("question__choices")
        review = []
        for row in rows:
            question = row.question_snapshot or {
                "prompt_fa": row.question.prompt_fa,
                "prompt_en": row.question.prompt_en,
                "question_type": row.question.question_type,
                "subskill": row.question.subskill,
                "difficulty": row.question.difficulty,
                "transcript": row.question.transcript,
                "explanation_fa": row.question.explanation_fa,
                "explanation_en": row.question.explanation_en,
            }
            choices = row.choices_snapshot or [
                {
                    "id": choice.pk,
                    "text_fa": choice.text_fa,
                    "text_en": choice.text_en,
                    "explanation_fa": choice.explanation_fa,
                    "explanation_en": choice.explanation_en,
                    "is_correct": choice.is_correct,
                }
                for choice in row.question.choices.all()
            ]
            selected_choice_id = row.effective_selected_choice_id
            selected = next((item for item in choices if item["id"] == selected_choice_id), None)
            correct = next((item for item in choices if item.get("is_correct")), None)
            status = "unanswered" if selected is None else ("correct" if selected.get("is_correct") else "incorrect")
            review.append({
                "position": row.position,
                "status": status,
                "prompt": question.get(f"prompt_{lang}") or question.get("prompt_en", ""),
                "selected": (selected or {}).get(f"text_{lang}", ""),
                "correct": (correct or {}).get(f"text_{lang}", ""),
                "explanation": question.get(f"explanation_{lang}") or question.get("explanation_en", ""),
                "selected_explanation": (selected or {}).get(f"explanation_{lang}", ""),
                "skill": row.question.skill.title_fa if lang == "fa" else row.question.skill.title_en,
                "subskill": question.get("subskill", ""),
                "difficulty": question.get("difficulty", 3),
                "transcript": question.get("transcript", "") if question.get("question_type") == "listening" else "",
            })
        context["review_groups"] = [
            (status, [item for item in review if item["status"] == status])
            for status in ("incorrect", "unanswered", "correct")
        ]
        context["learning_plan"] = self._learning_plan(lang)
        event_labels = {
            "visibility_hidden": ("خروج‌های ثبت‌شده", "Recorded page exits"),
            "visibility_returned": ("بازگشت‌های ثبت‌شده", "Recorded returns"),
            "tab_hidden": ("رویداد قدیمی غیرقابل اتکا", "Legacy unreliable event"),
            "window_blur": ("رویداد قدیمی غیرقابل اتکا", "Legacy unreliable event"),
            "copy": ("تلاش برای کپی", "Copy attempts"),
            "paste": ("تلاش برای جای‌گذاری", "Paste attempts"),
            "other": ("سایر رخدادها", "Other events"),
        }
        context["integrity_events"] = [
            {
                "code": item["event_type"], "count": item["total"],
                "label": event_labels[item["event_type"]][0 if lang == "fa" else 1],
            }
            for item in self.object.attempt.integrity_events.values("event_type").annotate(total=Count("id")).order_by("event_type")
        ]
        context["integrity_needs_review"] = (
            self.object.attempt.integrity_score < settings.ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD
        )
        context["integrity_threshold"] = settings.ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD
        return context

    def _learning_plan(self, lang):
        actions = {
            "python": ("تحلیل خروجی کد و حل تمرین‌های کوتاه را روزانه تمرین کن.", "Practise code tracing and short problems every day."),
            "python-core": ("مبانی پایتون، scope، data model و مدیریت خطا را مرور کن.", "Review Python fundamentals, scope, the data model, and error handling."),
            "django": ("چرخه request/response، فرم‌ها، middleware و class-based viewها را در یک پروژه کوچک تمرین کن.", "Build a small project around request/response, forms, middleware, and class-based views."),
            "database": ("QuerySet، ایندکس، transaction و بهینه‌سازی query را با داده واقعی تمرین کن.", "Practise QuerySets, indexes, transactions, and query optimisation with realistic data."),
            "security": ("تهدیدهای OWASP، مجوزدهی، CSRF و مدیریت secretها را روی یک نمونه عملی مرور کن.", "Review OWASP risks, authorisation, CSRF, and secret management in a practical example."),
            "testing-quality": ("برای view، service و edge caseها تست واحد و یکپارچه بنویس.", "Write unit and integration tests for views, services, and edge cases."),
            "deployment": ("تنظیمات production، PostgreSQL، static/media، logging و health check را تمرین کن.", "Practise production settings, PostgreSQL, static/media, logging, and health checks."),
            "grammar": ("خطاهای گرامری ثبت‌شده را دسته‌بندی و با مثال‌های مشابه بازنویسی کن.", "Classify your grammar errors and rewrite comparable examples."),
            "vocabulary": ("واژگان اشتباه را در جمله و collocation مرور کن، نه به‌صورت منفرد.", "Review missed vocabulary in sentences and collocations, not in isolation."),
            "reading": ("هر روز یک متن سطح بالا را زمان‌دار بخوان و ادعا، لحن و استنباط را استخراج کن.", "Time one advanced text daily and identify claims, tone, and inferences."),
            "use-of-english": ("ساخت‌های ثابت، اصلاح خطا و paraphrase را با تمرین زمان‌دار تقویت کن.", "Strengthen fixed expressions, error correction, and paraphrasing under time pressure."),
            "listening": ("فایل را یک‌بار برای مفهوم کلی و بار دوم برای جزئیات گوش کن، سپس transcript را مقایسه کن.", "Listen once for gist and once for detail, then compare with the transcript."),
            "writing-objective": ("سازمان‌دهی متن، register، cohesion و انتخاب دقیق عبارت را در نمونه‌های کوتاه تمرین کن.", "Practise organisation, register, cohesion, and precise phrasing in short samples."),
            "advanced": ("روی nuance، inference و انتخاب‌های نزدیک به هم در سطح C1 تمرکز کن.", "Focus on nuance, inference, and closely competing options at C1 level."),
        }
        skill_rows = sorted(self.object.skill_results.all(), key=lambda item: (item.percentage, item.skill.display_order))
        plan = []
        for item in skill_rows[:3]:
            pair = actions.get(item.skill.code, (
                "پاسخ‌های اشتباه این مهارت را مرور و با تمرین هدفمند تکرار کن.",
                "Review missed answers in this skill and repeat with targeted practice.",
            ))
            plan.append({
                "title": item.skill.title_fa if lang == "fa" else item.skill.title_en,
                "percentage": item.percentage,
                "action": pair[0] if lang == "fa" else pair[1],
                "priority": ("بالا" if lang == "fa" else "High") if item.percentage < 60 else ("متوسط" if lang == "fa" else "Medium"),
            })
        score = float(self.object.percentage)
        if score < 60:
            retest = "پس از ۲ تا ۳ هفته تمرین هدفمند دوباره آزمون بده." if lang == "fa" else "Retake after 2–3 weeks of targeted practice."
        elif score < 75:
            retest = "پس از ۱۰ تا ۱۴ روز مرور هدفمند دوباره آزمون بده." if lang == "fa" else "Retake after 10–14 days of targeted review."
        else:
            retest = "پس از رفع خطاهای ثبت‌شده، حدود ۷ روز دیگر دوباره آزمون بده." if lang == "fa" else "Retake in about 7 days after addressing the recorded errors."
        return {"items": plan, "retest": retest}


class CertificateView(LanguageViewMixin, DetailView):
    model = Certificate
    template_name = "assessments/certificate.html"
    context_object_name = "certificate"
    slug_field = "verification_code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return Certificate.objects.filter(is_revoked=False).select_related(
            "result__attempt__user", "result__attempt__exam", "result__attempt__version"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integrity_needs_review"] = (
            self.object.result.attempt.integrity_score < settings.ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD
        )
        return context


class CertificateVerifyView(LanguageViewMixin, TemplateView):
    template_name = "assessments/verify_certificate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw_code = self.request.GET.get("code", "")
        code = re.sub(r"[\s-]+", "", normalize_digits(raw_code)).upper()
        context["submitted_code"] = code
        if not raw_code:
            return context
        if not re.fullmatch(r"[0-9A-F]{12}", code):
            context["verification_failed"] = True
            return context
        certificate = Certificate.objects.select_related(
            "result__attempt__exam", "result__attempt__version", "result__attempt__user"
        ).filter(verification_code=code).first()
        if certificate is None or certificate.is_revoked:
            context["verification_failed"] = True
            context["certificate_revoked"] = bool(certificate and certificate.is_revoked)
            return context
        context["verified_certificate"] = certificate
        context["integrity_needs_review"] = (
            certificate.result.attempt.integrity_score < settings.ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD
        )
        return context
