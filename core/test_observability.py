from django.test import SimpleTestCase

from core.observability import _before_send, _before_send_transaction, _sample_rate


class SentryPrivacyTests(SimpleTestCase):
    def test_error_event_excludes_customer_request_data_and_sensitive_extras(self):
        event = {
            "user": {"email": "customer@example.com", "ip_address": "127.0.0.1"},
            "request": {
                "headers": {"Authorization": "Bearer secret"},
                "cookies": {"sessionid": "private"},
                "data": {"password": "private"},
                "env": {"REMOTE_ADDR": "127.0.0.1"},
            },
            "extra": {"password": "private", "safe": "technical"},
        }

        cleaned = _before_send(event, None)

        self.assertNotIn("user", cleaned)
        self.assertEqual(cleaned["request"], {})
        self.assertEqual(cleaned["extra"]["password"], "[Filtered]")
        self.assertEqual(cleaned["extra"]["safe"], "technical")

    def test_transaction_event_excludes_request_payload(self):
        event = {"request": {"headers": {"Cookie": "private"}, "data": {"phone": "0912"}}}

        cleaned = _before_send_transaction(event, None)

        self.assertEqual(cleaned["request"], {})

    def test_sample_rate_is_bounded(self):
        self.assertEqual(_sample_rate("MISSING_RATE", 0.1), 0.1)
