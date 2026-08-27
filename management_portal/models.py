from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def customer_case_code():
    return "CASE-" + get_random_string(10, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class Customer(models.Model):
    """The canonical company/person record shared by every operational module."""
    KINDS = (("company", "شرکت"), ("person", "شخص"))

    name = models.CharField(max_length=180, db_index=True)
    kind = models.CharField(max_length=12, choices=KINDS, default="company", db_index=True)
    phone = models.CharField(max_length=24, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ("name", "pk")

    def __str__(self):
        return self.name


class CustomerContact(models.Model):
    """A real person connected to a customer, optionally with an Rvion account."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=140, db_index=True)
    role = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=24, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="customer_contact_profiles")
    is_primary = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_primary", "name", "pk")
        constraints = [models.UniqueConstraint(fields=("customer", "phone", "email", "name"), name="unique_customer_contact_identity")]

    def __str__(self):
        return self.name


class CustomerEvent(models.Model):
    """Append-only operational ledger; domain models remain the source of truth."""

    CATEGORIES = (
        ("identity", "هویت و عضویت"),
        ("sales", "فروش و نیازسنجی"),
        ("order", "سفارش"),
        ("payment", "پرداخت"),
        ("assessment", "آزمون"),
        ("contract", "قرارداد"),
        ("support", "پشتیبانی"),
        ("communication", "ارتباط"),
        ("task", "وظیفه"),
        ("system", "سیستم"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="events")
    case = models.ForeignKey("CustomerCase", on_delete=models.PROTECT, blank=True, null=True, related_name="customer_events")
    category = models.CharField(max_length=20, choices=CATEGORIES, db_index=True)
    event_type = models.CharField(max_length=60, db_index=True)
    title_fa = models.CharField(max_length=180)
    title_en = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=60, blank=True, db_index=True)
    source_id = models.CharField(max_length=80, blank=True, db_index=True)
    dedupe_key = models.CharField(max_length=180, blank=True, null=True, unique=True)
    metadata = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="recorded_customer_events")
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [models.Index(fields=("customer", "event_type", "occurred_at"), name="cust_event_timeline_idx")]


class SavedCustomerSegment(models.Model):
    """A reusable, permission-scoped customer filter definition."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_customer_segments")
    name = models.CharField(max_length=100)
    filters = models.JSONField(default=dict)
    is_shared = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "pk")
        constraints = [models.UniqueConstraint(fields=("owner", "name"), name="unique_saved_segment_name_per_owner")]


class CustomerCase(models.Model):
    KINDS = (("lead", "همکاری"), ("crm", "CRM"), ("clinic", "کلینیک"), ("general", "عمومی"))
    STAGES = (("new", "جدید"), ("discovery", "نیازسنجی"), ("qualified", "واجد شرایط"), ("proposal", "پیشنهاد/قرارداد"), ("won", "موفق"), ("lost", "بسته‌شده"))
    PRIORITIES = (("low", "کم"), ("normal", "عادی"), ("high", "زیاد"), ("urgent", "فوری"))
    code = models.CharField(max_length=15, unique=True, default=customer_case_code, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True, related_name="cases")
    kind = models.CharField(max_length=12, choices=KINDS, db_index=True)
    customer_name = models.CharField(max_length=180, db_index=True)
    contact_name = models.CharField(max_length=140, blank=True)
    phone = models.CharField(max_length=24, blank=True, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    stage = models.CharField(max_length=16, choices=STAGES, default="new", db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITIES, default="normal", db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="owned_customer_cases")
    next_follow_up_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_contact_at = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True)
    source_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, blank=True, null=True, related_name="rvion_customer_cases")
    source_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    source = GenericForeignKey("source_content_type", "source_object_id")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        constraints = [models.UniqueConstraint(fields=("source_content_type", "source_object_id"), condition=models.Q(source_content_type__isnull=False, source_object_id__isnull=False), name="unique_customer_case_source")]


class CaseActivity(models.Model):
    KINDS = (("system", "سیستم"), ("note", "یادداشت"), ("call", "تماس"), ("message", "پیام"), ("meeting", "جلسه"), ("status", "تغییر وضعیت"), ("document", "سند"), ("task", "وظیفه"))
    case = models.ForeignKey(CustomerCase, on_delete=models.CASCADE, related_name="activities")
    kind = models.CharField(max_length=12, choices=KINDS, db_index=True)
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="customer_case_activities")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)


class CaseTask(models.Model):
    STATUSES = (("open", "باز"), ("done", "انجام‌شده"), ("cancelled", "لغوشده"))
    PRIORITIES = CustomerCase.PRIORITIES
    case = models.ForeignKey(CustomerCase, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="open", db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITIES, default="normal", db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="assigned_customer_tasks")
    due_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_customer_tasks")
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("status", "due_at", "-created_at")


class CaseDocument(models.Model):
    KINDS = (("initial", "نیازسنجی اولیه"), ("specialist", "نیازسنجی تخصصی"), ("contract", "قرارداد"), ("payment", "پرداخت"), ("export", "خروجی"), ("attachment", "پیوست"))
    case = models.ForeignKey(CustomerCase, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=16, choices=KINDS, db_index=True)
    title = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, blank=True, null=True, related_name="rvion_case_documents")
    object_id = models.PositiveBigIntegerField(blank=True, null=True)
    linked_object = GenericForeignKey("content_type", "object_id")
    snapshot = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="created_case_documents")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("case", "content_type", "object_id", "kind"), condition=models.Q(content_type__isnull=False, object_id__isnull=False), name="unique_case_linked_document")]


