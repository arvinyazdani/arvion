"""Alt text for the reviewed v2 editorial assets; no model/schema change."""
from pathlib import PurePosixPath
from django.templatetags.static import static

INTERNATIONAL_COVERS = {
    "custom-software-cost-us-2026-crm-accounting-b2b": ("software", (
        "گره‌های CRM، سند فاکتور و فروشگاه‌های B2B متصل؛ برنامه‌ریزی بودجه نرم‌افزار سفارشی.",
        "Connected CRM records, invoice and B2B storefronts illustrating custom software budgeting.")),
    "hire-django-freelancer-us-rates-2026": ("freelancer", (
        "ویرایشگر کد و ساعت برای نمایش ارتباط تخصص جنگو، زمان توسعه و هزینه پروژه.",
        "A code editor and clock illustrating Django expertise, development time and project cost.")),
    "personal-accounting-economic-progress-raya": ("raya", (
        "دفتر هزینه، کیف پول و نمودار ماهانه برای ثبت هزینه و مدیریت مالی شخصی با رایا.", "")),
}


def cover_url(post, language):
    item = INTERNATIONAL_COVERS.get(post.slug_fa)
    name = PurePosixPath(str(post.hero_image or "")).name
    # A manually chosen owner image always wins; no model/schema addition.
    if item and (not name or name.startswith(item[0] + "-fa-v1")):
        if language == "en" and item[0] == "raya":
            return ""
        return static(f"blog/covers/{item[0]}-{language}-v1.jpg")
    return post.hero_image.url if post.hero_image else ""

COVER_ALTS = {
    "corporate-website-cost-1405": (
        "سه طرح صفحه با جزئیات افزایشی، متصل به یک خط نارنجی برای نمایش ارتباط دامنه کار و هزینه.",
        "Three increasingly detailed page wireframes connected by an orange scope line.",
    ),
    "custom-website-vs-template": (
        "کاشی‌های یکسان در یک شبکه منظم و در یک قاب نامنظم، با درز نارنجی میان دو شیوه طراحی.",
        "Matching tiles in a rigid grid and an irregular outline, divided by an orange seam.",
    ),
    "custom-or-ready-made-crm": (
        "یک جعبه بسته کنار گره‌های ماژولار به‌هم‌پیوسته با مسیر نارنجی گردش کار.",
        "A closed box beside connected modular nodes with an orange workflow line.",
    ),
    "english-teacher-assessment": (
        "دفتر باز، خطوط خالی فهرست، قاب گفت‌وگو و مداد برای نمایش ارزیابی مهارت زبان.",
        "An open notebook, blank checklist lines, speech bubble and pencil for language assessment.",
    ),
    "clinic-website-design-online-booking": (
        "شبکه تقویم با یک زمان نارنجی مشخص‌شده کنار قاب تلفن برای نمایش نوبت‌دهی آنلاین.",
        "A calendar with one orange highlighted slot beside a phone outline for online booking.",
    ),
    "academy-website-structure-webinar": (
        "کارت‌های دوره، کمان پیشرفت و قاب نمایشگر با نشان هندسی بی‌چهره برای آموزش آنلاین.",
        "Course cards, a progress arc and a screen with a faceless geometric presenter placeholder.",
    ),
    "enterprise-crm-development-cost-stages": (
        "چهار پله با ساختار افزایشی در امتداد یک خط نارنجی برای نمایش مراحل توسعه سامانه.",
        "Four increasingly built-up steps along an orange line representing development stages.",
    ),
    "django-interview-questions-with-short-answers": (
        "قاب انتزاعی ویرایشگر با بلوک‌های خطی به شکل پرسش برای نمایش مصاحبه فنی.",
        "An abstract editor window with line blocks arranged into a question shape for a technical interview.",
    ),
}


def cover_alt(post, language):
    item = INTERNATIONAL_COVERS.get(post.slug_fa)
    if item and cover_url(post, language) == static(f"blog/covers/{item[0]}-{language}-v1.jpg"):
        return item[1][0 if language == "fa" else 1]
    filename = PurePosixPath(str(post.hero_image or "")).name
    slug = filename.removesuffix("-v2.jpg")
    if filename.endswith("-v2.jpg") and slug in COVER_ALTS:
        return COVER_ALTS[slug][0 if language == "fa" else 1]
    title = getattr(post, "title_" + language) or ""
    return ("تصویر توضیحی برای " if language == "fa" else "Illustration for ") + title
