"""V2.1-C2: the account dashboard's safe, read-only display of a
customer's own in-progress `leads_contact` FormDraft. Covers the
`accounts.views.dashboard` wiring, `leads.draft_dashboard.
build_draft_dashboard_card`'s safety guarantees, and the rendered
template's bilingual, no-leak, no-mutation contract. Does not touch
`FormDraft` writes, finalize/idempotency, rate limiting, or migrations —
see `leads.test_finalize`/`leads.test_form_draft`/`leads.test_draft_api`
for those."""

import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from leads.form_draft_service import attach_demo_snapshot, save_draft_fields
from leads.models import FormDraft
from projects.models import DemoSelection, DemoTemplate
from services.models import Service

User = get_user_model()

DASHBOARD_URL = reverse("accounts:dashboard")
# The URL language prefix is authoritative for accounts.views.dashboard
# (its own comment: "The language prefix is authoritative") — a bare
# ?lang= query string on the default /fa/ path does not switch it, so
# English assertions must hit the literal /en/ path, exactly like the
# existing accounts.tests dashboard tests already do.
DASHBOARD_URL_FA = "/fa/account/dashboard/"
DASHBOARD_URL_EN = "/en/account/dashboard/"


def make_customer(suffix="a"):
    return User.objects.create_user(
        username=f"dashboard-draft-{suffix}@example.com", email=f"dashboard-draft-{suffix}@example.com",
        password="x", is_active=True, email_verified=True,
    )


def make_service(suffix="a", is_active=True):
    return Service.objects.create(
        title_fa=f"خدمت آزمایشی {suffix}", title_en=f"Test service {suffix}", slug=f"dashboard-draft-service-{suffix}",
        short_description_fa="خلاصه", short_description_en="Summary", is_active=is_active,
    )


def make_demo_selection(suffix="a", title_fa="دموی فروشگاهی", title_en="Storefront demo",
                         fictional_brand_fa="برند آزمایشی", fictional_brand_en="Test Brand"):
    template = DemoTemplate.objects.create(
        slug=f"dashboard-draft-demo-{suffix}", category="ecommerce", title_fa=title_fa,
        title_en=title_en, tagline_fa="x", tagline_en="y", fictional_brand_fa=fictional_brand_fa,
        fictional_brand_en=fictional_brand_en, style_key="minimal",
    )
    return DemoSelection.objects.create(
        template=template, session_key=f"dashboard-draft-session-{suffix}",
        selections={"theme": "warm", "personality": "minimal", "features": ["blog"]},
    )


def make_full_draft(owner, service=None):
    fields = {
        "request_type": "webapp", "budget_range": "50_150", "timeline": "one_three", "preferred_contact": "email",
    }
    if service is not None:
        fields["service_id"] = service.pk
    draft, _ = save_draft_fields(owner=owner, form_type="leads_contact", fields=fields, current_step=1, expected_revision=0)
    return draft


class DashboardRequiresLoginTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(DASHBOARD_URL)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={DASHBOARD_URL}")


class DashboardNoDraftStateTests(TestCase):
    def test_customer_without_active_draft_sees_shortcut_and_no_draft_card(self):
        customer = make_customer(suffix="empty")
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["order_draft"])
        content = response.content.decode("utf-8")
        self.assertNotIn('id="my-order-draft"', content)
        self.assertIn("شروع سفارش پروژه", content)
        # The compact shortcut goes straight to the contact form, and the
        # sidebar offers the demo-browsing path too — no big empty-state
        # panel is rendered anywhere for this state.
        self.assertIn(reverse("leads:contact"), content)
        self.assertIn(reverse("projects:demo_gallery"), content)

    def test_a_submitted_draft_is_not_treated_as_an_unfinished_one(self):
        customer = make_customer(suffix="submitted-only")
        draft = make_full_draft(customer)
        draft.status = "submitted"
        draft.save(update_fields=["status"])
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertIsNone(response.context["order_draft"])
        self.assertNotIn('id="my-order-draft"', response.content.decode("utf-8"))


class DashboardActiveDraftTests(TestCase):
    def test_customer_with_active_draft_sees_own_card(self):
        customer = make_customer(suffix="own")
        make_full_draft(customer)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertIsNotNone(response.context["order_draft"])
        content = response.content.decode("utf-8")
        self.assertIn('id="my-order-draft"', content)
        self.assertIn("پیش‌نویس سفارش پروژه", content)
        self.assertIn("ادامه تکمیل سفارش", content)

    def test_another_owners_draft_is_never_shown(self):
        owner_a = make_customer(suffix="theirs")
        owner_b = make_customer(suffix="mine")
        make_full_draft(owner_a)
        self.client.force_login(owner_b)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertIsNone(response.context["order_draft"])
        self.assertNotIn('id="my-order-draft"', response.content.decode("utf-8"))

    def test_expired_draft_is_not_shown(self):
        customer = make_customer(suffix="expired")
        draft = make_full_draft(customer)
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertIsNone(response.context["order_draft"])
        self.assertNotIn('id="my-order-draft"', response.content.decode("utf-8"))

    def test_submitted_draft_is_not_shown(self):
        customer = make_customer(suffix="done")
        draft = make_full_draft(customer)
        draft.status = "submitted"
        draft.save(update_fields=["status"])
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertIsNone(response.context["order_draft"])
        self.assertNotIn('id="my-order-draft"', response.content.decode("utf-8"))


