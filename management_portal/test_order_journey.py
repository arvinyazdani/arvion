from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from django.utils import translation, timezone

from accounts.models import User
from contracts.models import ContractProposal, RoomEvent, ContractVersion
from contracts.workspace_services import ensure_case_workspace, create_specialist_template_version, create_access_grant, publish_customer_workspace
from leads.models import Lead
from .models import CustomerCase, Customer, CaseDocument, CaseDocumentRevision, OperationalAudit
from .test_customer_workspaces import SCHEMA


class OrderJourneyTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)
        self.admin = User.objects.create_superuser(username='journey-qa', email='journey@example.test', password='test-password')
        self.customer = Customer.objects.create(name='مشتری آزمایشی', phone='09120000041')
        self.case = CustomerCase.objects.create(customer=self.customer, kind='crm', customer_name=self.customer.name, phone=self.customer.phone)
        self.client.force_login(self.admin)
        self.url = reverse('management_portal:workspace_detail', args=[self.case.pk])
        self.preview = reverse('management_portal:workspace_preview', args=[self.case.pk])

    def package(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.admin)
        create_specialist_template_version(proposal=proposal, schema=SCHEMA, actor=self.admin)
        proposal.private_terms = 'ماده ۱ ـ شرایط اختصاصی محفوظ'
        proposal.amount_irr = 123456789
        proposal.save()
        create_access_grant(proposal=proposal, authorized_phone=self.case.phone, raw_password='Safe-QA-password!', actor=self.admin)
        return proposal

    def test_documents_and_archived_revisions_visible_before_workspace_creation(self):
        document = CaseDocument.objects.create(case=self.case, kind='initial', title='پاسخ پایه', snapshot={'goal': 'پاسخ فعلی'}, checksum='a'*64)
        CaseDocumentRevision.objects.create(document=document, title='قدیمی', snapshot={'goal': 'پاسخ قدیمی'}, checksum='b'*64)
        response = self.client.get(self.url)
        self.assertContains(response, 'پاسخ فعلی')
        self.assertContains(response, 'پاسخ قدیمی')
        self.assertContains(response, '1 نسخه')
        self.assertFalse(ContractProposal.objects.exists())
        self.assertEqual(document.revisions.count(), 1)

    def test_checklist_does_not_confuse_preparation_with_customer_completion(self):
        proposal = self.package()
        response = self.client.get(self.url)
        self.assertTrue(response.context['ready_to_publish'])
        self.assertEqual(response.context['progress']['percent'], 0)
        self.assertContains(response, 'نه تأیید مشتری')
        proposal.access_grants.update(is_active=False)
        self.assertFalse(self.client.get(self.url).context['ready_to_publish'])

    def test_preview_is_read_only_and_does_not_consume_once_only_credentials(self):
        proposal = self.package()
        session = self.client.session
        key = f'workspace_credentials_{self.case.pk}'
        session[key] = {'password': 'ONLY-ONCE-QA-SECRET'}
        session.save()
        before = (RoomEvent.objects.count(), OperationalAudit.objects.count(), ContractVersion.objects.count())
        response = self.client.get(self.preview)
        self.assertContains(response, '123,456,789')
        self.assertContains(response, SCHEMA[0]['questions'][0]['label'])
        self.assertNotContains(response, 'ONLY-ONCE-QA-SECRET')
        self.assertNotContains(response, proposal.token)
        self.assertEqual(self.client.session[key]['password'], 'ONLY-ONCE-QA-SECRET')
        self.assertEqual(before, (RoomEvent.objects.count(), OperationalAudit.objects.count(), ContractVersion.objects.count()))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'draft')

    def test_published_preview_uses_frozen_snapshot_not_mutated_proposal(self):
        proposal = self.package()
        version = publish_customer_workspace(proposal=proposal, actor=self.admin)
        old = version.snapshot.copy()
        ContractProposal.objects.filter(pk=proposal.pk).update(private_terms='NOT-IN-FROZEN-VERSION', amount_irr=1)
        response = self.client.get(self.preview)
        self.assertTrue(response.context['published'])
        self.assertContains(response, '123,456,789')
        self.assertNotContains(response, 'NOT-IN-FROZEN-VERSION')
        version.refresh_from_db()
        self.assertEqual(version.snapshot, old)

    def test_preview_blocks_nonstaff_and_redirects_when_no_workspace(self):
        self.assertRedirects(self.client.get(self.preview), self.url)
        user = User.objects.create_user(username='client', email='client@example.test', password='test-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.preview).status_code, 302)
        self.assertEqual(self.client.post(reverse('management_portal:workspace_create', args=[self.case.pk])).status_code, 302)
        self.assertFalse(ContractProposal.objects.exists())

    def test_source_links_require_permission_and_survive_deleted_source(self):
        lead = Lead.objects.create(name='Source customer', phone='09120000042', email_or_telegram='source@example.test', message='project', privacy_accepted_at=timezone.now())
        self.case = CustomerCase.objects.get(source_content_type=ContentType.objects.get_for_model(Lead), source_object_id=lead.pk)
        self.url = reverse('management_portal:workspace_detail', args=[self.case.pk])
        response = self.client.get(self.url)
        self.assertEqual(response.context['source_links']['detail'], reverse('management_portal:request_detail', args=['lead', lead.pk]))
        staff = User.objects.create_user(username='staff', email='staff@example.test', password='test-password', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).context['source_links'], {})
        staff.user_permissions.add(Permission.objects.get(codename='view_lead', content_type=self.case.source_content_type))
        self.assertIn('export', self.client.get(self.url).context['source_links'])
        lead.delete()
        self.assertEqual(self.client.get(self.url).context['source_links'], {})

    def test_list_has_real_totals_pagination_and_latest_status_not_historical_status(self):
        proposal, _ = ensure_case_workspace(case=self.case, actor=self.admin)
        proposal.status = 'sent'
        proposal.save()
        ContractProposal.objects.create(customer_case=self.case, title='Newest', customer_name='Newest', customer_phone=self.case.phone, project_title='Newest', project_scope='Scope', amount_irr=1, delivery_terms='Soon', created_by=self.admin, status='draft')
        for n in range(21):
            CustomerCase.objects.create(kind='general', customer_name=f'Another {n}')
        url = reverse('management_portal:workspace_list')
        response = self.client.get(url)
        self.assertEqual(response.context['page'].paginator.count, 22)
        self.assertEqual(len(response.context['rows']), 20)
        response = self.client.get(url, {'state':'sent'})
        self.assertEqual(response.context['page'].paginator.count, 0)
        response = self.client.get(url, {'state':'draft'})
        self.assertEqual(response.context['stats']['active'], 1)
        self.assertEqual(response.context['page'].paginator.count, 1)
        response = self.client.get(url, {'q': 'Another', 'page': 2})
        self.assertEqual(len(response.context['rows']), 1)
        self.assertIn('q=Another', response.context['page'].previous_url)

    def test_invalid_agreement_preserves_context_and_shows_inline_errors(self):
        proposal = self.package()
        CaseDocument.objects.create(case=self.case, kind='initial', title='KEEP BASE', snapshot={'goal':'KEEP GOAL'}, checksum='c'*64)
        response = self.client.post(reverse('management_portal:workspace_contract_save', args=[self.case.pk]), {'proposal_id':proposal.pk, 'project_title':'Typed project', 'amount_irr':'not-money'})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'KEEP GOAL', status_code=400)
        self.assertContains(response, 'data-start-section="agreement"', status_code=400)
        self.assertTrue(response.context['contract_form'].errors)
        self.assertContains(response, 'Typed project', status_code=400)
        proposal.refresh_from_db()
        self.assertEqual(proposal.amount_irr, 123456789)

    def test_english_controls_are_localized_and_authored_content_preserved(self):
        self.package()
        response = self.client.get(f'/en/management/workspaces/{self.case.pk}/')
        self.assertContains(response, 'Package preparation')
        self.assertContains(response, 'Preview form and agreement')
        self.assertContains(response, '0%')
        self.assertNotContains(response, '۰٪')
        response = self.client.get(f'/en/management/workspaces/{self.case.pk}/preview/')
        self.assertContains(response, 'Back to preparation')
        self.assertContains(response, 'ماده ۱ ـ شرایط اختصاصی محفوظ')

    def test_list_query_count_does_not_grow_with_more_prepared_cases(self):
        self.package()
        url = reverse('management_portal:workspace_list')
        with CaptureQueriesContext(connection) as queries:
            self.client.get(url)
        baseline = len(queries)
        for n in range(4):
            case = CustomerCase.objects.create(kind='crm', customer_name=f'Case {n}', phone=self.case.phone)
            proposal, _ = ensure_case_workspace(case=case, actor=self.admin)
            create_specialist_template_version(proposal=proposal, schema=SCHEMA, actor=self.admin)
        with CaptureQueriesContext(connection) as queries:
            self.client.get(url)
        self.assertLessEqual(len(queries), baseline)

    def test_export_returns_only_to_matching_workspace(self):
        lead = Lead.objects.create(name='Export QA', phone='09120000045', email_or_telegram='export@example.test', website_url='https://project.example.test', request_type='ecommerce', timeline='one_three', preferred_contact='email', message='Full original response', privacy_accepted_at=timezone.now())
        case = CustomerCase.objects.get(source_content_type=ContentType.objects.get_for_model(Lead), source_object_id=lead.pk)
        url = reverse('management_portal:request_export', args=['lead', lead.pk])
        response = self.client.get(url, {'workspace':case.pk})
        self.assertContains(response, 'Full original response')
        self.assertContains(response, 'https://project.example.test')
        self.assertContains(response, 'export@example.test')
        for label in ('نوع درخواست:', 'بودجه:', 'زمان‌بندی:', 'روش تماس:'):
            self.assertContains(response, label)
        self.assertEqual(response.context['back_url'], reverse('management_portal:workspace_detail', args=[case.pk]) + '#base')
        for wrong in (self.case.pk, 'https://example.test', '9'*100):
            response = self.client.get(url, {'workspace':wrong})
            self.assertEqual(response.context['back_url'], reverse('management_portal:request_detail', args=['lead', lead.pk]))

    def test_activity_has_actual_total_and_pages_without_losing_case_scope(self):
        proposal = self.package()
        RoomEvent.objects.bulk_create([RoomEvent(proposal=proposal, event_type='login_succeeded') for _ in range(25)])
        total = proposal.room_events.count()
        response = self.client.get(self.url)
        self.assertEqual(response.context['events_page'].paginator.count, total)
        self.assertEqual(len(response.context['room_events']), 20)
        self.assertIn('events_page=2', response.context['events_page'].next_url)
        self.assertTrue(response.context['events_page'].next_url.endswith('#activity'))
        second = self.client.get(self.url, {'events_page':2})
        self.assertEqual(len(second.context['room_events']), total - 20)
        self.assertTrue(all(row['event'].proposal_id == proposal.pk for row in second.context['room_events']))

    def test_builder_ignores_deleted_blank_row_and_keeps_other_question(self):
        self.package()
        response = self.client.post(reverse('management_portal:workspace_questionnaire', args=[self.case.pk]), {
            'questions-TOTAL_FORMS':'2', 'questions-INITIAL_FORMS':'1',
            'questions-MIN_NUM_FORMS':'1', 'questions-MAX_NUM_FORMS':'120',
            'questions-0-section_title':'Preserved section', 'questions-0-question_label':'Preserved question',
            'questions-0-answer_type':'long_text', 'questions-1-answer_type':'long_text',
            'questions-1-DELETE':'on',
        })
        self.assertRedirects(response, self.url)
        proposal = ContractProposal.objects.get(customer_case=self.case)
        schema = proposal.specialist_assignment.version.schema
        self.assertEqual(len(schema), 1)
        self.assertEqual(len(schema[0]['questions']), 1)
        self.assertEqual(schema[0]['questions'][0]['label'], 'Preserved question')
