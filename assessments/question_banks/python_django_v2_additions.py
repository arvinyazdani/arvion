"""Additional reviewed items for the 200-question Python/Django v2 bank."""

EXPERT_SUBSKILLS = {
    "descriptors", "inheritance", "asyncio", "distributed-systems", "concurrency",
    "mutation-testing", "contract-testing", "transactions", "orm-performance",
    "query-plans", "isolation", "ssrf", "authorization", "migrations",
    "deployment-strategy", "disaster-recovery",
}


def build(section, specs):
    questions = []
    for fa, en, correct, wrong1, wrong2, wrong3, difficulty, subskill in specs:
        if difficulty == 4 and subskill in EXPERT_SUBSKILLS:
            difficulty = 5
        explanation_fa = f"«{correct}» پاسخ درست است و دقیقاً با قواعد {subskill} در این سناریو سازگار است."
        explanation_en = f"‘{correct}’ is correct and matches the {subskill} rules required by this scenario."
        wrong = (wrong1, wrong2, wrong3)
        questions.append({
            "section": section, "prompt_fa": fa, "prompt_en": en,
            "choices": (correct,) + wrong, "difficulty": difficulty,
            "subskill": subskill, "question_type": "code_analysis" if "`" in en else "single_choice",
            "suggested_seconds": 90 if difficulty >= 4 else 70,
            "explanation_fa": explanation_fa, "explanation_en": explanation_en,
            "choice_explanations_fa": (explanation_fa,) + tuple(
                f"«{choice}» با شرایط مسئله یا رفتار تعریف‌شده {subskill} سازگار نیست." for choice in wrong
            ),
            "choice_explanations_en": (explanation_en,) + tuple(
                f"‘{choice}’ does not match the scenario or the defined {subskill} behavior." for choice in wrong
            ),
        })
    return questions


