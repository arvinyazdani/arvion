from django.db import models
from django.utils.crypto import get_random_string


def clinic_tracking_code():
    return "CLN-" + get_random_string(10, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class ClinicOrder(models.Model):
    STATUSES = [("new", "جدید"), ("discovery", "جلسه تحلیل"), ("proposal", "پیشنهاد ارسال شد"), ("won", "قرارداد"), ("lost", "بسته‌شده")]
    BUDGETS = [("under_150", "کمتر از ۱۵۰ میلیون تومان"), ("150_300", "۱۵۰ تا ۳۰۰ میلیون تومان"), ("300_600", "۳۰۰ تا ۶۰۰ میلیون تومان"), ("over_600", "بیشتر از ۶۰۰ میلیون تومان"), ("estimate", "ابتدا نیازمند برآورد"), ("private", "تمایل ندارم اعلام کنم")]
    TIMELINES = [("under_2", "کمتر از ۲ ماه"), ("2_4", "۲ تا ۴ ماه"), ("4_6", "۴ تا ۶ ماه"), ("over_6", "بیشتر از ۶ ماه"), ("unsure", "نیازمند پیشنهاد")]

    tracking_code = models.CharField(max_length=14, unique=True, default=clinic_tracking_code, editable=False)
    clinic_name = models.CharField(max_length=180)
    clinic_type = models.CharField(max_length=30)
    city = models.CharField(max_length=100)
    branch_count = models.PositiveSmallIntegerField(default=1)
    specialties = models.TextField()
    practitioner_count = models.PositiveSmallIntegerField()
    website = models.URLField(blank=True)
    contact_name = models.CharField(max_length=120)
    job_title = models.CharField(max_length=120)
    work_email = models.EmailField()
    phone = models.CharField(max_length=24)

    primary_goals = models.JSONField(default=list)
    target_audiences = models.JSONField(default=list)
    current_channels = models.JSONField(default=list)
    current_process = models.TextField()
    main_pain_points = models.TextField()
    success_metrics = models.TextField()

    visit_modes = models.JSONField(default=list)
    schedule_model = models.CharField(max_length=24)
    appointment_rules = models.TextField()
    intake_requirements = models.TextField(blank=True)
    reminder_channels = models.JSONField(default=list)
    waitlist_requirement = models.CharField(max_length=16)
    practitioner_features = models.JSONField(default=list)
    patient_account_features = models.JSONField(default=list)

    payment_methods = models.JSONField(default=list)
    pricing_model = models.CharField(max_length=24)
    insurance_requirement = models.CharField(max_length=20)
    cancellation_refund_rules = models.TextField()
    financial_documents = models.JSONField(default=list)

    content_types = models.JSONField(default=list)
    content_access = models.CharField(max_length=24)
    publishing_workflow = models.TextField()
    media_requirements = models.TextField(blank=True)
    webinar_features = models.JSONField(default=list)
    webinar_platform = models.CharField(max_length=24)
    expected_live_attendees = models.PositiveIntegerField(blank=True, null=True)

    system_roles = models.JSONField(default=list)
    record_scope = models.CharField(max_length=24)
    notification_channels = models.JSONField(default=list)
    integration_types = models.JSONField(default=list)
    required_integrations = models.TextField(blank=True)
    migration_sources = models.TextField(blank=True)
    security_requirements = models.TextField()
    hosting_preference = models.CharField(max_length=20)

    delivery_strategy = models.CharField(max_length=20)
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
        verbose_name = "درخواست وب‌سایت کلینیک"
        verbose_name_plural = "درخواست‌های وب‌سایت کلینیک"

    def __str__(self):
        return f"{self.tracking_code} — {self.clinic_name}"
