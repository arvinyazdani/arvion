"""Validation and progress helpers for versioned specialist questionnaires.

The public form renderer, autosave endpoint and management builder all consume the
same frozen JSON schema.  Keeping validation here prevents a browser-crafted POST
from introducing fields that were not approved in the published questionnaire.
"""

from __future__ import annotations

import re
from copy import deepcopy
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


ANSWER_TYPES = {
    "short_text",
    "long_text",
    "single_choice",
    "multiple_choice",
    "yes_no",
    "number",
    "date",
}
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MAX_SECTIONS = 20
MAX_QUESTIONS = 120
MAX_CHOICES = 40
MAX_SHORT_TEXT = 500
MAX_LONG_TEXT = 8000


def _text(value, *, label, maximum, required=False):
    rendered = str(value or "").strip()
    if required and not rendered:
        raise ValidationError(f"{label} الزامی است.")
    if len(rendered) > maximum:
        raise ValidationError(f"{label} بیش از حد مجاز طولانی است.")
    return rendered


def _key(value, *, label):
    rendered = _text(value, label=label, maximum=64, required=True)
    if not KEY_PATTERN.fullmatch(rendered):
        raise ValidationError(f"{label} معتبر نیست.")
    return rendered


def normalize_schema(schema):
    """Return a validated, serialisable questionnaire schema.

    Schema changes are allowed only while the surrounding assignment is a draft;
    that lifecycle rule lives in the management service.  This function only
    validates the immutable value stored on a template version/assignment.
    """

    if not isinstance(schema, list) or not schema:
        raise ValidationError("فرم تخصصی باید حداقل یک بخش داشته باشد.")
    if len(schema) > MAX_SECTIONS:
        raise ValidationError("تعداد بخش‌های فرم از حد مجاز بیشتر است.")

    normalized = []
    section_keys = set()
    question_count = 0
    for raw_section in schema:
        if not isinstance(raw_section, dict):
            raise ValidationError("ساختار یکی از بخش‌های فرم معتبر نیست.")
        section_key = _key(raw_section.get("key"), label="شناسه بخش")
        if section_key in section_keys:
            raise ValidationError("شناسه بخش‌ها باید یکتا باشد.")
        section_keys.add(section_key)
        raw_questions = raw_section.get("questions")
        if not isinstance(raw_questions, list) or not raw_questions:
            raise ValidationError("هر بخش باید حداقل یک سؤال داشته باشد.")
        section = {
            "key": section_key,
            "title": _text(raw_section.get("title"), label="عنوان بخش", maximum=180, required=True),
            "description": _text(raw_section.get("description"), label="توضیح بخش", maximum=800),
            "questions": [],
        }
        question_keys = set()
        for raw_question in raw_questions:
            question_count += 1
            if question_count > MAX_QUESTIONS:
                raise ValidationError("تعداد سؤال‌های فرم از حد مجاز بیشتر است.")
            if not isinstance(raw_question, dict):
                raise ValidationError("ساختار یکی از سؤال‌ها معتبر نیست.")
            question_key = _key(raw_question.get("key"), label="شناسه سؤال")
            if question_key in question_keys:
                raise ValidationError("شناسه سؤال‌ها باید در هر بخش یکتا باشد.")
            question_keys.add(question_key)
            answer_type = str(raw_question.get("type") or "long_text")
            if answer_type not in ANSWER_TYPES:
                raise ValidationError("نوع پاسخ یکی از سؤال‌ها پشتیبانی نمی‌شود.")
            choices = raw_question.get("choices") or []
            if answer_type in {"single_choice", "multiple_choice"}:
                if not isinstance(choices, list) or len(choices) < 2:
                    raise ValidationError("سؤال گزینه‌ای باید حداقل دو گزینه داشته باشد.")
                if len(choices) > MAX_CHOICES:
                    raise ValidationError("تعداد گزینه‌های یک سؤال از حد مجاز بیشتر است.")
                choices = [
                    _text(choice, label="متن گزینه", maximum=180, required=True)
                    for choice in choices
                ]
                if len(set(choices)) != len(choices):
                    raise ValidationError("گزینه‌های تکراری در یک سؤال مجاز نیست.")
            else:
                choices = []
            section["questions"].append({
                "key": question_key,
                "label": _text(raw_question.get("label"), label="متن سؤال", maximum=500, required=True),
                "help_text": _text(raw_question.get("help_text"), label="راهنمای سؤال", maximum=1200),
                "type": answer_type,
                "required": bool(raw_question.get("required", True)),
                "choices": choices,
                "placeholder": _text(raw_question.get("placeholder"), label="نمونه پاسخ", maximum=300),
            })
        normalized.append(section)
    return normalized