PYTHON_CORE = build("python-core", [
    ("خروجی `bool([])` چیست؟", "What is the result of `bool([])`?", "False", "True", "None", "TypeError", 1, "truthiness"),
    ("`dict.get('x', 0)` برای کلید ناموجود چه می‌دهد؟", "What does `dict.get('x', 0)` return for a missing key?", "0", "None", "KeyError", "False", 1, "mappings"),
    ("تفاوت اصلی `append` و `extend` چیست؟", "What is the key difference between `append` and `extend`?", "append adds one object; extend adds items from an iterable", "Both always add one item", "extend returns a new list", "append accepts only strings", 2, "sequences"),
    ("خروجی `'a,b'.split(',')` چیست؟", "What does `'a,b'.split(',')` return?", "['a', 'b']", "('a', 'b')", "['a,b']", "'ab'", 1, "strings"),
    ("`zip(a, b)` چه زمانی متوقف می‌شود؟", "When does `zip(a, b)` stop by default?", "When the shortest iterable is exhausted", "When the longest iterable is exhausted", "Only after an error", "After one item", 2, "iteration"),
    ("کاربرد `nonlocal` چیست؟", "What is `nonlocal` used for?", "Rebinding a variable in an enclosing function scope", "Creating a global variable", "Importing a module", "Freezing a local value", 3, "scope"),
    ("یک closure چه چیزی را حفظ می‌کند؟", "What does a closure retain?", "References to variables from its enclosing scope", "Only global constants", "The current OS thread", "A copy of every module", 3, "closures"),
    ("decorator تابع معمولاً چه کاری انجام می‌دهد؟", "What does a function decorator normally do?", "Receives a callable and returns a callable", "Compiles Python to SQL", "Creates an OS process", "Disables exceptions", 3, "decorators"),
    ("متد `__enter__` متعلق به کدام protocol است؟", "Which protocol uses `__enter__`?", "Context manager", "Iterator", "Descriptor only", "Serialization", 2, "protocols"),
    ("iterator پایان داده را چگونه اعلام می‌کند؟", "How does an iterator signal exhaustion?", "Raises StopIteration", "Returns False forever", "Raises EOFError", "Returns an empty list", 2, "iteration"),
    ("در `try/except/else` بخش `else` چه زمانی اجرا می‌شود؟", "When does `else` run in `try/except/else`?", "When the try block raises no handled exception", "Only after an exception", "Before the try block", "Only when finally is absent", 3, "exceptions"),
    ("مزیت `raise NewError() from exc` چیست؟", "Why use `raise NewError() from exc`?", "It preserves explicit exception causality", "It suppresses every traceback", "It retries the operation", "It converts errors to warnings", 4, "exceptions"),
    ("`functools.lru_cache` برای چه تابعی خطرناک است؟", "For which function is `functools.lru_cache` risky?", "A function whose result depends on mutable external state", "A deterministic pure function", "A recursive Fibonacci function", "A function with hashable arguments", 4, "caching"),
    ("استفاده از `field(default_factory=list)` در dataclass چه مشکلی را حل می‌کند؟", "What does `field(default_factory=list)` solve in a dataclass?", "It creates a fresh list per instance", "It makes the list immutable", "It sorts the list", "It shares one cached list", 3, "dataclasses"),
    ("`__slots__` معمولاً چه اثری دارد؟", "What is a typical effect of `__slots__`?", "Restricts instance attributes and may reduce memory", "Makes every method asynchronous", "Prevents object creation", "Adds database indexes", 4, "object-model"),
    ("descriptor دارای `__get__` و `__set__` چه نوعی است؟", "A descriptor with `__get__` and `__set__` is what kind?", "A data descriptor", "A generator", "A metaclass only", "A context variable", 5, "descriptors"),
    ("ترتیب MRO در وراثت چندگانه پایتون با چه الگوریتمی ساخته می‌شود؟", "Which algorithm determines Python's multiple-inheritance MRO?", "C3 linearization", "Depth-first search only", "Dijkstra", "Topological sort without constraints", 5, "inheritance"),
    ("GIL در CPython چه چیزی را محدود می‌کند؟", "What does the GIL limit in CPython?", "Parallel execution of Python bytecode by threads", "All I/O concurrency", "Multiprocessing", "Database transactions", 4, "concurrency"),
    ("برای کار CPU-bound موازی در CPython معمولاً کدام مناسب‌تر است؟", "What is usually preferable for parallel CPU-bound work in CPython?", "Multiple processes", "One asyncio task", "More synchronous callbacks", "A larger recursion limit", 3, "concurrency"),
    ("`asyncio.gather` بدون `return_exceptions=True` با اولین exception چه می‌کند؟", "What does `asyncio.gather` do when an awaited task raises and `return_exceptions` is false?", "Propagates the exception to the awaiter", "Silently ignores it", "Converts it to None", "Restarts every task", 4, "asyncio"),
    ("`contextvars` برای چه مسئله‌ای مناسب است؟", "What problem are `contextvars` designed for?", "Context-local state across asynchronous tasks", "Global file locking", "Static type inference", "Process creation", 4, "asyncio"),
    ("مزیت `Protocol` در typing چیست؟", "What is a benefit of `Protocol` in typing?", "Structural subtyping without explicit inheritance", "Runtime input validation automatically", "Faster bytecode", "Encrypted attributes", 4, "typing"),
    ("`TypeVar` چه کاربردی دارد؟", "What is `TypeVar` used for?", "Expressing relationships between generic types", "Creating environment variables", "Catching exceptions", "Declaring SQL columns", 3, "typing"),
    ("چرا `Decimal('0.1')` از `Decimal(0.1)` دقیق‌تر است؟", "Why is `Decimal('0.1')` preferable to `Decimal(0.1)`?", "The string avoids importing binary-float approximation", "Strings use less memory", "Floats cannot be converted", "Decimal rounds every value to an integer", 4, "numeric-types"),
    ("برای نگهداری زمان مطلق قابل مقایسه چه نوع datetime مناسب است؟", "What kind of datetime should represent comparable absolute instants?", "Timezone-aware datetime", "Naive local datetime", "A formatted string only", "A date without time", 3, "datetime"),
])


