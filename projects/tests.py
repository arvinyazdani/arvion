from django.test import TestCase
from django.urls import reverse

from .models import Project


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
