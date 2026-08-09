"""Bilingual professional Python/Django bank; correct choice is stored first."""

from .technical_rationales import technical_rationale

BANK_VERSION = 3

SECTIONS = (
    ("python-core", "هسته پایتون", "Python Core", 40, 10),
    ("problem-solving", "حل مسئله و تحلیل کد", "Problem Solving & Code Analysis", 30, 8),
    ("testing-quality", "تست و کیفیت کد", "Testing & Code Quality", 25, 6),
    ("django", "توسعه و معماری جنگو", "Django Development & Architecture", 40, 10),
    ("database", "پایگاه داده و ORM", "Database & ORM", 25, 6),
    ("security", "امنیت وب", "Web Security", 20, 5),
    ("deployment", "استقرار و عملیات", "Deployment & Operations", 20, 5),
)


def q(section, fa, en, correct, *wrong, difficulty=3, subskill="", question_type=None,
      suggested_seconds=75, explanation_fa="", explanation_en=""):
    subskill = subskill or section
    generated_fa, generated_en = technical_rationale(section, subskill, fa, en, correct)
    explanation_fa = explanation_fa or generated_fa
    explanation_en = explanation_en or generated_en
    return {"section": section, "prompt_fa": fa, "prompt_en": en,
            "choices": (correct,) + wrong, "difficulty": difficulty,
            "subskill": subskill,
            "question_type": question_type or ("code_analysis" if "`" in en else "single_choice"),
            "suggested_seconds": suggested_seconds,
            "explanation_fa": explanation_fa, "explanation_en": explanation_en,
            "choice_explanations_fa": (explanation_fa,) + tuple(
                f"«{choice}» در این سناریو رفتار یا مفهوم مورد سؤال را تأمین نمی‌کند." for choice in wrong
            ),
            "choice_explanations_en": (explanation_en,) + tuple(
                f"‘{choice}’ does not provide the behavior or concept required in this scenario." for choice in wrong
            )}


