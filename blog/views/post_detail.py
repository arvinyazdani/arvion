# blog/views/post_detail.py
# جزئیات پست — کلاسی
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from blog.models import Post
from core.views.lang import LanguageViewMixin
from django.conf import settings
from django.urls import reverse
from django.utils import translation

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        urls = {}
        for language, slug in (("fa", self.object.slug_fa), ("en", self.object.slug_en)):
            with translation.override(language):
                urls[language] = f"{settings.SITE_URL}{reverse('blog:detail', args=[slug])}"
        context["alternate_urls"] = urls
        context["canonical_url"] = urls[self.lang]
        context["language_switch_url"] = urls["en" if self.lang == "fa" else "fa"].removeprefix(settings.SITE_URL)
        return context
