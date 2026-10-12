"""Public, bilingual demo content and bounded order preferences (no PII)."""

GOALS = {
    "ecommerce": (("sales", "فروش آنلاین", "Online sales"), ("catalogue", "معرفی و استعلام محصول", "Product enquiries"), ("repeat", "خرید مجدد مشتریان", "Repeat purchases")),
    "restaurant": (("tables", "رزرو میز", "Table reservations"), ("takeaway", "سفارش بیرون‌بر", "Takeaway orders"), ("menu", "منوی دیجیتال", "Digital menu")),
    "portfolio": (("enquiries", "دریافت پروژه", "Project enquiries"), ("work", "نمایش نمونه‌کار", "Showcase work"), ("profile", "برند شخصی", "Personal profile")),
    "corporate": (("consult", "درخواست مشاوره", "Consultation enquiries"), ("services", "معرفی خدمات", "Present services"), ("clients", "خدمات به مشتریان فعلی", "Existing client services")),
    "clinic": (("appointments", "نوبت‌دهی", "Appointments"), ("care", "معرفی خدمات و پزشکان", "Services and practitioners"), ("education", "آموزش و پیگیری", "Guidance and follow-up")),
    "education": (("courses", "فروش دوره", "Course sales"), ("webinars", "برگزاری وبینار", "Webinars"), ("learning", "پنل یادگیری", "Learning portal")),
    "jewelry": (("collection", "معرفی کالکشن و استعلام", "Collections and enquiries"), ("custom", "سفارش ساخت اختصاصی", "Bespoke commissions"), ("shop", "فروش آنلاین", "Online sales")),
    "accounting": (("daily", "ثبت دخل‌وخرج روزانه", "Daily money tracking"), ("accounts", "مدیریت چند حساب", "Manage multiple accounts"), ("reports", "گزارش و خروجی مالی", "Financial reports and exports")),
}
COMMON = {
    "scope": (("focused", "سایت جمع‌وجور؛ تا ۵ صفحه", "Focused site; up to 5 pages"), ("complete", "سایت کامل؛ ۶ تا ۱۲ صفحه", "Complete site; 6–12 pages"), ("platform", "سامانه با پنل اختصاصی", "Platform with a dedicated portal")),
    "content": (("ready", "متن و تصاویر آماده است", "Copy and images are ready"), ("partial", "بخشی از محتوا آماده است", "Some content is ready"), ("help", "برای محتوا کمک می‌خواهم", "I need help with content")),
    "timing": (("flexible", "زمان‌بندی با پیشنهاد شما", "Recommend a timeline"), ("month", "ترجیحاً طی یک ماه", "Preferably within a month"), ("quarter", "طی سه ماه آینده", "Within the next three months")),
}
FIELD_LABELS = {
    "goal": ("هدف اصلی سایت", "Main website goal"),
    "scope": ("حجم پروژه", "Project scope"),
    "content": ("وضعیت محتوا", "Content readiness"),
    "timing": ("زمان مدنظر", "Preferred timeline"),
}

ACCOUNTING_SCOPE = (
    ("focused", "ثبت سادهٔ روزانه", "Simple daily tracking"),
    ("complete", "چند حساب و انتقال بین آن‌ها", "Multiple accounts and transfers"),
    ("platform", "گزارش و خروجی قابل چاپ", "Reports and printable exports"),
)

