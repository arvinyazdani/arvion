from time import perf_counter

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from assessments.models import (
    Choice, Exam, ExamEntitlement, ExamSection, ExamVersion, Order, Question, Skill,
)
from assessments.services import score_attempt, start_attempt


class Command(BaseCommand):
    help = "Benchmark full 50-question attempt generation and deterministic scoring; always rolls back data"

    def add_arguments(self, parser):
        parser.add_argument("--attempts", type=int, default=100)

    def handle(self, *args, **options):
        count = options["attempts"]
        if count < 1 or count > 5000:
            raise ValueError("--attempts must be between 1 and 5000")
        timings = []
        with transaction.atomic():
            user = get_user_model().objects.create(
                username="benchmark@local.invalid", email="benchmark@local.invalid",
                is_active=True, email_verified=True,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            exam = Exam.objects.create(
                slug="benchmark-50", title_fa="بنچمارک", title_en="Benchmark",
                description_fa="موقت", description_en="Temporary", language_mode="bilingual",
                question_count=50, duration_minutes=60, is_active=False,
            )
            version = ExamVersion.objects.create(
                exam=exam, version=1, is_published=True, published_at=timezone.now(),
            )
            skill = Skill.objects.create(exam=exam, code="benchmark", title_fa="بنچمارک", title_en="Benchmark")
            section = ExamSection.objects.create(
                version=version, code="benchmark", title_fa="بنچمارک", title_en="Benchmark", question_count=50,
            )
            for index in range(50):
                question = Question.objects.create(
                    version=version, section=section, skill=skill,
                    prompt_fa=f"سؤال {index}", prompt_en=f"Question {index}",
                )
                Choice.objects.bulk_create([
                    Choice(question=question, text_fa=f"گزینه {choice}", text_en=f"Choice {choice}", is_correct=choice == 0)
                    for choice in range(4)
                ])
            started = perf_counter()
            for _ in range(count):
                lap = perf_counter()
                order = Order.objects.create(user=user, exam=exam, amount_irr=exam.price_irr, status="paid", gateway="benchmark")
                entitlement = ExamEntitlement.objects.create(user=user, exam=exam, order=order)
                attempt, _ = start_attempt(entitlement.pk, user, enforce_daily_limit=False)
                attempt.status = "submitted"
                attempt.submitted_at = timezone.now()
                attempt.save(update_fields=["status", "submitted_at", "updated_at"])
                score_attempt(attempt.pk)
                timings.append(perf_counter() - lap)
            elapsed = perf_counter() - started
            transaction.set_rollback(True)
        ordered = sorted(timings)
        p95 = ordered[max(0, int(len(ordered) * .95) - 1)]
        self.stdout.write(self.style.SUCCESS(
            f"attempts={count} elapsed={elapsed:.2f}s throughput={count / elapsed:.2f}/s "
            f"avg={sum(timings) / count * 1000:.1f}ms p95={p95 * 1000:.1f}ms rollback=yes"
        ))
