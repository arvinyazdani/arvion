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
