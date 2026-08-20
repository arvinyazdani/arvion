from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import transaction
from datetime import timedelta
import secrets

from core.sms import send_otp
from .models import PhoneVerification


@transaction.atomic
def issue_phone_verification(user):
    # Serialize issuance per account so concurrent resend requests cannot all
    # pass the same rate-limit check.
    user = user.__class__.objects.select_for_update().get(pk=user.pk)
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
