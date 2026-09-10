from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .models import DemoSelection, DemoTemplate, Project


class ProjectTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(title_fa="پروژه", title_en="Project", slug="project", is_active=True)

    def test_project_uses_slug_url(self):
        response = self.client.get(reverse("projects:detail", args=["project"]), {"lang": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project")

    def test_project_labels_follow_page_language(self):
        fa_list = self.client.get(reverse("projects:list") + "?lang=fa")
        self.assertRedirects(fa_list, reverse("projects:demo_gallery"), status_code=302, fetch_redirect_response=False)

        en_detail = self.client.get(reverse("projects:detail", args=["project"]) + "?lang=en")
        self.assertContains(en_detail, "Case study")
        self.assertContains(en_detail, "LINKS")
        self.assertNotContains(en_detail, "مطالعه موردی")

    def test_inactive_project_is_hidden(self):
        self.project.is_active = False
        self.project.save()
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 404)

    def test_gallery_shows_fictional_demos_and_configurator_creates_session_selection(self):
        demo = DemoTemplate.objects.create(
            slug="demo-test", category="ecommerce", title_fa="دموی تست", title_en="Test demo",
            tagline_fa="نمونه فرضی", tagline_en="Fictional demo", fictional_brand_fa="برند فرضی",
            fictional_brand_en="TEST BRAND", style_key="minimal", default_features=["payment"],
        )
        gallery = self.client.get(reverse("projects:demo_gallery") + "?lang=fa")
        self.assertContains(gallery, "دموی تست")
        self.assertContains(gallery, "بدون ثبت‌نام")
        self.assertContains(gallery, "بازکردن و شخصی‌سازی")
        preview = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
        self.assertContains(preview, "برند فرضی")
        self.assertContains(preview, reverse("projects:demo_full", args=[demo.slug]))
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "brand_preview": "فروشگاه من", "theme": "custom", "custom_color": "#123abc",
            "personality": "minimal", "features": ["payment", "catalog"],
        })
        selection = DemoSelection.objects.get()
        self.assertRedirects(response, reverse("leads:contact") + f"?demo={selection.public_token}&request_type=ecommerce")
        self.assertEqual(selection.selections["features"], ["payment", "catalog"])
        self.assertEqual(selection.selections["brand"], "فروشگاه من")
        self.assertEqual(selection.selections["custom_color"], "#123abc")

        full = self.client.get(reverse("projects:demo_full", args=[demo.slug]) + "?lang=fa")
        self.assertContains(full, 'content="noindex,nofollow"', html=False)
        self.assertContains(full, "بازگشت به انتخاب‌ها")
        self.assertContains(full, 'data-demo-view="desktop"', html=False)
        self.assertContains(full, 'data-demo-view="mobile"', html=False)

    def test_invalid_custom_colour_is_rejected_without_creating_selection(self):
        demo = DemoTemplate.objects.create(
            slug="invalid-colour", category="portfolio", title_fa="تست", title_en="Test",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="editorial", default_features=[],
        )
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "theme": "custom", "custom_color": "not-a-colour", "personality": "editorial",
        })
        self.assertRedirects(
            response,
            reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1",
            fetch_redirect_response=False,
        )
        self.assertFalse(DemoSelection.objects.exists())

    def test_configurator_is_single_page_and_preserves_state_between_views(self):
        script = (Path(settings.BASE_DIR) / "projects/static/projects/js/demo-configurator.js").read_text(encoding="utf-8")
        self.assertIn("history.replaceState", script)
        self.assertIn("sessionStorage.setItem", script)
        self.assertIn('state.theme = "custom"', script)
        self.assertIn('setAttribute("aria-pressed"', script)
        self.assertIn("data-demo-back", script)
        self.assertNotIn("location.reload", script)
