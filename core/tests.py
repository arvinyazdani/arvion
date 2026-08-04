from django.test import TestCase
from django.urls import reverse


class CorePagesTests(TestCase):
    def test_home_defaults_to_persian(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["lang"], "fa")
        self.assertContains(response, "ایده‌ات را")

    def test_language_is_kept_in_session(self):
        self.client.get(reverse("home"), {"lang": "en"})
        response = self.client.get(reverse("about"))
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, "Technology should")

    def test_invalid_language_falls_back_to_persian(self):
        response = self.client.get(reverse("home"), {"lang": "xx"})
        self.assertEqual(response.context["lang"], "fa")
