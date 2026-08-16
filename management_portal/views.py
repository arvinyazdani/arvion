from datetime import datetime, timedelta
import json
from pathlib import Path

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from assessments.models import Attempt, AttemptResult, Certificate, Exam, ManualPaymentSubmission, Order, SupportTicket
from clinic_orders.models import ClinicOrder
from crm_orders.models import CrmOrder
from leads.models import Lead
from traffic.models import ActiveVisitor, TrafficDay
from contracts.models import ContractProposal
from blog.models import Post
from core.models import Page
from projects.models import Project
from services.models import Service
from accounts.staff_roles import STAFF_ROLES, group_name
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .forms import CaseActivityForm, CaseTaskForm, CustomerCaseForm, CustomerContactForm, ManualSMSForm, StaffCreateForm, StaffRolesForm
from assessments.services import PaymentVerificationError, verify_gateway_payment
from .models import CaseActivity, CaseTask, Customer, CustomerCase, CustomerContact, ManagementNotification, NotificationReceipt, OperationalAudit, PushSubscription, SMSDispatch, StaffAccessAudit


@staff_member_required(login_url="accounts:login")
def customer_workspace(request):
    """One connected list of real customers, not a list of isolated forms."""
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.prefetch_related("contacts", "cases__tasks", "cases__activities").order_by("-updated_at")
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query) | Q(contacts__name__icontains=query) | Q(contacts__phone__icontains=query) | Q(contacts__email__icontains=query)).distinct()
    page = Paginator(customers, 30).get_page(request.GET.get("page"))
    now = timezone.now()
    no_contact = Customer.objects.annotate(contact_count=Count("contacts")).filter(contact_count=0).order_by("-updated_at")
    no_identity = Customer.objects.filter(phone="", email="").order_by("-updated_at")
    duplicate_phones = list(Customer.objects.exclude(phone="").values("phone").annotate(total=Count("pk")).filter(total__gt=1).order_by("-total")[:4])
    duplicate_emails = list(Customer.objects.exclude(email="").values("email").annotate(total=Count("pk")).filter(total__gt=1).order_by("-total")[:4])
    duplicate_candidates = ([{"label": row["phone"], "total": row["total"], "kind": "phone"} for row in duplicate_phones] + [{"label": row["email"], "total": row["total"], "kind": "email"} for row in duplicate_emails])[:6]
    data_quality = {
        "cases_without_customer": CustomerCase.objects.filter(customer__isnull=True).count(),
        "orders_without_customer": Order.objects.filter(customer__isnull=True).count(),
        "customers_without_contact": no_contact.count(),
        "customers_without_identity": no_identity.count(),
        "duplicate_count": len(duplicate_candidates),
        "needs_attention": no_contact[:4],
        "duplicate_candidates": duplicate_candidates,
    }
    return render(request, "management_portal/v2/customer_workspace.html", {
        "customers": page, "page_obj": page, "query": query, "lang": lang,
        "data_quality": data_quality,
        "stats": {
            "customers": Customer.objects.count(),
            "contacts": CustomerContact.objects.count(),
            "active_cases": CustomerCase.objects.exclude(stage__in=("won", "lost")).count(),
            "overdue": CaseTask.objects.filter(status="open", due_at__lt=now).count(),
        },
    })


@staff_member_required(login_url="accounts:login")
def customer_duplicates(request):
    """Read-only comparison surface. A later explicit merge action will live separately."""
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    field = request.GET.get("field", "")
    value = request.GET.get("value", "").strip()
    if field not in {"phone", "email"}:
        field, value = "", ""
    groups = []
    for candidate_field in ("phone", "email"):
        rows = Customer.objects.exclude(**{candidate_field: ""}).values(candidate_field).annotate(total=Count("pk")).filter(total__gt=1).order_by("-total", candidate_field)
        groups.extend({"field": candidate_field, "value": row[candidate_field], "total": row["total"]} for row in rows)
    compared_customers = Customer.objects.none()
    if field and value:
        compared_customers = Customer.objects.filter(**{field: value}).prefetch_related("contacts", "cases", "contracts", "assessment_orders").order_by("name")
    return render(request, "management_portal/v2/customer_duplicates.html", {"lang": lang, "groups": groups, "field": field, "value": value, "compared_customers": compared_customers})


