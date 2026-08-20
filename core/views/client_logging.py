# core/views/client_logging.py
# نقطه پایانی عمومی برای ثبت خطاهای جاوااسکریپت مرورگر کاربر در لاگ سیستم

import json

from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.security import client_address, normalized_fingerprint


@csrf_exempt
@require_POST
def report_js_error(request):
    key = f"js-error-report:{normalized_fingerprint(client_address(request))}"
    count = cache.get(key, 0)
    if count >= 20:  # سقف نرخ برای جلوگیری از سوءاستفاده
        return HttpResponse(status=204)
    cache.set(key, count + 1, 3600)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=204)

    message = str(payload.get("message", ""))[:280]
    source = str(payload.get("source", ""))[:200]
    line = payload.get("line", "")
    path = str(payload.get("path", request.META.get("HTTP_REFERER", "")))[:300]
    if not message:
        return HttpResponse(status=204)

    from management_portal.models import SystemLog

    SystemLog.objects.create(
        level="warning",
        category="frontend",
        message_fa=f"خطای جاوااسکریپت در مرورگر کاربر: {message}",
        detail=f"source={source} line={line}",
        path=path,
        user=request.user if request.user.is_authenticated else None,
    )
    return HttpResponse(status=204)
