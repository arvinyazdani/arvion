import logging

from django.urls import Resolver404, resolve

EXCEPTION_FA = {
    "OperationalError": "خطای اتصال یا ساختار پایگاه داده",
    "IntegrityError": "نقض محدودیت یکپارچگی داده در پایگاه داده",
    "DoesNotExist": "رکورد موردنظر در پایگاه داده پیدا نشد",
    "PermissionDenied": "دسترسی غیرمجاز به یک بخش سیستم",
    "ValidationError": "داده ارسالی معتبر نبود",
    "Http404": "صفحه یا منبع درخواستی پیدا نشد",
    "ConnectionError": "خطای اتصال به یک سرویس بیرونی",
    "Timeout": "زمان پاسخ‌گویی یک سرویس به پایان رسید",
    "KeyError": "یک مقدار موردنیاز در داده‌های ارسالی وجود نداشت",
    "TypeError": "نوع داده نامعتبر در پردازش سرور",
    "AttributeError": "خطای داخلی در پردازش سرور",
}


def describe_exception_fa(exc_type_name):
    return EXCEPTION_FA.get(exc_type_name, f"خطای پیش‌بینی‌نشده در سرور ({exc_type_name})")


def safe_request_route(request):
    """Store the resolved route pattern, never identifiers embedded in a URL."""
    if request is None:
        return ""
    try:
        match = getattr(request, "resolver_match", None) or resolve(request.path)
    except (Resolver404, TypeError, ValueError):
        return ""
    return ("/" + str(match.route).lstrip("/"))[:300]


class PersianSystemLogHandler(logging.Handler):
    """خطاهای سطح سرور جنگو را با شرح فارسی در جدول SystemLog ذخیره می‌کند."""

    def emit(self, record):
        try:
            from .models import SystemLog

            exc_type_name = ""
            detail = record.getMessage()
            if record.exc_info and record.exc_info[0]:
                exc_type_name = record.exc_info[0].__name__
                import traceback
                detail = "".join(traceback.format_exception(*record.exc_info))

            request = getattr(record, "request", None)
            path = safe_request_route(request)
            if request is not None:
                # django.request messages commonly embed the concrete URL.
                # Replace it with the resolver pattern before persisting logs,
                # otherwise contract tokens and customer identifiers survive
                # even though the dedicated path column is sanitized.
                concrete_paths = {
                    getattr(request, "path", ""),
                    request.get_full_path() if hasattr(request, "get_full_path") else "",
                }
                for concrete in sorted(filter(None, concrete_paths), key=len, reverse=True):
                    detail = detail.replace(concrete, path or "[private-route]")
            user = None
            if request is not None and getattr(request, "user", None) is not None and request.user.is_authenticated:
                user = request.user

            SystemLog.objects.create(
                level="error" if record.levelno >= logging.ERROR else "warning",
                category="server",
                message_fa=describe_exception_fa(exc_type_name) if exc_type_name else detail[:300],
                detail=detail[:8000],
                path=path[:300],
                user=user,
            )
        except Exception:
            pass
