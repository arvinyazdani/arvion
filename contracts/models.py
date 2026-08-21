import hashlib
import json
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .questionnaires import normalize_schema


def contract_token():
    return secrets.token_urlsafe(32)


def validate_json_object(value):
    """Keep persisted workflow state predictable and safe to merge."""
    if not isinstance(value, dict):
        raise ValidationError("این مقدار باید یک شیء JSON باشد.")


def validate_specialist_schema(value):
    """Validate the portable, versioned specialist-form schema."""
    normalize_schema(value)


def _stable_json_hash(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


iran_mobile_validator = RegexValidator(
    regex=r"^989\d{9}$",
    message="شماره همراه باید به شکل استاندارد 989xxxxxxxxx ذخیره شود.",
)


class SpecialistFormTemplate(models.Model):
    SERVICE_KINDS = (("crm", "CRM"), ("clinic", "کلینیک"), ("general", "عمومی"))

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=100, unique=True)
    service_kind = models.CharField(max_length=12, choices=SERVICE_KINDS, default="general", db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    current_version = models.ForeignKey(
        "SpecialistFormTemplateVersion",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="current_for_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "الگوی نیازسنجی تخصصی"
        verbose_name_plural = "الگوهای نیازسنجی تخصصی"

    def clean(self):
        super().clean()
        if self.current_version_id and not SpecialistFormTemplateVersion.objects.filter(
            pk=self.current_version_id,
            template_id=self.pk,
        ).exists():
            raise ValidationError({"current_version": "نسخه جاری باید متعلق به همین الگو باشد."})

    def __str__(self):
        return self.name


class SpecialistFormTemplateVersion(models.Model):
    template = models.ForeignKey(SpecialistFormTemplate, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveSmallIntegerField()
    schema = models.JSONField(validators=[validate_specialist_schema])
    schema_hash = models.CharField(max_length=64, editable=False)
    change_note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="created_specialist_form_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-number", "-pk")
        constraints = [
            models.UniqueConstraint(fields=("template", "number"), name="unique_spec_template_version"),
        ]
        verbose_name = "نسخه الگوی نیازسنجی تخصصی"
        verbose_name_plural = "نسخه‌های الگوی نیازسنجی تخصصی"

    def save(self, *args, **kwargs):
        normalized_schema = normalize_schema(self.schema)
        calculated_hash = _stable_json_hash(normalized_schema)
        if self.pk:
            original = type(self).objects.only("template_id", "number", "schema", "schema_hash").get(pk=self.pk)
            if (
                original.template_id != self.template_id
                or original.number != self.number
                or original.schema != self.schema
                or original.schema_hash != calculated_hash
            ):
                raise ValidationError("نسخه منتشرشده فرم تغییرپذیر نیست؛ نسخه تازه‌ای بسازید.")
        self.schema = normalized_schema
        self.schema_hash = calculated_hash
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template.name} · نسخه {self.number}"


class GeneralTermsTemplate(models.Model):
    LANGUAGES = (("fa", "فارسی"), ("en", "English"))

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=100, unique=True)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="fa", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    current_version = models.ForeignKey(
        "GeneralTermsVersion",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="current_for_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("language", "name", "pk")
        verbose_name = "الگوی شرایط عمومی"
        verbose_name_plural = "الگوهای شرایط عمومی"

    def clean(self):
        super().clean()
        if self.current_version_id and not GeneralTermsVersion.objects.filter(
            pk=self.current_version_id,
            template_id=self.pk,
        ).exists():
            raise ValidationError({"current_version": "نسخه جاری باید متعلق به همین الگو باشد."})

    def __str__(self):
        return self.name


class GeneralTermsVersion(models.Model):
    template = models.ForeignKey(GeneralTermsTemplate, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    body = models.TextField()
    content_hash = models.CharField(max_length=64, editable=False)
    change_note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="created_general_terms_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-number", "-pk")
        constraints = [
            models.UniqueConstraint(fields=("template", "number"), name="unique_general_terms_version"),
        ]
        verbose_name = "نسخه شرایط عمومی"
        verbose_name_plural = "نسخه‌های شرایط عمومی"

    def clean(self):
        super().clean()
        if not (self.body or "").strip():
            raise ValidationError({"body": "متن شرایط عمومی نمی‌تواند خالی باشد."})

    def save(self, *args, **kwargs):
        calculated_hash = hashlib.sha256((self.body or "").encode("utf-8")).hexdigest()
        if self.pk:
            original = type(self).objects.only(
                "template_id", "number", "title", "body", "content_hash"
            ).get(pk=self.pk)
            if (
                original.template_id != self.template_id
                or original.number != self.number
                or original.title != self.title
                or original.body != self.body
                or original.content_hash != calculated_hash
            ):
                raise ValidationError("نسخه منتشرشده شرایط عمومی تغییرپذیر نیست؛ نسخه تازه‌ای بسازید.")
        self.content_hash = calculated_hash
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template.name} · نسخه {self.number}"


