import hashlib
import json

from django.db import transaction
from django.utils import timezone

from .models import ContractClause, ContractVersion


DEFAULT_CLAUSES = (
    ("موضوع و دامنه کار", "مجری خدمات تحلیل، طراحی، توسعه، آزمون و استقرار را فقط در محدوده شرح پروژه و خروجی‌های مکتوب این پیشنهاد انجام می‌دهد."),
    ("تعهدات و همکاری سفارش‌دهنده", "سفارش‌دهنده اطلاعات، محتوا، دسترسی‌ها و تأییدهای لازم را در زمان توافق‌شده ارائه می‌کند. تأخیر در این موارد می‌تواند برنامه تحویل را تغییر دهد."),
    ("مبلغ و روش پرداخت", "شروع کار پس از تأیید قرارداد و ثبت مرحله نخست پرداخت است. مبالغ و مراحل پرداخت مطابق مشخصات مالی همین پیشنهاد خواهد بود."),
    ("زمان‌بندی و تحویل", "زمان‌بندی از زمان دریافت پیش‌پرداخت و همه پیش‌نیازهای اعلام‌شده محاسبه می‌شود. تحویل هر مرحله بر اساس معیارهای مکتوب بررسی خواهد شد."),
    ("تغییر دامنه", "درخواست خارج از دامنه پس از بررسی اثر آن بر مبلغ و زمان و با تأیید مکتوب طرفین اجرا می‌شود."),
    ("مالکیت فکری", "پس از تسویه کامل، حقوق استفاده از خروجی اختصاصی پروژه مطابق قرارداد به سفارش‌دهنده منتقل می‌شود. ابزارها و اجزای عمومی یا شخص ثالث تابع مجوز خود هستند."),
    ("محرمانگی و داده", "طرفین اطلاعات محرمانه دریافت‌شده را فقط برای اجرای پروژه استفاده می‌کنند و الزامات دسترسی و نگهداری داده را رعایت خواهند کرد."),
    ("خدمات شخص ثالث", "دامنه، میزبانی، پیامک، درگاه، سرویس ایمیل و سایر خدمات شخص ثالث تابع هزینه و شرایط ارائه‌دهنده خود هستند مگر صراحتاً خلاف آن نوشته شود."),
    ("پشتیبانی و رفع ایراد", "ایرادهای قابل بازتولید در کد تحویلی تا سه ماه پس از تحویل نهایی بدون هزینه رفع می‌شوند. قابلیت جدید و تغییر دامنه جزو رفع ایراد نیست."),
    ("توقف یا خاتمه", "در صورت توقف همکاری، کار انجام‌شده و هزینه‌های قطعی تا تاریخ توقف محاسبه و خروجی قابل تحویل پس از تسویه ارائه می‌شود."),
    ("قوه قهریه", "رویدادهای خارج از کنترل متعارف طرفین که اجرای تعهد را ناممکن کند، موجب بازنگری زمان‌بندی و راه‌حل منصفانه خواهد شد."),
    ("حل اختلاف و مکاتبات", "طرفین ابتدا اختلاف را از طریق مذاکره و مکاتبات ثبت‌شده حل می‌کنند؛ مرجع و قانون حاکم باید در نسخه حقوقی نهایی توسط مشاور حقوقی تأیید شود."),
)


def add_default_clauses(proposal):
    ContractClause.objects.bulk_create([
        ContractClause(proposal=proposal, title=title, body=body, position=index)
        for index, (title, body) in enumerate(DEFAULT_CLAUSES, 1)
    ])


def proposal_snapshot(proposal):
    return {
        "title": proposal.title, "customer_name": proposal.customer_name,
        "customer_phone": proposal.customer_phone, "customer_email": proposal.customer_email,
        "project_title": proposal.project_title, "project_scope": proposal.project_scope,
        "amount_irr": proposal.amount_irr, "payment_terms": proposal.payment_terms,
        "delivery_terms": proposal.delivery_terms, "client_details": proposal.client_details,
        "clauses": [{"id": clause.id, "title": clause.title, "body": clause.body} for clause in proposal.clauses.filter(is_enabled=True)],
    }


@transaction.atomic
def publish_version(proposal, actor):
    snapshot = proposal_snapshot(proposal)
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    number = proposal.current_version + 1
    version = ContractVersion.objects.create(
        proposal=proposal, number=number, snapshot=snapshot,
        snapshot_hash=hashlib.sha256(canonical.encode()).hexdigest(), created_by=actor,
    )
    proposal.current_version = number
    proposal.status = "sent"
    if not proposal.expires_at:
        proposal.expires_at = timezone.now() + timezone.timedelta(days=14)
    proposal.save(update_fields=["current_version", "status", "expires_at", "updated_at"])
    return version
