import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def contract_token():
    return secrets.token_urlsafe(32)


class ContractProposal(models.Model):
    STATUSES = (("draft", "پیش‌نویس"), ("sent", "ارسال‌شده"), ("review", "بازخورد مشتری"), ("accepted", "پذیرفته‌شده"), ("expired", "منقضی"), ("revoked", "باطل‌شده"))

    title = models.CharField(max_length=200, default="پیشنهاد طراحی و توسعه سامانه")
    customer_name = models.CharField(max_length=160)
    customer_phone = models.CharField(max_length=16)
    customer_email = models.EmailField(blank=True)
    project_title = models.CharField(max_length=200)
    project_scope = models.TextField()
    amount_irr = models.PositiveBigIntegerField()
    payment_terms = models.TextField(default="۵۰٪ هنگام شروع و ۵۰٪ هنگام تحویل نهایی")
    delivery_terms = models.CharField(max_length=200, help_text="مثال: ۸ هفته پس از دریافت پیش‌پرداخت و اطلاعات لازم")
    client_details = models.TextField(blank=True)
    token = models.CharField(max_length=64, unique=True, default=contract_token, editable=False)
    status = models.CharField(max_length=12, choices=STATUSES, default="draft", db_index=True)
    current_version = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_contracts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "پیشنهاد قرارداد"
        verbose_name_plural = "پیشنهادهای قرارداد"

    @property
    def is_publicly_available(self):
        return self.status in {"sent", "review", "accepted"} and (not self.expires_at or self.expires_at > timezone.now())

    def __str__(self):
        return f"{self.project_title} — {self.customer_name}"


class ContractClause(models.Model):
    proposal = models.ForeignKey(ContractProposal, on_delete=models.CASCADE, related_name="clauses")
    title = models.CharField(max_length=180)
    body = models.TextField()
    position = models.PositiveSmallIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "id")


class ContractVersion(models.Model):
    proposal = models.ForeignKey(ContractProposal, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveSmallIntegerField()
    snapshot = models.JSONField()
    snapshot_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contract_versions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-number",)
        constraints = [models.UniqueConstraint(fields=("proposal", "number"), name="unique_contract_version")]


class ContractReview(models.Model):
    version = models.OneToOneField(ContractVersion, on_delete=models.PROTECT, related_name="review")
    accepted_clause_ids = models.JSONField(default=list)
    rejected_clause_ids = models.JSONField(default=list)
    rejection_notes = models.TextField(blank=True)
    suggested_clause = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ("-reviewed_at",)
