from dataclasses import dataclass


MAX_ABSENCE_MS = 900_000


@dataclass(frozen=True)
class IntegrityAssessment:
    points: int
    severity: str
    reason_fa: str
    reason_en: str


def assess_event(event_type, duration_ms=0):
    """Return an explainable risk weight; signals are evidence, not proof."""
    if event_type == "visibility_returned":
        duration_ms = max(0, min(int(duration_ms or 0), MAX_ABSENCE_MS))
        if duration_ms < 3_000:
            return IntegrityAssessment(0, "info", "بازگشت در کمتر از ۳ ثانیه", "Returned in under 3 seconds")
        if duration_ms < 15_000:
            return IntegrityAssessment(1, "low", "خروج ۳ تا ۱۵ ثانیه‌ای از آزمون", "Away for 3 to 15 seconds")
        if duration_ms < 60_000:
            return IntegrityAssessment(3, "medium", "خروج ۱۵ تا ۶۰ ثانیه‌ای از آزمون", "Away for 15 to 60 seconds")
        return IntegrityAssessment(6, "high", "خروج بیش از یک دقیقه از آزمون", "Away for more than one minute")
    if event_type == "visibility_hidden":
        return IntegrityAssessment(0, "info", "خروج از صفحه ثبت شد؛ در انتظار بازگشت", "Page exit recorded; awaiting return")
    if event_type in {"tab_hidden", "window_blur"}:
        return IntegrityAssessment(0, "info", "رویداد قدیمی و غیرقابل اتکا؛ در تصمیم‌گیری استفاده نشود", "Legacy unreliable event; exclude from decisions")
    if event_type == "copy":
        return IntegrityAssessment(2, "medium", "فرمان کپی روی سؤال اجرا شد", "Copy command used on the question")
    if event_type == "paste":
        return IntegrityAssessment(3, "high", "فرمان جای‌گذاری روی سؤال اجرا شد", "Paste command used on the question")
    return IntegrityAssessment(0, "info", "رویداد اطلاعاتی", "Informational event")


DIFFICULTY_LABELS_FA = {1: "پایه", 2: "آسان", 3: "متوسط", 4: "پیشرفته", 5: "بسیار دشوار"}
DIFFICULTY_LABELS_EN = {1: "Foundation", 2: "Easy", 3: "Intermediate", 4: "Advanced", 5: "Expert"}

# A correct answer produced far faster than the authored time is the strongest
# single signal of a leaked or looked-up item, so it carries its own weight.
IMPLAUSIBLE_RATIO = 0.2
FAST_RATIO = 0.45
SLOW_RATIO = 2.5


@dataclass(frozen=True)
class PaceAssessment:
    verdict: str
    points: int
    severity: str
    reason_fa: str
    reason_en: str


def expected_seconds(suggested_seconds, difficulty):
    """Scale the authored time by difficulty so the expectation is explainable."""
    base = max(5, int(suggested_seconds or 60))
    factor = {1: 0.7, 2: 0.85, 3: 1.0, 4: 1.25, 5: 1.5}.get(int(difficulty or 3), 1.0)
    return int(round(base * factor))


def assess_pace(active_seconds, suggested_seconds, difficulty, *, answered=True, is_correct=True):
    """Compare real time-on-question against the expected time for its difficulty."""
    expected = expected_seconds(suggested_seconds, difficulty)
    seconds = max(0, int(active_seconds or 0))
    if not answered:
        return PaceAssessment("unanswered", 0, "info", "بدون پاسخ", "Unanswered")
    if seconds == 0:
        return PaceAssessment(
            "no_timing", 0, "info",
            "زمانی برای این سؤال ثبت نشده است", "No timing recorded for this question",
        )
    ratio = seconds / expected
    if not is_correct and ratio <= FAST_RATIO:
        return PaceAssessment(
            "fast_incorrect", 0, "info",
            f"پاسخ نادرست در {seconds} ثانیه ثبت شد؛ سرعت به‌تنهایی امتیاز سلامت را کم نمی‌کند",
            f"An incorrect answer was recorded in {seconds}s; pace alone does not reduce integrity",
        )
    if ratio <= IMPLAUSIBLE_RATIO:
        return PaceAssessment(
            "implausible", 4, "high",
            f"پاسخ در {seconds} ثانیه در برابر انتظار {expected} ثانیه؛ سرعت غیرمنتظره",
            f"Answered in {seconds}s against an expected {expected}s; implausibly fast",
        )
    if ratio <= FAST_RATIO:
        return PaceAssessment(
            "fast", 1, "low",
            f"پاسخ در {seconds} ثانیه در برابر انتظار {expected} ثانیه؛ سریع‌تر از حد معمول",
            f"Answered in {seconds}s against an expected {expected}s; faster than usual",
        )
    if ratio >= SLOW_RATIO:
        return PaceAssessment(
            "slow", 0, "info",
            f"پاسخ در {seconds} ثانیه در برابر انتظار {expected} ثانیه؛ کندتر از حد معمول",
            f"Answered in {seconds}s against an expected {expected}s; slower than usual",
        )
    return PaceAssessment(
        "normal", 0, "info",
        f"پاسخ در {seconds} ثانیه در برابر انتظار {expected} ثانیه",
        f"Answered in {seconds}s against an expected {expected}s",
    )


def question_pace_rows(attempt, lang="fa"):
    """Per-question timing record: taken, expected, difficulty, and verdict."""
    rows = []
    for item in attempt.attempt_questions.all().order_by("position"):
        snapshot = item.question_snapshot or {}
        difficulty = snapshot.get("difficulty", 3)
        suggested = snapshot.get("suggested_seconds", 60)
        answered = item.effective_selected_choice_id is not None
        selected_id = item.effective_selected_choice_id
        selected = next((choice for choice in item.choices_snapshot if choice.get("id") == selected_id), None)
        is_correct = bool(selected and selected.get("is_correct"))
        pace = assess_pace(
            item.active_seconds, suggested, difficulty,
            answered=answered, is_correct=is_correct,
        )
        labels = DIFFICULTY_LABELS_FA if lang == "fa" else DIFFICULTY_LABELS_EN
        rows.append({
            "position": item.position,
            "section": snapshot.get("section_title_fa" if lang == "fa" else "section_title_en", ""),
            "difficulty": difficulty,
            "difficulty_label": labels.get(int(difficulty or 3), ""),
            "expected_seconds": expected_seconds(suggested, difficulty),
            "active_seconds": item.active_seconds,
            "visit_count": item.visit_count,
            "answer_change_count": item.answer_change_count,
            "answered": answered,
            "is_correct": is_correct,
            "verdict": pace.verdict,
            "severity": pace.severity,
            "risk_points": pace.points,
            "reason": pace.reason_fa if lang == "fa" else pace.reason_en,
        })
    return rows


def pace_risk_points(attempt):
    """Total pace-derived risk, capped so timing alone cannot void an attempt."""
    total = sum(row["risk_points"] for row in question_pace_rows(attempt))
    return min(total, 25)


def format_duration(duration_ms, lang="fa"):
    seconds = max(0, int(round((duration_ms or 0) / 1000)))
    if lang == "fa":
        return f"{seconds} ثانیه"
    return f"{seconds} sec"
