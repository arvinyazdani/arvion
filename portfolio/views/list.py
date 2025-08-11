# portfolio/views/list.py
from django.views.generic import ListView
from portfolio.models import Project

class ProjectListView(ListView):
    """
    لیست پروژه‌ها با فیلتر اختیاری تکنولوژی (پارامتر tech).
    """
    template_name = "portfolio/list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        qs = Project.objects.published()
        tech = self.request.GET.get("tech")
        if tech:
            qs = qs.filter(techs__name__iexact=tech)
        return qs