# core/views/base.py
# ویوهای پایه (Home و About) — کلاسی، چندزبانه و قابل گسترش

# ==== ایمپورت‌ها ====
from django.views.generic import TemplateView
from blog.models import Post
from blog.languages import translated_posts
from projects.models import DemoTemplate
from projects.demo_labels import CATEGORY_LABELS_EN
from services.models import Service
from django.urls import reverse
from .lang import LanguageViewMixin  # میکسین مدیریت زبان

# ==== ویو خانه ====
class HomeView(LanguageViewMixin, TemplateView):
    """
    ویوی صفحه خانه:
      - ارث‌بری از LanguageViewMixin برای تشخیص زبان جاری
      - نمایش خلاصه‌ای از برند
      - نمایش آخرین پست‌ها و چند دموی قابل شخصی‌سازی
      - داده‌ها بر اساس زبان انتخابی از مدل‌ها خوانده می‌شوند
    """
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        # گرفتن context پایه از TemplateView + LanguageViewMixin
        ctx = super().get_context_data(**kwargs)

        # آخرین ۳ پست منتشر شده
        posts = list(translated_posts(Post.objects.published(), self.lang)[:3])
        # One active representative per business type; no dead demo links.
        featured_slugs = ("nava-market", "sarvin-atelier", "saffron-table", "linea-studio",
                          "parsa-advisory", "roshna-clinic", "ariana-academy")
        demo_by_slug = {
            demo.slug: demo
            for demo in DemoTemplate.objects.filter(is_active=True, slug__in=featured_slugs)
        }
        demos = [demo_by_slug[slug] for slug in featured_slugs if slug in demo_by_slug]
        for demo in demos:
            demo.category_label = (demo.get_category_display() if self.lang == "fa"
                                   else CATEGORY_LABELS_EN[demo.category])

        # افزودن به context
        ctx["latest_posts"] = posts
        ctx["featured_demos"] = demos[:3]
        ctx["home_demo_categories"] = [
            {"label": demo.category_label,
             "url": reverse("projects:demo_gallery") + "#demo-" + demo.slug}
            for demo in demos
        ]
        ctx["available_demo_count"] = DemoTemplate.objects.filter(is_active=True).count()

        # Copy remains owned by the live catalogue, not a second home catalogue.
        ranks = {slug: index for index, slug in enumerate((
            "corporate-website-design", "ecommerce-platform", "custom-web-application",
            "digital-product-consulting", "maintenance-and-growth",
        ))}
        services = list(Service.objects.filter(is_active=True))
        if all(service.slug in ranks for service in services):
            services.sort(key=lambda service: ranks[service.slug])
        icons = {"corporate-website-design": "globe", "ecommerce-platform": "payment",
                 "custom-web-application": "settings", "digital-product-consulting": "message",
                 "maintenance-and-growth": "services"}
        cards = [{"slug": service.slug, "title": getattr(service, f"title_{self.lang}"),
                  "summary": getattr(service, f"short_description_{self.lang}"),
                  "url": service.get_absolute_url(), "icon": icons.get(service.slug, "services")}
                 for service in services]
        cards.insert(min(3, len(cards)), {
            "slug": "crm", "title": "CRM سازمانی" if self.lang == "fa" else "Enterprise CRM",
            "summary": "مشتری، فروش و عملیات" if self.lang == "fa" else "Customers, sales & operations",
            "url": reverse("crm_product"), "icon": "customers",
        })
        ctx["home_services"] = cards

        return ctx


class ProjectStartView(LanguageViewMixin, TemplateView):
    """A single, low-friction entry point for every project discovery route."""

    template_name = "core/project_start.html"

    def get(self, request, *args, **kwargs):
        from core.order_gateway import gateway_get_destination
        from django.shortcuts import redirect
        destination = gateway_get_destination(request)
        if destination:
            return redirect(destination)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from core.order_gateway import submit_existing_demo
        return submit_existing_demo(request)

    def get_context_data(self, **kwargs):
        from core.order_gateway import gateway_context
        context = super().get_context_data(**kwargs)
        context.update(gateway_context(self.request, self.lang))
        return context


# ==== ویو درباره ====
class AboutView(LanguageViewMixin, TemplateView):
    template_name = "core/about.html"


class CompanyInfoView(LanguageViewMixin, TemplateView):
    template_name = "core/company_info.html"


class PrivacyView(LanguageViewMixin, TemplateView):
    template_name = "core/privacy.html"


class ServiceTermsView(LanguageViewMixin, TemplateView):
    template_name = "core/service_terms.html"


class RefundPolicyView(LanguageViewMixin, TemplateView):
    template_name = "core/refund_policy.html"


