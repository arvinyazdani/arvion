# core/views/base.py
# ویوهای پایه (Home و About) — کلاسی، چندزبانه و قابل گسترش

# ==== ایمپورت‌ها ====
from django.views.generic import TemplateView
from blog.models import Post
from portfolio.models import Project
from .lang import LanguageViewMixin  # میکسین مدیریت زبان

# ==== ویو خانه ====
class HomeView(LanguageViewMixin, TemplateView):
    """
    ویوی صفحه خانه:
      - ارث‌بری از LanguageViewMixin برای تشخیص زبان جاری
      - نمایش خلاصه‌ای از برند
      - نمایش آخرین پست‌ها و پروژه‌ها (۳ مورد)
      - داده‌ها بر اساس زبان انتخابی از مدل‌ها خوانده می‌شوند
    """
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        # گرفتن context پایه از TemplateView + LanguageViewMixin
        ctx = super().get_context_data(**kwargs)

        # آخرین ۳ پست منتشر شده
        posts = list(Post.objects.published()[:3])
        # آخرین ۳ پروژه منتشر شده
        projects = list(Project.objects.published()[:3])

        # اگر مدل‌ها چندزبانه هستند (مثلاً با django-parler) این قسمت زبان را اعمال می‌کند
        for p in posts:
            try:
                p.set_current_language(self.lang)
            except AttributeError:
                pass  # اگر مدل از parler استفاده نمی‌کند، مشکلی ایجاد نشود

        for pr in projects:
            try:
                pr.set_current_language(self.lang)
            except AttributeError:
                pass

        # افزودن به context
        ctx["latest_posts"] = posts
        ctx["latest_projects"] = projects

        return ctx


# ==== ویو درباره ====
class AboutView(LanguageViewMixin, TemplateView):
    template_name = "core/about.html"