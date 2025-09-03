"""
تنظیمات مسیرهای اصلی پروژه Arvion

در این ساختار:
    - زبان سایت از طریق پارامتر GET به نام lang کنترل می‌شود (fa یا en)
    - برای ساده‌سازی، از i18n_patterns استفاده نشده است
    - مسیرهای اپلیکیشن‌ها به صورت namespace شده اضافه شده‌اند
"""

# ==== ایمپورت‌ها ====
from django.contrib import admin
from django.urls import path, include
from core.views import HomeView, AboutView  # ویوهای اصلی سایت
from django.conf import settings
from django.conf.urls.static import static

# ==== مسیرهای اصلی ====
urlpatterns = [
    # مسیر پنل مدیریت
    path('admin/', admin.site.urls),

    # مسیرهای اپلیکیشن core
    path('', HomeView.as_view(), name='home'),  # صفحه اصلی
    path('about/', AboutView.as_view(), name='about'),  # درباره ما

    # مسیرهای اپلیکیشن وبلاگ
    path('blog/', include(('blog.urls', 'blog'), namespace='blog')),  # وبلاگ

    # مسیرهای اپلیکیشن نمونه‌کارها
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),  # پروژه‌ها

    # مسیرهای اپلیکیشن سرویس‌ها
    path('services/', include(('services.urls', 'services'), namespace='services')),  # سرویس‌ها

    # مسیرهای اپلیکیشن تماس/فرم لید
    path('contact/', include(('leads.urls', 'leads'), namespace='leads')),  # تماس با ما/فرم لید

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)