import re
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.html import escape

from leads.models import Lead
from management_portal.models import CaseDocument, CustomerCase
from projects.demo_briefs import GOALS, COMMON
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection, DemoTemplate


class DemoOrderPathTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        cache.clear()
        self.payload = {"name": "QA Customer", "email_or_telegram": "qa@example.test",
                        "message": "A fictional enquiry for a complete website.",
                        "phone": "", "business_name": "", "website_url": "",
                        "request_type": "website", "service": "", "budget_range": "50_150",
                        "timeline": "one_three", "preferred_contact": "email", "privacy_accept": "on"}

    def selection(self, category="restaurant", lang="fa", empty=False):
        demo = DemoTemplate.objects.create(slug="path-" + category, category=category,
            title_fa="نمونه سفارش", title_en="Order sample", fictional_brand_fa="برند فرضی",
            fictional_brand_en="Fictional Brand", style_key="minimal", default_features=["blog"])
        prefix = "/" + lang
        preview = self.client.get(prefix + reverse("projects:demo_preview", args=[demo.slug])[3:])
        values = {"submission_token": preview.context["submission_token"], "theme": "custom",
                  "custom_color": "#123abc", "personality": "industrial", "brand_preview": "QA Atelier",
                  "features": [] if empty else ["booking", "blog"],
                  "brief_goal": GOALS[category][0][0],
                  **{"brief_" + key: rows[0][0] for key, rows in COMMON.items()}}
        response = self.client.post(prefix + reverse("projects:demo_configure", args=[demo.slug])[3:], values)
        self.assertEqual(response.status_code, 302)
        return demo, DemoSelection.objects.get(submission_token=values["submission_token"]), response.url, values

    def test_all_seven_categories_keep_preferences_through_validation_lead_case_and_export(self):
        staff = get_user_model().objects.create_user(username="path-staff", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_lead"))
        expected = {"ecommerce": "ecommerce", "jewelry": "ecommerce", "clinic": "webapp",
                    "education": "webapp", "restaurant": "website", "corporate": "website", "portfolio": "website"}
        for category, request_type in expected.items():
            cache.clear()
            demo, selection, url, _ = self.selection(category)
            page = self.client.get(url)
            self.assertEqual(page.context["form"].initial["request_type"], request_type)
            self.assertEqual(page.context["form"].initial["timeline"], "flexible")
            self.assertContains(page, "#123abc")
            self.assertEqual(len(page.context["demo_summary"]["brief"]), 4)
            invalid = self.client.post(url, {**self.payload, "message": ""})
            self.assertEqual(invalid.status_code, 200)
            self.assertEqual(invalid.context["demo_summary"], page.context["demo_summary"])
            self.assertEqual(invalid.context["form"]["email_or_telegram"].value(), "qa@example.test")
            submitted = self.client.post(url, {**self.payload, "request_type": request_type})
            self.assertEqual(submitted.status_code, 302)
            lead = Lead.objects.get(demo_selection=selection)
            case = CustomerCase.objects.get(kind="lead", source_object_id=lead.pk)
            document = CaseDocument.objects.get(case=case, title="انتخاب دمو")
            self.assertEqual(document.snapshot, build_demo_selection_snapshot(selection))
            self.assertEqual(selection.selections["brief"]["goal"], GOALS[category][0][0])
            self.client.force_login(staff)
            detail = self.client.get(reverse("management_portal:request_detail", args=["lead", lead.pk]))
            export = self.client.get(reverse("management_portal:request_export", args=["lead", lead.pk]) + "?download=1")
            self.assertContains(detail, "#123abc")
            self.assertIn("#123abc", export.content.decode())
            for private in (str(selection.public_token), selection.session_key, selection.submission_token):
                self.assertNotIn(private, detail.content.decode())
                self.assertNotIn(private, export.content.decode())
            self.client.logout()

    def test_english_summary_is_localized_and_editor_link_restores_exact_choices(self):
        demo, selection, url, _ = self.selection(lang="en")
        page = self.client.get(url)
        summary = page.context["demo_summary"]
        self.assertIsNone(re.search(r"[\u0600-\u06ff]", str(summary)))
        self.assertIn("Table reservations", summary["features"])
        alternate = self.client.get(page.context["language_switch_url"])
        self.assertEqual(alternate.context["demo_summary"]["theme"], "رنگ دلخواه (#123abc)")
        self.assertEqual(alternate.context["demo_summary"]["features"], ["رزرو میز", "مقاله و محتوا"])
        query = parse_qs(urlsplit(page.context["demo_edit_url"]).query, keep_blank_values=True)
        self.assertEqual(query["color"], ["#123abc"])
        self.assertEqual(query["personality"], ["industrial"])
        self.assertEqual(query["brand"], ["QA Atelier"])
        for key, value in selection.selections["brief"].items():
            self.assertEqual(query["brief_" + key], [value])
        for private in (str(selection.public_token), selection.session_key, selection.submission_token):
            self.assertNotIn(private, page.context["demo_edit_url"])

    def test_language_switch_is_tab_specific_and_cannot_resume_in_another_session(self):
        _, first, url, _ = self.selection("restaurant")
        first_page = self.client.get(url)
        alternate_url = first_page.context["language_switch_url"]
        _, second, second_url, _ = self.selection("jewelry")
        self.client.get(second_url)
        resumed = self.client.get(alternate_url)
        self.assertEqual(resumed.context["demo_summary"]["category"], "Restaurant & cafe")
        self.assertNotIn(str(first.public_token), resumed.content.decode())
        self.client.logout()
        foreign = self.client.get(alternate_url)
        self.assertNotIn("demo_summary", foreign.context)
        self.assertTrue(foreign.context["demo_link_invalid"])

    def test_empty_features_are_explicit_in_edit_and_stale_retry_links(self):
        demo, selection, url, values = self.selection(empty=True)
        page = self.client.get(url)
        query = parse_qs(urlsplit(page.context["demo_edit_url"]).query, keep_blank_values=True)
        self.assertEqual(query["features"], [""])
        self.assertContains(page, "بدون امکانات اضافی")
        stale = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {**values, "personality": "modern"})
        query = parse_qs(urlsplit(stale.url).query, keep_blank_values=True)
        self.assertEqual(query["features"], [""])
        self.assertEqual(DemoSelection.objects.count(), 1)

    def test_foreign_token_has_no_summary_or_editor_link(self):
        _, selection, url, _ = self.selection()
        self.client.logout()
        page = self.client.get(url)
        self.assertNotIn("demo_summary", page.context)
        self.assertNotIn("demo_edit_url", page.context)
        self.assertContains(page, "انتخاب دموی شما ذخیره نشد")
        submitted = self.client.post(url, self.payload)
        self.assertEqual(submitted.status_code, 302)
        self.assertIsNone(Lead.objects.get().demo_selection_id)

    def test_summary_and_edit_url_do_not_trust_extra_stored_keys_or_html(self):
        _, selection, url, _ = self.selection()
        selection.selections["brand"] = '<script>alert("qa")</script>'
        selection.selections["brief"]["session_key"] = "MUST_NOT_LEAK"
        selection.selections["custom_color"] = "MUST_NOT_LEAK"
        selection.save()
        page = self.client.get(url)
        self.assertNotContains(page, '<script>alert("qa")</script>')
        self.assertNotContains(page, "MUST_NOT_LEAK")
        self.assertNotIn("session_key", page.context["demo_edit_url"])

    def test_authenticated_customer_replay_keeps_one_lead_and_snapshot(self):
        user = get_user_model().objects.create_user(username="path-customer")
        self.client.force_login(user)
        _, selection, url, _ = self.selection()
        page = self.client.get(url)
        payload = {**self.payload, "final_submission_token": page.context["final_submission_token"]}
        first = self.client.post(url, payload)
        replay = self.client.post(url, payload)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(replay.url, first.url)
        self.assertEqual(Lead.objects.filter(demo_selection=selection).count(), 1)

    def test_account_continuation_preserves_frozen_choices_without_reconstructing_live_fk(self):
        user = get_user_model().objects.create_user(username="path-resume")
        self.client.force_login(user)
        _, selection, url, _ = self.selection()
        self.client.get(url)  # authorized attach
        frozen = build_demo_selection_snapshot(selection)
        self.client.logout()
        self.client.force_login(user)  # a different authenticated session
        contact = reverse("leads:contact")
        page = self.client.get(contact)
        self.assertContains(page, "#123abc")
        self.assertNotIn("demo_edit_url", page.context)
        self.assertNotContains(page, str(selection.public_token))
        payload = {**self.payload, "final_submission_token": page.context["final_submission_token"]}
        submitted = self.client.post(contact, payload)
        self.assertEqual(submitted.status_code, 302)
        lead = Lead.objects.get()
        self.assertIsNone(lead.demo_selection_id)
        document = CaseDocument.objects.get(case__kind="lead", case__source_object_id=lead.pk, title="انتخاب دمو")
        self.assertEqual(document.snapshot, frozen)
        replay = self.client.post(contact, payload)
        self.assertEqual(replay.url, submitted.url)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(CaseDocument.objects.filter(pk=document.pk).count(), 1)
        staff = get_user_model().objects.create_user(username="resume-staff", email="resume-staff@example.test", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_lead"))
        self.client.force_login(staff)
        detail = self.client.get(reverse("management_portal:request_detail", args=["lead", lead.pk]))
        self.assertContains(detail, "#123abc")
        self.assertContains(detail, "رزرو میز")
        for lang in ("fa", "en"):
            for value in ("only", "restaurant"):
                listing = self.client.get("/" + lang + reverse("management_portal:request_list")[3:] + "?demo=" + value)
                with self.subTest(language=lang, demo_filter=value):
                    self.assertContains(listing, lead.tracking_code)
                    self.assertContains(listing, escape(frozen[f"category_{lang}"]))
        export = self.client.get(reverse("management_portal:request_export", args=["lead", lead.pk]) + "?download=1")
        self.assertIn("#123abc", export.content.decode())

    def test_frozen_document_failure_rolls_back_the_submission_and_allows_retry(self):
        from leads.models import FormDraft
        user = get_user_model().objects.create_user(username="path-rollback")
        self.client.force_login(user)
        _, _, url, _ = self.selection()
        self.client.get(url)
        self.client.logout()
        self.client.force_login(user)
        contact = reverse("leads:contact")
        page = self.client.get(contact)
        payload = {**self.payload, "final_submission_token": page.context["final_submission_token"]}
        with patch("management_portal.cases.sync_demo_snapshot_document", side_effect=RuntimeError("QA injected error")):
            with self.assertRaises(RuntimeError):
                self.client.post(contact, payload)
        self.assertFalse(Lead.objects.exists())
        self.assertFalse(CustomerCase.objects.filter(kind="lead").exists())
        self.assertEqual(FormDraft.objects.get(owner=user).status, "open")
        retry = self.client.post(contact, payload)
        self.assertEqual(retry.status_code, 302)

    def test_unrelated_account_cannot_see_or_submit_another_accounts_snapshot(self):
        user = get_user_model().objects.create_user(username="path-owner")
        other = get_user_model().objects.create_user(username="path-other", email="path-other@example.test")
        self.client.force_login(user)
        _, _, url, _ = self.selection()
        self.client.get(url)
        self.client.logout()
        self.client.force_login(other)
        page = self.client.get(reverse("leads:contact"))
        self.assertNotIn("demo_summary", page.context)
        submitted = self.client.post(reverse("leads:contact"), {**self.payload,
            "final_submission_token": page.context["final_submission_token"]})
        self.assertEqual(submitted.status_code, 302)
        self.assertFalse(CaseDocument.objects.filter(title="انتخاب دمو").exists())

    def test_explicit_invalid_demo_does_not_silently_use_older_account_snapshot(self):
        user = get_user_model().objects.create_user(username="path-invalid")
        self.client.force_login(user)
        _, _, url, _ = self.selection()
        self.client.get(url)
        invalid_url = reverse("leads:contact") + "?demo=invalid"
        page = self.client.get(invalid_url)
        self.assertNotIn("demo_summary", page.context)
        submitted = self.client.post(invalid_url, {**self.payload,
            "final_submission_token": page.context["final_submission_token"]})
        self.assertEqual(submitted.status_code, 302)
        self.assertFalse(CaseDocument.objects.filter(title="انتخاب دمو").exists())
