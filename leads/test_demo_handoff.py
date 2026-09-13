import unittest
from unittest import mock

from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model, login as auth_login
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest
from django.test import Client, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.db import DatabaseError, connection
from django.urls import reverse

from leads.demo_handoff import (
    FORM_TYPE,
    PENDING_DEMO_SESSION_KEY,
    pop_pending_demo_selection_id,
    store_pending_demo_selection,
)
from leads.form_draft_service import DraftValidationError
from leads.models import FormDraft
from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection, DemoTemplate

User = get_user_model()


def make_session():
    return SessionStore()


def make_template(slug="handoff-demo"):
    return DemoTemplate.objects.create(
        slug=slug, category="ecommerce",
        title_fa="دموی فروشگاهی", title_en="Storefront demo",
        tagline_fa="فرضی", tagline_en="Fictional",
        fictional_brand_fa="برند فرضی", fictional_brand_en="Fictional Brand",
        style_key="minimal",
    )


class PendingDemoMarkerHelperTests(TestCase):
    def setUp(self):
        self.template = make_template()

    def _selection(self, session_key):
        return DemoSelection.objects.create(
            template=self.template, session_key=session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

    def test_store_writes_only_the_internal_id_and_form_type(self):
        session = make_session()
        session.save()
        selection = self._selection(session.session_key)

        request = HttpRequest()
        request.session = session
        store_pending_demo_selection(request, selection)

        marker = session[PENDING_DEMO_SESSION_KEY]
        self.assertEqual(marker, {"demo_selection_id": selection.pk, "form_type": FORM_TYPE})
        serialized = str(marker)
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn(selection.session_key, serialized)

    def test_store_skips_the_write_when_marker_already_matches(self):
        session = make_session()
        session.save()
        selection = self._selection(session.session_key)
        request = HttpRequest()
        request.session = session
        store_pending_demo_selection(request, selection)
        session.save()
        session.modified = False

        store_pending_demo_selection(request, selection)

        self.assertFalse(session.modified)

    def test_pop_returns_the_id_and_removes_the_marker(self):
        session = make_session()
        session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": 42, "form_type": FORM_TYPE}
        request = HttpRequest()
        request.session = session

        result = pop_pending_demo_selection_id(request)

        self.assertEqual(result, 42)
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, session)

    def test_pop_rejects_a_marker_for_a_different_form_type(self):
        session = make_session()
        session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": 42, "form_type": "crm_order"}
        request = HttpRequest()
        request.session = session

        self.assertIsNone(pop_pending_demo_selection_id(request))
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, session)

    def test_pop_rejects_a_malformed_marker(self):
        for bad_marker in ["not-a-dict", {"demo_selection_id": "not-an-int", "form_type": FORM_TYPE}, {"form_type": FORM_TYPE}, {"demo_selection_id": True, "form_type": FORM_TYPE}]:
            session = make_session()
            session[PENDING_DEMO_SESSION_KEY] = bad_marker
            request = HttpRequest()
            request.session = session
            self.assertIsNone(pop_pending_demo_selection_id(request))

    def test_pop_returns_none_when_absent(self):
        session = make_session()
        request = HttpRequest()
        request.session = session
        self.assertIsNone(pop_pending_demo_selection_id(request))


