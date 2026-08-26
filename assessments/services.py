import random
import secrets
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Subquery
from django.utils import timezone

from .models import (
    Attempt, AttemptQuestion, AttemptResult, Certificate, ExamEntitlement,
    ExamVersion, ManualPaymentSubmission, Order, PaymentTransaction, Question, SkillResult,
)


class ExamContentError(Exception):
    pass


class AttemptLimitError(Exception):
    pass


class PaymentVerificationError(Exception):
    pass


SENSITIVE_GATEWAY_FIELDS = {
    "authorization", "card_number", "card_pan", "cvv", "password", "secret", "token",
}


def _safe_gateway_response(payload):
    """Keep useful audit metadata without persisting credentials or full card data."""
    if not isinstance(payload, dict):
        return {}
    return {
        str(key)[:80]: value
        for key, value in payload.items()
        if str(key).lower() not in SENSITIVE_GATEWAY_FIELDS
        and isinstance(value, (str, int, float, bool, type(None)))
    }


def _choose_section_questions(pool, count, rng, recent_ids, difficulty_distribution=None):
    """Choose an auditable, balanced set while preferring unseen content groups."""
    distribution = {int(level): int(quota) for level, quota in (difficulty_distribution or {}).items()}
    if distribution and sum(distribution.values()) != count:
        raise ExamContentError("Section difficulty blueprint does not match its question quota")
    buckets = distribution or {0: count}
    chosen = []
    used_groups = set()
    for difficulty, quota in buckets.items():
        candidates = [item for item in pool if difficulty == 0 or item[1] == difficulty]
        unseen = [item for item in candidates if item[0] not in recent_ids]
        repeated = [item for item in candidates if item[0] in recent_ids]
        rng.shuffle(unseen)
        rng.shuffle(repeated)
        for candidate in unseen + repeated:
            question_id, _difficulty, content_group = candidate
            if question_id in chosen or (content_group and content_group in used_groups):
                continue
            chosen.append(question_id)
            if content_group:
                used_groups.add(content_group)
            if sum(1 for selected in chosen if selected in {item[0] for item in candidates}) >= quota:
                break
        selected_for_bucket = sum(1 for selected in chosen if selected in {item[0] for item in candidates})
        if selected_for_bucket < quota:
            raise ExamContentError(f"Not enough eligible questions for difficulty {difficulty}")
    return chosen


@transaction.atomic
def verify_gateway_payment(order_id, *, gateway, external_id, amount_irr, response=None):
    """Verify a provider-confirmed payment exactly once and grant one entitlement."""
    order = Order.objects.select_for_update().select_related("exam", "user").get(pk=order_id)
    gateway = str(gateway).strip().lower()
    external_id = str(external_id).strip()
    if not gateway or gateway != order.gateway:
        raise PaymentVerificationError("Payment gateway does not match the order")
    if not external_id or len(external_id) > 120:
        raise PaymentVerificationError("Invalid gateway transaction identifier")
    if amount_irr != order.amount_irr:
        raise PaymentVerificationError("Verified amount does not match the order")
    if order.status == "paid":
        payment = PaymentTransaction.objects.filter(external_id=external_id).first()
        if not payment or payment.order_id != order.id or payment.gateway != gateway or payment.amount_irr != amount_irr:
            raise PaymentVerificationError("Paid order does not match this transaction")
        return order, False
    if not order.terms_accepted_at or not order.terms_version:
        raise PaymentVerificationError("Assessment terms must be accepted before payment")
    existing = PaymentTransaction.objects.select_for_update().filter(external_id=external_id).first()
    if existing and (existing.order_id != order.id or existing.gateway != gateway or existing.amount_irr != amount_irr):
        raise PaymentVerificationError("Gateway transaction is already linked to another payment")
    payment = existing or PaymentTransaction.objects.create(
        external_id=external_id, order=order, gateway=gateway, amount_irr=amount_irr,
    )
    now = timezone.now()
    payment.status = "verified"
    payment.verified_at = now
    payment.raw_response = {**_safe_gateway_response(response), "verified": True}
    payment.save(update_fields=["status", "verified_at", "raw_response"])
    order.status = "paid"
    order.paid_at = now
    order.save(update_fields=["status", "paid_at", "updated_at"])
    ExamEntitlement.objects.get_or_create(
        order=order,
        defaults={"user": order.user, "exam": order.exam, "attempts_remaining": 1},
    )
    return order, True


