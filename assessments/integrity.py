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


def format_duration(duration_ms, lang="fa"):
    seconds = max(0, int(round((duration_ms or 0) / 1000)))
    if lang == "fa":
        return f"{seconds} ثانیه"
    return f"{seconds} sec"
