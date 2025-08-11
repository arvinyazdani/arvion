# core/views/i18n.py
# سوییچ زبان ساده با نگهداشتن مسیر قبلی
from django.shortcuts import redirect
from django.utils import translation

def switch_language(request):
    """
    تغییر زبان جاری سشن و برگشت به صفحه قبل.
    """
    lang = request.GET.get("lang")
    next_url = request.META.get("HTTP_REFERER") or "/"
    if lang in ("fa", "en"):
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect(next_url)