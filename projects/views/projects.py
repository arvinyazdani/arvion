


import secrets

from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, RedirectView
from projects.models import DemoSelection, DemoTemplate
from projects.models.projects import Project
from core.views.lang import LanguageViewMixin


THEMES = ("warm", "midnight", "sage", "plum", "custom")
PERSONALITIES = ("minimal", "editorial", "luxury", "bold")
FEATURES = ("payment", "booking", "catalog", "blog", "membership", "multilingual")
REQUEST_TYPES = {
    "ecommerce": "ecommerce", "restaurant": "website", "portfolio": "website",
    "corporate": "website", "clinic": "webapp", "education": "webapp",
}
CATEGORY_LABELS_EN = {
    "ecommerce": "E-commerce", "restaurant": "Restaurant & cafe",
    "portfolio": "Portfolio", "corporate": "Corporate website",
    "clinic": "Clinic", "education": "Education & webinar",
}

CATEGORY_DETAILS = {
    "ecommerce": {
        "fa": {
            "fit": "برای فروش مستقیم محصول با مسیر خرید کوتاه و واضح",
            "pages": ("صفحه اصلی فروش", "فهرست و فیلتر", "جزئیات محصول", "سبد و پرداخت"),
            "detail": "روی تصویر محصول، اعتماد پیش از خرید و رساندن مشتری به پرداخت با کمترین اصطکاک تمرکز دارد.",
        },
        "en": {
            "fit": "For direct product sales with a short, clear purchase path",
            "pages": ("Storefront", "Catalogue and filters", "Product detail", "Basket and checkout"),
            "detail": "Focuses on product imagery, pre-purchase confidence and a low-friction path to checkout.",
        },
    },
    "restaurant": {
        "fa": {
            "fit": "برای رستوران و کافه‌ای که منو، رویداد و رزرو را یکجا می‌خواهد",
            "pages": ("معرفی و پیشنهاد روز", "منوی دسته‌بندی‌شده", "رزرو میز", "رویداد و تماس"),
            "detail": "فضای برند را با منوی خوانا، رزرو سریع و اطلاعات ضروری مراجعه حضوری ترکیب می‌کند.",
        },
        "en": {
            "fit": "For restaurants and cafés combining menus, events and reservations",
            "pages": ("Welcome and daily pick", "Structured menu", "Table booking", "Events and contact"),
            "detail": "Combines brand atmosphere with a readable menu, quick booking and essential visit information.",
        },
    },
    "portfolio": {
        "fa": {
            "fit": "برای متخصص یا استودیویی که باید کیفیت کار را سریع اثبات کند",
            "pages": ("معرفی کوتاه", "نمونه‌های منتخب", "شرح فرایند", "درباره و تماس"),
            "detail": "نمونه‌ها را به روایت مسئله، تصمیم و نتیجه تبدیل می‌کند تا مخاطب فقط یک گالری خام نبیند.",
        },
        "en": {
            "fit": "For experts or studios that need to prove the quality of their work quickly",
            "pages": ("Concise introduction", "Selected work", "Process", "About and contact"),
            "detail": "Turns work into a problem-decision-outcome story instead of an unexplained image gallery.",
        },
    },
    "corporate": {
        "fa": {
            "fit": "برای شرکت خدماتی که اعتماد، خدمات و تماس روشن اولویت دارد",
            "pages": ("ارزش پیشنهادی", "خدمات", "فرایند همکاری", "اعتبار و تماس"),
            "detail": "به بازدیدکننده کمک می‌کند در چند دقیقه حوزه کار، روش همکاری و مسیر اقدام بعدی را بفهمد.",
        },
        "en": {
            "fit": "For service companies prioritising trust, offers and a clear contact path",
            "pages": ("Value proposition", "Services", "Engagement process", "Proof and contact"),
            "detail": "Helps a visitor understand the offer, working model and next action within minutes.",
        },
    },
    "clinic": {
        "fa": {
            "fit": "برای کلینیک با معرفی پزشک، محتوای آگاه‌کننده و نوبت‌دهی",
            "pages": ("معرفی کلینیک", "پزشکان و خدمات", "انتخاب زمان", "راهنما و پیگیری"),
            "detail": "اطلاعات درمانی را آرام و خوانا ارائه می‌کند و رزرو را بدون جمع‌آوری زودهنگام داده حساس پیش می‌برد.",
        },
        "en": {
            "fit": "For clinics combining practitioner profiles, guidance and appointment booking",
            "pages": ("Clinic overview", "Practitioners and services", "Time selection", "Guidance and follow-up"),
            "detail": "Presents care information calmly and supports booking without premature collection of sensitive data.",
        },
    },
    "education": {
        "fa": {
            "fit": "برای آکادمی، دوره آنلاین یا مجموعه برگزارکننده وبینار",
            "pages": ("مسیرهای یادگیری", "دوره و مدرس", "جلسه و وبینار", "عضویت و پرداخت"),
            "detail": "انتخاب مسیر، اعتماد به مدرس و ادامه یادگیری را در یک تجربه منسجم کنار هم می‌گذارد.",
        },
        "en": {
            "fit": "For academies, online courses and webinar-led education",
            "pages": ("Learning paths", "Course and tutor", "Sessions and webinars", "Membership and payment"),
            "detail": "Combines path selection, tutor confidence and continued learning in one coherent experience.",
        },
    },
}


def _decorate_demo(demo, lang):
    content = CATEGORY_DETAILS[demo.category][lang]
    feature_names = dict(_labels(lang)["features"])
    demo.fit_label = content["fit"]
    demo.page_labels = content["pages"]
    demo.detail_text = content["detail"]
    demo.feature_labels = [feature_names[key] for key in demo.default_features if key in feature_names]
    demo.category_label = demo.get_category_display() if lang == "fa" else CATEGORY_LABELS_EN[demo.category]
    return demo