QUESTIONS = [
q("python-core","خروجی `len({1, 1, 2})` چیست؟","What is the result of `len({1, 1, 2})`?","2","3","1","Error",difficulty=1),
q("python-core","کدام نوع داده تغییرناپذیر است؟","Which data type is immutable?","tuple","list","set","dict",difficulty=1),
q("python-core","عملگر مقایسه هویت آبجکت چیست؟","Which operator compares object identity?","is","==","in",":=",difficulty=1),
q("python-core","برای پیمایش همزمان index و value از چه استفاده می‌شود؟","What provides both index and value while iterating?","enumerate","zip","range only","map",difficulty=2),
q("python-core","خروجی `[x*x for x in range(3)]` چیست؟","What does `[x*x for x in range(3)]` return?","[0, 1, 4]","[1, 4, 9]","[0, 1, 2]","(0, 1, 4)",difficulty=1),
q("python-core","هدف `with open(...)` چیست؟","Why use `with open(...)`?","It closes the resource reliably","It encrypts the file","It caches all reads","It makes writes atomic",difficulty=2),
q("python-core","`*args` در تابع چه چیزی دریافت می‌کند؟","What does `*args` collect in a function?","Extra positional arguments as a tuple","Keyword arguments as a dict","Only strings","A generator",difficulty=2),
q("python-core","پیچیدگی متوسط lookup در dict چیست؟","What is the average complexity of a dict lookup?","O(1)","O(n)","O(log n)","O(n²)",difficulty=3),
q("python-core","کدام روش کپی کم‌عمق لیست می‌سازد؟","Which creates a shallow copy of a list?","items.copy()","items = original","copy.deepcopy(items)","id(items)",difficulty=2),
q("python-core","generator چه مزیت اصلی دارد؟","What is a generator's main advantage?","Lazy, memory-efficient iteration","Automatic parallelism","Static typing","Database persistence",difficulty=3),
q("python-core","`@property` چه می‌کند؟","What does `@property` do?","Exposes method logic through attribute access","Makes a method static","Prevents inheritance","Serializes an object",difficulty=3),
q("python-core","برای مقایسه مقدار dataclass معمولاً چه چیزی تولید می‌شود؟","What is normally generated for value comparison in a dataclass?","__eq__","__iter__","__enter__","__call__",difficulty=3),
q("python-core","چرا default mutable در آرگومان تابع خطرناک است؟","Why is a mutable default function argument risky?","It is shared across calls","It is always copied","It cannot be modified","It causes syntax errors",difficulty=4),
q("python-core","در async Python، `await` چه می‌کند؟","What does `await` do in async Python?","Suspends the coroutine until an awaitable completes","Starts a new OS process","Blocks every thread","Converts code to sync",difficulty=4),
q("python-core","هدف type hint چیست؟","What is the purpose of a type hint?","Static analysis and clearer contracts","Runtime encryption","Automatic validation in all cases","Faster SQL",difficulty=2),
q("problem-solving","برای جلوگیری از جست‌وجوی تکراری membership از چه ساختاری استفاده می‌کنید؟","Which structure avoids repeated linear membership searches?","set","list","tuple","string",difficulty=2),
q("testing-quality","بهترین تست برای یک تابع pure چیست؟","What is the best basic test for a pure function?","Assert outputs for representative inputs","Inspect server logs only","Test CSS layout","Mock every value",difficulty=2),
q("testing-quality","اصل Arrange-Act-Assert مربوط به چیست؟","What does Arrange-Act-Assert structure?","A test case","A database index","A deployment pipeline","A class hierarchy",difficulty=2),
q("testing-quality","برای تست exception در pytest از چه استفاده می‌شود؟","How do you test an exception with pytest?","pytest.raises","pytest.warns only","assert False","try without assert",difficulty=3),
q("problem-solving","مزیت dependency injection چیست؟","What is a benefit of dependency injection?","Easier isolation and testing","More global state","Tighter coupling","No interfaces",difficulty=4),
q("problem-solving","برای پردازش n آیتم یک‌بار، پیچیدگی مطلوب چیست؟","For one pass over n items, what is the expected complexity?","O(n)","O(n²)","O(2ⁿ)","O(n!)",difficulty=2),
q("problem-solving","چه زمانی binary search معتبر است؟","When is binary search valid?","When data is sorted","For any linked list","Only for strings","When values are unique only",difficulty=2),
q("testing-quality","یک تست regression چه هدفی دارد؟","What is the purpose of a regression test?","Prevent a fixed bug from returning","Measure network speed","Generate migrations","Format code",difficulty=3),
q("testing-quality","property-based testing چه چیزی تولید می‌کند؟","What does property-based testing generate?","Many inputs to check invariants","Production passwords","Database schemas","HTML templates",difficulty=4),
q("testing-quality","برای خطای intermittent اولین اقدام مناسب چیست؟","What is a good first step for an intermittent failure?","Capture reproducible inputs and context","Ignore it","Add an infinite retry","Disable tests",difficulty=4),
q("django","Model در معماری Django عمدتاً مسئول چیست؟","What is a Django model primarily responsible for?","Data structure and persistence","CSS rendering","DNS configuration","Browser routing",difficulty=1),
q("django","برای URL نام‌دار از چه تابعی استفاده می‌شود؟","What resolves a named Django URL?","reverse","redirect only","render","resolve_static",difficulty=1),
q("django","کاربرد `select_related` چیست؟","What is `select_related` used for?","Joining single-valued relations","Loading CSS","Creating migrations","Hashing passwords",difficulty=3),
q("django","برای ManyToMany و reverse FK کدام مناسب است؟","Which is suitable for ManyToMany and reverse foreign keys?","prefetch_related","select_related","defer only","raw always",difficulty=3),
q("django","چرا QuerySet lazy است؟","Why is a QuerySet lazy?","It waits to query until evaluated","It never queries","It runs only in Celery","It stores JSON",difficulty=3),
q("django","`transaction.atomic` چه تضمینی می‌دهد؟","What does `transaction.atomic` provide?","All-or-nothing database operations","Automatic caching","HTTP retries","Template escaping",difficulty=3),
q("django","فرم ModelForm چه مزیتی دارد؟","What is a benefit of ModelForm?","Model-aware validation and saving","Automatic deployment","SQL indexing","Async execution",difficulty=2),
q("django","برای محدودکردن queryset به کاربر جاری کجا عمل می‌کنید؟","Where should a view restrict a queryset to the current user?","Server-side get_queryset/query logic","Only in JavaScript","Only in CSS","In the URL text",difficulty=3),
q("django","middleware در چه سطحی عمل می‌کند؟","At what level does middleware operate?","Request/response processing","Per model field only","Database storage only","Template CSS only",difficulty=2),
q("django","سیگنال‌ها چه ریسکی دارند؟","What is a common risk of signals?","Hidden side effects","No database access","Mandatory async behavior","They cannot be tested",difficulty=4),
q("django","برای custom user model چه زمانی باید تصمیم گرفت؟","When should you choose a custom user model?","At project start before initial migrations","After production launch only","Never","Inside a template",difficulty=3),
q("django","`F()` expression چه مزیتی دارد؟","What is a benefit of an `F()` expression?","Database-side atomic field operations","Template translation","HTTP compression","Form rendering",difficulty=4),
q("django","برای جلوگیری از N+1 چه باید کرد؟","How do you avoid N+1 queries?","Use appropriate related-object loading","Add more templates","Disable indexes","Loop twice",difficulty=3),
q("django","کدام پاسخ برای API validation نامعتبر مناسب است؟","Which response is appropriate for invalid API input?","400 Bad Request","200 OK","301 Redirect","503 Service Unavailable",difficulty=2),
q("django","migration داده با چه ابزاری نوشته می‌شود؟","How is a data migration normally written?","RunPython with historical models","Raw model import only","Template tags","Static files",difficulty=4),
q("database","هدف database index چیست؟","What is the purpose of a database index?","Speed up selected lookups at write/storage cost","Encrypt rows","Replace backups","Validate HTML",difficulty=2),
q("database","unique constraint کجا باید enforce شود؟","Where should uniqueness be enforced?","In the database (and validated in the app)","Only in JavaScript","Only in documentation","Only in CSS",difficulty=3),
q("database","مشکل lost update با چه چیزی کاهش می‌یابد؟","What helps prevent a lost update?","Row locking or atomic updates","Template caching","Gzip","Static typing",difficulty=4),
q("database","normalization چه هدفی دارد؟","What is a goal of normalization?","Reduce redundant inconsistent data","Increase duplicate values","Remove all relations","Avoid constraints",difficulty=3),
q("database","برای بررسی query کند از چه استفاده می‌شود؟","What helps investigate a slow query?","EXPLAIN / query plan","HTML validator","DNS lookup","Password hasher",difficulty=3),
q("security","CSRF protection برای چه حمله‌ای است؟","What does CSRF protection defend against?","Forged state-changing requests","SQL joins","Slow CSS","Disk failure",difficulty=2),
q("deployment","چرا `DEBUG=False` در production لازم است؟","Why should production use `DEBUG=False`?","Avoid exposing sensitive debug details","Enable migrations","Create users","Compile Python",difficulty=2),
q("security","secret key باید کجا باشد؟","Where should a production secret key live?","A protected environment/secret manager","Committed to Git","A public template","Client-side JavaScript",difficulty=2),
q("deployment","static و user media چه تفاوتی دارند؟","What is the distinction between static files and user media?","Application assets vs user uploads","Both are Python code","Both belong in Git","There is no difference",difficulty=3),
q("deployment","health check مناسب چه چیزی را نشان می‌دهد؟","What should a useful health check indicate?","Whether the service can handle required dependencies","User passwords","Full stack traces publicly","Marketing content",difficulty=4),
]

from .python_django_v2_additions import ADDITIONAL_QUESTIONS  # noqa: E402

QUESTIONS.extend(ADDITIONAL_QUESTIONS)
