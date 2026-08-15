from django.conf import settings
from django.middleware.csrf import get_token


def management_alerts(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    get_token(request)  # Push subscription POST must work even on read-only dashboard pages.
    current_lang = getattr(request, "LANGUAGE_CODE", "fa")
    other_lang = "en" if current_lang == "fa" else "fa"
    path_parts = request.path.split("/")
    if len(path_parts) > 1 and path_parts[1] in {"fa", "en"}:
        path_parts[1] = other_lang
    language_switch_url = "/".join(path_parts)
    if request.META.get("QUERY_STRING"):
        language_switch_url += "?" + request.META["QUERY_STRING"]
    return {
        "web_push_public_key": settings.WEB_PUSH_VAPID_PUBLIC_KEY,
        "unread_count": request.user.notification_receipts.filter(seen_at__isnull=True, notification__status="unread").count(),
        "language_switch_url": language_switch_url,
    }
