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
    customer = models.ForeignKey("management_portal.Customer", on_delete=models.PROTECT, blank=True, null=True, related_name="contracts")
    crm_order = models.ForeignKey("crm_orders.CrmOrder", on_delete=models.PROTECT, blank=True, null=True, related_name="contract_proposals")
    project_title = models.CharField(max_length=200)
    project_scope = models.TextField()
    amount_irr = models.PositiveBigIntegerField()
    payment_terms = models.TextField(default="۵۰٪ هنگام شروع و ۵۰٪ هنگام تحویل نهایی")
    delivery_terms = models.CharField(max_length=200, help_text="مثال: ۸ هفته پس از دریافت پیش‌پرداخت و اطلاعات لازم")
    client_details = models.TextField(blank=True)
    general_terms = models.TextField(blank=True)
    private_terms = models.TextField(blank=True)
    room_progress = models.JSONField(default=dict, blank=True)
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
        if self.status == "accepted":
            return True
        return self.status in {"sent", "review"} and (not self.expires_at or self.expires_at > timezone.now())

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


class ContractOtpChallenge(models.Model):
    PURPOSES = (("access", "ورود به اتاق قرارداد"), ("acceptance", "تأیید نهایی قرارداد"))
    version = models.ForeignKey(ContractVersion, on_delete=models.PROTECT, related_name="otp_challenges")
    phone = models.CharField(max_length=12)
    purpose = models.CharField(max_length=12, choices=PURPOSES, default="acceptance")
    code_hash = models.CharField(max_length=128)
    provider_reference = models.CharField(max_length=120, blank=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)


class ContractAcceptance(models.Model):
    version = models.OneToOneField(ContractVersion, on_delete=models.PROTECT, related_name="acceptance")
    verified_phone = models.CharField(max_length=12)
    provider_reference = models.CharField(max_length=120, blank=True)
    discovery_snapshot = models.JSONField(default=dict, blank=True)
    evidence_hash = models.CharField(max_length=64, blank=True)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ("-accepted_at",)


class ContractRoomAcknowledgement(models.Model):
    """Auditable acknowledgement of the fixed documents in a contract room."""

    DOCUMENTS = (
        ("general", "شرایط عمومی پیمان"),
        ("private", "شرایط خصوصی پیمان"),
    )
    version = models.ForeignKey(ContractVersion, on_delete=models.PROTECT, related_name="room_acknowledgements")
    document = models.CharField(max_length=12, choices=DOCUMENTS)
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("version", "document"), name="unique_contract_room_ack")]
