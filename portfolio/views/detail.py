# portfolio/views/detail.py
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from portfolio.models import Project

class ProjectDetailView(DetailView):
    """
    صفحه جزئیات پروژه.
    """
    template_name = "portfolio/detail.html"
    context_object_name = "project"

    def get_object(self):
        slug = self.kwargs.get("slug")
        return get_object_or_404(Project, translations__slug=slug, is_published=True)