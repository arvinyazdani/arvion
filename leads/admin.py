# leads/admin.py
from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email_or_telegram", "request_type", "created_at", "is_reviewed")
    list_filter = ("request_type", "is_reviewed", "created_at")
    search_fields = ("name", "email_or_telegram", "message")