def verify_sandbox_payment(order_id):
    order = Order.objects.get(pk=order_id)
    gateway = "free" if settings.ASSESSMENT_FREE_CHECKOUT and order.amount_irr == 0 else "sandbox"
    return verify_gateway_payment(
        order.id,
        gateway=gateway,
        external_id=f"{gateway}-{order.id}",
        amount_irr=order.amount_irr,
        response={"sandbox": gateway == "sandbox", "free_checkout": gateway == "free"},
    )


@transaction.atomic
def approve_manual_payment(submission_id, *, reviewer=None, review_note="", automatic=False):
    """Approve one pending card transfer exactly once and grant its entitlement.

    Manager actions and the timed fallback share this lock-protected path so a
    race at the three-minute boundary cannot issue duplicate access.
    """
    submission = ManualPaymentSubmission.objects.select_for_update().select_related(
        "order__user", "order__exam",
    ).get(pk=submission_id)
    if submission.status != "pending":
        return submission, submission.order, False, False
    order, transaction_created = verify_gateway_payment(
        submission.order_id,
        gateway="card_transfer",
        external_id=f"card-{submission.reference_number}",
        amount_irr=submission.order.amount_irr,
        response={
            "manual_review": not automatic,
            "automatic_review": automatic,
            "reference": submission.reference_number,
        },
    )
    submission.status = "approved"
    submission.reviewed_by = reviewer
    submission.reviewed_at = timezone.now()
    submission.review_note = review_note.strip()[:500]
    submission.save(update_fields=[
        "status", "reviewed_by", "reviewed_at", "review_note", "updated_at",
    ])
    return submission, order, transaction_created, True


