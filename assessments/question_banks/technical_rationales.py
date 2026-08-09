"""Contextual rationale builder for definition and scenario-based technical MCQs."""


SECTION_FA = {
    "python-core": "قواعد زبان و مدل داده پایتون",
    "problem-solving": "تحلیل الگوریتم و طراحی راه‌حل",
    "testing-quality": "اصول تست و کیفیت نرم‌افزار",
    "django": "رفتار و معماری Django",
    "database": "قواعد پایگاه داده و ORM",
    "security": "مدل تهدید و کنترل امنیتی",
    "deployment": "اصول استقرار و عملیات",
}

SECTION_EN = {
    "python-core": "Python language and data-model semantics",
    "problem-solving": "algorithm analysis and solution design",
    "testing-quality": "software testing and quality principles",
    "django": "Django behavior and architecture",
    "database": "database and ORM rules",
    "security": "the threat model and security control",
    "deployment": "deployment and operations principles",
}


def technical_rationale(section, subskill, prompt_fa, prompt_en, correct):
    topic_fa = SECTION_FA[section]
    topic_en = SECTION_EN[section]
    label = subskill.replace("-", " ")
    lowered = prompt_en.casefold()
    if any(token in lowered for token in ("result", "output", "return")):
        fa = f"با اجرای عبارت طبق {topic_fa}، نتیجه «{correct}» است؛ گزینه‌های دیگر با ارزیابی تعریف‌شده برای {label} به دست نمی‌آیند."
        en = f"Evaluating the expression under {topic_en} produces ‘{correct}’; the alternatives do not follow the defined {label} evaluation."
    elif lowered.startswith("why") or " why " in lowered:
        fa = f"«{correct}» علت فنی مرتبط با {label} را بیان می‌کند و پیامد مطرح‌شده در سؤال را توضیح می‌دهد؛ سایر گزینه‌ها رابطه علّی درستی ندارند."
        en = f"‘{correct}’ states the {label} reason that explains the consequence in the question; the alternatives do not provide the relevant causal link."
    elif lowered.startswith("how"):
        fa = f"برای این سناریو، سازوکار درست در {topic_fa} «{correct}» است؛ این روش الزام {label} را مستقیماً تأمین می‌کند."
        en = f"For this scenario, the appropriate {topic_en} mechanism is ‘{correct}’; it directly satisfies the stated {label} requirement."
    else:
        fa = f"در مبحث {label}، قاعده یا تعریف مرتبط «{correct}» است؛ این گزینه دقیقاً با {topic_fa} مورد سؤال تطبیق دارد."
        en = f"For {label}, the relevant rule or definition is ‘{correct}’; it directly matches the {topic_en} concept being tested."
    return fa, en
