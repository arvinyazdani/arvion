from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import Resolver404, resolve


def csrf_failure(request, reason=""):
    """Return a safe, actionable response without weakening CSRF protection."""
    # A stale contract form commonly occurs when the owner publishes a corrected
    # version while the customer still has the previous page open. Do not expose a
    # raw 403: return them to the guarded entry point where a fresh token is issued.
    try:
        match = resolve(request.path)
    except Resolver404:
        match = None
    if match and match.namespace == "contracts" and match.kwargs.get("token"):
        messages.warning(request, "فرم تأیید منقضی شده یا نسخهٔ پرونده تغییر کرده است. برای ادامه، صفحهٔ ورود قرارداد را تازه کنید.")
        return redirect("contracts:contract_access", token=match.kwargs["token"])
    lang = "en" if request.path.startswith("/en/") else "fa"
    response = render(request, "core/csrf_failure.html", {"lang": lang}, status=403)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response
