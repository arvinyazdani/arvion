import secrets
from urllib.parse import urlencode
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView

from core.views.lang import LanguageViewMixin
from leads.demo_handoff import handle_resolved_demo_selection, maybe_retry_pending_demo_selection
from leads.form_draft_service import (
    InvalidSubmissionTokenError,
    MAX_SUBMISSION_TOKEN_LENGTH,
    NewLeadRateLimitedError,
    SubmissionConflictError,
    finalize_form_draft_to_lead,
    get_active_draft,
)
from leads.forms import LeadForm
from leads.models import Lead
from services.models import Service
from projects.models import DemoSelection
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.demo_labels import demo_config_labels
from projects.demo_briefs import brief_fields


def _demo_summary(snapshot, lang):
    return {
        "title": snapshot[f"template_title_{lang}"],
        "category": snapshot[f"category_{lang}"], "brand": snapshot["brand"],
        "theme": snapshot[f"theme_{lang}"], "personality": snapshot[f"personality_{lang}"],
        "features": snapshot[f"features_{lang}"], "brief": snapshot.get(f"brief_{lang}", []),
    }


def _demo_context_requested(request):
    if "demo" in request.GET:
        return bool(request.GET.get("demo", ""))
    return bool(request.GET.get("resume_demo"))


def _session_demo_selection(request):
    """Return a selected demo only when its public token is well formed and session-bound."""
    if "demo" not in request.GET and request.GET.get("resume_demo"):
        selection_id = request.session.get("contact_demo_language_tokens", {}).get(request.GET["resume_demo"])
        if not isinstance(selection_id, int):
            return None
        return DemoSelection.objects.select_related("template").filter(pk=selection_id, session_key=request.session.session_key).first()
    token = request.GET.get("demo", "")
    if not token:
        return None
    try:
        UUID(token)
    except (TypeError, ValueError, AttributeError):
        return None
    return DemoSelection.objects.select_related("template").filter(
        public_token=token,
        session_key=request.session.session_key,
    ).first()


