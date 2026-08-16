import hashlib
import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from core.sms import send_otp
from core.sms.backends import SMSDeliveryError
from management_portal.models import Customer, CustomerContact
from core.models import CompanyProfile
from .forms import ClauseSelectionForm, ContractAccessForm, ContractReviewForm, ContractSettingsForm, OtpRequestForm, OtpVerifyForm, ProposalForm
from .models import ContractAcceptance, ContractClause, ContractOtpChallenge, ContractProposal, ContractReview, ContractRoomAcknowledgement
from .services import add_default_clauses, proposal_snapshot, publish_version


def _require_contract_manager(request):
    if not request.user.is_superuser:
        raise PermissionDenied


def _manager_url(request, old_name, new_name, *args):
    namespace = getattr(getattr(request, "resolver_match", None), "namespace", "")
    return reverse(f"management_portal:{new_name}" if namespace == "management_portal" else f"contracts:{old_name}", args=args)


def _link_customer(proposal):
    customer = Customer.objects.filter(phone=proposal.customer_phone).first()
    if customer is None and proposal.customer_email:
        customer = Customer.objects.filter(email__iexact=proposal.customer_email).first()
    if customer is None:
        customer = Customer.objects.filter(name__iexact=proposal.customer_name).first()
    if customer is None:
        customer = Customer.objects.create(name=proposal.customer_name, kind="company", phone=proposal.customer_phone, email=proposal.customer_email)
    proposal.customer = customer
    CustomerContact.objects.get_or_create(customer=customer, name=proposal.customer_name, phone=proposal.customer_phone, email=proposal.customer_email, defaults={"is_primary": not customer.contacts.filter(is_primary=True).exists()})


