from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.urls import include, path
from django.views.generic import TemplateView

from core.health import HealthCheckView
from core.admin_dashboard import operations_dashboard
from core.sitemaps import sitemaps
from core.views import (
    AboutView, CompanyInfoView, CRMProductView, HomeView, PrivacyView,
    RefundPolicyView, ServiceTermsView,
)


def default_language(request):
    return HttpResponsePermanentRedirect("/fa/")


def robots_txt(request):
    content = "\n".join((
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /fa/account/",
        "Disallow: /en/account/",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ))
    return HttpResponse(content, content_type="text/plain")


def favicon(request):
    return HttpResponsePermanentRedirect("/static/core/favicon.svg")


def legacy_management(request, path=""):
    suffix = f"{path}/" if path else ""
    return HttpResponsePermanentRedirect(f"/fa/management/{suffix}")


urlpatterns = [
    path("", default_language, name="language_root"),
    path("health/", HealthCheckView.as_view(), name="health"),
    path("admin/operations/", operations_dashboard, name="admin_operations"),
    path("admin/", admin.site.urls),
    path("management/", legacy_management, name="legacy_management"),
    path("management/<path:path>", legacy_management),
    path("contract/", include(("contracts.urls", "contracts"), namespace="contracts")),
    path("robots.txt", robots_txt, name="robots"),
    path("favicon.ico", favicon, name="favicon"),
    path("service-worker.js", TemplateView.as_view(template_name="core/service-worker.js", content_type="application/javascript"), name="service_worker"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

urlpatterns += i18n_patterns(
    path("management/", include(("management_portal.urls", "management_portal"), namespace="management_portal")),
    path("account/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("assessments/", include(("assessments.urls", "assessments"), namespace="assessments")),
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("company/", CompanyInfoView.as_view(), name="company_info"),
    path("crm/", CRMProductView.as_view(), name="crm_product"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("service-terms/", ServiceTermsView.as_view(), name="service_terms"),
    path("refund-policy/", RefundPolicyView.as_view(), name="refund_policy"),
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("projects/", include(("projects.urls", "projects"), namespace="projects")),
    path("services/", include(("services.urls", "services"), namespace="services")),
    path("contact/", include(("leads.urls", "leads"), namespace="leads")),
    path("crm-order/", include(("crm_orders.urls", "crm_orders"), namespace="crm_orders")),
    path("clinic-order/", include(("clinic_orders.urls", "clinic_orders"), namespace="clinic_orders")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
