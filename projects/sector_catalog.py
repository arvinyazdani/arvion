"""Pure fictional scenarios, keyed by existing validated enquiry goals."""
from projects.demo_briefs import GOALS
from projects.demo_labels import demo_config_labels


# (heading, summary, detail), Persian / English. No commercial/live data.
SCENARIOS = {
    "restaurant": [
        (("یک میز، یک شب به‌یادماندنی", "A table for a memorable evening"), ("سالن باغ · میز دو تا چهار نفره", "Garden room · tables for two to four"), ("فضای داخلی، میز کنار پنجره و دسترسی بدون پله در این سناریوی فرضی. میز گروهی با هماهنگی قبلی؛ شرایط لغو و ظرفیت واقعی باید پیش از تأیید روشن باشند. این صفحه میز رزرو نمی‌کند.", "Indoor window seating and step-free access in this fictional scenario. Group tables by prior arrangement; cancellation and real capacity must be clear before confirmation. This page books no table.")),
        (("از آشپزخانه تا خانه", "From our kitchen to your home"), ("پاستای زعفرانی · آماده‌سازی نمونه ۲۵ دقیقه", "Saffron butter pasta · sample preparation 25 minutes"), ("قارچ و سس کره؛ حاوی گلوتن و لبنیات. سس جدا و بسته‌بندی غذای گرم. محدوده ارسال، هزینه و زمان تخمینی باید پیش از پرداخت روشن شوند؛ این دمو نشانی نمی‌گیرد.", "Mushrooms and butter sauce; contains gluten and dairy. Sauce separately, warm-food packaging. Delivery area, fee and estimated timing must be clear before payment; this demo collects no address.")),
        (("منوی امروز، با جزئیات", "Today's menu, thoughtfully explained"), ("تارت انجیر · ۲۲۰٬۰۰۰ تومان، قیمت فرضی", "Fig and almond tart · 220,000 Toman, fictional price"), ("انجیر، بادام و خمیر کره‌ای؛ حاوی مغزها، گلوتن و لبنیات. مواد، آلرژن‌ها و موجودی باید با آشپزخانه واقعی کنترل شوند؛ این قیمت برای نمونه است.", "Figs, almonds and butter pastry; contains nuts, gluten and dairy. Verify ingredients, allergens and availability with the real kitchen; this price is illustrative.")),
    ],
    "portfolio": [
        (("برای همکاری بعدی", "For the next collaboration"), ("طراحی محصول · پژوهش، جریان و نمونه تعاملی", "Product design · research, flows and prototype"), ("شروع با هدف، مخاطب و محدوده پروژه. نقش طراح، ورودی کارفرما و تعداد بازبینی در پیشنهاد مشخص می‌شوند. این معرفی فرضی است و سابقه واقعی ادعا نمی‌کند.", "Start with goals, audience and project scope. The proposal defines the designer's role, client inputs and review rounds. This fictional introduction claims no real credentials.")),
        (("پشت هر تصویر، یک تصمیم", "Behind every image, a decision"), ("بازآفرینی تجربه خرید روزمره · مطالعه موردی فرضی", "Reframing the everyday shop · fictional case study"), ("مسئله: مقایسه دشوار محصولات. تصمیم: دسته‌بندی روشن و اطلاعات پیش از خرید. خروجی: نمونه صفحه محصول. سهم تیم و اجازه انتشار در پروژه واقعی مشخص می‌شود؛ نتیجه ساختگی ارائه نمی‌کنیم.", "Problem: difficult product comparisons. Decision: clearer categories and pre-purchase information. Output: a product-page prototype. Real cases define team contributions and publication permission; no invented results.")),
        (("آشنایی، پیش از همکاری", "Meet the person behind the work"), ("تجربه کاربر · نظام بصری · روش همکاری", "User experience · visual systems · working methods"), ("گفت‌وگو، نمونه‌سازی و بازبینی با خروجی روشن در هر مرحله. رزومه، ظرفیت و کارهای قابل انتشار باید با اطلاعات واقعی جایگزین شوند. این پروفایل متعلق به شخص واقعی نیست.", "Conversation, prototyping and review with a clear output at each stage. Replace the CV, availability and published work with verified information. This profile represents no real person.")),
    ],
    "corporate": [
        (("از مسئله به برنامه اجرایی", "From problem to delivery plan"), ("شناخت → طراحی → تحویل", "Discovery → design → delivery"), ("ابتدا هدف، کاربران و معیار پذیرش؛ سپس جریان‌ها و نمونه تعاملی؛ در پایان تحویل مرحله‌ای. هزینه، زمان، مسئولیت و سطح پشتیبانی در پیشنهاد اختصاصی تعیین می‌شوند.", "First goals, users and acceptance criteria; then flows and a prototype; finally milestone delivery. Cost, timing, ownership and support belong in a tailored proposal.")),
        (("خدمت دقیق، انتخاب آگاهانه", "Clear services, informed choices"), ("بهبود فرایند · سامانه مشتریان · وب‌سایت", "Process improvement · customer platform · website"), ("هر خدمت با ورودی، خروجی و مرز مسئولیت مشخص. نیاز به اتصال، نقش‌ها و مجوزها در نیازسنجی واقعی تعیین می‌شوند؛ این نمونه قیمت یا اتصال آماده وعده نمی‌دهد.", "Each service specifies inputs, outputs and boundaries. Real discovery determines integrations, roles and permissions; this sample promises no fixed price or ready integration.")),
        (("همکاری قابل پیگیری", "An accountable engagement"), ("پرونده نمونه · مرحله طراحی · منتظر بازبینی", "Sample case · design stage · awaiting review"), ("نمای مشتری فعلی: وضعیت مرحله، خروجی قابل بررسی، مسئول پاسخ‌گویی و درخواست پشتیبانی. این پرونده فرضی است؛ در محصول واقعی مشتری فقط اسناد مجاز خودش را می‌بیند.", "Existing-client view: milestone status, reviewable deliverable, contact owner and support request. This case is fictional; real customers see only their own authorized documents.")),
    ],
    "clinic": [
        (("مراجعه با مسیر روشن", "A clear path to your visit"), ("خدمت → نوع مراجعه → زمان", "Service → visit type → time"), ("مشاوره اولیه و پیگیری مسیر جدا دارند. شرح خدمت، مدت، دسترسی و شرایط لغو باید از کلینیک تأیید شوند. این نمونه تشخیص، توصیه درمان یا رزرو واقعی نیست و اطلاعات پزشکی نمی‌گیرد.", "Initial visits and follow-ups have separate paths. Confirm scope, duration, access and cancellation with the clinic. This preview is not diagnosis, treatment advice or a real booking; it collects no health data.")),
        (("خدمت و متخصص، شفاف", "Services and practitioners, clearly explained"), ("خدمات پوست · تغذیه و سبک زندگی", "Skin services · nutrition and lifestyle"), ("دامنه خدمت و محدودیت‌ها با نظر متخصص واقعی وارد می‌شوند. صلاحیت و اطلاعات حرفه‌ای پیش از انتشار بررسی می‌شوند. نام‌ها و پروفایل‌های این دمو فرضی‌اند.", "Real practitioners supply service scope and limitations. Verify qualifications and professional information before publication. Demo names and profiles are fictional.")),
        (("آگاهی پیش از مراجعه", "Information before your visit"), ("راهنمای پذیرش · پرسش‌های رایج · آموزش", "Reception guide · common questions · education"), ("راهنمای عمومی: مسیر پذیرش، دسترسی و شرایط مراجعه را پیش از آمدن از کلینیک بپرسید. پرسش پزشکی شخصی به پزشک ارجاع داده می‌شود. محتوای نهایی نیازمند تأیید تخصصی است.", "General guide: ask the clinic about reception, access and visit arrangements beforehand. Refer personal medical questions to a practitioner. Final content needs professional approval.")),
    ],
    "education": [
        (("از درس اول تا پروژه نهایی", "From the first lesson to a final project"), ("مبانی طراحی محصول · مسیر فرضی چهار هفته‌ای", "Product design essentials · fictional four-week path"), ("هفته اول صورت مسئله، دوم پژوهش، سوم نمونه‌سازی و چهارم بازبینی پروژه. پیش‌نیاز نمونه: آشنایی با مرورگر. مدت دسترسی و شیوه بازخورد در دوره واقعی مشخص می‌شوند؛ اینجا دوره فروخته نمی‌شود.", "Week one: problem framing; two: research; three: prototyping; four: project review. Sample prerequisite: basic browser skills. Real courses define access and feedback; no course is sold here.")),
        (("یک جلسه، یک موضوع مشخص", "One session, one focused topic"), ("از ایده تا اولین محصول · وبینار فرضی ۴۵ دقیقه", "From idea to first product · fictional 45-minute webinar"), ("ده دقیقه صورت مسئله، بیست دقیقه نمونه‌سازی و پانزده دقیقه پرسش‌وپاسخ. مدت دسترسی به ضبط و رضایت انتشار باید پیش از شرکت روشن باشند. اینجا جلسه یا ثبت‌نام زنده نداریم.", "Ten minutes framing, twenty prototyping and fifteen Q&A. Clarify recording access and publication consent before attendance. No live session or enrollment happens here.")),
        (("یک درس کوتاه را امتحان کنید", "Try a short lesson"), ("متن درس · اولویت‌بندی محتوا", "Lesson text · content priorities"), ("کاربر اول می‌پرسد چه چیزی ارائه می‌کنید، سپس آیا مناسب اوست و در پایان قدم بعدی چیست. تمرین: عنوان، توضیح و اقدام اصلی یک صفحه را پیدا کنید؛ آیا مسیر بعدی روشن است؟ هیچ پاسخی ارسال یا نمره‌ای ثبت نمی‌شود.", "Visitors first ask what you offer, then whether it fits, then what to do next. Exercise: find a page's heading, explanation and primary action; is the next step clear? No answer is submitted or graded.")),
    ],
    "jewelry": [
        (("قطعاتی با شناسنامه روشن", "Pieces with a clear identity"), ("انگشتر آفتاب · مشخصات فرضی طلای ۱۸ عیار", "Aftab signet ring · fictional 18-karat specifications"), ("وزن نمونه ۴٫۲ گرم، پرداخت مات و اندازه ۵۴. وزن نهایی، جنس و شرایط تعمیر باید پیش از خرید تأیید شوند. همه مشخصات فرضی‌اند و قیمت روز نیازمند استعلام است.", "Sample weight 4.2 g, matte finish, size 54. Confirm final weight, material and repair terms before purchase. All specifications are fictional; current pricing requires a quote.")),
        (("از ایده شما تا مشخصات ساخت", "From your idea to a craft brief"), ("طرح → عیار و اندازه → تأیید ساخت", "Design → purity and size → craft approval"), ("عیار، تزئین و اندازه را در سازنده پایین انتخاب کنید؛ این‌ها ترجیح اولیه‌اند. کارشناس قابلیت ساخت، وزن و مبلغ نهایی را تأیید می‌کند. این انتخاب‌ها سفارش واقعی نیستند.", "Choose purity, finish and size in the builder below; these are initial preferences. A specialist confirms feasibility, weight and final amount. These choices are not a real order.")),
        (("قیمت شفاف، پیش از پرداخت", "Transparent pricing before payment"), ("ماده اولیه · اجرت · مبلغ قابل تأیید", "Material · making charges · confirmed total"), ("وزن نهایی، نرخ با زمان اعتبار و هزینه‌های تفکیک‌شده باید روشن باشند. مبلغ و شرایط تحویل نیازمند تأیید فروشگاه‌اند؛ این دمو نرخ زنده، محاسبه مالیات یا دریافت وجه ندارد.", "Explain final weight, quote validity and itemised charges. The shop confirms amount and delivery terms; this demo has no live rate, tax calculation or payment collection.")),
    ],
}