class ContractProposal(models.Model):
    STATUSES = (("draft", "پیش‌نویس"), ("sent", "ارسال‌شده"), ("review", "بازخورد مشتری"), ("accepted", "پذیرفته‌شده"), ("expired", "منقضی"), ("revoked", "باطل‌شده"))

    title = models.CharField(max_length=200, default="پیشنهاد طراحی و توسعه سامانه")
    customer_name = models.CharField(max_length=160)
    customer_phone = models.CharField(max_length=16)
    customer_email = models.EmailField(blank=True)
    customer = models.ForeignKey("management_portal.Customer", on_delete=models.PROTECT, blank=True, null=True, related_name="contracts")
    crm_order = models.ForeignKey("crm_orders.CrmOrder", on_delete=models.PROTECT, blank=True, null=True, related_name="contract_proposals")
    customer_case = models.ForeignKey(
        "management_portal.CustomerCase",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contract_proposals",
    )
    general_terms_version = models.ForeignKey(
        GeneralTermsVersion,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contract_proposals",
    )
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
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)
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


class SpecialistAssignment(models.Model):
    STATUSES = (("draft", "پیش‌نویس"), ("submitted", "تکمیل‌شده"), ("reviewed", "بررسی‌شده"))

    proposal = models.OneToOneField(ContractProposal, on_delete=models.CASCADE, related_name="specialist_assignment")
    version = models.ForeignKey(
        SpecialistFormTemplateVersion,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    answers = models.JSONField(default=dict, blank=True, validators=[validate_json_object])
    progress = models.JSONField(default=dict, blank=True, validators=[validate_json_object])
    status = models.CharField(max_length=12, choices=STATUSES, default="draft", db_index=True)
    revision = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(blank=True, null=True)
    last_saved_at = models.DateTimeField(blank=True, null=True, db_index=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-pk")
        indexes = [models.Index(fields=("status", "last_saved_at"), name="ctr_spec_status_saved_idx")]
        constraints = [
            models.CheckConstraint(check=models.Q(revision__gte=0), name="spec_assignment_revision_gte_0"),
        ]
        verbose_name = "فرم تخصصی اختصاص‌یافته"
        verbose_name_plural = "فرم‌های تخصصی اختصاص‌یافته"

    def clean(self):
        super().clean()
        validate_json_object(self.answers)
        validate_json_object(self.progress)

    def __str__(self):
        return f"{self.proposal.customer_name} · {self.version.template.name}"


class RoomAccessGrant(models.Model):
    proposal = models.ForeignKey(ContractProposal, on_delete=models.CASCADE, related_name="access_grants")
    authorized_phone = models.CharField(max_length=12, validators=[iran_mobile_validator], db_index=True)
    password_hash = models.CharField(max_length=256)
    credential_version = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="created_room_access_grants",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=("proposal", "is_active", "expires_at"), name="ctr_access_active_exp_idx")]
        constraints = [
            models.CheckConstraint(check=models.Q(credential_version__gte=1), name="room_access_version_gte_1"),
            models.UniqueConstraint(
                fields=("proposal", "authorized_phone", "credential_version"),
                name="unique_room_access_version",
            ),
            models.UniqueConstraint(
                fields=("proposal", "authorized_phone"),
                condition=models.Q(is_active=True),
                name="unique_active_room_phone",
            ),
        ]
        verbose_name = "دسترسی اتاق مشتری"
        verbose_name_plural = "دسترسی‌های اتاق مشتری"

    @property
    def is_available(self):
        return self.is_active and (not self.expires_at or self.expires_at > timezone.now())

    def set_password(self, raw_password):
        if not isinstance(raw_password, str) or len(raw_password) < 12:
            raise ValidationError({"password_hash": "رمز ورود باید حداقل ۱۲ نویسه داشته باشد."})
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return bool(self.password_hash) and check_password(raw_password, self.password_hash)

    def clean(self):
        super().clean()
        if self.revoked_at and self.is_active:
            raise ValidationError({"is_active": "دسترسی باطل‌شده نمی‌تواند فعال باشد."})

    def __str__(self):
        return f"{self.proposal.customer_name} · {self.authorized_phone}"


