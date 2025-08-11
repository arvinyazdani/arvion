from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Page

@admin.register(Page)
class PageAdmin(TranslatableAdmin):
    """
    ادمین چندزبانه برای مدیریت صفحات ثابت.
    """
    list_display = ("slug", "get_title", "updated_at")
    search_fields = ("translations__title", "slug")

    def get_title(self, obj):
        return obj.safe_translation_getter("title", any_language=True)
    get_title.short_description = "Title"
