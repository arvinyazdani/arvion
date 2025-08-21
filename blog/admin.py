from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title_fa', 'is_published', 'published_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title_fa', 'title_en', 'summary_fa', 'summary_en')