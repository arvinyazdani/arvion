from django.shortcuts import render


def _language(request):
    language = getattr(request, "LANGUAGE_CODE", "")
    if language in {"fa", "en"}:
        return language
    return "en" if request.path.startswith("/en/") else "fa"


def _is_management_request(request):
    return "/management/" in request.path and getattr(request.user, "is_staff", False)


def _render_error(request, status, *, management=False):
    context = {"lang": _language(request), "error_status": status, "seo_noindex": True}
    template = "management_portal/v2/error.html" if management else "core/error.html"
    return render(request, template, context, status=status)


def permission_denied(request, exception=None):
    return _render_error(request, 403, management=_is_management_request(request))


def page_not_found(request, exception=None):
    return _render_error(request, 404, management=_is_management_request(request))


def method_not_allowed(request):
    return _render_error(request, 405, management=_is_management_request(request))


def server_error(request):
    # Keep the 500 template standalone so it remains renderable when an app,
    # database query, or context processor is the original failure source.
    return render(request, "core/server_error.html", {"lang": _language(request)}, status=500)