PROBLEM_SOLVING = build("problem-solving", [
    ("برای یافتن دو عدد با مجموع هدف در زمان خطی چه روشی مناسب است؟", "How can two numbers summing to a target be found in linear time?", "Track complements in a hash set", "Sort with bubble sort", "Check every pair", "Use recursion without state", 3, "algorithms"),
    ("برای پردازش FIFO از کدام ساختار استفاده می‌شود؟", "Which structure supports FIFO processing?", "collections.deque", "set", "heap with negative keys", "LIFO stack", 2, "data-structures"),
    ("برای دریافت کوچک‌ترین عضو به‌صورت تکراری چه ساختاری مناسب است؟", "Which structure is suitable for repeatedly retrieving the smallest item?", "A min-heap", "An unordered list with full scan only", "A stack", "A Bloom filter", 3, "data-structures"),
    ("پیچیدگی merge sort چیست؟", "What is merge sort's time complexity?", "O(n log n)", "O(n²) always", "O(log n)", "O(1)", 2, "complexity"),
    ("برای تشخیص cycle در linked list با حافظه ثابت چه روشی مناسب است؟", "How can a linked-list cycle be detected with constant extra space?", "Floyd's slow and fast pointers", "Copy every node to a list", "Binary search", "Topological sorting", 4, "algorithms"),
    ("کدام روش shortest path برای یال‌های وزن منفی مناسب نیست؟", "Which shortest-path algorithm is unsuitable for negative edge weights?", "Dijkstra's algorithm", "Bellman-Ford", "Dynamic programming on a DAG", "Floyd-Warshall", 4, "graphs"),
    ("شرط اصلی استفاده از topological sort چیست؟", "What is required for a topological ordering?", "A directed acyclic graph", "An undirected complete graph", "Equal edge weights", "A balanced tree", 3, "graphs"),
    ("memoization چه trade-off اصلی دارد؟", "What is memoization's main trade-off?", "Uses memory to avoid repeated computation", "Uses more CPU to save disk", "Removes deterministic behavior", "Requires network access", 3, "dynamic-programming"),
    ("برای داده جریانی بسیار بزرگ چه الگویی حافظه کمتری مصرف می‌کند؟", "Which approach uses less memory for a very large stream?", "Process items incrementally", "Materialize the entire stream", "Deep-copy every item", "Store duplicate batches", 2, "streaming"),
    ("یک invariant در طراحی الگوریتم چیست؟", "What is an invariant in algorithm design?", "A property that remains true through defined steps", "A random test input", "A mutable global", "A performance benchmark only", 3, "reasoning"),
    ("برای کاهش nesting پیچیده شرط‌ها چه روشی مناسب است؟", "What helps reduce deeply nested conditionals?", "Guard clauses with clear early returns", "More global flags", "Catch every exception", "Duplicate each branch", 2, "readability"),
    ("کدام نشانه معمولاً بیانگر abstraction نامناسب است؟", "Which is a common sign of a poor abstraction?", "Many unrelated reasons for one module to change", "A focused public interface", "Explicit dependencies", "Small cohesive functions", 4, "design"),
    ("اصل single responsibility درباره چیست؟", "What does the single-responsibility principle emphasize?", "One primary reason for a component to change", "One function per repository", "No dependencies", "Only one class instance", 3, "design"),
    ("برای جایگزینی شرط‌های متعدد وابسته به نوع چه الگویی می‌تواند مناسب باشد؟", "What may replace many conditionals based on object type?", "Polymorphism or a strategy pattern", "A larger global dictionary only", "Nested try blocks", "String concatenation", 4, "design"),
    ("idempotent بودن یک عملیات یعنی چه؟", "What does it mean for an operation to be idempotent?", "Repeating it has the same intended effect as doing it once", "It always runs only once", "It cannot fail", "It returns no value", 3, "reliability"),
    ("برای retry امن عملیات خارجی چه ویژگی مهم است؟", "What is important for safely retrying an external operation?", "An idempotency key or equivalent deduplication", "An infinite timeout", "A global mutable counter", "Disabling logs", 4, "reliability"),
    ("exponential backoff چه مشکلی را کاهش می‌دهد؟", "What does exponential backoff help reduce?", "Retry storms against a failing dependency", "Database normalization", "Static type errors", "Memory fragmentation", 3, "reliability"),
    ("circuit breaker چه زمانی درخواست را متوقف می‌کند؟", "When does a circuit breaker stop forwarding requests?", "After failures cross a threshold", "Whenever latency is zero", "Only during deployment", "After every successful call", 4, "reliability"),
    ("برای رخدادهای خارج از ترتیب چه چیزی لازم است؟", "What helps handle out-of-order events?", "Versioning or monotonic sequence checks", "Assuming arrival order", "Removing timestamps", "Random retries only", 5, "distributed-systems"),
    ("race condition چه زمانی رخ می‌دهد؟", "When does a race condition occur?", "When correctness depends on uncontrolled operation ordering", "Whenever two functions exist", "Only with syntax errors", "When a query uses an index", 3, "concurrency"),
    ("برای جلوگیری از deadlock چه نظم ساده‌ای مفید است؟", "What simple discipline helps prevent deadlocks?", "Acquire shared locks in a consistent order", "Acquire locks randomly", "Never release locks", "Retry without limits", 4, "concurrency"),
    ("backpressure در pipeline چه هدفی دارد؟", "What is backpressure for in a pipeline?", "Preventing producers from overwhelming consumers", "Increasing duplicate work", "Disabling queues", "Sorting all messages", 4, "systems"),
    ("برای pagination پایدار روی داده در حال تغییر چه روشی بهتر است؟", "What is preferable for stable pagination over changing data?", "Cursor pagination with a deterministic ordering", "Offset without ordering", "Random sampling", "Client-side slicing of all rows", 4, "api-design"),
    ("برای شکستن مسئله بزرگ چه روشی علمی‌تر است؟", "What is a sound way to decompose a large problem?", "Define smaller components with explicit contracts", "Start coding every path at once", "Use shared globals", "Avoid acceptance criteria", 2, "reasoning"),
    ("اولین قدم در بهینه‌سازی performance چیست؟", "What should come first when optimizing performance?", "Measure and identify the actual bottleneck", "Add caching everywhere", "Rewrite in another language", "Remove tests", 2, "performance"),
    ("چه زمانی cache می‌تواند داده stale ایجاد کند؟", "When can a cache serve stale data?", "When invalidation does not follow source updates", "When keys are strings", "When values are small", "When compression is enabled", 3, "caching"),
])


