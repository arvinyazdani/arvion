


from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from projects.models import DemoSelection, DemoTemplate
from projects.models.projects import Project
from core.views.lang import LanguageViewMixin


THEMES = ("warm", "midnight", "sage", "plum")
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


def _selection_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _labels(lang):
    fa = lang == "fa"
    return {
        "themes": [("warm", "گرم و نارنجی"), ("midnight", "تیره و حرفه‌ای"), ("sage", "سبز آرام"), ("plum", "ارغوانی خلاق")]
        if fa else [("warm", "Warm orange"), ("midnight", "Professional dark"), ("sage", "Calm sage"), ("plum", "Creative plum")],
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
        demos = list(context["demos"])
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
        context.update(lang=self.lang, labels=_labels(self.lang))
        return context


class DemoConfigureView(LanguageViewMixin, View):
    def post(self, request, slug):
        demo = DemoTemplate.objects.filter(slug=slug, is_active=True).first()
        if demo is None:
            raise Http404
        theme = request.POST.get("theme", "")
        personality = request.POST.get("personality", "")
        features = [item for item in request.POST.getlist("features") if item in FEATURES]
        if theme not in THEMES or personality not in PERSONALITIES or len(features) > 6:
            return redirect(reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1")
        selection = DemoSelection.objects.create(
            template=demo,
            session_key=_selection_session_key(request),
            selections={"theme": theme, "personality": personality, "features": features},
        )
        request.session["demo_selection_token"] = str(selection.public_token)
        request.session.modified = True
        request_type = REQUEST_TYPES[demo.category]
        return redirect(f"{reverse('leads:contact')}?demo={selection.public_token}&request_type={request_type}")

class ProjectListView(LanguageViewMixin, ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return Project.objects.filter(is_active=True).only(
            "id", "title_en", "title_fa", "slug", "image", "description_en", "description_fa", "demo_url", "repo_url"
        )

class ProjectDetailView(LanguageViewMixin, DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Project.objects.filter(is_active=True)
