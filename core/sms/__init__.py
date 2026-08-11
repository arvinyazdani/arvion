from django.conf import settings
from django.utils.module_loading import import_string


def get_sms_backend():
    """Return the configured SMS backend without retaining secrets globally."""
    return import_string(settings.SMS_BACKEND)()


def send_sms(to, text):
    return get_sms_backend().send(to=to, text=text)


def send_otp(to, code, *, body_id=None):
    return get_sms_backend().send_otp(to=to, code=code, body_id=body_id)
