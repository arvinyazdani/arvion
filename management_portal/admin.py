from django.contrib import admin

from .models import StaffAccessAudit


@admin.register(StaffAccessAudit)
class StaffAccessAuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "target", "action", "staff_enabled")
    list_filter = ("action", "staff_enabled", "created_at")
    search_fields = ("actor__email", "target__email")
    readonly_fields = ("actor", "target", "action", "roles", "staff_enabled", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
