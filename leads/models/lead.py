# leads/models/lead.py
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


def lead_tracking_code():
    return get_random_string(12, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")

class Lead(models.Model):
    """
    درخواست همکاری/آموزش (Lead)
    شامل نام، ایمیل یا تلگرام، شماره تماس، نوع درخواست، پیام و وضعیت بررسی
    """
    REQUEST_TYPES = [
        ("consultation", _("Consultation")),
        ("website", _("Website")),
        ("webapp", _("Web application")),
        ("ecommerce", _("E-commerce")),
        ("support", _("Support and optimization")),
        ("training", _("Training Request")),
        ("other", _("Other")),
    ]
    BUDGETS = [
        ("unsure", _("Not sure yet")),
        ("under_50", _("Under 50 million toman")),
        ("50_150", _("50–150 million toman")),
        ("150_500", _("150–500 million toman")),
        ("over_500", _("Over 500 million toman")),
    ]
    TIMELINES = [
        ("flexible", _("Flexible")), ("one_month", _("Within one month")),
        ("one_three", _("One to three months")), ("over_three", _("More than three months")),
    ]
    CONTACT_METHODS = [("phone", _("Phone")), ("email", _("Email")), ("telegram", _("Telegram"))]
    STATUSES = [
        ("new", _("New")), ("contacted", _("Contacted")), ("qualified", _("Qualified")),
        ("proposal", _("Proposal sent")), ("won", _("Won")), ("lost", _("Lost")),
    ]
    tracking_code = models.CharField(max_length=12, unique=True, default=lead_tracking_code, editable=False)
    name = models.CharField(max_length=120)
    business_name = models.CharField(max_length=160, blank=True)
    email_or_telegram = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website_url = models.URLField(blank=True)
    service = models.ForeignKey("services.Service", on_delete=models.SET_NULL, blank=True, null=True, related_name="leads")
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPES,
        default="consultation",
        verbose_name=_("Request Type")
    )
    budget_range = models.CharField(max_length=20, choices=BUDGETS, default="unsure")
    timeline = models.CharField(max_length=20, choices=TIMELINES, default="flexible")
    preferred_contact = models.CharField(max_length=12, choices=CONTACT_METHODS, default="phone")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    privacy_accepted_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=STATUSES, default="new", db_index=True)
    is_reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.tracking_code} — {self.name}"
