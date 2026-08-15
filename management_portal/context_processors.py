from django.conf import settings


def management_alerts(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    return {
        "web_push_public_key": settings.WEB_PUSH_VAPID_PUBLIC_KEY,
        "unread_count": request.user.notification_receipts.filter(seen_at__isnull=True, notification__status="unread").count(),
    }