@staff_member_required(login_url="accounts:login")
def proposal_list(request):
    _require_contract_manager(request)
    rows = [{"item": item, "url": _manager_url(request, "proposal_detail", "contract_detail", item.pk)} for item in ContractProposal.objects.select_related("created_by")]
    return render(request, "contracts/proposal_list_v2.html", {"proposal_rows": rows, "create_url": _manager_url(request, "proposal_create", "contract_create"), "settings_url": _manager_url(request, "contract_settings", "contract_settings"), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
def contract_settings(request):
    _require_contract_manager(request)
    company = CompanyProfile.objects.first()
    if company is None:
        raise ImproperlyConfigured("Company profile must be configured before contract publishing.")
    form = ContractSettingsForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تنظیمات مجری قرارداد ذخیره شد؛ فقط نسخه‌های جدید از آن استفاده می‌کنند.")
        return redirect(_manager_url(request, "proposal_list", "contract_list"))
    return render(request, "contracts/contract_settings.html", {"form": form, "list_url": _manager_url(request, "proposal_list", "contract_list"), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_create(request):
    _require_contract_manager(request)
    form = ProposalForm(request.POST or None, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        form.apply_assessment()
        proposal.created_by = request.user
        _link_customer(proposal)
        proposal.save()
        add_default_clauses(proposal)
        messages.success(request, "پیش‌نویس قرارداد ساخته شد؛ بندها را بررسی و سپس لینک را فعال کنید.")
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_form_v2.html", {"form": form, "assessment_data": form.assessment_data, "list_url": _manager_url(request, "proposal_list", "contract_list"), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_edit(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    form = ProposalForm(request.POST or None, instance=proposal, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        if form.cleaned_data.get("needs_assessment"):
            form.apply_assessment()
        _link_customer(proposal)
        proposal.save()
        messages.success(request, "پیش‌نویس ذخیره شد. برای مشتری نسخه تازه بسازید.")
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_form_v2.html", {"form": form, "assessment_data": form.assessment_data, "list_url": _manager_url(request, "proposal_list", "contract_list"), "proposal": proposal, "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
def proposal_preview(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    return render(request, "contracts/proposal_preview.html", {"proposal": proposal, "snapshot": proposal_snapshot(proposal), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_revoke(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    proposal.status = "revoked"
    proposal.save(update_fields=("status", "updated_at"))
    messages.success(request, "لینک مشتری غیرفعال شد؛ اطلاعات و نسخه‌ها حفظ شده‌اند.")
    return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_delete(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.current_version or proposal.status not in {"draft", "revoked"}:
        raise PermissionDenied
    proposal.delete()
    messages.success(request, "پیش‌نویس بدون نسخه حذف شد.")
    return redirect(_manager_url(request, "proposal_list", "contract_list"))


@staff_member_required(login_url="accounts:login")
def proposal_detail(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses", "versions"), pk=proposal_id)
    public_url = request.build_absolute_uri(reverse("contracts:public_contract", args=[proposal.token]))
    return render(request, "contracts/proposal_detail_v2.html", {"proposal": proposal, "public_url": public_url, "list_url": _manager_url(request, "proposal_list", "contract_list"), "clauses_url": _manager_url(request, "proposal_clauses", "contract_clauses", proposal.pk), "publish_url": _manager_url(request, "proposal_publish", "contract_publish", proposal.pk), "edit_url": _manager_url(request, "proposal_edit", "contract_edit", proposal.pk), "preview_url": _manager_url(request, "proposal_preview", "contract_preview", proposal.pk), "revoke_url": _manager_url(request, "proposal_revoke", "contract_revoke", proposal.pk), "delete_url": _manager_url(request, "proposal_delete", "contract_delete", proposal.pk), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_clauses(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    form = ClauseSelectionForm(request.POST or None, proposal=proposal, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        enabled = {int(value) for value in form.cleaned_data["enabled_clauses"]}
        proposal.clauses.update(is_enabled=False)
        proposal.clauses.filter(pk__in=enabled).update(is_enabled=True)
        title, body = form.cleaned_data["custom_title"].strip(), form.cleaned_data["custom_body"].strip()
        if title and body:
            position = (proposal.clauses.order_by("-position").values_list("position", flat=True).first() or 0) + 1
            ContractClause.objects.create(proposal=proposal, title=title, body=body, position=position)
        messages.success(request, "انتخاب بندها ذخیره شد. برای ارسال، نسخه جدید بسازید.")
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_clauses.html", {"proposal": proposal, "form": form, "detail_url": _manager_url(request, "proposal_detail", "contract_detail", proposal.pk), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_publish(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    version = publish_version(proposal, request.user)
    messages.success(request, f"نسخه {version.number} ثبت و لینک مشتری فعال شد.")
    return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))


@never_cache
def public_contract(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") != proposal.customer_phone:
        return redirect("contracts:contract_access", token=token)
    discovery = getattr(proposal.crm_order, "specialist_discovery", None) if proposal.crm_order_id else None
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    return render(request, "contracts/contract_room.html", {"proposal": proposal, "version": version, "discovery": discovery, "acknowledgements": acknowledgements})


@never_cache
def contract_document(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") != proposal.customer_phone:
        return redirect("contracts:contract_access", token=token)
    existing = getattr(version, "review", None)
    if request.method == "GET" and existing and not existing.rejected_clause_ids and not existing.suggested_clause:
        return redirect("contracts:contract_accept", token=token)
    form = ContractReviewForm(request.POST or None, version=version)
    if request.method == "POST" and not existing and form.is_valid():
        all_ids = {str(item["id"]) for item in version.snapshot["clauses"]}
        accepted = set(form.cleaned_data["accepted_clauses"])
        ip = request.META.get("REMOTE_ADDR", "")
        ContractReview.objects.create(
            version=version, accepted_clause_ids=sorted(accepted), rejected_clause_ids=sorted(all_ids - accepted),
            rejection_notes=form.cleaned_data["rejection_notes"].strip(), suggested_clause=form.cleaned_data["suggested_clause"].strip(),
            ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else "",
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:240],
        )
        proposal.status = "review"
        proposal.save(update_fields=["status", "updated_at"])
        return redirect("contracts:contract_document", token=token)
    return render(request, "contracts/public_contract.html", {"proposal": proposal, "version": version, "snapshot": version.snapshot, "form": form, "review": existing, "acknowledgements": set(version.room_acknowledgements.values_list("document", flat=True))})


@never_cache
@require_POST
def contract_acknowledge(request, token, document):
    proposal = get_object_or_404(ContractProposal, token=token)
    if document not in {"general", "private"} or not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") != proposal.customer_phone:
        return redirect("contracts:contract_access", token=token)
    if not version.snapshot.get(f"{document}_terms"):
        raise Http404
    ip = request.META.get("REMOTE_ADDR", "")
    ContractRoomAcknowledgement.objects.get_or_create(
        version=version, document=document,
        defaults={"ip_hash": hashlib.sha256(ip.encode()).hexdigest() if ip else "", "user_agent": request.META.get("HTTP_USER_AGENT", "")[:240]},
    )
    messages.success(request, f"بررسی «{'شرایط عمومی پیمان' if document == 'general' else 'شرایط خصوصی پیمان'}» ثبت شد.")
    return redirect("contracts:public_contract", token=token)


@never_cache
@require_POST
def contract_logout(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if proposal.current_version:
        version = proposal.versions.filter(number=proposal.current_version).first()
        if version:
            request.session.pop(f"contract-access:{version.pk}", None)
    request.session.modified = True
    messages.success(request, "از اتاق قرارداد خارج شدید.")
    return redirect("contracts:contract_access", token=token)


def _acceptance_version(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") != proposal.customer_phone:
        raise PermissionDenied
    review = getattr(version, "review", None)
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    if acknowledgements != {"general", "private"}:
        raise PermissionDenied
    if not review or review.rejected_clause_ids or review.suggested_clause:
        raise PermissionDenied
    return proposal, version


@never_cache
def contract_accept(request, token):
    proposal, version = _acceptance_version(request, token)
    acceptance = getattr(version, "acceptance", None)
    active = version.otp_challenges.filter(purpose="acceptance", used_at__isnull=True, expires_at__gt=timezone.now()).first()
    return render(request, "contracts/contract_accept.html", {
        "proposal": proposal, "version": version, "acceptance": acceptance, "active_challenge": active,
        "request_form": OtpRequestForm(), "verify_form": OtpVerifyForm(),
    })


@never_cache
@require_POST
def contract_request_otp(request, token):
    proposal, version = _acceptance_version(request, token)
    if hasattr(version, "acceptance"):
        return redirect("contracts:contract_accept", token=token)
    form = OtpRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, "برای دریافت کد، موافقت با نسخه را علامت بزنید.")
        return redirect("contracts:contract_accept", token=token)
    window_start = timezone.now() - timedelta(seconds=settings.OTP_REQUEST_WINDOW_SECONDS)
    if version.otp_challenges.filter(created_at__gte=window_start).count() >= settings.OTP_REQUEST_LIMIT:
        messages.error(request, "تعداد درخواست کد بیش از حد مجاز است؛ کمی بعد دوباره تلاش کنید.")
        return redirect("contracts:contract_accept", token=token)
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = ContractOtpChallenge.objects.create(
        version=version, phone=proposal.customer_phone, code_hash=make_password(code),
        purpose="acceptance",
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    try:
        result = send_otp(proposal.customer_phone, code)
    except (SMSDeliveryError, ValueError, ImproperlyConfigured):
        challenge.delete()
        messages.error(request, "ارسال کد تأیید انجام نشد؛ تنظیمات قالب پیامک را بررسی کنید.")
        return redirect("contracts:contract_accept", token=token)
    challenge.provider_reference = result.reference
    challenge.save(update_fields=["provider_reference"])
    messages.success(request, "کد تأیید برای شماره ثبت‌شده ارسال شد.")
    return redirect("contracts:contract_accept", token=token)


@never_cache
@require_POST
@transaction.atomic
def contract_verify_otp(request, token):
    proposal, version = _acceptance_version(request, token)
    if hasattr(version, "acceptance"):
        return redirect("contracts:contract_accept", token=token)
    form = OtpVerifyForm(request.POST)
    challenge = version.otp_challenges.select_for_update().filter(purpose="acceptance", used_at__isnull=True).order_by("-created_at").first()
    if not form.is_valid() or not challenge or challenge.expires_at <= timezone.now() or challenge.attempts >= settings.OTP_MAX_VERIFY_ATTEMPTS:
        messages.error(request, "کد معتبر یا فعال نیست؛ کد تازه درخواست کنید.")
        return redirect("contracts:contract_accept", token=token)
    challenge.attempts += 1
    challenge.save(update_fields=["attempts"])
    if not check_password(form.cleaned_data["code"], challenge.code_hash):
        messages.error(request, "کد واردشده صحیح نیست.")
        return redirect("contracts:contract_accept", token=token)
    challenge.used_at = timezone.now()
    challenge.save(update_fields=["used_at"])
    ip = request.META.get("REMOTE_ADDR", "")
    ContractAcceptance.objects.create(
        version=version, verified_phone=challenge.phone, provider_reference=challenge.provider_reference,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else "", user_agent=request.META.get("HTTP_USER_AGENT", "")[:240],
    )
    proposal.status = "accepted"
    proposal.save(update_fields=["status", "updated_at"])
    return redirect("contracts:contract_accept", token=token)


@never_cache
def contract_access(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") == proposal.customer_phone:
        return redirect("contracts:public_contract", token=token)
    form = ContractAccessForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        configured_password = getattr(settings, "CONTRACT_ACCESS_PASSWORD", "")
        if not configured_password or form.cleaned_data["phone"] != proposal.customer_phone or not secrets.compare_digest(form.cleaned_data["password"], configured_password):
            messages.error(request, "شماره همراه یا رمز ورود صحیح نیست.")
        else:
            request.session[f"contract-access:{version.pk}"] = proposal.customer_phone
            request.session.set_expiry(3600)
            return redirect("contracts:public_contract", token=token)
    return render(request, "contracts/contract_access.html", {"proposal": proposal, "form": form})
