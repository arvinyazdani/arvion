"""Privacy-first Sentry setup for the Django application.

The DSN is supplied only by the production environment.  The SDK receives
technical error and timing data; customer form values, request headers,
cookies, IP addresses and local variables are deliberately excluded.
"""

from __future__ import annotations

import os


SENSITIVE_KEYS = frozenset({
    "authorization", "cookie", "csrfmiddlewaretoken", "password", "password1",
    "password2", "token", "access_token", "api_key", "secret", "otp", "code",
    "card_number", "card_payment_number", "melipayamak_password",
})


def _sample_rate(name: str, default: float) -> float:
    """Read a bounded sampling rate without breaking a production boot."""
    try:
        return min(1.0, max(0.0, float(os.getenv(name, str(default)))))
    except ValueError:
        return default


def _scrub_mapping(value):
    if not isinstance(value, dict):
        return value
    return {
        key: "[Filtered]" if str(key).lower() in SENSITIVE_KEYS else _scrub_mapping(item)
        for key, item in value.items()
    }


def _before_send(event, hint):
    """Remove data that can identify a customer before an error leaves Rvion."""
    event.pop("user", None)
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("headers", None)
        request.pop("cookies", None)
        request.pop("data", None)
        request.pop("env", None)
    if "extra" in event:
        event["extra"] = _scrub_mapping(event["extra"])
    return event


def _before_send_transaction(event, hint):
    """Performance events keep route timing but never retain request payloads."""
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("headers", None)
        request.pop("cookies", None)
        request.pop("data", None)
        request.pop("env", None)
    return event


def initialize_sentry():
    """Enable monitoring only when a DSN has explicitly been configured."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=os.getenv("SENTRY_RELEASE", "").strip() or None,
        send_default_pii=False,
        enable_logs=False,
        enable_tracing=_sample_rate("SENTRY_TRACES_SAMPLE_RATE", 0.10) > 0,
        traces_sample_rate=_sample_rate("SENTRY_TRACES_SAMPLE_RATE", 0.10),
        profiles_sample_rate=_sample_rate("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
        max_request_body_size="never",
        include_local_variables=False,
        max_breadcrumbs=30,
        before_send=_before_send,
        before_send_transaction=_before_send_transaction,
    )
