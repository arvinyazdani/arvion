# services/admin.py
from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Service

@admin.register(Service)
class ServiceAdmin(TranslatableAdmin):
    list_display = ("get_title", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("translations__title",)

    def get_title(self, obj):
        return obj.safe_translation_getter("title", any_language=True)
    get_title.short_description = "Title"