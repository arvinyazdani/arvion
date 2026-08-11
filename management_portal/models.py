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
