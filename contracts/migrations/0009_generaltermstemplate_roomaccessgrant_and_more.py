import hashlib
import json

import contracts.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


# Frozen copy of crm_orders.specialist.SECTIONS at the time this migration was
# authored.  Never import application code in a data migration: deployments must
# remain reproducible even after the live questionnaire evolves.
LEGACY_CRM_SECTIONS = [
    ("users_access", "کاربران و دسترسی‌ها", "چه کسانی با سامانه کار می‌کنند و هر نقش چه چیزی می‌بیند؟", [
        ("roles", "نقش‌ها و تعداد کاربران هر نقش را بنویسید.", "مثال: مدیرعامل ۱ نفر، مدیر فروش ۱ نفر، کارشناس فروش ۸ نفر."),
        ("permissions", "برای هر نقش چه دسترسی‌هایی لازم است؟", "مشخص کنید چه کسی می‌تواند ببیند، ویرایش کند، حذف کند یا خروجی بگیرد."),
        ("approval", "در غیاب مدیر، جانشین و مسیر تأیید چگونه باشد؟", "اگر مدیر اصلی در دسترس نبود، نفر یا نقش جایگزین را مشخص کنید."),
    ]),
    ("data_model", "مشتری، پزشک، مرکز و پروژه", "تعریف درست موجودیت‌ها پایه طراحی CRM است.", [
        ("entities", "جراح، مرکز درمانی، مشتری و پروژه چه ارتباطی با هم دارند؟", "مثلاً یک جراح می‌تواند هم‌زمان با چند مرکز مرتبط باشد؟"),
        ("customer_fields", "برای هر نوع مشتری چه اطلاعاتی ضروری است؟", "اشخاص، شرکت‌ها، نمایندگان و مراکز دولتی ممکن است اطلاعات متفاوتی داشته باشند."),
        ("duplicate", "مشتری تکراری را با چه شناسه‌ای تشخیص دهیم؟", "شماره تماس، کد ملی، شناسه ملی یا ترکیبی از چند مورد را مشخص کنید."),
    ]),
    ("sales", "فرآیند واقعی فروش", "فروش را از سرنخ تا نتیجه نهایی مرحله‌بندی می‌کنیم.", [
        ("pipeline", "مراحل قیف فروش شما از سرنخ تا فروش چیست؟", "نام هر مرحله و شرط ورود و خروج آن را بنویسید."),
        ("lost", "چه زمانی فرصت را راکد یا ازدست‌رفته بدانیم؟", "دلایل شکست فروش و فاصله استاندارد پیگیری را مشخص کنید."),
        ("alerts", "سیستم چه زمانی و به چه کسی هشدار پیگیری بدهد؟", "مثلاً دو روز بعد از آخرین تماس به مالک فرصت اعلان شود."),
    ]),
    ("visit_ai", "ویزیت، گزارش صوتی و هوش مصنوعی", "این بخش برای طراحی گزارش و تحلیل عملکرد کارشناسان است.", [
        ("visit_form", "گزارش ویزیت چه سؤال‌ها و خروجی‌هایی داشته باشد؟", "ویزیت جراح، مرکز و پروژه یک فرم است یا فرم جدا می‌خواهید؟"),
        ("audio", "فایل صوتی چگونه ضبط و بررسی شود؟", "حداکثر مدت، زبان‌ها، زمان نهایی‌شدن و افراد مجاز به شنیدن را مشخص کنید."),
        ("quality", "گزارش یا پرزنت خوب از نظر مدیر چه ویژگی‌هایی دارد؟", "کشف نیاز، معرفی محصول، پاسخ به اعتراض، رقیب و اقدام بعدی را توضیح دهید."),
        ("ai", "AI دقیقاً چه کمکی ارائه دهد؟", "خلاصه‌سازی، استخراج اقدام بعدی، جست‌وجو یا تحلیل عملکرد را انتخاب و توضیح دهید."),
    ]),
    ("management", "تحلیل مدیر و شاخص‌ها", "هدف، شاخص قابل اندازه‌گیری است؛ نه امتیاز مبهم.", [
        ("manager_view", "مدیرعامل و مدیر فروش چه چیزهایی را بیشتر ببینند؟", "پنج شاخص اصلی داشبورد را اولویت‌بندی کنید."),
        ("kpi", "فرمول شاخص‌های مهم چیست؟", "مثلاً فروش بر اساس فاکتور، دریافت وجه یا تحویل کالا محاسبه شود؟"),
        ("samples", "نمونه گزارش واقعی برای آموزش یا تحلیل دارید؟", "۱۰ تا ۲۰ نمونه ناشناس‌شده خوب، متوسط و ضعیف بسیار کمک می‌کند."),
    ]),
    ("operations", "کالا، پیش‌فاکتور و مأموریت", "فرآیندهای داخلی را به گردش‌کار قابل پیگیری تبدیل می‌کنیم.", [
        ("goods", "درخواست کالا شامل فروش، نمونه، امانت یا مصرف داخلی است؟", "سطح تأیید، رزرو موجودی و حالت نبود کالا را بنویسید."),
        ("quotation", "پیش‌فاکتور چگونه ساخته و تأیید شود؟", "قیمت، تخفیف، مالیات، ارز، حمل، نصب، اعتبار و نسخه‌بندی را مشخص کنید."),
        ("mission", "مأموریت شهرستان چه مسیر تأییدی دارد؟", "تأیید مدیر مستقیم، مدیرعامل، مالی و منابع انسانی را مشخص کنید."),
    ]),
    ("migration", "مهاجرت اطلاعات", "برآورد مهاجرت به نمونه واقعی فایل‌ها نیاز دارد.", [
        ("volume", "چه تعداد رکورد، فایل و پیش‌فاکتور باید منتقل شود؟", "حجم دقیق هر منبع و فایل‌های ضمیمه را بنویسید."),
        ("quality", "رکوردهای تکراری و ناقص چگونه تعیین تکلیف شوند؟", "چه کسی نتیجه پاک‌سازی را تأیید می‌کند؟"),
        ("ocr", "آیا فایل اسکن‌شده یا نیاز به OCR دارید؟", "نمونه فایل‌ها را در جلسه تحلیل ارائه کنید."),
    ]),
    ("security", "استقرار، امنیت و پشتیبان‌گیری", "این پاسخ‌ها مستقیماً روی معماری و هزینه اثر دارند.", [
        ("hosting", "سرور، دامنه و محیط آزمایشی در اختیار چه کسی است؟", "داخل یا خارج ایران، UAT جدا و افراد دارای دسترسی فنی را مشخص کنید."),
        ("security", "MFA، ثبت رویداد و سطح دسترسی چگونه باشد؟", "مدت نگهداری Audit و مجوز Export داده را بنویسید."),
        ("backup", "برنامه Backup و بازیابی مورد انتظار چیست؟", "تعداد نسخه، محل نسخه دوم، RPO و RTO را مشخص کنید."),
    ]),
    ("support", "آموزش و پشتیبانی", "این بخش معیار تحویل و خدمات بعد از انتشار را روشن می‌کند.", [
        ("training", "چند جلسه آموزش و برای چه گروه‌هایی لازم است؟", "آموزش مدیران و کاربران را جداگانه مشخص کنید."),
        ("support_hours", "ساعات و کانال پشتیبانی چیست؟", "زمان پاسخ خطاهای بحرانی و دوره رفع اشکال رایگان را بنویسید."),
        ("changes", "درخواست تغییر بعد از تحویل چگونه قیمت‌گذاری شود؟", "چه کسی از طرف مشتری مجاز به ثبت تغییر است؟"),
    ]),
]