class ContactViewDemoHandoffTests(TestCase):
    def setUp(self):
        self.template = make_template(slug="contact-view-demo")

    def _make_selection_for_a_fresh_client_session(self, client):
        session = client.session
        session["marker-init"] = True
        session.save()
        return DemoSelection.objects.create(
            template=self.template, session_key=session.session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

    def test_anonymous_visit_with_valid_demo_stores_a_pending_marker(self):
        client = Client()
        selection = self._make_selection_for_a_fresh_client_session(client)

        response = client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")

        self.assertEqual(response.status_code, 200)
        marker = client.session[PENDING_DEMO_SESSION_KEY]
        self.assertEqual(marker, {"demo_selection_id": selection.pk, "form_type": "leads_contact"})
        serialized = str(client.session.load())
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn(selection.session_key, serialized)

    def test_invalid_or_foreign_token_never_creates_or_overwrites_a_marker(self):
        client = Client()
        selection = self._make_selection_for_a_fresh_client_session(client)
        client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")
        original_marker = dict(client.session[PENDING_DEMO_SESSION_KEY])

        other_template = make_template(slug="foreign-demo")
        foreign = DemoSelection.objects.create(
            template=other_template, session_key="some-other-session",
            selections={"theme": "warm", "personality": "minimal", "features": []},
        )
        client.get(reverse("leads:contact") + f"?lang=fa&demo={foreign.public_token}")
        client.get(reverse("leads:contact") + "?lang=fa&demo=not-a-real-token")

        self.assertEqual(client.session[PENDING_DEMO_SESSION_KEY], original_marker)

    def test_no_duplicate_demo_selection_query_per_request(self):
        client = Client()
        selection = self._make_selection_for_a_fresh_client_session(client)

        with CaptureQueriesContext(connection) as ctx:
            client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")

        demo_queries = [q for q in ctx.captured_queries if "projects_demoselection" in q["sql"]]
        self.assertEqual(len(demo_queries), 1, demo_queries)

    def test_authenticated_non_staff_customer_gets_the_snapshot_synced_immediately(self):
        customer = User.objects.create_user(
            username="contact-customer@example.com", email="contact-customer@example.com",
            password="x", is_active=True,
        )
        client = Client()
        client.force_login(customer)
        selection = self._make_selection_for_a_fresh_client_session(client)

        client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")

        draft = FormDraft.objects.get(owner=customer)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "contact-view-demo")
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)

        # A second visit is idempotent: still exactly one draft.
        client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 1)

    def test_staff_visiting_with_a_demo_link_gets_no_draft_and_no_marker(self):
        staff = User.objects.create_user(
            username="contact-staff@example.com", email="contact-staff@example.com",
            password="x", is_active=True, is_staff=True,
        )
        client = Client()
        client.force_login(staff)
        selection = self._make_selection_for_a_fresh_client_session(client)

        client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")

        self.assertEqual(FormDraft.objects.filter(owner=staff).count(), 0)
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)

    def test_authenticated_customer_cannot_attach_another_sessions_demo_selection(self):
        customer = User.objects.create_user(
            username="contact-crosssession@example.com", email="contact-crosssession@example.com",
            password="x", is_active=True,
        )
        foreign = DemoSelection.objects.create(
            template=self.template, session_key="a-completely-different-session",
            selections={"theme": "warm", "personality": "minimal", "features": []},
        )
        client = Client()
        client.force_login(customer)

        client.get(reverse("leads:contact") + f"?lang=fa&demo={foreign.public_token}")

        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 0)


