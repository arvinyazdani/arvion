# core/views/i18n.py
# سوییچ زبان ساده با نگهداشتن مسیر قبلی
from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme

def switch_language(request):
    """
    تغییر زبان جاری سشن و برگشت به صفحه قبل.
    """
    lang = request.GET.get("lang")
    candidate = request.META.get("HTTP_REFERER") or "/"
    next_url = candidate if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ) else "/"
    if lang in ("fa", "en"):
        translation.activate(lang)
    response = redirect(next_url)
    if lang in ("fa", "en"):
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    return response