@transaction.atomic
def start_attempt(entitlement_id, user, *, enforce_daily_limit=True):
    entitlement = ExamEntitlement.objects.select_for_update().select_related("exam").get(pk=entitlement_id, user=user)
    if hasattr(entitlement, "attempt"):
        return entitlement.attempt, False
    now = timezone.now()
    if entitlement.expires_at is not None and entitlement.expires_at <= now:
        raise ExamContentError("Assessment entitlement has expired")
    if entitlement.attempts_remaining < 1:
        raise ExamContentError("No attempts remaining")
    get_user_model().objects.select_for_update().get(pk=user.pk)
    since = now - timedelta(hours=24)
    recent_count = Attempt.objects.filter(
        user_id=user.pk, exam=entitlement.exam, started_at__gte=since,
    ).count()
    if enforce_daily_limit and recent_count >= settings.ASSESSMENT_ATTEMPTS_PER_DAY:
        raise AttemptLimitError("Daily assessment attempt limit reached")
    version = ExamVersion.objects.filter(exam=entitlement.exam, is_published=True).order_by("-version").first()
    if not version:
        raise ExamContentError("No published exam version")
    selected_questions = []
    selection_seed = secrets.token_hex(32)
    rng = random.Random(selection_seed)
    recent_attempts = Attempt.objects.filter(
        user=user, exam=entitlement.exam,
    ).order_by("-created_at").values("pk")[:3]
    recent_question_ids = set(AttemptQuestion.objects.filter(
        attempt_id__in=Subquery(recent_attempts),
    ).values_list("question_id", flat=True))
    for section in version.sections.all():
        pool = list(Question.objects.filter(
            version=version, section=section, is_active=True, status="active",
        ).values_list("id", "difficulty", "content_group"))
        if len(pool) < section.question_count:
            raise ExamContentError(f"Section {section.code} does not have enough active questions")
        section_ids = _choose_section_questions(
            pool, section.question_count, rng, recent_question_ids,
            section.difficulty_distribution,
        )
        rng.shuffle(section_ids)
        selected_questions.extend(section_ids)
    if len(selected_questions) != entitlement.exam.question_count:
        raise ExamContentError("Published section quotas do not match the exam question count")
    questions = {
        q.id: q for q in Question.objects.filter(id__in=selected_questions)
        .select_related("section", "skill")
        .prefetch_related("choices")
    }
    attempt = Attempt.objects.create(
        user=user,
        exam=entitlement.exam,
        version=version,
        entitlement=entitlement,
        status="in_progress",
        selection_seed=selection_seed,
        started_at=now,
        expires_at=now + timedelta(minutes=entitlement.exam.duration_minutes),
    )
    rows = []
    for position, question_id in enumerate(selected_questions, start=1):
        question = questions[question_id]
        question_choices = list(question.choices.all())
        choice_ids = [choice.id for choice in question_choices]
        if len(choice_ids) != 4 or sum(choice.is_correct for choice in question_choices) != 1:
            raise ExamContentError(f"Question {question.id} must have four choices and one correct answer")
        rng.shuffle(choice_ids)
        question_snapshot = {
            "prompt_fa": question.prompt_fa, "prompt_en": question.prompt_en,
            "question_type": question.question_type, "subskill": question.subskill,
            "difficulty": question.difficulty, "weight": str(question.weight),
            "suggested_seconds": question.suggested_seconds,
            "audio_path": question.audio_path, "transcript": question.transcript,
            "max_plays": question.max_plays,
            "explanation_fa": question.explanation_fa, "explanation_en": question.explanation_en,
            "section_code": question.section.code,
            "section_title_fa": question.section.title_fa,
            "section_title_en": question.section.title_en,
            "skill_code": question.skill.code,
        }
        choices_snapshot = [
            {
                "id": choice.id, "text_fa": choice.text_fa, "text_en": choice.text_en,
                "explanation_fa": choice.explanation_fa, "explanation_en": choice.explanation_en,
                "is_correct": choice.is_correct,
            }
            for choice in question_choices
        ]
        rows.append(AttemptQuestion(
            attempt=attempt, question=question, position=position, choice_order=choice_ids,
            question_snapshot=question_snapshot, choices_snapshot=choices_snapshot,
        ))
    AttemptQuestion.objects.bulk_create(rows)
    Question.objects.filter(id__in=selected_questions).update(exposure_count=F("exposure_count") + 1)
    entitlement.attempts_remaining -= 1
    entitlement.save(update_fields=["attempts_remaining"])
    return attempt, True


def expire_if_needed(attempt):
    if attempt.status == "in_progress" and attempt.expires_at <= timezone.now():
        attempt.status = "expired"
        attempt.completion_reason = "timeout"
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["status", "completion_reason", "submitted_at", "updated_at"])
        return True
    return False


@transaction.atomic
def finalize_expired_attempt(attempt_id):
    attempt = Attempt.objects.select_for_update().get(pk=attempt_id)
    expire_if_needed(attempt)
    if hasattr(attempt, "result"):
        return attempt.result
    if attempt.status == "expired":
        return score_attempt(attempt.pk)[0]
    return None


def _level_for(exam, percentage):
    value = float(percentage)
    if exam.slug == "english-placement-a1-c1":
        bands = (
            (20, "A1", "مقدماتی", "Beginner"), (40, "A2", "پایه", "Elementary"),
            (60, "B1", "متوسط", "Intermediate"), (75, "B2", "بالاتر از متوسط", "Upper-intermediate"),
            (101, "C1", "پیشرفته", "Advanced"),
        )
    else:
        bands = (
            (40, "foundation", "پایه", "Foundation"), (60, "junior", "جونیور", "Junior"),
            (75, "intermediate", "متوسط", "Intermediate"), (90, "advanced", "پیشرفته", "Advanced"),
            (101, "expert", "متخصص", "Expert"),
        )
    return next((code, title_fa, title_en) for ceiling, code, title_fa, title_en in bands if value < ceiling)


