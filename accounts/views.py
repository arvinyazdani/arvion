from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView, PasswordResetCompleteView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetView,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import Resolver404, resolve, reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, UpdateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import OrderedDict
import math
from urllib.parse import urlsplit

from core.views.lang import LanguageViewMixin
from core.form_accessibility import enhance_form_accessibility
from core.sms.backends import SMSDeliveryError, normalize_iran_mobile

from .forms import EmailAuthenticationForm, PhoneVerificationForm, ProfileIdentityForm, RegistrationForm, ResendVerificationForm
from .models import PhoneVerification, User
from .services import issue_phone_verification
from .security import AttemptThrottle
from assessments.models import AttemptResult, Order


def _remember_sms_delivery_failure(request):
    """Keep the verification screen truthful when the provider did not accept a code."""
    request.session["phone_verification_sms_failed"] = True


def _clear_sms_delivery_failure(request):
    request.session.pop("phone_verification_sms_failed", None)


def _activate_with_pending_mobile_verification(request, user, lang):
    """Grant temporary access only when the SMS provider itself is unavailable.

    The mobile remains explicitly unverified so staff can distinguish this
    recovery path from a completed OTP verification in the approval queue.
    """
    user.is_active = True
    user.save(update_fields=["is_active"])
    request.session.pop("phone_verification_user_id", None)
    _clear_sms_delivery_failure(request)
    login(request, user)
    messages.warning(
        request,
        "حساب شما موقتاً فعال شد. سرویس پیامک در دسترس نبود؛ کارشناسان آرویون به‌زودی برای تأیید شماره با شما تماس می‌گیرند."
        if lang == "fa" else
        "Your account is temporarily active. SMS delivery is unavailable; Rvion specialists will contact you shortly to verify your number.",
    )
    return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")