class LoginSignalHandoffTests(TestCase):
    def setUp(self):
        self.template = make_template(slug="login-signal-demo")

    def _pending_session_with_selection(self):
        session = make_session()
        session.save()
        selection = DemoSelection.objects.create(
            template=self.template, session_key=session.session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        request = HttpRequest()
        request.session = session
        store_pending_demo_selection(request, selection)
        session.save()
        return request, selection

    def test_normal_login_attaches_the_snapshot_and_clears_the_marker(self):
        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-a@example.com", email="login-a@example.com", password="x", is_active=True)

        auth_login(request, user)

        draft = FormDraft.objects.get(owner=user)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "login-signal-demo")
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)

    def test_session_key_rotation_does_not_break_the_link(self):
        request, selection = self._pending_session_with_selection()
        original_key = request.session.session_key
        user = User.objects.create_user(username="login-rotate@example.com", email="login-rotate@example.com", password="x", is_active=True)

        auth_login(request, user)

        self.assertNotEqual(request.session.session_key, original_key)
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 1)

    def test_existing_fields_and_current_step_are_preserved_across_login_attach(self):
        from leads.form_draft_service import upsert_active_draft

        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-preserve@example.com", email="login-preserve@example.com", password="x", is_active=True)
        upsert_active_draft(owner=user, form_type="leads_contact", fields={"request_type": "webapp"}, current_step=2)

        auth_login(request, user)

        draft = FormDraft.objects.get(owner=user)
        self.assertEqual(draft.fields, {"request_type": "webapp"})
        self.assertEqual(draft.current_step, 2)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "login-signal-demo")

    def test_repeated_receiver_invocation_does_not_duplicate_the_draft(self):
        from leads.signals import attach_pending_demo_selection_on_login

        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-repeat@example.com", email="login-repeat@example.com", password="x", is_active=True)

        # Re-store the marker each time, since the receiver already fired
        # once (via auth_login above would pop it) — here we call the
        # receiver directly, twice, to prove idempotency of the underlying
        # ensure+attach operation itself.
        attach_pending_demo_selection_on_login(sender=User, request=request, user=user)
        store_pending_demo_selection(request, selection)
        attach_pending_demo_selection_on_login(sender=User, request=request, user=user)

        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 1)

    def test_malformed_marker_is_cleared_and_login_still_succeeds(self):
        session = make_session()
        session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": "not-an-int", "form_type": FORM_TYPE}
        session.save()
        request = HttpRequest()
        request.session = session
        user = User.objects.create_user(username="login-malformed@example.com", email="login-malformed@example.com", password="x", is_active=True)

        auth_login(request, user)  # must not raise

        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

    def test_deleted_demo_selection_is_cleared_and_login_still_succeeds(self):
        request, selection = self._pending_session_with_selection()
        DemoSelection.objects.filter(pk=selection.pk).delete()
        user = User.objects.create_user(username="login-deleted@example.com", email="login-deleted@example.com", password="x", is_active=True)

        auth_login(request, user)  # must not raise

        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

    def test_database_error_looking_up_demo_selection_does_not_block_login(self):
        """The DemoSelection lookup itself used to sit outside any
        try/except in leads/signals.py — a DatabaseError there would have
        propagated all the way up through auth_login() into whatever
        view called it. It must not: login must complete, the user must
        actually be authenticated, the marker must survive intact for a
        retry, and no partial FormDraft may be created."""
        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-db-error@example.com", email="login-db-error@example.com", password="x", is_active=True)

        with mock.patch(
            "leads.demo_handoff.DemoSelection.objects.select_related",
            side_effect=DatabaseError("simulated connection hiccup"),
        ):
            auth_login(request, user)  # must not raise

        self.assertEqual(request.session.get(SESSION_KEY), str(user.pk))
        marker = request.session.get(PENDING_DEMO_SESSION_KEY)
        self.assertEqual(marker, {"demo_selection_id": selection.pk, "form_type": FORM_TYPE})
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

    def test_transient_error_does_not_block_login_and_restores_the_marker_for_retry(self):
        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-transient@example.com", email="login-transient@example.com", password="x", is_active=True)

        with mock.patch(
            "leads.demo_handoff.ensure_active_draft_with_demo_snapshot",
            side_effect=OSError("simulated transient database hiccup"),
        ):
            auth_login(request, user)  # must not raise

        self.assertEqual(request.session.get(SESSION_KEY), str(user.pk))
        marker = request.session.get(PENDING_DEMO_SESSION_KEY)
        self.assertEqual(marker, {"demo_selection_id": selection.pk, "form_type": FORM_TYPE})
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

    def test_final_rejection_does_not_restore_the_marker(self):
        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-rejected@example.com", email="login-rejected@example.com", password="x", is_active=True)

        with mock.patch(
            "leads.demo_handoff.ensure_active_draft_with_demo_snapshot",
            side_effect=DraftValidationError("boom", code="invalid_snapshot_shape"),
        ):
            auth_login(request, user)  # must not raise

        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

    def test_staff_login_never_receives_a_customers_pending_demo_selection(self):
        request, selection = self._pending_session_with_selection()
        staff = User.objects.create_user(
            username="login-staff@example.com", email="login-staff@example.com",
            password="x", is_active=True, is_staff=True,
        )

        auth_login(request, staff)

        self.assertEqual(FormDraft.objects.filter(owner=staff).count(), 0)
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)

    def test_superuser_login_never_receives_a_customers_pending_demo_selection(self):
        request, selection = self._pending_session_with_selection()
        superuser = User.objects.create_superuser(
            username="login-superuser@example.com", email="login-superuser@example.com", password="x",
        )

        auth_login(request, superuser)

        self.assertEqual(FormDraft.objects.filter(owner=superuser).count(), 0)
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)

    def test_account_switch_via_session_flush_never_transfers_the_marker(self):
        """A session that already belongs to a different authenticated user
        takes django.contrib.auth.login()'s flush() branch, which wipes all
        session data — including our marker — before the new user's login
        fires. The pending demo selection must never reach the new
        account."""
        request, selection = self._pending_session_with_selection()
        request.session[SESSION_KEY] = "999999"
        request.session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
        request.session[HASH_SESSION_KEY] = "irrelevant"
        request.session.save()
        self.assertIn(PENDING_DEMO_SESSION_KEY, request.session)

        new_user = User.objects.create_user(
            username="login-switch@example.com", email="login-switch@example.com", password="x", is_active=True,
        )
        auth_login(request, new_user)

        self.assertNotIn(PENDING_DEMO_SESSION_KEY, request.session)
        self.assertEqual(FormDraft.objects.filter(owner=new_user).count(), 0)

    def test_no_forbidden_tokens_anywhere_after_login_attach(self):
        request, selection = self._pending_session_with_selection()
        user = User.objects.create_user(username="login-notoken@example.com", email="login-notoken@example.com", password="x", is_active=True)

        auth_login(request, user)

        draft = FormDraft.objects.get(owner=user)
        serialized = str(draft.demo_snapshot) + str(dict(request.session.items()))
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn(selection.session_key, serialized)
        self.assertNotIn("submission_token", serialized)


