

"""
مسیرهای اپلیکیشن core

این اپلیکیشن شامل صفحات اصلی سایت است:
    - صفحه خانه (Home)
    - صفحه درباره ما (About)

زبان سایت از طریق پارامتر GET (مثل ?lang=fa یا ?lang=en) کنترل می‌شود.
"""

# ==== ایمپورت‌ها ====
from django.urls import path
from .views.base import HomeView, AboutView

# ==== فضای نام (namespace) ====
app_name = "core"

# ==== مسیرها ====
urlpatterns = [
    # صفحه خانه
    path("", HomeView.as_view(), name="home"),

    # صفحه درباره ما
    path("about/", AboutView.as_view(), name="about"),
]