import json
import re
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from leads.models import Lead
from projects.models import DemoSelection, DemoTemplate
from projects.storefront_catalog import storefront_catalog


class StorefrontTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.demo = DemoTemplate.objects.create(slug="reference-store", category="ecommerce", title_fa="فروشگاه مرجع", title_en="Reference store", fictional_brand_fa="نوا", fictional_brand_en="NAVA", default_features=["catalog", "payment"], is_active=True)

    def test_catalog_has_six_products_and_consistent_integer_prices(self):
        for lang in ("fa", "en"):
            data = storefront_catalog(lang)
            self.assertEqual(len(data["products"]), 6)
            self.assertEqual(len({p["id"] for p in data["products"]}), 6)
            for product in data["products"]:
                self.assertEqual(len(product["specs"]), 2)
                self.assertEqual(len(product["variants"]), 6)
                self.assertEqual(len(product["sizes"]), 2)
                self.assertTrue(all(isinstance(v["price"], int) and v["price"] > 0 for v in product["variants"]))
            self.assertEqual(data["products"][0]["variants"][4]["stock"], 0)
        self.assertEqual([p["price"] for p in storefront_catalog("fa")["products"]], [p["price"] for p in storefront_catalog("en")["products"]])

    def test_preview_and_full_include_same_local_catalog_and_controls(self):
        for route in ("projects:demo_preview", "projects:demo_full"):
            response = self.client.get(reverse(route, args=[self.demo.slug]))
            self.assertContains(response, "storefront-model.js")
            self.assertContains(response, "storefront.js")
            self.assertContains(response, "storefront.css")
            self.assertContains(response, 'data-store-product=', count=6)
            self.assertContains(response, 'data-store-detail aria-labelledby="store-detail-title"')
            self.assertContains(response, 'data-store-cart aria-labelledby="store-cart-title"')
            match = re.search(r'<script id="storefront-catalog" type="application/json">(.*?)</script>', response.content.decode(), re.S)
            self.assertEqual(json.loads(match[1]), storefront_catalog("fa"))

    def test_english_store_slice_is_fully_english(self):
        with translation.override("en"):
            response = self.client.get(reverse("projects:demo_preview", args=[self.demo.slug]))
        scene = response.content.decode().split('data-storefront>', 1)[1].split('</section>', 1)[0]
        self.assertIsNone(re.search(r"[\u0600-\u06ff]", scene))
        self.assertIn("No real order is placed", scene)

    def test_rendering_basket_has_no_database_effects(self):
        counts = (Lead.objects.count(), DemoSelection.objects.count())
        for route in ("projects:demo_preview", "projects:demo_full"):
            self.client.get(reverse(route, args=[self.demo.slug]))
        self.assertEqual(counts, (Lead.objects.count(), DemoSelection.objects.count()))

    def test_other_categories_do_not_load_store_scripts(self):
        self.demo.category = "restaurant"
        self.demo.save()
        response = self.client.get(reverse("projects:demo_preview", args=[self.demo.slug]))
        self.assertNotContains(response, "storefront-model.js")
        self.assertNotContains(response, "data-storefront")

    def test_json_script_safely_escapes_fixture_content(self):
        catalog = storefront_catalog("en")
        catalog["products"][0]["name"] = '</script><img src=x onerror="alert(1)">'
        with patch("projects.templatetags.demo_store.storefront_catalog", return_value=catalog):
            html = render_to_string("projects/demo_scenes/ecommerce.html", {"lang": "en"})
        self.assertNotIn('</script><img', html)
        self.assertIn(r"\u003C/script\u003E", html)

    def test_sample_has_no_contact_payment_fields_and_a_no_js_recovery(self):
        html = render_to_string("projects/demo_scenes/ecommerce.html", {"lang": "en"})
        self.assertNotIn("<form", html)
        self.assertNotIn('type="email"', html)
        self.assertNotIn('type="tel"', html)
        self.assertIn("Enable JavaScript", html)
        self.assertIn("No personal or banking details", html)
        self.assertIn('aria-describedby="store-quantity-error"', html)
        self.assertIn('id="store-quantity-error"', html)