@transaction.atomic
def score_attempt(attempt_id):
    attempt = Attempt.objects.select_for_update().select_related("exam").get(pk=attempt_id)
    if hasattr(attempt, "result"):
        return attempt.result, False
    if attempt.status not in {"submitted", "expired", "scoring"}:
        raise ExamContentError("Attempt is not ready for scoring")
    attempt.status = "scoring"
    attempt.save(update_fields=["status", "updated_at"])
    rows = list(attempt.attempt_questions.select_related("question__skill", "selected_choice"))
    maximum = sum(
        (Decimal(row.question_snapshot.get("weight", str(row.question.weight))) for row in rows),
        Decimal("0"),
    )
    earned = Decimal("0")
    correct = incorrect = unanswered = 0
    skill_totals = {}
    for row in rows:
        skill = row.question.skill
        stats = skill_totals.setdefault(skill.pk, {"skill": skill, "correct": 0, "total": 0})
        stats["total"] += 1
        selected_choice_id = row.effective_selected_choice_id
        if selected_choice_id is None:
            unanswered += 1
        else:
            snapshot_choice = next(
                (choice for choice in row.choices_snapshot if choice["id"] == selected_choice_id),
                None,
            )
            is_correct = (
                snapshot_choice["is_correct"]
                if snapshot_choice
                else bool(row.selected_choice and row.selected_choice.is_correct)
            )
        if selected_choice_id is not None and is_correct:
            correct += 1
            stats["correct"] += 1
            earned += Decimal(row.question_snapshot.get("weight", str(row.question.weight)))
            Question.objects.filter(pk=row.question_id).update(
                correct_response_count=F("correct_response_count") + 1,
            )
        elif selected_choice_id is not None:
            incorrect += 1
    percentage = ((earned / maximum * 100) if maximum else Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    level_code, level_fa, level_en = _level_for(attempt.exam, percentage)
    skill_payload = []
    strengths = []
    weaknesses = []
    for stats in skill_totals.values():
        skill_percentage = (Decimal(stats["correct"]) / Decimal(stats["total"]) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        payload = {
            "code": stats["skill"].code, "title_fa": stats["skill"].title_fa,
            "title_en": stats["skill"].title_en, "percentage": float(skill_percentage),
        }
        skill_payload.append((stats, skill_percentage))
        if skill_percentage >= 75:
            strengths.append(payload)
        elif skill_percentage < 60:
            weaknesses.append(payload)
    summary_fa = f"سطح شما {level_fa} با امتیاز {percentage} از ۱۰۰ است. این تحلیل بر اساس پاسخ‌های ثبت‌شده و قواعد ثابت آزمون تولید شده است."
    summary_en = f"Your level is {level_en} with a score of {percentage} out of 100. This analysis was generated from your recorded answers using fixed assessment rules."
    result = AttemptResult.objects.create(
        attempt=attempt, correct_count=correct, incorrect_count=incorrect,
        unanswered_count=unanswered, percentage=percentage, level_code=level_code,
        level_title_fa=level_fa, level_title_en=level_en, summary_fa=summary_fa,
        summary_en=summary_en, strengths=strengths, weaknesses=weaknesses,
    )
    SkillResult.objects.bulk_create([
        SkillResult(
            result=result, skill=stats["skill"], correct_count=stats["correct"],
            question_count=stats["total"], percentage=skill_percentage,
        ) for stats, skill_percentage in skill_payload
    ])
    Certificate.objects.create(
        result=result,
        holder_name=attempt.user.get_full_name().strip() or "Rvion Candidate",
        verification_code=secrets.token_hex(6).upper(),
    )
    attempt.status = "completed"
    attempt.save(update_fields=["status", "updated_at"])
    return result, True
