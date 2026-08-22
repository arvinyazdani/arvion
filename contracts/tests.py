from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from crm_orders.specialist import SECTIONS
from contracts.forms import ClauseSelectionForm, ProposalForm
from contracts.models import ContractAcceptance, ContractProposal, ContractReview, ContractRoomAcknowledgement
from contracts.services import add_default_clauses, publish_version
from contracts.templatetags.contract_extras import contract_terms_html, persian_amount
from django.utils import timezone, translation
from django.core.cache import cache
from django.core.exceptions import ValidationError


class ContractWorkflowTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("fa")
        self.addCleanup(translation.deactivate)
        self.root = User.objects.create_superuser(username="contract-root", email="contracts@example.com", password="safe-password")
        self.proposal = ContractProposal.objects.create(
            customer_name="مشتری نمونه", customer_phone="989120373271", project_title="سامانه نمونه",
            project_scope="تحلیل و توسعه نسخه اول", amount_irr=1_000_000_000,
            delivery_terms="۸ هفته", general_terms="ماده ۱ ـ شرایط عمومی\n۱-۱. متن عمومی",
            private_terms="ماده ۱ ـ شرایط خصوصی\n۱-۱. متن خصوصی", created_by=self.root,
        )
        add_default_clauses(self.proposal)

    def grant_contract_access(self, version):
        session = self.client.session
        session[f"contract-access:{version.pk}"] = self.proposal.customer_phone
        session.save()

    def link_crm_discovery(self, *, complete=False):
        crm = CrmOrder.objects.create(
            organization_name="سازمان متصل", industry="فناوری", organization_size="under_10",
            contact_name="مدیر نمونه", job_title="مدیر", work_email="manager@example.com",
            phone="09120373271", crm_user_count="1_5", current_process="فرآیند اولیه",
            main_pain_points="پیگیری دستی", success_metrics="کاهش زمان",
            critical_workflows="فروش", reports_needed="", permission_requirements="",
            budget_range="estimate", expected_timeline="1_2", decision_process="مدیرعامل",
            privacy_accepted_at=timezone.now(),
        )
        answers = {
            section_key: {
                key: "پاسخ کامل و معتبر مشتری برای این پرسش تخصصی"
                for key, _question, _help_text in questions
            }
            for section_key, _title, _description, questions in SECTIONS
        } if complete else {}
        discovery = CrmSpecialistDiscovery.objects.create(
            order=crm,
            status="submitted" if complete else "draft",
            answers=answers,
        )
        self.proposal.crm_order = crm
        self.proposal.save(update_fields=["crm_order"])
        return discovery

    def test_contract_amount_uses_persian_three_digit_groups(self):
        self.assertEqual(persian_amount(380_000_000), "۳۸۰,۰۰۰,۰۰۰")

    def test_contract_terms_are_grouped_into_closable_articles(self):
        html = contract_terms_html("مقدمه\nماده ۱ ـ موضوع\n۱-۱. متن نخست\nماده ۲ ـ مدت\n۲-۱. متن دوم")
        self.assertEqual(html.count('class="legal-article"'), 2)
        self.assertIn('data-legal-article', html)
        self.assertIn('data-legal-close', html)
        self.assertIn('بستن ماده', html)

    def test_stale_contract_version_redirects_instead_of_403_on_confirmation(self):
        self.proposal.general_terms = "شرایط عمومی نمونه"
        self.proposal.private_terms = "شرایط خصوصی نمونه"
        self.proposal.save()
        old_version = publish_version(self.proposal, self.root)
        self.grant_contract_access(old_version)
        ContractRoomAcknowledgement.objects.create(version=old_version, document="general")
        ContractRoomAcknowledgement.objects.create(version=old_version, document="private")
        publish_version(self.proposal, self.root)
        response = self.client.post(reverse("contracts:contract_confirm", args=[self.proposal.token]), {"agreement": "on"})
        self.assertRedirects(response, reverse("contracts:contract_access", args=[self.proposal.token]))

    def test_public_link_is_hidden_before_publish(self):
        response = self.client.get(reverse("contracts:contract_document", args=[self.proposal.token, "general"]))
        self.assertEqual(response.status_code, 404)

    @override_settings(SITE_URL="https://rvionai.example")
    def test_contract_access_has_private_share_metadata(self):
        version = publish_version(self.proposal, self.root)
        response = self.client.get(reverse("contracts:contract_access", args=[self.proposal.token]))
        access_url = f"https://rvionai.example{reverse('contracts:contract_access', args=[self.proposal.token])}"
        self.assertContains(response, 'property="og:title" content="پروندهٔ اختصاصی قرارداد | آرویون"')
        self.assertContains(response, access_url)
        self.assertContains(response, "contracts/images/share-contract-room-v1.png", html=False)

    def test_contract_access_errors_are_linked_to_their_controls(self):
        publish_version(self.proposal, self.root)
        response = self.client.post(
            reverse("contracts:contract_access", args=[self.proposal.token]),
            {"phone": "", "password": ""},
        )
        self.assertContains(response, 'aria-invalid="true"', count=2)
        self.assertContains(response, 'aria-describedby="id_phone_error"', html=False)
        self.assertContains(response, 'aria-describedby="id_password_error"', html=False)
        self.assertContains(response, 'id="id_phone_error"', html=False)
        self.assertContains(response, 'id="id_password_error"', html=False)

    def test_proposal_form_can_prefill_from_crm_assessment(self):
        crm = CrmOrder.objects.create(
            organization_name="شرکت نمونه", industry="فناوری", organization_size="under_10",
            contact_name="علی نمونه", job_title="مدیر", work_email="ali@example.com", phone="09120373271",
            primary_goals=[], departments=[], customer_types=[], lead_sources=[], crm_user_count="1_5",
            current_process="فرآیند فعلی", current_data_sources=[], main_pain_points="پیگیری دستی",
            success_metrics="کاهش زمان پاسخ", required_capabilities=[], customer_data_fields=[], reminder_types=[],
            notification_channels=[], critical_workflows="", correspondence_features=[], ai_use_cases=[],
            reporting_priorities=[], system_roles=[], reports_needed="", permission_requirements="", budget_range="estimate",
            expected_timeline="1_2", decision_process="مدیرعامل", privacy_accepted_at=timezone.now(),
        )
        self.client.force_login(self.root)
        response = self.client.post(reverse("contracts:proposal_create"), {
            "needs_assessment": f"crm:{crm.pk}", "title": "پیشنهاد CRM", "customer_name": "x",
            "customer_phone": "09120373271", "customer_email": "x@example.com", "client_details": "",
            "project_title": "x", "project_scope": "x", "amount_irr": "1000000",
            "payment_terms": "۵۰/۵۰", "delivery_terms": "۸ هفته",
        })
        self.assertEqual(response.status_code, 302)
        proposal = ContractProposal.objects.latest("created_at")
        self.assertEqual(proposal.customer_name, "علی نمونه")
        self.assertIn("فرآیند فعلی", proposal.project_scope)

    def test_english_contract_builder_localizes_generated_discovery_copy(self):
        crm = CrmOrder.objects.create(
            organization_name="Example Co", industry="Technology", organization_size="under_10",
            contact_name="Alex", job_title="Director", work_email="alex@example.com",
            phone="09120373271", crm_user_count="1_5", current_process="Current process",
            main_pain_points="Manual follow-up", success_metrics="Faster response",
            critical_workflows="Sales", reports_needed="", permission_requirements="",
            budget_range="estimate", expected_timeline="1_2", decision_process="CEO",
            privacy_accepted_at=timezone.now(),
        )
        form = ProposalForm(language="en")
        self.assertEqual(form.initial["title"], "Custom software design and development proposal")
        self.assertEqual(form.initial["payment_terms"], "50% at project start and 50% at final delivery")
        self.assertIn("8 weeks after", form.fields["delivery_terms"].help_text)
        payload = form.assessment_data[f"crm:{crm.pk}"]
        self.assertEqual(payload["project_title"], "Enterprise CRM platform Example Co")
        self.assertIn("Organisation: Example Co", payload["client_details"])
        self.assertIn("Discovery reference:", payload["client_details"])
        self.assertNotIn("نام مجموعه", payload["client_details"])

        clause_form = ClauseSelectionForm(
            {"enabled_clauses": [], "custom_title": "Title", "custom_body": ""},
            proposal=self.proposal,
            language="en",
        )
        self.assertFalse(clause_form.is_valid())
        self.assertIn("Enter both a title and text", str(clause_form.non_field_errors()))

    def test_management_contract_routes_use_new_shell(self):
        self.client.force_login(self.root)
        listing = self.client.get(reverse("management_portal:contract_list"))
        self.assertContains(listing, "پیشنهادهای قرارداد")
        self.assertContains(listing, self.proposal.project_title)
        self.assertNotContains(listing, 'href="/admin/')
        detail = self.client.get(reverse("management_portal:contract_detail", args=[self.proposal.pk]))
        self.assertContains(detail, "مدیریت بندها")
        self.assertContains(detail, "ساخت نسخه و فعال‌سازی لینک")
        self.assertContains(detail, "نسخه ۱ از اطلاعات و بندهای فعلی ساخته", html=False)
        self.assertContains(detail, reverse("management_portal:contract_clauses", args=[self.proposal.pk]))

    def test_english_management_contract_copy_status_and_settings_are_separate(self):
        self.client.force_login(self.root)
        listing = self.client.get("/en/management/contracts/")
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Contract proposals")
        self.assertContains(listing, "Draft")
        self.assertNotContains(listing, ">پیش‌نویس<", html=False)

        detail = self.client.get(f"/en/management/contracts/{self.proposal.pk}/")
        self.assertContains(detail, "Draft · Version")
        self.assertContains(detail, "Publish & customer link")
        self.assertNotContains(detail, "مدیریت بندها")

        settings_response = self.client.get("/en/management/contracts/settings/")
        self.assertContains(settings_response, "Contractor details used in contracts")
        self.assertContains(settings_response, "Contractor legal name")
        self.assertContains(settings_response, "Save contract settings")
        self.assertNotContains(settings_response, "مشخصات مجری در قرارداد")

        preview = self.client.get(f"/en/management/contracts/{self.proposal.pk}/preview/")
        self.assertContains(preview, "Review the contract as the customer will see it")
        self.assertContains(preview, "Pre-send preview")
        self.assertContains(preview, "contracts/proposal-preview.css")
        self.assertContains(preview, "data-print-contract")
        self.assertNotContains(preview, "TEST PREVIEW")

    def test_management_preview_includes_every_document_before_publish(self):
        self.client.force_login(self.root)
        response = self.client.get(
            reverse("management_portal:contract_preview", args=[self.proposal.pk]),
        )
        self.assertContains(response, "ماده ۱ ـ شرایط عمومی")
        self.assertContains(response, "ماده ۱ ـ شرایط خصوصی")
        self.assertContains(response, "بندهای فعال")
        self.assertContains(response, "پیش‌نمایش داخلی آرویون")
        self.assertContains(
            response,
            reverse("management_portal:contract_detail", args=[self.proposal.pk]),
        )

    def test_contract_detail_only_offers_actions_allowed_by_current_status(self):
        self.client.force_login(self.root)
        draft_response = self.client.get(
            reverse("management_portal:contract_detail", args=[self.proposal.pk]),
        )
        self.assertContains(draft_response, "ویرایش پیش‌نویس")
        self.assertContains(draft_response, "مدیریت بندها")
        self.assertContains(draft_response, 'data-confirm=', count=3)
        self.assertContains(draft_response, "contracts/manager-contracts.js")

        self.proposal.status = "accepted"
        self.proposal.save(update_fields=["status", "updated_at"])
        accepted_response = self.client.get(
            reverse("management_portal:contract_detail", args=[self.proposal.pk]),
        )
        self.assertContains(accepted_response, "این نسخه توسط مشتری پذیرفته شده")
        self.assertNotContains(accepted_response, "ویرایش پیش‌نویس")
        self.assertNotContains(accepted_response, "مدیریت بندها")
        self.assertNotContains(accepted_response, "فعال‌سازی لینک مشتری")
        self.assertNotContains(accepted_response, "غیرفعال‌کردن لینک مشتری")

    def test_specialist_discovery_is_included_in_contract_scope(self):
        crm = CrmOrder.objects.create(
            organization_name="نور بینان", industry="تجهیزات", organization_size="under_10",
            contact_name="مدیر پروژه", job_title="مدیر", work_email="manager@example.com", phone="09120373271",
            crm_user_count="1_5", current_process="فرآیند اولیه", main_pain_points="پیگیری دستی",
            success_metrics="کاهش زمان", critical_workflows="فروش", reports_needed="", permission_requirements="",
            budget_range="estimate", expected_timeline="1_2", decision_process="مدیرعامل", privacy_accepted_at=timezone.now(),
        )
        CrmSpecialistDiscovery.objects.create(order=crm, status="submitted", answers={"نقش‌های واقعی": ["فروش", "مدیر سیستم"]})
        self.client.force_login(self.root)
        response = self.client.post(reverse("management_portal:contract_create"), {
            "needs_assessment": f"crm:{crm.pk}", "title": "پیشنهاد CRM", "customer_name": "x",
            "customer_phone": "09120373271", "customer_email": "x@example.com", "client_details": "",
            "project_title": "x", "project_scope": "x", "amount_irr": "1000000", "payment_terms": "۵۰/۵۰", "delivery_terms": "۸ هفته",
        })
        self.assertEqual(response.status_code, 302)
        proposal = ContractProposal.objects.latest("created_at")
        self.assertIn("نیازسنجی تخصصی", proposal.project_scope)
        self.assertIn("مدیر سیستم", proposal.project_scope)

    def test_publish_creates_immutable_snapshot_and_public_noindex_page(self):
        self.proposal.general_terms = "شرایط عمومی نمونه"
        self.proposal.save()
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        original = version.snapshot["project_scope"]
        self.proposal.project_scope = "متن تغییر یافته"
        self.proposal.save()
        version.refresh_from_db()
        self.assertEqual(version.snapshot["project_scope"], original)
        response = self.client.get(reverse("contracts:contract_document", args=[self.proposal.token, "general"]))
        self.assertContains(response, "noindex,nofollow,noarchive")
        self.assertContains(response, "قرارداد مشتری نمونه | آرویون")
        self.assertContains(response, "شرایط عمومی پیمان")
        self.assertNotContains(response, "متن تغییر یافته")

    def test_legacy_final_document_returns_to_contract_room(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")
        url = reverse("contracts:contract_document", args=[self.proposal.token, "final"])
        self.assertRedirects(self.client.get(url), reverse("contracts:public_contract", args=[self.proposal.token]))

    @override_settings(CONTRACT_ACCESS_PASSWORD="test-contract-password")
    def test_phone_access_requires_matching_number_and_password(self):
        version = publish_version(self.proposal, self.root)
        url = reverse("contracts:contract_access", args=[self.proposal.token])
        self.assertRedirects(self.client.get(reverse("contracts:public_contract", args=[self.proposal.token])), url)
        invalid = self.client.post(url, {"phone": "09120000000", "password": "test-contract-password"})
        self.assertContains(invalid, "شماره همراه یا رمز ورود صحیح نیست")
        response = self.client.post(url, {"phone": "09120373271", "password": "test-contract-password"})
        self.assertRedirects(response, reverse("contracts:public_contract", args=[self.proposal.token]))

    def test_contract_logout_accepts_secure_csrf_post(self):
        version = publish_version(self.proposal, self.root)
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session[f"contract-access:{version.pk}"] = self.proposal.customer_phone
        session.save()
        room_url = reverse("contracts:public_contract", args=[self.proposal.token])
        response = client.get(room_url, secure=True)
        token = response.cookies["csrftoken"].value
        response = client.post(
            reverse("contracts:contract_logout", args=[self.proposal.token]),
            {"csrfmiddlewaretoken": token}, secure=True,
            HTTP_REFERER=f"https://testserver{room_url}",
        )
        self.assertRedirects(response, reverse("contracts:contract_access", args=[self.proposal.token]))
        self.assertNotIn(f"contract-access:{version.pk}", client.session)

    def test_document_acknowledgement_accepts_secure_csrf_post(self):
        self.proposal.general_terms = "شرایط عمومی نمونه"
        self.proposal.private_terms = "شرایط خصوصی نمونه"
        self.proposal.save()
        version = publish_version(self.proposal, self.root)
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session[f"contract-access:{version.pk}"] = self.proposal.customer_phone
        session.save()
        document_url = reverse("contracts:contract_document", args=[self.proposal.token, "general"])
        response = client.get(document_url, secure=True)
        token = response.cookies["csrftoken"].value
        response = client.post(
            reverse("contracts:contract_acknowledge", args=[self.proposal.token, "general"]),
            {"csrfmiddlewaretoken": token, "acknowledge": "on"}, secure=True,
            HTTP_REFERER=f"https://testserver{document_url}",
        )
        self.assertRedirects(response, reverse("contracts:public_contract", args=[self.proposal.token]))
        self.assertTrue(ContractRoomAcknowledgement.objects.filter(version=version, document="general").exists())

    def test_document_acknowledgement_requires_explicit_checkbox(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        response = self.client.post(
            reverse("contracts:contract_acknowledge", args=[self.proposal.token, "general"]),
            {},
        )
        self.assertRedirects(
            response,
            reverse("contracts:contract_document", args=[self.proposal.token, "general"]),
        )
        self.assertFalse(ContractRoomAcknowledgement.objects.filter(version=version).exists())

    def test_linked_contract_documents_are_readable_before_discovery_is_complete(self):
        discovery = self.link_crm_discovery()
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        room_url = reverse("contracts:public_contract", args=[self.proposal.token])
        general_url = reverse(
            "contracts:contract_document", args=[self.proposal.token, "general"],
        )
        private_url = reverse(
            "contracts:contract_document", args=[self.proposal.token, "private"],
        )

        room = self.client.get(room_url)
        self.assertContains(room, f'href="{general_url}"', html=False)
        self.assertContains(room, f'href="{private_url}"', html=False)
        general = self.client.get(general_url)
        private = self.client.get(private_url)
        self.assertEqual(general.status_code, 200)
        self.assertEqual(private.status_code, 200)
        self.assertContains(general, "سند برای مطالعه در دسترس است")
        self.assertContains(private, "سند برای مطالعه در دسترس است")
        self.assertNotContains(general, 'name="acknowledge"', html=False)
        self.assertNotContains(private, 'name="acknowledge"', html=False)

        discovery.answers = {
            section_key: {
                key: "پاسخ کامل و معتبر مشتری برای این پرسش تخصصی"
                for key, _question, _help_text in questions
            }
            for section_key, _title, _description, questions in SECTIONS
        }
        discovery.status = "submitted"
        discovery.save(update_fields=["answers", "status", "updated_at"])

        room = self.client.get(room_url)
        self.assertContains(room, f'href="{general_url}"', html=False)
        self.assertEqual(self.client.get(general_url).status_code, 200)

    def test_linked_contract_direct_acknowledgement_posts_enforce_document_sequence(self):
        discovery = self.link_crm_discovery()
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        room_url = reverse("contracts:public_contract", args=[self.proposal.token])
        general_ack_url = reverse(
            "contracts:contract_acknowledge", args=[self.proposal.token, "general"],
        )
        private_ack_url = reverse(
            "contracts:contract_acknowledge", args=[self.proposal.token, "private"],
        )

        blocked_general = self.client.post(general_ack_url, {"acknowledge": "on"})
        self.assertRedirects(blocked_general, room_url)
        self.assertFalse(ContractRoomAcknowledgement.objects.filter(version=version).exists())

        discovery.answers = {
            section_key: {
                key: "پاسخ کامل و معتبر مشتری برای این پرسش تخصصی"
                for key, _question, _help_text in questions
            }
            for section_key, _title, _description, questions in SECTIONS
        }
        discovery.status = "submitted"
        discovery.save(update_fields=["answers", "status", "updated_at"])

        blocked_private = self.client.post(private_ack_url, {"acknowledge": "on"})
        self.assertRedirects(blocked_private, room_url)
        self.assertFalse(
            ContractRoomAcknowledgement.objects.filter(version=version, document="private").exists(),
        )

        self.assertRedirects(self.client.post(general_ack_url, {"acknowledge": "on"}), room_url)
        self.assertRedirects(self.client.post(private_ack_url, {"acknowledge": "on"}), room_url)
        self.assertEqual(
            set(version.room_acknowledgements.values_list("document", flat=True)),
            {"general", "private"},
        )

    def test_room_confirmation_control_posts_the_server_required_field(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")

        response = self.client.get(reverse("contracts:public_contract", args=[self.proposal.token]))

        self.assertContains(response, 'name="agreement"', html=False)
        self.assertContains(response, 'value="on"', html=False)

    def test_private_document_shows_dynamic_customer_and_snapshot_clauses(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")

        response = self.client.get(
            reverse("contracts:contract_document", args=[self.proposal.token, "private"]),
        )

        self.assertContains(response, self.proposal.customer_name)
        self.assertNotContains(response, "نور بینان")
        self.assertContains(response, version.snapshot["clauses"][0]["title"])

    def test_final_confirmation_accepts_secure_csrf_post(self):
        version = publish_version(self.proposal, self.root)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session[f"contract-access:{version.pk}"] = self.proposal.customer_phone
        session.save()
        accept_url = reverse("contracts:contract_accept", args=[self.proposal.token])
        response = client.get(accept_url, secure=True)
        token = response.cookies["csrftoken"].value
        response = client.post(
            reverse("contracts:contract_confirm", args=[self.proposal.token]),
            {"csrfmiddlewaretoken": token, "agreement": "on"}, secure=True,
            HTTP_REFERER=f"https://testserver{accept_url}",
        )
        self.assertRedirects(response, reverse("contracts:contract_access", args=[self.proposal.token]))
        self.assertTrue(hasattr(version, "acceptance"))

    def test_non_superuser_cannot_manage_contracts(self):
        staff = User.objects.create_user(username="staff-c", email="staff-c@example.com", password="safe-password", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("contracts:proposal_list")).status_code, 403)

    def test_manager_can_disable_and_add_clause_without_mutating_old_version(self):
        first = publish_version(self.proposal, self.root)
        old_count = len(first.snapshot["clauses"])
        self.client.force_login(self.root)
        kept = [str(item.pk) for item in self.proposal.clauses.all()[1:]]
        response = self.client.post(reverse("contracts:proposal_clauses", args=[self.proposal.pk]), {
            "enabled_clauses": kept, "custom_title": "بند اختصاصی", "custom_body": "متن بند اختصاصی",
        })
        self.assertRedirects(response, reverse("contracts:proposal_detail", args=[self.proposal.pk]))
        first.refresh_from_db()
        self.assertEqual(len(first.snapshot["clauses"]), old_count)
        second = publish_version(self.proposal, self.root)
        self.assertEqual(len(second.snapshot["clauses"]), old_count)
        self.assertEqual(second.snapshot["clauses"][-1]["title"], "بند اختصاصی")

    def test_final_confirmation_is_bound_to_version_and_single_use(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")
        confirm_url = reverse("contracts:contract_confirm", args=[self.proposal.token])
        response = self.client.post(confirm_url, {"agreement": "on"})
        self.assertRedirects(response, reverse("contracts:contract_access", args=[self.proposal.token]))
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, "accepted")
        self.assertEqual(version.acceptance.verified_phone, self.proposal.customer_phone)
        self.assertEqual(len(version.acceptance.evidence_hash), 64)
        self.grant_contract_access(version)
        second = self.client.post(confirm_url, {"agreement": "on"})
        self.assertRedirects(second, reverse("contracts:contract_accept", args=[self.proposal.token]))
        self.assertEqual(ContractAcceptance.objects.filter(version=version).count(), 1)

    def test_accepted_room_shows_receipt_instead_of_a_second_confirmation_form(self):
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")
        ContractAcceptance.objects.create(
            version=version,
            verified_phone=self.proposal.customer_phone,
            evidence_hash=version.snapshot_hash,
        )
        ContractProposal.objects.filter(pk=self.proposal.pk).update(status="accepted")

        response = self.client.get(
            reverse("contracts:public_contract", args=[self.proposal.token]),
        )

        self.assertContains(response, "تأیید این نسخه ثبت شده است")
        self.assertContains(response, "مشاهده رسید تأیید")
        self.assertNotContains(response, 'name="agreement"', html=False)

    def test_acceptance_captures_specialist_answers_and_freezes_customer_edits(self):
        crm = CrmOrder.objects.create(
            organization_name="سازمان نمونه", industry="فناوری", organization_size="under_10",
            contact_name="مدیر نمونه", job_title="مدیر", work_email="manager@example.com",
            phone="09120373271", crm_user_count="1_5", current_process="فرآیند اولیه",
            main_pain_points="پیگیری دستی", success_metrics="کاهش زمان",
            critical_workflows="فروش", reports_needed="", permission_requirements="",
            budget_range="estimate", expected_timeline="1_2", decision_process="مدیرعامل",
            privacy_accepted_at=timezone.now(),
        )
        answers = {
            section_key: {
                key: "پاسخ کامل و معتبر مشتری برای این پرسش تخصصی"
                for key, _question, _help_text in questions
            }
            for section_key, _title, _description, questions in SECTIONS
        }
        discovery = CrmSpecialistDiscovery.objects.create(
            order=crm, status="submitted",
            answers={"users_access": {"roles": "پاسخ ناقص قدیمی"}},
        )
        self.proposal.crm_order = crm
        self.proposal.save(update_fields=["crm_order"])
        version = publish_version(self.proposal, self.root)
        self.grant_contract_access(version)
        ContractRoomAcknowledgement.objects.create(version=version, document="general")
        ContractRoomAcknowledgement.objects.create(version=version, document="private")

        blocked = self.client.post(
            reverse("contracts:contract_confirm", args=[self.proposal.token]),
            {"agreement": "on"},
        )
        self.assertRedirects(
            blocked, reverse("contracts:public_contract", args=[self.proposal.token]),
        )
        self.assertFalse(ContractAcceptance.objects.filter(version=version).exists())
        discovery.answers = answers
        discovery.save(update_fields=["answers", "updated_at"])

        response = self.client.post(
            reverse("contracts:contract_confirm", args=[self.proposal.token]),
            {"agreement": "on"},
        )

        self.assertRedirects(response, reverse("contracts:contract_access", args=[self.proposal.token]))
        acceptance = ContractAcceptance.objects.get(version=version)
        self.assertEqual(acceptance.discovery_snapshot["answers"], discovery.answers)
        self.assertEqual(len(acceptance.evidence_hash), 64)

        self.client.force_login(self.root)
        edit = self.client.post(
            reverse("crm_orders:specialist_section", args=[crm.tracking_code, "users_access"]),
            {
                "roles": "نقش تازه بعد از امضا",
                "permissions": "دسترسی کامل برای مدیر سیستم",
                "approval": "جانشین مدیر فروش درخواست را تأیید می‌کند",
            },
        )
        self.assertEqual(edit.status_code, 403)
        acceptance.refresh_from_db()
        self.assertEqual(acceptance.discovery_snapshot["answers"], discovery.answers)

    def test_sent_proposal_must_be_revoked_before_editing(self):
        publish_version(self.proposal, self.root)
        self.client.force_login(self.root)

        response = self.client.get(
            reverse("contracts:proposal_edit", args=[self.proposal.pk]),
        )

        self.assertEqual(response.status_code, 403)

    def test_accepted_contract_archive_remains_available_after_expiry(self):
        version = publish_version(self.proposal, self.root)
        ContractAcceptance.objects.create(
            version=version, verified_phone=self.proposal.customer_phone,
        )
        ContractProposal.objects.filter(pk=self.proposal.pk).update(
            status="accepted", expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        response = self.client.get(
            reverse("contracts:contract_access", args=[self.proposal.token]),
        )

        self.assertEqual(response.status_code, 200)

    def test_publish_rejects_missing_legal_documents(self):
        self.proposal.private_terms = ""
        self.proposal.save(update_fields=["private_terms"])
        with self.assertRaises(ValidationError):
            publish_version(self.proposal, self.root)

    @override_settings(CONTRACT_ACCESS_PASSWORD="test-contract-password", CONTRACT_ACCESS_ATTEMPTS=2)
    def test_contract_access_is_rate_limited(self):
        publish_version(self.proposal, self.root)
        url = reverse("contracts:contract_access", args=[self.proposal.token])
        for _ in range(2):
            self.client.post(url, {"phone": "09120000000", "password": "wrong"})
        blocked = self.client.post(url, {"phone": "09120373271", "password": "test-contract-password"})
        self.assertEqual(blocked.status_code, 200)
        self.assertContains(blocked, "تلاش‌های ورود بیش از حد مجاز")
        self.assertFalse(any(key.startswith("contract-access:") for key in self.client.session.keys()))

    @override_settings(CONTRACT_ACCESS_PASSWORD="test-contract-password")
    def test_access_identity_is_bound_to_published_snapshot(self):
        version = publish_version(self.proposal, self.root)
        self.proposal.customer_phone = "989111111111"
        self.proposal.save(update_fields=["customer_phone"])
        url = reverse("contracts:contract_access", args=[self.proposal.token])

        response = self.client.post(url, {
            "phone": "09120373271", "password": "test-contract-password",
        })

        self.assertRedirects(response, reverse("contracts:public_contract", args=[self.proposal.token]))
        self.assertEqual(self.client.session[f"contract-access:{version.pk}"], "989120373271")