class RegistrationHandoffTests(TestCase):
    def setUp(self):
        self.template = make_template(slug="registration-demo")

    def registration_payload(self):
        return {
            "first_name": "Arvin", "last_name": "Yazdani", "email": "handoff-register@example.com",
            "mobile": "09120373271", "password1": "A-secure-test-password-42", "password2": "A-secure-test-password-42",
        }

    def test_registration_auto_login_attaches_a_pending_demo_selection(self):
        client = Client()
        session = client.session
        session["marker-init"] = True
        session.save()
        selection = DemoSelection.objects.create(
            template=self.template, session_key=session.session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        client.get(reverse("leads:contact") + f"?lang=fa&demo={selection.public_token}")
        self.assertIn(PENDING_DEMO_SESSION_KEY, client.session)

        response = client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="handoff-register@example.com")
        draft = FormDraft.objects.get(owner=user)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "registration-demo")
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)


class RetryPendingDemoSelectionOnContactPageTests(TestCase):
    """The narrow, page-scoped retry path (leads/demo_handoff.py's
    maybe_retry_pending_demo_selection, wired in only from
    LeadCreateView._resolved_demo_selection): an authenticated, non-staff
    customer's next visit to the contact page *without* a `?demo=` gets
    one more chance to attach a pending marker left over from an earlier
    failed attempt (at login, or a prior visit)."""

    def setUp(self):
        self.template = make_template(slug="retry-demo")
        self.customer = User.objects.create_user(
            username="retry-customer@example.com", email="retry-customer@example.com", password="x", is_active=True,
        )

    def _selection(self, session_key="retry-selection-session"):
        return DemoSelection.objects.create(
            template=self.template, session_key=session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )

    def _client_with_pending_marker(self, selection):
        client = Client()
        client.force_login(self.customer)
        session = client.session
        session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": selection.pk, "form_type": FORM_TYPE}
        session.save()
        return client

    def test_retry_attaches_the_snapshot_and_clears_the_marker(self):
        selection = self._selection()
        client = self._client_with_pending_marker(selection)

        response = client.get(reverse("leads:contact") + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        draft = FormDraft.objects.get(owner=self.customer)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "retry-demo")
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)
        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 1)

    def test_repeated_visits_after_a_successful_retry_stay_idempotent(self):
        selection = self._selection()
        client = self._client_with_pending_marker(selection)

        client.get(reverse("leads:contact") + "?lang=fa")
        client.get(reverse("leads:contact") + "?lang=fa")
        client.get(reverse("leads:contact") + "?lang=fa")

        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 1)

    def test_deleted_demo_selection_clears_the_marker_without_creating_a_draft(self):
        selection = self._selection()
        stale_pk = selection.pk
        DemoSelection.objects.filter(pk=stale_pk).delete()
        client = self._client_with_pending_marker(selection)

        response = client.get(reverse("leads:contact") + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)
        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 0)

    def test_transient_error_during_retry_preserves_the_marker_and_still_renders(self):
        selection = self._selection()
        client = self._client_with_pending_marker(selection)

        with mock.patch(
            "leads.demo_handoff.ensure_active_draft_with_demo_snapshot",
            side_effect=OSError("simulated transient database hiccup"),
        ):
            response = client.get(reverse("leads:contact") + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            client.session.get(PENDING_DEMO_SESSION_KEY),
            {"demo_selection_id": selection.pk, "form_type": FORM_TYPE},
        )
        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 0)

    def test_explicit_valid_demo_wins_over_an_old_marker_and_clears_it(self):
        old_selection = self._selection(session_key="retry-old-session")
        client = self._client_with_pending_marker(old_selection)
        session = client.session
        session["new-selection-init"] = True
        session.save()
        new_selection = DemoSelection.objects.create(
            template=self.template, session_key=session.session_key,
            selections={"theme": "warm", "personality": "minimal", "features": []},
        )

        response = client.get(reverse("leads:contact") + f"?lang=fa&demo={new_selection.public_token}")

        self.assertEqual(response.status_code, 200)
        draft = FormDraft.objects.get(owner=self.customer)
        self.assertEqual(draft.demo_snapshot, build_demo_selection_snapshot(new_selection))
        self.assertNotIn(PENDING_DEMO_SESSION_KEY, client.session)
        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 1)

    def test_invalid_demo_param_does_not_fall_back_to_retrying_the_old_marker(self):
        selection = self._selection()
        client = self._client_with_pending_marker(selection)

        response = client.get(reverse("leads:contact") + "?lang=fa&demo=not-a-real-token")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FormDraft.objects.filter(owner=self.customer).count(), 0)
        # The old marker is left untouched — neither consumed nor
        # discarded — so a later visit without the bad param can still
        # retry it successfully.
        self.assertEqual(
            client.session.get(PENDING_DEMO_SESSION_KEY),
            {"demo_selection_id": selection.pk, "form_type": FORM_TYPE},
        )

    def test_staff_and_superuser_visits_never_trigger_the_retry(self):
        selection = self._selection()
        for is_staff, is_superuser, username in [
            (True, False, "retry-staff@example.com"), (False, True, "retry-superuser@example.com"),
        ]:
            staff_or_super = User.objects.create_user(
                username=username, email=username, password="x", is_active=True,
                is_staff=is_staff, is_superuser=is_superuser,
            )
            client = Client()
            client.force_login(staff_or_super)
            session = client.session
            session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": selection.pk, "form_type": FORM_TYPE}
            session.save()

            response = client.get(reverse("leads:contact") + "?lang=fa")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(FormDraft.objects.filter(owner=staff_or_super).count(), 0)

    def test_no_forbidden_tokens_anywhere_after_a_successful_retry(self):
        selection = self._selection()
        client = self._client_with_pending_marker(selection)

        response = client.get(reverse("leads:contact") + "?lang=fa")

        draft = FormDraft.objects.get(owner=self.customer)
        serialized = (
            str(draft.demo_snapshot) + str(dict(client.session.items())) + response.content.decode()
        )
        self.assertNotIn(str(selection.public_token), serialized)
        self.assertNotIn(selection.session_key, serialized)
        self.assertNotIn("submission_token", serialized)


