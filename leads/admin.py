# leads/admin.py
from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "name", "business_name", "service", "request_type", "budget_range", "status", "created_at")
    list_filter = ("status", "request_type", "budget_range", "timeline", "preferred_contact", "created_at")
    search_fields = ("tracking_code", "name", "business_name", "email_or_telegram", "phone", "message")
    readonly_fields = ("tracking_code", "privacy_accepted_at", "created_at")
    list_select_related = ("service",)
