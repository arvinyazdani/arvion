import json
import logging
import unicodedata
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


class SMSDeliveryError(RuntimeError):
    """Raised when the provider rejects or cannot receive a message."""


@dataclass(frozen=True)
class SMSResult:
    provider: str
    reference: str
    accepted: bool = True


def normalize_iran_mobile(value):
    digits = "".join(
        str(unicodedata.digit(ch))
        for ch in str(value).strip()
        if ch.isdecimal()
    )
    if digits.startswith("0098"):
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = "98" + digits[1:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "98" + digits
    if len(digits) != 12 or not digits.startswith("989"):
        raise ValueError("شماره موبایل ایران معتبر نیست.")
    return digits


def melipayamak_recipient(value):
    """Return the local 09… format accepted by Melipayamak's REST API."""
    canonical = normalize_iran_mobile(value)
    return "0" + canonical[2:]


class ConsoleSMSBackend:
    """Safe development backend; it never calls an external provider."""

    def send(self, *, to, text):
        mobile = normalize_iran_mobile(to)
        logger.info("Development SMS accepted for %s (length=%d)", mobile[-4:], len(text))
        return SMSResult(provider="console", reference="console")

    def send_otp(self, *, to, code, body_id=None):
        return self.send(to=to, text=str(code))


class MelipayamakSMSBackend:
    SEND_URL = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
    OTP_URL = "https://rest.payamak-panel.com/api/SendSMS/BaseServiceNumber"

    def __init__(self):
        self.username = settings.MELIPAYAMAK_USERNAME
        self.password = settings.MELIPAYAMAK_PASSWORD
        self.sender = settings.MELIPAYAMAK_SENDER_NUMBER
        self.default_body_id = settings.MELIPAYAMAK_BODY_ID
        self.otp_mode = settings.MELIPAYAMAK_OTP_MODE
        self.timeout = settings.SMS_HTTP_TIMEOUT
        if not self.username or not self.password or not self.sender:
            raise ImproperlyConfigured("تنظیمات اتصال ملی‌پیامک کامل نیست.")

    def _post(self, url, payload):
        request = Request(
            url,
            data=urlencode(payload).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise SMSDeliveryError("ارتباط با سرویس پیامک برقرار نشد.") from exc
        try:
            result = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise SMSDeliveryError("پاسخ سرویس پیامک قابل پردازش نبود.") from exc
        if result.get("RetStatus") != 1:
            status = str(result.get("StrRetStatus") or "provider_rejected")[:120]
            raise SMSDeliveryError(f"سرویس پیامک درخواست را نپذیرفت: {status}")
        return SMSResult(provider="melipayamak", reference=str(result.get("Value") or ""))

    def send(self, *, to, text):
        if not str(text).strip():
            raise ValueError("متن پیامک نمی‌تواند خالی باشد.")
        return self._post(self.SEND_URL, {
            "username": self.username,
            "password": self.password,
            "from": self.sender,
            "to": melipayamak_recipient(to),
            "text": str(text),
            "isFlash": "false",
        })

    def send_otp(self, *, to, code, body_id=None):
        template_id = str(body_id or self.default_body_id).strip()
        if self.otp_mode != "pattern" and not body_id:
            return self.send(
                to=to,
                text=f"کد تأیید آرویون: {code}\nاین کد ۵ دقیقه اعتبار دارد.",
            )
        if not template_id:
            raise ImproperlyConfigured("MELIPAYAMAK_BODY_ID برای حالت pattern تنظیم نشده است.")
        return self._post(self.OTP_URL, {
            "username": self.username,
            "password": self.password,
            "to": melipayamak_recipient(to),
            "text": str(code),
            "bodyId": template_id,
        })