TESTING_QUALITY = build("testing-quality", [
    ("هدف unit test چیست؟", "What is the purpose of a unit test?", "Verify a small unit in isolation", "Exercise the whole production network", "Replace type checking", "Test visual CSS only", 1, "unit-testing"),
    ("integration test چه چیزی را می‌سنجد؟", "What does an integration test verify?", "Interaction between real components", "One expression without dependencies", "Only formatting", "Compiler speed", 2, "integration-testing"),
    ("مزیت test fixture چیست؟", "What is a benefit of a test fixture?", "Repeatable setup and teardown", "Sharing production passwords", "Skipping assertions", "Disabling isolation", 2, "fixtures"),
    ("mock بیش‌ازحد چه خطری دارد؟", "What is a risk of excessive mocking?", "Tests can mirror implementation instead of behavior", "Tests become integration tests automatically", "Database constraints improve", "Coverage becomes impossible", 4, "mocking"),
    ("برای بررسی تعداد فراخوانی dependency چه ابزاری مناسب است؟", "What can verify how often a dependency was called?", "A mock or spy assertion", "A database migration", "A template filter", "A linter comment", 2, "mocking"),
    ("چه تستی boundary value را خوب پوشش می‌دهد؟", "Which test best covers a boundary?", "Values just below, at, and above the limit", "Only one average value", "A random string without assertions", "Production traffic only", 3, "test-design"),
    ("parameterized test چه مزیتی دارد؟", "What is a benefit of parameterized tests?", "Runs one behavior contract against multiple cases", "Removes all fixtures", "Guarantees 100% correctness", "Makes failures invisible", 2, "test-design"),
    ("flaky test چیست؟", "What is a flaky test?", "A test that passes or fails without relevant code changes", "A consistently failing test", "A skipped test", "A slow but deterministic test", 2, "reliability"),
    ("برای کنترل زمان در تست expiry چه روشی بهتر است؟", "How should expiry logic be tested reliably?", "Inject or freeze the clock", "Wait in real time", "Change the OS timezone randomly", "Remove the assertion", 4, "time-testing"),
    ("برای تست random behavior چه چیزی کمک می‌کند؟", "What helps test randomized behavior reproducibly?", "A controlled seed", "The global clock only", "More print statements", "An infinite loop", 3, "determinism"),
    ("coverage بالا به‌تنهایی چه چیزی را تضمین نمی‌کند؟", "What does high code coverage alone not guarantee?", "Meaningful assertions and correct behavior", "That lines executed", "A measurable percentage", "Identification of unexecuted lines", 3, "coverage"),
    ("mutation testing چه چیزی را ارزیابی می‌کند؟", "What does mutation testing assess?", "Whether tests detect deliberate code changes", "Database migration speed", "Python import order", "CSS compatibility", 5, "mutation-testing"),
    ("contract test برای چه چیزی مفید است؟", "What are contract tests useful for?", "Checking expectations between service consumers and providers", "Replacing every unit test", "Measuring disk space", "Generating secrets", 4, "contract-testing"),
    ("golden master test چه زمانی مفید است؟", "When can a golden-master test be useful?", "Characterizing legacy output before refactoring", "Validating passwords", "Testing nondeterministic timestamps unchanged", "Replacing requirements", 4, "legacy-testing"),
    ("linting چه نوع مشکل‌هایی را زود پیدا می‌کند؟", "What does linting catch early?", "Static style and probable code issues", "Runtime database deadlocks", "Network outages", "User acceptance problems", 1, "static-analysis"),
    ("type checker چه زمانی بیشترین ارزش را دارد؟", "When is a type checker most valuable?", "When interfaces carry precise type contracts", "When every value is Any", "When annotations contradict behavior", "Only after deployment", 3, "typing"),
    ("اصل DRY در تست‌ها چرا نباید افراطی اجرا شود؟", "Why should DRY not be over-applied in tests?", "Some duplication can keep scenarios explicit and readable", "Tests must never use helpers", "Every assertion must be duplicated", "Fixtures cannot be reused", 4, "test-maintainability"),
    ("یک assertion خوب چه ویژگی دارد؟", "What characterizes a good assertion?", "It checks one meaningful observable outcome", "It reproduces all implementation steps", "It catches every exception", "It has no failure message", 2, "assertions"),
    ("تست end-to-end را کجا باید متمرکز کرد؟", "Where should end-to-end tests be focused?", "Critical user journeys", "Every private helper", "All possible strings", "Only database indexes", 3, "end-to-end"),
])


