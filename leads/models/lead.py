# leads/models/lead.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Lead(models.Model):
    """
    درخواست همکاری/آموزش (Lead)
    شامل نام، ایمیل یا تلگرام، شماره تماس، نوع درخواست، پیام و وضعیت بررسی
    """
    REQUEST_TYPES = [
        ("project", _("Project Request")),
        ("training", _("Training Request")),
        ("other", _("Other")),
    ]
    name = models.CharField(max_length=120)
    email_or_telegram = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True, null=True)
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPES,
        default="project",
        verbose_name=_("Request Type")
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.request_type}"