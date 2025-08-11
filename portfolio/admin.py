from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Project

@admin.register(Project)
class ProjectAdmin(TranslatableAdmin):
    list_display = ('get_title', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('translations__title', 'translations__slug')

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}

    def get_title(self, obj):
        return obj.safe_translation_getter('title', any_language=True)
    get_title.short_description = 'Title'