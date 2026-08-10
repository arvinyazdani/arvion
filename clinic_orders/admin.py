from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .models import ClinicOrder
from .text_export import render_clinic_order_text


@admin.action(description="انتقال به مرحله جلسه تحلیل")
def mark_discovery(modeladmin, request, queryset):
    queryset.filter(status="new").update(status="discovery")


@admin.action(description="دریافت گزارش متنی کامل موارد انتخاب‌شده", permissions=["view"])
def export_text_reports(modeladmin, request, queryset):
    content = "\n\n".join(render_clinic_order_text(item) for item in queryset.order_by("created_at"))
    response = HttpResponse("\ufeff" + content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="rvion-clinic-orders.txt"'
    return response


@admin.register(ClinicOrder)
class ClinicOrderAdmin(admin.ModelAdmin):
    change_form_template = "admin/clinic_orders/clinicorder/change_form.html"
    list_display = ("tracking_code", "clinic_name", "clinic_type", "city", "practitioner_count", "budget_range", "status", "created_at")
    list_filter = ("status", "clinic_type", "schedule_model", "content_access", "webinar_platform", "budget_range", "expected_timeline")
    search_fields = ("tracking_code", "clinic_name", "specialties", "contact_name", "work_email", "phone")
    readonly_fields = ("tracking_code", "privacy_accepted_at", "created_at")
    actions = (mark_discovery, export_text_reports)
    fieldsets = (
        ("پیگیری", {"fields": ("tracking_code", "status", "created_at", "internal_notes")}),
        ("کلینیک و تماس", {"fields": ("clinic_name", "clinic_type", "city", "branch_count", "specialties", "practitioner_count", "website", "contact_name", "job_title", "work_email", "phone")}),
        ("هدف و فرآیند", {"fields": ("primary_goals", "target_audiences", "current_channels", "current_process", "main_pain_points", "success_metrics")}),
        ("نوبت و پرداخت", {"fields": ("visit_modes", "schedule_model", "appointment_rules", "intake_requirements", "reminder_channels", "waitlist_requirement", "practitioner_features", "patient_account_features", "payment_methods", "pricing_model", "insurance_requirement", "cancellation_refund_rules", "financial_documents")}),
        ("آموزش و وبینار", {"fields": ("content_types", "content_access", "publishing_workflow", "media_requirements", "webinar_features", "webinar_platform", "expected_live_attendees")}),
        ("فناوری و امنیت", {"fields": ("system_roles", "record_scope", "notification_channels", "integration_types", "required_integrations", "migration_sources", "security_requirements", "hosting_preference")}),
        ("تصمیم پروژه", {"fields": ("delivery_strategy", "requested_services", "budget_range", "expected_timeline", "decision_process", "additional_notes", "privacy_accepted_at")}),
    )

    def get_urls(self):
        return [path("<path:object_id>/download-text/", self.admin_site.admin_view(self.download_text), name="clinic_orders_clinicorder_download_text")] + super().get_urls()

    def download_text(self, request, object_id):
        order = self.get_object(request, object_id)
        if order is None or not self.has_view_permission(request, order):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        response = HttpResponse("\ufeff" + render_clinic_order_text(order), content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="clinic-{order.tracking_code}.txt"'
        return response