class RoomDelivery(models.Model):
    CHANNELS = (("sms", "پیامک"), ("manual", "ارسال دستی"), ("copy", "کپی لینک"), ("whatsapp", "واتس‌اپ"))
    STATUSES = (("queued", "در صف"), ("sent", "ارسال‌شده"), ("failed", "ناموفق"))

    proposal = models.ForeignKey(ContractProposal, on_delete=models.PROTECT, related_name="room_deliveries")
    access_grant = models.ForeignKey(
        RoomAccessGrant,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="deliveries",
    )
    recipient_phone = models.CharField(max_length=12, validators=[iran_mobile_validator], db_index=True)
    channel = models.CharField(max_length=12, choices=CHANNELS, default="sms", db_index=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="queued", db_index=True)
    template_key = models.CharField(max_length=80, blank=True)
    provider_reference = models.CharField(max_length=120, blank=True)
    error_message = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="created_room_deliveries",
    )
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("proposal", "created_at"), name="ctr_delivery_proposal_idx"),
            models.Index(fields=("status", "created_at"), name="ctr_delivery_status_idx"),
        ]
        verbose_name = "سابقه ارسال اتاق مشتری"
        verbose_name_plural = "سوابق ارسال اتاق مشتری"

    def clean(self):
        super().clean()
        if self.access_grant_id and self.access_grant.proposal_id != self.proposal_id:
            raise ValidationError({"access_grant": "دسترسی انتخاب‌شده متعلق به این قرارداد نیست."})

    def __str__(self):
        return f"{self.get_channel_display()} · {self.recipient_phone}"


class RoomEvent(models.Model):
    EVENT_TYPES = (
        ("workspace_created", "اتاق مشتری ساخته شد"),
        ("access_created", "دسترسی ساخته شد"),
        ("access_rotated", "دسترسی تغییر کرد"),
        ("access_revoked", "دسترسی باطل شد"),
        ("link_sent", "لینک ارسال شد"),
        ("link_copied", "لینک کپی شد"),
        ("delivery_failed", "ارسال ناموفق بود"),
        ("login_succeeded", "ورود موفق"),
        ("login_failed", "ورود ناموفق"),
        ("session_expired", "نشست منقضی شد"),
        ("form_saved", "فرم ذخیره شد"),
        ("form_conflict", "تداخل ذخیره فرم"),
        ("form_submitted", "فرم تکمیل شد"),
        ("general_viewed", "شرایط عمومی دیده شد"),
        ("general_accepted", "شرایط عمومی تأیید شد"),
        ("private_viewed", "شرایط خصوصی دیده شد"),
        ("private_accepted", "شرایط خصوصی تأیید شد"),
        ("final_accepted", "تأیید نهایی انجام شد"),
        ("logout", "خروج"),
    )

    proposal = models.ForeignKey(ContractProposal, on_delete=models.PROTECT, related_name="room_events")
    access_grant = models.ForeignKey(
        RoomAccessGrant,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="events",
    )
    assignment = models.ForeignKey(
        SpecialistAssignment,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="events",
    )
    event_type = models.CharField(max_length=32, choices=EVENT_TYPES, db_index=True)
    metadata = models.JSONField(default=dict, blank=True, validators=[validate_json_object])
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="customer_room_events",
    )
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("proposal", "created_at"), name="ctr_event_proposal_idx"),
            models.Index(fields=("event_type", "created_at"), name="ctr_event_type_time_idx"),
        ]
        verbose_name = "رویداد اتاق مشتری"
        verbose_name_plural = "رویدادهای اتاق مشتری"

    def clean(self):
        super().clean()
        validate_json_object(self.metadata)
        if self.access_grant_id and self.access_grant.proposal_id != self.proposal_id:
            raise ValidationError({"access_grant": "دسترسی انتخاب‌شده متعلق به این قرارداد نیست."})
        if self.assignment_id and self.assignment.proposal_id != self.proposal_id:
            raise ValidationError({"assignment": "فرم انتخاب‌شده متعلق به این قرارداد نیست."})

    def __str__(self):
        return f"{self.proposal.customer_name} · {self.get_event_type_display()}"


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
