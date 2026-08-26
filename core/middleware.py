from django.utils import translation
from django.conf import settings


class FriendlyMethodNotAllowedMiddleware:
    """Replace bare HTML 405 responses with the branded recovery page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        accepts_html = "text/html" in request.headers.get("Accept", "text/html")
        if response.status_code != 405 or not accepts_html:
            return response

        from core.views.errors import method_not_allowed

        rendered = method_not_allowed(request)
        if response.has_header("Allow"):
            rendered["Allow"] = response["Allow"]
        return rendered


class SecurityResponseHeadersMiddleware:
    """Apply browser security boundaries consistently to public and staff pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.CONTENT_SECURITY_POLICY:
            response.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)
        if settings.PERMISSIONS_POLICY:
            response.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response


class AdminPersianLocaleMiddleware:
    """Keep the operational admin Persian regardless of the public-site language cookie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            translation.activate("fa")
            request.LANGUAGE_CODE = "fa"
        return self.get_response(request)
