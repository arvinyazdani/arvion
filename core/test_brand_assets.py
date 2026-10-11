import json
import struct
from pathlib import Path
from xml.etree import ElementTree

from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils import translation


class BrandAssetTests(SimpleTestCase):
    root = Path(settings.BASE_DIR)

    def test_vector_exports_share_the_approved_silhouette(self):
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        mark = ElementTree.fromstring(render_to_string("core/includes/code_mark.html"))
        path = mark.find("svg:path", namespace).attrib["d"]
        self.assertEqual(mark.attrib["aria-hidden"], "true")
        self.assertEqual(mark.attrib["focusable"], "false")
        for name in ("favicon.svg", "icons/app-icon-maskable.svg"):
            svg = ElementTree.parse(self.root / "core/static/core" / name)
            self.assertEqual(svg.find("svg:path", namespace).attrib["d"], path)

    def test_app_exports_have_exact_dimensions_and_small_payloads(self):
        for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
            data = (self.root / "core/static/core/icons" / name).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", data[16:24]), (size, size))
            self.assertEqual(data[25], 2)  # Opaque RGB; no transparency channel on iOS.
            self.assertLess(len(data), 20_000)

    def test_app_mark_bounding_box_fits_maskable_safe_circle(self):
        # Vector viewBox 628x726, translated by (317,264) in a 1254 square.
        center, safe_radius = 627, 1254 * 0.4
        for x in (317, 945):
            for y in (264, 990):
                self.assertLess((x - center) ** 2 + (y - center) ** 2, safe_radius ** 2)

    def test_affected_standalone_shells_compile(self):
        for name in (
            "core/flow_base.html", "core/offline.html", "core/company_info.html",
            "management_portal/v2/base.html", "accounts/payment_receipt.html",
            "assessments/attempt.html", "assessments/attempt_review.html",
            "assessments/certificate.html", "contracts/contract_base.html",
            "crm_orders/specialist_wizard.html", "crm_orders/specialist_done.html",
        ):
            self.assertIsNotNone(get_template(name))

    def test_manifest_preserves_app_identity_and_references_existing_assets(self):
        manifest = json.loads((self.root / "core/static/core/manifest.webmanifest").read_text())
        self.assertEqual((manifest["id"], manifest["start_url"], manifest["scope"]), ("/fa/", "/fa/", "/"))
        self.assertTrue(any(icon["type"] == "image/png" and "maskable" in icon["purpose"] for icon in manifest["icons"]))
        for icon in manifest["icons"]:
            self.assertTrue((self.root / "core/static" / icon["src"].removeprefix("/static/")).is_file())

    def test_shared_mark_only_and_custom_wrapper_contract_remains_available(self):
        mark = render_to_string("core/includes/brand.html", {"mark_class": "install-logo", "mark_only": True})
        self.assertIn("install-logo", mark)
        self.assertIn("rvion-code-glyph", mark)
        self.assertNotIn("brand-wordmark", mark)
        self.assertIn('dir="ltr">Rvion</span>', render_to_string("core/includes/brand.html"))


class BrandShellTests(TestCase):
    def test_both_languages_render_new_header_footer_and_install_mark(self):
        self.addCleanup(translation.deactivate_all)
        for lang in ("fa", "en"):
            response = self.client.get(f"/{lang}/account/login/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "rvion-code-glyph", count=4)
            self.assertContains(response, 'sizes="180x180"')
            self.assertContains(response, "core/icons/apple-touch-icon.png")
            self.assertNotContains(response, "app-icon-concept.png")
            self.assertNotContains(response, "logo-light-concept.png")

    def test_worker_rotates_old_icon_cache_and_precaches_all_exports(self):
        response = self.client.get("/service-worker.js")
        self.assertContains(response, 'const CACHE = "rvion-shell-v6"')
        for name in ("icon-192.png", "icon-512.png", "apple-touch-icon.png"):
            self.assertContains(response, f"/static/core/icons/{name}")