class DashboardDraftLabelTranslationTests(TestCase):
    def test_all_five_allowlist_values_render_as_bilingual_safe_labels_fa(self):
        customer = make_customer(suffix="labels-fa")
        service = make_service(suffix="labels-fa")
        make_full_draft(customer, service=service)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        self.assertIn("وب‌اپلیکیشن اختصاصی", content)   # request_type=webapp
        self.assertIn("۵۰ تا ۱۵۰ میلیون تومان", content)  # budget_range=50_150
        self.assertIn("یک تا سه ماه", content)            # timeline=one_three
        self.assertIn("ایمیل", content)                   # preferred_contact=email
        self.assertIn(service.title_fa, content)
        # Raw stored values must never leak verbatim.
        self.assertNotIn(">webapp<", content)
        self.assertNotIn("50_150", content)
        self.assertNotIn("one_three", content)

    def test_all_five_allowlist_values_render_as_bilingual_safe_labels_en(self):
        customer = make_customer(suffix="labels-en")
        service = make_service(suffix="labels-en")
        make_full_draft(customer, service=service)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_EN)
        content = response.content.decode("utf-8")

        self.assertIn("Web application", content)
        self.assertIn("50–150 million toman", content)
        self.assertIn("One to three months", content)
        self.assertIn("Email", content)
        self.assertIn(service.title_en, content)
        self.assertNotIn("وب‌اپلیکیشن", content)
        self.assertNotIn("50_150", content)
        self.assertNotIn("one_three", content)


class DashboardDraftDemoSnapshotTests(TestCase):
    def test_demo_snapshot_renders_in_the_correct_language(self):
        customer = make_customer(suffix="demo")
        selection = make_demo_selection(suffix="dash")
        make_full_draft(customer)
        attach_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)
        self.client.force_login(customer)

        fa_response = self.client.get(DASHBOARD_URL_FA)
        self.assertContains(fa_response, "دموی فروشگاهی")
        self.assertNotContains(fa_response, "Storefront demo")
        # V2.1-C2 corrective: brand is not bilingual and must never render
        # in either language on this card.
        self.assertNotContains(fa_response, "برند آزمایشی")
        self.assertNotContains(fa_response, "Test Brand")

        en_response = self.client.get(DASHBOARD_URL_EN)
        self.assertContains(en_response, "Storefront demo")
        self.assertNotContains(en_response, "دموی فروشگاهی")
        self.assertNotContains(en_response, "برند آزمایشی")
        self.assertNotContains(en_response, "Test Brand")

    def test_a_draft_with_no_demo_never_renders_a_demo_row(self):
        customer = make_customer(suffix="no-demo")
        make_full_draft(customer)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertNotIn("دموی مرجع", response.content.decode("utf-8"))

    def test_an_empty_or_malformed_demo_snapshot_does_not_crash(self):
        customer = make_customer(suffix="malformed")
        draft = make_full_draft(customer)
        FormDraft.objects.filter(pk=draft.pk).update(demo_snapshot={"template_title_fa": "x"})  # missing keys
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("دموی مرجع", response.content.decode("utf-8"))

    def test_a_legacy_snapshot_with_only_valid_bilingual_title_and_category_still_renders(self):
        # V2.1-C2 corrective, requirement 6: brand is no longer part of
        # what this card requires or reads at all — a snapshot missing it
        # entirely (e.g. written before brand existed, or simply dropped)
        # must still show its title/category, not disappear.
        customer = make_customer(suffix="legacy-no-brand")
        draft = make_full_draft(customer)
        FormDraft.objects.filter(pk=draft.pk).update(demo_snapshot={
            "template_title_fa": "دموی قدیمی", "template_title_en": "Legacy demo",
            "category_fa": "فروشگاه اینترنتی", "category_en": "E-commerce",
        })
        self.client.force_login(customer)

        fa_response = self.client.get(DASHBOARD_URL_FA)
        self.assertContains(fa_response, "دموی قدیمی")
        self.assertContains(fa_response, "فروشگاه اینترنتی")

        en_response = self.client.get(DASHBOARD_URL_EN)
        self.assertContains(en_response, "Legacy demo")
        self.assertContains(en_response, "E-commerce")

    def test_snapshot_with_a_fully_persian_brand_never_leaks_into_the_english_dashboard(self):
        customer = make_customer(suffix="brand-fa-only")
        selection = make_demo_selection(
            suffix="brand-fa-only", title_fa="دموی برند فارسی", title_en="Persian brand demo",
            fictional_brand_fa="برند کاملاً فارسی", fictional_brand_en="Fully English Brand",
        )
        make_full_draft(customer)
        attach_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_EN)
        content = response.content.decode("utf-8")

        self.assertContains(response, "Persian brand demo")
        self.assertContains(response, "E-commerce")
        self.assertNotIn("برند کاملاً فارسی", content)
        self.assertNotIn("Fully English Brand", content)

        match = re.search(r"<dt>Reference demo</dt><dd>(.*?)</dd>", content)
        self.assertIsNotNone(match, content)
        demo_row_html = match.group(1)
        self.assertFalse(re.search(r"[؀-ۿ]", demo_row_html), demo_row_html)

    def test_snapshot_title_and_category_render_correctly_in_persian(self):
        customer = make_customer(suffix="brand-fa-check")
        selection = make_demo_selection(
            suffix="brand-fa-check", title_fa="دموی برند فارسی دو", title_en="Persian brand demo two",
            fictional_brand_fa="برند کاملاً فارسی", fictional_brand_en="Fully English Brand",
        )
        make_full_draft(customer)
        attach_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        self.assertContains(response, "دموی برند فارسی دو")
        self.assertContains(response, "فروشگاه اینترنتی")
        self.assertNotIn("Fully English Brand", content)
        self.assertNotIn("برند کاملاً فارسی", content)