def schema_from_legacy_sections(sections):
    """Freeze the existing Noorbinan questionnaire without changing its keys."""

    return normalize_schema([
        {
            "key": section_key,
            "title": title,
            "description": description,
            "questions": [
                {
                    "key": question_key,
                    "label": label,
                    "help_text": help_text,
                    "type": "long_text",
                    "required": True,
                    "choices": [],
                    "placeholder": "پاسخ خود را با مثال واقعی بنویسید…",
                }
                for question_key, label, help_text in questions
            ],
        }
        for section_key, title, description, questions in sections
    ])


def section_for_key(schema, section_key):
    normalized = normalize_schema(schema)
    for section in normalized:
        if section["key"] == section_key:
            return section
    raise ValidationError("بخش در فرم تخصصی وجود ندارد.")


def clean_answer(question, value, *, enforce_required=False):
    """Validate one value against a frozen question definition."""

    required = bool(question.get("required")) and enforce_required
    answer_type = question["type"]
    if answer_type == "multiple_choice":
        if value in (None, ""):
            values = []
        elif isinstance(value, (list, tuple)):
            values = [str(item).strip() for item in value if str(item).strip()]
        else:
            values = [str(value).strip()]
        if required and not values:
            raise ValidationError("پاسخ به این سؤال الزامی است.")
        allowed = set(question.get("choices") or [])
        if any(item not in allowed for item in values) or len(values) != len(set(values)):
            raise ValidationError("یکی از گزینه‌های انتخاب‌شده معتبر نیست.")
        return values

    rendered = str(value or "").strip()
    if required and not rendered:
        raise ValidationError("پاسخ به این سؤال الزامی است.")
    if not rendered:
        return ""
    if answer_type in {"single_choice"} and rendered not in set(question.get("choices") or []):
        raise ValidationError("گزینه انتخاب‌شده معتبر نیست.")
    if answer_type == "yes_no" and rendered not in {"yes", "no"}:
        raise ValidationError("پاسخ بله یا خیر معتبر نیست.")
    if answer_type == "number":
        try:
            Decimal(rendered)
        except InvalidOperation as exc:
            raise ValidationError("مقدار عددی معتبر نیست.") from exc
    if answer_type == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rendered):
        raise ValidationError("تاریخ معتبر نیست.")
    maximum = MAX_SHORT_TEXT if answer_type in {"short_text", "single_choice", "yes_no", "number", "date"} else MAX_LONG_TEXT
    if len(rendered) > maximum:
        raise ValidationError("پاسخ بیش از حد مجاز طولانی است.")
    return rendered


def clean_section_answers(schema, section_key, values, *, enforce_required=True):
    section = section_for_key(schema, section_key)
    values = values if isinstance(values, dict) else {}
    return {
        question["key"]: clean_answer(
            question,
            values.get(question["key"]),
            enforce_required=enforce_required,
        )
        for question in section["questions"]
    }


def completion(schema, answers):
    """Calculate authoritative progress from schema and stored answers."""

    normalized = normalize_schema(schema)
    answers = answers if isinstance(answers, dict) else {}
    completed_sections = []
    total_questions = answered_questions = 0
    for section in normalized:
        section_values = answers.get(section["key"])
        section_values = section_values if isinstance(section_values, dict) else {}
        section_complete = True
        for question in section["questions"]:
            total_questions += 1
            raw_value = section_values.get(question["key"])
            try:
                cleaned = clean_answer(question, raw_value, enforce_required=True)
            except ValidationError:
                section_complete = False
                continue
            has_value = bool(cleaned) if not isinstance(cleaned, list) else bool(cleaned)
            if has_value:
                answered_questions += 1
        if section_complete:
            completed_sections.append(section["key"])
    total_sections = len(normalized)
    return {
        "completed_sections": completed_sections,
        "completed_section_count": len(completed_sections),
        "total_sections": total_sections,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "percent": round((len(completed_sections) / total_sections) * 100) if total_sections else 0,
        "is_complete": len(completed_sections) == total_sections,
    }


def merge_section_answers(answers, section_key, cleaned_values):
    merged = deepcopy(answers) if isinstance(answers, dict) else {}
    merged[section_key] = dict(cleaned_values)
    return merged