FACTS = {
    "restaurant": [
        [("فضا", "Room", "سالن باغ", "Garden room"), ("میز", "Table", "دو تا چهار مهمان", "Two to four guests"), ("رزرو", "Reservation", "نیازمند تأیید رستوران", "Restaurant approval required")],
        [("غذا", "Dish", "پاستای زعفرانی", "Saffron butter pasta"), ("آماده‌سازی نمونه", "Sample preparation", "۲۵ دقیقه", "25 minutes"), ("آلرژن نمونه", "Sample allergens", "گلوتن و لبنیات", "Gluten and dairy")],
        [("دسر", "Dessert", "تارت انجیر", "Fig and almond tart"), ("قیمت فرضی", "Fictional price", "۲۲۰٬۰۰۰ تومان", "220,000 Toman"), ("ترکیبات نمونه", "Sample ingredients", "انجیر، بادام، کره", "Figs, almonds, butter")],
    ],
    "portfolio": [
        [("تخصص نمونه", "Sample practice", "طراحی محصول دیجیتال", "Digital product design"), ("خروجی", "Output", "نمونه تعاملی", "Interactive prototype"), ("شروع", "Starting point", "هدف و مخاطب", "Goal and audience")],
        [("مسئله", "Problem", "مقایسه دشوار محصول", "Difficult comparisons"), ("تصمیم", "Decision", "اطلاعات پیش از خرید", "Pre-purchase information"), ("خروجی فرضی", "Illustrative output", "صفحه محصول", "Product page")],
        [("تمرکز", "Focus", "تجربه و نظام بصری", "Experience and visual systems"), ("روش", "Method", "نمونه‌سازی و بازبینی", "Prototype and review"), ("پروفایل", "Profile", "فرضی، نه رزومه واقعی", "Fictional, not a real CV")],
    ],
    "corporate": [
        [("مرحله اول", "Stage one", "شناخت نیاز", "Discovery"), ("مرحله دوم", "Stage two", "طراحی راهکار", "Solution design"), ("مرحله سوم", "Stage three", "تحویل و پذیرش", "Delivery and acceptance")],
        [("فرایند", "Process", "نقشه عملیات", "Operations map"), ("سامانه", "Platform", "پرونده مشتری", "Customer case"), ("وب‌سایت", "Website", "خدمات و تماس", "Services and contact")],
        [("پرونده فرضی", "Fictional case", "سامانه خدمات", "Services platform"), ("مرحله نمونه", "Sample stage", "منتظر بازبینی طراحی", "Awaiting design review"), ("قدم بعدی", "Next step", "بررسی خروجی مرحله", "Review the deliverable")],
    ],
    "clinic": [
        [("خدمت نمونه", "Sample service", "مشاوره اولیه", "Initial consultation"), ("نوع مراجعه", "Visit type", "اولین مراجعه یا پیگیری", "Initial or follow-up"), ("نوبت", "Booking", "دمو؛ ثبت نمی‌شود", "Preview; not booked")],
        [("خدمات نمونه", "Sample services", "پوست و تغذیه", "Skin and nutrition"), ("پروفایل‌ها", "Profiles", "نام‌های فرضی", "Fictional names"), ("پیش از انتشار", "Before publication", "بررسی صلاحیت واقعی", "Verify real qualifications")],
        [("راهنما", "Guide", "مسیر پذیرش", "Reception path"), ("پرسش‌ها", "Questions", "دسترسی و شرایط مراجعه", "Access and arrangements"), ("محتوا", "Content", "آگاهی عمومی، نه درمان", "Information, not treatment")],
    ],
    "education": [
        [("دوره فرضی", "Fictional course", "مبانی طراحی محصول", "Product design essentials"), ("مدت نمونه", "Sample duration", "چهار هفته", "Four weeks"), ("خروجی تمرین", "Exercise output", "نمونه صفحه محصول", "Product-page prototype")],
        [("موضوع نمونه", "Sample topic", "از ایده تا محصول", "From idea to product"), ("برنامه فرضی", "Fictional outline", "۱۰ + ۲۰ + ۱۵ دقیقه", "10 + 20 + 15 minutes"), ("جلسه زنده", "Live session", "این دمو برگزار نمی‌کند", "Not hosted by this demo")],
        [("درس نمونه", "Sample lesson", "اولویت‌بندی محتوا", "Content priorities"), ("قالب", "Format", "متن و تمرین", "Reading and exercise"), ("تمرین", "Exercise", "پیداکردن اقدام اصلی", "Find the main action")],
    ],
    "jewelry": [
        [("عیار فرضی", "Fictional purity", "۱۸ عیار", "18 karat"), ("وزن نمونه", "Sample weight", "۴٫۲ گرم", "4.2 grams"), ("قیمت", "Price", "نیازمند استعلام روز", "Current quote required")],
        [("قدم اول", "First step", "طرح و کاربرد", "Design and purpose"), ("قدم دوم", "Second step", "عیار، اندازه و تزئین", "Purity, size and finish"), ("پیش از ساخت", "Before crafting", "تأیید کارشناس", "Specialist confirmation")],
        [("ماده اولیه", "Material", "وزن و نرخ تأییدشده", "Confirmed weight and rate"), ("هزینه‌ها", "Charges", "اجرت و جزئیات روشن", "Making and clear breakdown"), ("پرداخت", "Payment", "بعد از تأیید مبلغ نهایی", "After final quote approval")],
    ],
}

