# services/admin.py
from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "slug", "duration_fa", "price", "is_featured", "is_active", "display_order")
    list_filter = ("is_active", "is_featured")
    search_fields = ("title_fa", "title_en")
    prepopulated_fields = {"slug": ("title_en",)}
    ordering = ("display_order",)
