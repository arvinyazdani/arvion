from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import secrets

from core.sms import send_otp
from .models import PhoneVerification


def send_verification_email(user, request, lang):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_path = reverse("accounts:verify", kwargs={"uidb64": uid, "token": token})
    verify_url = request.build_absolute_uri(f"{verify_path}?lang={lang}")
    subject = "تأیید حساب آرویون" if lang == "fa" else "Verify your Rvion account"
    message = (
        f"برای فعال‌سازی حساب روی لینک زیر بزنید:\n{verify_url}"
        if lang == "fa" else f"Activate your account using this link:\n{verify_url}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    user.verification_sent_at = timezone.now()
    user.verification_email_count += 1
    user.save(update_fields=["verification_sent_at", "verification_email_count"])


def issue_phone_verification(user):
    now = timezone.now()
    window_start = now - timedelta(seconds=settings.OTP_REQUEST_WINDOW_SECONDS)
    if user.phone_verifications.filter(sent_at__gte=window_start).count() >= settings.OTP_REQUEST_LIMIT:
        raise PermissionError("otp_rate_limited")
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = PhoneVerification.objects.create(
        user=user,
        code_hash=make_password(code),
        expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS),
        resend_available_at=now + timedelta(seconds=settings.OTP_RESEND_SECONDS),
    )
    try:
        result = send_otp(user.mobile, code)
    except Exception:
        challenge.delete()
        raise
    challenge.delivery_reference = result.reference
    challenge.save(update_fields=["delivery_reference"])
    return challenge
