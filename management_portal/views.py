from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from assessments.models import Attempt, ManualPaymentSubmission, SupportTicket
from clinic_orders.models import ClinicOrder
from crm_orders.models import CrmOrder
from leads.models import Lead
from traffic.models import ActiveVisitor, TrafficDay
from contracts.models import ContractProposal
from accounts.staff_roles import STAFF_ROLES, group_name
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .forms import ManualSMSForm, StaffCreateForm, StaffRolesForm
from .models import ManagementNotification, SMSDispatch, StaffAccessAudit


def _metric(label, value, description, url="", tone=""):
    return {"label": label, "value": value, "description": description, "url": url, "tone": tone}


@staff_member_required(login_url="accounts:login")
def dashboard(request):
    """Permission-aware command centre outside Django's model administration UI."""
    user = request.user
    metrics = []
    queues = []
    if user.has_perm("accounts.change_user"):
        pending_users = User.objects.filter(is_active=False).order_by("-date_joined")
        metrics.append(_metric("حساب نیازمند تأیید", pending_users.count(), "فعال‌سازی و کنترل ثبت‌نام", reverse("admin:accounts_user_changelist") + "?is_active__exact=0", "warning"))
        queues += [{"kind": "حساب", "title": item.email, "meta": "منتظر فعال‌سازی", "date": item.date_joined, "url": reverse("admin:accounts_user_change", args=[item.pk])} for item in pending_users[:4]]
    if user.has_perm("leads.view_lead"):
        new_leads = Lead.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("درخواست همکاری جدید", new_leads.count(), "نیازمند اولین تماس", reverse("admin:leads_lead_changelist") + "?status__exact=new", "warning"))
        queues += [{"kind": "همکاری", "title": item.name, "meta": item.business_name or item.tracking_code, "date": item.created_at, "url": reverse("admin:leads_lead_change", args=[item.pk])} for item in new_leads[:4]]
    if user.has_perm("crm_orders.view_crmorder"):
        crm = CrmOrder.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("نیازسنجی CRM", crm.count(), "سفارش‌های تحلیل‌نشده", reverse("admin:crm_orders_crmorder_changelist") + "?status__exact=new", "warning"))
        queues += [{"kind": "CRM", "title": item.organization_name, "meta": item.tracking_code, "date": item.created_at, "url": reverse("admin:crm_orders_crmorder_change", args=[item.pk])} for item in crm[:4]]
    if user.has_perm("clinic_orders.view_clinicorder"):
        clinics = ClinicOrder.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("نیازسنجی کلینیک", clinics.count(), "درخواست‌های تحلیل‌نشده", reverse("admin:clinic_orders_clinicorder_changelist") + "?status__exact=new", "warning"))
        queues += [{"kind": "کلینیک", "title": item.clinic_name, "meta": item.tracking_code, "date": item.created_at, "url": reverse("admin:clinic_orders_clinicorder_change", args=[item.pk])} for item in clinics[:4]]
    if user.has_perm("assessments.view_manualpaymentsubmission"):
        payments = ManualPaymentSubmission.objects.filter(status="pending").select_related("order__user").order_by("-created_at")
        metrics.append(_metric("پرداخت منتظر بررسی", payments.count(), "تأیید بانکی و دسترسی آزمون", reverse("admin:assessments_manualpaymentsubmission_changelist") + "?status__exact=pending", "danger"))
        queues += [{"kind": "پرداخت", "title": item.payer_name, "meta": item.reference_number, "date": item.created_at, "url": reverse("admin:assessments_manualpaymentsubmission_change", args=[item.pk])} for item in payments[:4]]
    if user.has_perm("assessments.view_supportticket"):
        metrics.append(_metric("تیکت باز", SupportTicket.objects.filter(status__in=("open", "in_review")).count(), "نیازمند پاسخ یا پیگیری", reverse("admin:assessments_supportticket_changelist")))
    if user.has_perm("assessments.view_attempt"):
        metrics.append(_metric("آزمون در حال اجرا", Attempt.objects.filter(status="in_progress").count(), "نشست‌های فعال آزمون", reverse("admin:assessments_attempt_changelist")))

    chart = []
    online = None
    if user.has_perm("traffic.view_trafficday"):
        online = ActiveVisitor.objects.filter(last_seen__gte=timezone.now() - timedelta(minutes=5)).count()
        for day in reversed(TrafficDay.objects.order_by("-date")[:7]):
            chart.append({"label": day.date.strftime("%m/%d"), "views": day.page_views, "visitors": day.unique_visitors})
        today = TrafficDay.objects.filter(date=timezone.localdate()).first()
        metrics += [
            _metric("بازدید امروز", today.page_views if today else 0, "نمایش صفحه‌های عمومی"),
            _metric("کاربر آنلاین", online, "فعال در پنج دقیقه اخیر", tone="positive"),
        ]
    queues.sort(key=lambda item: item["date"], reverse=True)
    notifications = _visible_notifications(user)
    metrics.insert(0, _metric("اعلان خوانده‌نشده", notifications.filter(status="unread").count(), "رویدادهای تازه مرتبط با مسئولیت شما", reverse("management_portal:notification_list"), "warning"))
    if user.is_superuser:
        metrics.insert(1, _metric("قراردادها", ContractProposal.objects.exclude(status__in=("expired", "revoked")).count(), "ساخت، ارسال و پیگیری پذیرش", reverse("contracts:proposal_list"), "positive"))
        metrics.insert(2, _metric("مدیران و مسئولان", User.objects.filter(is_staff=True, is_superuser=False).count(), "ساخت همکار و تنظیم نقش‌ها", reverse("management_portal:staff_list")))
        metrics.insert(3, _metric("ارسال پیامک", SMSDispatch.objects.filter(status="sent").count(), "ارسال تکی یا گروهی و مشاهده سابقه", reverse("management_portal:sms_send")))
    # V2 never sends managers back to Django Admin. Modules are replaced phase by phase.
    for item in metrics:
        if item.get("url", "").startswith("/admin/"):
            item["url"] = ""
    for item in queues:
        if item.get("url", "").startswith("/admin/"):
            item["url"] = ""
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    if lang == "en":
        labels = {
            "اعلان خوانده‌نشده": ("Unread alerts", "New events related to your role"),
            "قراردادها": ("Contracts", "Create, share and track acceptance"),
            "مدیران و مسئولان": ("Team members", "Manage staff roles and access"),
            "ارسال پیامک": ("SMS messages", "Send and review delivery history"),
            "حساب نیازمند تأیید": ("Accounts awaiting approval", "Review and activate registrations"),
            "درخواست همکاری جدید": ("New enquiries", "Waiting for first contact"),
            "نیازسنجی CRM": ("CRM discoveries", "New requests awaiting review"),
            "نیازسنجی کلینیک": ("Clinic discoveries", "New requests awaiting review"),
            "پرداخت منتظر بررسی": ("Payments awaiting review", "Verify transfer and grant access"),
            "تیکت باز": ("Open tickets", "Waiting for a response"), "آزمون در حال اجرا": ("Active assessments", "Sessions currently in progress"),
            "بازدید امروز": ("Views today", "Public page views"), "کاربر آنلاین": ("Online users", "Active in the last five minutes"),
        }
        kinds = {"حساب": "Account", "همکاری": "Enquiry", "کلینیک": "Clinic", "پرداخت": "Payment"}
        for item in metrics:
            if item["label"] in labels:
                item["label"], item["description"] = labels[item["label"]]
        for item in queues:
            item["kind"] = kinds.get(item["kind"], item["kind"])
    return render(request, "management_portal/v2/dashboard.html", {
        "metrics": metrics, "queues": queues[:12], "chart": chart, "online": online, "lang": lang,
        "unread_count": notifications.filter(status="unread").count(),
    })


