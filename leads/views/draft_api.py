"""Account-bound, revision-checked read/save/delete API for a customer's
`leads_contact` `FormDraft` — the server-side infrastructure Phase C's UI
will call. No UI, JavaScript, template change, or Lead-submission wiring
happens here; this module is endpoints only.

Every view here:
- requires an authenticated, non-staff, non-superuser customer (a JSON
  401/403 — never an HTML redirect — for anyone else);
- operates only on `request.user`'s own draft; no draft id, owner id, or
  user id is ever accepted from a payload;
- responds with `Cache-Control: no-store` (a draft may reflect the
  customer's own selections and must never be cached by a shared proxy);
- relies on the project's already-active `CsrfViewMiddleware` for CSRF
  protection on the unsafe (POST) endpoints — nothing here is
  `csrf_exempt`;
- never echoes a caller-supplied key name or value back in an error
  message, and never logs a request body.

All revision/conflict/field-allowlist business logic lives in
`leads.form_draft_service` — these views only parse/validate the HTTP
envelope (content type, body size, JSON shape) and translate the
service's fixed, English `.code` values into a bilingual message for the
page's active language.
"""

import json

from django.http import JsonResponse
from django.views import View

from leads.form_draft_service import (
    DraftConflictError,
    DraftValidationError,
    delete_draft_with_revision,
    get_active_draft,
    save_draft_fields,
    serialize_draft_canonical,
)

FORM_TYPE = "leads_contact"

# A generous ceiling for a payload that is only ever a handful of short,
# categorical values — never free text. Anything larger is rejected
# before it is ever parsed as JSON.
MAX_BODY_BYTES = 16 * 1024

_VALIDATION_MESSAGES = {
    "unauthenticated_owner": ("برای دسترسی باید وارد حساب خود شوید.", "You must be signed in to access this."),
    "staff_or_superuser_not_allowed": (
        "این قابلیت فقط برای حساب‌های مشتری در دسترس است.",
        "This feature is only available to customer accounts.",
    ),
    "unsupported_form_type": ("نوع فرم پشتیبانی نمی‌شود.", "This form type is not supported."),
    "invalid_current_step": ("مقدار مرحله ارسالی نامعتبر است.", "The submitted step is invalid."),
    "invalid_fields_type": ("ساختار فیلدهای ارسالی نامعتبر است.", "The fields payload has an invalid structure."),
    "forbidden_field": ("یک یا چند فیلد ارسالی مجاز نیستند.", "One or more submitted fields are not allowed."),
    "unknown_field": ("یک یا چند فیلد ارسالی شناسایی نشدند.", "One or more submitted fields were not recognized."),
    "invalid_field_value": ("مقدار یک یا چند فیلد ارسالی نامعتبر است.", "One or more field values are invalid."),
    "invalid_expected_revision": (
        "مقدار نسخه ارسالی نامعتبر است.", "The submitted revision value is invalid.",
    ),
}
_DEFAULT_VALIDATION_MESSAGE = ("درخواست نامعتبر است.", "The request is invalid.")


def _lang(request):
    return getattr(request, "LANGUAGE_CODE", "fa")


def _bilingual(request, fa_message, en_message):
    return fa_message if _lang(request) == "fa" else en_message


def _json_error(request, status, code, fa_message, en_message, extra=None):
    body = {"code": code, "message": _bilingual(request, fa_message, en_message)}
    if extra:
        body.update(extra)
    response = JsonResponse(body, status=status)
    response["Cache-Control"] = "no-store"
    return response


def _validation_error_response(request, exc):
    fa_message, en_message = _VALIDATION_MESSAGES.get(exc.code, _DEFAULT_VALIDATION_MESSAGE)
    return _json_error(request, 400, exc.code or "invalid_request", fa_message, en_message)


def _conflict_response(request, exc):
    return _json_error(
        request, 409, "conflict",
        "این پیش‌نویس از آخرین باری که خواندید تغییر کرده است.",
        "This draft has changed since you last read it.",
        extra={"draft": serialize_draft_canonical(exc.draft) if exc.draft is not None else None},
    )


def _authorize_customer(request):
    """None if the request may proceed; otherwise the JSON error response
    to return immediately, before any query. Never a redirect."""
    if not request.user.is_authenticated:
        return _json_error(
            request, 401, "unauthenticated",
            "برای دسترسی باید وارد حساب خود شوید.", "You must be signed in to access this.",
        )
    if request.user.is_staff or request.user.is_superuser:
        return _json_error(
            request, 403, "staff_or_superuser_not_allowed",
            "این قابلیت فقط برای حساب‌های مشتری در دسترس است.",
            "This feature is only available to customer accounts.",
        )
    return None