class LeadCreateView(LanguageViewMixin, FormView):
    template_name = "leads/contact.html"
    form_class = LeadForm

    # One-based step index matching the template's fieldset[data-step]
    # numbering, used only to focus a Django-side validation error rerender
    # on the right step — mirrors the existing CrmOrderCreateView/
    # ClinicOrderCreateView field_steps pattern.
    FIELD_STEPS = {
        **dict.fromkeys(("request_type", "service", "business_name", "website_url", "message"), 1),
        **dict.fromkeys(("budget_range", "timeline"), 2),
        **dict.fromkeys(("name", "phone", "email_or_telegram", "preferred_contact", "privacy_accept"), 3),
    }

    def form_invalid(self, form):
        error_fields = [name for name in form.errors if name != "__all__"]
        error_step = min((self.FIELD_STEPS.get(name, 1) for name in error_fields), default=1)
        return self.render_to_response(self.get_context_data(form=form, error_step=error_step))

    def _resolved_demo_selection(self):
        """Resolve `?demo=` for this request at most once — `get_initial`,
        `get_context_data`, and `form_valid` can all run within the same
        request/response cycle (e.g. `get_initial` is always called while
        building the form, even on POST) and would otherwise each issue
        their own `DemoSelection` query. The pre-login-marker/already-
        authenticated hand-off (`handle_resolved_demo_selection`) also
        runs exactly once here, as a side effect of the first resolution,
        rather than once per call site.

        When there is no explicit `?demo=` at all (never for an
        invalid/foreign one — that must not silently fall back to an
        unrelated old marker), an authenticated non-staff customer also
        gets one retry of a pending marker left over from an earlier
        failed attach (at login, or a prior visit here) — see
        `maybe_retry_pending_demo_selection`. This is the only place in
        the whole site that check runs; it is not a middleware.
        """
        if not hasattr(self, "_demo_selection_cache"):
            selection = _session_demo_selection(self.request)
            self._demo_selection_cache = selection
            if selection:
                handle_resolved_demo_selection(self.request, selection)
            elif not _demo_context_requested(self.request):
                maybe_retry_pending_demo_selection(self.request)
        return self._demo_selection_cache

    def _resolved_final_submission_token(self):
        """Minted fresh on every ordinary `GET`, so a genuinely new visit
        can never collide with an earlier, unrelated attempt's identity
        (V2.1-D). On a validation-error rerender (the same request that
        was just POSTed), the value the customer already submitted is
        echoed back verbatim instead — fixing a typo and resubmitting must
        still be recognized as the same attempt, not a new one that resets
        rate-limit/idempotency bookkeeping. Cached per request since both
        `get_context_data` and `form_valid` may need it. Never rendered at
        all for a guest, staff, or superuser — see `get_context_data`."""
        if not hasattr(self, "_final_submission_token_cache"):
            if self.request.method == "POST":
                posted = self.request.POST.get("final_submission_token", "").strip()[:MAX_SUBMISSION_TOKEN_LENGTH]
                self._final_submission_token_cache = posted or secrets.token_urlsafe(24)
            else:
                self._final_submission_token_cache = secrets.token_urlsafe(24)
        return self._final_submission_token_cache

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["lang"] = self.lang
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        service_slug = self.request.GET.get("service", "")
        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service:
            initial["service"] = service
            initial["request_type"] = {
                "corporate-website-design": "website", "custom-web-application": "webapp",
                "ecommerce-platform": "ecommerce", "maintenance-and-growth": "support",
            }.get(service.slug, "consultation")
        selection = self._resolved_demo_selection()
        if selection:
            values = selection.selections if isinstance(selection.selections, dict) else {}
            brief = values.get("brief")
            timing = brief.get("timing") if isinstance(brief, dict) else None
            if timing in ("flexible", "month", "quarter"):
                initial["timeline"] = {"flexible": "flexible", "month": "one_month", "quarter": "one_three"}[timing]
            initial["request_type"] = {
                "ecommerce": "ecommerce", "restaurant": "website", "portfolio": "website",
                "corporate": "website", "clinic": "webapp", "education": "webapp", "jewelry": "ecommerce",
            }.get(selection.template.category, "consultation")
            initial["message"] = (
                f"نمونه انتخاب‌شده: {selection.template.title_fa}\n"
                "هدف و جزئیات پروژه را اینجا کامل می‌کنم: "
            ) if self.lang == "fa" else (
                f"Selected demo: {selection.template.title_en}\n"
                "Project goals and details: "
            )
        from core.order_summary import lead_initial
        return lead_initial(self.request, initial, self.lang)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.order_summary import summary_lines
        from core.order_paths import parse_choices
        context["order_summary"] = summary_lines(self.request, self.lang)
        context["order_choices"] = parse_choices(self.request.GET)
        # A `demo` token in the URL that cannot be resolved for this session —
        # wrong session, wrong device, expired, or simply invalid — must not
        # block or explain itself (that would leak whether the token exists
        # at all); it just surfaces a neutral, non-blocking notice.
        selection = self._resolved_demo_selection()
        if _demo_context_requested(self.request) and not selection:
            context["demo_link_invalid"] = True
        elif selection:
            # Non-secret display data only — never public_token or
            # session_key — so the client-side draft can keep a same-device
            # pointer to this exact demo without needing to hold onto the
            # URL itself (see wizard-engine.js's dedicated demo context).
            context["demo_context"] = {
                "label": selection.template.title_fa if self.lang == "fa" else selection.template.title_en,
            }
            snapshot = build_demo_selection_snapshot(selection)
            context["demo_summary"] = _demo_summary(snapshot, self.lang)
            pointers = self.request.session.get("contact_demo_language_tokens", {})
            reference = next((key for key, value in pointers.items() if value == selection.pk), None)
            if reference is None:
                reference = secrets.token_urlsafe(12)
                pointers = dict(list(pointers.items())[-9:])
                pointers[reference] = selection.pk
                self.request.session["contact_demo_language_tokens"] = pointers
            other_lang = "en" if self.lang == "fa" else "fa"
            context["language_switch_url"] = "/" + other_lang + reverse("leads:contact")[3:] + "?" + urlencode({**context["order_choices"], "resume_demo": reference})
            # Only editor settings go into this public URL, never contact
            # fields or any session/submission/public token. Explicitly empty
            # features overrides a previous tab's stored defaults too.
            values = selection.selections if isinstance(selection.selections, dict) else {}
            labels = demo_config_labels(self.lang, selection.template.category)
            query = {"brand": snapshot["brand"], "features": ""}
            for key, group in (("theme", "themes"), ("personality", "personalities")):
                if isinstance(values.get(key), str) and values[key] in dict(labels[group]):
                    query[key] = values[key]
            features = values.get("features")
            if isinstance(features, list):
                query["features"] = ",".join(key for key in features if isinstance(key, str) and key in dict(labels["features"]))
            if query.get("theme") == "custom" and snapshot[f"theme_{self.lang}"].endswith(")"):
                query["color"] = values["custom_color"].lower()
            brief = values.get("brief")
            if isinstance(brief, dict):
                for field in brief_fields(selection.template.category, self.lang):
                    value = brief.get(field["key"])
                    if isinstance(value, str) and value in dict(field["options"]):
                        query["brief_" + field["key"]] = value
            context["demo_edit_url"] = reverse("projects:demo_preview", args=[selection.template.slug]) + "?" + urlencode({**context["order_choices"], **query}) + "#configurator"
        user = self.request.user
        if user.is_authenticated and not user.is_staff and not user.is_superuser:
            if not selection and not _demo_context_requested(self.request):
                draft = get_active_draft(user, "leads_contact")
                if draft and draft.demo_snapshot:
                    context["demo_summary"] = _demo_summary(draft.demo_snapshot, self.lang)
            # Server-side account-bound draft mode (V2.1-C1): only ever
            # offered to a real, non-staff customer — never a guest, staff,
            # or superuser. Only plain, already-reversed URLs and a fixed
            # "1" flag are exposed; no draft id, owner id, token, or session
            # key is ever part of this context.
            context["server_draft_enabled"] = True
            context["draft_url"] = reverse("leads:draft")
            context["draft_delete_url"] = reverse("leads:draft_delete")
            context["login_url"] = reverse("accounts:login")
            context["final_submission_token"] = self._resolved_final_submission_token()
        return context

    def form_valid(self, form):
        user = self.request.user
        if user.is_authenticated and not user.is_staff and not user.is_superuser:
            # V2.1-D: the only branch that touches FormDraft at all —
            # guest/staff/superuser behavior below is byte-for-byte
            # unchanged from before this phase.
            return self._form_valid_authenticated_customer(form)

        client_ip = self.request.META.get("REMOTE_ADDR", "unknown")
        limit_key = f"lead-submit:{client_ip}"
        if not cache.add(limit_key, True, settings.LEAD_RATE_LIMIT_SECONDS):
            form.add_error(None, "لطفاً کمی صبر کنید و دوباره تلاش کنید." if self.lang == "fa" else "Please wait before submitting another enquiry.")
            return self.form_invalid(form)
        lead = form.save(commit=False)
        selection = _session_demo_selection(self.request)
        if selection:
            lead.demo_selection = selection
        lead.privacy_accepted_at = timezone.now()
        lead.save()
        self.lead = lead
        send_mail(
            subject=f"New Rvion enquiry [{lead.tracking_code}]",
            message=(
                f"Reference: {lead.tracking_code}\nName: {lead.name}\nBusiness: {lead.business_name or '-'}\n"
                f"Contact: {lead.email_or_telegram}\nPhone: {lead.phone or '-'}\nPreferred: {lead.preferred_contact}\n"
                f"Type: {lead.request_type}\nService: {lead.service or '-'}\nBudget: {lead.budget_range}\n"
                f"Timeline: {lead.timeline}\nWebsite: {lead.website_url or '-'}\n\n{lead.message}"
            ),
            from_email=None,
            recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
            fail_silently=True,
        )
        messages.success(self.request, "درخواست شما با موفقیت ثبت شد." if self.lang == "fa" else "Your enquiry was submitted successfully.")
        return super().form_valid(form)

    def _form_valid_authenticated_customer(self, form):
        """V2.1-D: atomic, non-duplicating FormDraft->Lead conversion for
        an authenticated, non-staff, non-superuser customer. All of the
        actual transition/idempotency logic lives in
        `leads.form_draft_service.finalize_form_draft_to_lead` — this
        method only wires the request-level concerns (the rate limiter and
        the deferred notification email) around it, exactly like the
        unchanged guest/staff/superuser path above does for itself."""
        user = self.request.user
        client_ip = self.request.META.get("REMOTE_ADDR", "unknown")
        limit_key = f"lead-submit:{client_ip}"
        token = self.request.POST.get("final_submission_token", "")
        selection = _session_demo_selection(self.request)

        consumed_rate_limit = False

        def allow_new_lead():
            nonlocal consumed_rate_limit
            if cache.add(limit_key, True, settings.LEAD_RATE_LIMIT_SECONDS):
                consumed_rate_limit = True
                return True
            return False

        def notify(lead):
            send_mail(
                subject=f"New Rvion enquiry [{lead.tracking_code}]",
                message=(
                    f"Reference: {lead.tracking_code}\nName: {lead.name}\nBusiness: {lead.business_name or '-'}\n"
                    f"Contact: {lead.email_or_telegram}\nPhone: {lead.phone or '-'}\nPreferred: {lead.preferred_contact}\n"
                    f"Type: {lead.request_type}\nService: {lead.service or '-'}\nBudget: {lead.budget_range}\n"
                    f"Timeline: {lead.timeline}\nWebsite: {lead.website_url or '-'}\n\n{lead.message}"
                ),
                from_email=None,
                recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
                fail_silently=True,
            )

        try:
            lead, created = finalize_form_draft_to_lead(
                owner=user, form=form, final_submission_token=token,
                demo_selection=selection, allow_new_lead=allow_new_lead, on_created=notify,
                use_saved_demo_snapshot=not _demo_context_requested(self.request),
            )
        except NewLeadRateLimitedError:
            form.add_error(None, "لطفاً کمی صبر کنید و دوباره تلاش کنید." if self.lang == "fa" else "Please wait before submitting another enquiry.")
            return self.form_invalid(form)
        except InvalidSubmissionTokenError:
            # Covers both a missing/malformed token and one belonging to a
            # different owner — never distinguished here either, for the
            # same reason the service itself never distinguishes them.
            form.add_error(
                None,
                "این صفحه قدیمی است؛ لطفاً آن را تازه‌سازی کنید و دوباره تلاش کنید."
                if self.lang == "fa" else "This page is out of date; please refresh it and try again.",
            )
            return self.form_invalid(form)
        except SubmissionConflictError:
            form.add_error(
                None,
                "این ارسال قبلاً با اطلاعات دیگری ثبت شده است؛ لطفاً صفحه را تازه‌سازی کنید."
                if self.lang == "fa" else "This submission was already recorded with different information; please refresh the page.",
            )
            return self.form_invalid(form)
        except Exception:
            # A genuinely unexpected failure (not one of the three known,
            # handled rejections above) after the rate limit may already
            # have been consumed by this exact request must never leave
            # the customer locked out of a real retry for no reason.
            if consumed_rate_limit:
                cache.delete(limit_key)
            raise

        self.lead = lead
        messages.success(self.request, "درخواست شما با موفقیت ثبت شد." if self.lang == "fa" else "Your enquiry was submitted successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return f"{reverse('leads:thanks', kwargs={'code': self.lead.tracking_code})}?lang={self.lang}"


class LeadThanksView(LanguageViewMixin, DetailView):
    model = Lead
    template_name = "leads/thanks.html"
    context_object_name = "lead"
    slug_field = "tracking_code"
    slug_url_kwarg = "code"

    def get_queryset(self):
        return Lead.objects.select_related("service")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["completed_order_label"] = dict(LeadForm(lang=self.lang).fields["request_type"].choices).get(self.object.request_type, "")
        return context
