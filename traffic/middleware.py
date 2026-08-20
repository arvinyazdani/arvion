import hashlib
import logging

from django.conf import settings
from django.db import DatabaseError, transaction
from django.db.models import F
from django.utils import timezone

from .models import ActiveVisitor, DailyVisitor, TrafficDay

logger = logging.getLogger(__name__)


class TrafficAnalyticsMiddleware:
    EXCLUDED_PREFIXES = (
        "/admin/", "/health/", "/static/", "/media/", "/favicon.ico",
        "/robots.txt", "/sitemap.xml", "/service-worker.js", "/offline/",
    )
    PRIVATE_NAMESPACES = {"accounts", "contracts", "management_portal"}
    PRIVATE_ROUTE_NAMES = {
        ("assessments", "checkout"),
        ("assessments", "sandbox_pay"),
        ("assessments", "manual_payment_submit"),
        ("assessments", "manual_payment_status"),
        ("assessments", "start_attempt"),
        ("assessments", "attempt"),
        ("assessments", "attempt_review"),
        ("assessments", "save_answer"),
        ("assessments", "audio_play"),
        ("assessments", "integrity_event"),
        ("assessments", "finish_attempt"),
        ("assessments", "result"),
        ("assessments", "support_create"),
        ("assessments", "support_history"),
        ("crm_orders", "thanks"),
        ("crm_orders", "specialist"),
        ("crm_orders", "specialist_section"),
        ("crm_orders", "specialist_done"),
        ("clinic_orders", "thanks"),
        ("leads", "thanks"),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._eligible(request, response):
            self._record(request)
        return response

    def _eligible(self, request, response):
        content_type = response.get("Content-Type", "")
        match = getattr(request, "resolver_match", None)
        route_identity = (getattr(match, "namespace", ""), getattr(match, "url_name", ""))
        is_private_route = bool(
            match and (
                match.namespace in self.PRIVATE_NAMESPACES
                or route_identity in self.PRIVATE_ROUTE_NAMES
            )
        )
        return (
            request.method == "GET"
            and response.status_code < 400
            and "text/html" in content_type
            and not request.path.startswith(self.EXCLUDED_PREFIXES)
            and not is_private_route
        )

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
