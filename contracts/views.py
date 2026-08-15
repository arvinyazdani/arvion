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
from .forms import ClauseSelectionForm, ContractReviewForm, OtpRequestForm, OtpVerifyForm, ProposalForm
from .models import ContractAcceptance, ContractClause, ContractOtpChallenge, ContractProposal, ContractReview
from .services import add_default_clauses, publish_version


def _require_contract_manager(request):
    if not request.user.is_superuser:
        raise PermissionDenied


@staff_member_required(login_url="accounts:login")
def proposal_list(request):
    _require_contract_manager(request)
    return render(request, "contracts/proposal_list_v2.html", {"proposals": ContractProposal.objects.select_related("created_by")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_create(request):
    _require_contract_manager(request)
    form = ProposalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        form.apply_assessment()
        proposal.created_by = request.user
        proposal.save()
        add_default_clauses(proposal)
        messages.success(request, "پیش‌نویس قرارداد ساخته شد؛ بندها را بررسی و سپس لینک را فعال کنید.")
        return redirect("contracts:proposal_detail", proposal_id=proposal.pk)
    return render(request, "contracts/proposal_form_v2.html", {"form": form})


@staff_member_required(login_url="accounts:login")
def proposal_detail(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses", "versions"), pk=proposal_id)
    public_url = request.build_absolute_uri(reverse("contracts:public_contract", args=[proposal.token]))
    return render(request, "contracts/proposal_detail_v2.html", {"proposal": proposal, "public_url": public_url})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_clauses(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    form = ClauseSelectionForm(request.POST or None, proposal=proposal)
    if request.method == "POST" and form.is_valid():
        enabled = {int(value) for value in form.cleaned_data["enabled_clauses"]}
        proposal.clauses.update(is_enabled=False)
        proposal.clauses.filter(pk__in=enabled).update(is_enabled=True)
        title, body = form.cleaned_data["custom_title"].strip(), form.cleaned_data["custom_body"].strip()
        if title and body:
            position = (proposal.clauses.order_by("-position").values_list("position", flat=True).first() or 0) + 1
            ContractClause.objects.create(proposal=proposal, title=title, body=body, position=position)
        messages.success(request, "انتخاب بندها ذخیره شد. برای ارسال، نسخه جدید بسازید.")
        return redirect("contracts:proposal_detail", proposal_id=proposal.pk)
    return render(request, "contracts/proposal_clauses.html", {"proposal": proposal, "form": form})


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_publish(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    version = publish_version(proposal, request.user)
    messages.success(request, f"نسخه {version.number} ثبت و لینک مشتری فعال شد.")
    return redirect("contracts:proposal_detail", proposal_id=proposal.pk)


@never_cache
def public_contract(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
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
        return redirect("contracts:public_contract", token=token)
    return render(request, "contracts/public_contract.html", {"proposal": proposal, "version": version, "snapshot": version.snapshot, "form": form, "review": existing})


def _acceptance_version(token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    review = getattr(version, "review", None)
    if not review or review.rejected_clause_ids or review.suggested_clause:
        raise PermissionDenied
    return proposal, version


@never_cache
def contract_accept(request, token):
    proposal, version = _acceptance_version(token)
    acceptance = getattr(version, "acceptance", None)
    active = version.otp_challenges.filter(used_at__isnull=True, expires_at__gt=timezone.now()).first()
    return render(request, "contracts/contract_accept.html", {
        "proposal": proposal, "version": version, "acceptance": acceptance, "active_challenge": active,
        "request_form": OtpRequestForm(), "verify_form": OtpVerifyForm(),
    })


@never_cache
@require_POST
def contract_request_otp(request, token):
    proposal, version = _acceptance_version(token)
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
    proposal, version = _acceptance_version(token)
    if hasattr(version, "acceptance"):
        return redirect("contracts:contract_accept", token=token)
    form = OtpVerifyForm(request.POST)
    challenge = version.otp_challenges.select_for_update().filter(used_at__isnull=True).order_by("-created_at").first()
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
