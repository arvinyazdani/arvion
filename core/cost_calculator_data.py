"""Editable, directional US-market planning ranges for the public calculator.

Values are USD and are not quotes. Vendor-published ranges are used as
anchors; modifiers explicitly marked as assumptions are a transparent model,
not measured Rvion project pricing.
"""

DATA_VERSION = "2026-10-14"

PRODUCTS = {
    "website": {"label": ("وب‌سایت بازاریابی سفارشی", "Custom marketing website"), "range": (10000, 25000, 50000), "weeks": (4, 8, 16), "source": "apptage_custom_marketing_website"},
    "ecommerce": {"label": ("فروشگاه اینترنتی", "E-commerce store"), "range": (10000, 30000, 100000), "weeks": (6, 12, 24), "source": "kelp_ecommerce_2026"},
    "crm": {"label": ("CRM اختصاصی", "Custom CRM"), "range": (24000, 112000, 360000), "weeks": (8, 16, 48), "source": "article11_crm"},
    "accounting": {"label": ("اپ حسابداری و فاکتور", "Accounting & invoicing app"), "range": (25000, 60000, 300000), "weeks": (8, 20, 48), "source": "article11_accounting_directional"},
    "b2b": {"label": ("پلتفرم B2B", "B2B platform"), "range": (15000, 50000, 150000), "weeks": (8, 18, 40), "source": "article11_b2b"},
    "marketplace": {"label": ("مارکت‌پلیس", "Marketplace"), "range": (50000, 150000, 250000), "weeks": (16, 32, 60), "source": "article11_marketplace"},
    "mvp": {"label": ("MVP وب‌اپ عمومی", "General web-app MVP"), "range": (20000, 50000, 150000), "weeks": (6, 14, 32), "source": "apptage_web_app_mvp"},
}

TEAM_FACTORS = {
    "freelancer": {"label": ("فریلنسر ارشد", "Senior freelancer"), "factor": 0.5},
    "company": {"label": ("شرکت توسعه", "Development company"), "factor": 1.0},
}

INTEGRATION = (2000, 6000, 10000)  # per integration; article 11 vendor range
ERP = (10000, 20000, 30000)  # per ERP integration; article 11 vendor range
MOBILE_APP = (30000, 55000, 80000)  # companion app; article 11 vendor range
LEGAL_UPLIFT = (1.2, 1.3, 1.4)  # scenario assumption informed by article 11's 20–40%
ANNUAL_MAINTENANCE = (0.10, 0.15, 0.20)  # article 11's vendor-published range
ROLE_FACTOR_PER_EXTRA = 0.05  # explicit planning assumption, not a market statistic

SOURCES = {
    "apptage_custom_marketing_website": {"label": "Apptage (vendor guide, 2026)", "url": "https://www.apptage.com/blogs/custom-web-development-cost/"},
    "apptage_web_app_mvp": {"label": "Apptage (vendor guide, 2026)", "url": "https://www.apptage.com/blogs/custom-web-development-cost/"},
    "kelp_ecommerce_2026": {"label": "Kelp (agency guide aggregating vendor/Clutch ranges, 2026)", "url": "https://www.kelp.agency/blog/how-much-does-an-ecommerce-website-cost/"},
    "article11_crm": {"label": "Rvion article 11; underlying sources are vendor-published", "url": "https://rvionai.com/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/"},
    "article11_accounting_directional": {"label": "Rvion article 11; directional only, not a verified US benchmark", "url": "https://rvionai.com/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/"},
    "article11_b2b": {"label": "Rvion article 11; underlying sources are vendor-published", "url": "https://rvionai.com/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/"},
    "article11_marketplace": {"label": "Rvion article 11; underlying sources are vendor-published", "url": "https://rvionai.com/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/"},
    "article12_team_ratio": {"label": "Rvion article 12; modeled hourly-rate ranges, not project-cost evidence", "url": "https://rvionai.com/en/blog/hire-django-freelancer-us-rates-2026/"},
}

SOURCE_LIST = (
    SOURCES["apptage_custom_marketing_website"],
    SOURCES["kelp_ecommerce_2026"],
    {"label": "Rvion article 11 — custom software cost ranges (vendor sources; accounting figures directional)",
     "label_fa": "مقالهٔ ۱۱ آرویون — بازه‌های هزینهٔ نرم‌افزار (منابع فروشنده؛ ارقام حسابداری صرفاً جهت‌نما)",
     "url": "https://rvionai.com/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/"},
    {"label": "Rvion article 12 — hiring rates used only for the team scenario ratio", "label_fa": "مقالهٔ ۱۲ آرویون — نرخ استخدام، فقط برای نسبت سناریوی تیم",
     "url": "https://rvionai.com/en/blog/hire-django-freelancer-us-rates-2026/"},
)
