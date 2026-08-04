# blog/views/post_detail.py
# جزئیات پست — کلاسی
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from blog.models import Post
from core.views.lang import LanguageViewMixin

class PostDetailView(LanguageViewMixin, DetailView):
    """
    نمایش صفحه‌ی جزئیات یک پست با پشتیبانی از دوزبانگی.
    """
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_object(self):
        slug = self.kwargs.get("slug")
        if self.lang == "fa":
            return get_object_or_404(Post, slug_fa=slug, is_published=True)
        else:
            return get_object_or_404(Post, slug_en=slug, is_published=True)