def _parse_json_body(request):
    """Returns `(payload, None)` on success or `(None, error_response)` on
    any failure — malformed JSON, a non-object root, wrong content type,
    or an oversized body. Never logs or echoes the raw body."""
    if request.content_type != "application/json":
        return None, _json_error(
            request, 400, "invalid_content_type",
            "نوع محتوای درخواست باید application/json باشد.", "Content-Type must be application/json.",
        )
    if len(request.body) > MAX_BODY_BYTES:
        return None, _json_error(
            request, 400, "payload_too_large",
            "حجم درخواست بیش از حد مجاز است.", "The request body is too large.",
        )
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None, _json_error(
            request, 400, "invalid_json",
            "ساختار JSON درخواست نامعتبر است.", "The request body is not valid JSON.",
        )
    if not isinstance(payload, dict):
        return None, _json_error(
            request, 400, "invalid_payload",
            "بدنه درخواست باید یک شیء JSON باشد.", "The request body must be a JSON object.",
        )
    return payload, None


class FormDraftView(View):
    """`GET`: the customer's current `leads_contact` draft, or `null`.
    `POST`: race-safe, revision-checked create-or-update of its
    `fields`/`current_step`.
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response

    def get(self, request):
        denial = _authorize_customer(request)
        if denial:
            return denial
        # Strictly read-only: no write, no lock, no expiry renewal.
        draft = get_active_draft(request.user, FORM_TYPE)
        return JsonResponse({"draft": serialize_draft_canonical(draft) if draft is not None else None})

    def post(self, request):
        denial = _authorize_customer(request)
        if denial:
            return denial

        payload, error = _parse_json_body(request)
        if error:
            return error

        if set(payload.keys()) != {"fields", "current_step", "expected_revision"}:
            return _json_error(
                request, 400, "invalid_payload_keys",
                "کلیدهای ارسالی نامعتبر یا ناقص هستند.", "The submitted keys are invalid or incomplete.",
            )

        fields = payload["fields"]
        current_step = payload["current_step"]
        expected_revision = payload["expected_revision"]

        if not isinstance(fields, dict):
            return _json_error(
                request, 400, "invalid_fields_type",
                "ساختار فیلدهای ارسالی نامعتبر است.", "The fields payload has an invalid structure.",
            )
        if not isinstance(current_step, int) or isinstance(current_step, bool):
            return _json_error(
                request, 400, "invalid_current_step_type",
                "نوع مرحله ارسالی نامعتبر است.", "The current_step type is invalid.",
            )
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
            return _json_error(
                request, 400, "invalid_expected_revision_type",
                "نوع نسخه ارسالی نامعتبر است.", "The expected_revision type is invalid.",
            )

        try:
            draft, created = save_draft_fields(
                owner=request.user, form_type=FORM_TYPE, fields=fields,
                current_step=current_step, expected_revision=expected_revision,
            )
        except DraftConflictError as exc:
            return _conflict_response(request, exc)
        except DraftValidationError as exc:
            return _validation_error_response(request, exc)

        return JsonResponse({"draft": serialize_draft_canonical(draft)}, status=201 if created else 200)


class FormDraftDeleteView(View):
    """`POST`: race-safe, revision-checked hard delete of the customer's
    current `leads_contact` draft. Idempotent when none exists."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        denial = _authorize_customer(request)
        if denial:
            return denial

        payload, error = _parse_json_body(request)
        if error:
            return error

        if set(payload.keys()) != {"expected_revision"}:
            return _json_error(
                request, 400, "invalid_payload_keys",
                "کلیدهای ارسالی نامعتبر یا ناقص هستند.", "The submitted keys are invalid or incomplete.",
            )

        expected_revision = payload["expected_revision"]
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
            return _json_error(
                request, 400, "invalid_expected_revision_type",
                "نوع نسخه ارسالی نامعتبر است.", "The expected_revision type is invalid.",
            )

        try:
            deleted = delete_draft_with_revision(
                owner=request.user, form_type=FORM_TYPE, expected_revision=expected_revision,
            )
        except DraftConflictError as exc:
            return _conflict_response(request, exc)
        except DraftValidationError as exc:
            return _validation_error_response(request, exc)

        return JsonResponse({"deleted": deleted})
