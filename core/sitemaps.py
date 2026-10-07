from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from blog.models import Post
from projects.models import DemoTemplate
from services.models import Service
from assessments.models import Exam


class LocalizedSitemap(Sitemap):
    protocol = "https"

    def languages(self):
        return ("fa", "en")


class StaticSitemap(LocalizedSitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        bilingual_names = (
            "home", "about", "company_info", "crm_product", "services:list",
            "projects:demo_gallery", "blog:list", "assessments:list", "leads:contact",
            "privacy", "service_terms", "refund_policy",
        )
        # These two discovery wizards intentionally redirect English requests to
        # Persian until their complete English copy is ready. Redirect targets do
        # not belong in a sitemap.
        persian_only_names = ("crm_orders:create", "clinic_orders:create")
        items = [(language, name) for language in self.languages() for name in bilingual_names]
        items.extend(("fa", name) for name in persian_only_names)
        return items

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


class DemoSitemap(LocalizedSitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        demos = DemoTemplate.objects.filter(is_active=True).only("slug", "updated_at")
        return [(language, demo) for language in self.languages() for demo in demos]

    def location(self, item):
        language, demo = item
        with translation.override(language):
            return reverse("projects:demo_preview", args=[demo.slug])

    def lastmod(self, item):
        return item[1].updated_at


class ExamSitemap(LocalizedSitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        exams = Exam.objects.filter(is_active=True).only("slug", "updated_at")
        return [(language, exam) for language in self.languages() for exam in exams]

    def location(self, item):
        language, exam = item
        with translation.override(language):
            return reverse("assessments:briefing", args=[exam.slug])

    def lastmod(self, item):
        return item[1].updated_at


sitemaps = {
    "static": StaticSitemap,
    "services": ServiceSitemap,
    "posts": PostSitemap,
    "demos": DemoSitemap,
    "assessments": ExamSitemap,
}
