"""Editorial search copy; no business identity, prices or catalogue data writes."""

# Each pair is Persian/English. The page's visible heading remains independent.
TITLES = {
    "home": (None, "Custom Django web apps & CRM development | Rvion"),
    "blog:list": ("مقاله‌های طراحی سایت، CRM و ارزیابی مهارت | آرویون", "Articles on web development, CRM & assessment | Rvion"),
    "assessments:list": ("آزمون ارزیابی مدرس زبان و پایتون و جنگو | آرویون", "English teacher & Python Django assessments | Rvion"),
    "cost_calculator": ("محاسبه‌گر هزینه طراحی سایت و وب‌اپلیکیشن | آرویون", "Web App Development Cost Calculator | Rvion"),
}

DESCRIPTIONS = {
    "home": (None, "Custom Django web apps, CRM and B2B platforms for your business. Explore the project process, shape your requirements and request a consultation."),
    "about": ("با شرکت آرویون، تخصص توسعه وب‌اپلیکیشن با پایتون و جنگو و روش شروع همکاری آشنا شوید؛ خدمات و اطلاعات رسمی شرکت را بررسی کنید.", "Meet Rvion and explore its Python and Django web application expertise, project services and registered company information before you enquire."),
    "company_info": ("اطلاعات رسمی شرکت آرویون، نام حقوقی، شماره ثبت، شناسه ملی و راه‌های تماس را بررسی کنید؛ پیش از سفارش پروژه، هویت طرف همکاری را بشناسید.", None),
    "crm_product": ("امکانات CRM اختصاصی آرویون برای مدیریت مشتری، فروش و عملیات را بررسی کنید؛ قابلیت‌های آماده را از توسعه پیشنهادی جدا ببینید و نیازسنجی را شروع کنید.", None),
    "services:list": ("خدمات طراحی سایت، ساخت وب‌اپلیکیشن با جنگو، مشاوره و پشتیبانی آرویون را مقایسه کنید؛ دامنه هر خدمت را ببینید و درخواست پروژه را آغاز کنید.", "Explore Rvion's website design, custom Django web apps, product consulting and maintenance services. Compare scopes and start your project enquiry."),
    "projects:demo_gallery": (None, "Explore fictional website demos for stores, clinics, restaurants and other businesses. Choose a layout, customise its details and start a project brief."),
    "assessments:list": ("آزمون ارزیابی مدرس زبان انگلیسی و آزمون تخصصی پایتون و جنگو را بررسی کنید؛ با مهارت‌های سنجیده‌شده، پایش رفتار و گزارش نتیجه آشنا شوید.", "Explore English teacher assessment and Python Django skills tests. Read about question coverage, integrity monitoring and answer review before starting."),
    "leads:contact": ("برای طراحی سایت، ساخت وب‌اپلیکیشن یا CRM اختصاصی درخواست مشاوره ثبت کنید؛ نیاز، هدف و راه تماس را بنویسید تا دامنه پروژه بررسی شود.", "Tell Rvion about your website, custom Django web app or CRM project. Share your goals and contact details to request an initial scope discussion."),
    "cost_calculator": ("هزینه ساخت وب‌اپلیکیشن، CRM یا فروشگاه را با ورودی‌های پروژه برآورد کنید؛ بازه، زمان و نگهداری سالانه را ببینید و برای بررسی دقیق‌تر درخواست دهید.", "Estimate a custom web app, CRM or ecommerce project using scope inputs. Explore cost, timing and annual maintenance ranges, then request a scoped discussion."),
    "service_terms": ("شرایط خدمات آرویون را پیش از سفارش سایت یا شرکت در آزمون بخوانید؛ درباره دامنه همکاری، پرداخت، تحویل و مسئولیت‌های دو طرف آگاه شوید.", None),
    "refund_policy": ("سیاست لغو سفارش و بازپرداخت آرویون را بررسی کنید؛ تفاوت خدمات پروژه‌ای و آزمون، شرایط رسیدگی و مسیر ثبت درخواست پشتیبانی را بخوانید.", None),
}

SERVICE_TITLES = {
    "digital-product-consulting": ("مشاوره طراحی محصول و ساخت MVP | آرویون", "Digital product consulting & MVP planning | Rvion"),
    "corporate-website-design": ("طراحی سایت شرکتی متناسب با کسب‌وکار | آرویون", "Custom corporate website design services | Rvion"),
    "custom-web-application": ("سفارش ساخت وب‌اپلیکیشن با پایتون و جنگو | آرویون", "Custom Django web application development | Rvion"),
    "ecommerce-platform": ("طراحی سایت فروشگاهی و مسیر سفارش آنلاین | آرویون", "Custom ecommerce website development | Rvion"),
    "maintenance-and-growth": ("پشتیبانی و بهینه‌سازی سایت و وب‌اپلیکیشن | آرویون", "Website maintenance & web app optimisation | Rvion"),
}

SERVICE_DESCRIPTIONS = {
    "digital-product-consulting": ("با مشاوره محصول دیجیتال، مسئله، کاربران و اولویت‌های MVP را روشن کنید؛ فرایند نیازسنجی و خروجی‌های پیشنهادی را ببینید و درخواست بررسی بدهید.", "Clarify your digital product, users and MVP priorities with Rvion. Explore the discovery process and proposed deliverables, then request a consultation."),
    "corporate-website-design": ("برای طراحی سایت شرکتی، مخاطب، خدمات و مسیر تماس را مشخص کنید؛ درباره محتوا، ساختار صفحه‌ها و تحویل پروژه بخوانید و سفارش خود را آغاز کنید.", "Plan a corporate website around your services, audience and enquiry journey. Explore content, page structure and delivery, then start your project brief."),
    "custom-web-application": ("ساخت وب‌اپلیکیشن با جنگو را از نیازسنجی تا توسعه مرحله‌ای بررسی کنید؛ درباره نقش‌ها، داده‌ها، API و خروجی پروژه بخوانید و درخواست ثبت کنید.", "Plan a custom Django web app around your workflows, roles and data. Explore discovery, API scope and phased delivery, then request a project discussion."),
    "ecommerce-platform": ("طراحی فروشگاه اینترنتی را بر پایه محصول، سبد خرید و فرایند سفارش شروع کنید؛ امکانات، محدودیت اتصال پرداخت و مراحل تحویل را پیش از سفارش بررسی کنید.", "Plan an ecommerce website around products, checkout and order management. Review payment integration requirements and delivery before starting your brief."),
    "maintenance-and-growth": ("برای پشتیبانی و بهینه‌سازی سایت، وضعیت فعلی، خطاها و اولویت‌های توسعه را مشخص کنید؛ مراحل بررسی فنی و دامنه همکاری را بخوانید و درخواست بدهید.", "Plan website maintenance around current issues, technical access and priorities. Explore the review process and support scope, then request a discussion."),
}
