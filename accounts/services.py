from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_verification_email(user, request, lang):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_path = reverse("accounts:verify", kwargs={"uidb64": uid, "token": token})
    verify_url = request.build_absolute_uri(f"{verify_path}?lang={lang}")
    subject = "تأیید حساب رویون" if lang == "fa" else "Verify your Rvion account"
    message = (
        f"برای فعال‌سازی حساب روی لینک زیر بزنید:\n{verify_url}"
        if lang == "fa" else f"Activate your account using this link:\n{verify_url}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    user.verification_sent_at = timezone.now()
    user.verification_email_count += 1
    user.save(update_fields=["verification_sent_at", "verification_email_count"])