class CRMProductView(LanguageViewMixin, TemplateView):
    template_name = "core/crm_product.html"

    features = (
        ("مدیریت مشتریان", "Customer management", "پرونده سازمان، اطلاعات حقوقی و تماس، جست‌وجو، تشخیص رکورد مشابه و ورود CSV.", "Company profiles, legal and contact details, search, duplicate detection, and CSV imports."),
        ("فروش و پایپ‌لاین", "Sales and pipeline", "فرصت، مبلغ، احتمال موفقیت، مراحل قابل تنظیم، تاریخ پایان و تاریخچه تغییر.", "Opportunities, value, win probability, configurable stages, close dates, and change history."),
        ("گزارش ویزیتورها", "Field sales reports", "تخصیص مراکز، نتیجه مذاکره، پزشک، نیاز، رقیب، اقدام بعدی و بازخورد مدیر.", "Account assignment, visit outcomes, contacts, needs, competitors, next actions, and manager feedback."),
        ("مکاتبات سازمانی", "Business correspondence", "نامه وارده و صادره، محرمانگی، شماره‌گذاری، نسخه‌ها و پیشنهاد نگارش با تأیید انسانی.", "Incoming and outgoing letters, confidentiality, numbering, versions, and human-approved drafting assistance."),
        ("پشتیبانی و SLA", "Support and SLA", "تیکت، صف، اولویت، قرارداد، گارانتی و تاریخچه اقدامات تیم خدمات.", "Tickets, queues, priorities, contracts, warranties, and complete service activity history."),
        ("حسابداری داخلی", "Internal accounting", "سند، کنترل تراز، ثبت قطعی، فاکتور، دریافت و پرداخت، چک و تراز آزمایشی.", "Journal entries, balance controls, posting, invoices, receipts, payments, cheques, and trial balance."),
        ("انبار و تجهیزات", "Inventory and equipment", "موجودی، اسناد انبار، سری ساخت، انقضا، سریال دستگاه، نصب، آموزش و سرویس.", "Stock, warehouse documents, batches, expiry, device serials, installation, training, and service."),
        ("اتوماسیون", "Automation", "کارتابل تصمیم، اعلان، گردش کار، گزارش زمان‌بندی‌شده و ثبت نتیجه تأیید.", "Decision inboxes, notifications, workflows, scheduled reports, and approval records."),
        ("امنیت سازمانی", "Enterprise security", "نقش، مجوز، محدوده مالک/شعبه/سازمان، MFA، نشست‌ها و رویداد ممیزی.", "Roles, permissions, owner/branch/organisation scopes, MFA, sessions, and audit events."),
    )
    audiences = (
        ("واردکننده و توزیع‌کننده", "Importers and distributors", "فروش B2B، نمایندگی برند، انبار، قیمت‌گذاری و خدمات پس از فروش.", "B2B sales, brand representation, inventory, pricing, and after-sales service."),
        ("تجهیزات پزشکی و آزمایشگاهی", "Medical and laboratory equipment", "بیمارستان، ویزیتور، پزشک، سریال دستگاه، نصب، گارانتی و سرویس.", "Hospitals, field representatives, physicians, device serials, installation, warranty, and service."),
        ("شرکت خدماتی", "Service companies", "تیکت، SLA، قرارداد، مأموریت فنی و سوابق پاسخ‌گویی.", "Tickets, SLAs, contracts, technical assignments, and response history."),
        ("فروش سازمانی و پروژه‌ای", "Enterprise and project sales", "چرخه چندمرحله‌ای، پیش‌فاکتور، مناقصه و تصمیم‌گیرندگان متعدد.", "Multi-stage cycles, quotations, tenders, and multiple decision makers."),
        ("شرکت در حال تأسیس", "New companies", "شروع یکپارچه CRM، عملیات پایه و حسابداری داخلی روی یک بستر.", "A unified start for CRM, essential operations, and internal accounting."),
        ("سازمان با داده محرمانه", "Data-sensitive organisations", "استقرار مستقل، دیتابیس اختصاصی و کنترل دسترسی دقیق.", "Independent deployment, dedicated database, and precise access control."),
    )
    roadmap = (
        ("هوش مصنوعی", "Artificial intelligence", "خلاصه گزارش، تحلیل روند، پیشنهاد اقدام بعدی و طبقه‌بندی نامه.", "Report summaries, trend analysis, suggested next actions, and letter classification."),
        ("اتصال حسابداری", "Accounting integration", "همگام‌سازی طرف حساب، کالا، فاکتور، دریافت و مانده با نرم‌افزار مشتری.", "Synchronise accounts, products, invoices, receipts, and balances with client software."),
        ("کانال‌های ارتباطی", "Communication channels", "ایمیل، پیامک، واتساپ سازمانی و مرکز تماس.", "Email, SMS, enterprise WhatsApp, and call-centre integration."),
        ("گردش‌های اختصاصی", "Custom workflows", "مناقصه، تأیید تخفیف، خرید، مأموریت فنی، مرجوعی و کنترل کیفیت.", "Tenders, discount approval, purchasing, technical missions, returns, and quality control."),
        ("موبایل و آفلاین", "Mobile and offline", "PWA یا اپ ویزیتور و تکنسین با عکس، موقعیت و امضا.", "PWA or mobile apps for field teams with photos, location, and signatures."),
        ("پرتال مشتری", "Customer portal", "درخواست خدمت، قرارداد، فاکتور، سفارش و مستندات.", "Service requests, contracts, invoices, orders, and documents."),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(features=self.features, audiences=self.audiences, roadmap=self.roadmap)
        return context
