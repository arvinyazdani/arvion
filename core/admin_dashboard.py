from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import reverse

from assessments.models import Attempt, ManualPaymentSubmission, Order, SupportTicket
from blog.models import Post
from leads.models import Lead
from crm_orders.models import CrmOrder
from accounts.models import User
from traffic.models import ActiveVisitor, TrafficDay
from django.utils import timezone
from datetime import timedelta


def _card(title, value, description, url, tone="neutral"):
    return {"title": title, "value": value, "description": description, "url": url, "tone": tone}


@staff_member_required
def operations_dashboard(request):
    """A permission-aware overview; staff never receive counts they cannot access."""
    cards = []
    user = request.user
    if user.has_perm("accounts.change_user"):
        cards.append(_card("حساب‌های در انتظار تأیید", User.objects.filter(is_active=False).count(), "تطبیق اطلاعات و فعال‌سازی دستی", reverse("admin:accounts_user_changelist") + "?is_active__exact=0", "attention"))
    if user.has_perm("leads.view_lead"):
        cards.extend((
            _card("درخواست‌های جدید", Lead.objects.filter(status="new").count(), "نیازمند اولین تماس", reverse("admin:leads_lead_changelist") + "?status__exact=new", "attention"),
            _card("فرصت‌های فعال", Lead.objects.filter(status__in=("contacted", "qualified", "proposal")).count(), "در مسیر مذاکره و پیشنهاد", reverse("admin:leads_lead_changelist"), "positive"),
        ))
    if user.has_perm("crm_orders.view_crmorder"):
        cards.append(_card("سفارش‌های CRM", CrmOrder.objects.filter(status="new").count(), "نیازمند تحلیل اولیه", reverse("admin:crm_orders_crmorder_changelist") + "?status__exact=new", "attention"))
    if user.has_perm("assessments.view_order"):
        cards.append(_card("سفارش‌های معلق", Order.objects.filter(status="pending").count(), "در انتظار تعیین وضعیت", reverse("admin:assessments_order_changelist") + "?status__exact=pending", "attention"))
    if user.has_perm("assessments.view_manualpaymentsubmission"):
        cards.append(_card("واریزهای نیازمند تأیید", ManualPaymentSubmission.objects.filter(status="pending").count(), "بررسی بانکی و فعال‌سازی دسترسی", reverse("admin:assessments_manualpaymentsubmission_changelist") + "?status__exact=pending", "attention"))
    if user.has_perm("assessments.view_attempt"):
        cards.append(_card("آزمون‌های در حال اجرا", Attempt.objects.filter(status="in_progress").count(), "جلسه‌های فعال کاربران", reverse("admin:assessments_attempt_changelist") + "?status__exact=in_progress"))
    if user.has_perm("assessments.view_supportticket"):
        cards.append(_card("تیکت‌های باز", SupportTicket.objects.filter(status__in=("open", "in_review")).count(), "نیازمند پاسخ یا پیگیری", reverse("admin:assessments_supportticket_changelist"), "attention"))
    if user.has_perm("blog.view_post"):
        cards.append(_card("پیش‌نویس محتوا", Post.objects.filter(is_published=False).count(), "مقاله‌های منتشرنشده", reverse("admin:blog_post_changelist") + "?is_published__exact=0"))
    traffic_history = []
    if user.has_perm("traffic.view_trafficday"):
        today = timezone.localdate()
        today_metric = TrafficDay.objects.filter(date=today).first()
        cards.extend((
            _card("بازدید امروز", today_metric.page_views if today_metric else 0, "تعداد نمایش صفحات عمومی", reverse("admin:traffic_trafficday_changelist")),
            _card("بازدیدکننده یکتای امروز", today_metric.unique_visitors if today_metric else 0, "بر پایه نشست ناشناس", reverse("admin:traffic_trafficday_changelist"), "positive"),
            _card("آنلاین در ۵ دقیقه", ActiveVisitor.objects.filter(last_seen__gte=timezone.now() - timedelta(minutes=5)).count(), "بازدیدکنندگان فعال اخیر", reverse("admin:traffic_activevisitor_changelist"), "positive"),
        ))
        traffic_history = list(TrafficDay.objects.order_by("-date")[:14])
    return render(request, "admin/operations_dashboard.html", {
        "cards": cards,
        "title": "داشبورد عملیات",
        "traffic_history": traffic_history,
    })
