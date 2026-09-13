import json
import threading
import unittest
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from leads.form_draft_service import save_draft_fields
from leads.models import FormDraft
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection, DemoTemplate

User = get_user_model()

DRAFT_URL = reverse("leads:draft")
DRAFT_DELETE_URL = reverse("leads:draft_delete")


def make_customer(suffix="a"):
    return User.objects.create_user(
        username=f"draft-api-customer-{suffix}@example.com", email=f"draft-api-customer-{suffix}@example.com",
        password="x", is_active=True,
    )


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


class FormDraftGetViewTests(TestCase):
    def test_no_draft_returns_null(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = client.get(DRAFT_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"draft": None})
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_owner_sees_only_their_own_safe_data(self):
        customer = make_customer()
        save_draft_fields(owner=customer, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=1, expected_revision=0)
        client = Client()
        client.force_login(customer)

        response = client.get(DRAFT_URL)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["draft"]["fields"], {"request_type": "webapp"})
        self.assertEqual(body["draft"]["current_step"], 1)
        self.assertEqual(body["draft"]["revision"], 1)
        self.assertEqual(body["draft"]["status"], "open")
        self.assertNotIn("owner", body["draft"])
        self.assertNotIn("id", body["draft"])

    def test_anonymous_gets_json_401_not_a_redirect(self):
        client = Client()
        response = client.get(DRAFT_URL)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["Content-Type"].split(";")[0], "application/json")
        body = response.json()
        self.assertEqual(body["code"], "unauthenticated")

    def test_staff_gets_json_403_and_no_write(self):
        staff = User.objects.create_user(
            username="draft-api-staff@example.com", email="draft-api-staff@example.com",
            password="x", is_active=True, is_staff=True,
        )
        client = Client()
        client.force_login(staff)

        response = client.get(DRAFT_URL)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "staff_or_superuser_not_allowed")
        self.assertEqual(FormDraft.objects.filter(owner=staff).count(), 0)

    def test_superuser_gets_json_403(self):
        superuser = User.objects.create_superuser(
            username="draft-api-superuser@example.com", email="draft-api-superuser@example.com", password="x",
        )
        client = Client()
        client.force_login(superuser)

        response = client.get(DRAFT_URL)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "staff_or_superuser_not_allowed")

    def test_user_a_cannot_read_user_bs_draft(self):
        customer_a = make_customer("a")
        customer_b = make_customer("b")
        save_draft_fields(owner=customer_b, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer_a)

        response = client.get(DRAFT_URL)

        self.assertEqual(response.json(), {"draft": None})

    def test_expired_draft_is_not_returned(self):
        customer = make_customer()
        draft, _ = save_draft_fields(owner=customer, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        FormDraft.objects.filter(pk=draft.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        client = Client()
        client.force_login(customer)

        response = client.get(DRAFT_URL)

        self.assertEqual(response.json(), {"draft": None})

    def test_get_issues_no_write_and_no_row_lock(self):
        customer = make_customer()
        save_draft_fields(owner=customer, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer)

        with mock.patch(
            "django.db.models.QuerySet.select_for_update",
            side_effect=AssertionError("GET must never call select_for_update"),
        ):
            with CaptureQueriesContext(connection) as ctx:
                response = client.get(DRAFT_URL)

        self.assertEqual(response.status_code, 200)
        statements = [q["sql"].strip().upper() for q in ctx.captured_queries]
        self.assertTrue(statements)
        for sql in statements:
            self.assertFalse(sql.startswith("UPDATE"), sql)
            self.assertFalse(sql.startswith("INSERT"), sql)
            self.assertFalse(sql.startswith("DELETE"), sql)

    def test_invalid_http_methods_are_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = client.put(DRAFT_URL, data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 405)
        self.assertIn("Allow", response)

        response = client.delete(DRAFT_URL)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Allow", response)

    def test_no_forbidden_tokens_in_response_when_a_snapshot_is_attached(self):
        customer = make_customer()
        template = DemoTemplate.objects.create(
            slug="draft-api-get-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="draft-api-get-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        from leads.form_draft_service import ensure_active_draft_with_demo_snapshot
        ensure_active_draft_with_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)

        client = Client()
        client.force_login(customer)
        response = client.get(DRAFT_URL)

        serialized = response.content.decode()
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn(selection.session_key, serialized)
        self.assertNotIn("submission_token", serialized)
        self.assertNotIn("session_key", serialized)
        self.assertNotIn("public_token", serialized)
        self.assertEqual(response.json()["draft"]["demo_snapshot"], build_demo_selection_snapshot(selection))


class FormDraftPostViewTests(TestCase):
    def test_initial_creation_returns_201_and_revision_one(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 1, "expected_revision": 0})

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["draft"]["revision"], 1)
        self.assertEqual(body["draft"]["fields"], {"request_type": "webapp"})
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_correct_update_returns_200_and_bumps_revision(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        created = post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 0, "expected_revision": 0}).json()

        response = post_json(client, DRAFT_URL, {
            "fields": {"request_type": "website"}, "current_step": 1, "expected_revision": created["draft"]["revision"],
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["revision"], created["draft"]["revision"] + 1)
        self.assertEqual(body["draft"]["fields"], {"request_type": "website"})

    def test_identical_save_is_idempotent(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        created = post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 1, "expected_revision": 0}).json()

        response = post_json(client, DRAFT_URL, {
            "fields": {"request_type": "webapp"}, "current_step": 1, "expected_revision": created["draft"]["revision"],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["draft"]["revision"], created["draft"]["revision"])

    def test_stale_expected_revision_returns_409_without_overwriting(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 0, "expected_revision": 0})

        response = post_json(client, DRAFT_URL, {"fields": {"request_type": "website"}, "current_step": 2, "expected_revision": 999})

        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["code"], "conflict")
        self.assertEqual(body["draft"]["fields"], {"request_type": "webapp"})
        self.assertEqual(body["draft"]["current_step"], 0)

    def test_conflict_response_only_ever_contains_the_requesters_own_draft(self):
        customer_a = make_customer("a")
        customer_b = make_customer("b")
        save_draft_fields(owner=customer_b, form_type="leads_contact", fields={"request_type": "consultation"}, current_step=0, expected_revision=0)
        mine, _ = save_draft_fields(owner=customer_a, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=0, expected_revision=0)

        client = Client()
        client.force_login(customer_a)
        response = post_json(client, DRAFT_URL, {"fields": {}, "current_step": 0, "expected_revision": 999})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["draft"]["fields"], {"request_type": "webapp"})

    def test_unknown_and_forbidden_fields_are_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_URL, {"fields": {"totally_made_up": "x"}, "current_step": 0, "expected_revision": 0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "unknown_field")

        response = post_json(client, DRAFT_URL, {"fields": {"phone": "0912"}, "current_step": 0, "expected_revision": 0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "forbidden_field")

        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)

    def test_demo_snapshot_and_other_forbidden_top_level_keys_are_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        for bad_payload in [
            {"fields": {}, "current_step": 0, "expected_revision": 0, "demo_snapshot": {"brand": "x"}},
            {"fields": {}, "current_step": 0, "expected_revision": 0, "status": "submitted"},
            {"fields": {}, "current_step": 0, "expected_revision": 0, "owner": 1},
            {"fields": {}, "current_step": 0, "expected_revision": 0, "submitted_lead": 1},
            {"fields": {}, "current_step": 0, "expected_revision": 0, "expires_at": "2099-01-01T00:00:00Z"},
        ]:
            response = post_json(client, DRAFT_URL, bad_payload)
            self.assertEqual(response.status_code, 400, bad_payload)
            self.assertEqual(response.json()["code"], "invalid_payload_keys")

        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)

    def test_malformed_json_and_non_object_body_are_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = client.post(DRAFT_URL, data="{not valid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_json")

        response = client.post(DRAFT_URL, data=json.dumps([1, 2, 3]), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_payload")

        response = client.post(DRAFT_URL, data=json.dumps("just a string"), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_payload")

    def test_oversized_body_is_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        huge_payload = {"fields": {}, "current_step": 0, "expected_revision": 0, "padding": "x" * 20_000}

        response = client.post(DRAFT_URL, data=json.dumps(huge_payload), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "payload_too_large")

    def test_wrong_content_type_is_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = client.post(DRAFT_URL, data=json.dumps({"fields": {}, "current_step": 0, "expected_revision": 0}), content_type="text/plain")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_content_type")

    def test_out_of_range_current_step_and_invalid_service_id_are_rejected(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_URL, {"fields": {}, "current_step": 99, "expected_revision": 0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_current_step")

        response = post_json(client, DRAFT_URL, {"fields": {"service_id": 999999}, "current_step": 0, "expected_revision": 0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_field_value")

    def test_anonymous_gets_json_401_and_no_write(self):
        client = Client()
        response = post_json(client, DRAFT_URL, {"fields": {}, "current_step": 0, "expected_revision": 0})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(FormDraft.objects.count(), 0)

    def test_staff_gets_json_403_and_no_write(self):
        staff = User.objects.create_user(
            username="draft-api-post-staff@example.com", email="draft-api-post-staff@example.com",
            password="x", is_active=True, is_staff=True,
        )
        client = Client()
        client.force_login(staff)

        response = post_json(client, DRAFT_URL, {"fields": {}, "current_step": 0, "expected_revision": 0})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(FormDraft.objects.filter(owner=staff).count(), 0)

    def test_invalid_http_methods_return_405_with_allow_header(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        response = client.patch(DRAFT_URL)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Allow", response)

    def test_expired_draft_recreates_with_expected_revision_zero(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        created = post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 0, "expected_revision": 0}).json()
        stale_pk = FormDraft.objects.get(owner=customer).pk
        FormDraft.objects.filter(pk=stale_pk).update(expires_at=timezone.now() - timedelta(seconds=1))

        response = post_json(client, DRAFT_URL, {"fields": {"request_type": "website"}, "current_step": 0, "expected_revision": 0})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["draft"]["revision"], 1)
        stale = FormDraft.objects.get(pk=stale_pk)
        self.assertEqual(stale.status, "expired")

    def test_save_preserves_a_previously_attached_demo_snapshot(self):
        customer = make_customer()
        template = DemoTemplate.objects.create(
            slug="draft-api-post-demo", category="ecommerce",
            title_fa="دموی فروشگاهی", title_en="Storefront demo",
            tagline_fa="فرضی", tagline_en="Fictional",
            fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
            style_key="minimal",
        )
        selection = DemoSelection.objects.create(
            template=template, session_key="draft-api-post-session",
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        from leads.form_draft_service import ensure_active_draft_with_demo_snapshot
        draft = ensure_active_draft_with_demo_snapshot(owner=customer, form_type="leads_contact", demo_selection=selection)

        client = Client()
        client.force_login(customer)
        response = post_json(client, DRAFT_URL, {"fields": {"request_type": "webapp"}, "current_step": 1, "expected_revision": draft.revision})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["draft"]["demo_snapshot"], build_demo_selection_snapshot(selection))

    def test_csrf_is_actually_enforced(self):
        customer = make_customer()
        client = Client(enforce_csrf_checks=True)
        client.force_login(customer)

        response = post_json(client, DRAFT_URL, {"fields": {}, "current_step": 0, "expected_revision": 0})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)


class FormDraftDeleteViewTests(TestCase):
    def test_correct_revision_deletes(self):
        customer = make_customer()
        draft, _ = save_draft_fields(owner=customer, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft.revision})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": True})
        self.assertEqual(FormDraft.objects.filter(pk=draft.pk).count(), 0)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_deleting_twice_is_idempotent(self):
        customer = make_customer()
        draft, _ = save_draft_fields(owner=customer, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer)
        post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft.revision})

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft.revision})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": False})

    def test_deleting_when_none_exists_is_idempotent(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": 0})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": False})

    def test_stale_revision_conflicts_without_deleting(self):
        customer = make_customer()
        draft, _ = save_draft_fields(owner=customer, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer)

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft.revision + 1})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["draft"]["fields"], {"request_type": "webapp"})
        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())

    def test_cannot_select_another_owners_draft_by_id_or_owner(self):
        customer_a = make_customer("a")
        customer_b = make_customer("b")
        draft_b, _ = save_draft_fields(owner=customer_b, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        client = Client()
        client.force_login(customer_a)

        # The delete payload has no id/owner field at all to even attempt
        # this with — confirmed structurally by the strict key-set check.
        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft_b.revision, "draft_id": draft_b.pk})

        self.assertEqual(response.status_code, 400)
        self.assertTrue(FormDraft.objects.filter(pk=draft_b.pk).exists())

    def test_anonymous_gets_json_401(self):
        client = Client()
        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": 0})
        self.assertEqual(response.status_code, 401)

    def test_staff_gets_json_403_and_no_write(self):
        staff = User.objects.create_user(
            username="draft-api-delete-staff@example.com", email="draft-api-delete-staff@example.com",
            password="x", is_active=True, is_staff=True,
        )
        client = Client()
        client.force_login(staff)

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": 0})

        self.assertEqual(response.status_code, 403)

    def test_invalid_http_methods_return_405(self):
        customer = make_customer()
        client = Client()
        client.force_login(customer)
        response = client.get(DRAFT_DELETE_URL)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Allow", response)

    def test_csrf_is_actually_enforced(self):
        customer = make_customer()
        draft, _ = save_draft_fields(owner=customer, form_type="leads_contact", fields={}, current_step=0, expected_revision=0)
        client = Client(enforce_csrf_checks=True)
        client.force_login(customer)

        response = post_json(client, DRAFT_DELETE_URL, {"expected_revision": draft.revision})

        self.assertEqual(response.status_code, 403)
        self.assertTrue(FormDraft.objects.filter(pk=draft.pk).exists())


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "Genuine row-lock concurrency can only be demonstrated on a real database engine; skipped on SQLite.",
)
class FormDraftApiPostgresConcurrencyTests(TransactionTestCase):
    def test_concurrent_saves_with_the_same_expected_revision_converge_to_one_winner(self):
        customer = User.objects.create_user(
            username="draft-api-race@example.com", email="draft-api-race@example.com", password="x", is_active=True,
        )
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=0, expected_revision=0,
        )
        shared_expected_revision = draft.revision

        barrier = threading.Barrier(2)
        outcomes = []

        def attempt(request_type):
            try:
                barrier.wait(timeout=5)
                with transaction.atomic():
                    updated, _ = save_draft_fields(
                        owner=customer, form_type="leads_contact", fields={"request_type": request_type},
                        current_step=1, expected_revision=shared_expected_revision,
                    )
                outcomes.append(("ok", updated.revision))
            except Exception as exc:
                outcomes.append(("error", exc))
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt, args=(rt,)) for rt in ("website", "ecommerce")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        for thread in threads:
            self.assertFalse(thread.is_alive(), "a thread is still running — possible deadlock or hang")

        from leads.form_draft_service import DraftConflictError

        successes = [o for o in outcomes if o[0] == "ok"]
        conflicts = [o for o in outcomes if o[0] == "error" and isinstance(o[1], DraftConflictError)]
        other_errors = [o for o in outcomes if o[0] == "error" and not isinstance(o[1], DraftConflictError)]

        self.assertEqual(other_errors, [], other_errors)
        self.assertEqual(len(successes), 1, outcomes)
        self.assertEqual(len(conflicts), 1, outcomes)

        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 1)
        survivor = FormDraft.objects.get(owner=customer)
        self.assertEqual(survivor.revision, shared_expected_revision + 1)
        self.assertIn(survivor.fields["request_type"], ("website", "ecommerce"))
