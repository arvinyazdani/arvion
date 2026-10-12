from django.utils import translation
from django.conf import settings
from django.utils.cache import patch_cache_control, patch_vary_headers


class PublicPageCachePolicyMiddleware:
    """Short shared-cache lifetime only for anonymous, cookieless HTML GETs.

    Runs outside Session/CSRF middleware so cookie decisions are final. Never
    cache form tokens, authenticated output, query-dependent variants or APIs.
    Vary: Cookie separates existing workflow sessions at a compliant CDN.
    """

    PUBLIC_ROUTES = {
        "home", "about", "company_info", "crm_product", "privacy",
        "service_terms", "refund_policy", "services:list", "services:detail",
        "projects:demo_gallery", "projects:demo_preview", "blog:list",
        "blog:detail", "assessments:list", "assessments:briefing",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "text/html" not in response.get("Content-Type", ""):
            return response
        if "no-store" in response.get("Cache-Control", "").lower():
            return response  # Preserve an existing stricter security contract.
        match = getattr(request, "resolver_match", None)
        route = getattr(match, "view_name", "")
        if route in {"offline", "offline_fa", "offline_en"}:
            # These standalone views render no request/user data. Preserve their
            # explicit public cache contract used by the PWA offline fallback.
            return response
        if (request.method != "GET" or response.status_code != 200
                or route not in self.PUBLIC_ROUTES or request.GET
                or request.COOKIES or response.cookies
                or getattr(request, "user", None) and request.user.is_authenticated):
            patch_cache_control(response, private=True, no_store=True, max_age=0)
        elif not response.has_header("Cache-Control"):
            patch_vary_headers(response, ("Cookie",))
            patch_cache_control(response, public=True, max_age=0, s_maxage=60)
        return response


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
