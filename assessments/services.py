import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Attempt, AttemptQuestion, ExamEntitlement, ExamVersion, Order, PaymentTransaction, Question


class ExamContentError(Exception):
    pass


@transaction.atomic
def verify_sandbox_payment(order_id):
    order = Order.objects.select_for_update().select_related("exam", "user").get(pk=order_id)
    if order.status == "paid":
        return order, False
    external_id = f"sandbox-{order.id}"
    payment, _ = PaymentTransaction.objects.get_or_create(
        external_id=external_id,
        defaults={"order": order, "gateway": "sandbox", "amount_irr": order.amount_irr},
    )
    if payment.amount_irr != order.amount_irr:
        order.status = "failed"
        order.save(update_fields=["status", "updated_at"])
        payment.status = "failed"
        payment.raw_response = {"reason": "amount_mismatch"}
        payment.save(update_fields=["status", "raw_response"])
        return order, False
    now = timezone.now()
    payment.status = "verified"
    payment.verified_at = now
    payment.raw_response = {"sandbox": True, "verified": True}
    payment.save(update_fields=["status", "verified_at", "raw_response"])
    order.status = "paid"
    order.paid_at = now
    order.save(update_fields=["status", "paid_at", "updated_at"])
    ExamEntitlement.objects.get_or_create(
        order=order,
        defaults={"user": order.user, "exam": order.exam, "attempts_remaining": 1},
    )
    return order, True


@transaction.atomic
def start_attempt(entitlement_id, user):
    entitlement = ExamEntitlement.objects.select_for_update().select_related("exam").get(pk=entitlement_id, user=user)
    if hasattr(entitlement, "attempt"):
        return entitlement.attempt, False
    if entitlement.attempts_remaining < 1:
        raise ExamContentError("No attempts remaining")
    version = ExamVersion.objects.filter(exam=entitlement.exam, is_published=True).order_by("-version").first()
    if not version:
        raise ExamContentError("No published exam version")
    selected_questions = []
    rng = random.SystemRandom()
    for section in version.sections.all():
        pool = list(Question.objects.filter(version=version, section=section, is_active=True).values_list("id", flat=True))
        if len(pool) < section.question_count:
            raise ExamContentError(f"Section {section.code} does not have enough active questions")
        section_ids = rng.sample(pool, section.question_count)
        rng.shuffle(section_ids)
        selected_questions.extend(section_ids)
    if len(selected_questions) != entitlement.exam.question_count:
        raise ExamContentError("Published section quotas do not match the exam question count")
    questions = {q.id: q for q in Question.objects.filter(id__in=selected_questions).prefetch_related("choices")}
    now = timezone.now()
    attempt = Attempt.objects.create(
        user=user,
        exam=entitlement.exam,
        version=version,
        entitlement=entitlement,
        status="in_progress",
        started_at=now,
        expires_at=now + timedelta(minutes=entitlement.exam.duration_minutes),
    )
    rows = []
    for position, question_id in enumerate(selected_questions, start=1):
        question = questions[question_id]
        choice_ids = [choice.id for choice in question.choices.all()]
        if len(choice_ids) != 4 or question.choices.filter(is_correct=True).count() != 1:
            raise ExamContentError(f"Question {question.id} must have four choices and one correct answer")
        rng.shuffle(choice_ids)
        rows.append(AttemptQuestion(attempt=attempt, question=question, position=position, choice_order=choice_ids))
    AttemptQuestion.objects.bulk_create(rows)
    entitlement.attempts_remaining -= 1
    entitlement.save(update_fields=["attempts_remaining"])
    return attempt, True


def expire_if_needed(attempt):
    if attempt.status == "in_progress" and attempt.expires_at <= timezone.now():
        attempt.status = "expired"
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["status", "submitted_at", "updated_at"])
        return True
    return False
