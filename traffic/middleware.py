import hashlib
import logging

from django.conf import settings
from django.db import DatabaseError, transaction
from django.db.models import F
from django.utils import timezone

from .models import ActiveVisitor, DailyVisitor, TrafficDay

logger = logging.getLogger(__name__)


class TrafficAnalyticsMiddleware:
    EXCLUDED_PREFIXES = ("/admin/", "/health/", "/static/", "/media/", "/favicon.ico", "/robots.txt")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._eligible(request, response):
            self._record(request)
        return response

    def _eligible(self, request, response):
        content_type = response.get("Content-Type", "")
        return request.method == "GET" and response.status_code < 400 and "text/html" in content_type and not request.path.startswith(self.EXCLUDED_PREFIXES)

    def _record(self, request):
        try:
            if not request.session.session_key:
                request.session.create()
            digest = hashlib.sha256(f"{settings.SECRET_KEY}:{request.session.session_key}".encode()).hexdigest()
            now = timezone.now()
            today = timezone.localdate(now)
            with transaction.atomic():
                TrafficDay.objects.get_or_create(date=today)
                TrafficDay.objects.filter(date=today).update(page_views=F("page_views") + 1)
                _, created = DailyVisitor.objects.get_or_create(date=today, visitor_hash=digest)
                if created:
                    TrafficDay.objects.filter(date=today).update(unique_visitors=F("unique_visitors") + 1)
                ActiveVisitor.objects.update_or_create(
                    visitor_hash=digest,
                    defaults={"last_seen": now, "path": request.path[:160], "is_authenticated": request.user.is_authenticated},
                )
        except DatabaseError:
            logger.warning("Traffic analytics write skipped because the database was unavailable", exc_info=True)
