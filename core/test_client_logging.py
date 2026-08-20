import json

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from management_portal.models import SystemLog


class ClientLoggingSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("report_js_error")
        self.origin = "http://testserver"

    def post_report(self, payload, *, origin="http://testserver", content_type="application/json"):
        extra = {"HTTP_ORIGIN": origin} if origin is not None else {}
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type=content_type,
            **extra,
        )

    def test_same_origin_report_is_minimized_before_storage(self):
        response = self.post_report({
            "kind": "TypeError",
            "message": "secret@example.com 09121234567 password=private-value",
            "source": "https://testserver/static/core/js/wizard-engine.js?token=private-value",
            "line": 91,
            "path": "/fa/crm-order/?email=secret@example.com",
        })

        self.assertEqual(response.status_code, 204)
        log = SystemLog.objects.get()
        stored = f"{log.message_fa} {log.detail} {log.path}"
        self.assertEqual(log.category, "frontend")
        self.assertIn("TypeError", log.message_fa)
        self.assertIn("source=wizard-engine.js", log.detail)
        self.assertEqual(log.path, "/fa/crm-order/")
        for sensitive_value in ("secret@example.com", "09121234567", "private-value"):
            self.assertNotIn(sensitive_value, stored)

    def test_cross_origin_and_missing_origin_are_rejected(self):
        payload = {"kind": "Error", "path": "/fa/"}

        self.post_report(payload, origin="https://attacker.example")
        self.post_report(payload, origin=None)

        self.assertFalse(SystemLog.objects.exists())

    def test_unrecognized_error_kind_and_non_json_body_are_not_stored(self):
        self.post_report({"kind": "Customer phone 09121234567", "path": "/fa/"})
        self.post_report({"kind": "Error"}, content_type="text/plain")

        self.assertFalse(SystemLog.objects.exists())

    def test_unrecognized_source_name_is_not_stored(self):
        self.post_report({
            "kind": "Error",
            "source": "https://testserver/static/09121234567.js",
            "path": "/fa/",
        })

        log = SystemLog.objects.get()
        self.assertNotIn("09121234567", log.detail)
        self.assertIn("source=", log.detail)

    def test_oversized_body_is_discarded(self):
        self.post_report({"kind": "Error", "padding": "x" * 3_000, "path": "/fa/"})

        self.assertFalse(SystemLog.objects.exists())

    def test_rate_limit_accepts_at_most_ten_reports_per_hour(self):
        for line in range(15):
            self.post_report({"kind": "Error", "line": line, "path": "/fa/"})

        self.assertEqual(SystemLog.objects.count(), 10)
