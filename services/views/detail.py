

from django.views.generic import DetailView
from services.models import Service
from core.views.lang import LanguageViewMixin

class ServiceDetailView(LanguageViewMixin, DetailView):
    model = Service
    template_name = "services/detail.html"
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object

        context["title"] = service.title_fa if self.lang == "fa" else service.title_en
        context["description"] = service.description_fa if self.lang == "fa" else service.description_en
        context["summary"] = service.short_description_fa if self.lang == "fa" else service.short_description_en
        context["duration"] = service.duration_fa if self.lang == "fa" else service.duration_en
        context["deliverables"] = service.deliverables(self.lang)
        context["process_steps"] = service.process_steps(self.lang)
        return context

    def get_queryset(self):
        return Service.objects.filter(is_active=True)

    slug_field = "slug"
    slug_url_kwarg = "slug"