def _selection_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _labels(lang):
    fa = lang == "fa"
    return {
        "themes": [("warm", "گرم و نارنجی"), ("midnight", "تیره و حرفه‌ای"), ("sage", "سبز آرام"), ("plum", "ارغوانی خلاق"), ("custom", "رنگ دلخواه")]
        if fa else [("warm", "Warm orange"), ("midnight", "Professional dark"), ("sage", "Calm sage"), ("plum", "Creative plum"), ("custom", "Custom colour")],
        "personalities": [("minimal", "مینیمال"), ("editorial", "محتوامحور"), ("luxury", "لوکس"), ("bold", "پر انرژی")]
        if fa else [("minimal", "Minimal"), ("editorial", "Editorial"), ("luxury", "Luxury"), ("bold", "Bold")],
        "features": [("payment", "پرداخت آنلاین"), ("booking", "رزرو / نوبت‌دهی"), ("catalog", "کاتالوگ و محصول"), ("blog", "مقاله و محتوا"), ("membership", "عضویت و پنل مشتری"), ("multilingual", "چندزبانه")]
        if fa else [("payment", "Online payments"), ("booking", "Booking"), ("catalog", "Catalogue"), ("blog", "Content"), ("membership", "Member area"), ("multilingual", "Multilingual")],
    }


class DemoGalleryView(LanguageViewMixin, ListView):
    template_name = "projects/demo_gallery.html"
    context_object_name = "demos"

    def get_queryset(self):
        return DemoTemplate.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demos = [_decorate_demo(demo, self.lang) for demo in context["demos"]]
        categories = []
        for key, label_fa in DemoTemplate.CATEGORY_CHOICES:
            items = [item for item in demos if item.category == key]
            if items:
                categories.append({
                    "key": key, "title": label_fa if self.lang == "fa" else CATEGORY_LABELS_EN[key],
                    "items": items,
                })
        context.update(categories=categories, lang=self.lang)
        return context


class DemoPreviewView(LanguageViewMixin, DetailView):
    template_name = "projects/demo_preview.html"
    context_object_name = "demo"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return DemoTemplate.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            demo=_decorate_demo(context["demo"], self.lang), lang=self.lang, labels=_labels(self.lang),
            # Minted server-side on every render so the one-shot idempotency
            # check in DemoConfigureView never depends on client JavaScript.
            submission_token=secrets.token_urlsafe(24),
        )
        return context


class DemoFullView(DemoPreviewView):
    template_name = "projects/demo_full.html"


class DemoConfigureView(LanguageViewMixin, View):
    def post(self, request, slug):
        demo = DemoTemplate.objects.filter(slug=slug, is_active=True).first()
        if demo is None:
            raise Http404
        invalid_url = reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1"
        submission_token = request.POST.get("submission_token", "").strip()[:64]
        theme = request.POST.get("theme", "")
        personality = request.POST.get("personality", "")
        features = [item for item in request.POST.getlist("features") if item in FEATURES]
        brand_preview = request.POST.get("brand_preview", "").strip()[:48]
        custom_color = request.POST.get("custom_color", "").strip().lower()
        # The token is minted server-side by DemoPreviewView on every GET, so a
        # missing one means the form was not rendered by that view — reject it
        # the same way as any other malformed submission.
        if not submission_token:
            return redirect(invalid_url)
        if theme not in THEMES or personality not in PERSONALITIES or len(features) > 6:
            return redirect(invalid_url)
        if theme == "custom" and (len(custom_color) != 7 or not custom_color.startswith("#") or any(character not in "0123456789abcdef" for character in custom_color[1:])):
            return redirect(invalid_url)

        session_key = _selection_session_key(request)
        selections_payload = {
            "theme": theme,
            "personality": personality,
            "features": features,
            "custom_color": custom_color if theme == "custom" else "",
            "brand": brand_preview or (demo.fictional_brand_fa if self.lang == "fa" else demo.fictional_brand_en),
        }

        def matches_this_submission(row):
            return row.session_key == session_key and row.template_id == demo.pk and row.selections == selections_payload

        # `submission_token` is globally unique, so a resubmission of the exact
        # same token — same tab double-clicking submit, a retried request, a
        # browser "confirm resubmission" — reuses the row it already created
        # instead of making a duplicate. A token replayed from a different
        # session, for a different demo, or with edited field values is
        # rejected outright: it must not create a second row and must not
        # expose or attach the row that owns the token.
        existing = DemoSelection.objects.filter(submission_token=submission_token).first()
        if existing is not None:
            if matches_this_submission(existing):
                selection = existing
            else:
                return redirect(invalid_url)
        else:
            try:
                selection = DemoSelection.objects.create(
                    template=demo, session_key=session_key,
                    submission_token=submission_token, selections=selections_payload,
                )
            except IntegrityError:
                # Two near-simultaneous requests raced past the check above;
                # the loser lands here once the winner's row is committed.
                existing = DemoSelection.objects.filter(submission_token=submission_token).first()
                if existing is not None and matches_this_submission(existing):
                    selection = existing
                else:
                    return redirect(invalid_url)
        request.session["demo_selection_token"] = str(selection.public_token)
        request.session.modified = True
        request_type = REQUEST_TYPES[demo.category]
        return redirect(f"{reverse('leads:contact')}?demo={selection.public_token}&request_type={request_type}")

class ProjectListView(LanguageViewMixin, RedirectView):
    """Temporarily sideline the public project index without deleting its data."""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse("projects:demo_gallery")

class ProjectDetailView(LanguageViewMixin, DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Project.objects.filter(is_active=True)
