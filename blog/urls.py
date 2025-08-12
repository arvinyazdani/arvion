"""
مسیرهای اپلیکیشن وبلاگ (blog)

در این فایل مسیرهای مربوط به:
    - لیست پست‌ها
    - صفحه جزئیات هر پست
تعریف شده‌اند.

نکته: برای پشتیبانی از اسلاگ‌های فارسی، از الگوی re_path با یونیکد استفاده می‌کنیم.
"""

# ==== ایمپورت‌ها ====
from django.urls import path, re_path  # ایمپورت path و re_path برای تعریف مسیرها
from .views import PostListView, PostDetailView  # ایمپورت ویوهای مورد نیاز

# ==== تنظیم فضای نام (namespace) ====
app_name = "blog"

# ==== مسیرها ====
urlpatterns = [
    # صفحه لیست تمام پست‌ها
    path("", PostListView.as_view(), name="list"),

    # صفحه جزئیات پست (پشتیبانی از اسلاگ‌های فارسی و انگلیسی)
    # این الگو اسلاگ‌هایی با حروف فارسی، انگلیسی، اعداد و خط تیره را می‌پذیرد
    re_path(r'^(?P<slug>[-\w\u0600-\u06FF]+)/$', PostDetailView.as_view(), name="detail"),
]