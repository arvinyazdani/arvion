from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.utils import translation
from urllib.parse import quote

from .models import CompanyProfile


def seo_context(request):
    """Return stable canonical and alternate URLs without query strings."""
    language = translation.get_language() or getattr(request, "LANGUAGE_CODE", "fa")
    language = language if language in {"fa", "en"} else "fa"
    segments = request.path.split("/")
    if len(segments) > 1 and segments[1] in {"fa", "en"}:
        segments[1] = language
        localized_path = "/".join(segments)
    else:
        localized_path = f"/{language}{request.path}"
    alternate_paths = {}
    for code in ("fa", "en"):
        localized_segments = localized_path.split("/")
        localized_segments[1] = code
        alternate_paths[code] = "/".join(localized_segments)
    match = request.resolver_match
    private_assessment_views = {
        "checkout", "sandbox_pay", "start_attempt", "attempt", "save_answer",
        "attempt_review", "finish_attempt", "result", "certificate", "audio_play",
        "integrity_event", "support_create", "support_history",
    }
    seo_noindex = bool(
        match and (
            match.namespace == "accounts"
            or (match.namespace == "leads" and match.url_name == "thanks")
            or (match.namespace == "assessments" and match.url_name in private_assessment_views)
        )
    )
    show_whatsapp_share = not seo_noindex and not (match and match.url_name == "crm_product")
    canonical_url = f"{settings.SITE_URL}{alternate_paths[language]}"
    share_text = (
        "آرویون؛ طراحی CRM سازمانی، وب‌سایت و سامانه‌های هوشمند"
        if language == "fa" else
        "Rvion — Enterprise CRM, websites and intelligent platforms"
    )
    whatsapp_share_url = "https://wa.me/?text=" + quote(share_text + "\n" + canonical_url)
    return {
        "canonical_url": canonical_url,
        "alternate_urls": {code: f"{settings.SITE_URL}{path}" for code, path in alternate_paths.items()},
        "language_switch_url": alternate_paths["en" if language == "fa" else "fa"],
        "site_url": settings.SITE_URL,
        "seo_noindex": seo_noindex,
        "whatsapp_share_url": whatsapp_share_url,
        "show_whatsapp_share": show_whatsapp_share,
    }


def assessment_flags(request):
    try:
        company = CompanyProfile.objects.first()
    except (OperationalError, ProgrammingError):
        company = None
    return {
        "assessment_free_checkout": settings.ASSESSMENT_FREE_CHECKOUT,
        "company": company,
    }