DJANGO = build("django", [
    ("`get_object_or_404` چه می‌کند؟", "What does `get_object_or_404` do?", "Returns an object or raises Http404", "Returns None for every miss", "Creates a model", "Redirects to login automatically", 1, "views"),
    ("کاربرد `login_required` چیست؟", "What does `login_required` enforce?", "Authenticated access to a view", "Staff access only", "CSRF exemption", "Database locking", 1, "authentication"),
    ("در CBV، `dispatch` چه نقشی دارد؟", "What is the role of `dispatch` in a class-based view?", "Routes the request to the HTTP-method handler", "Renders CSS", "Creates migrations", "Validates model constraints only", 3, "class-based-views"),
    ("چرا override کردن `form_valid` مفید است؟", "Why override `form_valid` in a form view?", "Add behavior after valid form processing", "Disable all validation", "Change URL routing globally", "Create static files", 3, "forms"),
    ("`clean_<fieldname>` در Form برای چیست؟", "What is `clean_<fieldname>` used for in a Form?", "Field-specific validation and normalization", "Rendering a template", "Opening a transaction", "Loading middleware", 2, "forms"),
    ("اعتبارسنجی وابسته به چند فیلد کجا انجام می‌شود؟", "Where should cross-field form validation live?", "Form.clean", "A CSS selector", "settings.py only", "The URL converter", 3, "forms"),
    ("چرا `AUTH_USER_MODEL` در ForeignKey توصیه می‌شود؟", "Why use `AUTH_USER_MODEL` in foreign keys?", "It supports the configured user model", "It creates a superuser", "It hashes every field", "It disables migrations", 2, "user-model"),
    ("برای permission سطح object چه چیزی لازم است؟", "What is needed for object-level authorization?", "A server-side check against the specific object", "Hiding a button only", "A public UUID alone", "Template translation", 4, "authorization"),
    ("context processor چه چیزی فراهم می‌کند؟", "What does a context processor provide?", "Common context data for templates", "Database indexes", "Background workers", "URL redirects only", 2, "templates"),
    ("template autoescape عمدتاً از چه چیزی جلوگیری می‌کند؟", "What does template autoescaping primarily mitigate?", "HTML injection and many XSS cases", "CSRF", "Deadlocks", "DNS spoofing", 2, "templates"),
    ("cache per-view چه چیزی را cache می‌کند؟", "What does per-view caching store?", "The generated response for a cache key", "Only model definitions", "User passwords", "Migration files", 2, "caching"),
    ("چرا cache key باید زبان را در نظر بگیرد؟", "Why should a cache key account for language?", "To avoid serving content in the wrong locale", "To enable SQL joins", "To hash passwords", "To compress images", 3, "caching"),
    ("`on_commit` چه زمانی callback را اجرا می‌کند؟", "When does `transaction.on_commit` run a callback?", "After the surrounding transaction commits successfully", "Before validation", "After every query", "Only on rollback", 4, "transactions"),
    ("چرا ارسال ایمیل داخل transaction می‌تواند بد باشد؟", "Why can sending email inside a transaction be problematic?", "The external side effect may happen before a later rollback", "Email changes isolation level", "SMTP creates migrations", "Transactions cannot contain functions", 4, "transactions"),
    ("`select_for_update` چه می‌کند؟", "What does `select_for_update` do?", "Locks selected rows until the transaction ends", "Adds a permanent index", "Caches query results", "Encrypts selected columns", 4, "concurrency"),
    ("برای افزایش counter بدون lost update چه روشی مناسب است؟", "How should a counter be incremented to avoid lost updates?", "Use an F expression in an update", "Read, add in Python, and save without locking", "Store it in a template", "Use a GET request", 4, "concurrency"),
    ("custom manager چه کاربردی دارد؟", "What is a custom model manager useful for?", "Encapsulating reusable table-level query behavior", "Rendering forms only", "Changing HTTP headers", "Serving static files", 3, "models"),
    ("custom QuerySet چه مزیتی دارد؟", "What is a benefit of a custom QuerySet?", "Chainable domain-specific query methods", "Automatic deployment", "Client-side validation", "Background scheduling", 3, "models"),
    ("`bulk_create` چه محدودیتی رایج دارد؟", "What is a common consideration with `bulk_create`?", "It bypasses each model instance's save method", "It performs one query per row always", "It cannot insert models", "It automatically sends every signal", 4, "orm"),
    ("چرا signal برای منطق اصلی کسب‌وکار خطرناک است؟", "Why can signals be risky for core business workflows?", "They hide control flow and transaction boundaries", "They cannot access models", "They always run remotely", "They disable tests", 4, "architecture"),
    ("برای job طولانی بعد از request چه روشی مناسب است؟", "How should a long-running job be handled after a request?", "Queue it for a background worker", "Block the request indefinitely", "Run it in a template tag", "Store code in a cookie", 3, "background-jobs"),
    ("idempotency در task پس‌زمینه چرا مهم است؟", "Why is idempotency important for background tasks?", "Workers may retry a task after partial execution", "Tasks never fail", "Queues guarantee exactly once", "It removes the need for logs", 4, "background-jobs"),
    ("برای API list بزرگ چه چیزی ضروری است؟", "What is essential for a large API list endpoint?", "Pagination with bounded page size", "Returning every row", "Disabling authorization", "Rendering admin HTML", 2, "api-design"),
    ("HTTP 403 چه معنایی دارد؟", "What does HTTP 403 mean?", "The request is understood but not authorized", "The resource was created", "The server timed out", "The URL moved permanently", 2, "http"),
    ("چه زمانی `StreamingHttpResponse` مناسب است؟", "When is `StreamingHttpResponse` appropriate?", "When producing a large response incrementally", "For every small JSON response", "To make ORM transactions atomic", "To validate forms", 4, "responses"),
])