class DashboardDraftPrivacyTests(TestCase):
    def test_no_forbidden_identifiers_or_free_text_in_dashboard_html(self):
        customer = make_customer(suffix="privacy")
        service = make_service(suffix="privacy")
        selection = make_demo_selection(suffix="privacy")
        draft = make_full_draft(customer, service=service)
        attach_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)
        draft.refresh_from_db()
        draft.submission_token = "should-never-leak-anywhere"
        draft.save(update_fields=["submission_token"])
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        # Bare numeric ids are deliberately not substring-checked here: a
        # small pk/owner-id can collide harmlessly with unrelated page
        # content (e.g. a step number or an asset cache-bust query
        # string) — see leads.test_contact_server_draft_ui for the same
        # established reasoning. The specific attribute/field shapes that
        # would actually leak an id or the internal token are checked
        # instead.
        self.assertNotIn("should-never-leak-anywhere", content)
        self.assertNotIn("submission_token", content)
        self.assertNotIn("session_key", content)
        self.assertNotIn("public_token", content)
        self.assertNotIn("data-draft-id", content)
        self.assertNotIn("data-owner-id", content)
        self.assertNotIn("data-user-id", content)
        self.assertNotIn("revision", content)

    def test_contact_and_free_text_details_never_appear_on_the_card(self):
        customer = make_customer(suffix="freetext")
        make_full_draft(customer)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        # These are simply never part of the FormDraft.fields allowlist in
        # the first place (leads.form_draft_service.FORBIDDEN_FIELD_KEYS),
        # so this asserts the card genuinely has nothing to leak, not just
        # that a filter is hiding it.
        self.assertNotIn("business_name", content)
        self.assertNotIn("website_url", content)

    def test_continue_cta_url_has_no_identifiers_or_tokens(self):
        customer = make_customer(suffix="cta")
        make_full_draft(customer)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        contact_url = reverse("leads:contact")
        self.assertIn(f'href="{contact_url}"', content)
        self.assertNotIn(f"{contact_url}?", content)


class DashboardDraftReadOnlyTests(TestCase):
    def test_dashboard_get_does_not_mutate_or_renew_the_draft(self):
        customer = make_customer(suffix="readonly")
        draft = make_full_draft(customer)
        revision_before = draft.revision
        updated_at_before = draft.updated_at
        expires_at_before = draft.expires_at
        self.client.force_login(customer)

        self.client.get(DASHBOARD_URL_FA)
        self.client.get(DASHBOARD_URL_EN)

        draft.refresh_from_db()
        self.assertEqual(draft.revision, revision_before)
        self.assertEqual(draft.updated_at, updated_at_before)
        self.assertEqual(draft.expires_at, expires_at_before)
        self.assertEqual(draft.status, "open")

    def test_query_count_does_not_grow_unreasonably_with_historical_drafts(self):
        customer = make_customer(suffix="queries")
        make_full_draft(customer)
        self.client.force_login(customer)

        with CaptureQueriesContext(connection) as few:
            self.client.get(DASHBOARD_URL_FA)

        for i in range(30):
            FormDraft.objects.create(
                owner=customer, form_type="leads_contact", fields={}, current_step=0, status="expired",
                submission_token=f"historical-{i}", expires_at=timezone.now() - timedelta(days=1),
            )

        with CaptureQueriesContext(connection) as many:
            self.client.get(DASHBOARD_URL_FA)

        self.assertEqual(len(few.captured_queries), len(many.captured_queries))


class DashboardExistingSectionsRegressionTests(TestCase):
    def test_assessment_payment_and_support_sections_still_render_without_regression(self):
        customer = make_customer(suffix="regression")
        make_full_draft(customer)
        self.client.force_login(customer)

        response = self.client.get(DASHBOARD_URL_FA)
        content = response.content.decode("utf-8")

        self.assertIn('id="my-assessments"', content)
        self.assertIn(reverse("accounts:orders_history"), content)
        self.assertIn(reverse("assessments:support_create"), content)
        self.assertIn(reverse("assessments:support_history"), content)
        self.assertIn('class="account-compass"', content)
