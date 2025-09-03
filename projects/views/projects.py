


from django.views.generic import ListView, DetailView
from projects.models.projects import Project

class ProjectListView(ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        lang = self.request.GET.get("lang", "fa")
        return Project.objects.filter(is_active=True).only(
            "id", "title_en", "title_fa", "slug", "image", "description_en", "description_fa", "link"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang"] = self.request.GET.get("lang", "fa")
        return context

class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang"] = self.request.GET.get("lang", "fa")
        return context