@unittest.skipUnless(
    connection.vendor == "postgresql",
    "A genuine database-level transaction abort can only be forced and observed on a real "
    "database engine; a mocked Python exception (used elsewhere in this file) behaves "
    "identically on any backend and is not evidence about PostgreSQL's own transaction "
    "semantics — skipped on SQLite.",
)
class RealTransactionErrorRecoveryTests(TransactionTestCase):
    """A mocked `OSError`/`DraftValidationError` proves our own exception
    handling works, but it never touches the database — it is not
    evidence that a *genuine* PostgreSQL transaction abort (a real
    statement failure inside `ensure_active_draft_with_demo_snapshot`'s
    own `transaction.atomic()` block) unwinds cleanly, leaves the
    connection usable afterward, and still lets the marker be restored
    for a retry. This forces a real, server-side error mid-transaction
    (an actual invalid `SELECT` sent to PostgreSQL, not a Python-level
    mock) to prove exactly that."""

    def setUp(self):
        self.template = make_template(slug="real-tx-error-demo")

    def test_a_genuine_postgresql_error_mid_attach_restores_the_marker_and_leaves_the_connection_usable(self):
        session = make_session()
        session.save()
        selection = DemoSelection.objects.create(
            template=self.template, session_key=session.session_key,
            selections={"theme": "sage", "personality": "luxury", "features": ["booking"]},
        )
        request = HttpRequest()
        request.session = session
        store_pending_demo_selection(request, selection)
        session.save()
        user = User.objects.create_user(
            username="real-tx-error@example.com", email="real-tx-error@example.com", password="x", is_active=True,
        )

        def _raise_real_database_error(*args, **kwargs):
            # A real, server-rejected statement — not a Python-level
            # mock — so PostgreSQL itself aborts the current transaction
            # exactly the way a genuine transient failure would.
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1/0")

        with mock.patch("leads.form_draft_service.FormDraft.objects.create", side_effect=_raise_real_database_error):
            auth_login(request, user)  # must not raise, despite the real DB-level error

        # The connection must be perfectly usable again afterward — proof
        # that Django's own transaction.atomic() rolled back cleanly
        # rather than leaving the connection in an aborted state.
        self.assertEqual(request.session.get(SESSION_KEY), str(user.pk))
        marker = request.session.get(PENDING_DEMO_SESSION_KEY)
        self.assertEqual(marker, {"demo_selection_id": selection.pk, "form_type": FORM_TYPE})
        self.assertEqual(FormDraft.objects.filter(owner=user).count(), 0)

        # A subsequent, real retry (no mock this time) must succeed
        # cleanly on the very same connection.
        from leads.demo_handoff import consume_pending_demo_selection
        consume_pending_demo_selection(request, user)
        draft = FormDraft.objects.get(owner=user)
        self.assertEqual(draft.demo_snapshot["demo_template_slug"], "real-tx-error-demo")
