from django.contrib import admin

from .models import CrmOrder


@admin.action(description="انتقال به مرحله جلسه تحلیل")
def mark_discovery(modeladmin, request, queryset):
    queryset.filter(status="new").update(status="discovery")


@admin.register(CrmOrder)
class CrmOrderAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "organization_name", "industry", "organization_size", "budget_range", "status", "created_at")
    list_filter = ("status", "organization_size", "crm_user_count", "hosting_preference", "budget_range", "expected_timeline")
    search_fields = ("tracking_code", "organization_name", "contact_name", "work_email", "phone", "current_process", "main_pain_points")
    readonly_fields = ("tracking_code", "privacy_accepted_at", "created_at")
    actions = (mark_discovery,)
    fieldsets = (
        ("پیگیری", {"fields": ("tracking_code", "status", "created_at", "internal_notes")}),
        ("سازمان و تماس", {"fields": ("organization_name", "industry", "organization_size", "website", "contact_name", "job_title", "work_email", "phone")}),
        ("نیاز کسب‌وکار", {"fields": ("primary_goals", "departments", "customer_types", "lead_sources", "crm_user_count", "current_data_sources", "current_tools", "current_process", "main_pain_points", "success_metrics")}),
        ("دامنه محصول", {"fields": ("required_capabilities", "customer_data_fields", "assignment_model", "reminder_types", "notification_channels", "critical_workflows", "correspondence_features", "ai_use_cases", "reporting_priorities", "reports_needed", "system_roles", "permission_requirements")}),
        ("فناوری و داده", {"fields": ("devices", "mobile_requirement", "integration_types", "required_integrations", "migration_types", "migration_sources", "approximate_record_count", "hosting_preference", "audit_requirement", "security_requirements")}),
        ("تصمیم پروژه", {"fields": ("delivery_strategy", "budget_range", "expected_timeline", "requested_services", "decision_process", "additional_notes", "privacy_accepted_at")}),
    )
