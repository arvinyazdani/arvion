# core/views/base.py
# ویوهای پایه (Home و About) — کلاسی و قابل گسترش
from django.views.generic import TemplateView
from blog.models import Post
from portfolio.models import Project

class HomeView(TemplateView):
    """
    صفحه خانه: نمایش خلاصه‌ای از برند + آخرین پست‌ها و پروژه‌ها.
    """
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # توجه: QuerySetها با managerهای published() تامین می‌شوند.
        ctx["latest_posts"] = Post.objects.published()[:3]
        ctx["latest_projects"] = Project.objects.published()[:3]
        return ctx


class AboutView(TemplateView):
    """
    صفحه درباره: محتوا از مدل Page خوانده می‌شود (دو زبانه).
    """
    template_name = "core/about.html"