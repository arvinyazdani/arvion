import re

from django.test import TestCase
from django.urls import reverse

from projects.models import DemoSelection, DemoTemplate


class AhaninoDemoTests(TestCase):
    def setUp(self):
        self.demo = DemoTemplate.objects.get(slug="ahanino-b2b-marketplace")

    def test_migration_seeds_an_active_bilingual_b2b_demo(self):
        self.assertTrue(self.demo.is_active)
        self.assertEqual(self.demo.category, "b2b")
        self.assertEqual(self.demo.title_fa, "بازار B2B آهنینو")
        self.assertEqual(self.demo.title_en, "Ahanino B2B steel marketplace")
        self.assertEqual(self.demo.default_features, ["catalog", "inquiries", "quotes", "membership"])

    def test_gallery_explains_reference_brand_and_links_both_languages(self):
        for lang, label in (("fa", "برند مرجع"), ("en", "Reference brand")):
            with self.subTest(lang=lang):
                response = self.client.get(reverse("projects:demo_gallery") + f"?lang={lang}")
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, label)
                self.assertContains(response, reverse("projects:demo_preview", args=[self.demo.slug]))
                self.assertContains(response, "AHANINO")
                self.assertContains(response, "اطلاعات نمونه نمایشی" if lang == "fa" else "sample details are illustrative")

    def test_preview_has_readable_desktop_and_mobile_screens_without_fabricated_live_data(self):
        for lang, expected in (("fa", "نمای دسکتاپ"), ("en", "Desktop view")):
            with self.subTest(lang=lang):
                response = self.client.get(reverse("projects:demo_preview", args=[self.demo.slug]) + f"?lang={lang}")
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn(expected, html)
                self.assertIn("ahanino-device-mobile", html)
                self.assertIn("Illustrative preview", html) if lang == "en" else self.assertIn("پیش‌نمایش نمایشی", html)
                self.assertIn('href="https://ahanino.com"', html)
                self.assertIn('rel="noopener noreferrer"', html)
                self.assertIn("پیش‌نمایش بر پایهٔ مفهوم بازارگاه آهنینو" if lang == "fa" else "illustrative preview based on Ahanino’s marketplace concept", html)
                self.assertNotIn("هویت فرضی است", html)
                self.assertNotIn("A fictional identity", html)
                self.assertRegex(html, r'<title>[^<]{1,60}</title>')
                description = re.search(r'<meta name="description" content="([^"]+)"', html)
                self.assertIsNotNone(description)
                self.assertGreaterEqual(len(description.group(1)), 110)
                self.assertLessEqual(len(description.group(1)), 155)
                scene_start = html.index('<section class="ahanino-market"')
                scene_end = html.index('class="ahanino-reference"', scene_start)
                scene = html[scene_start:scene_end]
                self.assertNotRegex(scene, r"[\u0600-\u06FF]") if lang == "en" else None
                self.assertIn("data-demo-view=\"desktop\"", html)
                self.assertIn("data-demo-view=\"mobile\"", html)
                self.assertIn("no live prices are shown", scene.lower()) if lang == "en" else self.assertIn("قیمت زنده نمایش داده نمی‌شود", scene)

    def test_b2b_enquiry_keeps_only_the_category_feature_allowlist(self):
        response = self.client.post(reverse("projects:demo_configure", args=[self.demo.slug]) + "?lang=en", {
            "submission_token": "ahanino-demo-test-token",
            "theme": "gold",
            "personality": "industrial",
            "features": ["catalog", "inquiries", "quotes", "membership", "payment"],
        })
        selection = DemoSelection.objects.get()
        self.assertEqual(selection.selections["features"], ["catalog", "inquiries", "quotes", "membership"])
        self.assertIn(f"request_type=webapp", response.url)

