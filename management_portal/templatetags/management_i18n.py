"""Presentation-only translations for persisted management events.

Notification and audit rows are evidence: their stored payload must remain
immutable.  These filters translate the finite system-generated vocabulary at
render time while leaving names, reference numbers, and user-authored text
untouched.
"""

import re

from django import template


register = template.Library()


NOTIFICATION_TITLES_EN = {
    "عضویت کاربر جدید": "New customer account",
    "درخواست همکاری جدید": "New project enquiry",
    "نیازسنجی CRM جدید": "New CRM discovery",
    "نیازسنجی تخصصی CRM تکمیل شد": "Specialist CRM discovery completed",
    "نیازسنجی کلینیک جدید": "New clinic discovery",
    "رسید پرداخت جدید": "New payment receipt",
    "رسید پرداخت اصلاح‌شده": "Updated payment receipt",
    "تیکت پشتیبانی جدید": "New support ticket",
    "بازخورد قرارداد ثبت شد": "Contract feedback received",
    "قرارداد تأیید شد": "Contract accepted",
    "تأیید پرداخت از مهلت عبور کرده است": "Payment review is overdue",
    "تیکت بدون پاسخ مانده است": "Support ticket is overdue",
    "پیگیری قرارداد از مهلت عبور کرده است": "Contract follow-up is overdue",
    "فرم جدید نیازمند پیگیری است": "New discovery needs follow-up",
    "وظیفه CRM عقب افتاده": "CRM task is overdue",
    "موعد پیگیری مشتری": "Customer follow-up is due",
}

AUDIT_ACTIONS_EN = {
    "customer_merged": "Customer records merged",
    "customer_contact_created": "Customer contact added",
    "customer_followup_created": "Customer follow-up created",
    "customer_activity_logged": "Customer activity logged",
    "sms_campaign_sent": "SMS campaign sent",
    "crm_case_updated": "CRM case updated",
    "crm_case_exported": "CRM case exported",
    "request_exported": "Discovery exported",
    "account_approve": "Account approved",
    "account_reject": "Account rejected",
    "payment_approve": "Payment approved",
    "payment_reject": "Payment rejected",
    "ticket_status": "Ticket status changed",
    "content_state": "Content visibility changed",
    "notification_claimed": "Notification ownership claimed",
}

AUDIT_ACTIONS_FA = {
    "customer_merged": "ادغام سوابق مشتری",
    "customer_contact_created": "افزودن مخاطب مشتری",
    "customer_followup_created": "ساخت پیگیری مشتری",
    "customer_activity_logged": "ثبت فعالیت مشتری",
    "sms_campaign_sent": "ارسال کمپین پیامکی",
    "crm_case_updated": "به‌روزرسانی پرونده CRM",
    "crm_case_exported": "خروجی پرونده CRM",
    "request_exported": "خروجی نیازسنجی",
    "account_approve": "تأیید حساب",
    "account_reject": "رد حساب",
    "payment_approve": "تأیید پرداخت",
    "payment_reject": "رد پرداخت",
    "ticket_status": "تغییر وضعیت تیکت",
    "content_state": "تغییر نمایش محتوا",
    "notification_claimed": "پذیرش مسئولیت اعلان",
}

TARGET_TYPES_EN = {
    "customer": "Customer",
    "customer_case": "Customer case",
    "user": "Account",
    "manual_payment": "Payment receipt",
    "support_ticket": "Support ticket",
    "management_notification": "Notification",
    "lead": "Project enquiry",
    "crm": "CRM discovery",
    "clinic": "Clinic discovery",
    "post": "Article",
    "project": "Project",
    "service": "Service",
    "exam": "Assessment",
    "sms_campaign": "SMS campaign",
}

TARGET_TYPES_FA = {
    "customer": "مشتری",
    "customer_case": "پرونده مشتری",
    "user": "حساب کاربری",
    "manual_payment": "رسید پرداخت",
    "support_ticket": "تیکت پشتیبانی",
    "management_notification": "اعلان",
    "lead": "درخواست همکاری",
    "crm": "نیازسنجی CRM",
    "clinic": "نیازسنجی کلینیک",
    "post": "مقاله",
    "project": "پروژه",
    "service": "خدمت",
    "exam": "آزمون",
    "sms_campaign": "کمپین پیامکی",
}

STATUS_EN = {
    "pending": "pending",
    "approved": "approved",
    "rejected": "rejected",
    "open": "open",
    "closed": "closed",
    "resolved": "resolved",
    "true": "visible",
    "false": "hidden",
}