class CaseDocumentRevision(models.Model):
    """An append-only copy of every distinct snapshot seen for a case document."""

    document = models.ForeignKey(
        CaseDocument,
        on_delete=models.PROTECT,
        related_name="revisions",
    )
    title = models.CharField(max_length=200)
    snapshot = models.JSONField(default=dict)
    checksum = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("document", "checksum"),
                name="unique_case_document_revision_checksum",
            )
        ]
        verbose_name = "نسخه سند پرونده"
        verbose_name_plural = "نسخه‌های اسناد پرونده"


class StaffAccessAudit(models.Model):
    ACTIONS = (("created", "ساخت همکار"), ("roles_updated", "تغییر مسئولیت‌ها"))

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="staff_access_actions")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="staff_access_changes")
    action = models.CharField(max_length=24, choices=ACTIONS)
    roles = models.JSONField(default=list)
    staff_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "سابقه دسترسی همکار"
        verbose_name_plural = "سوابق دسترسی همکاران"


class ManagementNotification(models.Model):
    STATUSES = (("unread", "خوانده‌نشده"), ("read", "خوانده‌شده"), ("resolved", "مختومه"))
    CATEGORIES = (("accounts", "حساب‌ها"), ("sales", "فروش و سفارش"), ("payments", "پرداخت"), ("support", "پشتیبانی"), ("contracts", "قرارداد"))

    category = models.CharField(max_length=20, choices=CATEGORIES, db_index=True)
    title = models.CharField(max_length=180)
    description = models.CharField(max_length=300, blank=True)
    target_url = models.CharField(max_length=300)
    role = models.CharField(max_length=24, blank=True, db_index=True)
    source_key = models.CharField(max_length=120, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="owned_management_notifications")
    due_at = models.DateTimeField(blank=True, null=True, db_index=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="unread", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="resolved_management_notifications")
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "اعلان مدیریتی"
        verbose_name_plural = "اعلان‌های مدیریتی"


class SMSDispatch(models.Model):
    STATUSES = (("sent", "ارسال شد"), ("failed", "ناموفق"))

    recipient = models.CharField(max_length=12, db_index=True)
    message = models.TextField(max_length=1000)
    status = models.CharField(max_length=10, choices=STATUSES, db_index=True)
    provider = models.CharField(max_length=40, blank=True)
    provider_reference = models.CharField(max_length=120, blank=True)
    error_message = models.CharField(max_length=240, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="manual_sms_dispatches")
    campaign = models.ForeignKey("SMSCampaign", on_delete=models.PROTECT, blank=True, null=True, related_name="dispatches")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "ارسال دستی پیامک"
        verbose_name_plural = "ارسال‌های دستی پیامک"


class SMSMessageTemplate(models.Model):
    AUDIENCES = (
        ("registered", "عضو بدون سفارش"),
        ("unpaid", "سفارش پرداخت‌نشده"),
        ("payment_review", "پرداخت منتظر بررسی"),
        ("ready", "پرداخت‌شده و شروع‌نشده"),
        ("completed", "نتیجه آماده"),
        ("manual", "دستی"),
    )

    key = models.SlugField(max_length=60, unique=True)
    title_fa = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    body_fa = models.TextField(max_length=1000)
    body_en = models.TextField(max_length=1000)
    audience = models.CharField(max_length=24, choices=AUDIENCES, default="manual", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "pk")

    def __str__(self):
        return self.title_fa


class SMSCampaign(models.Model):
    audience = models.CharField(max_length=24, choices=SMSMessageTemplate.AUDIENCES, db_index=True)
    message = models.TextField(max_length=1000)
    recipient_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sms_campaigns")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)


class OperationalAudit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="management_operations")
    action = models.CharField(max_length=60, db_index=True)
    target_type = models.CharField(max_length=60, db_index=True)
    target_id = models.CharField(max_length=80, db_index=True)
    summary = models.CharField(max_length=240)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "رویداد عملیاتی"
        verbose_name_plural = "سابقه عملیات"


class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationReceipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_receipts")
    notification = models.ForeignKey(ManagementNotification, on_delete=models.CASCADE, related_name="receipts")
    seen_at = models.DateTimeField(blank=True, null=True, db_index=True)
    push_sent_at = models.DateTimeField(blank=True, null=True)
    sms_sent_at = models.DateTimeField(blank=True, null=True)
    last_reminded_at = models.DateTimeField(blank=True, null=True)
    last_error = models.CharField(max_length=240, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "notification"), name="unique_user_notification_receipt")]


class SystemLog(models.Model):
    """رویدادهای فنی سیستم (خطای سرور، خطای مرورگر کاربر) با شرح فارسی، مستقل از سابقه عملیات مدیریتی."""
    LEVELS = (("error", "خطا"), ("warning", "هشدار"), ("info", "اطلاعات"))
    CATEGORIES = (
        ("server", "خطای سرور"), ("frontend", "خطای مرورگر کاربر"),
        ("wizard", "رفتار ویزارد"), ("other", "سایر"),
    )

    level = models.CharField(max_length=10, choices=LEVELS, default="error", db_index=True)
    category = models.CharField(max_length=12, choices=CATEGORIES, default="other", db_index=True)
    message_fa = models.CharField(max_length=300)
    detail = models.TextField(blank=True)
    path = models.CharField(max_length=300, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="system_logs")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "رویداد سیستمی"
        verbose_name_plural = "لاگ‌های سیستم"
