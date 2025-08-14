# leads/urls.py
# ==========================================
# مسیرهای اپلیکیشن Leads
#
# این اپلیکیشن مسئول مدیریت فرم‌های تماس یا ثبت لید (مشتری بالقوه) است.
# صفحات شامل:
#     - فرم تماس (LeadCreateView)
#     - صفحه تشکر پس از ارسال فرم (LeadThanksView)
# ==========================================

# ==== ایمپورت‌ها ====
from django.urls import path
from .views import LeadCreateView

# ==== فضای نام (namespace) ====
app_name = "leads"

# ==== مسیرها ====
urlpatterns = [
    # صفحه فرم تماس (نمایش فرم ثبت لید)
    path("", LeadCreateView.as_view(), name="contact"),

   
]