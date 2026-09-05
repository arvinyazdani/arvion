from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from assessments.models import Choice, Exam, ExamSection, ExamVersion, Question, Skill
from assessments.question_banks.english import BANK_VERSION as EN_VERSION
from assessments.question_banks.english import QUESTIONS as EN_QUESTIONS, SECTIONS as EN_SECTIONS
from assessments.question_banks.python_django import BANK_VERSION as PY_VERSION
from assessments.question_banks.python_django import QUESTIONS as PY_QUESTIONS, SECTIONS as PY_SECTIONS


def section_spec(section):
    if len(section) == 4:
        code, title_fa, title_en, count = section
        return code, title_fa, title_en, count, count
    return section


def scaled_difficulty_distribution(counts, bank_count, exam_count):
    exact = {level: count * exam_count / bank_count for level, count in counts.items()}
    scaled = {str(level): int(value) for level, value in exact.items()}
    remaining = exam_count - sum(scaled.values())
    priorities = sorted(exact, key=lambda level: (exact[level] - int(exact[level]), counts[level]), reverse=True)
    for level in priorities[:remaining]:
        scaled[str(level)] += 1
    return {level: quota for level, quota in scaled.items() if quota}


def validate_bank(questions, sections):
    bank_counts = {code: bank_count for code, _fa, _en, bank_count, _exam_count in map(section_spec, sections)}
    counts = {code: 0 for code in bank_counts}
    seen_prompts = set()
    for index, item in enumerate(questions, start=1):
        prompt_en = item.get("prompt_en", item.get("prompt", "")).strip()
        prompt_fa = item.get("prompt_fa", prompt_en).strip()
        if not prompt_en or not prompt_fa:
            raise CommandError(f"Question {index} must have complete prompts")
        prompt_key = (prompt_fa.casefold(), prompt_en.casefold())
        if prompt_key in seen_prompts:
            raise CommandError(f"Question {index} duplicates an existing prompt")
        seen_prompts.add(prompt_key)
        if item["section"] not in bank_counts:
            raise CommandError(f"Question {index} has an unknown section")
        choices = item.get("choices", ())
        if len(choices) != 4 or len(set(choices)) != 4 or any(not choice.strip() for choice in choices):
            raise CommandError(f"Question {index} must have four unique choices")
        explanation_fa = item.get("explanation_fa", item.get("explanation", "")).strip()
        explanation_en = item.get("explanation_en", item.get("explanation", "")).strip()
        if not explanation_fa or not explanation_en:
            raise CommandError(f"Question {index} must have bilingual explanations")
        if not 1 <= item["difficulty"] <= 5:
            raise CommandError(f"Question {index} has an invalid difficulty")
        counts[item["section"]] += 1
    if counts != bank_counts:
        raise CommandError(f"Section counts {counts} do not match bank targets {bank_counts}")


class Command(BaseCommand):
    help = "Create assessment products and publish validated, versioned question banks"

    @transaction.atomic
    def handle(self, *args, **options):
        self.publish("english-placement-a1-c1", EN_VERSION, EN_QUESTIONS, EN_SECTIONS, english_only=True)
        self.publish("python-django-professional", PY_VERSION, PY_QUESTIONS, PY_SECTIONS, english_only=False)

    def publish(self, slug, version_number, questions, sections, english_only):
        validate_bank(questions, sections)
        catalog = {
            "english-placement-a1-c1": {
                "title_fa": "تعیین سطح انگلیسی A1 تا C1", "title_en": "English Placement Test A1–C1",
                "description_fa": "ارزیابی گرامر، واژگان، درک مطلب، کاربرد زبان، شنیدار و مهارت‌های نوشتاری.",
                "description_en": "A structured assessment of grammar, vocabulary, reading, use of English, listening, and writing skills.",
                "language_mode": "en", "question_count": 50, "duration_minutes": 75,
                "price_irr": 2_000_000, "is_active": True, "display_order": 1,
            },
            "python-django-professional": {
                "title_fa": "ارزیابی تخصصی Python و Django", "title_en": "Professional Python & Django Assessment",
                "description_fa": "سنجش عملی Python، حل مسئله، دیتابیس، تست، امنیت و استقرار پروژه‌های Django.",
                "description_en": "A practical assessment of Python, problem solving, databases, testing, security, and Django deployment.",
                "language_mode": "bilingual", "question_count": 50, "duration_minutes": 70,
                "price_irr": 2_000_000, "is_active": True, "display_order": 2,
            },
        }
        exam, _ = Exam.objects.update_or_create(slug=slug, defaults=catalog[slug])
        version, created = ExamVersion.objects.get_or_create(exam=exam, version=version_number)
        if not created and version.questions.exists():
            if version.questions.count() != len(questions):
                raise CommandError(f"{slug} v{version_number} exists but is incomplete; publish a new version")
            self.stdout.write(self.style.WARNING(f"{slug} v{version_number} already exists; no records changed."))
            return
        section_models = {}
        skill_models = {}
        for order, raw_section in enumerate(sections, start=1):
            code, title_fa, title_en, bank_count, exam_count = section_spec(raw_section)
            difficulty_distribution = Counter(
                item["difficulty"] for item in questions if item["section"] == code
            )
            skill_models[code], _ = Skill.objects.update_or_create(
                exam=exam, code=code,
                defaults={"title_fa": title_fa, "title_en": title_en, "display_order": order},
            )
            section_models[code] = ExamSection.objects.create(
                version=version, code=code, title_fa=title_fa, title_en=title_en,
                question_count=exam_count,
                difficulty_distribution=scaled_difficulty_distribution(
                    difficulty_distribution, bank_count, exam_count,
                ),
                display_order=order,
            )
        for item in questions:
            prompt_en = item.get("prompt_en", item.get("prompt"))
            prompt_fa = prompt_en if english_only else item["prompt_fa"]
            question = Question.objects.create(
                version=version, section=section_models[item["section"]], skill=skill_models[item["section"]],
                prompt_fa=prompt_fa, prompt_en=prompt_en, difficulty=item["difficulty"],
                question_type=item.get("question_type", "single_choice"),
                subskill=item.get("subskill", item["section"]),
                content_group=item.get("content_group", ""),
                suggested_seconds=item.get("suggested_seconds", 60),
                audio_path=item.get("audio_path", ""), transcript=item.get("transcript", ""),
                max_plays=item.get("max_plays", 0),
                explanation_fa=item.get("explanation_fa", item.get("explanation")),
                explanation_en=item.get("explanation_en", item.get("explanation")),
            )
            for order, text in enumerate(item["choices"]):
                choice_explanations_fa = item.get("choice_explanations_fa", ())
                choice_explanations_en = item.get("choice_explanations_en", ())
                Choice.objects.create(
                    question=question, text_fa=text, text_en=text,
                    explanation_fa=choice_explanations_fa[order] if choice_explanations_fa else "",
                    explanation_en=choice_explanations_en[order] if choice_explanations_en else "",
                    is_correct=order == 0, display_order=order,
                )
        version.is_published = True
        version.published_at = timezone.now()
        version.save(update_fields=["is_published", "published_at"])
        self.stdout.write(self.style.SUCCESS(
            f"Published {slug} v{version_number} with {len(questions)} validated questions."
        ))
from collections import Counter
