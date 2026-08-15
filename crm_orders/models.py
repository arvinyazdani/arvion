from django.db import models
from django.utils.crypto import get_random_string
import secrets


def specialist_token():
    return secrets.token_urlsafe(32)


def crm_tracking_code():
    return "CRM-" + get_random_string(10, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class CrmOrder(models.Model):
    STATUSES = [
        ("new", "جدید"), ("discovery", "جلسه تحلیل"), ("qualified", "واجد شرایط"),
        ("proposal", "پیشنهاد ارسال شد"), ("won", "قرارداد"), ("lost", "بسته‌شده"),
    ]
    SIZES = [("under_10", "کمتر از ۱۰"), ("10_30", "۱۰ تا ۳۰"), ("31_100", "۳۱ تا ۱۰۰"), ("over_100", "بیش از ۱۰۰")]
    USER_COUNTS = [("1_5", "۱ تا ۵"), ("6_15", "۶ تا ۱۵"), ("16_30", "۱۶ تا ۳۰"), ("over_30", "بیش از ۳۰"), ("unsure", "هنوز مشخص نیست")]
    BUDGETS = [("under_100", "کمتر از ۱۰۰ میلیون تومان"), ("100_250", "۱۰۰ تا ۲۵۰ میلیون تومان"), ("250_500", "۲۵۰ تا ۵۰۰ میلیون تومان"), ("over_500", "بیش از ۵۰۰ میلیون تومان"), ("estimate", "ابتدا نیازمند برآورد"), ("private", "تمایل ندارم اعلام کنم")]
    TIMELINES = [("under_1", "کمتر از یک ماه"), ("1_2", "۱ تا ۲ ماه"), ("2_4", "۲ تا ۴ ماه"), ("over_4", "بیشتر از ۴ ماه"), ("unsure", "زمان مشخصی نداریم")]

    tracking_code = models.CharField(max_length=14, unique=True, default=crm_tracking_code, editable=False)
    organization_name = models.CharField(max_length=180)
    industry = models.CharField(max_length=120)
    organization_size = models.CharField(max_length=12, choices=SIZES)
    website = models.URLField(blank=True)
    contact_name = models.CharField(max_length=120)
    job_title = models.CharField(max_length=120)
    work_email = models.EmailField()
    phone = models.CharField(max_length=24)

    primary_goals = models.JSONField(default=list)
    departments = models.JSONField(default=list)
    customer_types = models.JSONField(default=list)
    lead_sources = models.JSONField(default=list)
    crm_user_count = models.CharField(max_length=12, choices=USER_COUNTS)
    current_process = models.TextField()
    current_data_sources = models.JSONField(default=list)
    main_pain_points = models.TextField()
    success_metrics = models.TextField()

    required_capabilities = models.JSONField(default=list)
    customer_data_fields = models.JSONField(default=list)
    assignment_model = models.CharField(max_length=20, blank=True)
    reminder_types = models.JSONField(default=list)
    notification_channels = models.JSONField(default=list)
    critical_workflows = models.TextField()
    correspondence_features = models.JSONField(default=list)
    ai_use_cases = models.JSONField(default=list)
    reporting_priorities = models.JSONField(default=list)
    system_roles = models.JSONField(default=list)
    reports_needed = models.TextField()
    permission_requirements = models.TextField()

    current_tools = models.TextField(blank=True)
    devices = models.JSONField(default=list)
    mobile_requirement = models.CharField(max_length=20, blank=True)
    integration_types = models.JSONField(default=list)
    required_integrations = models.TextField(blank=True)
    migration_types = models.JSONField(default=list)
    migration_sources = models.TextField(blank=True)
    approximate_record_count = models.PositiveIntegerField(blank=True, null=True)
    hosting_preference = models.CharField(max_length=20, choices=[("cloud", "آنلاین از هر مکان"), ("on_premise", "فقط شبکه داخلی"), ("hybrid", "ترکیبی با دسترسی امن"), ("unsure", "نیازمند بررسی")])
    audit_requirement = models.CharField(max_length=20, blank=True)
    security_requirements = models.TextField(blank=True)

    delivery_strategy = models.CharField(max_length=20, blank=True)
    requested_services = models.JSONField(default=list)
    budget_range = models.CharField(max_length=16, choices=BUDGETS)
    expected_timeline = models.CharField(max_length=12, choices=TIMELINES)
    decision_process = models.TextField()
    additional_notes = models.TextField(blank=True)
    privacy_accepted_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=STATUSES, default="new", db_index=True)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.tracking_code} — {self.organization_name}"


class CrmSpecialistDiscovery(models.Model):
    STATUS = [("draft", "پیش‌نویس"), ("submitted", "تکمیل‌شده"), ("reviewed", "بررسی‌شده")]
    order = models.OneToOneField(CrmOrder, on_delete=models.CASCADE, related_name="specialist_discovery")
    token = models.CharField(max_length=64, unique=True, default=specialist_token, editable=False)
    answers = models.JSONField(default=dict)
    status = models.CharField(max_length=12, choices=STATUS, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نیازسنجی تخصصی CRM"
        verbose_name_plural = "نیازسنجی‌های تخصصی CRM"

    def __str__(self):
        return f"{self.order.tracking_code} · نیازسنجی تخصصی"
