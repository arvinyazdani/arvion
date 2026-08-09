from django.db import models
from django.utils.crypto import get_random_string


def crm_tracking_code():
    return "CRM-" + get_random_string(10, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class CrmOrder(models.Model):
    STATUSES = [
        ("new", "جدید"), ("discovery", "جلسه تحلیل"), ("qualified", "واجد شرایط"),
        ("proposal", "پیشنهاد ارسال شد"), ("won", "قرارداد"), ("lost", "بسته‌شده"),
    ]
    SIZES = [("1_10", "۱ تا ۱۰"), ("11_50", "۱۱ تا ۵۰"), ("51_200", "۵۱ تا ۲۰۰"), ("over_200", "بیش از ۲۰۰")]
    USER_COUNTS = [("under_10", "کمتر از ۱۰"), ("10_30", "۱۰ تا ۳۰"), ("31_100", "۳۱ تا ۱۰۰"), ("over_100", "بیش از ۱۰۰")]
    BUDGETS = [("unsure", "نیازمند برآورد"), ("under_150", "کمتر از ۱۵۰ میلیون تومان"), ("150_500", "۱۵۰ تا ۵۰۰ میلیون تومان"), ("500_1500", "۵۰۰ میلیون تا ۱.۵ میلیارد تومان"), ("over_1500", "بیش از ۱.۵ میلیارد تومان")]
    TIMELINES = [("urgent", "کمتر از ۲ ماه"), ("2_4", "۲ تا ۴ ماه"), ("4_8", "۴ تا ۸ ماه"), ("flexible", "منعطف")]

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
    crm_user_count = models.CharField(max_length=12, choices=USER_COUNTS)
    current_process = models.TextField()
    main_pain_points = models.TextField()
    success_metrics = models.TextField()

    required_capabilities = models.JSONField(default=list)
    critical_workflows = models.TextField()
    reports_needed = models.TextField()
    permission_requirements = models.TextField()

    current_tools = models.TextField(blank=True)
    required_integrations = models.TextField(blank=True)
    migration_sources = models.TextField(blank=True)
    approximate_record_count = models.PositiveIntegerField(blank=True, null=True)
    hosting_preference = models.CharField(max_length=20, choices=[("cloud", "ابری"), ("on_premise", "داخل سازمان"), ("unsure", "نیازمند بررسی")])
    security_requirements = models.TextField(blank=True)

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
