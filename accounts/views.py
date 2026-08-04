from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import FormView

from core.views.lang import LanguageViewMixin

from .forms import EmailAuthenticationForm, RegistrationForm
from .models import User


class RegisterView(LanguageViewMixin, FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def form_valid(self, form):
        user = form.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_path = reverse("accounts:verify", kwargs={"uidb64": uid, "token": token})
        verify_url = self.request.build_absolute_uri(verify_path)
        subject = "تأیید حساب آرویون" if self.lang == "fa" else "Verify your Arvion account"
        message = (
            f"برای فعال‌سازی حساب روی لینک زیر بزنید:\n{verify_url}"
            if self.lang == "fa"
            else f"Activate your account using this link:\n{verify_url}"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        self.request.session["verification_email"] = user.email
        return redirect(f"{reverse('accounts:verification_sent')}?lang={self.lang}")


class AccountLoginView(LanguageViewMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs


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
    return render(request, "accounts/verification_sent.html", {"lang": lang, "email": request.session.get("verification_email")})


@login_required
def dashboard(request):
    lang = request.GET.get("lang") or request.user.preferred_language
    entitlements = request.user.exam_entitlements.select_related("exam", "order")
    orders = request.user.assessment_orders.select_related("exam")[:5]
    return render(request, "accounts/dashboard.html", {"lang": lang, "entitlements": entitlements, "orders": orders})
