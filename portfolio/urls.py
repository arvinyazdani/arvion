"""
مسیرهای اپلیکیشن Portfolio

این اپلیکیشن مسئول نمایش نمونه‌کارها و جزئیات آن‌هاست.
صفحات شامل:
    - لیست نمونه‌کارها (ProjectListView)
    - صفحه جزئیات هر نمونه‌کار (ProjectDetailView)
"""

# ==== ایمپورت‌ها ====
from django.urls import path, re_path
from .views import ProjectListView, ProjectDetailView

# ==== فضای نام (namespace) ====
app_name = "portfolio"

# ==== مسیرها ====
urlpatterns = [
    # صفحه لیست تمام نمونه‌کارها
    path("", ProjectListView.as_view(), name="list"),

    # صفحه جزئیات نمونه‌کار (پشتیبانی از اسلاگ فارسی و انگلیسی)
    re_path(
        r'^(?P<slug>[-\w\u0600-\u06FF]+)/$',
        ProjectDetailView.as_view(),
        name="detail"
    ),
]