STATUS_FA = {
    "pending": "در انتظار بررسی",
    "approved": "تأییدشده",
    "rejected": "ردشده",
    "open": "باز",
    "closed": "بسته",
    "resolved": "مختومه",
    "true": "نمایش داده می‌شود",
    "false": "پنهان است",
}

CASE_TEXT_EN = {
    "پرونده عملیاتی ایجادشده از رویداد خدمات مشتری": "Operational case created from a customer service event",
    "پرونده مشتری ساخته شد": "Customer case created",
    "پرونده مشتری از اطلاعات موجود ساخته شد": "Customer case created from existing data",
    "سند به پرونده افزوده شد": "Document added to the case",
    "سند موجود به پرونده متصل شد": "Existing document linked to the case",
    "قرارداد موجود به پرونده متصل شد": "Existing contract linked to the case",
    "سند جدید": "New document",
    "پرونده مشتری ادغام شد": "Customer records merged",
    "پرونده بروزرسانی شد": "Customer case updated",
    "وظیفه ساخته شد": "Task created",
    "وضعیت وظیفه تغییر کرد": "Task status changed",
    "درخواست همکاری اولیه": "Initial project enquiry",
    "فرم نیازسنجی اولیه CRM": "Initial CRM discovery",
    "فرم نیازسنجی تخصصی CRM": "Specialist CRM discovery",
    "فرم نیازسنجی اولیه کلینیک": "Initial clinic discovery",
    "رسید پرداخت ارسال شد": "Payment receipt submitted",
    "رسید پرداخت اصلاح و دوباره ارسال شد": "Payment receipt updated and resubmitted",
    "تیکت پشتیبانی جدید": "New support ticket",
    "بازخورد قرارداد ثبت شد": "Contract feedback received",
    "قرارداد تأیید شد": "Contract accepted",
}


def _is_english(lang):
    return str(lang or "").lower().startswith("en")


@register.filter
def management_notification_title(value, lang="fa"):
    if not _is_english(lang):
        return value
    return NOTIFICATION_TITLES_EN.get(str(value), value)


@register.filter
def management_notification_description(value, lang="fa"):
    if not _is_english(lang) or not value:
        return value
    text = str(value)
    if text.startswith("شماره پیگیری:"):
        return "Reference:" + text.removeprefix("شماره پیگیری:")
    return text


@register.filter
def management_audit_action(value, lang="fa"):
    text = str(value)
    if _is_english(lang):
        return AUDIT_ACTIONS_EN.get(text, text.replace("_", " ").title())
    return AUDIT_ACTIONS_FA.get(text, text)


@register.filter
def management_target_type(value, lang="fa"):
    text = str(value)
    if _is_english(lang):
        return TARGET_TYPES_EN.get(text, text.replace("_", " ").title())
    return TARGET_TYPES_FA.get(text, text)


@register.filter
def management_audit_summary(value, lang="fa"):
    if not value:
        return value
    text = str(value)

    if not _is_english(lang):
        generated = re.fullmatch(r"(رسید .+|تیکت #.+): ([A-Za-z_]+)", text)
        if generated:
            return f"{generated.group(1)}: {STATUS_FA.get(generated.group(2).lower(), generated.group(2))}"
        content = re.fullmatch(r"([A-Za-z_]+) #(.+): (True|False)", text)
        if content:
            target = TARGET_TYPES_FA.get(content.group(1), content.group(1))
            return f"{target} #{content.group(2)}: {STATUS_FA[content.group(3).lower()]}"
        return text

    account = re.fullmatch(r"حساب (.+) (فعال شد|رد شد)", text)
    if account:
        outcome = "was activated" if account.group(2) == "فعال شد" else "was rejected"
        return f"Account {account.group(1)} {outcome}"

    payment = re.fullmatch(r"رسید (.+): ([A-Za-z_]+)", text)
    if payment:
        return f"Receipt {payment.group(1)}: {STATUS_EN.get(payment.group(2), payment.group(2))}"

    ticket = re.fullmatch(r"تیکت #(.+): ([A-Za-z_]+)", text)
    if ticket:
        return f"Ticket #{ticket.group(1)}: {STATUS_EN.get(ticket.group(2), ticket.group(2))}"

    return NOTIFICATION_TITLES_EN.get(text, text)


@register.filter
def management_case_text(value, lang="fa"):
    """Translate only known system-authored case copy, never customer prose."""
    if not _is_english(lang) or not value:
        return value
    text = str(value)
    if text in CASE_TEXT_EN:
        return CASE_TEXT_EN[text]
    if text.startswith("پیش‌نویس قرارداد:"):
        return "Contract draft:" + text.removeprefix("پیش‌نویس قرارداد:")
    if text.startswith("شماره پیگیری:"):
        return "Reference:" + text.removeprefix("شماره پیگیری:")
    return text
