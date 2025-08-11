from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Post

@admin.register(Post)
class PostAdmin(TranslatableAdmin):
    list_display = ('get_title', 'is_published', 'published_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('translations__title', 'translations__summary', 'translations__slug')

    # به‌جای prepopulated_fields:
    def get_prepopulated_fields(self, request, obj=None):
        # این کار با فیلدهای ترجمه‌ای سازگاره
        return {'slug': ('title',)}

    def get_title(self, obj):
        return obj.safe_translation_getter('title', any_language=True)
    get_title.short_description = 'Title'