from django.db import migrations, models


SERVICES = (
    {
        "slug": "digital-product-consulting", "title_fa": "مشاوره محصول و پلتفرم آنلاین", "title_en": "Digital product and platform consulting",
        "short_description_fa": "تبدیل مسئله کسب‌وکار به نقشه اجرایی روشن، پیش از صرف هزینه توسعه.", "short_description_en": "Turn a business problem into a clear delivery plan before investing in development.",
        "description_fa": "برای ایده‌های تازه یا سامانه‌های موجود، نیازها، کاربران، ریسک‌ها و اولویت‌ها را بررسی می‌کنیم و مسیر MVP یا بازطراحی را مشخص می‌کنیم.", "description_en": "We assess needs, users, risks and priorities for new ideas or existing systems, then define an MVP or redesign path.",
        "deliverables_fa": "جلسه شناخت مسئله\nتحلیل نیازها و ریسک‌ها\nتعریف دامنه و اولویت MVP\nبرآورد اولیه زمان و هزینه", "deliverables_en": "Discovery session\nNeeds and risk analysis\nMVP scope and priorities\nInitial time and cost estimate",
        "process_fa": "ثبت درخواست رایگان\nجلسه شناخت\nتحلیل و جمع‌بندی\nپیشنهاد مسیر اجرا", "process_en": "Free enquiry\nDiscovery call\nAnalysis and summary\nRecommended delivery path", "duration_fa": "۱ تا ۵ روز کاری", "duration_en": "1–5 business days", "price": 0, "is_featured": True, "display_order": 1,
    },
    {
        "slug": "corporate-website-design", "title_fa": "طراحی و توسعه وب‌سایت شرکتی", "title_en": "Corporate website design and development",
        "short_description_fa": "وب‌سایت سریع، معتبر و دوزبانه برای معرفی شرکت، جذب مشتری و فروش خدمات.", "short_description_en": "A fast, credible bilingual website for company presence, lead generation and service sales.",
        "description_fa": "هویت دیجیتال شرکت را از معماری محتوا و تجربه کاربری تا توسعه، پنل مدیریت و استقرار نهایی طراحی و اجرا می‌کنیم.", "description_en": "We deliver the complete corporate presence from content architecture and UX to development, administration and deployment.",
        "deliverables_fa": "طراحی اختصاصی موبایل و دسکتاپ\nمدیریت محتوا و خدمات\nفرم سفارش و ارتباط\nسئو فنی پایه\nاستقرار و آموزش", "deliverables_en": "Custom mobile and desktop design\nContent and service management\nEnquiry workflow\nTechnical SEO foundation\nDeployment and training",
        "process_fa": "شناخت برند\nطراحی ساختار و رابط\nتوسعه و ورود محتوا\nتست و تحویل", "process_en": "Brand discovery\nInformation and UI design\nDevelopment and content\nQA and launch", "duration_fa": "۴ تا ۸ هفته", "duration_en": "4–8 weeks", "price": 0, "is_featured": True, "display_order": 2,
    },
    {
        "slug": "custom-web-application", "title_fa": "ساخت وب‌اپلیکیشن و MVP اختصاصی", "title_en": "Custom web application and MVP",
        "short_description_fa": "پلتفرم امن و قابل رشد با Python، Django و PostgreSQL برای فرآیند واقعی کسب‌وکار.", "short_description_en": "A secure, scalable Python, Django and PostgreSQL platform for real business workflows.",
        "description_fa": "پنل‌های عملیاتی، سامانه‌های اشتراکی، بازارگاه‌ها و نرم‌افزارهای تحت وب را با معماری قابل تست و استقرار حرفه‌ای می‌سازیم.", "description_en": "We build operational portals, SaaS products, marketplaces and web software with testable architecture and production deployment.",
        "deliverables_fa": "تحلیل و معماری\nUI/UX اختصاصی\nBackend و API امن\nپنل مدیریت\nتست، استقرار و مستندات", "deliverables_en": "Analysis and architecture\nCustom UI/UX\nSecure backend and API\nOperations dashboard\nTests, deployment and documentation",
        "process_fa": "کشف و دامنه‌بندی\nنمونه اولیه\nتوسعه مرحله‌ای\nتست پذیرش و انتشار", "process_en": "Discovery and scope\nPrototype\nIterative development\nAcceptance and launch", "duration_fa": "۸ تا ۱۶ هفته", "duration_en": "8–16 weeks", "price": 0, "is_featured": True, "display_order": 3,
    },
    {
        "slug": "ecommerce-platform", "title_fa": "فروشگاه و پلتفرم تجارت آنلاین", "title_en": "E-commerce platform",
        "short_description_fa": "فروش آنلاین کالا یا خدمات با مدیریت سفارش، پرداخت، مشتری و گزارش‌های عملیاتی.", "short_description_en": "Sell products or services with order, payment, customer and operational management.",
        "description_fa": "از فروشگاه تخصصی تا سامانه B2B، تجربه خرید و عملیات پشت‌صحنه را متناسب با مدل تجارت شما طراحی می‌کنیم.", "description_en": "From specialist stores to B2B systems, we design the buying journey and back-office operations around your business model.",
        "deliverables_fa": "کاتالوگ و جست‌وجو\nسبد و پرداخت\nمدیریت سفارش و مشتری\nگزارش فروش\nاتصال‌های موردنیاز", "deliverables_en": "Catalogue and search\nCart and payment\nOrder and customer management\nSales reports\nRequired integrations",
        "process_fa": "تحلیل مدل فروش\nطراحی تجربه خرید\nپیاده‌سازی عملیات\nتست تراکنش و انتشار", "process_en": "Commerce analysis\nBuying experience design\nOperations implementation\nTransaction QA and launch", "duration_fa": "۸ تا ۱۸ هفته", "duration_en": "8–18 weeks", "price": 0, "is_featured": False, "display_order": 4,
    },
    {
        "slug": "maintenance-and-growth", "title_fa": "پشتیبانی، بهینه‌سازی و توسعه", "title_en": "Maintenance, optimization and growth",
        "short_description_fa": "رفع اشکال، افزایش سرعت، امنیت، سئو و توسعه مرحله بعدی محصول موجود.", "short_description_en": "Bug fixing, performance, security, SEO and the next growth phase for an existing product.",
        "description_fa": "سامانه موجود را بررسی می‌کنیم، ریسک‌ها و بدهی فنی را اولویت می‌دهیم و با برنامه شفاف نگهداری یا توسعه می‌دهیم.", "description_en": "We audit an existing system, prioritize risks and technical debt, then maintain or extend it through a clear plan.",
        "deliverables_fa": "ممیزی فنی\nرفع اشکال و امنیت\nبهبود عملکرد\nبرنامه بروزرسانی\nگزارش دوره‌ای", "deliverables_en": "Technical audit\nBug and security fixes\nPerformance improvements\nUpdate plan\nPeriodic reporting",
        "process_fa": "دریافت دسترسی امن\nممیزی و اولویت‌بندی\nاجرای دوره‌ای\nگزارش و برنامه بعدی", "process_en": "Secure access\nAudit and priorities\nScheduled delivery\nReporting and next plan", "duration_fa": "قرارداد ماهانه یا پروژه‌ای", "duration_en": "Monthly or project engagement", "price": 0, "is_featured": False, "display_order": 5,
    },
)


