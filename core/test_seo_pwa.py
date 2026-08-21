import json
import re
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from assessments.models import Exam
from blog.models import Post
from projects.models import Project
from traffic.models import TrafficDay


class PWAEndpointTests(TestCase):
    def test_worker_has_root_scope_and_cannot_be_served_stale(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("service_worker"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("application/javascript", response["Content-Type"])
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertContains(response, 'const CACHE = "rvion-shell-v4"')
        self.assertContains(response, 'const OFFLINE_URL_FA = "/offline/fa/"')
        self.assertContains(response, 'const OFFLINE_URL_EN = "/offline/en/"')
        self.assertContains(response, 'url.pathname.startsWith("/en/")')
        self.assertEqual(len(queries), 0)

    def test_offline_fallback_is_public_data_free_and_not_tracked(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("offline"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اتصال اینترنت برقرار نیست")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("public", response["Cache-Control"])
        self.assertNotIn("sessionid", response.cookies)
        self.assertEqual(TrafficDay.objects.count(), 0)
        self.assertEqual(len(queries), 0)

    def test_offline_fallback_keeps_language_and_retries_requested_url(self):
        english = self.client.get(reverse("offline_en"))
        self.assertContains(english, '<html lang="en" dir="ltr">', html=False)
        self.assertContains(english, "You’re currently offline.")
        self.assertContains(english, '<a href="">Try again</a>', html=False)
        self.assertNotContains(english, "اتصال اینترنت برقرار نیست")

        persian = self.client.get(reverse("offline_fa"))
        self.assertContains(persian, '<html lang="fa" dir="rtl">', html=False)
        self.assertContains(persian, "اتصال اینترنت برقرار نیست.")
        self.assertNotContains(persian, "You’re currently offline.")

    def test_manifest_exposes_stable_identity_and_local_shortcuts(self):
        manifest_path = Path(settings.BASE_DIR) / "core/static/core/manifest.webmanifest"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["id"], "/fa/")
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["lang"], "fa")
        self.assertEqual(manifest["dir"], "rtl")
        self.assertFalse(manifest["prefer_related_applications"])
        self.assertTrue(all(item["url"].startswith("/fa/") for item in manifest["shortcuts"]))
        self.assertTrue(any("maskable" in icon.get("purpose", "") for icon in manifest["icons"]))


class SearchDiscoveryTests(TestCase):
    def test_sitemap_has_public_project_and_exam_details_in_both_languages(self):
        project = Project.objects.create(
            title_fa="پروژه نمایشی",
            title_en="Public project",
            slug="public-project",
            is_active=True,
        )
        exam = Exam.objects.create(
            slug="public-exam",
            title_fa="آزمون عمومی",
            title_en="Public exam",
            description_fa="شرح",
            description_en="Description",
            language_mode="bilingual",
            is_active=True,
        )

        response = self.client.get(reverse("sitemap"))

        self.assertContains(response, f"https://testserver/fa/projects/{project.slug}/")
        self.assertContains(response, f"https://testserver/en/projects/{project.slug}/")
        self.assertContains(response, f"https://testserver/fa/assessments/{exam.slug}/")
        self.assertContains(response, f"https://testserver/en/assessments/{exam.slug}/")
        self.assertNotContains(response, "https://testserver/en/crm-order/")
        self.assertNotContains(response, "https://testserver/en/clinic-order/")

    def test_private_workspaces_are_excluded_from_crawling(self):
        response = self.client.get(reverse("robots"))

        self.assertContains(response, "Disallow: /contract/")
        self.assertContains(response, "Disallow: /fa/management/")
        self.assertContains(response, "Disallow: /en/account/")
        self.assertContains(response, "Disallow: /fa/assessments/attempt/")
        self.assertEqual(response["X-Robots-Tag"], "noindex")
        self.assertIn("max-age=3600", response["Cache-Control"])

    def test_scheduled_blog_post_is_not_public_before_publish_time(self):
        post = Post.objects.create(
            title_fa="مقاله آینده",
            title_en="Future post",
            summary_fa="خلاصه",
            summary_en="Summary",
            body_fa="متن",
            body_en="Body",
            slug_fa="مقاله-آینده",
            slug_en="future-post",
            is_published=True,
            published_at=timezone.now() + timedelta(days=1),
        )

        self.assertEqual(self.client.get(f"/fa/blog/{post.slug_fa}/").status_code, 404)
        self.assertEqual(self.client.get(f"/en/blog/{post.slug_en}/").status_code, 404)

    def test_blog_article_exposes_valid_structured_data(self):
        post = Post.objects.create(
            title_fa="معماری امن",
            title_en="Secure architecture",
            summary_fa="خلاصهٔ مقاله",
            summary_en="Article summary",
            body_fa="متن مقاله",
            body_en="Article body",
            slug_fa="معماری-امن",
            slug_en="secure-architecture",
            is_published=True,
            published_at=timezone.now(),
        )

        response = self.client.get(f"/fa/blog/{post.slug_fa}/")
        documents = [
            json.loads(value)
            for value in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                response.content.decode("utf-8"),
            )
        ]
        article = next(document for document in documents if document.get("@type") == "BlogPosting")
        self.assertEqual(article["headline"], post.title_fa)
        self.assertEqual(article["mainEntityOfPage"]["@id"], response.context["canonical_url"])