DATABASE = build("database", [
    ("`EXPLAIN ANALYZE` چه اطلاعاتی اضافه می‌کند؟", "What does `EXPLAIN ANALYZE` add?", "Actual execution timing and row counts", "Automatic index creation", "A database backup", "Password rotation", 4, "query-plans"),
    ("index مرکب `(a, b)` معمولاً برای کدام filter مفید است؟", "A composite index on `(a, b)` commonly helps which filter?", "A filter beginning with column a", "Only a filter on b in every database", "A filter on unrelated c", "No filters", 3, "indexes"),
    ("partial index چه مزیتی دارد؟", "What is a benefit of a partial index?", "Indexes only rows matching a predicate", "Indexes every table", "Removes constraints", "Stores full backups", 4, "indexes"),
    ("هزینه index اضافی چیست؟", "What is a cost of an additional index?", "More storage and write maintenance", "Slower reads in every case", "Loss of transactions", "No foreign keys", 2, "indexes"),
    ("foreign key چه چیزی را تضمین می‌کند؟", "What does a foreign key enforce?", "Referential integrity", "Uniqueness of every column", "Query ordering", "Encryption", 2, "constraints"),
    ("check constraint برای چیست؟", "What is a check constraint for?", "Enforcing a row-level predicate in the database", "Caching queries", "Creating users", "Serving media", 2, "constraints"),
    ("transaction isolation چه چیزی را کنترل می‌کند؟", "What does transaction isolation control?", "How concurrent transactions observe each other's changes", "Python import order", "HTTP compression", "Template escaping", 3, "transactions"),
    ("در read committed یک query تکراری ممکن است چه ببیند؟", "Under read committed, what may a repeated query observe?", "Rows committed by another transaction between statements", "Uncommitted dirty rows always", "No database rows", "Only cached templates", 4, "isolation"),
    ("optimistic locking معمولاً بر چه چیزی تکیه دارد؟", "What does optimistic locking commonly rely on?", "A version value checked during update", "A permanent table lock", "No constraints", "Browser local storage", 4, "concurrency"),
    ("deadlock را database معمولاً چگونه حل می‌کند؟", "How does a database normally resolve a deadlock?", "Aborts one transaction so it can be retried", "Commits every transaction", "Deletes the locked rows", "Disables indexes", 4, "concurrency"),
    ("N+1 query چگونه تشخیص داده می‌شود؟", "How can an N+1 query issue be identified?", "Inspect query count and repeated similar queries", "Count template lines", "Disable logging", "Check DNS", 3, "orm-performance"),
    ("`annotate` در Django ORM چه می‌کند؟", "What does `annotate` do in Django ORM?", "Adds calculated values to each result row", "Mutates every database row", "Creates a migration", "Loads static files", 3, "orm"),
    ("`aggregate` چه نوع نتیجه‌ای می‌دهد؟", "What kind of result does `aggregate` return?", "A summary dictionary for the queryset", "A model instance per row", "An HTTP response", "A migration graph", 2, "orm"),
    ("چرا `exists()` برای بررسی وجود مناسب است؟", "Why use `exists()` to check for rows?", "It can avoid loading full model rows", "It locks the entire table", "It always caches objects", "It sorts results", 2, "orm-performance"),
    ("`iterator()` برای queryset بزرگ چه فایده‌ای دارد؟", "Why use `iterator()` for a large queryset?", "Reduces ORM result caching in memory", "Adds pagination automatically", "Creates indexes", "Validates forms", 3, "orm-performance"),
    ("برای update گروهی چه روشی مناسب است؟", "What is suitable for updating many matching rows?", "QuerySet.update", "Calling save through a template", "One HTTP request per field", "Changing a migration history file", 2, "orm"),
    ("مشکل offset pagination در صفحات عمیق چیست؟", "What is a problem with deep offset pagination?", "The database may scan and discard many rows", "It prevents sorting", "It removes authorization", "It changes row values", 4, "pagination"),
    ("connection pooling چه مزیتی دارد؟", "What is a benefit of connection pooling?", "Reuses database connections and limits connection churn", "Removes transactions", "Caches every query result", "Replaces backups", 3, "connections"),
    ("backup بدون restore test چه ضعفی دارد؟", "Why is a backup insufficient without restore testing?", "Recoverability has not been verified", "It cannot be encrypted", "It creates indexes", "It changes isolation", 3, "recovery"),
    ("برای migration بزرگ production چه رویکردی امن‌تر است؟", "What is safer for a large production migration?", "Use staged, backward-compatible changes", "Lock and rewrite everything in one request", "Delete migration history", "Disable backups", 5, "migrations"),
])


