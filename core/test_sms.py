import json
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from core.sms.backends import MelipayamakSMSBackend, SMSDeliveryError, normalize_iran_mobile


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class SMSBackendTests(SimpleTestCase):
    settings = override_settings(
        MELIPAYAMAK_USERNAME="9333021100",
        MELIPAYAMAK_PASSWORD="secret",
        MELIPAYAMAK_SENDER_NUMBER="50004001021100",
        MELIPAYAMAK_BODY_ID="42",
        SMS_HTTP_TIMEOUT=2,
    )

    def test_normalizes_supported_iran_mobile_formats(self):
        for value in ("09120373271", "9120373271", "+98 912 037 3271", "00989120373271"):
            self.assertEqual(normalize_iran_mobile(value), "989120373271")

    @settings
    @patch("core.sms.backends.urlopen")
    def test_sends_regular_sms_as_form_data(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "tracking-id", "RetStatus": 1, "StrRetStatus": "Ok"})
        result = MelipayamakSMSBackend().send(to="09120373271", text="سلام")
        request = mocked_open.call_args.args[0]
        self.assertEqual(result.reference, "tracking-id")
        self.assertIn(b"from=50004001021100", request.data)
        self.assertIn(b"to=989120373271", request.data)
        self.assertNotIn(b"secret", str(request.headers).encode())

    @settings
    @patch("core.sms.backends.urlopen")
    def test_sends_otp_with_approved_body_id(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "otp-id", "RetStatus": 1, "StrRetStatus": "Ok"})
        MelipayamakSMSBackend().send_otp(to="09120373271", code="123456")
        request = mocked_open.call_args.args[0]
        self.assertIn(b"bodyId=42", request.data)
        self.assertIn(b"text=123456", request.data)

    @override_settings(
        MELIPAYAMAK_USERNAME="9333021100", MELIPAYAMAK_PASSWORD="secret",
        MELIPAYAMAK_SENDER_NUMBER="50004001021100", MELIPAYAMAK_BODY_ID="",
        SMS_HTTP_TIMEOUT=2,
    )
    def test_refuses_otp_without_template(self):
        with self.assertRaises(ImproperlyConfigured):
            MelipayamakSMSBackend().send_otp(to="09120373271", code="123456")

    @settings
    @patch("core.sms.backends.urlopen")
    def test_raises_safe_error_when_provider_rejects(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "", "RetStatus": 0, "StrRetStatus": "Error"})
        with self.assertRaises(SMSDeliveryError):
            MelipayamakSMSBackend().send(to="09120373271", text="سلام")