# Each topic adds real visitor-facing content, not software marketing claims.
# All brands/scenarios are fictional. No live medical, trading or booking action.
STORIES = {
    "restaurant": (
        ("از آشپزخانه تا میز شما", "From our kitchen to your table", "منویی که با فصل حرکت می‌کند", "A menu that moves with the season", "مواد اولیه‌ی ساده، ترکیب‌های دقیق و پیشنهادهایی برای دورهمی‌های کوچک. پیش از انتخاب، ترکیبات و حساسیت‌های غذایی هر غذا را ببینید.", "Simple ingredients, thoughtful pairings and choices for small gatherings. Explore ingredients and allergen information before choosing.", (("گیاهی", "Plant-based"), ("پیشنهاد فصل", "Seasonal choices"), ("ترکیبات شفاف", "Clear ingredients"))),
        ("برای دورهمی بعدی", "For your next gathering", "یک میز. یک مناسبت. یک تجربه.", "A table. An occasion. An experience.", "از شام دونفره تا پذیرایی گروهی؛ تعداد مهمان، زمان و ترجیحات غذایی را مشخص کنید. هماهنگی نهایی باید توسط رستوران تأیید شود.", "From dinner for two to group hosting: choose the party size, time and food preferences. Final arrangements require restaurant confirmation.", (("میز دونفره", "Dinner for two"), ("پذیرایی گروهی", "Group hosting"), ("درخواست ویژه", "Special requests"))),
    ),
    "ecommerce": (
        ("جزئیات زندگی روزمره", "Everyday details", "کمتر، اما با دقت بیشتر", "Fewer things, chosen thoughtfully", "محصول را از نزدیک بشناسید؛ جنس، ابعاد و شیوه‌ی نگهداری کنار تصاویر قرار می‌گیرند تا انتخاب فقط بر اساس ظاهر نباشد.", "Know each piece: materials, dimensions and care guidance accompany its images, so the choice goes beyond appearance.", (("ابعاد و جنس", "Dimensions and materials"), ("راهنمای نگهداری", "Care guidance"), ("مقایسه محصول", "Product comparison"))),
        ("پیش از خرید", "Before you buy", "از انتخاب تا تحویل، روشن و قابل پیگیری", "Clear from selection to delivery", "موجودی، روش ارسال و شرایط بازگشت باید پیش از پرداخت مشخص باشند. این نمونه مسیر خرید را نشان می‌دهد؛ خرید واقعی انجام نمی‌شود.", "Availability, shipping choices and return terms belong before payment. This sample illustrates the journey; it does not place a real order.", (("موجودی روشن", "Clear availability"), ("انتخاب ارسال", "Delivery choices"), ("پیگیری سفارش", "Order tracking"))),
    ),
    "jewelry": (
        ("پشت هر قطعه", "Behind each piece", "از طرح اولیه تا جزئیات ساخت", "From first sketch to final craft", "عیار، وزن، نوع سنگ و روش ساخت هر قطعه جدا معرفی می‌شوند. مبلغ نهایی با اجرت و شرایط روز، پس از بررسی مشخصات اعلام می‌شود.", "Purity, weight, stones and craft are described individually. A final quote including workmanship and current conditions follows specification review.", (("عیار و وزن", "Purity and weight"), ("اجرت شفاف", "Clear workmanship"), ("مشخصات سنگ", "Stone details"))),
        ("ساخته‌شده برای شما", "Made for you", "قطعه‌ای با داستان شخصی شما", "A piece with your own story", "اندازه، طرح و تزئینات را برای مشاوره انتخاب کنید. قبل از شروع ساخت، مشخصات، زمان تحویل و قیمت باید به تأیید شما برسند.", "Choose size, design and details for a consultation. Specifications, delivery time and price need your approval before production begins.", (("مشاوره طرح", "Design consultation"), ("تأیید پیش از ساخت", "Approval before crafting"), ("شناسنامه محصول", "Product record"))),
    ),
    "accounting": (
        ("پول روزمره، تصویر روشن", "Everyday money, clearly in view", "ثبت سریع، بدون پیچیدگی", "Quick entries, without the clutter", "هزینه و درآمد را با مبلغ، حساب و توضیح ثبت کنید. مانده از موجودی آغازین و تراکنش‌های معتبر محاسبه می‌شود؛ انتقال میان حساب‌های خودتان درآمد یا هزینه نیست.", "Record an expense or income with its amount, account and a short note. Balances reflect opening amounts and valid entries; moving money between your own accounts is not income or spending.", (("ثبت درآمد و هزینه", "Income and expenses"), ("چند حساب شخصی", "Multiple personal accounts"), ("انتقال روشن", "Clear transfers"))),
        ("پایان ماه، قابل فهم", "A month you can understand", "گزارش و خروجی در کنار هم", "Reports and exports in one place", "فهرست تراکنش‌ها را جست‌وجو کنید، روند درآمد و هزینه را در گزارش ببینید و نسخهٔ قابل چاپ تهیه کنید. این پیش‌نمایش فقط از داده‌های ساختگی استفاده می‌کند.", "Search your entries, review income and expense trends, and prepare a printable record. This preview uses fictional data only.", (("جست‌وجوی تراکنش", "Search entries"), ("گزارش دوره‌ای", "Period reports"), ("خروجی قابل چاپ", "Printable export"))),
    ),
    "portfolio": (
        ("پشت صحنه‌ی کار", "Behind the work", "هر پروژه، یک تصمیم طراحی", "Every project, a design decision", "مسئله، محدودیت‌ها و مسیر رسیدن به نتیجه را کنار خروجی نهایی ببینید. مطالعه‌ی موردی کمک می‌کند روش فکر کردن استودیو را بشناسید.", "Explore the problem, constraints and decisions beside the outcome. Case studies reveal how the studio thinks, not only how its work looks.", (("مسئله و ایده", "Problem and idea"), ("فرایند طراحی", "Design process"), ("خروجی نهایی", "Final outcome"))),
        ("شروع همکاری", "Starting together", "برای ایده‌ی بعدی شما", "For your next idea", "زمینه پروژه و هدف را با ما در میان بگذارید. بعد از بررسی تناسب، محدوده کار و روش همکاری روشن می‌شود؛ ارسال درخواست تعهد مالی ایجاد نمی‌کند.", "Share the project context and goal. After a fit review, scope and working arrangements become clear; an enquiry creates no payment obligation.", (("شناخت مسئله", "Understand the problem"), ("تعریف محدوده", "Define the scope"), ("تحویل مرحله‌ای", "Staged delivery"))),
    ),
    "corporate": (
        ("خدمات متناسب با مسئله", "Services shaped around the problem", "به جای نسخه‌ی یکسان، مسیر روشن", "A clear path, not a one-size-fits-all answer", "ابتدا وضعیت فعلی و هدف کسب‌وکار بررسی می‌شود. پیشنهاد همکاری شامل محدوده، مسئولیت‌ها و خروجی قابل ارزیابی است.", "Start with the current situation and business goal. An engagement proposal defines scope, responsibilities and assessable outcomes.", (("بررسی وضعیت", "Situation review"), ("پیشنهاد اجرایی", "Action proposal"), ("گزارش پیشرفت", "Progress reporting"))),
        ("همکاری قابل پیگیری", "An accountable engagement", "از گفتگو تا اجرای مرحله‌ای", "From conversation to staged delivery", "هر مرحله صاحب مسئولیت، خروجی مشخص و زمان بازبینی دارد. تصمیم‌های مهم در مسیر همکاری ثبت و با تیم شما هماهنگ می‌شوند.", "Each stage has an owner, a clear output and a review point. Key decisions are recorded and coordinated with your team.", (("مسئول مشخص", "Named owner"), ("بازبینی دوره‌ای", "Scheduled reviews"), ("خروجی مستند", "Documented outcomes"))),
    ),
    "clinic": (
        ("پیش از مراجعه", "Before your visit", "اطلاعات روشن، انتخاب آگاهانه", "Clear information, informed choices", "حوزه خدمات، معرفی متخصص و راهنمای آمادگی برای مراجعه را بخوانید. محتوای این نمونه توصیه درمانی نیست و جای مشاوره پزشک را نمی‌گیرد.", "Explore services, practitioner profiles and preparation guidance. This sample is not medical advice or a substitute for a clinician's consultation.", (("معرفی متخصص", "Practitioner profiles"), ("راهنمای مراجعه", "Visit preparation"), ("انتخاب زمان", "Time selection"))),
        ("نوبت بدون پیچیدگی", "Appointments without friction", "از انتخاب خدمت تا تأیید نوبت", "From choosing a service to confirming a visit", "خدمت و زمان مناسب را انتخاب کنید و بعد از تأیید مرکز، جزئیات مراجعه را دریافت کنید. در این دمو اطلاعات پزشکی جمع‌آوری نمی‌شود.", "Choose a service and suitable time, then receive visit details after clinic confirmation. No health information is collected in this demo.", (("انتخاب خدمت", "Choose a service"), ("تأیید مرکز", "Clinic confirmation"), ("راهنمای پیگیری", "Follow-up guidance"))),
    ),
    "education": (
        ("یادگیری با مسیر مشخص", "Learning with direction", "از اولین جلسه تا تمرین عملی", "From the first lesson to hands-on practice", "سرفصل، پیش‌نیاز و شکل تمرین‌ها را قبل از ثبت‌نام ببینید. هر دوره مسیر یادگیری مشخصی دارد و دستاوردهای آن قابل بررسی است.", "Review the syllabus, prerequisites and exercises before enrolling. Each course has a defined learning path and assessable outcomes.", (("سرفصل شفاف", "Clear syllabus"), ("تمرین عملی", "Practical exercises"), ("پیگیری پیشرفت", "Progress tracking"))),
        ("فراتر از ویدیو", "Beyond video", "گفتگو، تمرین و یادگیری پیوسته", "Conversation, practice and continued learning", "جلسه زنده، محتوای ضبط‌شده و تمرین در یک مسیر قرار می‌گیرند. انتخاب‌های این نمونه فقط تجربه پنل را نشان می‌دهند و ثبت‌نام واقعی نیستند.", "Live sessions, recordings and exercises form one learning path. This sample demonstrates the portal experience; it does not enrol anyone.", (("جلسه زنده", "Live sessions"), ("محتوای ضبط‌شده", "Recorded content"), ("پرسش و پاسخ", "Questions and answers"))),
    ),
}


def brief_fields(category, lang):
    index = 1 if lang == "fa" else 2
    choices = {"goal": GOALS.get(category, ()), **COMMON}
    if category == "accounting":
        choices["scope"] = ACCOUNTING_SCOPE
    labels = dict(FIELD_LABELS)
    if category == "accounting":
        labels["scope"] = ("مسیر مالی موردنیاز", "The finance workflow you need")
    return [{"key": key, "label": labels[key][index - 1],
             "options": [(value, fa if lang == "fa" else en) for value, fa, en in items]}
            for key, items in choices.items()]


def brief_labels(values, category, lang):
    """Ignore malformed/unknown stored fields instead of exposing arbitrary data."""
    if not isinstance(values, dict):
        return []
    rows = []
    for field in brief_fields(category, lang):
        value = values.get(field["key"])
        label = dict(field["options"]).get(value) if isinstance(value, str) else None
        if label:
            rows.append({"label": field["label"], "value": label})
    return rows


def story_sections(category, lang):
    fa = lang == "fa"
    return [{"eyebrow": row[0 if fa else 1], "title": row[2 if fa else 3],
             "text": row[4 if fa else 5], "points": [point[0 if fa else 1] for point in row[6]]}
            for row in STORIES.get(category, ())]
