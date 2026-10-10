# blog/views/post_list.py
# لیست پست‌ها با جستجو و فیلتر برچسب — کلاسی
from django.views.generic import ListView
from django.db.models import Q
from collections import Counter
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
                Q(**{f"title_{self.lang}__icontains": q}) |
                Q(**{f"summary_{self.lang}__icontains": q}) |
                Q(tags__name__icontains=q)
            )
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__name__iexact=tag)
        return qs.distinct().prefetch_related("tags")

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
        counts = Counter(available.values_list("tags__name", flat=True))
        context["article_tags"] = [{"name": name, "count": count} for name, count in sorted(
            ((name, count) for name, count in counts.items() if name), key=lambda item: item[0])
            if self.lang == "fa" or not re.search(r"[\u0600-\u06ff]", name)]
        context["article_total"] = available.count()
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_tag"] = self.request.GET.get("tag", "")
        posts = list(context["posts"])
        featured = bool(posts and not context["search_query"] and not context["selected_tag"]
                        and context["page_obj"].number == 1)
        context["featured_post"] = posts[0] if featured else None
        context["grid_posts"] = posts[1:] if featured else posts
        return context
