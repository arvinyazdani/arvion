from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """Minimal load-balancer probe; never exposes exception or configuration details."""

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return JsonResponse({"status": "unavailable"}, status=503)
        return JsonResponse({"status": "ok"})
