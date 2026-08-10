from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from blog.models import Post
from services.models import Service


class LocalizedSitemap(Sitemap):
    protocol = "https"

    def languages(self):
        return ("fa", "en")


class StaticSitemap(LocalizedSitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        names = ("home", "about", "company_info", "crm_product", "services:list", "projects:list", "blog:list", "assessments:list", "leads:contact", "privacy", "service_terms", "refund_policy")
        return [(language, name) for language in self.languages() for name in names]

    def location(self, item):
        language, name = item
        with translation.override(language):
            return reverse(name)


class ServiceSitemap(LocalizedSitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return [(language, service) for language in self.languages() for service in Service.objects.filter(is_active=True)]

    def location(self, item):
        language, service = item
        with translation.override(language):
            return reverse("services:detail", args=[service.slug])


class PostSitemap(LocalizedSitemap):
    changefreq = "weekly"

    def items(self):
        return [
            (language, post)
            for language in self.languages()
            for post in Post.objects.published()
            if (post.slug_fa if language == "fa" else post.slug_en)
        ]

    def location(self, item):
        language, post = item
        slug = post.slug_fa if language == "fa" else post.slug_en
        if not slug:
            slug = post.slug_fa or post.slug_en
        with translation.override(language):
            return reverse("blog:detail", args=[slug])

    def lastmod(self, item):
        return item[1].published_at


sitemaps = {"static": StaticSitemap, "services": ServiceSitemap, "posts": PostSitemap}
