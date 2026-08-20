from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def service_worker(request):
    """Serve the worker from the origin root with an explicit, non-stale scope."""
    response = HttpResponse(
        render_to_string("core/service-worker.js"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@require_GET
@cache_control(public=True, max_age=300)
def offline(request):
    """A data-free fallback; no authenticated or customer response is cached."""
    response = HttpResponse(render_to_string("core/offline.html"), content_type="text/html; charset=utf-8")
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