def _visible_notifications(user):
    queryset = ManagementNotification.objects.all()
    if user.is_superuser:
        return queryset
    roles = [name.removeprefix("rvion_") for name in user.groups.values_list("name", flat=True) if name.startswith("rvion_")]
    return queryset.filter(role__in=roles)


@staff_member_required(login_url="accounts:login")
def notification_list(request):
    status, category = request.GET.get("status", ""), request.GET.get("category", "")
    queryset = _visible_notifications(request.user)
    if status in dict(ManagementNotification.STATUSES):
        queryset = queryset.filter(status=status)
    if category in dict(ManagementNotification.CATEGORIES):
        queryset = queryset.filter(category=category)
    return render(request, "management_portal/notifications.html", {
        "notifications": queryset[:100], "statuses": ManagementNotification.STATUSES,
        "categories": ManagementNotification.CATEGORIES, "active_status": status, "active_category": category,
    })


@staff_member_required(login_url="accounts:login")
def notification_feed(request):
    since = request.GET.get("since")
    queryset = _visible_notifications(request.user).filter(status="unread")
    if since and since.isdigit():
        queryset = queryset.filter(pk__gt=int(since))
    items = list(queryset.order_by("pk")[:25])
    return JsonResponse({"notifications": [{"id": item.pk, "title": item.title, "description": item.description, "url": item.target_url} for item in items]})