SECURITY = build("security", [
    ("IDOR چیست؟", "What is IDOR?", "Accessing another object's data through missing authorization checks", "A database index", "A slow static file", "A DNS record", 3, "authorization"),
    ("برای جلوگیری از IDOR چه کاری لازم است؟", "How should IDOR be prevented?", "Authorize access to the specific requested object", "Hide numeric IDs only", "Use JavaScript validation", "Rename the URL", 4, "authorization"),
    ("XSS stored چه زمانی رخ می‌دهد؟", "When does stored XSS occur?", "Malicious content is persisted and later rendered unsafely", "A query has no index", "A CSRF token expires", "A worker retries", 3, "xss"),
    ("استفاده از `mark_safe` روی ورودی کاربر چه خطری دارد؟", "What is the risk of using `mark_safe` on user input?", "It can bypass escaping and enable XSS", "It causes a deadlock", "It rotates secrets", "It disables cookies", 4, "xss"),
    ("SQL injection با Django ORM معمولاً چگونه کاهش می‌یابد؟", "How does Django ORM usually mitigate SQL injection?", "By parameterizing query values", "By hiding table names", "By using GET only", "By disabling indexes", 2, "sql-injection"),
    ("در raw SQL چه چیزی ضروری است؟", "What is essential when using raw SQL?", "Pass untrusted values as query parameters", "Interpolate input with f-strings", "Disable escaping", "Expose query errors", 4, "sql-injection"),
    ("SSRF چه چیزی را هدف می‌گیرد؟", "What does SSRF target?", "Server-side requests to attacker-chosen destinations", "Browser CSS", "Password length only", "Database sorting", 4, "ssrf"),
    ("برای کاهش SSRF چه روشی مناسب است؟", "What helps mitigate SSRF?", "Allowlist destinations and block private-network resolution", "Follow every redirect", "Accept every URL scheme", "Disable timeouts", 5, "ssrf"),
    ("آپلود فایل امن به چه چیزی نیاز دارد؟", "What is needed for safer file uploads?", "Validate content, size, name, and storage behavior", "Trust the filename extension", "Execute uploaded files", "Store them in templates", 3, "file-uploads"),
    ("چرا فایل کاربر نباید executable سرو شود؟", "Why should user uploads not be served as executable content?", "Uploaded content could run attacker-controlled code", "It slows SQL", "It changes timezone", "It prevents caching", 4, "file-uploads"),
    ("rate limiting چه حمله‌ای را به‌تنهایی کامل حل نمی‌کند؟", "What does rate limiting not fully solve by itself?", "Distributed abuse across many identities", "A single client's request burst", "Accidental repeated clicks", "Password retry speed", 4, "abuse-prevention"),
    ("password باید چگونه ذخیره شود؟", "How should passwords be stored?", "With a slow salted password hash", "With reversible encryption only", "As plaintext", "With a fast unsalted hash", 2, "passwords"),
    ("MFA چه ریسکی را کاهش می‌دهد؟", "What risk does MFA reduce?", "Account takeover from a stolen password", "SQL query latency", "Static file cache misses", "Database normalization", 2, "authentication"),
    ("session fixation چگونه کاهش می‌یابد؟", "What helps prevent session fixation?", "Rotate the session identifier after authentication", "Reuse one session forever", "Put session IDs in public URLs", "Disable logout", 4, "sessions"),
    ("cookie احراز هویت چه flagهایی باید داشته باشد؟", "Which flags are important for an authentication cookie?", "Secure, HttpOnly, and an appropriate SameSite", "Public and cacheable", "Executable", "Cross-site without restriction", 3, "cookies"),
    ("CSP چه کمکی می‌کند؟", "How does a Content Security Policy help?", "Restricts allowed content sources and reduces XSS impact", "Prevents every CSRF automatically", "Encrypts database rows", "Creates backups", 4, "browser-security"),
    ("چرا جزئیات stack trace نباید عمومی شود؟", "Why should stack traces not be public?", "They may reveal sensitive internals and data", "They prevent migrations", "They slow CSS", "They invalidate TLS", 2, "information-disclosure"),
    ("اصل least privilege چیست؟", "What is the principle of least privilege?", "Grant only the permissions required for the task", "Give every service admin access", "Share one root account", "Disable audit logs", 3, "authorization"),
])


