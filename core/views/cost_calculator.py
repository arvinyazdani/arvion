from django.views.generic import TemplateView

from .lang import LanguageViewMixin
from core.cost_calculator_data import (
    ANNUAL_MAINTENANCE, ERP, INTEGRATION, LEGAL_UPLIFT, MOBILE_APP,
    PRODUCTS, ROLE_FACTOR_PER_EXTRA, SOURCE_LIST, TEAM_FACTORS,
)


class CostCalculatorView(LanguageViewMixin, TemplateView):
    template_name = "core/cost_calculator.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            calculator_products=[{"key": key, **value} for key, value in PRODUCTS.items()],
            calculator_teams=[{"key": key, **value} for key, value in TEAM_FACTORS.items()],
            calculator_source_list=SOURCE_LIST,
            calculator_data={
                "products": {key: {"range": list(value["range"]), "weeks": list(value["weeks"])} for key, value in PRODUCTS.items()},
                "teams": {key: value["factor"] for key, value in TEAM_FACTORS.items()},
                "integration": list(INTEGRATION), "erp": list(ERP), "mobile": list(MOBILE_APP),
                "legal": list(LEGAL_UPLIFT), "maintenance": list(ANNUAL_MAINTENANCE),
                "roleFactor": ROLE_FACTOR_PER_EXTRA,
            },
            calculator_inputs={
                "product": self.request.GET.get("product", "crm"),
                "roles": self.request.GET.get("roles", "3"),
                "integrations": self.request.GET.get("integrations", "0"),
                "erp": self.request.GET.get("erp", "0"),
                "mobile": self.request.GET.get("mobile", "0"),
                "legal": self.request.GET.get("legal", "0"),
                "team": self.request.GET.get("team", "company"),
                "maintenance": self.request.GET.get("maintenance", "15"),
            },
        )
        return context
