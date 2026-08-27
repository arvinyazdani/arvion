from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class JourneyStage:
    key: str
    label_fa: str
    label_en: str
    state: str
    state_fa: str
    state_en: str


@dataclass(frozen=True)
class JourneyAction:
    key: str
    label_fa: str
    label_en: str
    detail_fa: str
    detail_en: str
    url: str
    kind: str = "link"
    urgent: bool = False


@dataclass(frozen=True)
class CustomerJourney:
    key: str
    label_fa: str
    label_en: str
    detail_fa: str
    detail_en: str
    tone: str
    stages: tuple
    actions: tuple


def _stage(key, labels, state, states):
    return JourneyStage(key, labels[0], labels[1], state, states[0], states[1])


def resolve_customer_journey(*, customer, orders, attempts, contracts, can_message, can_change_case):
    """Derive operational state from domain records without persisting a second truth."""

    contacts = list(customer.contacts.all())
    accounts = [contact.user for contact in contacts if contact.user_id]
    has_account = bool(accounts)
    account_active = any(account.is_active for account in accounts)
    has_order = bool(orders)
    pending_orders = [order for order in orders if order.status == "pending"]
    pending_payments = [
        order for order in pending_orders
        if getattr(order, "manual_payment", None) is not None and order.manual_payment.status == "pending"
    ]
    paid_orders = [order for order in orders if order.status == "paid"]
    has_paid = bool(paid_orders)
    active_attempts = [attempt for attempt in attempts if attempt.status in {"ready", "in_progress", "submitted", "scoring"}]
    completed_attempts = [attempt for attempt in attempts if attempt.status == "completed"]
    has_attempt = bool(attempts)
    has_completed = bool(completed_attempts)
    accepted_contracts = [contract for contract in contracts if contract.status == "accepted"]
    active_contracts = [contract for contract in contracts if contract.status in {"sent", "review"}]

    stages = (
        _stage("account", ("حساب", "Account"), "done" if account_active else "attention" if has_account else "waiting", ("فعال" if account_active else "منتظر تأیید" if has_account else "ساخته نشده", "Active" if account_active else "Awaiting approval" if has_account else "Not created")),
        _stage("order", ("سفارش", "Order"), "done" if has_order else "waiting", ("ثبت شده" if has_order else "ثبت نشده", "Created" if has_order else "Not created")),
        _stage("payment", ("پرداخت", "Payment"), "done" if has_paid else "attention" if pending_payments else "active" if pending_orders else "waiting", ("تأیید شده" if has_paid else "منتظر بررسی" if pending_payments else "پرداخت نشده" if pending_orders else "ثبت نشده", "Approved" if has_paid else "Awaiting review" if pending_payments else "Unpaid" if pending_orders else "Not submitted")),
        _stage("assessment", ("آزمون", "Assessment"), "done" if has_completed else "active" if active_attempts else "waiting", ("نتیجه آماده" if has_completed else "در حال انجام" if active_attempts else "شروع نشده", "Result ready" if has_completed else "In progress" if active_attempts else "Not started")),
        _stage("contract", ("قرارداد", "Contract"), "done" if accepted_contracts else "active" if active_contracts else "waiting", ("پذیرفته شده" if accepted_contracts else "در انتظار مشتری" if active_contracts else "فعال نیست", "Accepted" if accepted_contracts else "Awaiting customer" if active_contracts else "Not active")),
    )

    actions = []
    if can_message and (customer.phone or any(contact.phone for contact in contacts)):
        actions.append(JourneyAction("message", "ارسال پیام", "Send message", "پیگیری مستقیم و ثبت نتیجه ارسال", "Send a direct follow-up and record delivery", "#customer-message", "anchor"))
    if can_change_case:
        actions.extend((
            JourneyAction("task", "ساخت پیگیری", "Create follow-up", "وظیفه مسئول‌دار با مهلت مشخص", "Create an assigned task with a due date", "#customer-actions", "form"),
            JourneyAction("activity", "ثبت تماس یا یادداشت", "Log activity", "تماس، جلسه یا تصمیم را در Timeline نگه دارید", "Keep a call, meeting or decision in the timeline", "#customer-actions", "form"),
        ))
    if pending_payments:
        actions.insert(0, JourneyAction("payment", "بررسی پرداخت", "Review payment", "رسید یا وضعیت سفارش منتظر تصمیم مدیر است", "A receipt or order is waiting for a decision", reverse("management_portal:approvals"), urgent=True))
    if has_completed:
        attempt = completed_attempts[0]
        actions.insert(0, JourneyAction("result", "مشاهده نتیجه", "Review result", "گزارش کامل و رفتار سؤال‌به‌سؤال را بررسی کنید", "Review the full result and question-level activity", reverse("management_portal:customer_assessment_detail", args=[customer.pk, attempt.user_id])))
    elif has_attempt:
        attempt = attempts[0]
        actions.insert(0, JourneyAction("assessment", "بررسی آزمون", "Review assessment", "وضعیت فعلی تلاش و رویدادها را ببینید", "Review attempt status and events", reverse("management_portal:customer_assessment_detail", args=[customer.pk, attempt.user_id])))
    if contracts:
        contract = contracts[0]
        actions.append(JourneyAction("contract", "باز کردن قرارداد", "Open contract", "نسخه و وضعیت پذیرش قرارداد را بررسی کنید", "Review contract version and acceptance", reverse("management_portal:contract_detail", args=[contract.pk])))
    else:
        actions.append(JourneyAction("contract", "ساخت قرارداد", "Create contract", "از اطلاعات پرونده یک پیشنهاد قرارداد بسازید", "Create a proposal from this customer record", reverse("management_portal:contract_create") + f"?customer={customer.pk}"))

    if not has_account:
        key, labels, details, tone = "identity_missing", ("حساب مشتری متصل نیست", "Customer account is not linked"), ("ابتدا حساب سایت را به مخاطب اصلی متصل کنید.", "Link a site account to the primary contact first."), "warning"
    elif not account_active:
        key, labels, details, tone = "account_pending", ("حساب منتظر تأیید است", "Account awaits approval"), ("فعال‌سازی حساب باید پیش از استفاده از خدمات بررسی شود.", "Review account activation before service access."), "urgent"
    elif not has_order:
        key, labels, details, tone = "registered", ("عضو شده؛ هنوز سفارشی ندارد", "Registered; no order yet"), ("پیگیری و دعوت به ثبت سفارش، اقدام بعدی این مشتری است.", "Follow up and invite the customer to place an order."), "neutral"
    elif pending_payments and not has_paid:
        key, labels, details, tone = "payment_pending", ("پرداخت منتظر بررسی است", "Payment awaits review"), ("رسید و اطلاعات پرداخت را بررسی و تصمیم را ثبت کنید.", "Review the receipt and record a payment decision."), "urgent"
    elif pending_orders and not has_paid:
        key, labels, details, tone = "unpaid", ("سفارش ثبت شده؛ پرداخت انجام نشده", "Order created; payment incomplete"), ("مشتری را برای تکمیل پرداخت راهنمایی و پیگیری کنید.", "Guide and follow up with the customer to complete payment."), "warning"
    elif has_paid and not has_attempt:
        key, labels, details, tone = "ready", ("دسترسی فعال؛ آزمون شروع نشده", "Access active; assessment not started"), ("مشتری آماده شروع است و در صورت تأخیر به یادآوری نیاز دارد.", "The customer can start and may need a reminder."), "active"
    elif active_attempts and not has_completed:
        key, labels, details, tone = "in_progress", ("آزمون در جریان است", "Assessment in progress"), ("فرایند را مختل نکنید؛ فقط وضعیت و خطاهای احتمالی را پایش کنید.", "Avoid interruption; monitor status and possible errors."), "active"
    elif has_completed:
        key, labels, details, tone = "completed", ("نتیجه آماده پیگیری است", "Result ready for follow-up"), ("گزارش را بررسی کنید و اقدام بعدی مشتری را مشخص کنید.", "Review the report and choose the customer's next step."), "success"
    else:
        key, labels, details, tone = "needs_review", ("پرونده نیازمند بررسی است", "Record needs review"), ("داده‌های پرونده را بررسی و یک پیگیری ثبت کنید.", "Review the record and create a follow-up."), "warning"

    return CustomerJourney(key, labels[0], labels[1], details[0], details[1], tone, stages, tuple(actions))
