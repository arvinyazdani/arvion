from datetime import datetime, timedelta
import json
from urllib.parse import urlsplit

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from assessments.integrity import (
    DIFFICULTY_LABELS_EN, DIFFICULTY_LABELS_FA, assess_event, assess_pace,
    expected_seconds, format_duration,
)

from accounts.models import User
from assessments.models import Attempt, AttemptResult, Certificate, Exam, ManualPaymentSubmission, Order, SupportTicket
from clinic_orders.models import ClinicOrder
from crm_orders.models import CrmOrder
from crm_orders.text_export import render_crm_order_text
from leads.models import Lead
from clinic_orders.text_export import render_clinic_order_text
from traffic.models import ActiveVisitor, TrafficDay
from contracts.models import ContractProposal
from blog.models import Post
from core.models import Page
from projects.models import Project
from services.models import Service
from accounts.staff_roles import STAFF_ROLES, group_name
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .forms import CaseActivityForm, CaseTaskForm, CustomerCaseForm, CustomerContactForm, CustomerMessageForm, ManualSMSForm, StaffCreateForm, StaffRolesForm
from .backups import find_backup_inventory
from .cases import case_for_customer
from .customer_journey import resolve_customer_journey
from .customer_events import record_customer_event
from assessments.services import PaymentVerificationError, approve_manual_payment
from .models import CaseActivity, CaseTask, Customer, CustomerCase, CustomerContact, CustomerEvent, ManagementNotification, NotificationReceipt, OperationalAudit, PushSubscription, SavedCustomerSegment, SMSCampaign, SMSDispatch, SMSMessageTemplate, StaffAccessAudit, SystemLog
from .sms_audiences import AUDIENCE_LABELS, resolve_sms_audience, sms_audience_overview
from .customer_segments import CASE_STAGE_CHOICES, JOURNEY_CHOICES, apply_customer_filters, normalize_segment_filters
from .customer_analytics import build_customer_funnel


