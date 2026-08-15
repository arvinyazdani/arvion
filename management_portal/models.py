from django.conf import settings
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "ارسال دستی پیامک"
        verbose_name_plural = "ارسال‌های دستی پیامک"


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
