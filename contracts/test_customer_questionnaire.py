import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User

from .models import (
    ContractProposal,
    ContractRoomAcknowledgement,
    RoomAccessGrant,
    RoomEvent,
    SpecialistAssignment,
    SpecialistFormTemplate,
    SpecialistFormTemplateVersion,
)
from .questionnaires import completion
from .services import add_default_clauses, publish_version


class CustomerQuestionnaireTests(TestCase):
    schema = [
        {
            "key": "organisation",
            "title": "شناخت مجموعه",
            "description": "وضعیت فعلی مجموعه را شرح دهید.",
            "questions": [
                {
                    "key": "summary",
                    "label": "فرآیند فعلی چگونه است؟",
                    "help_text": "یک نمونه واقعی از شروع تا پایان بنویسید.",
                    "type": "long_text",
                    "required": True,
                    "choices": [],
                    "placeholder": "مثلاً درخواست مشتری ابتدا ثبت می‌شود…",
                },
                {
                    "key": "team",
                    "label": "تیم درگیر چند نفر است؟",
                    "help_text": "",
                    "type": "short_text",
                    "required": False,
                    "choices": [],
                    "placeholder": "",
                },
            ],
        },
        {
            "key": "goals",
            "title": "هدف‌های پروژه",
            "description": "مهم‌ترین اولویت را مشخص کنید.",
            "questions": [
                {
                    "key": "priority",
                    "label": "اولویت اصلی چیست؟",
                    "help_text": "گزینه نزدیک‌تر به هدف اصلی را انتخاب کنید.",
                    "type": "single_choice",
                    "required": True,
                    "choices": ["سرعت", "شفافیت"],
                    "placeholder": "",
                },
            ],
        },
    ]

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="workspace-owner",
            email="workspace@example.com",
            password="safe-password",
        )
        self.proposal = ContractProposal.objects.create(
            customer_name="مشتری فرم تخصصی",
            customer_phone="989120373271",
            project_title="سامانه یکپارچه مشتری",
            project_scope="تحلیل و اجرای سامانه",
            amount_irr=1_500_000_000,
            delivery_terms="۸ هفته",
            general_terms="ماده ۱ ـ شرایط عمومی\n۱-۱. متن عمومی",
            private_terms="ماده ۱ ـ شرایط خصوصی\n۱-۱. متن خصوصی",
            created_by=self.user,
        )
        add_default_clauses(self.proposal)
        template = SpecialistFormTemplate.objects.create(
            name="فرم تخصصی پروژه نمونه",
            slug="sample-project-specialist",
            service_kind="general",
        )
        template_version = SpecialistFormTemplateVersion.objects.create(
            template=template,
            number=1,
            schema=self.schema,
            created_by=self.user,
        )
        template.current_version = template_version
        template.save(update_fields=("current_version", "updated_at"))
        self.assignment = SpecialistAssignment.objects.create(
            proposal=self.proposal,
            version=template_version,
            progress=completion(template_version.schema, {}),
        )
        self.version = publish_version(self.proposal, self.user)
        self.grant = RoomAccessGrant(
            proposal=self.proposal,
            authorized_phone=self.proposal.customer_phone,
            created_by=self.user,
        )
        self.grant.set_password("A-strong-room-password")
        self.grant.save()
        self._authenticate(self.client)

    def _authenticate(self, client):
        session = client.session
        session[f"contract-access:{self.version.pk}"] = (
            f"grant:{self.grant.pk}:{self.grant.credential_version}"
        )
        session.save()

    def _section_url(self, key):
        return reverse(
            "contracts:customer_questionnaire_section",
            args=[self.proposal.token, key],
        )

    def _autosave(self, client, payload, **extra):
        return client.post(
            reverse("contracts:questionnaire_autosave", args=[self.proposal.token]),
            data=json.dumps(payload),
            content_type="application/json",
            **extra,
        )

    def test_customer_can_sign_in_with_the_per_workspace_hashed_credential(self):
        client = Client()
        response = client.post(
            reverse("contracts:contract_access", args=[self.proposal.token]),
            {"phone": "09120373271", "password": "A-strong-room-password"},
        )

        self.assertRedirects(
            response,
            reverse("contracts:public_contract", args=[self.proposal.token]),
        )
        marker = client.session[f"contract-access:{self.version.pk}"]
        self.assertEqual(
            marker,
            f"grant:{self.grant.pk}:{self.grant.credential_version}",
        )
        self.grant.refresh_from_db()
        self.assertIsNotNone(self.grant.last_login_at)
        self.assertTrue(
            RoomEvent.objects.filter(
                proposal=self.proposal,
                access_grant=self.grant,
                event_type="login_succeeded",
            ).exists()
        )

    @override_settings(CONTRACT_ACCESS_PASSWORD="legacy-shared-password")
    def test_global_legacy_password_cannot_bypass_a_workspace_grant(self):
        client = Client()
        response = client.post(
            reverse("contracts:contract_access", args=[self.proposal.token]),
            {"phone": "09120373271", "password": "legacy-shared-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "شماره همراه یا رمز ورود صحیح نیست")
        self.assertNotIn(f"contract-access:{self.version.pk}", client.session)
        self.assertTrue(
            RoomEvent.objects.filter(
                proposal=self.proposal,
                event_type="login_failed",
            ).exists()
        )

    def test_entry_resumes_at_first_incomplete_section_and_is_private(self):
        entry = reverse("contracts:customer_questionnaire", args=[self.proposal.token])
        response = self.client.get(entry)
        self.assertRedirects(response, self._section_url("organisation"))

        response = self.client.get(self._section_url("organisation"))
        self.assertContains(response, "پاسخ‌ها هنگام نوشتن روی سرور ذخیره می‌شوند")
        self.assertContains(response, "فرآیند فعلی چگونه است؟")
        self.assertIn("private", response.headers["Cache-Control"])
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(response.headers["Pragma"], "no-cache")

    def test_sections_are_sequential_and_normal_submit_updates_progress(self):
        blocked = self.client.get(self._section_url("goals"))
        self.assertRedirects(blocked, self._section_url("organisation"))

        response = self.client.post(self._section_url("organisation"), {
            "revision": "0",
            "summary": "درخواست مشتری ثبت و سپس توسط مدیر بررسی می‌شود.",
            "team": "شش نفر",
        })
        self.assertRedirects(response, self._section_url("goals"))
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.revision, 1)
        self.assertEqual(self.assignment.status, "draft")
        self.assertEqual(
            self.assignment.answers["organisation"]["team"],
            "شش نفر",
        )
        self.assertTrue(RoomEvent.objects.filter(
            proposal=self.proposal,
            assignment=self.assignment,
            event_type="form_saved",
        ).exists())

        response = self.client.post(self._section_url("goals"), {
            "revision": "1",
            "priority": "شفافیت",
        })
        self.assertRedirects(
            response,
            reverse("contracts:public_contract", args=[self.proposal.token]),
        )
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.status, "submitted")
        self.assertEqual(self.assignment.progress["percent"], 100)
        self.assertIsNotNone(self.assignment.submitted_at)
        self.assertEqual(RoomEvent.objects.filter(
            proposal=self.proposal,
            event_type="form_submitted",
        ).count(), 1)

    def test_autosave_resumes_on_another_device_and_rejects_stale_revision(self):
        first = self._autosave(self.client, {
            "section": "organisation",
            "field": "summary",
            "value": "پاسخ ذخیره‌شده روی سرور",
            "revision": 0,
        })
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["revision"], 1)

        second_device = Client()
        self._authenticate(second_device)
        resumed = second_device.get(self._section_url("organisation"))
        self.assertContains(resumed, "پاسخ ذخیره‌شده روی سرور")

        conflict = self._autosave(second_device, {
            "section": "organisation",
            "field": "summary",
            "value": "نباید جایگزین شود",
            "revision": 0,
        })
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["code"], "revision_conflict")
        self.assertEqual(conflict.json()["server_value"], "پاسخ ذخیره‌شده روی سرور")
        self.assignment.refresh_from_db()
        self.assertEqual(
            self.assignment.answers["organisation"]["summary"],
            "پاسخ ذخیره‌شده روی سرور",
        )
        self.assertTrue(RoomEvent.objects.filter(
            proposal=self.proposal,
            event_type="form_conflict",
        ).exists())

        stale_submit = second_device.post(self._section_url("organisation"), {
            "revision": "0",
            "summary": "پاسخ قدیمی صفحه",
            "team": "",
        })
        self.assertEqual(stale_submit.status_code, 409)
        self.assertContains(stale_submit, "نسخه جدیدتری روی سرور وجود دارد", status_code=409)
        self.assertNotContains(stale_submit, "ذخیره و رفتن به بخش بعد", status_code=409)
        self.assignment.refresh_from_db()
        self.assertEqual(
            self.assignment.answers["organisation"]["summary"],
            "پاسخ ذخیره‌شده روی سرور",
        )

    def test_autosave_rejects_unknown_and_oversized_payloads(self):
        out_of_sequence = self._autosave(self.client, {
            "section": "goals",
            "field": "priority",
            "value": "شفافیت",
            "revision": 0,
        })
        self.assertEqual(out_of_sequence.status_code, 403)
        self.assertEqual(out_of_sequence.json()["code"], "section_locked")

        unknown = self._autosave(self.client, {
            "section": "organisation",
            "field": "injected_field",
            "value": "bad",
            "revision": 0,
        })
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(unknown.json()["code"], "unknown_field")

        extra_key = self._autosave(self.client, {
            "section": "organisation",
            "field": "summary",
            "value": "bad",
            "revision": 0,
            "unexpected": "value",
        })
        self.assertEqual(extra_key.status_code, 400)
        self.assertEqual(extra_key.json()["code"], "invalid_payload")

        oversized = self._autosave(self.client, {
            "section": "organisation",
            "field": "summary",
            "value": "x" * 17_000,
            "revision": 0,
        })
        self.assertEqual(oversized.status_code, 413)
        self.assertEqual(oversized.json()["code"], "payload_too_large")

    def test_acknowledging_a_document_locks_answers_but_keeps_review_available(self):
        saved = self._autosave(self.client, {
            "section": "organisation",
            "field": "summary",
            "value": "پاسخ نهایی",
            "revision": 0,
        })
        self.assertEqual(saved.status_code, 200)
        ContractRoomAcknowledgement.objects.create(
            version=self.version,
            document="general",
        )

        locked_save = self._autosave(self.client, {
            "section": "organisation",
            "field": "summary",
            "value": "تغییر غیرمجاز",
            "revision": 1,
        })
        self.assertEqual(locked_save.status_code, 423)

        locked_submit = self.client.post(self._section_url("organisation"), {
            "revision": "1",
            "summary": "تغییر غیرمجاز",
            "team": "",
        })
        self.assertRedirects(locked_submit, self._section_url("organisation"))
        review = self.client.get(self._section_url("organisation"))
        self.assertContains(review, "پاسخ‌های این نسخه نهایی شده‌اند")
        self.assertContains(review, "disabled", html=False)
        self.assignment.refresh_from_db()
        self.assertEqual(
            self.assignment.answers["organisation"]["summary"],
            "پاسخ نهایی",
        )

    def test_autosave_requires_room_session_and_csrf(self):
        anonymous = Client()
        denied = self._autosave(anonymous, {
            "section": "organisation",
            "field": "summary",
            "value": "پاسخ",
            "revision": 0,
        })
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.json()["code"], "authentication_required")

        csrf_client = Client(enforce_csrf_checks=True)
        self._authenticate(csrf_client)
        page = csrf_client.get(self._section_url("organisation"), secure=True)
        csrf_token = page.cookies["csrftoken"].value
        rejected = self._autosave(csrf_client, {
            "section": "organisation",
            "field": "summary",
            "value": "پاسخ",
            "revision": 0,
        }, secure=True)
        self.assertRedirects(
            rejected,
            reverse("contracts:contract_access", args=[self.proposal.token]),
            fetch_redirect_response=False,
        )
        accepted = self._autosave(csrf_client, {
            "section": "organisation",
            "field": "summary",
            "value": "پاسخ",
            "revision": 0,
        }, secure=True, HTTP_X_CSRFTOKEN=csrf_token, HTTP_REFERER=f"https://testserver{self._section_url('organisation')}")
        self.assertEqual(accepted.status_code, 200)

    def test_contract_room_prefers_generic_assignment_link(self):
        room = self.client.get(
            reverse("contracts:public_contract", args=[self.proposal.token]),
        )
        questionnaire_url = reverse(
            "contracts:customer_questionnaire",
            args=[self.proposal.token],
        )
        self.assertContains(room, f'href="{questionnaire_url}"', html=False)
        self.assertContains(room, "شروع فرم تخصصی")
        self.assertNotContains(room, "این قرارداد فرم تخصصی متصل ندارد")