DEPLOYMENT = build("deployment", [
    ("Gunicorn در معماری Django چه نقشی دارد؟", "What role does Gunicorn play for Django?", "Runs WSGI application workers", "Serves as a database", "Builds CSS", "Provides DNS", 2, "application-server"),
    ("Nginx معمولاً جلوی Django چه کاری می‌کند؟", "What does Nginx commonly do in front of Django?", "Reverse proxying and serving static assets", "Runs migrations per request", "Stores Python objects", "Creates users", 2, "reverse-proxy"),
    ("چرا `ALLOWED_HOSTS` باید محدود باشد؟", "Why should `ALLOWED_HOSTS` be restricted?", "To reject unexpected Host headers", "To enable DEBUG", "To create TLS certificates", "To speed Python loops", 3, "configuration"),
    ("readiness check با liveness check چه تفاوتی دارد؟", "How does a readiness check differ from a liveness check?", "Readiness says whether traffic can be accepted", "Readiness always restarts the service", "Liveness checks marketing pages", "There is no distinction", 3, "health-checks"),
    ("چرا liveness نباید به dependency ناپایدار حساس باشد؟", "Why should liveness avoid fragile dependency checks?", "It can cause unnecessary restart loops", "It prevents logs", "It disables TLS", "It changes migrations", 4, "health-checks"),
    ("graceful shutdown چه هدفی دارد؟", "What is the purpose of graceful shutdown?", "Stop new work and finish or safely release in-flight work", "Kill storage immediately", "Delete queues", "Disable monitoring", 3, "reliability"),
    ("zero-downtime deployment به چه چیزی نیاز دارد؟", "What supports zero-downtime deployment?", "Overlapping healthy instances and compatible changes", "One instance stopped before build", "Destructive schema changes first", "No health checks", 4, "deployment-strategy"),
    ("blue-green deployment چه مزیتی دارد؟", "What is a benefit of blue-green deployment?", "Traffic can switch between two complete environments", "It removes database backups", "It prevents all bugs", "It needs no monitoring", 4, "deployment-strategy"),
    ("rollback کد با migration ناسازگار چه خطری دارد؟", "What is risky about rolling back code after an incompatible migration?", "Old code may not understand the new schema", "Static files become encrypted", "DNS always fails", "Logs disappear automatically", 5, "migrations"),
    ("ترتیب expand-and-contract برای schema چیست؟", "What is the expand-and-contract schema pattern?", "Add compatible schema, migrate usage, then remove old schema", "Drop old columns first", "Disable transactions", "Copy production to Git", 5, "migrations"),
    ("۱۲-factor app تنظیمات را کجا نگه می‌دارد؟", "Where does a twelve-factor app keep deploy-specific configuration?", "Environment-backed configuration", "Hard-coded source constants", "Public templates", "User cookies", 2, "configuration"),
    ("structured logging چه مزیتی دارد؟", "What is a benefit of structured logging?", "Logs can be searched and aggregated by fields", "It hides every error", "It replaces metrics", "It prevents retries", 3, "observability"),
    ("correlation ID برای چیست؟", "What is a correlation ID used for?", "Tracing one request across services and logs", "Encrypting passwords", "Creating indexes", "Selecting language", 3, "observability"),
    ("metric با log چه تفاوتی دارد؟", "How does a metric differ from a log?", "A metric is an aggregated numeric signal over time", "A metric is always a stack trace", "Logs cannot contain timestamps", "There is no difference", 2, "observability"),
    ("alert خوب بر چه چیزی متمرکز است؟", "What should a useful alert focus on?", "Actionable user-impacting symptoms", "Every debug message", "Normal CPU variation", "Successful requests only", 3, "alerting"),
    ("RPO چه چیزی را بیان می‌کند؟", "What does RPO describe?", "Acceptable amount of data loss measured in time", "Maximum request latency", "Required CPU count", "Password rotation interval", 4, "disaster-recovery"),
    ("RTO چه چیزی را بیان می‌کند؟", "What does RTO describe?", "Target time to restore service", "Database row count", "TLS key size", "Test coverage", 4, "disaster-recovery"),
])


ADDITIONAL_QUESTIONS = (
    PYTHON_CORE + PROBLEM_SOLVING + TESTING_QUALITY + DJANGO + DATABASE + SECURITY + DEPLOYMENT
)