@method_decorator(never_cache, name="dispatch")
class RegisterView(LanguageViewMixin, FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def form_valid(self, form):
        user = form.save()
        self.request.session["phone_verification_user_id"] = user.pk
        try:
            issue_phone_verification(user)
        except PermissionError:
            _remember_sms_delivery_failure(self.request)
            messages.error(
                self.request,
                "تعداد درخواست کد زیاد شده است؛ ۱۰ دقیقه دیگر دوباره تلاش کنید."
                if self.lang == "fa" else
                "Too many code requests. Please try again in 10 minutes.",
            )
        except (SMSDeliveryError, ImproperlyConfigured):
            return _activate_with_pending_mobile_verification(self.request, user, self.lang)
        except Exception:
            _remember_sms_delivery_failure(self.request)
            messages.error(
                self.request,
                "حساب ساخته شد، اما ارسال کد کامل نشد. کمی بعد دوباره تلاش کنید."
                if self.lang == "fa" else
                "Your account was created, but the code could not be delivered. Please try again shortly.",
            )
        else:
            _clear_sms_delivery_failure(self.request)
        return redirect(f"{reverse('accounts:verify_phone')}?lang={self.lang}")

    def form_invalid(self, form):
        """Resume an interrupted signup only after proving the saved password."""
        email = self.request.POST.get("email", "").strip().lower()
        try:
            mobile = normalize_iran_mobile(self.request.POST.get("mobile", ""))
        except ValueError:
            mobile = None
        user = User.objects.filter(
            email__iexact=email, mobile=mobile, is_active=False, mobile_verified_at__isnull=True,
        ).first() if email and mobile else None
        if user and user.check_password(self.request.POST.get("password1", "")):
            self.request.session["phone_verification_user_id"] = user.pk
            latest = user.phone_verifications.first()
            if not latest or latest.resend_available_at <= timezone.now():
                try:
                    issue_phone_verification(user)
                    _clear_sms_delivery_failure(self.request)
                    messages.success(
                        self.request,
                        "ثبت‌نام نیمه‌کاره پیدا شد و یک کد جدید فرستادیم."
                        if self.lang == "fa" else
                        "We found your interrupted signup and sent a new code.",
                    )
                except PermissionError:
                    _remember_sms_delivery_failure(self.request)
                    messages.error(
                        self.request,
                        "تعداد درخواست کد زیاد بوده است؛ چند دقیقه بعد دوباره تلاش کنید."
                        if self.lang == "fa" else
                        "Too many code requests. Try again in a few minutes.",
                    )
                except (SMSDeliveryError, ImproperlyConfigured):
                    return _activate_with_pending_mobile_verification(self.request, user, self.lang)
                except Exception:
                    _remember_sms_delivery_failure(self.request)
                    messages.error(
                        self.request,
                        "ارسال کد انجام نشد؛ کمی بعد دوباره تلاش کنید."
                        if self.lang == "fa" else
                        "The code could not be sent. Try again shortly.",
                    )
            else:
                messages.info(
                    self.request,
                    "ثبت‌نام قبلی پیدا شد؛ تا پایان تایمر می‌توانید همان کد را وارد کنید."
                    if self.lang == "fa" else
                    "We found your previous signup. You can use the current code until the timer ends.",
                )
            return redirect(f"{reverse('accounts:verify_phone')}?lang={self.lang}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manual_approval"] = settings.MANUAL_ACCOUNT_APPROVAL
        return context


@method_decorator(never_cache, name="dispatch")
class PhoneVerificationView(LanguageViewMixin, FormView):
    template_name = "accounts/verify_phone.html"
    form_class = PhoneVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def _user(self):
        user_id = self.request.session.get("phone_verification_user_id")
        return User.objects.filter(pk=user_id, is_active=False, mobile_verified_at__isnull=True).first()

    def form_invalid(self, form):
        # Some OTP errors are added after the initial form clean (expired,
        # exhausted, or mismatched challenges), so refresh the ARIA links.
        enhance_form_accessibility(form, autocomplete={"code": "one-time-code"})
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not self._user():
            lang = request.GET.get("lang") or getattr(request, "LANGUAGE_CODE", "fa")
            messages.info(request, "ابتدا فرم ثبت‌نام را تکمیل کنید." if lang == "fa" else "Complete registration first.")
            return redirect(f"{reverse('accounts:register')}?lang={lang}")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "restart":
            user = self._user()
            user.delete()
            request.session.pop("phone_verification_user_id", None)
            messages.info(request, "اطلاعات قبلی پاک شد؛ شماره درست را وارد کنید." if self.lang == "fa" else "Previous details were cleared. Enter the correct number.")
            return redirect(f"{reverse('accounts:register')}?lang={self.lang}")
        if request.POST.get("action") == "resend":
            return self._resend()
        if request.POST.get("action") == "continue_without_sms":
            return _activate_with_pending_mobile_verification(request, self._user(), self.lang)
        return super().post(request, *args, **kwargs)

    def _resend(self):
        user = self._user()
        latest = user.phone_verifications.first()
        if latest and latest.resend_available_at > timezone.now():
            messages.warning(
                self.request,
                "تا پایان زمان نمایش‌داده‌شده صبر کنید." if self.lang == "fa" else "Wait until the timer finishes before requesting another code.",
            )
        else:
            try:
                issue_phone_verification(user)
                _clear_sms_delivery_failure(self.request)
                messages.success(self.request, "کد جدید ارسال شد." if self.lang == "fa" else "A new code was sent.")
            except PermissionError:
                _remember_sms_delivery_failure(self.request)
                messages.error(self.request, "درخواست‌ها زیاد بوده است؛ ۱۰ دقیقه بعد دوباره امتحان کنید." if self.lang == "fa" else "Too many requests. Try again in 10 minutes.")
            except (SMSDeliveryError, ImproperlyConfigured):
                _remember_sms_delivery_failure(self.request)
                messages.error(self.request, "سرویس پیامک کد را نپذیرفت. شماره و دسترسی پیامک را بررسی کنید و دوباره تلاش کنید." if self.lang == "fa" else "The SMS provider did not accept the code. Check SMS access and retry.")
            except Exception:
                _remember_sms_delivery_failure(self.request)
                messages.error(self.request, "ارسال پیامک کامل نشد. کمی بعد دوباره تلاش کنید." if self.lang == "fa" else "The SMS could not be delivered. Please try again shortly.")
        return redirect(f"{reverse('accounts:verify_phone')}?lang={self.lang}")

    @transaction.atomic
    def form_valid(self, form):
        user_id = self.request.session.get("phone_verification_user_id")
        user = User.objects.select_for_update().filter(
            pk=user_id, is_active=False, mobile_verified_at__isnull=True,
        ).first()
        if user is None:
            messages.info(
                self.request,
                "این ثبت‌نام قبلاً تأیید شده یا دیگر معتبر نیست."
                if self.lang == "fa" else
                "This signup was already verified or is no longer valid.",
            )
            return redirect(f"{reverse('accounts:login')}?lang={self.lang}")
        challenge = user.phone_verifications.select_for_update().first()
        if not challenge or challenge.expires_at <= timezone.now():
            form.add_error("code", "کد منقضی شده است؛ کد جدید بگیرید." if self.lang == "fa" else "This code has expired. Request a new one.")
            return self.form_invalid(form)
        if not challenge.is_usable:
            form.add_error("code", "تعداد تلاش‌ها تمام شده است؛ کد جدید بگیرید." if self.lang == "fa" else "Too many attempts. Request a new code.")
            return self.form_invalid(form)
        if not check_password(form.cleaned_data["code"], challenge.code_hash):
            challenge.attempts += 1
            challenge.save(update_fields=["attempts"])
            remaining = max(0, settings.OTP_MAX_VERIFY_ATTEMPTS - challenge.attempts)
            form.add_error("code", (f"کد درست نیست؛ {remaining} تلاش دیگر دارید." if self.lang == "fa" else f"Incorrect code. {remaining} attempts remain."))
            return self.form_invalid(form)
        now = timezone.now()
        challenge.used_at = now
        challenge.save(update_fields=["used_at"])
        user.mobile_verified_at = now
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["mobile_verified_at", "email_verified", "is_active"])
        login(self.request, user)
        self.request.session.pop("phone_verification_user_id", None)
        messages.success(self.request, "شماره شما تأیید شد؛ به حساب آرویون خوش آمدید." if self.lang == "fa" else "Your number is verified. Welcome to Rvion.")
        return redirect(f"{reverse('accounts:dashboard')}?lang={self.lang}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self._user()
        latest = user.phone_verifications.first()
        remaining = 0
        if latest:
            remaining = max(0, math.ceil((latest.resend_available_at - timezone.now()).total_seconds()))
        context.update({
            "mobile_masked": f"{user.mobile[:4]}••••{user.mobile[-4:]}", "resend_seconds": remaining,
            "sms_delivery_failed": bool(self.request.session.get("phone_verification_sms_failed")),
        })
        return context


class ResendVerificationView(LanguageViewMixin, FormView):
    template_name = "accounts/resend_verification.html"
    form_class = ResendVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def form_valid(self, form):
        return self._sms_recovery()

    def get(self, request, *args, **kwargs):
        return self._sms_recovery()

    def post(self, request, *args, **kwargs):
        return self._sms_recovery()

    def _sms_recovery(self):
        messages.info(
            self.request,
            "فعال‌سازی حساب فقط با کد پیامکی انجام می‌شود. فرم ثبت‌نام را با همان اطلاعات قبلی کامل کنید تا ادامه ثبت‌نام بازیابی شود."
            if self.lang == "fa" else
            "Accounts are activated by SMS only. Submit the registration form with the same details to resume an interrupted signup.",
        )
        return redirect(f"{reverse('accounts:register')}?lang={self.lang}")


@method_decorator(never_cache, name="dispatch")
class AccountLoginView(LanguageViewMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_reset_available"] = settings.ACCOUNT_EMAIL_PASSWORD_RESET_ENABLED
        return context

    def get_success_url(self):
        """Never redirect a successful login to a POST-only purchase action."""
        target = super().get_success_url()
        try:
            match = resolve(urlsplit(target).path)
        except Resolver404:
            return target
        if match.view_name != "assessments:create_order":
            return target
        messages.info(
            self.request,
            "ورود موفق بود. برای ادامه خرید، دکمه خرید آزمون را بزنید."
            if self.lang == "fa" else
            "You are signed in. Select the assessment purchase button to continue.",
        )
        return reverse("assessments:detail", kwargs={"slug": match.kwargs["slug"]})

    def _throttle(self):
        return AttemptThrottle(
            "login", self.request, self.request.POST.get("username", ""),
            settings.AUTH_LOGIN_ATTEMPTS, settings.AUTH_LOGIN_WINDOW_SECONDS,
        )

    def post(self, request, *args, **kwargs):
        if self._throttle().blocked():
            form = self.get_form()
            form.add_error(None, "تلاش‌های ورود بیش از حد مجاز است؛ کمی بعد دوباره امتحان کنید." if self.lang == "fa" else "Too many sign-in attempts. Please try again later.")
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        self._throttle().failure()
        return super().form_invalid(form)

    def form_valid(self, form):
        self._throttle().success()
        return super().form_valid(form)


class AccountPasswordResetView(LanguageViewMixin, PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"

    def get(self, request, *args, **kwargs):
        if not settings.ACCOUNT_EMAIL_PASSWORD_RESET_ENABLED:
            return self._support_recovery()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not settings.ACCOUNT_EMAIL_PASSWORD_RESET_ENABLED:
            return self._support_recovery()
        return super().post(request, *args, **kwargs)

    def _support_recovery(self):
        messages.info(
            self.request,
            "بازیابی ایمیلی هنوز فعال نیست. از فرم تماس، موضوع «بازیابی حساب» را بفرستید تا هویت شما بررسی شود."
            if self.lang == "fa" else
            "Email recovery is not active yet. Use the contact form and mention “account recovery” so we can verify your identity.",
        )
        return redirect(reverse("leads:contact"))

    def form_valid(self, form):
        email = form.cleaned_data.get("email", "")
        throttle = AttemptThrottle(
            "password-reset", self.request, email,
            settings.AUTH_EMAIL_REQUESTS, settings.AUTH_EMAIL_WINDOW_SECONDS,
        )
        if throttle.blocked():
            return redirect(self.get_success_url())
        throttle.failure()
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


class AccountOrdersView(LanguageViewMixin, LoginRequiredMixin, ListView):
    template_name = "accounts/orders_history.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("exam")


class AccountReceiptView(LanguageViewMixin, LoginRequiredMixin, DetailView):
    template_name = "accounts/payment_receipt.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user, status__in=("paid", "refunded")
        ).select_related("exam").prefetch_related("transactions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transaction"] = next(
            (item for item in self.object.transactions.all() if item.status == "verified"), None
        )
        return context


def verify_email(request, uidb64, token):
    lang = request.GET.get("lang") or request.session.get("lang", "fa")
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=user_id)
    except (ValueError, TypeError, OverflowError):
        user = None
    if user and default_token_generator.check_token(user, token):
        if user.mobile_verified_at is None:
            return render(request, "accounts/verification_invalid.html", {"lang": lang}, status=400)
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        login(request, user)
        messages.success(request, "حساب شما فعال شد." if lang == "fa" else "Your account is now active.")
        return redirect(f"{reverse('accounts:dashboard')}?lang={lang}")
    return render(request, "accounts/verification_invalid.html", {"lang": lang}, status=400)


def verification_sent(request):
    lang = request.GET.get("lang") or request.session.get("lang", "fa")
    messages.info(
        request,
        "روش فعال‌سازی ایمیلی کنار گذاشته شده است؛ ثبت‌نام را با کد پیامکی ادامه دهید."
        if lang == "fa" else
        "Email activation has been retired. Continue registration with the SMS code instead.",
    )
    return redirect(f"{reverse('accounts:register')}?lang={lang}")


@login_required
def dashboard(request):
    # The language prefix is authoritative. Falling back to the stored
    # preference previously made /en/account/dashboard/ render in Persian.
    lang = getattr(request, "LANGUAGE_CODE", None) or request.GET.get("lang") or request.user.preferred_language
    lang = lang if lang in {"fa", "en"} else "fa"
    request.session["lang"] = lang
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
    return render(request, "accounts/dashboard.html", {
        "lang": lang, "assessment_groups": list(grouped.values()),
    })
