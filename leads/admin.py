# leads/admin.py
from django.contrib import admin
from .models import Lead


@admin.action(description="ثبت تماس با درخواست‌های انتخاب‌شده")
def mark_contacted(modeladmin, request, queryset):
    queryset.filter(status="new").update(status="contacted", is_reviewed=True)


@admin.action(description="انتقال درخواست‌های انتخاب‌شده به واجد شرایط")
def mark_qualified(modeladmin, request, queryset):
    queryset.exclude(status__in=("won", "lost")).update(status="qualified", is_reviewed=True)


@admin.action(description="بستن درخواست‌های انتخاب‌شده بدون نتیجه")
def mark_lost(modeladmin, request, queryset):
    queryset.exclude(status="won").update(status="lost", is_reviewed=True)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "name", "business_name", "service", "request_type", "budget_range", "status", "created_at")
    list_filter = ("status", "request_type", "budget_range", "timeline", "preferred_contact", "created_at")
    search_fields = ("tracking_code", "name", "business_name", "email_or_telegram", "phone", "message")
    readonly_fields = ("tracking_code", "privacy_accepted_at", "created_at")
    list_select_related = ("service",)
    actions = (mark_contacted, mark_qualified, mark_lost)
    fieldsets = (
        ("پیگیری", {"fields": ("tracking_code", "status", "is_reviewed", "created_at")}),
        ("اطلاعات مشتری", {"fields": ("name", "business_name", "email_or_telegram", "phone", "preferred_contact", "website_url")}),
        ("درخواست", {"fields": ("service", "request_type", "budget_range", "timeline", "message")}),
        ("رضایت حریم خصوصی", {"fields": ("privacy_accepted_at",), "classes": ("collapse",)}),
    )
