from django.shortcuts import render


def csrf_failure(request, reason=""):
    """Return a safe, actionable response without weakening CSRF protection."""
    lang = "en" if request.path.startswith("/en/") else "fa"
    response = render(request, "core/csrf_failure.html", {"lang": lang}, status=403)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response
