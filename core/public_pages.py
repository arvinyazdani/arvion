"""Explicit data-free reading routes; forms and account workflows stay private."""
from django.urls import Resolver404, resolve


PUBLIC_CONTENT_ROUTES = frozenset({
    "home", "about", "company_info", "crm_product", "privacy", "service_terms",
    "refund_policy", "services:list", "services:detail", "projects:demo_gallery",
    "projects:kimia_medical_crm",
    "blog:list", "blog:detail", "assessments:list", "assessments:briefing",
    "cost_calculator", "sitemap", "robots", "indexnow_key",
    "offline", "offline_fa", "offline_en",
})


def is_public_content_request(request):
    if request.method not in {"GET", "HEAD"}:
        return False
    match = getattr(request, "resolver_match", None)
    if match is None:
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return False
    return match.view_name in PUBLIC_CONTENT_ROUTES