def frozen_specialist_schema():
    return [
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
        for section_key, title, description, questions in LEGACY_CRM_SECTIONS
    ]


def stable_json_hash(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def completion_for(schema, answers):
    answers = answers if isinstance(answers, dict) else {}
    completed_sections = []
    answered_questions = 0
    total_questions = 0
    first_incomplete = ""
    for section in schema:
        section_answers = answers.get(section["key"])
        section_answers = section_answers if isinstance(section_answers, dict) else {}
        complete = True
        for question in section["questions"]:
            total_questions += 1
            value = section_answers.get(question["key"])
            has_value = bool(value.strip()) if isinstance(value, str) else bool(value)
            if has_value:
                answered_questions += 1
            elif question.get("required", True):
                complete = False
        if complete:
            completed_sections.append(section["key"])
        elif not first_incomplete:
            first_incomplete = section["key"]
    total_sections = len(schema)
    return {
        "completed_sections": completed_sections,
        "completed_section_count": len(completed_sections),
        "total_sections": total_sections,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "percent": round((len(completed_sections) / total_sections) * 100) if total_sections else 0,
        "is_complete": len(completed_sections) == total_sections,
        "next_section": first_incomplete,
    }


def seed_workspace_foundation(apps, schema_editor):
    ContractProposal = apps.get_model("contracts", "ContractProposal")
    GeneralTermsTemplate = apps.get_model("contracts", "GeneralTermsTemplate")
    GeneralTermsVersion = apps.get_model("contracts", "GeneralTermsVersion")
    SpecialistFormTemplate = apps.get_model("contracts", "SpecialistFormTemplate")
    SpecialistFormTemplateVersion = apps.get_model("contracts", "SpecialistFormTemplateVersion")
    SpecialistAssignment = apps.get_model("contracts", "SpecialistAssignment")
    CrmSpecialistDiscovery = apps.get_model("crm_orders", "CrmSpecialistDiscovery")
    CustomerCase = apps.get_model("management_portal", "CustomerCase")
    CaseDocument = apps.get_model("management_portal", "CaseDocument")
    ContentType = apps.get_model("contenttypes", "ContentType")

    general_template, _ = GeneralTermsTemplate.objects.get_or_create(
        slug="global-general-terms-fa",
        defaults={"name": "شرایط عمومی قرارداد آرویون", "language": "fa", "is_active": True},
    )

    # Preserve every distinct legacy text while choosing the newest non-empty one
    # as the shared current version.  Blank proposals safely reference a clearly
    # marked placeholder instead of silently inventing legal terms.
    version_by_body = {}
    version_number = 0
    latest_nonempty_body = ""
    proposals = list(ContractProposal.objects.order_by("created_at", "pk"))
    for proposal in proposals:
        body = (proposal.general_terms or "").strip()
        if not body:
            continue
        latest_nonempty_body = body
        if body in version_by_body:
            continue
        version_number += 1
        version_by_body[body] = GeneralTermsVersion.objects.create(
            template=general_template,
            number=version_number,
            title="شرایط عمومی قرارداد",
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            change_note="انتقال خودکار از نسخه قدیمی قرارداد",
        )

    if not latest_nonempty_body:
        latest_nonempty_body = (
            "این نسخه صرفاً جای‌نگهدار است و باید پیش از انتشار قرارداد "
            "توسط مدیر تکمیل و تأیید شود."
        )
        version_number += 1
        version_by_body[latest_nonempty_body] = GeneralTermsVersion.objects.create(
            template=general_template,
            number=version_number,
            title="پیش‌نویس شرایط عمومی قرارداد",
            body=latest_nonempty_body,
            content_hash=hashlib.sha256(latest_nonempty_body.encode("utf-8")).hexdigest(),
            change_note="نسخه اولیه امن؛ پیش از انتشار تکمیل شود",
        )

    current_general_version = version_by_body[latest_nonempty_body]
    general_template.current_version_id = current_general_version.pk
    general_template.save(update_fields=("current_version",))

    schema = frozen_specialist_schema()
    specialist_template, _ = SpecialistFormTemplate.objects.get_or_create(
        slug="crm-enterprise-noorbinan",
        defaults={
            "name": "نیازسنجی تخصصی CRM سازمانی",
            "service_kind": "crm",
            "description": "نسخه پایه برگرفته از فرم تخصصی پروژه نور بینان راه ابزار",
            "is_active": True,
        },
    )
    specialist_version, _ = SpecialistFormTemplateVersion.objects.get_or_create(
        template=specialist_template,
        number=1,
        defaults={
            "schema": schema,
            "schema_hash": stable_json_hash(schema),
            "change_note": "انتقال بدون تغییر فرم تخصصی CRM موجود",
        },
    )
    if not specialist_template.current_version_id:
        specialist_template.current_version_id = specialist_version.pk
        specialist_template.save(update_fields=("current_version",))

    try:
        crm_content_type = ContentType.objects.get(app_label="crm_orders", model="crmorder")
    except ContentType.DoesNotExist:
        crm_content_type = None
    try:
        contract_content_type = ContentType.objects.get(app_label="contracts", model="contractproposal")
    except ContentType.DoesNotExist:
        contract_content_type = None

    for proposal in proposals:
        body = (proposal.general_terms or "").strip()
        proposal.general_terms_version_id = (
            version_by_body.get(body, current_general_version).pk
        )
        proposal.last_activity_at = proposal.updated_at or proposal.created_at

        case_id = None
        if proposal.crm_order_id and crm_content_type:
            cases = list(
                CustomerCase.objects.filter(
                    source_content_type_id=crm_content_type.pk,
                    source_object_id=proposal.crm_order_id,
                ).values_list("pk", "customer_id")[:2]
            )
            if len(cases) == 1:
                candidate_id, candidate_customer_id = cases[0]
                if not proposal.customer_id or not candidate_customer_id or candidate_customer_id == proposal.customer_id:
                    case_id = candidate_id

        # The contract document is an exact source link.  Requiring a single
        # matching case (and the same canonical customer when present) avoids
        # guessing from names, phone numbers, or recency.
        if not case_id and contract_content_type:
            linked_documents = CaseDocument.objects.filter(
                content_type_id=contract_content_type.pk,
                object_id=proposal.pk,
                kind="contract",
            )
            if proposal.customer_id:
                linked_documents = linked_documents.filter(case__customer_id=proposal.customer_id)
            linked_case_ids = list(linked_documents.values_list("case_id", flat=True).distinct()[:2])
            if len(linked_case_ids) == 1:
                case_id = linked_case_ids[0]

        proposal.customer_case_id = case_id
        proposal.save(update_fields=("general_terms_version", "last_activity_at", "customer_case"))

        if not proposal.crm_order_id:
            continue
        discovery = CrmSpecialistDiscovery.objects.filter(order_id=proposal.crm_order_id).first()
        if not discovery:
            continue
        status = discovery.status if discovery.status in {"draft", "submitted", "reviewed"} else "draft"
        answers = discovery.answers if isinstance(discovery.answers, dict) else {}
        assignment, created = SpecialistAssignment.objects.get_or_create(
            proposal=proposal,
            defaults={
                "version": specialist_version,
                "answers": answers,
                "progress": completion_for(schema, answers),
                "status": status,
                "revision": 1 if answers else 0,
                "started_at": discovery.created_at,
                "last_saved_at": discovery.updated_at,
                "submitted_at": discovery.updated_at if status in {"submitted", "reviewed"} else None,
                "reviewed_at": discovery.updated_at if status == "reviewed" else None,
            },
        )
        if created:
            SpecialistAssignment.objects.filter(pk=assignment.pk).update(
                created_at=discovery.created_at,
                updated_at=discovery.updated_at,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('management_portal', '0011_systemlog'),
        ('crm_orders', '0003_crmspecialistdiscovery'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contracts', '0008_contractacceptance_evidence'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralTermsTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('language', models.CharField(choices=[('fa', 'فارسی'), ('en', 'English')], db_index=True, default='fa', max_length=5)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'الگوی شرایط عمومی',
                'verbose_name_plural': 'الگوهای شرایط عمومی',
                'ordering': ('language', 'name', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='RoomAccessGrant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authorized_phone', models.CharField(db_index=True, max_length=12, validators=[django.core.validators.RegexValidator(message='شماره همراه باید به شکل استاندارد 989xxxxxxxxx ذخیره شود.', regex='^989\\d{9}$')])),
                ('password_hash', models.CharField(max_length=256)),
                ('credential_version', models.PositiveSmallIntegerField(default=1)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('expires_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('last_login_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_room_access_grants', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'دسترسی اتاق مشتری',
                'verbose_name_plural': 'دسترسی\u200cهای اتاق مشتری',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='SpecialistFormTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('service_kind', models.CharField(choices=[('crm', 'CRM'), ('clinic', 'کلینیک'), ('general', 'عمومی')], db_index=True, default='general', max_length=12)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'الگوی نیازسنجی تخصصی',
                'verbose_name_plural': 'الگوهای نیازسنجی تخصصی',
                'ordering': ('name', 'pk'),
            },
        ),
        migrations.AddField(
            model_name='contractproposal',
            name='customer_case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contract_proposals', to='management_portal.customercase'),
        ),
        migrations.AddField(
            model_name='contractproposal',
            name='last_activity_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.CreateModel(
            name='SpecialistFormTemplateVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField()),
                ('schema', models.JSONField(validators=[contracts.models.validate_specialist_schema])),
                ('schema_hash', models.CharField(editable=False, max_length=64)),
                ('change_note', models.CharField(blank=True, max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_specialist_form_versions', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='versions', to='contracts.specialistformtemplate')),
            ],
            options={
                'verbose_name': 'نسخه الگوی نیازسنجی تخصصی',
                'verbose_name_plural': 'نسخه\u200cهای الگوی نیازسنجی تخصصی',
                'ordering': ('-number', '-pk'),
            },
        ),
        migrations.AddField(
            model_name='specialistformtemplate',
            name='current_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='current_for_templates', to='contracts.specialistformtemplateversion'),
        ),
        migrations.CreateModel(
            name='SpecialistAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answers', models.JSONField(blank=True, default=dict, validators=[contracts.models.validate_json_object])),
                ('progress', models.JSONField(blank=True, default=dict, validators=[contracts.models.validate_json_object])),
                ('status', models.CharField(choices=[('draft', 'پیش\u200cنویس'), ('submitted', 'تکمیل\u200cشده'), ('reviewed', 'بررسی\u200cشده')], db_index=True, default='draft', max_length=12)),
                ('revision', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('last_saved_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proposal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='specialist_assignment', to='contracts.contractproposal')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='contracts.specialistformtemplateversion')),
            ],
            options={
                'verbose_name': 'فرم تخصصی اختصاص\u200cیافته',
                'verbose_name_plural': 'فرم\u200cهای تخصصی اختصاص\u200cیافته',
                'ordering': ('-updated_at', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='RoomEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('workspace_created', 'اتاق مشتری ساخته شد'), ('access_created', 'دسترسی ساخته شد'), ('access_rotated', 'دسترسی تغییر کرد'), ('access_revoked', 'دسترسی باطل شد'), ('link_sent', 'لینک ارسال شد'), ('link_copied', 'لینک کپی شد'), ('delivery_failed', 'ارسال ناموفق بود'), ('login_succeeded', 'ورود موفق'), ('login_failed', 'ورود ناموفق'), ('session_expired', 'نشست منقضی شد'), ('form_saved', 'فرم ذخیره شد'), ('form_conflict', 'تداخل ذخیره فرم'), ('form_submitted', 'فرم تکمیل شد'), ('general_viewed', 'شرایط عمومی دیده شد'), ('general_accepted', 'شرایط عمومی تأیید شد'), ('private_viewed', 'شرایط خصوصی دیده شد'), ('private_accepted', 'شرایط خصوصی تأیید شد'), ('final_accepted', 'تأیید نهایی انجام شد'), ('logout', 'خروج')], db_index=True, max_length=32)),
                ('metadata', models.JSONField(blank=True, default=dict, validators=[contracts.models.validate_json_object])),
                ('ip_hash', models.CharField(blank=True, max_length=64)),
                ('user_agent', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('access_grant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='events', to='contracts.roomaccessgrant')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_room_events', to=settings.AUTH_USER_MODEL)),
                ('assignment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='events', to='contracts.specialistassignment')),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='room_events', to='contracts.contractproposal')),
            ],
            options={
                'verbose_name': 'رویداد اتاق مشتری',
                'verbose_name_plural': 'رویدادهای اتاق مشتری',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='RoomDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient_phone', models.CharField(db_index=True, max_length=12, validators=[django.core.validators.RegexValidator(message='شماره همراه باید به شکل استاندارد 989xxxxxxxxx ذخیره شود.', regex='^989\\d{9}$')])),
                ('channel', models.CharField(choices=[('sms', 'پیامک'), ('manual', 'ارسال دستی'), ('copy', 'کپی لینک'), ('whatsapp', 'واتس\u200cاپ')], db_index=True, default='sms', max_length=12)),
                ('status', models.CharField(choices=[('queued', 'در صف'), ('sent', 'ارسال\u200cشده'), ('failed', 'ناموفق')], db_index=True, default='queued', max_length=12)),
                ('template_key', models.CharField(blank=True, max_length=80)),
                ('provider_reference', models.CharField(blank=True, max_length=120)),
                ('error_message', models.CharField(blank=True, max_length=240)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('access_grant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='deliveries', to='contracts.roomaccessgrant')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_room_deliveries', to=settings.AUTH_USER_MODEL)),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='room_deliveries', to='contracts.contractproposal')),
            ],
            options={
                'verbose_name': 'سابقه ارسال اتاق مشتری',
                'verbose_name_plural': 'سوابق ارسال اتاق مشتری',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.AddField(
            model_name='roomaccessgrant',
            name='proposal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_grants', to='contracts.contractproposal'),
        ),
        migrations.CreateModel(
            name='GeneralTermsVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField()),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('content_hash', models.CharField(editable=False, max_length=64)),
                ('change_note', models.CharField(blank=True, max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_general_terms_versions', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='versions', to='contracts.generaltermstemplate')),
            ],
            options={
                'verbose_name': 'نسخه شرایط عمومی',
                'verbose_name_plural': 'نسخه\u200cهای شرایط عمومی',
                'ordering': ('-number', '-pk'),
            },
        ),
        migrations.AddField(
            model_name='generaltermstemplate',
            name='current_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='current_for_templates', to='contracts.generaltermsversion'),
        ),
        migrations.AddField(
            model_name='contractproposal',
            name='general_terms_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contract_proposals', to='contracts.generaltermsversion'),
        ),
        migrations.AddConstraint(
            model_name='specialistformtemplateversion',
            constraint=models.UniqueConstraint(fields=('template', 'number'), name='unique_spec_template_version'),
        ),
        migrations.AddIndex(
            model_name='specialistassignment',
            index=models.Index(fields=['status', 'last_saved_at'], name='ctr_spec_status_saved_idx'),
        ),
        migrations.AddConstraint(
            model_name='specialistassignment',
            constraint=models.CheckConstraint(check=models.Q(('revision__gte', 0)), name='spec_assignment_revision_gte_0'),
        ),
        migrations.AddIndex(
            model_name='roomevent',
            index=models.Index(fields=['proposal', 'created_at'], name='ctr_event_proposal_idx'),
        ),
        migrations.AddIndex(
            model_name='roomevent',
            index=models.Index(fields=['event_type', 'created_at'], name='ctr_event_type_time_idx'),
        ),
        migrations.AddIndex(
            model_name='roomdelivery',
            index=models.Index(fields=['proposal', 'created_at'], name='ctr_delivery_proposal_idx'),
        ),
        migrations.AddIndex(
            model_name='roomdelivery',
            index=models.Index(fields=['status', 'created_at'], name='ctr_delivery_status_idx'),
        ),
        migrations.AddIndex(
            model_name='roomaccessgrant',
            index=models.Index(fields=['proposal', 'is_active', 'expires_at'], name='ctr_access_active_exp_idx'),
        ),
        migrations.AddConstraint(
            model_name='roomaccessgrant',
            constraint=models.CheckConstraint(check=models.Q(('credential_version__gte', 1)), name='room_access_version_gte_1'),
        ),
        migrations.AddConstraint(
            model_name='roomaccessgrant',
            constraint=models.UniqueConstraint(fields=('proposal', 'authorized_phone', 'credential_version'), name='unique_room_access_version'),
        ),
        migrations.AddConstraint(
            model_name='roomaccessgrant',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('proposal', 'authorized_phone'), name='unique_active_room_phone'),
        ),
        migrations.AddConstraint(
            model_name='generaltermsversion',
            constraint=models.UniqueConstraint(fields=('template', 'number'), name='unique_general_terms_version'),
        ),
        migrations.RunPython(seed_workspace_foundation, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contractproposal',
            name='last_activity_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]
