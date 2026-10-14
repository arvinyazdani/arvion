from django.http import HttpResponse

from core.indexnow import INDEXNOW_KEY


def indexnow_key_file(request, key):
    if key != INDEXNOW_KEY:
        return HttpResponse(status=404)
    response = HttpResponse(key, content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "public, max-age=86400"
    response["X-Robots-Tag"] = "noindex"
    return response
