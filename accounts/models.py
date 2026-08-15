from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=12, unique=True, blank=True, null=True)
    mobile_verified_at = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(blank=True, null=True)
    verification_email_count = models.PositiveSmallIntegerField(default=0)
    preferred_language = models.CharField(
        max_length=2,
        choices=(("fa", "فارسی"), ("en", "English")),
        default="fa",
    )

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return self.get_full_name() or self.email


class PhoneVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_verifications")
    code_hash = models.CharField(max_length=128)
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resend_available_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(blank=True, null=True)
    delivery_reference = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ("-sent_at",)
        indexes = [models.Index(fields=("user", "sent_at"))]

    @property
    def is_usable(self):
        from django.conf import settings
        from django.utils import timezone
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
            and self.attempts < settings.OTP_MAX_VERIFY_ATTEMPTS
        )
