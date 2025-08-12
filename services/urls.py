"""
مسیرهای اپلیکیشن Services

این اپلیکیشن مسئول نمایش لیست خدمات و جزئیات آن‌هاست.
در حال حاضر فقط صفحه لیست خدمات پیاده‌سازی شده است.
"""

# ==== ایمپورت‌ها ====
from django.urls import path
from .views import ServiceListView

# ==== فضای نام (namespace) ====
app_name = "services"

# ==== مسیرها ====
urlpatterns = [
    # صفحه لیست تمام خدمات
    path("", ServiceListView.as_view(), name="list"),
]
