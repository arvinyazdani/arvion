import json
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from core.sms.backends import (
    MelipayamakSMSBackend,
    SMSDeliveryError,
    melipayamak_recipient,
    normalize_iran_mobile,
)


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
        for value in (
            "09120373271",
            "9120373271",
            "+98 912 037 3271",
            "00989120373271",
            "۰۹۱۲۰۳۷۳۲۷۱",
            "+۹۸ ۹۱۲ ۰۳۷ ۳۲۷۱",
            "٠٩١٢٠٣٧٣٢٧١",
        ):
            self.assertEqual(normalize_iran_mobile(value), "989120373271")

    def test_formats_all_supported_inputs_for_melipayamak(self):
        for value in ("09120373271", "9120373271", "+989120373271", "۰۰۹۸۹۱۲۰۳۷۳۲۷۱"):
            self.assertEqual(melipayamak_recipient(value), "09120373271")

    def test_rejects_invalid_iran_mobile_numbers(self):
        for value in ("", "02112345678", "0912037327", "9891203732719"):
            with self.assertRaises(ValueError):
                normalize_iran_mobile(value)

    @settings
    @patch("core.sms.backends.urlopen")
    def test_sends_regular_sms_as_form_data(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "tracking-id", "RetStatus": 1, "StrRetStatus": "Ok"})
        result = MelipayamakSMSBackend().send(to="09120373271", text="سلام")
        request = mocked_open.call_args.args[0]
        self.assertEqual(result.reference, "tracking-id")
        self.assertIn(b"from=50004001021100", request.data)
        self.assertIn(b"to=09120373271", request.data)
        self.assertIn(b"isflash=false", request.data)
        self.assertNotIn(b"secret", str(request.headers).encode())

    @settings
    @patch("core.sms.backends.urlopen")
    def test_sends_otp_as_free_text_without_body_id(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "otp-id", "RetStatus": 1, "StrRetStatus": "Ok"})
        MelipayamakSMSBackend().send_otp(to="09120373271", code="123456")
        request = mocked_open.call_args.args[0]
        self.assertIn(b"text=%DA%A9%D8%AF+%D8%AA%D8%A3%DB%8C%DB%8C%D8%AF+%D8%A2%D8%B1%D9%88%DB%8C%D9%88%D9%86%3A+123456", request.data)
        self.assertNotIn(b"bodyId", request.data)
        self.assertIn(b"to=09120373271", request.data)

    @override_settings(
        MELIPAYAMAK_USERNAME="9333021100", MELIPAYAMAK_PASSWORD="secret",
        MELIPAYAMAK_SENDER_NUMBER="50004001021100", MELIPAYAMAK_BODY_ID="",
        SMS_HTTP_TIMEOUT=2,
    )
    def test_pattern_mode_requires_template(self):
        with override_settings(MELIPAYAMAK_OTP_MODE="pattern"):
            with self.assertRaises(ImproperlyConfigured):
                MelipayamakSMSBackend().send_otp(to="09120373271", code="123456")

    @settings
    @patch("core.sms.backends.urlopen")
    def test_sends_otp_with_approved_pattern_payload(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "otp-id", "RetStatus": 1, "StrRetStatus": "Ok"})
        with override_settings(MELIPAYAMAK_OTP_MODE="pattern"):
            MelipayamakSMSBackend().send_otp(to="+989120373271", code="123456")
        request = mocked_open.call_args.args[0]
        self.assertEqual(request.full_url, MelipayamakSMSBackend.OTP_URL)
        self.assertIn(b"to=09120373271", request.data)
        self.assertIn(b"text=123456", request.data)
        self.assertIn(b"bodyId=42", request.data)

    @settings
    @patch("core.sms.backends.urlopen")
    def test_raises_safe_error_when_provider_rejects(self, mocked_open):
        mocked_open.return_value = FakeResponse({"Value": "", "RetStatus": 0, "StrRetStatus": "Error"})
        with self.assertRaises(SMSDeliveryError):
            MelipayamakSMSBackend().send(to="09120373271", text="سلام")