@staff_member_required(login_url="accounts:login")
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer.objects.prefetch_related("contacts__user", "cases__owner", "cases__tasks", "cases__documents", "cases__activities__actor"), pk=customer_id)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    events = CaseActivity.objects.filter(case__customer=customer).select_related("case", "actor").order_by("-created_at")[:30]
    contracts = customer.contracts.select_related("created_by").order_by("-updated_at")[:10]
    orders = customer.assessment_orders.select_related("exam", "user", "manual_payment").order_by("-created_at")[:10]
    tickets = SupportTicket.objects.filter(Q(order__customer=customer) | Q(user__customer_contact_profiles__customer=customer)).select_related("order__exam", "user").distinct().order_by("-updated_at")[:10]
    return render(request, "management_portal/v2/customer_detail.html", {"customer": customer, "contact_form": CustomerContactForm(lang=lang), "events": events, "contracts": contracts, "orders": orders, "tickets": tickets, "lang": lang})


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_contact_create(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    form = CustomerContactForm(request.POST, lang=getattr(request, "LANGUAGE_CODE", "fa"))
    if form.is_valid():
        contact = form.save(commit=False)
        contact.customer = customer
        if contact.is_primary:
            CustomerContact.objects.filter(customer=customer, is_primary=True).update(is_primary=False)
        contact.save()
        OperationalAudit.objects.create(actor=request.user, action="customer_contact_created", target_type="customer", target_id=str(customer.pk), summary=contact.name)
        messages.success(request, "مخاطب به پرونده مشتری اضافه شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Contact added to customer record.")
    else:
        messages.error(request, "اطلاعات مخاطب معتبر نیست." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Contact details are invalid.")
    return redirect("management_portal:customer_detail", customer_id=customer.pk)


@staff_member_required(login_url="accounts:login")
def crm_workspace(request):
    _require_sales_access(request.user)
    lang = getattr(request, "LANGUAGE_CODE", "fa"); query = request.GET.get("q", "").strip(); stage = request.GET.get("stage", ""); owner = request.GET.get("owner", "")
    cases = CustomerCase.objects.select_related("owner", "source_content_type").prefetch_related("tasks", "documents")
    if query: cases = cases.filter(Q(customer_name__icontains=query) | Q(contact_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query) | Q(code__icontains=query))
    if stage in dict(CustomerCase.STAGES): cases = cases.filter(stage=stage)
    if owner.isdigit(): cases = cases.filter(owner_id=owner)
    now = timezone.now(); page = Paginator(cases, 30).get_page(request.GET.get("page")); backup_dir = Path(getattr(settings, "CRM_BACKUP_DIR", "/srv/arvion/backups")); backups = sorted(backup_dir.glob("*.dump"), key=lambda item: item.stat().st_mtime, reverse=True) if backup_dir.exists() else []; latest_backup = backups[0] if backups else None
    backup_status = {"available": bool(latest_backup), "name": latest_backup.name if latest_backup else "", "size_mb": round(latest_backup.stat().st_size / 1048576, 2) if latest_backup else 0, "modified_at": datetime.fromtimestamp(latest_backup.stat().st_mtime, tz=timezone.get_current_timezone()) if latest_backup else None}
    backup_status["healthy"] = bool(backup_status["modified_at"] and backup_status["modified_at"] >= now - timedelta(hours=26))
    return render(request, "management_portal/v2/crm_workspace.html", {"cases": page, "page_obj": page, "query": query, "active_stage": stage, "active_owner": owner, "stages": CustomerCase.STAGES, "owners": User.objects.filter(is_staff=True, is_active=True), "lang": lang, "backup_status": backup_status, "stats": {"all": CustomerCase.objects.count(), "urgent": CustomerCase.objects.filter(priority="urgent").count(), "overdue": CaseTask.objects.filter(status="open", due_at__lt=now).count(), "today": CustomerCase.objects.filter(next_follow_up_at__date=timezone.localdate()).count()}})


@staff_member_required(login_url="accounts:login")
def crm_case_detail(request, case_id):
    _require_sales_access(request.user); case = get_object_or_404(CustomerCase.objects.select_related("owner", "source_content_type"), pk=case_id); lang = getattr(request, "LANGUAGE_CODE", "fa")
    return render(request, "management_portal/v2/crm_case_detail.html", {"case": case, "case_form": CustomerCaseForm(instance=case, lang=lang), "task_form": CaseTaskForm(lang=lang), "activity_form": CaseActivityForm(lang=lang), "lang": lang})


@staff_member_required(login_url="accounts:login")
@require_POST
def crm_case_update(request, case_id):
    _require_case_change(request.user); case = get_object_or_404(CustomerCase, pk=case_id); old_stage = case.stage; form = CustomerCaseForm(request.POST, instance=case, lang=getattr(request, "LANGUAGE_CODE", "fa"))
    if form.is_valid():
        case = form.save(); CaseActivity.objects.create(case=case, actor=request.user, kind="status", title="پرونده بروزرسانی شد", body=f"{old_stage} → {case.stage}"); OperationalAudit.objects.create(actor=request.user, action="crm_case_updated", target_type="customer_case", target_id=str(case.pk), summary=case.customer_name, metadata={"stage": case.stage, "priority": case.priority})
        messages.success(request, "پرونده ذخیره شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Case saved.")
    else: messages.error(request, "اطلاعات پرونده معتبر نیست." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Case data is invalid.")
    return redirect("management_portal:crm_case_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
@require_POST
def crm_task_create(request, case_id):
    _require_case_change(request.user); case = get_object_or_404(CustomerCase, pk=case_id); form = CaseTaskForm(request.POST, lang=getattr(request, "LANGUAGE_CODE", "fa"))
    if form.is_valid():
        task = form.save(commit=False); task.case, task.created_by = case, request.user; task.save(); CaseActivity.objects.create(case=case, actor=request.user, kind="task", title="وظیفه ساخته شد", body=task.title)
    return redirect("management_portal:crm_case_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
@require_POST
def crm_task_toggle(request, task_id):
    _require_case_change(request.user); task = get_object_or_404(CaseTask, pk=task_id); task.status = "open" if task.status == "done" else "done"; task.completed_at = None if task.status == "open" else timezone.now(); task.save(update_fields=("status", "completed_at")); CaseActivity.objects.create(case=task.case, actor=request.user, kind="task", title="وضعیت وظیفه تغییر کرد", body=task.title); return redirect("management_portal:crm_case_detail", case_id=task.case_id)


@staff_member_required(login_url="accounts:login")
@require_POST
def crm_activity_create(request, case_id):
    _require_case_change(request.user); case = get_object_or_404(CustomerCase, pk=case_id); form = CaseActivityForm(request.POST, lang=getattr(request, "LANGUAGE_CODE", "fa"))
    if form.is_valid(): activity = form.save(commit=False); activity.case, activity.actor = case, request.user; activity.save(); case.last_contact_at = timezone.now(); case.save(update_fields=("last_contact_at", "updated_at"))
    return redirect("management_portal:crm_case_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
def crm_case_export(request, case_id):
    _require_sales_access(request.user); case = get_object_or_404(CustomerCase, pk=case_id); lines = [f"پرونده {case.code}", f"مشتری: {case.customer_name}", f"مخاطب: {case.contact_name}", f"تلفن: {case.phone}", f"ایمیل: {case.email}", f"مرحله: {case.get_stage_display()}", f"اولویت: {case.get_priority_display()}", "", "اسناد:"]
    lines += [f"- {doc.get_kind_display()}: {doc.title} ({doc.created_at:%Y-%m-%d %H:%M})" for doc in case.documents.all()]; lines += ["", "تاریخچه:"]; lines += [f"- {item.created_at:%Y-%m-%d %H:%M} | {item.get_kind_display()} | {item.title} | {item.body}" for item in case.activities.all()]
    OperationalAudit.objects.create(actor=request.user, action="crm_case_exported", target_type="customer_case", target_id=str(case.pk), summary=case.customer_name)
    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8"); response["Content-Disposition"] = f'attachment; filename="{case.code}.txt"'; return response


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
        metrics.append(_metric("حساب نیازمند تأیید", pending_users.count(), "فعال‌سازی و کنترل ثبت‌نام", reverse("management_portal:approvals"), "warning"))
        queues += [{"kind": "حساب", "title": item.email, "meta": "منتظر فعال‌سازی", "date": item.date_joined, "url": reverse("management_portal:approvals")} for item in pending_users[:4]]
    if user.has_perm("leads.view_lead"):
        new_leads = Lead.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("درخواست همکاری جدید", new_leads.count(), "نیازمند اولین تماس", reverse("management_portal:request_list") + "?kind=lead", "warning"))
        queues += [{"kind": "همکاری", "title": item.name, "meta": item.business_name or item.tracking_code, "date": item.created_at, "url": reverse("management_portal:request_detail", args=["lead", item.pk])} for item in new_leads[:4]]
    if user.has_perm("crm_orders.view_crmorder"):
        crm = CrmOrder.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("نیازسنجی CRM", crm.count(), "سفارش‌های تحلیل‌نشده", reverse("management_portal:request_list") + "?kind=crm", "warning"))
        queues += [{"kind": "CRM", "title": item.organization_name, "meta": item.tracking_code, "date": item.created_at, "url": reverse("management_portal:request_detail", args=["crm", item.pk])} for item in crm[:4]]
    if user.has_perm("clinic_orders.view_clinicorder"):
        clinics = ClinicOrder.objects.filter(status="new").order_by("-created_at")
        metrics.append(_metric("نیازسنجی کلینیک", clinics.count(), "درخواست‌های تحلیل‌نشده", reverse("management_portal:request_list") + "?kind=clinic", "warning"))
        queues += [{"kind": "کلینیک", "title": item.clinic_name, "meta": item.tracking_code, "date": item.created_at, "url": reverse("management_portal:request_detail", args=["clinic", item.pk])} for item in clinics[:4]]
    if user.has_perm("assessments.view_manualpaymentsubmission"):
        payments = ManualPaymentSubmission.objects.filter(status="pending").select_related("order__user").order_by("-created_at")
        metrics.append(_metric("پرداخت منتظر بررسی", payments.count(), "تأیید بانکی و دسترسی آزمون", reverse("management_portal:approvals"), "danger"))
        queues += [{"kind": "پرداخت", "title": item.payer_name, "meta": item.reference_number, "date": item.created_at, "url": reverse("management_portal:approvals")} for item in payments[:4]]
    if user.has_perm("assessments.view_supportticket"):
        metrics.append(_metric("تیکت باز", SupportTicket.objects.filter(status__in=("open", "in_review")).count(), "نیازمند پاسخ یا پیگیری", reverse("management_portal:assessment_support")))
    if user.has_perm("assessments.view_attempt"):
        metrics.append(_metric("آزمون در حال اجرا", Attempt.objects.filter(status="in_progress").count(), "نشست‌های فعال آزمون", reverse("management_portal:assessment_support")))

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
        metrics.insert(1, _metric("قراردادها", ContractProposal.objects.exclude(status__in=("expired", "revoked")).count(), "ساخت، ارسال و پیگیری پذیرش", reverse("management_portal:contract_list"), "positive"))
        metrics.insert(2, _metric("مدیران و مسئولان", User.objects.filter(is_staff=True, is_superuser=False).count(), "ساخت همکار و تنظیم نقش‌ها", reverse("management_portal:staff_list")))
        metrics.insert(3, _metric("ارسال پیامک", SMSDispatch.objects.filter(status="sent").count(), "ارسال تکی یا گروهی و مشاهده سابقه", reverse("management_portal:sms_send")))
    # V2 never sends managers back to Django Admin. Modules are replaced phase by phase.
    for item in metrics:
        if item.get("url", "").startswith("/admin/"):
            if item["label"] in {"درخواست همکاری جدید", "نیازسنجی CRM", "نیازسنجی کلینیک"}:
                item["url"] = reverse("management_portal:request_list")
            elif item["label"] in {"حساب نیازمند تأیید", "پرداخت منتظر بررسی"}:
                item["url"] = reverse("management_portal:approvals")
            else:
                item["url"] = ""
    for item in queues:
        if item.get("url", "").startswith("/admin/"):
            kind_map = {"همکاری": "lead", "CRM": "crm", "کلینیک": "clinic"}
            kind = kind_map.get(item["kind"])
            if kind:
                source = item["url"].split("/")[-3]
                item["url"] = reverse("management_portal:request_detail", args=[kind, source])
            elif item["kind"] in {"حساب", "پرداخت"}:
                item["url"] = reverse("management_portal:approvals")
            else:
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
    recent_customers = Customer.objects.prefetch_related("contacts", "cases").order_by("-updated_at")[:8]
    open_tasks = CaseTask.objects.filter(status="open").select_related("case__customer", "assigned_to").order_by("due_at", "-created_at")[:8]
    inbox_items = notifications.select_related().filter(status="unread").order_by("-created_at")[:6]
    return render(request, "management_portal/v2/operations_dashboard.html", {
        "metrics": metrics, "queues": queues[:12], "chart": chart, "online": online, "lang": lang,
        "unread_count": notifications.filter(status="unread").count(),
        "recent_customers": recent_customers, "open_tasks": open_tasks, "inbox_items": inbox_items,
        "document_counts": {"discoveries": CrmOrder.objects.count() + ClinicOrder.objects.count(), "contracts": ContractProposal.objects.count() if user.is_superuser else 0},
    })


def _require_sales_access(user):
    if not user.is_superuser and not (user.has_perm("leads.view_lead") or user.has_perm("crm_orders.view_crmorder") or user.has_perm("clinic_orders.view_clinicorder")):
        raise PermissionDenied


def _require_case_change(user):
    if not user.is_superuser and not (user.has_perm("leads.change_lead") or user.has_perm("crm_orders.change_crmorder") or user.has_perm("clinic_orders.change_clinicorder")):
        raise PermissionDenied


@staff_member_required(login_url="accounts:login")
def request_list(request):
    _require_sales_access(request.user)
    kind = request.GET.get("kind", "all")
    query = request.GET.get("q", "").strip()
    rows = []
    if kind in {"all", "lead"} and (request.user.is_superuser or request.user.has_perm("leads.view_lead")):
        qs = Lead.objects.all()
        if query: qs = qs.filter(name__icontains=query)
        rows += [{"kind": "lead", "kind_label": "درخواست همکاری", "id": x.pk, "title": x.business_name or x.name, "contact": x.name, "code": x.tracking_code, "status": x.get_status_display(), "created_at": x.created_at} for x in qs[:100]]
    if kind in {"all", "crm"} and (request.user.is_superuser or request.user.has_perm("crm_orders.view_crmorder")):
        qs = CrmOrder.objects.all()
        if query: qs = qs.filter(organization_name__icontains=query)
        rows += [{"kind": "crm", "kind_label": "CRM", "id": x.pk, "title": x.organization_name, "contact": x.contact_name, "code": x.tracking_code, "status": x.get_status_display(), "created_at": x.created_at} for x in qs[:100]]
    if kind in {"all", "clinic"} and (request.user.is_superuser or request.user.has_perm("clinic_orders.view_clinicorder")):
        qs = ClinicOrder.objects.all()
        if query: qs = qs.filter(clinic_name__icontains=query)
        rows += [{"kind": "clinic", "kind_label": "کلینیک", "id": x.pk, "title": x.clinic_name, "contact": x.contact_name, "code": x.tracking_code, "status": x.get_status_display(), "created_at": x.created_at} for x in qs[:100]]
    rows.sort(key=lambda x: x["created_at"], reverse=True)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    if lang == "en":
        status_labels = {"جدید": "New", "جلسه تحلیل": "Discovery", "واجد شرایط": "Qualified", "پیشنهاد ارسال شد": "Proposal sent", "قرارداد": "Won", "بسته‌شده": "Closed"}
        for row in rows:
            row["status"] = status_labels.get(str(row["status"]), row["status"])
    return render(request, "management_portal/v2/request_list.html", {"rows": rows, "active_kind": kind, "query": query, "lang": lang})


@staff_member_required(login_url="accounts:login")
def request_detail(request, kind, object_id):
    _require_sales_access(request.user)
    models = {"lead": Lead, "crm": CrmOrder, "clinic": ClinicOrder}
    model = models.get(kind)
    if not model: raise Http404
    permission = {"lead": "leads.view_lead", "crm": "crm_orders.view_crmorder", "clinic": "clinic_orders.view_clinicorder"}[kind]
    if not request.user.is_superuser and not request.user.has_perm(permission): raise PermissionDenied
    item = get_object_or_404(model, pk=object_id)
    if kind == "lead":
        title, contact, phone, email, code, summary = item.business_name or item.name, item.name, item.phone or "—", item.email_or_telegram, item.tracking_code, item.message
    elif kind == "crm":
        title, contact, phone, email, code, summary = item.organization_name, item.contact_name, item.phone, item.work_email, item.tracking_code, item.main_pain_points
    else:
        title, contact, phone, email, code, summary = item.clinic_name, item.contact_name, item.phone, item.work_email, item.tracking_code, item.main_pain_points
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    status_choices = list(model.STATUSES)
    if lang == "en" and kind in {"crm", "clinic"}:
        status_en = {"new": "New", "discovery": "Discovery", "qualified": "Qualified", "proposal": "Proposal sent", "won": "Won", "lost": "Closed"}
        status_choices = [(value, status_en[value]) for value, _ in status_choices]
    status_display = dict(status_choices).get(item.status, item.status)
    return render(request, "management_portal/v2/request_detail.html", {
        "item": item, "kind": kind, "title": title, "contact": contact, "phone": phone,
        "email": email, "code": code, "summary": summary, "lang": lang, "status_choices": status_choices, "status_display": status_display,
        "can_change": request.user.is_superuser or request.user.has_perm({"lead": "leads.change_lead", "crm": "crm_orders.change_crmorder", "clinic": "clinic_orders.change_clinicorder"}[kind]),
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def request_update(request, kind, object_id):
    """Update an enquiry without exposing Django Admin."""
    _require_sales_access(request.user)
    models = {"lead": Lead, "crm": CrmOrder, "clinic": ClinicOrder}
    model = models.get(kind)
    if not model:
        raise Http404
    permission = {"lead": "leads.change_lead", "crm": "crm_orders.change_crmorder", "clinic": "clinic_orders.change_clinicorder"}[kind]
    if not request.user.is_superuser and not request.user.has_perm(permission):
        raise PermissionDenied
    item = get_object_or_404(model, pk=object_id)
    status = request.POST.get("status", "")
    if status not in dict(model.STATUSES):
        raise Http404
    item.status = status
    update_fields = ["status"]
    if hasattr(item, "internal_notes"):
        item.internal_notes = request.POST.get("internal_notes", "").strip()
        update_fields.append("internal_notes")
    if kind == "lead":
        item.is_reviewed = status != "new"
        update_fields.append("is_reviewed")
    item.save(update_fields=update_fields)
    text = "درخواست با موفقیت بروزرسانی شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Request updated successfully."
    messages.success(request, text)
    return redirect("management_portal:request_detail", kind=kind, object_id=object_id)


def _require_account_or_payment_access(user):
    if not user.is_superuser and not (user.has_perm("accounts.change_user") or user.has_perm("assessments.view_manualpaymentsubmission")):
        raise PermissionDenied


@staff_member_required(login_url="accounts:login")
def approvals(request):
    _require_account_or_payment_access(request.user)
    users = User.objects.filter(is_active=False).order_by("-date_joined")[:100] if request.user.is_superuser or request.user.has_perm("accounts.change_user") else []
    payments = ManualPaymentSubmission.objects.select_related("order__user", "order__exam", "reviewed_by").order_by("-created_at")[:100] if request.user.is_superuser or request.user.has_perm("assessments.view_manualpaymentsubmission") else []
    return render(request, "management_portal/v2/approvals.html", {"pending_users": users, "payments": payments, "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def account_approval(request, user_id, decision):
    if not request.user.is_superuser and not request.user.has_perm("accounts.change_user"):
        raise PermissionDenied
    if decision not in {"approve", "reject"}:
        raise Http404
    customer = get_object_or_404(User.objects.select_for_update(), pk=user_id, is_staff=False)
    if decision == "approve":
        customer.is_active = True
        customer.email_verified = True
        customer.save(update_fields=["is_active", "email_verified"])
        summary = f"حساب {customer.email} فعال شد"
    else:
        customer.is_active = False
        customer.save(update_fields=["is_active"])
        summary = f"درخواست حساب {customer.email} رد شد"
    OperationalAudit.objects.create(actor=request.user, action=f"account_{decision}", target_type="user", target_id=str(customer.pk), summary=summary)
    messages.success(request, summary)
    return redirect("management_portal:approvals")


@staff_member_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def payment_review(request, payment_id, decision):
    if not request.user.is_superuser and not request.user.has_perm("assessments.change_manualpaymentsubmission"):
        raise PermissionDenied
    if decision not in {"approve", "reject"}:
        raise Http404
    payment = get_object_or_404(ManualPaymentSubmission.objects.select_for_update().select_related("order__user", "order__exam"), pk=payment_id)
    if payment.status != "pending":
        messages.warning(request, "این رسید قبلاً بررسی شده است." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "This receipt has already been reviewed.")
        return redirect("management_portal:approvals")
    note = request.POST.get("review_note", "").strip()[:500]
    if decision == "approve":
        try:
            order, created = verify_gateway_payment(payment.order_id, gateway="card_transfer", external_id=f"card-{payment.reference_number}", amount_irr=payment.order.amount_irr, response={"manual_review": True, "reference": payment.reference_number})
        except PaymentVerificationError as exc:
            messages.error(request, str(exc))
            return redirect("management_portal:approvals")
        payment.status = "approved"
        if created:
            send_mail("پرداخت شما تأیید شد", f"پرداخت سفارش {order.pk} تأیید شد و دسترسی آزمون فعال است.\n{settings.SITE_URL}/fa/account/", settings.DEFAULT_FROM_EMAIL, [order.user.email], fail_silently=True)
    else:
        payment.status = "rejected"
    payment.reviewed_by, payment.reviewed_at, payment.review_note = request.user, timezone.now(), note
    payment.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
    OperationalAudit.objects.create(actor=request.user, action=f"payment_{decision}", target_type="manual_payment", target_id=str(payment.pk), summary=f"رسید {payment.reference_number}: {payment.status}", metadata={"order": str(payment.order_id)})
    messages.success(request, "بررسی رسید ذخیره شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Payment review saved.")
    return redirect("management_portal:approvals")


@staff_member_required(login_url="accounts:login")
def assessment_support(request):
    user = request.user
    if not user.is_superuser and not (user.has_perm("assessments.view_exam") or user.has_perm("assessments.view_supportticket")):
        raise PermissionDenied
    context = {"lang": getattr(request, "LANGUAGE_CODE", "fa")}
    if user.is_superuser or user.has_perm("assessments.view_exam"):
        context.update({
            "exams": Exam.objects.all()[:50],
            "attempts": Attempt.objects.select_related("user", "exam").order_by("-created_at")[:30],
            "result_count": AttemptResult.objects.count(), "certificate_count": Certificate.objects.filter(is_revoked=False).count(),
        })
    if user.is_superuser or user.has_perm("assessments.view_supportticket"):
        context["tickets"] = SupportTicket.objects.select_related("user").order_by("status", "-created_at")[:100]
    return render(request, "management_portal/v2/assessment_support.html", context)


@staff_member_required(login_url="accounts:login")
@require_POST
def ticket_status(request, ticket_id):
    if not request.user.is_superuser and not request.user.has_perm("assessments.change_supportticket"):
        raise PermissionDenied
    ticket = get_object_or_404(SupportTicket, pk=ticket_id)
    status = request.POST.get("status", "")
    if status not in dict(SupportTicket.STATUSES):
        raise Http404
    ticket.status = status
    ticket.save(update_fields=["status", "updated_at"])
    OperationalAudit.objects.create(actor=request.user, action="ticket_status", target_type="support_ticket", target_id=str(ticket.pk), summary=f"تیکت #{ticket.pk}: {status}")
    messages.success(request, "وضعیت تیکت بروزرسانی شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Ticket status updated.")
    return redirect("management_portal:assessment_support")


@staff_member_required(login_url="accounts:login")
def content_center(request):
    if not request.user.is_superuser and not (request.user.has_perm("blog.view_post") or request.user.has_perm("projects.view_project") or request.user.has_perm("services.view_service") or request.user.has_perm("core.view_page")):
        raise PermissionDenied
    return render(request, "management_portal/v2/content_center.html", {
        "posts": Post.objects.all()[:50] if request.user.is_superuser or request.user.has_perm("blog.view_post") else [],
        "projects": Project.objects.all()[:50] if request.user.is_superuser or request.user.has_perm("projects.view_project") else [],
        "services": Service.objects.all()[:50] if request.user.is_superuser or request.user.has_perm("services.view_service") else [],
        "pages": Page.objects.all()[:50] if request.user.is_superuser or request.user.has_perm("core.view_page") else [],
        "lang": getattr(request, "LANGUAGE_CODE", "fa"),
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def content_toggle(request, kind, object_id):
    config = {
        "post": (Post, "blog.change_post", "is_published"), "project": (Project, "projects.change_project", "is_active"),
        "service": (Service, "services.change_service", "is_active"),
    }
    if kind not in config:
        raise Http404
    model, permission, field = config[kind]
    if not request.user.is_superuser and not request.user.has_perm(permission):
        raise PermissionDenied
    item = get_object_or_404(model, pk=object_id)
    enabled = request.POST.get("enabled") == "1"
    setattr(item, field, enabled)
    update_fields = [field]
    if kind == "post":
        item.published_at = timezone.now() if enabled else None
        update_fields.append("published_at")
    item.save(update_fields=update_fields)
    OperationalAudit.objects.create(actor=request.user, action="content_state", target_type=kind, target_id=str(item.pk), summary=f"{kind} #{item.pk}: {enabled}")
    messages.success(request, "وضعیت انتشار ذخیره شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Publishing state saved.")
    return redirect("management_portal:content_center")


@staff_member_required(login_url="accounts:login")
def audit_log(request):
    _require_superuser(request)
    query = request.GET.get("q", "").strip()
    events = OperationalAudit.objects.select_related("actor")
    if query:
        from django.db.models import Q
        events = events.filter(Q(summary__icontains=query) | Q(action__icontains=query) | Q(actor__email__icontains=query))
    return render(request, "management_portal/v2/audit_log.html", {"events": events[:200], "query": query, "lang": getattr(request, "LANGUAGE_CODE", "fa")})


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
    visible_ids = list(queryset.values_list("pk", flat=True)[:100])
    NotificationReceipt.objects.filter(user=request.user, notification_id__in=visible_ids, seen_at__isnull=True).update(seen_at=timezone.now())
    return render(request, "management_portal/notifications.html", {
        "notifications": queryset[:100], "statuses": ManagementNotification.STATUSES,
        "categories": ManagementNotification.CATEGORIES, "active_status": status, "active_category": category,
        "lang": getattr(request, "LANGUAGE_CODE", "fa"),
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
def push_subscribe(request):
    if not settings.WEB_PUSH_VAPID_PUBLIC_KEY:
        return JsonResponse({"ok": False, "error": "push_not_configured"}, status=503)
    try:
        data = json.loads(request.body)
        endpoint, keys = data["endpoint"], data["keys"]
        p256dh, auth = keys["p256dh"], keys["auth"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_subscription"}, status=400)
    subscription, _ = PushSubscription.objects.update_or_create(endpoint=endpoint, defaults={"user": request.user, "p256dh": p256dh, "auth": auth, "user_agent": request.META.get("HTTP_USER_AGENT", "")[:240], "is_active": True})
    return JsonResponse({"ok": True, "id": subscription.pk})


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


@staff_member_required(login_url="accounts:login")
def notification_open(request, notification_id):
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    NotificationReceipt.objects.filter(user=request.user, notification=notification, seen_at__isnull=True).update(seen_at=timezone.now())
    return redirect(notification.target_url or "management_portal:notification_list")


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
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    for member in staff:
        rows.append({
            "user": member,
            "roles": [config[f"label_{lang}"] for key, config in STAFF_ROLES.items() if member.groups.filter(name=group_name(key)).exists()],
        })
    return render(request, "management_portal/staff_list.html", {"staff_rows": rows, "role_names": role_names, "lang": lang})


@staff_member_required(login_url="accounts:login")
def staff_create(request):
    _require_superuser(request)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = StaffCreateForm(request.POST or None, lang=lang)
    if request.method == "POST" and form.is_valid():
        member = form.save()
        StaffAccessAudit.objects.create(actor=request.user, target=member, action="created", roles=form.cleaned_data["roles"], staff_enabled=True)
        messages.success(request, f"حساب مدیریتی {member.email} ساخته شد." if lang == "fa" else f"Management account {member.email} was created.")
        return redirect("management_portal:staff_list")
    return render(request, "management_portal/staff_form.html", {"form": form, "title": "ساخت همکار جدید" if lang == "fa" else "Create team member", "is_create": True, "lang": lang})


@staff_member_required(login_url="accounts:login")
def staff_edit(request, user_id):
    _require_superuser(request)
    member = get_object_or_404(User, pk=user_id, is_staff=True)
    if member.is_superuser:
        raise PermissionDenied
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = StaffRolesForm(request.POST or None, user=member, lang=lang)
    if request.method == "POST" and form.is_valid():
        form.save()
        StaffAccessAudit.objects.create(actor=request.user, target=member, action="roles_updated", roles=form.cleaned_data["roles"], staff_enabled=form.cleaned_data["is_staff"])
        messages.success(request, f"مسئولیت‌های {member.email} بروزرسانی شد." if lang == "fa" else f"Responsibilities for {member.email} were updated.")
        return redirect("management_portal:staff_list")
    return render(request, "management_portal/staff_form.html", {"form": form, "title": "ویرایش مسئولیت‌ها" if lang == "fa" else "Edit responsibilities", "member": member, "lang": lang})


@staff_member_required(login_url="accounts:login")
def sms_send(request):
    _require_superuser(request)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = ManualSMSForm(request.POST or None, lang=lang)
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
            messages.success(request, f"{sent} پیامک برای ارسال پذیرفته شد." if lang == "fa" else f"{sent} SMS messages were accepted for delivery.")
        if failed:
            messages.error(request, f"ارسال برای {failed} شماره ناموفق بود؛ جزئیات در سابقه ثبت شد." if lang == "fa" else f"Delivery failed for {failed} numbers; details were recorded in history.")
        return redirect("management_portal:sms_send")
    return render(request, "management_portal/sms_send.html", {
        "form": form, "history": SMSDispatch.objects.select_related("sent_by")[:50], "lang": getattr(request, "LANGUAGE_CODE", "fa"),
    })
