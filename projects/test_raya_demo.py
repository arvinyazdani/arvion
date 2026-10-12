import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from projects.demo_briefs import brief_fields, story_sections
from projects.demo_labels import CATEGORY_FEATURE_KEYS, demo_config_labels
from projects.models import DemoTemplate


class RayaDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.demo = DemoTemplate.objects.get(slug="raya-personal-finance")

    def test_seed_is_active_fictional_and_uses_existing_raya_scope(self):
        self.assertTrue(self.demo.is_active)
        self.assertEqual(self.demo.category, "accounting")
        self.assertEqual(self.demo.default_features, ["accounts", "transactions", "reports", "exports"])
        self.assertEqual(CATEGORY_FEATURE_KEYS["accounting"], tuple(self.demo.default_features))
        self.assertEqual(len(brief_fields("accounting", "fa")), 4)
        self.assertEqual(len(story_sections("accounting", "en")), 2)
        self.assertEqual(dict(demo_config_labels("en", "accounting")["features"])["reports"], "Financial reports")

    def test_fa_and_en_preview_and_full_use_the_product_specific_workspace(self):
        for lang in ("fa", "en"):
            with translation.override(lang):
                for route in ("projects:demo_preview", "projects:demo_full"):
                    response = self.client.get(reverse(route, args=[self.demo.slug]) + f"?lang={lang}")
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "raya-demo.css")
                    self.assertContains(response, "raya-demo.js")
                    self.assertContains(response, "data-raya-demo")
                    self.assertContains(response, "https://raya.rvionai.com/")
                    self.assertContains(response, "fictional data" if lang == "en" else "ساختگی")
                    self.assertContains(response, "Nothing is saved" if lang == "en" else "چیزی در حساب واقعی ذخیره نمی‌شود")

    def test_english_workspace_copy_and_initial_amounts_are_ltr_localized(self):
        with translation.override("en"):
            response = self.client.get(reverse("projects:demo_preview", args=[self.demo.slug]) + "?lang=en")
        html = response.content.decode()
        self.assertIn("<title>Raya personal finance app design | Rvion</title>", html)
        section = html.split('data-raya-demo', 1)[1].split("</section>", 1)[0]
        self.assertIsNone(re.search(r"[\u0600-\u06ff]", section))
        self.assertIn("47,350,000", section)
        self.assertIn("32,500,000", section)
        self.assertIn("Show rials", Path(settings.BASE_DIR, "projects/static/projects/js/raya-demo.js").read_text())

    def test_configure_keeps_accounting_category_features_and_routes_to_webapp_order(self):
        preview = self.client.get(reverse("projects:demo_preview", args=[self.demo.slug]) + "?lang=fa")
        response = self.client.post(reverse("projects:demo_configure", args=[self.demo.slug]), {
            "submission_token": preview.context["submission_token"],
            "theme": "sage", "personality": "minimal", "brand_preview": "رایا",
            "features": ["accounts", "transactions", "reports", "exports"],
            "brief_goal": "daily", "brief_scope": "focused", "brief_content": "ready",
            "brief_timing": "flexible",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("request_type=webapp", response.url)
        self.assertIn("demo=", response.url)

    def test_javascript_binds_features_to_modules_and_starts_at_overview(self):
        script = Path(settings.BASE_DIR, "projects/static/projects/js/raya-demo.js").read_text()
        configurator = Path(settings.BASE_DIR, "projects/static/projects/js/demo-configurator.js").read_text()
        self.assertIn('setPanel("raya-overview")', script)
        self.assertIn('node.dataset.featureModule = feature', script)
        self.assertIn('panel.dataset.rayaFeaturePanel = feature', script)
        self.assertIn('dataset.featureModule = "exports"', script)
        self.assertIn("خروجی نمایشی", script)
        for feature in self.demo.default_features:
            self.assertIn(f'"{feature}"', configurator)
