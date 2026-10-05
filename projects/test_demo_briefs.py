from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone, translation
from unittest.mock import patch

from leads.models import Lead
from leads.form_draft_service import DraftValidationError, ensure_active_draft_with_demo_snapshot
from management_portal.models import CaseDocument, CustomerCase
from management_portal.views import _demo_selection_card, _demo_selection_report_lines
from projects.demo_briefs import GOALS, brief_labels
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection, DemoTemplate


class DemoBriefTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.demo = DemoTemplate.objects.create(
            slug="brief-restaurant", category="restaurant", title_fa="رستوران نمونه",
            title_en="Sample restaurant", fictional_brand_fa="نمونه", fictional_brand_en="Sample",
            tagline_fa="توضیح", tagline_en="Description", is_active=True,
        )
        self.payload = {"submission_token": "brief-test-token", "theme": "plum",
                        "personality": "editorial", "features": ["catalog", "booking"],
                        "brief_goal": "tables", "brief_scope": "complete",
                        "brief_content": "help", "brief_timing": "quarter"}

    def post(self, **changes):
        return self.client.post(reverse("projects:demo_configure", args=[self.demo.slug]),
                                {**self.payload, **changes})

    def test_details_are_saved_and_duplicate_retry_reuses_selection(self):
        first = self.post()
        second = self.post()
        self.assertEqual(first.url, second.url)
        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertEqual(DemoSelection.objects.get().selections["brief"],
                         {"goal": "tables", "scope": "complete", "content": "help", "timing": "quarter"})

    def test_brief_survives_account_bound_draft_handoff(self):
        self.post()
        owner = get_user_model().objects.create_user(username="draft@example.com", email="draft@example.com", password="QaOnly1221!")
        draft = ensure_active_draft_with_demo_snapshot(
            owner=owner, form_type="leads_contact", demo_selection=DemoSelection.objects.get())
        self.assertEqual(draft.demo_snapshot["brief_en"][0]["value"], "Table reservations")
        self.assertEqual(len(draft.demo_snapshot["brief_fa"]), 4)

    def test_draft_brief_validation_rejects_malformed_or_unbounded_snapshot(self):
        self.post()
        selection = DemoSelection.objects.get()
        owner = get_user_model().objects.create_user(username="invalid@example.com", email="invalid@example.com", password="QaOnly1221!")
        snapshot = build_demo_selection_snapshot(selection)
        for rows in ("bad", [{"label": "x", "value": "y", "email": "private@example.com"}],
                     [{"label": "x", "value": "x" * 301}],
                     [{"label": "x", "value": []}], snapshot["brief_fa"] * 2):
            with self.subTest(rows=rows), patch(
                    "leads.form_draft_service.build_demo_selection_snapshot",
                    return_value={**snapshot, "brief_fa": rows}):
                with self.assertRaises(DraftValidationError):
                    ensure_active_draft_with_demo_snapshot(
                        owner=owner, form_type="leads_contact", demo_selection=selection)

    def test_goal_from_a_different_topic_is_rejected_without_write(self):
        response = self.post(brief_goal="appointments")
        self.assertIn("invalid=1", response.url)
        self.assertFalse(DemoSelection.objects.exists())

    def test_arbitrary_brief_value_is_rejected_and_unknown_fields_never_saved(self):
        response = self.post(brief_scope="<script>bad()</script>")
        self.assertIn("invalid=1", response.url)
        self.assertFalse(DemoSelection.objects.exists())
        self.post(brief_email="private@example.com", brief_token="hidden")
        self.assertNotIn("private@example.com", str(DemoSelection.objects.get().selections))

    def test_stale_resubmission_preserves_changed_preferences_for_retry(self):
        self.post()
        response = self.post(brief_goal="takeaway")
        self.assertIn("stale=1", response.url)
        self.assertIn("brief_goal=takeaway", response.url)
        self.assertEqual(DemoSelection.objects.get().selections["brief"]["goal"], "tables")

    def test_older_clients_keep_the_original_payload_shape(self):
        self.post(**{f"brief_{key}": "" for key in ("goal", "scope", "content", "timing")})
        self.assertNotIn("brief", DemoSelection.objects.get().selections)

    def test_all_topics_have_localized_story_and_project_choices(self):
        for category in GOALS:
            self.demo.category = category
            self.demo.save(update_fields=["category"])
            for lang in ("fa", "en"):
                with self.subTest(category=category, lang=lang):
                    response = self.client.get(f"/{lang}/projects/demos/{self.demo.slug}/")
                    self.assertContains(response, 'id="sample-story"')
                    self.assertContains(response, 'id="sample-faq"')
                    self.assertEqual(len(response.context["demo"].brief_fields), 4)
                    for section in response.context["demo"].story_sections:
                        self.assertContains(response, section["title"])
                        if lang == "en":
                            self.assertNotRegex(section["text"], r"[\u0600-\u06ff]")

    def test_brief_reaches_manager_export_and_frozen_case_snapshot(self):
        self.post()
        selection = DemoSelection.objects.get()
        lead = Lead.objects.create(name="QA", phone="09120000000", email_or_telegram="qa@example.com",
                                   message="QA", privacy_accepted_at=timezone.now(), demo_selection=selection)
        self.assertEqual(len(_demo_selection_card(lead, "en")["brief_rows"]), 4)
        self.assertIn("هدف اصلی سایت: رزرو میز", _demo_selection_report_lines(lead))
        snapshot = build_demo_selection_snapshot(selection)
        self.assertEqual(snapshot["brief_en"][0]["value"], "Table reservations")
        case = CustomerCase.objects.get(kind="lead", source_object_id=lead.pk)
        document = CaseDocument.objects.filter(case=case, snapshot__brief_fa__isnull=False).first()
        self.assertIsNotNone(document)
        self.assertEqual(document.snapshot["brief_fa"][0]["value"], "رزرو میز")
        staff = get_user_model().objects.create_superuser(username="brief-qa", email="brief-qa@example.com", password="test-only-password")
        self.client.force_login(staff)
        with translation.override("en"):
            detail = self.client.get(reverse("management_portal:request_detail", args=["lead", lead.pk]))
            workspace = self.client.get(reverse("management_portal:workspace_detail", args=[case.pk]))
        self.assertContains(detail, "Main website goal")
        self.assertContains(workspace, "Table reservations")
        for secret in (selection.session_key, str(selection.public_token), selection.submission_token):
            self.assertNotIn(secret, str(snapshot))

    def test_malformed_legacy_brief_is_ignored_safely(self):
        self.assertEqual(brief_labels(["bad"], "restaurant", "en"), [])
        self.assertEqual(brief_labels({"goal": ["bad"], "token": "private"}, "restaurant", "en"), [])
