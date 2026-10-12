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
from blog.presentation import reader_content, reading_minutes, article_dek, article_topics
from django.db.models import Q
from blog.actions import article_actions
import mimetypes

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
        body, toc = reader_content(self.object, self.lang)
        context.update(article_body=body, article_toc=toc,
                       article_topics=article_topics(body, toc),
                       article_cover_type=mimetypes.guess_type(self.object.hero_image.name or "")[0] or "image/jpeg",
                       reading_minutes=reading_minutes(body, self.lang),
                       article_dek=article_dek(self.object, self.lang))
        candidates = translated_posts(Post.objects.published(), self.lang).exclude(pk=self.object.pk)
        related = list(candidates.filter(tags__in=self.object.tags.all()).distinct().prefetch_related("tags")[:3])
        context["related_posts"] = related
        names = [tag.name for tag in self.object.tags.all()]
        localized = [name for name in names
                     if any('\u0600' <= c <= '\u06ff' for c in name) == (self.lang == "fa")]
        context["article_tags"] = localized or (names if self.lang == "fa" else [])
        if candidates.exists():
            date, pk = self.object.published_at, self.object.pk
            context["previous_post"] = candidates.filter(Q(published_at__lt=date) | Q(published_at=date, pk__lt=pk)).first()
            context["next_post"] = candidates.filter(Q(published_at__gt=date) | Q(published_at=date, pk__gt=pk)).order_by("published_at", "pk").first()
        actions = article_actions(body, self.lang)
        context["article_actions"] = actions
        preferred = {
            "corporate-website-cost-1405": "corporate-website-design",
            "custom-website-vs-template": "corporate-website-design",
            "custom-or-ready-made-crm": "custom-web-application",
        }.get(self.object.slug_fa)
        context["article_service_url"] = next((item["url"] for item in actions
            if preferred and item["url"].rstrip("/").endswith("/" + preferred)),
            actions[0]["url"] if actions else None)
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
