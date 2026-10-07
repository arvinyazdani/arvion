from datetime import timedelta
import threading
import time
from unittest import skipUnless
from unittest.mock import patch
from django.db import close_old_connections, connection
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Attempt, IntegrityEvent, WelcomeAssessmentCredit, AttemptResult, Certificate, Order, ExamEntitlement
from .services import start_attempt, redeem_welcome_assessment, finalize_attempt_submission
from . import tests as fixtures


class WelcomeCopyStopTests(TestCase):
    # Reuse the fixture, not the inherited domain suite.
    setUp = fixtures.AssessmentEngineTests.setUp
    make_question = fixtures.AssessmentEngineTests.make_question
    def gift(self, accepted=True):
        self.order.gateway = 'welcome_trial'
        self.order.amount_irr = 0
        self.order.save(update_fields=['gateway', 'amount_irr'])
        WelcomeAssessmentCredit.objects.create(user=self.user, order=self.order)
        return start_attempt(self.entitlement.pk, self.user, copy_policy_accepted=accepted)[0]

    def copy(self, attempt, n):
        return self.client.post(reverse('assessments:integrity_event', args=[attempt.pk]),
            {'event_type':'copy', 'copy_scope':'question', 'copy_event_id':f'action-copy-{n}',
             'item_id':attempt.attempt_questions.first().pk})

    def stop(self, attempt):
        self.client.force_login(self.user)
        for n in range(1, 6):
            response = self.copy(attempt, n)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(bool(response.json().get('stopped')), n == 5)
        return response

    def test_fifth_copy_stops_only_gift_and_preserves_saved_answers(self):
        attempt = self.gift()
        self.client.force_login(self.user)
        item = attempt.attempt_questions.first()
        choice = item.choice_order[0]
        answer_url = reverse('assessments:save_answer', args=[attempt.pk, item.pk])
        self.assertEqual(self.client.post(answer_url, {'choice':choice}).status_code, 200)
        self.stop(attempt)
        attempt.refresh_from_db(); item.refresh_from_db(); self.user.refresh_from_db()
        self.assertEqual(attempt.status, 'invalidated')
        self.assertEqual(attempt.completion_reason, 'copy_limit')
        self.assertEqual(item.effective_selected_choice_id, choice)
        self.assertTrue(self.user.is_active)
        self.assertEqual(WelcomeAssessmentCredit.objects.get(user=self.user).order_id, self.order.pk)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertFalse(AttemptResult.objects.filter(attempt=attempt).exists())
        self.assertFalse(Certificate.objects.filter(result__attempt=attempt).exists())
        self.assertEqual(self.copy(attempt, 5).json()['copy_count'], 5)
        self.assertEqual(self.copy(attempt, 6).json()['copy_count'], 5)
        self.assertEqual(attempt.integrity_events.filter(metadata__kind='welcome_copy_stop').count(), 1)
        denied = self.client.post(answer_url, {'choice':item.choice_order[1]})
        self.assertEqual(denied.status_code, 409)
        self.assertTrue(denied.json()['result_url'])
        item.refresh_from_db()
        self.assertEqual(item.effective_selected_choice_id, choice)
        self.assertEqual(self.client.post(reverse('assessments:audio_play', args=[attempt.pk,item.pk])).status_code,409)
        self.client.post(reverse('assessments:finish_attempt', args=[attempt.pk]), {'confirm_submission':'yes'})
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'invalidated')
        self.assertFalse(AttemptResult.objects.filter(attempt=attempt).exists())
        self.assertEqual(start_attempt(self.entitlement.pk,self.user)[0].status,'invalidated')
        self.assertEqual(redeem_welcome_assessment(user=self.user,exam=self.exam)[0].pk,self.order.pk)

    def test_paid_attempt_warns_but_continues_at_five(self):
        attempt = start_attempt(self.entitlement.pk,self.user,copy_policy_accepted=True)[0]
        self.client.force_login(self.user)
        for n in range(1, 7):
            self.assertFalse(self.copy(attempt,n).json().get('stopped',False))
        attempt.refresh_from_db()
        self.assertEqual(attempt.status,'in_progress')

    def test_existing_unacknowledged_gift_is_not_retroactively_stopped(self):
        attempt = self.gift(accepted=False)
        self.client.force_login(self.user)
        for n in range(1, 7):
            self.assertFalse(self.copy(attempt,n).json().get('stopped',False))
        start_attempt(self.entitlement.pk,self.user,copy_policy_accepted=True)
        self.assertFalse(attempt.integrity_events.filter(metadata__kind='copy_policy_acceptance').exists())

    def test_audit_failure_rolls_back_fifth_event_and_stop_then_retry_succeeds(self):
        attempt=self.gift(); self.client.force_login(self.user)
        for n in range(1,5): self.copy(attempt,n)
        create=IntegrityEvent.objects.create
        def fail_stop_audit(**kwargs):
            if kwargs.get('metadata',{}).get('kind')=='welcome_copy_stop':
                raise RuntimeError('injected audit failure')
            return create(**kwargs)
        with patch.object(IntegrityEvent.objects,'create',side_effect=fail_stop_audit):
            with self.assertRaisesMessage(RuntimeError,'injected audit failure'):
                self.copy(attempt,5)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status,'in_progress')
        self.assertEqual(attempt.integrity_events.filter(event_type='copy').count(),4)
        self.assertTrue(self.copy(attempt,5).json()['stopped'])

    def test_zero_price_non_welcome_attempt_is_not_subject_to_gift_stop(self):
        self.order.amount_irr=0; self.order.gateway='free'
        self.order.save(update_fields=['amount_irr','gateway'])
        attempt=start_attempt(self.entitlement.pk,self.user,copy_policy_accepted=True)[0]
        self.client.force_login(self.user)
        for n in range(1,6): self.assertFalse(self.copy(attempt,n).json().get('stopped',False))
        attempt.refresh_from_db()
        self.assertEqual(attempt.status,'in_progress')

    def test_stop_page_and_appeal_are_available_without_payment(self):
        attempt = self.gift(); self.stop(attempt)
        for lang in ('fa','en'):
            response = self.client.get(f'/{lang}/assessments/attempt/{attempt.pk}/')
            self.assertContains(response,'copy-stop-title')
            self.assertContains(response,f'copy_appeal={attempt.pk}')
            self.assertNotContains(response,'answer-form')
            review=self.client.get(f'/{lang}/assessments/attempt/{attempt.pk}/review/')
            self.assertContains(review,'copy-stop-title')
            self.assertNotContains(review,'confirm_submission')
        appeal = self.client.get(reverse('assessments:support_create')+f'?copy_appeal={attempt.pk}')
        self.assertEqual(appeal.context['form'].initial['order'], self.order.pk)
        self.assertContains(appeal,attempt.get_absolute_url())
        submitted = self.client.post(reverse('assessments:support_create'), {'category':'technical',
            'order':self.order.pk,'subject':'Review copy stop','message':'A technical error occurred.'})
        self.assertEqual(submitted.status_code,302)
        self.assertEqual(self.user.assessment_tickets.count(),1)

    def test_invalid_appeal_id_does_not_crash(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('assessments:support_create')+'?copy_appeal=bad').status_code,200)

    def test_gift_start_requires_acknowledgement_and_records_it_once(self):
        self.order.gateway='welcome_trial'; self.order.save(update_fields=['gateway'])
        WelcomeAssessmentCredit.objects.create(user=self.user,order=self.order)
        self.client.force_login(self.user)
        url=reverse('assessments:start_attempt',args=[self.entitlement.pk])
        self.assertEqual(self.client.post(url).status_code,302)
        self.assertFalse(hasattr(self.entitlement,'attempt'))
        self.client.post(url,{'guidance_read':'yes'})
        attempt=Attempt.objects.get(entitlement=self.entitlement)
        self.client.post(url,{'guidance_read':'yes'})
        self.assertEqual(attempt.integrity_events.filter(metadata__kind='copy_policy_acceptance').count(),1)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False)
    def test_stopped_gift_can_order_paid_retake_without_erasing_history(self):
        attempt=self.gift(); self.stop(attempt)
        response=self.client.post(reverse('assessments:create_order',args=[self.exam.slug]))
        order=Order.objects.get(user=self.user,status='pending')
        self.assertEqual(response.status_code,302)
        self.assertIn(str(order.pk),response.url)
        self.assertGreater(order.amount_irr,0)
        self.assertNotEqual(order.gateway,'welcome_trial')
        attempt.refresh_from_db()
        self.assertEqual(attempt.completion_reason,'copy_limit')
        self.assertEqual(attempt.integrity_events.filter(event_type='copy').count(),5)
        # Simulate an approved new payment, never send a real payment request.
        order.status='paid'; order.save(update_fields=['status'])
        entitlement=ExamEntitlement.objects.create(user=self.user,exam=self.exam,order=order,attempts_remaining=1)
        retake=start_attempt(entitlement.pk,self.user,copy_policy_accepted=True)[0]
        for n in range(1,6): self.assertFalse(self.copy(retake,n).json().get('stopped',False))
        retake.refresh_from_db()
        self.assertEqual(retake.status,'in_progress')

    def test_expiry_never_scores_a_copy_stopped_gift(self):
        attempt=self.gift(); self.stop(attempt)
        Attempt.objects.filter(pk=attempt.pk).update(expires_at=timezone.now()-timedelta(hours=1))
        self.assertContains(self.client.get(attempt.get_absolute_url()),'copy-stop-title')
        self.assertIsNone(finalize_attempt_submission(attempt.pk,self.user.pk)[0])
        self.assertFalse(AttemptResult.objects.filter(attempt=attempt).exists())

    def test_appeal_and_attempt_are_owner_only_and_dashboard_keeps_a_return_path(self):
        attempt=self.gift(); self.stop(attempt)
        dashboard=self.client.get(reverse('accounts:dashboard'))
        self.assertContains(dashboard,attempt.get_absolute_url())
        other=type(self.user).objects.create_user(username='other@example.com',password='test-pass')
        self.client.force_login(other)
        appeal=self.client.get(reverse('assessments:support_create')+f'?copy_appeal={attempt.pk}')
        self.assertNotIn('order',appeal.context['form'].initial)
        self.assertEqual(self.client.get(attempt.get_absolute_url()).status_code,404)
        response=self.client.post(reverse('assessments:support_create'), {'category':'technical',
            'order':self.order.pk,'subject':'Review','message':'Please review.'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(other.assessment_tickets.count(),0)


@skipUnless(connection.vendor=='postgresql','PostgreSQL row locks required')
class WelcomeCopyStopConcurrencyTests(TransactionTestCase):
    setUp = fixtures.AssessmentFinishConcurrencyTests.setUp

    def prepare(self):
        order=self.attempt.entitlement.order
        order.gateway='welcome_trial'; order.save(update_fields=['gateway'])
        WelcomeAssessmentCredit.objects.create(user=self.user,order=order)
        IntegrityEvent.objects.create(attempt=self.attempt,event_type='other',metadata={
            'kind':'copy_policy_acceptance','copy_policy_version':2})
        self.item=self.attempt.attempt_questions.first()
        for n in range(4):
            IntegrityEvent.objects.create(attempt=self.attempt,attempt_question=self.item,
                event_type='copy',metadata={'copy_policy_version':1,'copy_event_id':f'prior-{n}'})

    def test_stop_lock_prevents_concurrent_save_and_finalization(self):
        from .views import IntegrityEventView, SaveAnswerView
        from .integrity import stop_welcome_copy_attempt
        self.prepare()
        held, release=threading.Event(),threading.Event()
        outcomes, errors, pids={},[],{}
        def held_stop(attempt):
            held.set()
            if not release.wait(5): raise RuntimeError('test lock timeout')
            return stop_welcome_copy_attempt(attempt)
        def run(name, action):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pids[name]=cursor.fetchone()[0]
                outcomes[name]=action()
            except Exception as exc: errors.append(exc)
            finally: close_old_connections()
        def copy():
            request=RequestFactory().post('/',{'event_type':'copy','copy_scope':'question',
                'copy_event_id':'fifth-copy','item_id':self.item.pk})
            request.user=self.user
            return IntegrityEventView.as_view()(request,pk=self.attempt.pk).status_code
        def save():
            request=RequestFactory().post('/',{'choice':self.item.choice_order[0]})
            request.user=self.user
            return SaveAnswerView.as_view()(request,pk=self.attempt.pk,item_pk=self.item.pk).status_code
        def finish(): return finalize_attempt_submission(self.attempt.pk,self.user.pk)[0]
        with patch('assessments.views.stop_welcome_copy_attempt',held_stop):
            threads=[threading.Thread(target=run,args=('copy',copy))]
            threads[0].start()
            try:
                self.assertTrue(held.wait(5))
                for name,fn in [('save',save),('finish',finish)]:
                    thread=threading.Thread(target=run,args=(name,fn)); threads.append(thread); thread.start()
                # Prove both writers actually wait on the stop transaction,
                # rather than merely running after it due to thread scheduling.
                waiting=0
                deadline=time.monotonic()+3
                while waiting<2 and time.monotonic()<deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE pid = ANY(%s) AND wait_event_type = 'Lock'",[[pids.get('save'),pids.get('finish')]])
                        waiting=cursor.fetchone()[0]
                    if waiting<2: threading.Event().wait(0.02)
            finally:
                release.set()
                for thread in threads: thread.join(10)
        self.assertEqual(waiting,2)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors,[])
        self.assertEqual(outcomes,{'copy':200,'save':409,'finish':None})
        self.attempt.refresh_from_db(); self.item.refresh_from_db()
        self.assertEqual(self.attempt.completion_reason,'copy_limit')
        self.assertIsNotNone(self.item.effective_selected_choice_id)
        self.assertFalse(AttemptResult.objects.filter(attempt=self.attempt).exists())
        self.assertFalse(Certificate.objects.filter(result__attempt=self.attempt).exists())
