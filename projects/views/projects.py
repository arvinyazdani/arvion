


from django.views.generic import ListView, DetailView
from projects.models.projects import Project
from core.views.lang import LanguageViewMixin

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
