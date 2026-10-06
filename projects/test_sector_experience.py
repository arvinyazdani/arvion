import re

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from leads.models import Lead
from projects.demo_briefs import GOALS, brief_labels
from projects.demo_labels import CATEGORY_FEATURE_KEYS
from projects.models import DemoSelection, DemoTemplate
from projects.sector_catalog import SCENARIOS, sector_catalog


class SectorExperienceTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def demo(self, category):
        return DemoTemplate.objects.create(slug="sector-" + category, category=category,
            title_fa="نمونه", title_en="Sample", fictional_brand_fa="برند فرضی",
            fictional_brand_en="Fictional brand", default_features=["blog", "booking"], is_active=True)

    def test_all_six_categories_cover_exactly_the_existing_three_goals(self):
        self.assertEqual(len(SCENARIOS), 6)
        for category in SCENARIOS:
            fa, en = sector_catalog(category), sector_catalog(category, "en")
            self.assertEqual([g["key"] for g in fa["goals"]], [g[0] for g in GOALS[category]])
            self.assertEqual([g["key"] for g in en["goals"]], [g[0] for g in GOALS[category]])
            self.assertEqual(len({g["title"] for g in fa["goals"]}), 3)
            for goal in en["goals"]:
                self.assertIsNone(re.search(r"[\u0600-\u06ff]", str(goal)))
                self.assertGreater(len(goal["detail"]), 100)
                self.assertEqual(len(goal["facts"]), 3)

    def test_unknown_and_store_category_keep_reference_store_unchanged(self):
        self.assertIsNone(sector_catalog("ecommerce"))
        self.assertIsNone(sector_catalog("unknown"))

    def test_catalog_is_fresh_and_does_not_mutate_shared_fixtures(self):
        catalog = sector_catalog("clinic")
        catalog["goals"][0]["title"] = "changed"
        self.assertNotEqual(sector_catalog("clinic")["goals"][0]["title"], "changed")

    def test_preview_and_full_render_same_goals_without_database_writes(self):
        for category in SCENARIOS:
            demo = self.demo(category)
            counts = (DemoSelection.objects.count(), Lead.objects.count())
            for route in ("projects:demo_preview", "projects:demo_full"):
                response = self.client.get(reverse(route, args=[demo.slug]))
                self.assertContains(response, "sector-experience.css")
                self.assertContains(response, "data-sector-panel=", count=3)
                self.assertContains(response, "data-sector-goal=", count=3)
                for key, _, _ in GOALS[category]:
                    self.assertContains(response, f'aria-controls="sector-{key}"')
                    self.assertContains(response, f'id="sector-{key}"')
            self.assertEqual(counts, (DemoSelection.objects.count(), Lead.objects.count()))

    def test_new_scene_is_localized_and_progressively_readable_without_js(self):
        for category in SCENARIOS:
            html = render_to_string("projects/demo_scenes/sector.html", {"sector": sector_catalog(category, "en"), "lang": "en"})
            self.assertIsNone(re.search(r"[\u0600-\u06ff]", html))
            self.assertNotIn("<form", html)
            self.assertNotIn('type="tel"', html)
            self.assertNotIn('type="email"', html)
            self.assertIn("<noscript>", html)
            self.assertEqual(html.count(" disabled>"), 6)
            self.assertNotIn('data-sector-panel="consult" hidden', html)

    def test_all_goals_use_real_order_contract_and_bilingual_report_labels(self):
        for category in SCENARIOS:
            demo = self.demo(category)
            for goal in sector_catalog(category)["goals"]:
                page = self.client.get(reverse("projects:demo_preview", args=[demo.slug]))
                token = page.context["submission_token"]
                response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
                    "submission_token": token, "theme": "sage", "personality": "modern",
                    "brief_goal": goal["key"], "brand_preview": "Sample", "features": ["blog"],
                })
                self.assertEqual(response.status_code, 302)
                selection = DemoSelection.objects.get(submission_token=token)
                self.assertEqual(selection.selections["brief"], {"goal": goal["key"]})
                for lang in ("fa", "en"):
                    self.assertEqual(len(brief_labels(selection.selections["brief"], category, lang)), 1)

    def test_foreign_category_goal_cannot_be_submitted(self):
        demo = self.demo("restaurant")
        page = self.client.get(reverse("projects:demo_preview", args=[demo.slug]))
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "submission_token": page.context["submission_token"], "theme": "sage",
            "personality": "modern", "brief_goal": "courses", "features": ["blog"],
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("invalid=1", response.url)
        self.assertFalse(DemoSelection.objects.exists())

    def test_entire_english_scene_has_no_persian_controls_or_numbers(self):
        for category in SCENARIOS:
            html = render_to_string("projects/demo_scenes/scene.html", {"demo": {"category": category}, "lang": "en"})
            self.assertIsNone(re.search(r"[\u0600-\u06ff]", html), category)
        restaurant = render_to_string("projects/demo_scenes/restaurant.html", {"lang": "en"})
        self.assertIn("220,000 Toman", restaurant)
        self.assertNotIn("$8", restaurant)

    def test_recommendations_are_bounded_to_each_category_and_localized(self):
        for category in SCENARIOS:
            for lang in ("fa", "en"):
                for goal in sector_catalog(category, lang)["goals"]:
                    self.assertTrue(goal["features"])
                    self.assertTrue({f["key"] for f in goal["features"]} <= set(CATEGORY_FEATURE_KEYS[category]))
                    self.assertNotEqual(goal["features"][0]["label"], goal["features"][0]["key"])
                self.assertEqual(sector_catalog(category, lang)["goals"][0]["number"], "۰۱" if lang == "fa" else "01")

    def test_full_sample_recommendations_return_to_preview_not_missing_sheet(self):
        demo = self.demo("education")
        response = self.client.get(reverse("projects:demo_full", args=[demo.slug]))
        self.assertNotContains(response, "data-config-open")
        self.assertContains(response, reverse("projects:demo_preview", args=[demo.slug]) + "#configurator")
        self.assertContains(response, "data-sector-feature-status=")

    def test_fixture_content_is_escaped_without_script_or_html_injection(self):
        sector = sector_catalog("portfolio", "en")
        sector["goals"][0]["title"] = '<img src=x onerror="bad()">'
        html = render_to_string("projects/demo_scenes/sector.html", {"sector": sector, "lang": "en"})
        self.assertNotIn('<img src=x', html)
        self.assertIn("&lt;img", html)
