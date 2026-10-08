# blog/views/post_list.py
# لیست پست‌ها با جستجو و فیلتر برچسب — کلاسی
from django.views.generic import ListView
from django.db.models import Q
from blog.models import Post
from blog.languages import indexable_list_languages, translated_posts
from django.conf import settings
from django.urls import reverse
from django.utils import translation
import re
from core.views.lang import LanguageViewMixin

class PostListView(LanguageViewMixin, ListView):
    """
    نمایش لیست پست‌ها با:
    - صفحه‌بندی
    - جستجو (q) در عنوان/خلاصه
    - فیلتر برچسب (tag)
    """
    template_name = "blog/list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        qs = translated_posts(Post.objects.published(), self.lang)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title_fa__icontains=q) |
                Q(title_en__icontains=q) |
                Q(summary_fa__icontains=q) |
                Q(summary_en__icontains=q)
            )
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__name__iexact=tag)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        languages = indexable_list_languages()
        context["blog_has_posts"] = self.lang in languages
        urls = {}
        for language in languages:
            with translation.override(language):
                urls[language] = f"{settings.SITE_URL}{reverse('blog:list')}"
        context["alternate_urls"] = urls
        available = translated_posts(Post.objects.published(), self.lang)
        tag_names = available.values_list("tags__name", flat=True).exclude(tags__name__isnull=True).order_by("tags__name").distinct()
        context["article_tags"] = [name for name in tag_names if self.lang == "fa" or not re.search(r"[\u0600-\u06ff]", name)]
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_tag"] = self.request.GET.get("tag", "")
        return context
