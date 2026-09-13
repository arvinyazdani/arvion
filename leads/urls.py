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
from .views import FormDraftDeleteView, FormDraftView, LeadCreateView, LeadThanksView

# ==== فضای نام (namespace) ====
app_name = "leads"

# ==== مسیرها ====
urlpatterns = [
    # صفحه فرم تماس (نمایش فرم ثبت لید)
    path("", LeadCreateView.as_view(), name="contact"),
    path("thanks/<str:code>/", LeadThanksView.as_view(), name="thanks"),

    # API حساب‌محور پیش‌نویس فرم تماس: GET/POST خواندن و ذخیره،
    # POST جدا برای حذف — هر دو فقط برای مشتری واردشده و غیر staff.
    path("draft/", FormDraftView.as_view(), name="draft"),
    path("draft/delete/", FormDraftDeleteView.as_view(), name="draft_delete"),
]
