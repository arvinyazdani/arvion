from collections import Counter
from difflib import SequenceMatcher


GENERIC_EXPLANATION_MARKERS = (
    "only option that is grammatically and contextually appropriate",
    "matches the defined behavior of this concept",
    "پاسخ درست است و دقیقاً با قواعد",
    "is correct and matches the",
)


def normalized(value):
    return " ".join((value or "").casefold().split())


def audit_bank(questions, sections):
    """Return actionable editorial metrics without mutating a question bank."""
    issues = []
    warnings = []
    section_codes = {row[0] for row in sections}
    prompts = []
    distributions = Counter()
    subskills = Counter()

    for index, question in enumerate(questions, 1):
        prompt = question.get("prompt_en", question.get("prompt", ""))
        prompts.append((index, normalized(prompt)))
        distributions[(question.get("section"), question.get("difficulty"))] += 1
        subskills[question.get("subskill") or question.get("section")] += 1
        choices = [normalized(choice) for choice in question.get("choices", ())]
        if len(set(choices)) != len(choices):
            issues.append(f"Q{index}: choices collide after case/space normalization")
        if question.get("section") not in section_codes:
            issues.append(f"Q{index}: unknown section")
        explanation = " ".join((
            question.get("explanation", ""),
            question.get("explanation_fa", ""),
            question.get("explanation_en", ""),
        )).casefold()
        if any(marker.casefold() in explanation for marker in GENERIC_EXPLANATION_MARKERS):
            warnings.append(f"Q{index}: rationale is generic and needs subject-matter editing")
        if normalized(question.get("prompt_fa")) != normalized(question.get("prompt_en")):
            if len(explanation.strip()) < 120:
                warnings.append(f"Q{index}: bilingual technical rationale is too short to be instructional")
            correct = normalized((question.get("choices") or ("",))[0])
            if correct and correct not in normalized(explanation):
                warnings.append(f"Q{index}: technical rationale does not identify the keyed answer")
        for language in ("fa", "en"):
            key = f"choice_explanations_{language}"
            values = question.get(key, ())
            if values and len(values) != len(choices):
                issues.append(f"Q{index}: {key} does not match choice count")

    for left_position, (left_index, left) in enumerate(prompts):
        for right_index, right in prompts[left_position + 1:]:
            if len(left) >= 24 and SequenceMatcher(None, left, right).ratio() >= .94:
                warnings.append(f"Q{left_index}/Q{right_index}: prompts are near duplicates")

    for code in section_codes:
        levels = {level for (section, level), count in distributions.items() if section == code and count}
        if len(levels) < 2:
            warnings.append(f"Section {code}: difficulty coverage is too narrow")

    return {
        "question_count": len(questions),
        "issues": issues,
        "warnings": warnings,
        "difficulty_distribution": dict(Counter(q.get("difficulty") for q in questions)),
        "section_distribution": dict(Counter(q.get("section") for q in questions)),
        "subskill_count": len(subskills),
    }