def seed_services(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    existing = list(Service.objects.order_by("id"))
    for index, service in enumerate(existing):
        if not service.slug:
            Service.objects.filter(pk=service.pk).update(
                slug=f"legacy-service-{service.pk}",
                short_description_fa=service.description_fa[:240],
                short_description_en=service.description_en[:240],
            )
    for data in SERVICES:
        if not Service.objects.filter(slug=data["slug"]).update(**data):
            columns = (
                "title_fa", "title_en", "slug", "short_description_fa", "short_description_en",
                "description_fa", "description_en", "deliverables_fa", "deliverables_en",
                "process_fa", "process_en", "duration_fa", "duration_en", "price",
                "is_featured", "display_order", "is_active",
            )
            values = [data.get(column, True if column == "is_active" else "") for column in columns]
            quote = schema_editor.connection.ops.quote_name
            placeholders = ", ".join(["%s"] * len(columns))
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {quote(Service._meta.db_table)} "
                    f"({', '.join(quote(column) for column in columns)}) VALUES ({placeholders})",
                    values,
                )


class Migration(migrations.Migration):
    dependencies = [("services", "0003_alter_service_description_en_and_more")]
    operations = [
        migrations.AddField(model_name="service", name="slug", field=models.SlugField(blank=True, null=True, unique=True)),
        migrations.AddField(model_name="service", name="short_description_fa", field=models.CharField(default="", max_length=240)),
        migrations.AddField(model_name="service", name="short_description_en", field=models.CharField(default="", max_length=240)),
        migrations.AddField(model_name="service", name="deliverables_fa", field=models.TextField(blank=True, help_text="هر مورد در یک خط", verbose_name="خروجی‌ها فارسی")),
        migrations.AddField(model_name="service", name="deliverables_en", field=models.TextField(blank=True, help_text="One item per line", verbose_name="English deliverables")),
        migrations.AddField(model_name="service", name="process_fa", field=models.TextField(blank=True, help_text="هر مرحله در یک خط", verbose_name="فرآیند فارسی")),
        migrations.AddField(model_name="service", name="process_en", field=models.TextField(blank=True, help_text="One step per line", verbose_name="English process")),
        migrations.AddField(model_name="service", name="duration_fa", field=models.CharField(blank=True, max_length=100, verbose_name="زمان تقریبی فارسی")),
        migrations.AddField(model_name="service", name="duration_en", field=models.CharField(blank=True, max_length=100, verbose_name="English estimated duration")),
        migrations.AddField(model_name="service", name="is_featured", field=models.BooleanField(default=False, verbose_name="خدمت شاخص؟")),
        migrations.AddField(model_name="service", name="display_order", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AlterModelOptions(name="service", options={"ordering": ("display_order", "id")}),
        migrations.RunPython(seed_services, migrations.RunPython.noop),
        migrations.AlterField(model_name="service", name="slug", field=models.SlugField(unique=True)),
        migrations.AlterField(model_name="service", name="short_description_fa", field=models.CharField(max_length=240, verbose_name="خلاصه فارسی")),
        migrations.AlterField(model_name="service", name="short_description_en", field=models.CharField(max_length=240, verbose_name="English summary")),
    ]
