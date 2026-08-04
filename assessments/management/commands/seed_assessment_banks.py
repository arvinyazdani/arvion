from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from assessments.models import Choice, Exam, ExamSection, ExamVersion, Question, Skill
from assessments.question_banks.english import QUESTIONS, SECTIONS


def validate_bank(questions, sections):
    quotas = {code: quota for code, _fa, _en, quota in sections}
    counts = {code: 0 for code in quotas}
    for index, item in enumerate(questions, start=1):
        if item["section"] not in quotas:
            raise CommandError(f"Question {index} has an unknown section")
        if len(item["choices"]) != 4 or len(set(item["choices"])) != 4:
            raise CommandError(f"Question {index} must have four unique choices")
        if not 1 <= item["difficulty"] <= 5:
            raise CommandError(f"Question {index} has an invalid difficulty")
        counts[item["section"]] += 1
    if counts != quotas:
        raise CommandError(f"Section counts {counts} do not match quotas {quotas}")


class Command(BaseCommand):
    help = "Publish validated, versioned assessment question banks"

    @transaction.atomic
    def handle(self, *args, **options):
        validate_bank(QUESTIONS, SECTIONS)
        exam = Exam.objects.get(slug="english-placement-a1-c1")
        version, created = ExamVersion.objects.get_or_create(exam=exam, version=1)
        if not created and version.questions.exists():
            if version.questions.count() != 50:
                raise CommandError("English v1 exists but is incomplete; create a new version instead of mutating it")
            self.stdout.write(self.style.WARNING("English v1 already exists; no records changed."))
            return
        section_models = {}
        skill_models = {}
        for order, (code, title_fa, title_en, quota) in enumerate(SECTIONS, start=1):
            skill_models[code] = Skill.objects.create(
                exam=exam, code=code, title_fa=title_fa, title_en=title_en, display_order=order,
            )
            section_models[code] = ExamSection.objects.create(
                version=version, code=code, title_fa=title_fa, title_en=title_en,
                question_count=quota, display_order=order,
            )
        for item in QUESTIONS:
            question = Question.objects.create(
                version=version, section=section_models[item["section"]], skill=skill_models[item["section"]],
                prompt_fa=item["prompt"], prompt_en=item["prompt"], difficulty=item["difficulty"],
                explanation_fa=item["explanation"], explanation_en=item["explanation"],
            )
            for order, text in enumerate(item["choices"]):
                Choice.objects.create(
                    question=question, text_fa=text, text_en=text,
                    is_correct=order == 0, display_order=order,
                )
        version.is_published = True
        version.published_at = timezone.now()
        version.save(update_fields=["is_published", "published_at"])
        self.stdout.write(self.style.SUCCESS("Published English placement v1 with 50 validated questions."))
