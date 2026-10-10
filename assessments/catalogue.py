"""Public assessment facts only; never question text, answers or user state."""
from django.db.models import Count, Prefetch, Q
from django.urls import reverse
from django.utils.translation import override
from .models import Exam, ExamVersion

PUBLIC_EXAM_SLUGS = ("english-placement-a1-c1", "python-django-professional")


def public_exam_catalogue(lang, exams=None):
    versions = ExamVersion.objects.filter(is_published=True).order_by("-version").annotate(
        bank_count=Count("questions", filter=Q(questions__is_active=True, questions__status="active"))
    ).prefetch_related("sections")
    exams = (exams if exams is not None else Exam.objects.filter(is_active=True, slug__in=PUBLIC_EXAM_SLUGS)).prefetch_related(
        Prefetch("versions", queryset=versions, to_attr="public_versions"))
    rows = []
    for exam in exams:
        version = exam.public_versions[0] if exam.public_versions else None
        sections = [{"title": getattr(s, "title_" + lang), "count": s.question_count}
                    for s in version.sections.all()] if version else []
        with override(lang):
            url = reverse("assessments:briefing", args=[exam.slug])
        rows.append({"slug": exam.slug, "title": getattr(exam, "title_" + lang),
                     "description": getattr(exam, "description_" + lang),
                     "questions": exam.question_count, "minutes": exam.duration_minutes,
                     "sections": sections, "bank_count": version.bank_count if version else 0,
                     "teacher_version": exam.slug == PUBLIC_EXAM_SLUGS[0] and bool(version and version.version >= 5),
                     "language": "English" if exam.language_mode == "en" else "فارسی و انگلیسی" if lang == "fa" else "Persian & English",
                     "url": url})
    return sorted(rows, key=lambda row: PUBLIC_EXAM_SLUGS.index(row["slug"]))
