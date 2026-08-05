from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView, PasswordResetCompleteView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetView,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from datetime import timedelta
from django.views.generic import FormView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import OrderedDict

from core.views.lang import LanguageViewMixin

from .forms import EmailAuthenticationForm, ProfileIdentityForm, RegistrationForm, ResendVerificationForm
from .models import User
from .services import send_verification_email
from assessments.models import AttemptResult


class RegisterView(LanguageViewMixin, FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def form_valid(self, form):
        user = form.save()
        send_verification_email(user, self.request, self.lang)
        self.request.session["verification_email"] = user.email
        return redirect(f"{reverse('accounts:verification_sent')}?lang={self.lang}")


class ResendVerificationView(LanguageViewMixin, FormView):
    template_name = "accounts/resend_verification.html"
    form_class = ResendVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=False, email_verified=False).first()
        threshold = timezone.now() - timedelta(seconds=settings.EMAIL_VERIFICATION_RESEND_SECONDS)
        if user and (user.verification_sent_at is None or user.verification_sent_at <= threshold):
            send_verification_email(user, self.request, self.lang)
        self.request.session["verification_email"] = email
        return redirect(f"{reverse('accounts:verification_sent')}?lang={self.lang}&resent=1")


class AccountLoginView(LanguageViewMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs


class AccountPasswordResetView(LanguageViewMixin, PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"

    def form_valid(self, form):
        self.extra_email_context = {"lang": self.lang}
        return super().form_valid(form)

    def get_success_url(self):
        return f"{reverse('accounts:password_reset_done')}?lang={self.lang}"


class AccountPasswordResetDoneView(LanguageViewMixin, PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class AccountPasswordResetConfirmView(LanguageViewMixin, PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"

    def get_success_url(self):
        return f"{reverse('accounts:password_reset_complete')}?lang={self.lang}"


class AccountPasswordResetCompleteView(LanguageViewMixin, PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class ProfileIdentityView(LanguageViewMixin, LoginRequiredMixin, UpdateView):
    template_name = "accounts/profile_identity.html"
    form_class = ProfileIdentityForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def get_success_url(self):
        messages.success(
            self.request,
            "نام دارنده گواهی ذخیره شد." if self.lang == "fa" else "Certificate holder name saved.",
        )
        return f"{reverse('accounts:dashboard')}?lang={self.lang}"


class AccountResultsView(LanguageViewMixin, LoginRequiredMixin, ListView):
    template_name = "accounts/results_history.html"
    context_object_name = "results"
    paginate_by = 10

    def get_queryset(self):
        return AttemptResult.objects.filter(attempt__user=self.request.user).select_related(
            "attempt__exam", "attempt__version", "certificate"
        )


def verify_email(request, uidb64, token):
    lang = request.GET.get("lang") or request.session.get("lang", "fa")
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=user_id)
    except (ValueError, TypeError, OverflowError):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        login(request, user)
        messages.success(request, "حساب شما فعال شد." if lang == "fa" else "Your account is now active.")
        return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
    return render(request, "accounts/verification_invalid.html", {"lang": lang}, status=400)


def verification_sent(request):
    lang = request.GET.get("lang") or request.session.get("lang", "fa")
    return render(request, "accounts/verification_sent.html", {
        "lang": lang, "email": request.session.get("verification_email"),
        "resent": request.GET.get("resent") == "1",
    })


@login_required
def dashboard(request):
    lang = request.GET.get("lang") or request.user.preferred_language
    entitlements = request.user.exam_entitlements.select_related("exam", "order", "attempt", "attempt__result")
    grouped = OrderedDict()
    for entitlement in entitlements:
        group = grouped.setdefault(entitlement.exam_id, {
            "exam": entitlement.exam, "ready": 0, "ready_entitlement": None,
            "in_progress": None, "completed": [],
        })
        attempt = getattr(entitlement, "attempt", None)
        if attempt and attempt.status == "in_progress":
            group["in_progress"] = attempt
        elif attempt and attempt.status == "completed":
            group["completed"].append(attempt)
        elif not attempt and entitlement.attempts_remaining:
            group["ready"] += entitlement.attempts_remaining
            group["ready_entitlement"] = group["ready_entitlement"] or entitlement
    orders = request.user.assessment_orders.select_related("exam")[:5]
    return render(request, "accounts/dashboard.html", {
        "lang": lang, "assessment_groups": list(grouped.values()), "orders": orders,
    })
