from dataclasses import dataclass


MAX_ABSENCE_MS = 900_000


@dataclass(frozen=True)
class IntegrityAssessment:
    points: int
    severity: str
    reason_fa: str
    reason_en: str


def assess_event(
    event_type,
    duration_ms=0,
    *,
    pairing_status="server_paired",
    connection_state="unknown",
):
    """Return an explainable risk weight; signals are evidence, not proof."""
    if event_type == "visibility_returned":
        duration_ms = max(0, min(int(duration_ms or 0), MAX_ABSENCE_MS))
        if pairing_status == "client_only":
            connection_note_fa = (
                " و دستگاه هنگام ثبت آفلاین بوده است"
                if connection_state == "offline" else ""
            )
            connection_note_en = (
                " and the device reported being offline"
                if connection_state == "offline" else ""
            )
            return IntegrityAssessment(
                0,
                "info",
                "بازگشت دستگاه ثبت شد، اما خروج متناظر به سرور نرسید"
                f"{connection_note_fa}؛ این فاصله فنی امتیاز سلامت را کم نمی‌کند",
                "The device reported a return, but the matching exit did not reach the server"
                f"{connection_note_en}; this telemetry gap does not reduce integrity",
            )
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


def integrity_evidence_summary(attempt, lang="fa"):
    """Aggregate review evidence without presenting any signal as proven cheating."""
    events = list(attempt.integrity_events.all())
    returned = [event for event in events if event.event_type == "visibility_returned"]
    hidden = [event for event in events if event.event_type == "visibility_hidden"]
    returned_tokens = {
        (event.metadata or {}).get("transition_id")
        for event in returned
        if (event.metadata or {}).get("transition_id")
    }
    open_absences = [
        event for event in hidden
        if (event.metadata or {}).get("transition_id")
        and (event.metadata or {}).get("transition_id") not in returned_tokens
    ]
    # Old records did not carry transition identifiers. Preserve the earlier
    # latest-event interpretation only for those historical rows.
    tokenless_events = [
        event for event in events
        if event.event_type in {"visibility_hidden", "visibility_returned"}
        and not (event.metadata or {}).get("transition_id")
    ]
    if tokenless_events and tokenless_events[-1].event_type == "visibility_hidden":
        open_absences.append(tokenless_events[-1])

    technical_gaps = sum(
        1
        for event in events
        if event.event_type in {"tab_hidden", "window_blur"}
        or (event.metadata or {}).get("pairing_status") == "client_only"
    ) + len(open_absences)
    def event_assessment(event):
        metadata = event.metadata or {}
        return assess_event(
            event.event_type,
            event.duration_ms,
            pairing_status=metadata.get("pairing_status", "server_paired"),
            connection_state=metadata.get("connection_state", "unknown"),
        )

    event_risk_points = sum(
        max(
            0,
            int(
                (event.metadata or {}).get(
                    "risk_points", event_assessment(event).points,
                ) or 0
            ),
        )
        for event in events
    )
    pace_rows = question_pace_rows(attempt, lang)
    fast_rows = [row for row in pace_rows if row["risk_points"]]
    high_events = sum(
        1
        for event in events
        if (event.metadata or {}).get("severity", event_assessment(event).severity) == "high"
    ) + sum(1 for row in fast_rows if row["severity"] == "high")
    missing_timing = sum(
        1 for row in pace_rows if row["verdict"] == "no_timing"
    )
    historical_without_timing = sum(
        1
        for item in attempt.attempt_questions.all()
        if not item.first_seen_at and not item.active_seconds
    )
    if historical_without_timing or missing_timing or technical_gaps:
        quality = "partial"
    elif pace_rows:
        quality = "complete"
    else:
        quality = "unavailable"

    if high_events or attempt.integrity_score < 75:
        band = "review"
    elif event_risk_points or fast_rows:
        band = "attention"
    else:
        band = "clear"

    labels = {
        "fa": {
            "review": "نیازمند بررسی انسانی",
            "attention": "دارای شواهد قابل بررسی",
            "clear": "بدون هشدار برجسته",
            "complete": "داده‌های پایش کامل",
            "partial": "داده‌های پایش ناقص یا قدیمی",
            "unavailable": "داده پایش در دسترس نیست",
        },
        "en": {
            "review": "Human review required",
            "attention": "Reviewable evidence present",
            "clear": "No prominent warning",
            "complete": "Monitoring data complete",
            "partial": "Monitoring data partial or legacy",
            "unavailable": "Monitoring data unavailable",
        },
    }["fa" if lang == "fa" else "en"]
    return {
        "band": band,
        "band_label": labels[band],
        "quality": quality,
        "quality_label": labels[quality],
        "absence_count": len(returned),
        "total_away_ms": sum(max(0, int(event.duration_ms or 0)) for event in returned),
        "copy_count": sum(event.event_type == "copy" for event in events),
        "paste_count": sum(event.event_type == "paste" for event in events),
        "technical_gap_count": technical_gaps,
        "open_absence_count": len(open_absences),
        "event_risk_points": event_risk_points,
        "pace_risk_points": min(sum(row["risk_points"] for row in pace_rows), 25),
        "fast_question_count": len(fast_rows),
        "missing_timing_count": missing_timing,
        "high_evidence_count": high_events,
    }


def pace_risk_points(attempt):
    """Total pace-derived risk, capped so timing alone cannot void an attempt."""
    total = sum(row["risk_points"] for row in question_pace_rows(attempt))
    return min(total, 25)


def format_duration(duration_ms, lang="fa"):
    seconds = max(0, int(round((duration_ms or 0) / 1000)))
    if lang == "fa":
        return f"{seconds} ثانیه"
    return f"{seconds} sec"
