

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
        return context

    def get_queryset(self):
        return Service.objects.filter(is_active=True)
