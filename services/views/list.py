# services/views/list.py
from django.views.generic import ListView
from services.models import Service

class ServiceListView(ListView):
    """
    لیست سرویس‌های فعال.
    """
    template_name = "services/list.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "fa")
        context["lang"] = lang
        return context