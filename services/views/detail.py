

from django.views.generic import DetailView
from services.models import Service

class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/detail.html"
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "en")
        service = self.object

        context["lang"] = lang
        context["title"] = service.title_fa if lang == "fa" else service.title_en
        context["description"] = service.description_fa if lang == "fa" else service.description_en
        return context