from django.contrib import admin
from .models.projects import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title_fa', 'title_en', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title_en', 'title_fa', 'description_en', 'description_fa']
    readonly_fields = ['created_at']
    prepopulated_fields = {"slug": ("title_en",)}
