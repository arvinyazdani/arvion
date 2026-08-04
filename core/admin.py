from django.contrib import admin
from .models import Page

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """
    ادمین چندزبانه برای مدیریت صفحات ثابت.
    """
    list_display = ("slug", "get_title", "updated_at")
    search_fields = ("title_fa", "title_en", "slug")

    def get_title(self, obj):
        return obj.title_fa or obj.title_en
    get_title.short_description = "Title"
