# core/views/client_logging.py
# نقطه پایانی عمومی برای ثبت حداقلی خطاهای جاوااسکریپت مرورگر کاربر در لاگ سیستم

import hashlib
import json
import posixpath
import re
from urllib.parse import urlsplit

from django.core.cache import cache
from django.http import HttpResponse
from django.urls import Resolver404, resolve
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.security import client_address, normalized_fingerprint


MAX_BODY_BYTES = 2_048
MAX_REPORTS_PER_HOUR = 10
ALLOWED_ERROR_KINDS = {
    "Error", "EvalError", "InternalError", "RangeError", "ReferenceError",
    "SyntaxError", "TypeError", "URIError", "UnhandledRejection",
}
SAFE_SOURCE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
ALLOWED_SOURCE_NAMES = {
    "admin-charts.js", "admin-persian.js", "error-report.js", "persian-ui.js",
    "site-shell.js", "staff-push.js", "theme-toggle.js", "wizard-engine.js",
}


def _origin_tuple(value):
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            return None
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return parsed.scheme, parsed.hostname.casefold(), port
    except (TypeError, ValueError):
        return None


def _is_same_origin(request):
    supplied = _origin_tuple(request.headers.get("Origin", ""))
    expected = _origin_tuple(f"{request.scheme}://{request.get_host()}")
    return supplied is not None and supplied == expected


def _safe_route(value):
    """Return the Django route pattern, never raw path parameters or query data."""
    try:
        path = urlsplit(str(value or "")).path
        if not path.startswith("/") or len(path) > 500:
            return ""
        match = resolve(path)
    except (Resolver404, TypeError, ValueError):
        return ""
    return ("/" + str(match.route).lstrip("/"))[:300]


def _safe_source(value):
    name = posixpath.basename(urlsplit(str(value or "")).path)
    return name if SAFE_SOURCE_NAME.fullmatch(name) and name in ALLOWED_SOURCE_NAMES else ""


@csrf_exempt
@require_POST
def report_js_error(request):
    # sendBeacon امکان افزودن CSRF header ندارد؛ Origin اجباری، آن را به همان دامنه محدود می‌کند.
    if not _is_same_origin(request) or request.content_type != "application/json":
        return HttpResponse(status=204)

    key = f"js-error-report:{normalized_fingerprint(client_address(request))}"
    if cache.add(key, 1, 3600):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, 3600)
            count = 1
    if count > MAX_REPORTS_PER_HOUR:
        return HttpResponse(status=204)

    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        if content_length > MAX_BODY_BYTES:
            return HttpResponse(status=204)
        raw_body = request.read(MAX_BODY_BYTES + 1)
        if len(raw_body) > MAX_BODY_BYTES:
            return HttpResponse(status=204)
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            return HttpResponse(status=204)
    except (TypeError, ValueError, UnicodeDecodeError):
        return HttpResponse(status=204)

    supplied_kind = str(payload.get("kind") or payload.get("message") or "").split(":", 1)[0]
    kind = supplied_kind if supplied_kind in ALLOWED_ERROR_KINDS else ""
    if not kind:
        return HttpResponse(status=204)
    source = _safe_source(payload.get("source"))
    path = _safe_route(payload.get("path"))
    try:
        line = int(payload.get("line") or 0)
    except (TypeError, ValueError):
        line = 0
    line = line if 0 <= line <= 1_000_000 else 0
    signature_input = f"{kind}|{source}|{line}|{path}".encode("utf-8")
    signature = hashlib.sha256(signature_input).hexdigest()[:16]

    from management_portal.models import SystemLog

    SystemLog.objects.create(
        level="warning",
        category="frontend",
        message_fa=f"خطای جاوااسکریپت گزارش‌شده از مرورگر ({kind})",
        detail=f"signature={signature} source={source} line={line}",
        path=path,
    )
    return HttpResponse(status=204)
