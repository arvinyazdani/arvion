# blog/views/post_detail.py
# جزئیات پست — کلاسی
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from blog.models import Post
from blog.languages import available_post_languages, translated_posts
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
        queryset = translated_posts(Post.objects.published(), self.lang).prefetch_related("tags")
        if self.lang == "fa":
            return get_object_or_404(queryset, slug_fa=slug)
        else:
            return get_object_or_404(queryset, slug_en=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        urls = {}
        for language in available_post_languages(self.object):
            slug = getattr(self.object, f"slug_{language}")
            with translation.override(language):
                urls[language] = f"{settings.SITE_URL}{reverse('blog:detail', args=[slug])}"
        context["alternate_urls"] = urls
        context["canonical_url"] = urls[self.lang]
        other_language = "en" if self.lang == "fa" else "fa"
        if other_language in urls:
            context["language_switch_url"] = urls[other_language].removeprefix(settings.SITE_URL)
        else:
            with translation.override(other_language):
                context["language_switch_url"] = reverse("blog:list")
        return context