@staff_member_required(login_url="accounts:login")
def customer_workspace(request):
    """One connected list of real customers, not a list of isolated forms."""
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    visible_segments = SavedCustomerSegment.objects.filter(Q(owner=request.user) | Q(is_shared=True)).select_related("owner").distinct()
    selected_segment = None
    segment_id = request.GET.get("segment", "")
    if segment_id.isdigit():
        selected_segment = visible_segments.filter(pk=int(segment_id)).first()
    incoming_filters = selected_segment.filters if selected_segment else request.GET
    filters = normalize_segment_filters(incoming_filters)
    query = filters.get("q", "")
    if request.method == "POST":
        name = request.POST.get("segment_name", "").strip()
        saved_filters = normalize_segment_filters(request.POST)
        if not name or len(name) > 100 or not saved_filters:
            messages.error(request, "نام و حداقل یک فیلتر معتبر لازم است." if lang == "fa" else "A name and at least one valid filter are required.")
        else:
            segment, _created = SavedCustomerSegment.objects.update_or_create(
                owner=request.user, name=name,
                defaults={"filters": saved_filters, "is_shared": request.POST.get("is_shared") == "on" and request.user.is_superuser},
            )
            OperationalAudit.objects.create(actor=request.user, action="customer_segment_saved", target_type="saved_customer_segment", target_id=str(segment.pk), summary=segment.name, metadata={"filters": saved_filters})
            messages.success(request, "فیلتر ذخیره شد." if lang == "fa" else "Filter saved.")
            return redirect(reverse("management_portal:customer_workspace") + f"?segment={segment.pk}")
    customers = Customer.objects.prefetch_related("contacts", "cases__tasks", "cases__activities").order_by("-updated_at")
    customers = apply_customer_filters(customers, filters)
    page = Paginator(customers, 30).get_page(request.GET.get("page"))
    for customer in page.object_list:
        identity_text = " ".join(filter(None, (customer.name, customer.email))).lower()
        customer.identity_warning = (
            "http://" in identity_text or "https://" in identity_text or len(customer.name.strip()) > 80
        )
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
        "customers": page, "page_obj": page, "query": query, "filters": filters, "lang": lang,
        "saved_segments": visible_segments, "selected_segment": selected_segment,
        "journey_choices": JOURNEY_CHOICES, "case_stage_choices": CASE_STAGE_CHOICES,
        "data_quality": data_quality,
        "stats": {
            "customers": Customer.objects.count(),
            "contacts": CustomerContact.objects.count(),
            "active_cases": CustomerCase.objects.exclude(stage__in=("won", "lost")).count(),
            "overdue": CaseTask.objects.filter(status="open", due_at__lt=now).count(),
        },
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_segment_delete(request, segment_id):
    segment = get_object_or_404(SavedCustomerSegment, pk=segment_id)
    if segment.owner_id != request.user.pk and not request.user.is_superuser:
        raise PermissionDenied
    name = segment.name
    segment.delete()
    OperationalAudit.objects.create(actor=request.user, action="customer_segment_deleted", target_type="saved_customer_segment", target_id=str(segment_id), summary=name)
    messages.success(request, "فیلتر ذخیره‌شده حذف شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "Saved filter deleted.")
    return redirect("management_portal:customer_workspace")


@staff_member_required(login_url="accounts:login")
def customer_reports(request):
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    return render(request, "management_portal/v2/customer_reports.html", {
        "lang": lang, "report": build_customer_funnel(),
    })


@staff_member_required(login_url="accounts:login")
def customer_account_open(request, user_id):
    """Resolve a registered account into its canonical customer record on demand."""
    account = get_object_or_404(User, pk=user_id, is_staff=False)
    contact = CustomerContact.objects.filter(user=account).select_related("customer").first()
    if contact:
        return redirect("management_portal:customer_detail", customer_id=contact.customer_id)
    customer = Customer.objects.filter(email__iexact=account.email).first()
    if not customer and account.mobile:
        customer = Customer.objects.filter(phone=account.mobile).first()
    if not customer:
        customer = Customer.objects.create(
            name=account.get_full_name() or account.email or account.mobile or f"کاربر {account.pk}",
            kind="person", phone=account.mobile or "", email=account.email,
        )
    CustomerContact.objects.create(
        customer=customer, user=account, name=account.get_full_name() or account.email or account.mobile,
        phone=account.mobile or "", email=account.email, is_primary=not customer.contacts.exists(),
    )
    Order.objects.filter(user=account, customer__isnull=True).update(customer=customer)
    record_customer_event(
        customer=customer, category="identity", event_type="account_created",
        title_fa="عضویت در سایت", title_en="Website account created",
        description=account.email or account.mobile, source=account,
        occurred_at=account.date_joined,
    )
    OperationalAudit.objects.create(actor=request.user, action="customer_account_linked", target_type="customer", target_id=str(customer.pk), summary=account.email or account.mobile)
    return redirect("management_portal:customer_detail", customer_id=customer.pk)


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
        rows = Customer.objects.exclude(**{candidate_field: ""}).values(candidate_field).annotate(total=Count("pk")).filter(total__gt=1).order_by("-total", candidate_field)[:100]
        groups.extend({"field": candidate_field, "value": row[candidate_field], "total": row["total"]} for row in rows)
    compared_customers = Customer.objects.none()
    if field and value:
        compared_customers = Customer.objects.filter(**{field: value}).prefetch_related("contacts", "cases", "contracts", "assessment_orders").order_by("name")
    return render(request, "management_portal/v2/customer_duplicates.html", {"lang": lang, "groups": groups, "field": field, "value": value, "compared_customers": compared_customers})


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_merge(request, source_id):
    """Merge only records proven equal by an exact phone number or email match."""
    if not request.user.is_superuser:
        raise PermissionDenied
    target_id = request.POST.get("target_id", "")
    if request.POST.get("confirmation") != "MERGE" or not target_id.isdigit() or int(target_id) == source_id:
        messages.error(request, "برای ادغام، عبارت MERGE و مشتری مقصد معتبر لازم است." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "A valid target and the word MERGE are required.")
        return redirect("management_portal:customer_duplicates")
    with transaction.atomic():
        source = get_object_or_404(Customer.objects.select_for_update(), pk=source_id)
        target = get_object_or_404(Customer.objects.select_for_update(), pk=int(target_id))
        shared_phone = bool(source.phone and source.phone == target.phone)
        shared_email = bool(source.email and source.email.lower() == target.email.lower())
        if not (shared_phone or shared_email):
            raise PermissionDenied
        moved_case_ids = list(source.cases.values_list("pk", flat=True))
        moved_contacts = moved_contracts = moved_orders = 0
        for contact in source.contacts.all():
            duplicate = CustomerContact.objects.filter(customer=target, name=contact.name, phone=contact.phone, email=contact.email).first()
            if duplicate:
                if contact.user_id and not duplicate.user_id:
                    duplicate.user = contact.user
                    duplicate.save(update_fields=("user", "updated_at"))
                contact.delete()
            else:
                contact.customer = target
                contact.save(update_fields=("customer", "updated_at"))
                moved_contacts += 1
        moved_cases = CustomerCase.objects.filter(pk__in=moved_case_ids).update(customer=target)
        moved_contracts = ContractProposal.objects.filter(customer=source).update(customer=target)
        moved_orders = Order.objects.filter(customer=source).update(customer=target)
        source_name = source.name
        source.delete()
        for case_id in moved_case_ids:
            CaseActivity.objects.create(case_id=case_id, actor=request.user, kind="system", title="پرونده مشتری ادغام شد", body=f"پرونده «{source_name}» در «{target.name}» ادغام شد.")
        OperationalAudit.objects.create(actor=request.user, action="customer_merged", target_type="customer", target_id=str(target.pk), summary=f"{source_name} → {target.name}", metadata={"source_customer_id": source_id, "target_customer_id": target.pk, "shared_by": "phone" if shared_phone else "email", "contacts": moved_contacts, "cases": moved_cases, "contracts": moved_contracts, "orders": moved_orders})
    messages.success(request, "ادغام با موفقیت ثبت شد و سابقه آن نگه‌داری می‌شود." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "The merge was completed and recorded in the audit log.")
    return redirect("management_portal:customer_detail", customer_id=target.pk)


@staff_member_required(login_url="accounts:login")
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer.objects.prefetch_related("contacts__user", "cases__owner", "cases__tasks", "cases__documents", "cases__activities__actor"), pk=customer_id)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    contracts = list(customer.contracts.select_related("created_by").order_by("-updated_at")[:10])
    orders = list(customer.assessment_orders.select_related("exam", "user", "manual_payment").order_by("-created_at")[:20])
    user_ids = set(customer.contacts.exclude(user__isnull=True).values_list("user_id", flat=True))
    user_ids.update(order.user_id for order in orders)
    attempts = list(
        Attempt.objects.filter(user_id__in=user_ids)
        .select_related("user", "exam", "entitlement__order", "result")
        .prefetch_related("result__skill_results__skill", "integrity_events")
        .order_by("-created_at")[:30]
    )
    tickets = SupportTicket.objects.filter(Q(order__customer=customer) | Q(user__customer_contact_profiles__customer=customer)).select_related("order__exam", "user").distinct().order_by("-updated_at")[:10]
    attempt_urls = {str(attempt.pk): reverse("management_portal:customer_assessment_detail", args=[customer.pk, attempt.user_id]) + f"#attempt-{attempt.pk}" for attempt in attempts}
    timeline = []
    for event in CustomerEvent.objects.filter(customer=customer).select_related("case", "actor")[:100]:
        url = ""
        if event.category == "payment":
            url = reverse("management_portal:approvals")
        elif event.source_type == "assessments.attempt":
            url = attempt_urls.get(event.source_id, "")
        elif event.category == "contract" and event.source_type == "contracts.contractproposal":
            url = reverse("management_portal:contract_detail", args=[event.source_id])
        timeline.append({
            "at": event.occurred_at, "kind": event.category,
            "title": event.title_fa if lang == "fa" else event.title_en,
            "detail": event.description, "url": url,
            "meta": event.case.code if event.case_id else "",
        })

    can_message = request.user.is_superuser or request.user.has_perm("management_portal.add_smsdispatch")
    can_change_case = request.user.is_superuser or request.user.has_perm("management_portal.change_customercase") or request.user.has_perm("crm_orders.change_crmorder") or request.user.has_perm("leads.change_lead") or request.user.has_perm("clinic_orders.change_clinicorder")
    journey = resolve_customer_journey(
        customer=customer,
        orders=orders,
        attempts=attempts,
        contracts=contracts,
        can_message=can_message,
        can_change_case=can_change_case,
    )
    initial_phone = customer.phone or next((contact.phone for contact in customer.contacts.all() if contact.phone), "")
    return render(request, "management_portal/v2/customer_detail.html", {
        "customer": customer,
        "contact_form": CustomerContactForm(lang=lang),
        "message_form": CustomerMessageForm(lang=lang, initial={"recipient": initial_phone}),
        "task_form": CaseTaskForm(lang=lang),
        "activity_form": CaseActivityForm(lang=lang),
        "can_message": can_message,
        "can_change_case": can_change_case,
        "events": timeline[:80], "contracts": contracts, "orders": orders,
        "attempts": attempts, "tickets": tickets, "journey": journey, "lang": lang,
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_task_create(request, customer_id):
    _require_case_change(request.user)
    customer = get_object_or_404(Customer, pk=customer_id)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = CaseTaskForm(request.POST, lang=lang)
    if not form.is_valid():
        messages.error(request, "اطلاعات پیگیری کامل یا معتبر نیست." if lang == "fa" else "Follow-up details are incomplete or invalid.")
        return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")
    with transaction.atomic():
        case = case_for_customer(customer)
        task = form.save(commit=False)
        task.case = case
        task.created_by = request.user
        task.save()
        CaseActivity.objects.create(case=case, actor=request.user, kind="task", title="پیگیری جدید ساخته شد", body=task.title, metadata={"task_id": task.pk})
        OperationalAudit.objects.create(actor=request.user, action="customer_followup_created", target_type="customer", target_id=str(customer.pk), summary=task.title, metadata={"case_id": case.pk, "task_id": task.pk})
    messages.success(request, "پیگیری ساخته شد و در پرونده مشتری ثبت شد." if lang == "fa" else "The follow-up was created and added to the customer record.")
    return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_activity_create(request, customer_id):
    _require_case_change(request.user)
    customer = get_object_or_404(Customer, pk=customer_id)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = CaseActivityForm(request.POST, lang=lang)
    if not form.is_valid():
        messages.error(request, "نوع و عنوان فعالیت را بررسی کنید." if lang == "fa" else "Review the activity type and title.")
        return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")
    with transaction.atomic():
        case = case_for_customer(customer)
        activity = form.save(commit=False)
        activity.case = case
        activity.actor = request.user
        activity.save()
        OperationalAudit.objects.create(actor=request.user, action="customer_activity_logged", target_type="customer", target_id=str(customer.pk), summary=activity.title, metadata={"case_id": case.pk, "activity_id": activity.pk, "kind": activity.kind})
    messages.success(request, "فعالیت در خط زمانی مشتری ثبت شد." if lang == "fa" else "The activity was added to the customer timeline.")
    return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")


def _customer_mobile_numbers(customer):
    from core.sms.backends import normalize_iran_mobile
    values = [customer.phone, *customer.contacts.exclude(phone="").values_list("phone", flat=True)]
    numbers = set()
    for value in values:
        try:
            numbers.add(normalize_iran_mobile(value))
        except ValueError:
            continue
    return numbers


@staff_member_required(login_url="accounts:login")
def customer_assessment_detail(request, customer_id, user_id):
    customer = get_object_or_404(Customer.objects.prefetch_related("contacts"), pk=customer_id)
    linked_user_ids = set(customer.contacts.exclude(user__isnull=True).values_list("user_id", flat=True))
    linked_user_ids.update(customer.assessment_orders.values_list("user_id", flat=True))
    if user_id not in linked_user_ids:
        raise Http404
    account = get_object_or_404(User, pk=user_id)
    attempts = list(
        Attempt.objects.filter(user=account)
        .select_related("exam", "entitlement__order", "result")
        .prefetch_related(
            "result__skill_results__skill",
            "integrity_events__attempt_question",
            "attempt_questions__integrity_events",
        )
        .order_by("-created_at")
    )
    integrity_labels = {
        "visibility_hidden": ("خروج از صفحه ثبت شد", "Page exit recorded"),
        "visibility_returned": ("بازگشت به آزمون", "Returned to assessment"),
        "tab_hidden": ("رویداد قدیمی غیرقابل اتکا", "Legacy unreliable event"),
        "window_blur": ("رویداد قدیمی غیرقابل اتکا", "Legacy unreliable event"),
        "copy": ("فرمان کپی در صفحه سؤال ثبت شد", "Copy command recorded on the question page"),
        "paste": ("فرمان جای‌گذاری در صفحه سؤال ثبت شد", "Paste command recorded on the question page"),
        "other": ("رویداد نیازمند بررسی", "Event requiring review"),
    }
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    attempt_status_labels = {
        "ready": ("آماده", "Ready"), "in_progress": ("در حال انجام", "In progress"),
        "submitted": ("ارسال‌شده", "Submitted"), "expired": ("منقضی‌شده", "Expired"),
        "scoring": ("در حال ارزیابی", "Scoring"), "completed": ("تکمیل‌شده", "Completed"),
        "invalidated": ("باطل‌شده", "Invalidated"),
    }
    for attempt in attempts:
        status_pair = attempt_status_labels.get(attempt.status, (attempt.status, attempt.status))
        attempt.management_status = status_pair[0 if lang == "fa" else 1]
        # Each row states the time taken alongside the difficulty and the time
        # the question was authored to take, so a reviewer can judge the pace.
        attempt.management_questions = list(attempt.attempt_questions.all())
        for item in attempt.management_questions:
            snapshot = item.question_snapshot or {}
            difficulty = snapshot.get("difficulty", 3)
            suggested = snapshot.get("suggested_seconds", 60)
            answered = item.effective_selected_choice_id is not None
            selected_id = item.effective_selected_choice_id
            selected = next(
                (choice for choice in item.choices_snapshot if choice.get("id") == selected_id),
                None,
            )
            pace = assess_pace(
                item.active_seconds, suggested, difficulty,
                answered=answered, is_correct=bool(selected and selected.get("is_correct")),
            )
            labels = DIFFICULTY_LABELS_FA if lang == "fa" else DIFFICULTY_LABELS_EN
            item.pace_difficulty = labels.get(int(difficulty or 3), "")
            item.pace_expected_seconds = expected_seconds(suggested, difficulty)
            item.pace_verdict = pace.verdict
            item.pace_severity = pace.severity
            item.pace_reason = pace.reason_fa if lang == "fa" else pace.reason_en
        latest_event = None
        for event in attempt.integrity_events.all():
            labels = integrity_labels.get(event.event_type, integrity_labels["other"])
            event.management_label = labels[0 if lang == "fa" else 1]
            assessment = assess_event(event.event_type, event.duration_ms)
            event.management_reason = assessment.reason_fa if lang == "fa" else assessment.reason_en
            event.management_severity = assessment.severity
            event.management_duration = format_duration(event.duration_ms, lang) if event.event_type == "visibility_returned" else ""
            latest_event = event
        attempt.has_open_absence = bool(latest_event and latest_event.event_type == "visibility_hidden")
    orders = customer.assessment_orders.filter(user=account).select_related("exam", "manual_payment").order_by("-created_at")
    return render(request, "management_portal/v2/customer_assessment_detail.html", {"customer": customer, "account": account, "attempts": attempts, "orders": orders, "lang": lang})


@staff_member_required(login_url="accounts:login")
@require_POST
def customer_message_send(request, customer_id):
    if not (request.user.is_superuser or request.user.has_perm("management_portal.add_smsdispatch")):
        raise PermissionDenied
    customer = get_object_or_404(Customer, pk=customer_id)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    form = CustomerMessageForm(request.POST, lang=lang)
    if not form.is_valid():
        messages.error(request, "شماره یا متن پیام معتبر نیست." if lang == "fa" else "The number or message is invalid.")
        return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-message")
    recipient = form.cleaned_data["recipient"]
    if recipient not in _customer_mobile_numbers(customer):
        raise PermissionDenied
    try:
        result = send_sms(recipient, form.cleaned_data["message"])
    except (SMSDeliveryError, ImproperlyConfigured, ValueError) as exc:
        SMSDispatch.objects.create(recipient=recipient, message=form.cleaned_data["message"], status="failed", error_message=str(exc)[:240], sent_by=request.user)
        messages.error(request, "ارسال پیام ناموفق بود؛ خطا برای پیگیری ثبت شد." if lang == "fa" else "Message delivery failed; the error was recorded.")
    else:
        SMSDispatch.objects.create(recipient=recipient, message=form.cleaned_data["message"], status="sent", provider=result.provider, provider_reference=result.reference, sent_by=request.user)
        OperationalAudit.objects.create(actor=request.user, action="customer_sms_sent", target_type="customer", target_id=str(customer.pk), summary=recipient, metadata={"message_length": len(form.cleaned_data["message"])})
        latest_case = customer.cases.order_by("-updated_at").first()
        if latest_case:
            CaseActivity.objects.create(case=latest_case, actor=request.user, kind="message", title="پیام پیگیری ارسال شد", body=form.cleaned_data["message"])
        messages.success(request, "پیام برای ارسال پذیرفته شد." if lang == "fa" else "The message was accepted for delivery.")
    return redirect(reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-message")


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
    now = timezone.now(); page = Paginator(cases, 30).get_page(request.GET.get("page")); inventory = find_backup_inventory(getattr(settings, "CRM_BACKUP_DIR", "/srv/arvion/backups")); latest_backup = inventory.preferred
    recent_backups = sorted(
        (*inventory.daily[:5], *inventory.pre_release[:3]),
        key=lambda backup: backup.modified_timestamp,
        reverse=True,
    )
    backup_status = {
        "available": bool(latest_backup),
        "name": latest_backup.name if latest_backup else "",
        "source": latest_backup.source if latest_backup else "",
        "size_mb": round(latest_backup.size_bytes / 1048576, 2) if latest_backup else 0,
        "modified_at": datetime.fromtimestamp(latest_backup.modified_timestamp, tz=timezone.get_current_timezone()) if latest_backup else None,
        "history": [
            {
                "name": backup.name,
                "source": backup.source,
                "size_mb": round(backup.size_bytes / 1048576, 2),
                "modified_at": datetime.fromtimestamp(backup.modified_timestamp, tz=timezone.get_current_timezone()),
            }
            for backup in recent_backups
        ],
    }
    backup_status["healthy"] = bool(backup_status["modified_at"] and backup_status["modified_at"] >= now - timedelta(hours=settings.OPERATIONS_BACKUP_MAX_AGE_HOURS))
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
    report = "\n".join(lines)
    filename = f"{case.code}.txt"
    if request.GET.get("download") == "1":
        OperationalAudit.objects.create(actor=request.user, action="crm_case_exported", target_type="customer_case", target_id=str(case.pk), summary=case.customer_name)
        response = HttpResponse(report, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    return render(request, "management_portal/v2/text_export_preview.html", {
        "lang": lang,
        "export_title": f"خروجی پرونده {case.code}" if lang == "fa" else f"Case export {case.code}",
        "export_description": "متن زیر قبل از ذخیره یا اشتراک‌گذاری قابل بازبینی است." if lang == "fa" else "Review the text before saving or sharing it.",
        "report": report,
        "filename": filename,
        "download_url": f"{request.path}?download=1",
        "back_url": reverse("management_portal:crm_case_detail", args=[case.pk]),
    })


def _metric(label, value, description, url="", tone=""):
    return {"label": label, "value": value, "description": description, "url": url, "tone": tone}


@staff_member_required(login_url="accounts:login")
def dashboard(request):
    """Permission-aware command centre outside Django's model administration UI."""
    user = request.user
    now = timezone.now()
    metrics = []
    sla_cards = []
    queues = []
    if user.has_perm("accounts.change_user"):
        # Unverified mobiles are normal since signup dropped the SMS step, so
        # only genuinely deactivated accounts belong in the approval queue.
        pending_users = User.objects.filter(is_staff=False, is_active=False).order_by("-date_joined")
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
        payments = ManualPaymentSubmission.objects.filter(status="pending").select_related("order__user").order_by("-updated_at")
        metrics.append(_metric("پرداخت منتظر بررسی", payments.count(), "تأیید بانکی و دسترسی آزمون", reverse("management_portal:approvals"), "danger"))
        queues += [{"kind": "پرداخت", "title": item.payer_name, "meta": item.reference_number, "date": item.created_at, "url": reverse("management_portal:approvals")} for item in payments[:4]]
        overdue_payments = payments.filter(updated_at__lte=now - timedelta(seconds=settings.PAYMENT_AUTO_APPROVE_SECONDS)).count()
        sla_cards.append(_metric("تأیید خودکار معطل", overdue_payments, "بیش از ۳ دقیقه در انتظار مانده", reverse("management_portal:approvals"), "danger"))
    if user.has_perm("assessments.view_supportticket"):
        metrics.append(_metric("تیکت باز", SupportTicket.objects.filter(status__in=("open", "in_review")).count(), "نیازمند پاسخ یا پیگیری", reverse("management_portal:assessment_support")))
        overdue_tickets = SupportTicket.objects.filter(status="open", created_at__lte=now - timedelta(seconds=settings.SUPPORT_FIRST_RESPONSE_SLA_SECONDS)).count()
        sla_cards.append(_metric("تیکت خارج از مهلت", overdue_tickets, "پاسخ اولیه بیش از ۴ ساعت عقب افتاده", reverse("management_portal:assessment_support"), "warning"))
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
    unread_notifications = notifications.filter(
        status="unread",
        receipts__user=user,
        receipts__seen_at__isnull=True,
    )
    unread_count = unread_notifications.count()
    # The management context processor runs during template rendering. Reuse
    # this value there instead of issuing the same count query again.
    request._management_unread_count = unread_count
    if user.is_superuser or user.has_perm("leads.view_lead") or user.has_perm("crm_orders.view_crmorder") or user.has_perm("clinic_orders.view_clinicorder"):
        sales_cutoff = now - timedelta(seconds=settings.SALES_FOLLOW_UP_SLA_SECONDS)
        overdue_sales = 0
        if user.is_superuser or user.has_perm("leads.view_lead"):
            overdue_sales += Lead.objects.filter(status="new", created_at__lte=sales_cutoff).count()
        if user.is_superuser or user.has_perm("crm_orders.view_crmorder"):
            overdue_sales += CrmOrder.objects.filter(status="new", created_at__lte=sales_cutoff).count()
        if user.is_superuser or user.has_perm("clinic_orders.view_clinicorder"):
            overdue_sales += ClinicOrder.objects.filter(status="new", created_at__lte=sales_cutoff).count()
        if user.is_superuser:
            overdue_sales += ContractProposal.objects.filter(status__in=("sent", "review"), created_at__lte=sales_cutoff).count()
        sla_cards.append(_metric("پیگیری فروش سررسیدشده", overdue_sales, "فرم یا قرارداد بیش از یک روز بدون پیگیری", reverse("management_portal:notification_list"), "warning"))
        overdue_tasks = CaseTask.objects.filter(status="open", due_at__lt=now).count()
        sla_cards.append(_metric("وظیفه CRM عقب‌افتاده", overdue_tasks, "موعد پیگیری مشتری گذشته است", reverse("management_portal:crm_workspace"), "danger"))
    metrics.insert(0, _metric("اعلان خوانده‌نشده", unread_count, "رویدادهای تازه مرتبط با مسئولیت شما", reverse("management_portal:notification_list"), "warning"))
    if user.is_superuser:
        metrics.insert(1, _metric("قراردادها", ContractProposal.objects.exclude(status__in=("expired", "revoked")).count(), "ساخت، ارسال و پیگیری پذیرش", reverse("management_portal:workspace_list"), "positive"))
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
        sla_labels = {
            "پرداخت خارج از مهلت": ("Overdue payment reviews", "Waiting beyond the 30-minute review target"),
            "تیکت خارج از مهلت": ("Overdue support tickets", "Initial response is beyond the four-hour target"),
            "پیگیری فروش سررسیدشده": ("Overdue sales follow-ups", "A form or contract has waited more than one day"),
            "وظیفه CRM عقب‌افتاده": ("Overdue CRM tasks", "A customer follow-up date has passed"),
        }
        kinds = {"حساب": "Account", "همکاری": "Enquiry", "کلینیک": "Clinic", "پرداخت": "Payment"}
        for item in metrics:
            if item["label"] in labels:
                item["label"], item["description"] = labels[item["label"]]
        for item in sla_cards:
            if item["label"] in sla_labels:
                item["label"], item["description"] = sla_labels[item["label"]]
        for item in queues:
            item["kind"] = kinds.get(item["kind"], item["kind"])
            if item["meta"] == "منتظر فعال‌سازی":
                item["meta"] = "Awaiting verification"
    recent_customers = Customer.objects.prefetch_related("contacts", "cases").order_by("-updated_at")[:8]
    registered_without_order = User.objects.filter(is_staff=False, is_active=True, assessment_orders__isnull=True, mobile__isnull=False).exclude(mobile="").order_by("-date_joined")[:6]
    pending_orders = Order.objects.filter(status="pending").select_related("user", "exam", "customer").order_by("-created_at")[:6]
    paid_not_started = Order.objects.filter(status="paid", entitlement__attempt__isnull=True).select_related("user", "exam", "customer").order_by("-paid_at", "-updated_at")[:6]
    completed_attempts = Attempt.objects.filter(status="completed").select_related("user", "exam", "entitlement__order__customer", "result").order_by("-submitted_at", "-updated_at")[:6]
    open_tasks = CaseTask.objects.filter(status="open").select_related("case__customer", "assigned_to").order_by("due_at", "-created_at")[:8]
    inbox_items = unread_notifications.select_related("owner").order_by("-created_at")[:6]
    return render(request, "management_portal/v2/dashboard.html", {
        "metrics": metrics, "queues": queues[:12], "chart": chart, "online": online, "lang": lang,
        "unread_count": unread_count,
        "sla_cards": sla_cards,
        "recent_customers": recent_customers, "open_tasks": open_tasks, "inbox_items": inbox_items,
        "journey_queues": {
            "registered": registered_without_order,
            "pending": pending_orders,
            "ready": paid_not_started,
            "completed": completed_attempts,
        },
        "document_counts": {"discoveries": CrmOrder.objects.count() + ClinicOrder.objects.count(), "contracts": ContractProposal.objects.count() if user.is_superuser else 0},
    })


def _require_sales_access(user):
    if not user.is_superuser and not (user.has_perm("leads.view_lead") or user.has_perm("crm_orders.view_crmorder") or user.has_perm("clinic_orders.view_clinicorder")):
        raise PermissionDenied


def _require_case_change(user):
    if not user.is_superuser and not (user.has_perm("management_portal.change_customercase") or user.has_perm("leads.change_lead") or user.has_perm("crm_orders.change_crmorder") or user.has_perm("clinic_orders.change_clinicorder")):
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
        full_report = "\n".join(("گزارش کامل درخواست همکاری آرویون", "=" * 38, f"کد پیگیری: {item.tracking_code}", f"نام: {item.name}", f"مجموعه: {item.business_name or '—'}", f"شماره تماس: {item.phone or '—'}", f"ایمیل / تلگرام: {item.email_or_telegram}", f"نوع درخواست: {item.get_request_type_display()}", f"بودجه: {item.get_budget_range_display()}", f"زمان‌بندی: {item.get_timeline_display()}", f"روش تماس: {item.get_preferred_contact_display()}", "", "شرح درخواست", "-" * 20, item.message))
    elif kind == "crm":
        title, contact, phone, email, code, summary = item.organization_name, item.contact_name, item.phone, item.work_email, item.tracking_code, item.main_pain_points
        full_report = render_crm_order_text(item)
    else:
        title, contact, phone, email, code, summary = item.clinic_name, item.contact_name, item.phone, item.work_email, item.tracking_code, item.main_pain_points
        full_report = render_clinic_order_text(item)
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    status_choices = list(model.STATUSES)
    if lang == "en":
        status_en = {
            "new": "New", "contacted": "Contacted", "discovery": "Discovery",
            "qualified": "Qualified", "proposal": "Proposal sent", "won": "Won",
            "lost": "Closed",
        }
        status_choices = [(value, status_en.get(value, str(label))) for value, label in status_choices]
    elif kind == "lead":
        status_fa = {
            "new": "جدید", "contacted": "تماس گرفته‌شده", "qualified": "واجد شرایط",
            "proposal": "پیشنهاد ارسال‌شده", "won": "موفق", "lost": "بسته‌شده",
        }
        status_choices = [(value, status_fa.get(value, str(label))) for value, label in status_choices]
    status_display = dict(status_choices).get(item.status, item.status)
    customer_case = CustomerCase.objects.filter(
        source_content_type=ContentType.objects.get_for_model(item),
        source_object_id=item.pk,
    ).first()
    return render(request, "management_portal/v2/request_detail.html", {
        "item": item, "kind": kind, "title": title, "contact": contact, "phone": phone,
        "email": email, "code": code, "summary": summary, "full_report": full_report, "lang": lang, "status_choices": status_choices, "status_display": status_display,
        "can_change": request.user.is_superuser or request.user.has_perm({"lead": "leads.change_lead", "crm": "crm_orders.change_crmorder", "clinic": "clinic_orders.change_clinicorder"}[kind]),
        "customer_case": customer_case,
    })


@staff_member_required(login_url="accounts:login")
def request_export(request, kind, object_id):
    _require_sales_access(request.user)
    models = {"lead": Lead, "crm": CrmOrder, "clinic": ClinicOrder}
    model = models.get(kind)
    if not model:
        raise Http404
    permission = {"lead": "leads.view_lead", "crm": "crm_orders.view_crmorder", "clinic": "clinic_orders.view_clinicorder"}[kind]
    if not request.user.is_superuser and not request.user.has_perm(permission):
        raise PermissionDenied
    item = get_object_or_404(model, pk=object_id)
    if kind == "crm": report = render_crm_order_text(item)
    elif kind == "clinic": report = render_clinic_order_text(item)
    else: report = "\n".join(("گزارش درخواست همکاری آرویون", f"کد پیگیری: {item.tracking_code}", f"نام: {item.name}", f"مجموعه: {item.business_name or '—'}", f"تماس: {item.phone or item.email_or_telegram}", "", item.message)) + "\n"
    filename = f"rvion-{kind}-{item.pk}.txt"
    if request.GET.get("download") == "1":
        OperationalAudit.objects.create(actor=request.user, action="request_exported", target_type=kind, target_id=str(item.pk), summary=getattr(item, "tracking_code", str(item.pk)))
        response = HttpResponse(report, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    titles = {
        "lead": ("خروجی کامل درخواست همکاری", "Enquiry export"),
        "crm": ("خروجی کامل نیازسنجی CRM", "CRM discovery export"),
        "clinic": ("خروجی کامل نیازسنجی کلینیک", "Clinic discovery export"),
    }
    return render(request, "management_portal/v2/text_export_preview.html", {
        "lang": lang,
        "export_title": titles[kind][0 if lang == "fa" else 1],
        "export_description": "متن زیر قبل از ذخیره یا اشتراک‌گذاری قابل بازبینی است." if lang == "fa" else "Review the text before saving or sharing it.",
        "report": report,
        "filename": filename,
        "download_url": f"{request.path}?download=1",
        "back_url": reverse("management_portal:request_detail", args=[kind, item.pk]),
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
    users = User.objects.filter(
        is_staff=False, is_active=False,
    ).order_by("-date_joined")[:100] if request.user.is_superuser or request.user.has_perm("accounts.change_user") else []
    payments = list(ManualPaymentSubmission.objects.select_related("order__user", "order__customer", "order__exam", "reviewed_by").order_by("-created_at")[:100]) if request.user.is_superuser or request.user.has_perm("assessments.view_manualpaymentsubmission") else []
    now = timezone.now()
    for payment in payments:
        payment.auto_approve_seconds = max(
            0,
            int((payment.updated_at + timedelta(seconds=settings.PAYMENT_AUTO_APPROVE_SECONDS) - now).total_seconds()),
        )
    return render(request, "management_portal/v2/approvals.html", {"pending_users": users, "payments": payments, "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def account_approval(request, user_id, decision):
    if not request.user.is_superuser and not request.user.has_perm("accounts.change_user"):
        raise PermissionDenied
    if decision not in {"approve", "reject", "verify_mobile"}:
        raise Http404
    customer = get_object_or_404(User.objects.select_for_update(), pk=user_id, is_staff=False)
    if decision == "verify_mobile":
        if not customer.is_active or customer.mobile_verified_at is not None:
            messages.error(request, "این حساب در وضعیت تأیید تلفنی نیست.")
            return redirect("management_portal:approvals")
        customer.mobile_verified_at = timezone.now()
        customer.email_verified = True
        customer.save(update_fields=["mobile_verified_at", "email_verified"])
        ManagementNotification.objects.filter(
            source_key=f"mobile-verification:{customer.pk}", status__in=("unread", "read"),
        ).update(status="resolved", resolved_by=request.user, resolved_at=timezone.now())
        summary = f"شماره موبایل {customer.email} به‌صورت تلفنی تأیید شد"
    elif decision == "approve":
        if customer.mobile_verified_at is None:
            customer.mobile_verified_at = timezone.now()
        customer.is_active = True
        customer.email_verified = True
        customer.save(update_fields=["is_active", "email_verified", "mobile_verified_at"])
        ManagementNotification.objects.filter(
            Q(source_key=f"user:{customer.pk}") | Q(source_key=f"mobile-verification:{customer.pk}"),
            status__in=("unread", "read"),
        ).update(status="resolved", resolved_by=request.user, resolved_at=timezone.now())
        summary = f"حساب {customer.email} با تأیید مدیر فعال شد"
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
            payment, order, created, applied = approve_manual_payment(
                payment.pk, reviewer=request.user, review_note=note, automatic=False,
            )
        except PaymentVerificationError as exc:
            messages.error(request, str(exc))
            return redirect("management_portal:approvals")
        if not applied:
            messages.warning(request, "این رسید هم‌زمان توسط سیستم یا مدیر دیگری بررسی شد.")
            return redirect("management_portal:approvals")
        if created:
            send_mail("پرداخت شما تأیید شد", f"پرداخت سفارش {order.pk} تأیید شد و دسترسی آزمون فعال است.\n{settings.SITE_URL}/fa/account/", settings.DEFAULT_FROM_EMAIL, [order.user.email], fail_silently=True)
    else:
        payment.status = "rejected"
        payment.reviewed_by, payment.reviewed_at, payment.review_note = request.user, timezone.now(), note
        payment.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
    ManagementNotification.objects.filter(
        Q(source_key=f"payment:{payment.pk}")
        | Q(source_key__startswith=f"payment:{payment.pk}:resubmitted:")
        | Q(source_key=f"sla:payment:{payment.pk}"),
        status__in=("unread", "read"),
    ).update(
        status="resolved",
        resolved_by=request.user,
        resolved_at=timezone.now(),
    )
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


@staff_member_required(login_url="accounts:login")
def system_log(request):
    _require_superuser(request)
    level = request.GET.get("level", "")
    category = request.GET.get("category", "")
    logs = SystemLog.objects.select_related("user")
    if level in dict(SystemLog.LEVELS):
        logs = logs.filter(level=level)
    if category in dict(SystemLog.CATEGORIES):
        logs = logs.filter(category=category)
    return render(request, "management_portal/v2/system_log.html", {
        "logs": logs[:200], "level": level, "category": category,
        "levels": SystemLog.LEVELS, "categories": SystemLog.CATEGORIES,
        "lang": getattr(request, "LANGUAGE_CODE", "fa"),
    })


def _visible_notifications(user):
    queryset = ManagementNotification.objects.all()
    if user.is_superuser:
        return queryset
    roles = [name.removeprefix("rvion_") for name in user.groups.values_list("name", flat=True) if name.startswith("rvion_")]
    return queryset.filter(Q(role__in=roles) | Q(owner=user)).distinct()


def _safe_notification_redirect(request, candidate):
    fallback = reverse("management_portal:notification_list")
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


def _notification_json_requested(request):
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _notification_unread_count(user):
    return user.notification_receipts.filter(
        seen_at__isnull=True,
        notification__status="unread",
    ).count()


def _notification_action_payload(request, notification, message, action):
    owner_label = ""
    if notification.owner:
        owner_label = notification.owner.get_full_name() or notification.owner.email
    fa = getattr(request, "LANGUAGE_CODE", "fa") == "fa"
    status_labels = {
        "unread": ("خوانده‌نشده", "Unread"),
        "read": ("خوانده‌شده", "Read"),
        "resolved": ("مختومه", "Resolved"),
    }
    return {
        "ok": True,
        "id": notification.pk,
        "action": action,
        "status": notification.status,
        "display_status": status_labels[notification.status][0 if fa else 1],
        "owner": owner_label,
        "unread_count": _notification_unread_count(request.user),
        "message": message,
    }


@staff_member_required(login_url="accounts:login")
def notification_list(request):
    status, category = request.GET.get("status", ""), request.GET.get("category", "")
    priority = request.GET.get("priority", "")
    queryset = _visible_notifications(request.user).select_related("owner")
    if status in dict(ManagementNotification.STATUSES):
        queryset = queryset.filter(status=status)
    if category in dict(ManagementNotification.CATEGORIES):
        queryset = queryset.filter(category=category)
    if priority in dict(ManagementNotification.PRIORITIES):
        queryset = queryset.filter(priority=priority)
    now = timezone.now()
    active = queryset.exclude(status="resolved").filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now)
    )
    priority_order = Case(
        *[When(priority=value, then=Value(rank)) for value, rank in ManagementNotification.PRIORITY_ORDER.items()],
        default=Value(2), output_field=IntegerField(),
    )
    active = active.annotate(priority_rank_db=priority_order).order_by("priority_rank_db", "due_at", "-created_at")
    overdue = active.filter(due_at__lt=now)
    upcoming = active.exclude(pk__in=overdue.values("pk"))
    snoozed = queryset.exclude(status="resolved").filter(snoozed_until__gt=now).order_by("snoozed_until")
    can_review_payments = request.user.is_superuser or request.user.has_perm("assessments.change_manualpaymentsubmission")
    groups = [
        list(overdue[:40]), list(upcoming[:40]), list(snoozed[:20]),
        list(queryset.filter(status="resolved")[:20]),
    ]
    fa = getattr(request, "LANGUAGE_CODE", "fa") == "fa"
    localized = {
        "status": {
            "unread": ("خوانده‌نشده", "Unread"), "read": ("خوانده‌شده", "Read"),
            "resolved": ("مختومه", "Resolved"),
        },
        "category": {
            "accounts": ("حساب‌ها", "Accounts"), "sales": ("فروش و سفارش", "Sales & orders"),
            "payments": ("پرداخت", "Payments"), "support": ("پشتیبانی", "Support"),
            "contracts": ("قرارداد", "Contracts"),
        },
        "priority": {
            "critical": ("بحرانی", "Critical"), "high": ("زیاد", "High"),
            "normal": ("معمولی", "Normal"), "low": ("کم", "Low"),
        },
    }
    for group in groups:
        for item in group:
            item.display_status = localized["status"][item.status][0 if fa else 1]
            item.display_category = localized["category"][item.category][0 if fa else 1]
            item.display_priority = localized["priority"][item.priority][0 if fa else 1]
            parts = item.source_key.split(":")
            item.can_review_payment = (
                item.category == "payments" and len(parts) >= 2
                and parts[0] == "payment" and parts[1].isdigit()
            )
    roles = {item.role for group in groups for item in group}
    eligible_by_role = {}
    for role in roles:
        candidates = User.objects.filter(is_staff=True, is_active=True).exclude(pk=request.user.pk)
        if role:
            candidates = candidates.filter(Q(is_superuser=True) | Q(groups__name=f"rvion_{role}"))
        else:
            candidates = candidates.filter(is_superuser=True)
        eligible_by_role[role] = list(candidates.distinct().order_by("first_name", "email"))
    for group in groups:
        for item in group:
            item.eligible_colleagues = eligible_by_role.get(item.role, [])
    statuses = [(value, localized["status"][value][0 if fa else 1]) for value, _ in ManagementNotification.STATUSES]
    categories = [(value, localized["category"][value][0 if fa else 1]) for value, _ in ManagementNotification.CATEGORIES]
    priorities = [(value, localized["priority"][value][0 if fa else 1]) for value, _ in ManagementNotification.PRIORITIES]
    return render(request, "management_portal/v2/notifications.html", {
        "overdue_notifications": groups[0],
        "upcoming_notifications": groups[1],
        "snoozed_notifications": groups[2],
        "resolved_notifications": groups[3],
        "statuses": statuses,
        "categories": categories,
        "priorities": priorities,
        "active_status": status, "active_category": category, "active_priority": priority,
        "can_review_payments": can_review_payments,
        "snooze_choices": (
            [("15m", "۱۵ دقیقه"), ("1h", "۱ ساعت"), ("4h", "۴ ساعت"), ("tomorrow", "فردا")]
            if fa else [("15m", "15 minutes"), ("1h", "1 hour"), ("4h", "4 hours"), ("tomorrow", "Tomorrow")]
        ),
        "lang": getattr(request, "LANGUAGE_CODE", "fa"),
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def notification_claim(request, notification_id):
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    if notification.status == "resolved":
        message = "این مورد مختومه شده است." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "This item has already been resolved."
        if _notification_json_requested(request):
            return JsonResponse({"ok": False, "message": message}, status=409)
        messages.warning(request, message)
        return redirect(_safe_notification_redirect(request, request.POST.get("next")))
    notification.owner = request.user
    notification.save(update_fields=["owner", "updated_at"])
    OperationalAudit.objects.create(actor=request.user, action="notification_claimed", target_type="management_notification", target_id=str(notification.pk), summary=notification.title)
    message = "مسئولیت این مورد به شما واگذار شد." if getattr(request, "LANGUAGE_CODE", "fa") == "fa" else "This item is now assigned to you."
    if _notification_json_requested(request):
        return JsonResponse(_notification_action_payload(request, notification, message, "claim"))
    messages.success(request, message)
    return redirect(_safe_notification_redirect(request, request.POST.get("next")))


SNOOZE_CHOICES = {"15m": 15 * 60, "1h": 60 * 60, "4h": 4 * 60 * 60, "tomorrow": 24 * 60 * 60}


@staff_member_required(login_url="accounts:login")
@require_POST
def notification_snooze(request, notification_id):
    """Hide an alert until later instead of resolving work that is not done."""
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    seconds = SNOOZE_CHOICES.get(request.POST.get("duration", "1h"))
    fa = getattr(request, "LANGUAGE_CODE", "fa") == "fa"
    if not seconds:
        message = "بازه یادآوری معتبر نیست." if fa else "That snooze interval is not valid."
        if _notification_json_requested(request):
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(_safe_notification_redirect(request, request.POST.get("next")))
    notification.snoozed_until = timezone.now() + timedelta(seconds=seconds)
    if notification.status == "unread":
        notification.status = "read"
    notification.save(update_fields=["snoozed_until", "status", "updated_at"])
    # A snooze must re-alert later, so the receipts are reopened for delivery.
    NotificationReceipt.objects.filter(notification=notification).update(push_sent_at=None, seen_at=None)
    OperationalAudit.objects.create(
        actor=request.user, action="notification_snoozed", target_type="management_notification",
        target_id=str(notification.pk), summary=notification.title,
        metadata={"until": notification.snoozed_until.isoformat()},
    )
    message = (
        f"این اعلان تا {notification.snoozed_until:%H:%M} به تعویق افتاد."
        if fa else f"Snoozed until {notification.snoozed_until:%H:%M}."
    )
    if _notification_json_requested(request):
        return JsonResponse(_notification_action_payload(request, notification, message, "snooze"))
    messages.success(request, message)
    return redirect(_safe_notification_redirect(request, request.POST.get("next")))


@staff_member_required(login_url="accounts:login")
@require_POST
def notification_assign(request, notification_id):
    """Hand an alert to a specific colleague rather than only claiming it."""
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    fa = getattr(request, "LANGUAGE_CODE", "fa") == "fa"
    from .notifications import recipients_for
    assignee = recipients_for(notification).filter(pk=request.POST.get("user_id")).first()
    if not assignee:
        message = "همکار انتخاب‌شده معتبر نیست." if fa else "That colleague is not a valid assignee."
        if _notification_json_requested(request):
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(_safe_notification_redirect(request, request.POST.get("next")))
    notification.owner = assignee
    notification.save(update_fields=["owner", "updated_at"])
    now = timezone.now()
    NotificationReceipt.objects.filter(notification=notification).exclude(user=assignee).update(seen_at=now)
    assignee_receipt, _ = NotificationReceipt.objects.get_or_create(user=assignee, notification=notification)
    if assignee_receipt.seen_at:
        assignee_receipt.seen_at = None
    assignee_receipt.push_sent_at = None
    assignee_receipt.push_retry_at = None
    assignee_receipt.push_attempt_count = 0
    assignee_receipt.save(update_fields=["seen_at", "push_sent_at", "push_retry_at", "push_attempt_count"])
    OperationalAudit.objects.create(
        actor=request.user, action="notification_assigned", target_type="management_notification",
        target_id=str(notification.pk), summary=notification.title,
        metadata={"assignee": assignee.email},
    )
    label = assignee.get_full_name() or assignee.email
    message = f"به {label} واگذار شد." if fa else f"Assigned to {label}."
    if _notification_json_requested(request):
        return JsonResponse(_notification_action_payload(request, notification, message, "assign"))
    messages.success(request, message)
    return redirect(_safe_notification_redirect(request, request.POST.get("next")))


@staff_member_required(login_url="accounts:login")
@require_POST
def notification_payment_action(request, notification_id, decision):
    """Approve or reject the payment an alert is about, without leaving it."""
    if decision not in {"approve", "reject"}:
        raise Http404
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    fa = getattr(request, "LANGUAGE_CODE", "fa") == "fa"
    if not request.user.has_perm("assessments.change_manualpaymentsubmission") and not request.user.is_superuser:
        raise PermissionDenied
    submission_id = notification.source_key.split(":")[1] if ":" in notification.source_key else ""
    submission = ManualPaymentSubmission.objects.filter(pk=submission_id).first() if submission_id.isdigit() else None
    if notification.category != "payments" or not submission:
        message = "این اعلان به یک رسید پرداخت متصل نیست." if fa else "This alert is not linked to a payment receipt."
        if _notification_json_requested(request):
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(_safe_notification_redirect(request, request.POST.get("next")))
    try:
        with transaction.atomic():
            submission = ManualPaymentSubmission.objects.select_for_update().select_related("order").get(pk=submission.pk)
            if submission.status != "pending":
                raise PaymentVerificationError("این رسید قبلاً بررسی شده است." if fa else "This receipt has already been reviewed.")
            if decision == "approve":
                _payment, _order, _created, applied = approve_manual_payment(
                    submission.pk, reviewer=request.user,
                    review_note="تأیید سریع از صفحه اعلان‌ها",
                )
                if not applied:
                    raise PaymentVerificationError("این رسید قبلاً بررسی شده است." if fa else "This receipt has already been reviewed.")
                message = "پرداخت تأیید و دسترسی آزمون صادر شد." if fa else "Payment approved and exam access granted."
            else:
                review_note = request.POST.get("review_note", "").strip()
                if len(review_note) < 3:
                    raise PaymentVerificationError("دلیل رد را وارد کنید." if fa else "Enter a rejection reason.")
                submission.status = "rejected"
                submission.reviewed_by = request.user
                submission.reviewed_at = timezone.now()
                submission.review_note = review_note
                submission.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note"])
                message = "رسید پرداخت رد شد." if fa else "The payment receipt was rejected."
            resolved_at = timezone.now()
            related = ManagementNotification.objects.filter(
                Q(source_key=f"payment:{submission.pk}")
                | Q(source_key__startswith=f"payment:{submission.pk}:resubmitted:")
                | Q(source_key=f"sla:payment:{submission.pk}"),
                status__in=("unread", "read"),
            )
            related.update(
                status="resolved", resolved_by=request.user,
                resolved_at=resolved_at, updated_at=resolved_at,
            )
            notification.refresh_from_db()
    except PaymentVerificationError as error:
        message = str(error)
        if _notification_json_requested(request):
            return JsonResponse({"ok": False, "message": message}, status=409)
        messages.error(request, message)
        return redirect(_safe_notification_redirect(request, request.POST.get("next")))
    OperationalAudit.objects.create(
        actor=request.user, action=f"notification_payment_{decision}", target_type="manual_payment",
        target_id=str(submission.pk), summary=notification.title,
    )
    if _notification_json_requested(request):
        return JsonResponse(_notification_action_payload(request, notification, message, f"payment_{decision}"))
    messages.success(request, message)
    return redirect(_safe_notification_redirect(request, request.POST.get("next")))


@staff_member_required(login_url="accounts:login")
def notification_feed(request):
    since = request.GET.get("since")
    now = timezone.now()
    queryset = _visible_notifications(request.user).filter(status="unread").filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now)
    )
    if since and since.isdigit():
        queryset = queryset.filter(pk__gt=int(since))
    items = list(queryset.order_by("pk")[:25])
    return JsonResponse({"notifications": [{
        "id": item.pk,
        "title": item.title,
        "description": item.description,
        # Always route through the audited opener.  A stored target URL must
        # never become a client-side open redirect.
        "url": reverse("management_portal:notification_open", args=[item.pk]),
    } for item in items]})


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
    allowed_suffixes = tuple(getattr(settings, "WEB_PUSH_ALLOWED_HOST_SUFFIXES", ()))
    try:
        parsed = urlsplit(endpoint)
        host = (parsed.hostname or "").lower().rstrip(".")
        trusted_host = any(host == suffix or host.endswith(f".{suffix}") for suffix in allowed_suffixes)
        valid_values = all(isinstance(value, str) and 1 <= len(value) <= 255 for value in (p256dh, auth))
        if (
            not isinstance(endpoint, str) or len(endpoint) > 1000
            or parsed.scheme != "https" or not host or parsed.username or parsed.password
            or not trusted_host or not valid_values
        ):
            raise ValueError
    except (TypeError, ValueError):
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
    if getattr(request, "LANGUAGE_CODE", "fa") == "fa":
        message = "اعلان مختومه شد." if status == "resolved" else "اعلان به‌عنوان خوانده‌شده ثبت شد."
    else:
        message = "The alert was resolved." if status == "resolved" else "The alert was marked as read."
    if _notification_json_requested(request):
        return JsonResponse(_notification_action_payload(request, notification, message, status))
    messages.success(request, message)
    return redirect(_safe_notification_redirect(request, request.POST.get("next")))


@staff_member_required(login_url="accounts:login")
def notification_open(request, notification_id):
    notification = get_object_or_404(_visible_notifications(request.user), pk=notification_id)
    NotificationReceipt.objects.filter(user=request.user, notification=notification, seen_at__isnull=True).update(seen_at=timezone.now())
    target = notification.target_url or ""
    legacy_targets = {
        "/admin/assessments/manualpaymentsubmission/": reverse("management_portal:approvals"),
        "/admin/accounts/user/": reverse("management_portal:approvals"),
        "/admin/assessments/supportticket/": reverse("management_portal:assessment_support"),
        "/admin/crm_orders/crmorder/": reverse("management_portal:request_list") + "?kind=crm",
        "/admin/clinic_orders/clinicorder/": reverse("management_portal:request_list") + "?kind=clinic",
        "/admin/leads/lead/": reverse("management_portal:request_list") + "?kind=lead",
    }
    return redirect(_safe_notification_redirect(request, legacy_targets.get(target, target)))


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
    selected_audience = request.GET.get("audience", "manual")
    if selected_audience not in {"manual", *AUDIENCE_LABELS}:
        selected_audience = "manual"
    initial = {"audience": selected_audience}
    selected_snapshot = None
    if selected_audience != "manual":
        selected_snapshot = resolve_sms_audience(selected_audience)
        initial.update({
            "recipients": "\n".join(selected_snapshot.recipients),
            "expected_count": selected_snapshot.count,
        })
        default_template = SMSMessageTemplate.objects.filter(is_active=True, audience=selected_audience).first()
        if default_template:
            initial.update({
                "template": default_template,
                "message": default_template.body_fa if lang == "fa" else default_template.body_en,
            })
    form = ManualSMSForm(request.POST or None, initial=initial, lang=lang)
    if request.method == "POST" and form.is_valid():
        audience = form.cleaned_data["audience"]
        if audience == "manual":
            recipients = form.cleaned_data["recipients"]
        else:
            snapshot = resolve_sms_audience(audience)
            recipients = list(snapshot.recipients)
            if form.cleaned_data.get("expected_count") != snapshot.count:
                form.add_error(None, "اعضای گروه تغییر کرده‌اند؛ پیش‌نمایش را دوباره بازبینی کنید." if lang == "fa" else "The segment changed; review the preview again.")
            if snapshot.count > 50:
                form.add_error(None, "برای امنیت ارسال، هر کمپین حداکثر ۵۰ گیرنده دارد." if lang == "fa" else "For delivery safety, each campaign is limited to 50 recipients.")
            if not recipients:
                form.add_error(None, "این گروه در حال حاضر گیرنده معتبری ندارد." if lang == "fa" else "This segment currently has no valid recipients.")
        if form.errors:
            return render(request, "management_portal/sms_send.html", {
                "form": form, "history": SMSDispatch.objects.select_related("sent_by")[:50],
                "campaigns": SMSCampaign.objects.select_related("created_by")[:20],
                "audiences": sms_audience_overview(), "selected_audience": audience,
                "template_payload": [{"id": item.pk, "body": item.body_fa if lang == "fa" else item.body_en} for item in SMSMessageTemplate.objects.filter(is_active=True)],
                "lang": lang,
            })
        campaign = SMSCampaign.objects.create(
            audience=audience,
            message=form.cleaned_data["message"],
            recipient_count=len(recipients),
            created_by=request.user,
        )
        sent = failed = 0
        for recipient in recipients:
            try:
                result = send_sms(recipient, form.cleaned_data["message"])
            except (SMSDeliveryError, ImproperlyConfigured, ValueError) as exc:
                failed += 1
                SMSDispatch.objects.create(
                    recipient=recipient, message=form.cleaned_data["message"], status="failed",
                    error_message=str(exc)[:240], sent_by=request.user, campaign=campaign,
                )
            else:
                sent += 1
                SMSDispatch.objects.create(
                    recipient=recipient, message=form.cleaned_data["message"], status="sent",
                    provider=result.provider, provider_reference=result.reference, sent_by=request.user, campaign=campaign,
                )
        campaign.sent_count = sent
        campaign.failed_count = failed
        campaign.save(update_fields=("sent_count", "failed_count"))
        OperationalAudit.objects.create(
            actor=request.user, action="sms_campaign_sent", target_type="sms_campaign",
            target_id=str(campaign.pk), summary=f"{audience}: {sent}/{len(recipients)}",
            metadata={"audience": audience, "recipient_count": len(recipients), "sent": sent, "failed": failed},
        )
        if sent:
            messages.success(request, f"{sent} پیامک برای ارسال پذیرفته شد." if lang == "fa" else f"{sent} SMS messages were accepted for delivery.")
        if failed:
            messages.error(request, f"ارسال برای {failed} شماره ناموفق بود؛ جزئیات در سابقه ثبت شد." if lang == "fa" else f"Delivery failed for {failed} numbers; details were recorded in history.")
        return redirect("management_portal:sms_send")
    return render(request, "management_portal/sms_send.html", {
        "form": form, "history": SMSDispatch.objects.select_related("sent_by")[:50],
        "campaigns": SMSCampaign.objects.select_related("created_by")[:20],
        "audiences": sms_audience_overview(), "selected_audience": selected_audience,
        "template_payload": [{"id": item.pk, "body": item.body_fa if lang == "fa" else item.body_en} for item in SMSMessageTemplate.objects.filter(is_active=True)],
        "lang": lang,
    })