@staff_member_required(login_url="accounts:login")
@require_POST
def notification_status(request, notification_id, status):
    if status not in dict(ManagementNotification.STATUSES):
        raise Http404
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    notification.status = status
    if status == "resolved":
        notification.resolved_by, notification.resolved_at = request.user, timezone.now()
    else:
        notification.resolved_by, notification.resolved_at = None, None
    notification.save(update_fields=["status", "resolved_by", "resolved_at", "updated_at"])
    return redirect(request.POST.get("next") or "management_portal:notification_list")


def _require_superuser(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return False
    if not request.user.is_superuser:
        raise PermissionDenied
    return True


@staff_member_required(login_url="accounts:login")
def staff_list(request):
    _require_superuser(request)
    role_names = [group_name(key) for key in STAFF_ROLES]
    staff = User.objects.filter(is_staff=True).prefetch_related("groups").order_by("-is_superuser", "first_name", "email")
    rows = []
    for member in staff:
        rows.append({
            "user": member,
            "roles": [config["label_fa"] for key, config in STAFF_ROLES.items() if member.groups.filter(name=group_name(key)).exists()],
        })
    return render(request, "management_portal/staff_list.html", {"staff_rows": rows, "role_names": role_names})


@staff_member_required(login_url="accounts:login")
def staff_create(request):
    _require_superuser(request)
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        member = form.save()
        StaffAccessAudit.objects.create(actor=request.user, target=member, action="created", roles=form.cleaned_data["roles"], staff_enabled=True)
        messages.success(request, f"حساب مدیریتی {member.email} ساخته شد.")
        return redirect("management_portal:staff_list")
    return render(request, "management_portal/staff_form.html", {"form": form, "title": "ساخت همکار جدید", "is_create": True})


@staff_member_required(login_url="accounts:login")
def staff_edit(request, user_id):
    _require_superuser(request)
    member = get_object_or_404(User, pk=user_id, is_staff=True)
    if member.is_superuser:
        raise PermissionDenied
    form = StaffRolesForm(request.POST or None, user=member)
    if request.method == "POST" and form.is_valid():
        form.save()
        StaffAccessAudit.objects.create(actor=request.user, target=member, action="roles_updated", roles=form.cleaned_data["roles"], staff_enabled=form.cleaned_data["is_staff"])
        messages.success(request, f"مسئولیت‌های {member.email} بروزرسانی شد.")
        return redirect("management_portal:staff_list")
    return render(request, "management_portal/staff_form.html", {"form": form, "title": "ویرایش مسئولیت‌ها", "member": member})


@staff_member_required(login_url="accounts:login")
def sms_send(request):
    _require_superuser(request)
    form = ManualSMSForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sent = failed = 0
        for recipient in form.cleaned_data["recipients"]:
            try:
                result = send_sms(recipient, form.cleaned_data["message"])
            except (SMSDeliveryError, ImproperlyConfigured, ValueError) as exc:
                failed += 1
                SMSDispatch.objects.create(
                    recipient=recipient, message=form.cleaned_data["message"], status="failed",
                    error_message=str(exc)[:240], sent_by=request.user,
                )
            else:
                sent += 1
                SMSDispatch.objects.create(
                    recipient=recipient, message=form.cleaned_data["message"], status="sent",
                    provider=result.provider, provider_reference=result.reference, sent_by=request.user,
                )
        if sent:
            messages.success(request, f"{sent} پیامک برای ارسال پذیرفته شد.")
        if failed:
            messages.error(request, f"ارسال برای {failed} شماره ناموفق بود؛ جزئیات در سابقه ثبت شد.")
        return redirect("management_portal:sms_send")
    return render(request, "management_portal/sms_send.html", {
        "form": form, "history": SMSDispatch.objects.select_related("sent_by")[:50],
    })
