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
        self.assertContains(fa_list, "پروژه‌های منتخب")
        self.assertContains(fa_list, "پروژه / ")
        self.assertNotContains(fa_list, "Selected work")
        self.assertNotContains(fa_list, "PROJECT / ")

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
        preview = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
        self.assertContains(preview, "برند فرضی")
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "theme": "warm", "personality": "minimal", "features": ["payment", "catalog"],
        })
        selection = DemoSelection.objects.get()
        self.assertRedirects(response, reverse("leads:contact") + f"?demo={selection.public_token}&request_type=ecommerce")
        self.assertEqual(selection.selections["features"], ["payment", "catalog"])