RECOMMENDATIONS = {
    "restaurant": (("booking", "catalog"), ("catalog", "payment"), ("catalog",)),
    "portfolio": (("booking",), ("blog",), ("blog", "multilingual")),
    "corporate": (("booking",), ("blog", "multilingual"), ("membership",)),
    "clinic": (("booking",), ("blog",), ("blog", "membership")),
    "education": (("membership", "payment"), ("membership",), ("blog", "membership")),
    "jewelry": (("catalog",), ("booking", "catalog"), ("catalog", "payment", "membership")),
}


def sector_catalog(category, lang="fa"):
    """Return fresh, localized fixtures; no ORM and no mutation of shared data."""
    if category not in SCENARIOS:
        return None
    lang = "en" if lang == "en" else "fa"
    index = 1 if lang == "en" else 0
    feature_labels = dict(demo_config_labels(lang, category)["features"])
    return {"category": category, "goals": [
        {"key": key, "label": fa if lang == "fa" else en, "title": scene[0][index],
         "summary": scene[1][index], "detail": scene[2][index],
         "number": ("۰۱", "۰۲", "۰۳")[position] if lang == "fa" else f"{position + 1:02d}",
         "facts": [{"label": row[index], "value": row[index + 2]} for row in FACTS[category][position]],
         "features": [{"key": key, "label": feature_labels[key]} for key in RECOMMENDATIONS[category][position]]}
        for position, ((key, fa, en), scene) in enumerate(zip(GOALS[category], SCENARIOS[category]))
    ]}
