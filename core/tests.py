from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.urls import reverse

from .i18n_numbers import normalize_digits, persian_digits


class CorePagesTests(TestCase):
    def test_health_check_confirms_database_connection(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_fails_closed_without_leaking_error(self):
        with patch.object(connection, "cursor", side_effect=RuntimeError("database secret detail")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "secret detail", status_code=503)

    def test_home_defaults_to_persian(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["lang"], "fa")
        self.assertContains(response, "ایده‌ات را")

    def test_persian_and_arabic_digits_are_normalized(self):
        self.assertEqual(normalize_digits("۱۲٣٫۴۵"), "123.45")

    def test_ascii_digits_are_rendered_as_persian(self):
        self.assertEqual(persian_digits("2026 / 50"), "۲۰۲۶ / ۵۰")

    def test_language_is_kept_in_session(self):
        self.client.get(reverse("home"), {"lang": "en"})
        response = self.client.get(reverse("about"))
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, "Technology should")

    def test_invalid_language_falls_back_to_persian(self):
        response = self.client.get(reverse("home"), {"lang": "xx"})
        self.assertEqual(response.context["lang"], "fa")
