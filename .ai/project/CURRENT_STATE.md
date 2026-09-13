# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** V2.1-B2 second corrective — the `DemoSelection`
  lookup inside `leads.demo_handoff.consume_pending_demo_selection`
  gained a `try`/`except` in the first corrective phase (`2cd1032`), but
  that alone was not enough: `2cd1032` is now known to have shipped
  `PARTIAL`. Under `ATOMIC_REQUESTS=True` (production), a *genuine*
  PostgreSQL error inside that lookup query aborts the underlying
  database transaction at the server level — merely catching the Python
  exception does not undo that. The lookup was not wrapped in its own
  `transaction.atomic()`, so nothing ever issued the `ROLLBACK TO
  SAVEPOINT` needed to recover; the *outer* request transaction
  (login/registration) was left needing a rollback, and the very next
  query on that connection — including, empirically, a request as basic
  as `login()`'s own follow-up work — would fail with
  `django.db.utils.InternalError: current transaction is aborted,
  commands ignored until end of transaction block`. This was reproduced
  before the fix (temporarily reverting the fix and re-running the new
  test below fails exactly this way) and is now fixed and verified — see
  "V2.1-B2 second corrective" entries below. Status: `VERIFIED` (local).
- **Last verified phase (code):** V2.1-B2 second corrective, on top of
  the V2.1-B2 first corrective phase (`2cd1032`), V2.1-B2 (`757f7a4`),
  the V2.1-B1 second corrective phase, the V2.1-B1 first corrective phase
  (`0e1a208`), V2.1-B1 (`537c9a2`), the V2.1-A corrective phase, and
  `08bd910`.
- **V2.1-B2 first corrective — historical recap (superseded as the
  "current phase"; kept for reference):** `757f7a4` shipped `PARTIAL`:
  (1) in `leads/signals.py`, the pending marker was popped before
  fetching the `DemoSelection` row, but that fetch sat *outside* any
  `try`/`except` at all — a `DatabaseError`/`OperationalError` there
  would have propagated straight through `user_logged_in.send()` and
  `django.contrib.auth.login()` into whatever view called it, turning a
  successful login or registration into a 500 error; (2) the phase's own
  report claimed a transient failure's marker "is retried on the
  customer's next authenticated request," but no such retry path
  actually existed anywhere in the code. Both were fixed in `2cd1032`:
  `leads.demo_handoff.consume_pending_demo_selection` became the single
  safe orchestration (pop → staff-check → fetch-in-a-`try` → attach-in-a-
  `try`), and `leads.demo_handoff.maybe_retry_pending_demo_selection` was
  added, wired into `LeadCreateView._resolved_demo_selection()` only when
  there is no explicit `?demo=`. **However**, the fetch's `try`/`except`
  added in `2cd1032` did not itself wrap the query in a
  `transaction.atomic()` — see "Current phase" above for why that still
  left a real gap under PostgreSQL, closed in this second corrective
  phase. `2cd1032`'s own `RealTransactionErrorRecoveryTests` (PostgreSQL,
  forcing a real `SELECT 1/0`) only ever exercised the *attach* step
  (which already had its own internal `transaction.atomic()` inside
  `ensure_active_draft_with_demo_snapshot`) — it did not, and could not,
  say anything about the separate, unwrapped lookup query, which is
  exactly the gap this second corrective phase closes and adds real
  PostgreSQL evidence for.
- **V2.1-B2 — historical recap (superseded as the "current phase"; kept
  for reference):** the first real wiring of `FormDraft` into a live
  path: a visitor's demo selection survives the login/register
  session-key rotation and lands as a safe snapshot on the newly
  authenticated (non-staff) customer's `FormDraft`, and an
  already-authenticated non-staff customer visiting the contact page with
  a valid demo link gets the same sync immediately. No auto-save
  endpoint, no restore/delete UI, no dashboard, and no `Lead`-submission
  change in that phase — see "V2.1-B2" entries below for what it built.
- **V2.1-B1 second corrective — historical recap (superseded as the
  "current phase"; kept for reference):** lifecycle and snapshot
  hardening on `FormDraft`'s service layer, one step further than the
  first corrective phase (`0e1a208`). Four real defects were found and
  fixed: (1) `attach_demo_snapshot`/`clear_demo_snapshot` did not extend
  `expires_at`, unlike every other draft-touching operation; (2) a
  `DraftValidationError` raised for "no active draft" could roll back an
  expired-draft status transition that had just happened inside the same
  `transaction.atomic()` block, since an exception propagating out of
  `atomic()` undoes everything written inside it — including a write that
  should have survived; (3) `attach_demo_snapshot` trusted the caller's
  in-memory `DemoSelection` instance rather than re-reading it from the
  database, so a locally mutated (never saved) instance, or one whose row
  had since been deleted, could still reach the snapshot builder; (4)
  snapshot validation only checked the key *set*, not each value's
  type/length, so a malformed `template_title_fa`/`brand`/`features_fa`
  etc. of the wrong type, unbounded length, or mismatched feature-list
  counts could still be written. All four were fixed and verified — see
  "V2.1-B1 second corrective" entries below.
- **V2.1-A corrective phase — historical status recap (superseded by
  later phases; kept for reference only, not the current phase's
  status):** `08bd910` was initially `VERIFIED` for
  correctness but is now known to have shipped `PARTIAL`, in the same
  class of "correct in outcome, wrong in cost or atomicity" already seen
  once before in that same phase (the `login()` `flush()`-path bug). Two
  real defects were found and are now fixed:
  1. **P1 — every authenticated customer request paid for a write lock.**
     `SingleSessionMiddleware._enforce_current_session` unconditionally
     entered `transaction.atomic()` and ran `select_for_update()` on both
     `User` and (via `get_or_create`) `ActiveSession` on *every* request,
     not just a mismatch. That serialized all of one customer's parallel
     requests against each other — exam autosave, dashboard polling,
     concurrent tabs — for no reason, since the overwhelmingly common case
     is simply confirming a session already owns its own pointer. **Fixed**
     by splitting into a lock-free fast path (one read-only
     `ActiveSession.objects.filter(user_id=...).values_list("session_key",
     flat=True).first()`, no transaction) that returns immediately on a
     match, and a slow path (only entered on "no ActiveSession yet" or a
     mismatch) that locks *only* `User` via `select_for_update()` and
     re-checks the real, current `ActiveSession.session_key` before acting
     — a pointer that changed between the fast-path read and acquiring the
     lock is picked up correctly and never causes a wrongful logout of the
     session that actually owns it.
  2. **P2 — non-atomic courtesy-marker consumption.**
     `_maybe_show_invalidated_message` did `cache.get()` then a separate
     `cache.delete()`; two concurrent requests from the same now-stale
     browser could both observe the marker before either deleted it,
     showing the one-time message twice. **Fixed** by consuming the marker
     with a single `cache.delete(marker_key)` call and using its boolean
     return value directly as the "did this request win the race to show
     the message" signal — confirmed (by reading the installed Django
     version's source, not just its docs) that all three cache backends
     this project configures (`LocMemCache` for dev/CI, `FileBasedCache`
     and `RedisCache` for production) return `True` only for the one
     caller that actually removed the key, making this safe without any
     extra locking of our own.
  Neither defect was a security hole — the *outcome* (correct session
  invalidation) was always right — but the performance cost of (1) and the
  duplicate-message possibility of (2) both needed a real fix, not just a
  note. A documented, accepted limitation remains and is unrelated to
  either fix: a request from the soon-to-be-superseded session that was
  already in flight at the exact instant a new login elsewhere changes the
  pointer cannot be retroactively cancelled — only that session's *next*
  request is guaranteed to see the mismatch.
- **Git boundary (historical, as of the V2.1-A corrective commit
  `7459651` — see the accurate, up-to-date git boundary near the end of
  this file for the real current count):** `main` was ten commits ahead
  of `origin/main` at that point (`06812d2`, `dc68011`, the "reliable
  hand-off" phase commit, `af6e0ac`, `fbe3320`, `777acf9`, `b3952a4`,
  `a4cb60b`, `08bd910`, and `7459651`). `08bd910` was not amended — that
  was a separate commit on top of it.
- **Active delegated work:** none.
- **Known blockers:** none. No model or migration change was needed for
  either fix (both are logic-only, inside `accounts/middleware.py`); the
  existing `accounts/migrations/0004_activesession.py` from `08bd910` is
  untouched. Push, deploy, and any migration against a
  permanent database (local dev `db.sqlite3` or production) remain outside
  this phase's authorization — that migration was never applied to the
  local dev database in this phase either; it was only ever applied
  automatically to Django's own disposable `test_...`-prefixed databases
  during test runs (SQLite in-memory for the default suite, a temporary
  `test_arvion_ci_local` PostgreSQL database for the race test — both
  created and destroyed by the test runner itself, never the permanent
  `arvion_ci_local` database that seeded them).
- **V2.1-A — what was built:** `accounts.ActiveSession` (`user`
  OneToOneField, `session_key`, `created_at`/`updated_at`; deliberately no
  admin registration, and `__str__`/`__repr__` show only `user_id`, never
  `session_key`). `accounts/signals.py`: `enforce_single_session_on_login`
  (on `user_logged_in`, `dispatch_uid="accounts.enforce_single_session_on_login"`)
  and `release_active_session_on_logout` (on `user_logged_out`,
  `dispatch_uid="accounts.release_active_session_on_logout"`) — both
  no-op for staff/superusers and when `settings.SINGLE_SESSION_ENFORCED`
  is `False` (new setting, default `"1"`/on, an env-var escape hatch
  needing no redeploy). `accounts/middleware.py`:
  `SingleSessionMiddleware`, added to `MIDDLEWARE` right after
  `MessageMiddleware` (so `messages.info()` is usable) — enforces the
  legacy-rollout claim race on every authenticated non-staff request
  (fail-closed: mismatched session → immediate `logout()`, independent of
  any messaging) and shows the one-time bilingual courtesy notice on a
  stale session's next anonymous request. `accounts/apps.py`:
  `AccountsConfig.ready()` imports `signals`, matching the existing
  `management_portal` pattern; idempotency comes from Django's own
  `dispatch_uid` deduplication (verified — see tests).
  `accounts/migrations/0004_activesession.py`: one additive
  `CreateModel`, no data migration, trivial rollback
  (`migrate accounts 0003_...`).
- **V2.1-A — a real bug found and fixed during this phase (not merely
  reasoned about — reproduced, diagnosed with temporary debug tracing,
  fixed, and the fix re-verified):** `django.contrib.auth.login()` takes
  one of two internal paths depending on the session's prior state — a
  fresh or same-user session gets `cycle_key()`, which mints a new,
  already-persisted `session_key` immediately; but a session that was
  previously authenticated as a *different* user gets `flush()` instead,
  which clears `session_key` to `None` without creating a replacement on
  the spot (a new key is only minted later, whenever something next calls
  `.save()` — in a real request that is `SessionMiddleware`'s
  `process_response()`, which runs *after* the view, i.e. *after*
  `user_logged_in` has already fired). `enforce_single_session_on_login`
  originally bailed out on seeing an empty `session_key`, so it silently
  did nothing for this path — meaning switching to a different account on
  a browser that was already logged in as someone else (e.g. a real
  staff-then-customer or customer-then-customer handoff on one machine)
  would never have been registered into `ActiveSession` at all. Caught by
  a pre-existing, unrelated test
  (`assessments.tests.AssessmentCommerceTests.test_card_transfer_waits_for_admin_then_grants_access`,
  which logs in as a customer, then an admin, then the same customer
  again on one `Client`) failing with a 302 instead of 200. Fixed by
  having the receiver force `request.session.save()` itself when the key
  is still empty at that point, so a real key always exists before it is
  read — verified by re-running that exact test (now passing) plus the
  full 554-test project suite (all green) after the fix.
- **V2.1-A — test level:** `accounts.tests.SingleSessionTests` (16 tests,
  all passing): second login invalidates the first session's `Session` row
  outright; the first session becomes anonymous (redirected to login) on
  its next request; `ActiveSession` points only at the second session;
  logging out a stale/old session never removes a newer session's pointer
  (exact `(user, session_key)` match required); logging out the active
  session clears its own pointer; staff and superusers may hold multiple
  concurrent sessions with no `ActiveSession` row created at all; a
  "legacy" session (constructed directly via `SessionStore`, bypassing
  `login()` entirely, to simulate one that pre-dates this feature) claims
  the account on its first request; two such legacy sessions racing
  converge to exactly one winner, the loser's `Session` row deleted; the
  courtesy message appears exactly once, in the correct language (both fa
  via `/fa/...` and en via `/en/...` — confirmed the `?lang=` query
  param alone does *not* set `request.LANGUAGE_CODE`, only the
  `i18n_patterns` URL prefix does, and fixed a translation-state leak
  between test methods the same way `ManagementDashboardTests` already
  does elsewhere in this project); the raw session key never appears in
  the message text, the cache marker string, or the model's `str()`/
  `repr()`; disabling `SINGLE_SESSION_ENFORCED` restores multi-session
  behaviour; two different accounts' `ActiveSession` rows are fully
  independent; registration, normal login, and (by the full-suite run)
  phone/email verification flows all still work and correctly claim an
  `ActiveSession`. Plus `accounts.tests.SingleSessionPostgresRaceTests`
  (1 test, `@skipUnless(connection.vendor == "postgresql", ...)` —
  auto-skipped on the local SQLite dev database, but this project's own
  GitHub Actions CI runs on PostgreSQL per `arvion/settings/ci.py`, so it
  will execute for real there on every future run, not just this one).
  `accounts` + `core` targeted suite: 141 tests, all passing (1 skip).
  Full project suite (all apps): 554 tests, all passing (2 skips). `manage.py
  check` (0 issues), `makemigrations --check --dry-run` ("No changes
  detected" — the one new migration this phase added is already fully
  captured), and `git diff --check` (clean) all passed.
- **V2.1-A — PostgreSQL concurrency evidence:** a local, isolated
  PostgreSQL 16 server was already running on this machine with an empty,
  purpose-named `arvion_ci_local` database. Ran
  `DJANGO_SETTINGS_MODULE=arvion.settings.ci DATABASE_URL=postgresql://rwin@localhost:5432/arvion_ci_local
  python manage.py test accounts.tests.SingleSessionPostgresRaceTests`,
  which spins up two real Python threads, each with its own database
  connection, synchronized on a `threading.Barrier` so both call
  `django.contrib.auth.login()` for the same user as close to
  simultaneously as the interpreter allows. Django's test runner created
  and destroyed its own temporary `test_arvion_ci_local` database for
  this — the permanent `arvion_ci_local` database was never migrated or
  written to directly. Result: exactly one `ActiveSession` row, exactly
  one surviving `Session` row, matching keys, zero exceptions from either
  thread — genuine proof that `select_for_update()` correctly serializes
  the two concurrent *new-login* claims on a real row-locking engine,
  re-confirmed after the `flush()` bug fix above. This test alone did
  **not** prove anything about two pre-existing (*legacy*) sessions racing
  through the middleware's own claim path — that gap is closed in the
  corrective phase below.
- **V2.1-A corrective phase — what changed:** `accounts/middleware.py`
  only (no model, migration, or `accounts/signals.py` change was needed).
  `_enforce_current_session` now does a lock-free fast-path SELECT first
  and only takes the `transaction.atomic()`/`select_for_update(User)` slow
  path on a miss, re-checking the real pointer before acting (see
  "Status" above for the exact mechanism). `_maybe_show_invalidated_message`
  now consumes the courtesy marker with one atomic `cache.delete()` call
  instead of a `get()`-then-`delete()` pair.
- **V2.1-A corrective phase — test level:** 6 new tests in
  `accounts.tests.SingleSessionTests` (23 total in that class, all
  passing): the matching-session fast path is exactly one read-only query
  against `accounts_activesession` and never calls `select_for_update`
  (verified by mocking `QuerySet.select_for_update` and asserting
  `assert_not_called()`, plus `CaptureQueriesContext` filtered to that
  table); a forced fast-path mismatch does enter the locked slow path
  (verified by mocking the fast-path read wrong and asserting
  `select_for_update` **was** called); a pointer that already matches by
  the time the lock is acquired — simulating a stale fast-path read racing
  a real, current, correct `ActiveSession` row — is never wrongly logged
  out; two requests racing to consume the same courtesy marker produce the
  message at most once, both through a real (sequential, single-process)
  HTTP-level check and a direct 4-thread proof that `cache.delete()` on
  the same key returns `True` for exactly one caller. Plus 1 new test in
  `accounts.tests.SingleSessionPostgresRaceTests`:
  `test_two_legacy_sessions_race_to_claim_the_active_session` — two
  sessions built to bypass `login()` entirely (mimicking sessions that
  pre-date this feature, exactly like `SingleSessionTests`'
  `_legacy_session_key` helper, now shared as a module-level
  `make_legacy_session_key`), racing via `threading.Barrier` with two
  independent DB connections against real PostgreSQL. Result across 6 runs
  (1 during the main suite + 5 repeats to rule out a lucky pass): exactly
  one `ActiveSession` row every time, exactly one `200` and one `302`
  response, the loser's `Session` row deleted, both threads observed
  finished (not hung) via `Thread.is_alive()`, zero exceptions in any run
  — this is the specific evidence that was missing before this phase, and
  is why the "legacy sessions race-safely converge" claim (made in
  `08bd910` and in the V2.1 design) is now backed by a real PostgreSQL
  test rather than only the SQLite-sequential test that existed before.
  `accounts` + `core` targeted suite: 147 tests, all passing (2 skips —
  both PostgreSQL-only tests, correctly auto-skipped on SQLite). Full
  project suite: 560 tests, all passing (3 skips). `manage.py check`
  (0 issues), `makemigrations --check --dry-run` ("No changes detected" —
  confirmed no schema change was needed for either fix), and
  `git diff --check` (clean) all passed.
- **V2.1 findings — current system (read-only investigation):**
  `accounts.User` (`accounts/models.py`) has no session-tracking field at
  all. `login()` is called directly from four separate places
  (`RegisterView.form_valid`, `PhoneVerificationView.form_valid`,
  `verify_email`, and implicitly inside `AccountLoginView`'s stock
  `LoginView.form_valid`) — no single call site to patch; Django's own
  `user_logged_in`/`user_logged_out` signals (which fire from every one of
  these paths automatically) are the correct integration point instead of
  touching each view. No `AUTHENTICATION_BACKENDS` or `SESSION_ENGINE`
  override exists anywhere in `arvion/settings/` — sessions use Django's
  default `django.contrib.sessions.backends.db` (the `django_session`
  table via `django.contrib.sessions.models.Session`), so deleting a
  session row is a first-class, supported operation, not a workaround.
  `MIDDLEWARE` (`arvion/settings/base.py`) already has a precedent for a
  small, single-purpose custom middleware right after
  `AuthenticationMiddleware` (`core.middleware.AdminPersianLocaleMiddleware`)
  — the natural slot for a future courtesy "you were signed out elsewhere"
  middleware. `leads.Lead` has no `user` FK at all (fully anonymous by
  design); the only existing bridge from `accounts.User` to the
  Customer/Lead world is `management_portal.CustomerContact.user`,
  established only *after* a Lead is submitted — the new Draft concept
  should not require touching `Lead` at all. `projects.DemoSelection`
  confirmed session-bound only (`public_token` + `session_key`, no user
  field, `leads/views/contact.py:_session_demo_selection` resolves it by
  exact `session_key` match against `request.session.session_key`) — and
  a real, previously-latent interaction was found during this
  investigation: `django.contrib.auth.login()` calls
  `request.session.cycle_key()` to prevent session fixation, which
  silently orphans any `DemoSelection` tied to the pre-login session_key
  the instant a visitor logs in mid-flow — today this just makes the demo
  card quietly disappear (existing neutral-notice behaviour, not a
  security bug); the V2.1 design explicitly closes this by snapshotting
  the pre-login session's demo selection *before* `login()` runs.
  `management_portal/cases.py:_demo_selection_snapshot` (built in the
  "structured customer-case hand-off" phase) already produces exactly the
  bilingual, non-sensitive snapshot shape (`template_title_fa/en`,
  `category_fa/en`, `brand`, `theme_fa/en`, `personality_fa/en`,
  `features_fa/en`, `demo_template_slug` — never `public_token`/
  `session_key`) that the new Draft's `demo_snapshot` field should reuse
  verbatim rather than re-deriving; it currently lives as a private,
  `management_portal`-only helper and should be promoted to a neutral
  shared module (mirroring the existing `projects/demo_labels.py`
  precedent) as part of implementation, not duplicated.
- **V2.1 decision — single session enforcement:** delete-on-login (the
  old `Session` row is deleted from `django_session` at the moment a new
  login succeeds), not a version/registry counter. Rationale: deleting the
  row is enforced by Django's own trusted, already-tested session-loading
  code on the stale browser's very next request (it silently becomes an
  empty/anonymous session with zero custom code required) — a fail-closed
  guarantee that does not depend on a custom middleware continuing to run
  correctly forever. A version-counter approach would leave the old
  session row alive and rely on a middleware check on every request to
  enforce the boundary — fail-open if that specific middleware is ever
  skipped, misconfigured, or bypassed on some route. A new small
  `accounts.ActiveSession` model (one row per user: `user` OneToOne,
  `session_key`, `updated_at`) tracks the current pointer; the swap
  (delete old row, write new pointer) is wrapped in
  `transaction.atomic()` with `User.objects.select_for_update()` on the
  owning user row, exactly mirroring the `select_for_update()` pattern
  already used in this codebase's `PhoneVerificationView.form_valid` — the
  second of two simultaneous logins to acquire the lock correctly sees the
  first's freshly-written pointer (not a stale one) and converges to
  exactly one surviving session, closing the two-simultaneous-login race
  named in the task. Normal logout: `user_logged_out` clears the
  `ActiveSession` row (Django's own `logout()` already flushes/deletes the
  session). Session expiry: no custom code needed — Django's own session
  expiry semantics already treat an expired session as empty; the
  `ActiveSession` pointer just goes stale until the next login. A stale
  session sending a new request: becomes anonymous automatically (session
  row gone); a short-lived cache marker
  (`session-invalidated:<old_session_key>`, written just before deletion)
  lets a small, non-security-critical courtesy middleware show a one-time
  bilingual message ("این دستگاه از حساب شما خارج شد چون در جای دیگری
  وارد شدید." / "You were signed out here because you signed in
  elsewhere.") — if that middleware were ever skipped, the user simply
  sees a generic sign-in prompt instead of the friendlier one; the actual
  security boundary is unaffected either way, since it never depended on
  that middleware running. Rollout is prospective only (no forced global
  logout at launch) — an existing logged-in user is registered into
  `ActiveSession` at their *next* login, not retroactively; flagged below
  as a decision a human should confirm or override.
- **V2.1 — Draft data contract (`FormDraft`, new model, not yet created):**
  `owner` (FK to `accounts.User`), `form_type` (choices, starting with
  `"leads_contact"` only — designed so CRM/Clinic can be added later as a
  new choice value, no schema change), `current_step` (small int),
  `fields` (JSONField — the *exact same* non-sensitive allowlist already
  used by the V1 local draft: `request_type`, `service`, `budget_range`,
  `timeline`, `preferred_contact` — never free text or contact fields by
  default), `demo_snapshot` (JSONField, empty or the shared bilingual
  snapshot shape above — never a live `DemoSelection` reference),
  `status` (`open` / `submitting` / `submitted` / `expired`),
  `submitted_object_id` (nullable, points at the created `Lead.pk` once
  submitted — `Lead` itself is never modified), `created_at`/`updated_at`/
  `expires_at` (retention proposed at 7 days, matching the existing local
  draft's `DRAFT_MAX_AGE_MS` so the user never sees two different expiry
  numbers for what looks like "the same draft"). A conditional
  `UniqueConstraint` on `(owner, form_type)` scoped to `status="open"`
  keeps exactly one open draft per form per account — the same
  conditional-unique-constraint technique already used by
  `management_portal.CustomerCase`'s `unique_customer_case_source`.
  Explicit user deletion is a hard delete (no soft-delete, no export,
  matching the existing local draft's "Clear this device's draft"
  philosophy, just moved server-side).
- **V2.1 — privacy boundary:** only the non-sensitive fields above may be
  stored server-side by default. Free text (`message`) and contact fields
  (`name`, `phone`, `email_or_telegram`, `business_name`, `website_url`)
  require a *separate*, explicit, off-by-default consent layered on top of
  being logged in — being authenticated proves *who* the visitor is, not
  that they agreed to have this more sensitive category persisted
  server-side across devices; this mirrors the local V1 draft's own
  separate consent gate and is treated as a distinct, later, human-gated
  feature, not part of this design's default scope. Never in the URL,
  localStorage, logs, or any export/admin surface: `DemoSelection.public_token`,
  `DemoSelection.session_key`, `ActiveSession.session_key` (if ever
  surfaced to staff, only redacted, mirroring the existing
  `mobile_masked = f"{user.mobile[:4]}••••{user.mobile[-4:]}"` pattern
  already used in `PhoneVerificationView`), and any free text/contact data
  unless/until the separate consent layer above is explicitly approved and
  built.
- **V2.1 — implementation plan (design only, not started):** Phase A —
  single-session foundation (`ActiveSession` model + migration,
  `user_logged_in`/`user_logged_out` signal receivers in a new
  `accounts/signals.py`, wired via `AccountsConfig.ready()`, courtesy
  middleware; tests for the race, normal logout, and the one-time
  message). Phase B — `FormDraft` model + migration, promote
  `_demo_selection_snapshot` to a neutral shared module, wire pre-login
  demo capture (must resolve `_session_demo_selection` *before* calling
  `login()`, since `cycle_key()` rotates the session immediately inside
  it) and post-login demo capture on the contact page; tests for
  idempotent snapshot upserts (mirroring the already-proven
  `CaseDocument` checksum pattern) and for the pre-login capture surviving
  the session-key rotation. Phase C — server-side restore/delete UI on
  `leads/contact.html` and a "saved drafts" section on
  `accounts/dashboard.html`; ownership-scoped, `LoginRequiredMixin`-gated
  endpoints; tests for authorization (a user must never see or delete
  another user's draft) and for guests seeing zero behaviour change.
  Phase D — atomic, race-safe final submission:
  `FormDraft.objects.select_for_update()` inside `transaction.atomic()`
  transitions `open → submitting → submitted` and sets
  `submitted_object_id`; a second, racing submission of the same draft is
  redirected to the already-created Lead instead of creating a duplicate
  — mirroring the `IntegrityError`/`select_for_update()` patterns already
  proven in this codebase (`PhoneVerificationView`,
  `DemoConfigureView`). Phase E — full regression suite, `check`,
  migration dry-run, `git diff --check`, and an optional
  `cleanup_form_drafts` command mirroring `cleanup_demo_selections`'s
  dry-run-by-default/`--apply`/batch-safe shape. Each phase lists its own
  migration expectation, tests, rollback, and risk in the fuller report
  delivered to the user this session; every phase requires explicit human
  approval before any code is written, per AGENTS.md.
- **V2.1 — decisions requiring explicit human approval (not decided by
  this design):** (1) whether/when to build the separate consent layer
  for storing free text/contact info in server-side drafts at all; (2) the
  exact retention period for `FormDraft` (7 days proposed, matching V1,
  but this is now tied to a real identified account); (3) whether to
  proactively suggest login to guests ("sign in to continue on another
  device"), given this project's explicit prior history of removing
  friction from registration; (4) confirming prospective-only single-
  session rollout (no forced global logout) is acceptable; (5) whether/
  when to schedule `cleanup_form_drafts` and the still-unresolved
  `cleanup_demo_selections` scheduling from an earlier phase.
- **V2.1-B1 — what was built:** `leads.FormDraft`
  (`leads/models/form_draft.py`, new file inside the existing
  `leads/models/` package — the package wins over the orphaned 3-line
  `leads/models.py` stub, so the new model follows the same
  package-module pattern as `leads/models/lead.py`): `owner` (FK to
  `settings.AUTH_USER_MODEL`, `related_name="form_drafts"`, `CASCADE`),
  `form_type` (choices, only `"leads_contact"` today), `current_step`
  (`PositiveSmallIntegerField`, default 0, `MinValueValidator(0)`/
  `MaxValueValidator(2)` — hardcoded to `leads_contact`'s 3-step wizard),
  `fields` (`JSONField`, `default=dict`), `demo_snapshot` (`JSONField`,
  `default=dict`, `blank=True`), `status` (`open`/`submitting`/
  `submitted`/`expired`), `submitted_lead` (a real
  `ForeignKey("leads.Lead", on_delete=models.SET_NULL, blank=True,
  null=True, related_name="source_form_drafts")` — referential integrity
  instead of a bare object-id, and it changes no column or behaviour on
  `Lead` itself), `created_at`/`updated_at`/`expires_at` (default 7 days
  out via `default_draft_expiry()`), two named indexes
  (`formdraft_owner_status_idx`, `formdraft_status_expiry_idx`), and a
  conditional `UniqueConstraint`
  (`unique_active_form_draft_per_owner_and_form_type` on
  `(owner, form_type)`, `condition=Q(status__in=("open", "submitting"))`)
  — mirrors `management_portal.CustomerCase`'s
  `unique_customer_case_source` technique, supported on both SQLite and
  PostgreSQL. `__str__` prints only `owner_id`/`form_type`/`status`, never
  field contents. Deliberately **no admin registration** for `FormDraft`.
  `leads/migrations/0006_formdraft_and_more.py`: one additive
  `CreateModel` + `AddConstraint`, no data migration, depends on
  `leads.0005_lead_demo_selection`; confirmed **not applied** to the local
  dev SQLite database (`showmigrations leads` shows only 0001–0005 as
  `[X]`) and confirmed fully captured (`makemigrations --check --dry-run`
  → "No changes detected").
  `leads/form_draft_service.py` (new file, the sole sanctioned write/read
  path — nothing else may construct or save a `FormDraft` directly):
  `normalize_fields(form_type, raw_fields)` allowlists exactly
  `request_type`/`service_id`/`budget_range`/`timeline`/
  `preferred_contact`, validated against `Lead.REQUEST_TYPES`/`Lead.BUDGETS`/
  `Lead.TIMELINES`/`Lead.CONTACT_METHODS` and (for `service_id`) an active
  `Service` row — any unknown key or invalid value raises
  `DraftValidationError` (never silently dropped or coerced), with
  forbidden keys (`name`, `phone`, `email_or_telegram`, `business_name`,
  `website_url`, `message`, `privacy_accept`, `public_token`,
  `session_key`, `submission_token`) named explicitly in the rejection.
  `get_active_draft(owner, form_type)` lazily expires a stale-but-not-yet-
  swept draft on read (mirrors Django's own session-expiry semantics — no
  sweep job has to have run first). `upsert_active_draft(...)` is the
  race-safe, idempotent create-or-update: `transaction.atomic()` +
  `select_for_update()` on the **owner** row (not `FormDraft` itself, the
  same pattern already proven in `accounts/services.py` and
  `accounts/signals.py`/`middleware.py` for V2.1-A) serializes every
  writer for that owner; an existing-but-expired draft is transitioned to
  `expired` and replaced rather than reused; `expires_at` is always
  recomputed to exactly `DRAFT_RETENTION_DAYS = 7` days from the current
  save; rejects any owner that is `None`/anonymous/unauthenticated before
  any query runs. `delete_draft(owner, draft_id)` is a hard delete
  strictly scoped to `pk=draft_id, owner=owner` — a foreign or
  nonexistent id deletes nothing and raises nothing.
  `projects/demo_snapshots.py` (new file): `build_demo_selection_snapshot`
  relocated from the private `management_portal.cases._demo_selection_snapshot`
  to a neutral, reusable module (same relocation pattern already used for
  `projects/demo_labels.py`), so both `management_portal.cases`
  (`sync_demo_selection_document`) and the future `leads.form_draft_service`
  wiring can share one source of truth instead of a private cross-app
  import. Output shape is byte-identical to the original for all existing
  valid data (`template_title_fa/en`, `category_fa/en`, `brand`,
  `theme_fa/en`, `personality_fa/en`, `features_fa/en`,
  `demo_template_slug`; never `public_token`/`session_key`/
  `submission_token`) — trusted, staff-managed template fields
  (title/category/slug) are left untouched, while visitor-controlled
  `selections` values (`brand`, theme/personality lookup keys, the
  `features` list) gained defensive type/length guards (`_safe_key`
  against unhashable lookup keys, a 200-char brand cap far more generous
  than the client's own 48-char limit, a 20-item feature cap) that only
  change behaviour for malformed/adversarial input, never for real data.
  `management_portal/cases.py` now imports and calls
  `build_demo_selection_snapshot` instead of defining its own copy; the
  removed local `DASH` constant had zero other usages in that file
  (confirmed via grep; `workspace_views.py` defines its own separate local
  `DASH`). **Not done in this phase, by explicit scope**: no view, signal,
  login path, or `LeadCreateView` change; no auto-save endpoint; no draft
  restore/delete UI; no wiring of `demo_snapshot` from an actual
  `DemoSelection` anywhere yet — only the model and internal service exist
  and are fully tested in isolation.
- **V2.1-B1 — test level:** `leads/test_form_draft.py` (new file, ~30
  tests across 5 classes): valid draft creation for a logged-in user;
  anonymous/no-owner rejection at the service layer; rejection of every
  forbidden key and of unknown keys; rejection of invalid choices and of
  an inactive or nonexistent `service_id`; `expires_at` extended to
  exactly 7 days on every valid save; an expired draft transitions to
  `expired` and a fresh active draft is created in its place; the
  conditional `UniqueConstraint` allows at most one open/submitting draft
  per owner+form_type; a repeated upsert updates the same row rather than
  creating a second one; `delete_draft` only ever removes a draft
  belonging to the specified owner; the relocated snapshot helper produces
  an output exactly equal, field-for-field, to a hand-written expected
  dict matching the original helper's shape; the snapshot and its
  serialization contain no `public_token`/`session_key`/`submission_token`
  anywhere. Plus `FormDraftPostgresRaceTests`
  (`@unittest.skipUnless(connection.vendor == "postgresql", ...)`,
  auto-skipped on SQLite): a `threading.Barrier`-synchronized, 4-thread
  concurrent-upsert test converges to exactly one active draft row with no
  duplicate-key exceptions escaping (a self-caught test bug — one thread
  originally used the out-of-range `current_step=3` for the 3-step
  `leads_contact` wizard, correctly triggering `DraftValidationError`; not
  a concurrency bug — fixed by reusing step 0 for that thread, re-run once
  plus 5 additional repeats, all clean); and a raw model-level
  `IntegrityError` race test proving the database-level constraint itself
  (not just the service's lock) rejects a second concurrent active row.
  `leads.test_form_draft` alone: 29 passed, 2 correctly skipped on SQLite.
  Re-ran the pre-existing `management_portal.tests.DemoSelectionCaseHandoffTests`
  (8 tests) unchanged immediately after the `cases.py` extraction to
  confirm zero regression before proceeding further.
  `leads`+`projects`+`management_portal` targeted suite: 204 tests, all
  passing (2 skips). Full project suite: 591 tests, all passing (5 skips —
  all correctly the PostgreSQL-only tests). `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected"), and
  `git diff --check` (clean) all passed.
- **V2.1-B1 — PostgreSQL constraint/race evidence:** same isolated local
  PostgreSQL 16 server and disposable `test_arvion_ci_local` database used
  for V2.1-A's own race tests (never the permanent `arvion_ci_local`
  database). Ran
  `DJANGO_SETTINGS_MODULE=arvion.settings.ci DATABASE_URL=postgresql://rwin@localhost:5432/arvion_ci_local
  python manage.py test leads.test_form_draft.FormDraftPostgresRaceTests`
  — both the service-level concurrent-upsert race and the raw
  `IntegrityError` constraint race passed, run once plus 5 additional
  repeats of the concurrent-upsert test to rule out a lucky pass (all 5
  clean). This is real row-locking/constraint evidence, not a SQLite-only
  claim dressed up as PostgreSQL-verified.
- **V2.1-B1 — security review:** `owner`/`form_type`/`current_step`/
  `fields`/`demo_snapshot`/`status`/`submitted_lead` never appear in any
  log statement, exception message, or `__str__`/`__repr__` — only
  `owner_id`, `form_type`, and `status` (all non-sensitive metadata) are
  ever printed. No admin registration or export exists for `FormDraft`. No
  public/anonymous path can create a draft — `_require_real_owner` checks
  `is_authenticated` and a real `pk` before any query. Raw request JSON is
  never stored directly; only `normalize_fields`'s validated output is
  ever written to the `fields` column. UI, login, signals, and
  `LeadCreateView` are untouched in this phase (confirmed via
  `git status --short`/`git diff --stat`: only `leads/models/__init__.py`
  and `management_portal/cases.py` modified, everything else new files).
- **V2.1-B1 corrective — what changed:** `leads/form_draft_service.py`
  only (no model or migration change; no view/signal/login-path change).
  Four real defects found in `537c9a2` and fixed:
  1. **P1 — arbitrary caller-supplied `demo_snapshot`.**
     `upsert_active_draft` no longer accepts a `demo_snapshot` keyword at
     all — `TypeError` if a caller tries. `demo_snapshot` can now only be
     changed through two new, explicitly named functions:
     `attach_demo_snapshot(*, owner, form_type, demo_selection)`, which
     requires a real, already-saved `projects.DemoSelection` instance
     (rejects a dict, `None`, or an unsaved instance with
     `DraftValidationError`), always derives the snapshot itself via
     `build_demo_selection_snapshot` (never trusts a caller-supplied
     dict), and re-validates the result's key set against a fixed
     12-key allowlist (`_validate_snapshot_shape`) before writing —
     defense in depth against a future change to the snapshot builder
     smuggling in a forbidden key; and `clear_demo_snapshot(*, owner,
     form_type)`, which sets it to `{}` and touches nothing else. Both
     operate only on the calling owner's own active draft (found via the
     same owner-row-locked path as `upsert_active_draft`), so neither can
     reach or modify another account's draft — actual session/ownership
     authorization of the `DemoSelection` itself is deferred to the
     caller in the still-`NOT_STARTED` B2 wiring phase, as originally
     scoped.
  2. **P1 — ordinary field saves silently wiped an existing snapshot.**
     `upsert_active_draft` no longer touches `demo_snapshot` in any way: a
     newly created draft gets the model's own `{}` default, and an
     existing draft's `demo_snapshot` is left out of both the in-memory
     assignment and `update_fields`, so a plain `fields`/`current_step`
     save can never revert a previously attached snapshot.
  3. **P1 — `get_active_draft` wrote on read, racing a renewal.**
     `get_active_draft` is now a single, plain `SELECT` — it filters
     directly on `expires_at__gt=now()` and returns `None` for a stale row
     without ever calling `.save()`, opening a transaction, or taking a
     row lock. The only place `status` is ever transitioned to
     `"expired"` as a write is the new shared helper
     `_get_active_draft_locked`, called only from inside the
     `transaction.atomic()` + `select_for_update(owner)` block already
     used by `upsert_active_draft`, and now also by
     `attach_demo_snapshot`/`clear_demo_snapshot`. This closes the race
     where a concurrent renewal's freshly-extended `expires_at` could be
     clobbered back to `"expired"` by a straggling read that captured the
     old (stale) row state before the renewal committed.
  4. **P1 — validation errors leaked payload content.** Every
     `DraftValidationError` raised anywhere in this module is now one of
     a small, fixed set of generic, non-interpolated messages (e.g. "One
     or more fields are not recognized.", "One or more field values are
     invalid.", "current_step is out of range for this form_type."),
     each tagged with a `code` attribute drawn only from this module's own
     fixed vocabulary (`unauthenticated_owner`, `unsupported_form_type`,
     `forbidden_field`, `unknown_field`, `invalid_field_value`,
     `invalid_current_step`, `invalid_demo_selection`, `no_active_draft`,
     `invalid_snapshot_shape`, ...) — never the caller-supplied value,
     never an arbitrary caller-supplied key name (even for the *forbidden*
     key case, where the key itself is one of 10 fixed known strings, the
     public message still never repeats it, keeping the exact same
     wording whether the field was merely unrecognized or explicitly
     forbidden).
  Plus a P2 fix: `DRAFT_RETENTION_DAYS` is no longer defined twice — the
  service now imports it from `leads/models/form_draft.py`
  (`from .models.form_draft import DRAFT_RETENTION_DAYS`), the single
  source also used by the model's own `default_draft_expiry()`. No schema
  or migration change, confirmed by `makemigrations --check --dry-run`
  ("No changes detected").
- **V2.1-B1 corrective — test level:** `leads/test_form_draft.py` gained
  16 new tests across 3 new/expanded areas, and 1 existing test was
  updated to match the now-read-only `get_active_draft` contract (it
  previously asserted the buggy write-on-read behaviour). New:
  `DemoSnapshotAttachClearTests` (7 tests) — attach builds the exact
  snapshot `build_demo_selection_snapshot` would produce; a dict, `None`,
  or an unsaved `DemoSelection` is rejected with no draft mutated; attach
  requires an existing active draft; a plain field-only upsert preserves
  a previously attached snapshot byte-for-byte; clear removes only the
  snapshot, leaving `fields`/`current_step` untouched; attach/clear for
  one owner can never reach or modify another owner's draft (verified by
  asserting the other owner's snapshot is unchanged after both
  operations). `OpaqueValidationErrorTests` (6 tests) — an invalid choice
  value, an unrecognized field's own key name, a forbidden field's value,
  an out-of-range `current_step`, and an invalid `demo_selection` payload
  are each confirmed absent, verbatim, from the raised exception's
  `str()`; a mixed-hashable-type, ~200KB payload is rejected cleanly (no
  `TypeError` from sorting/formatting, no unbounded content echoed back,
  message kept under 500 characters). Plus 2 more in
  `UpsertActiveDraftTests` — `demo_snapshot=` now raises `TypeError`
  (keyword no longer exists) and leaves zero rows persisted; the service's
  `DRAFT_RETENTION_DAYS` is confirmed (via `assertIs`) to be the exact
  same object as the model's, not a second copy. And 1 new direct
  query-evidence test, `test_get_active_draft_issues_no_writes_and_no_row_lock`,
  which wraps a `get_active_draft` call in `CaptureQueriesContext` (asserts
  none of the captured statements start with `UPDATE`/`INSERT`/`DELETE`)
  while `django.db.models.QuerySet.select_for_update` is patched to raise
  if ever called — proving both "no write" and "no lock" directly rather
  than only by code inspection. `leads.test_form_draft` alone: 47 tests
  total, 44 passed and 3 correctly skipped on SQLite (up from 31 total/29
  passed/2 skipped in `537c9a2` — the net +16 total reflects the 16 new
  tests; 1 existing test was also updated in place to assert the new,
  correct read-only behaviour rather than the old buggy one, which does
  not change the total). **Correction (found and fixed in the V2.1-B1
  second corrective phase below): this bullet previously misstated the
  above as "47 passed, 3 correctly skipped" — i.e. treating the total
  test count as the passed count. The true breakdown for this commit
  (`0e1a208`) is 44 passed + 3 skipped = 47 total, as corrected here.**
  `leads`+`projects`+`management_portal` targeted suite: 220 tests, all
  passing (3 skips). Full project suite: 607 tests, all passing (6 skips
  — all correctly PostgreSQL-only, up from 5 in `537c9a2` by exactly the
  one new race test). `manage.py check` (0 issues), `makemigrations
  --check --dry-run` ("No changes detected"), and `git diff --check`
  (clean) all passed.
- **V2.1-B1 corrective — PostgreSQL race evidence:** added
  `test_concurrent_expired_read_cannot_clobber_a_racing_renewal` to
  `FormDraftPostgresRaceTests` — a real regression proof, not just a code-
  inspection claim: one thread calls `get_active_draft` in a tight loop
  against a row already past its `expires_at` while a second thread
  concurrently calls `upsert_active_draft` to renew that same row (expire
  the stale one, create a fresh active one), synchronized via
  `threading.Barrier(2)` with independent database connections. After
  every run: exactly one active (`"open"`) draft survives with a future
  `expires_at`, and the original stale row is `"expired"` — the reader
  thread never re-expires the freshly renewed row, because it never
  writes anything at all. Run against the same isolated local PostgreSQL
  16 `test_arvion_ci_local` database used throughout this project (never
  the permanent `arvion_ci_local`), alongside the two pre-existing race
  tests from `537c9a2` (all 3 tests, once plus 5 additional repeats of the
  full `FormDraftPostgresRaceTests` class — all clean, no failures, no
  hangs).
- **V2.1-B1 corrective — security review:** confirmed opaque, fixed error
  messages contain no interpolated value or key name anywhere in
  `form_draft_service.py` (grepped for every remaining f-string/`.format`/
  `%`-style interpolation into a `DraftValidationError` message — none
  found). `attach_demo_snapshot`/`clear_demo_snapshot` reuse
  `_require_real_owner` and the owner-row lock, so the "no anonymous/
  public draft creation" and "never another account's draft" guarantees
  established in `537c9a2` extend unchanged to the new snapshot
  operations. No admin registration, no new log statement, no new
  `__str__`/`__repr__` surface. Confirmed via `git status --short`/
  `git diff --stat` that only `leads/form_draft_service.py` and
  `leads/test_form_draft.py` changed (plus this documentation file) —
  no view, template, signal, URL, or `LeadCreateView` touched.
- **Git boundary (as of `0e1a208`, historical — see the accurate,
  up-to-date count directly below):** `main` was twelve commits ahead of
  `origin/main` at that point (the ten from the V2.1-A corrective entry,
  plus the V2.1-B1 commit `537c9a2`, plus the V2.1-B1 first corrective
  commit `0e1a208`). `537c9a2` was not amended.
- **V2.1-B1 second corrective — what changed:**
  `leads/form_draft_service.py` only (no model or migration change; no
  view/signal/login-path change). Four more real defects found on top of
  the already-`VERIFIED` `0e1a208` and fixed:
  1. **P1 — attach/clear did not extend `expires_at`.** Both
     `attach_demo_snapshot` and `clear_demo_snapshot` now recompute
     `expires_at` to exactly `DRAFT_RETENTION_DAYS` from the same `now`
     used for the rest of the write, and include it in `update_fields` —
     attaching or clearing a snapshot is a real draft-touching operation,
     exactly like `upsert_active_draft`, and must renew the draft the
     same way. `fields`/`current_step` remain untouched by both.
  2. **P1 — an expired-draft transition could be rolled back.**
     `_get_active_draft_locked` transitions a stale draft to `"expired"`
     as a write inside the caller's `transaction.atomic()` block; if that
     same block then raised `DraftValidationError("no active draft ...")`
     for `attach_demo_snapshot`/`clear_demo_snapshot`, the exception
     propagating out of `atomic()` rolled back *everything* written
     inside it — including the expiry transition that should have
     survived. Both functions now assign to `draft` inside the `with
     transaction.atomic():` block but only raise `no_active_draft`
     *after* that block exits normally (i.e., after the transaction has
     committed), so a concurrently-discovered expiry always survives even
     when the calling operation itself then reports "nothing to act on".
  3. **P1 — `attach_demo_snapshot` trusted the caller's in-memory
     instance.** A new `_reload_demo_selection` helper re-reads the
     `DemoSelection` fresh from the database by primary key (with
     `select_related("template")`) before `build_demo_selection_snapshot`
     ever sees it, so a caller's locally mutated (never-saved) instance,
     or one whose row has since been deleted by another process, can
     never influence or fabricate a stored snapshot. Session/ownership
     authorization of which `DemoSelection` a caller may attach is still
     explicitly deferred to the B2 wiring phase, unchanged from
     `0e1a208`'s scoping — not added here.
  4. **P2 — snapshot validation only checked the key set, not values.**
     `_validate_snapshot_shape` now also requires every text field
     (`template_title_fa/en`, `category_fa/en`, `brand`, `theme_fa/en`,
     `personality_fa/en`, `demo_template_slug`) to be a plain `str` no
     longer than 300 characters (bool/int/bytes/list/dict all fail the
     `isinstance` check outright), both `features_fa`/`features_en` to be
     lists of at most 20 strings of at most 200 characters each, and the
     two feature lists to have the exact same length — all before any
     write, with the same fixed, non-interpolated `invalid_snapshot_shape`
     message regardless of which check failed.
- **V2.1-B1 second corrective — test level:** `leads/test_form_draft.py`
  gained 13 new tests, all in `DemoSnapshotAttachClearTests` except 2 new
  PostgreSQL-only race tests in `FormDraftPostgresRaceTests`: expires_at
  extension on a successful attach and on a successful clear (2 tests);
  the expired-transition-survives-a-rollback regression proof for both
  attach and clear, asserting via a fresh `refresh_from_db()` that the
  stale draft's `status` really is `"expired"` even though the same call
  raised `DraftValidationError(code="no_active_draft")` (2 tests); an
  expired draft is never revived by either operation (1 test);
  `upsert_active_draft` still creates a fresh draft after expiry,
  confirming no regression from the control-flow change (1 test); a
  `DemoSelection` mutated only in memory (never saved) cannot leak its
  tampered `selections` into the stored snapshot (1 test); a
  `DemoSelection` row deleted out from under a caller's stale reference is
  rejected with `invalid_demo_selection` and leaves the draft's
  `demo_snapshot` at `{}` (1 test); seven malformed-snapshot variants
  (wrong-typed `brand`, an oversized string, non-list `features_fa`,
  non-string feature members, mismatched feature-list lengths, a nested
  list where a string was expected, and a `bool` where a string was
  expected), each via `mock.patch` on `build_demo_selection_snapshot`,
  rejected with `invalid_snapshot_shape` and confirmed to leave the
  existing draft's `fields`/`current_step`/`demo_snapshot`/`expires_at`
  completely unchanged (1 parametrized test covering all seven). Plus 2
  new PostgreSQL-only race tests (see below). `leads.test_form_draft`
  alone: 58 tests total, 53 passed and 5 correctly skipped on SQLite (up
  from 47 total/44 passed/3 skipped after `0e1a208` — the net +9
  passed/+2 skipped reflects the 9 new non-Postgres tests and 2 new
  PostgreSQL-only race tests, all additive; none of the prior tests were
  removed or altered).
  `leads`+`projects`+`management_portal`
  targeted suite: 231 tests, all passing (5 skips).
  `management_portal.tests.DemoSelectionCaseHandoffTests` re-run
  explicitly (8 tests, unchanged, all passing) to confirm the stricter
  snapshot-value validation causes no regression against real
  `CaseDocument` snapshot data. Full project suite: 618 tests total, 610
  passed and 8 correctly skipped (all PostgreSQL-only; up from 607
  total/601 passed/6 skips at `0e1a208` by exactly the 11 new tests added
  this phase). `manage.py check` (0 issues), `makemigrations --check
  --dry-run` ("No changes detected"), and `git diff --check` (clean) all
  passed.
- **V2.1-B1 second corrective — PostgreSQL race evidence:** two new tests
  added to `FormDraftPostgresRaceTests`, run against the same isolated
  local PostgreSQL 16 `test_arvion_ci_local` database used throughout this
  project (never the permanent `arvion_ci_local`):
  `test_concurrent_attach_and_upsert_on_an_active_draft_both_apply` (an
  already-active draft is concurrently updated by `upsert_active_draft`
  and by `attach_demo_snapshot`; since the two write disjoint columns and
  both go through the same owner-row lock, both must and do survive
  regardless of ordering) and
  `test_concurrent_upsert_and_attach_around_expiry_never_double_expires_or_revives`
  (a stale draft is concurrently raced by a renewing `upsert_active_draft`
  and an `attach_demo_snapshot` call; the attach side may legitimately
  lose the race and fail with `DraftValidationError(code="no_active_draft")`
  — that is an accepted, correct outcome, not a bug — but exactly one row
  ever transitions to `"expired"`, exactly one active draft survives, and
  the expired row is never revived, regardless of which thread the lock
  admits first). Run once plus 5 additional repeats of the full
  `FormDraftPostgresRaceTests` class (now 5 tests total) — all clean, no
  failures, no hangs, no deadlocks.
- **V2.1-B1 second corrective — security review:** the new
  `_reload_demo_selection`/value-validation logic introduces no new log
  statement, no new `__str__`/`__repr__` surface, and no admin
  registration. All new `DraftValidationError` messages remain fixed and
  generic (`invalid_snapshot_shape`/`invalid_demo_selection`/
  `no_active_draft`) — confirmed by tests that inject a wrong-typed or
  oversized value and assert it never appears in `str(exception)`. The
  owner-row lock and `_require_real_owner` gate are unchanged and still
  apply to both `attach_demo_snapshot` and `clear_demo_snapshot`, so
  "never another account's draft" continues to hold (re-confirmed by the
  existing `test_attach_and_clear_never_touch_another_owners_draft`).
  Confirmed via `git status --short`/`git diff --stat` that only
  `leads/form_draft_service.py` and `leads/test_form_draft.py` changed
  (plus this documentation file) — no view, template, signal, URL, or
  `LeadCreateView` touched.
- **Git boundary (as of `a5d2371`, historical — see the accurate,
  up-to-date count directly below):** `main` was thirteen commits ahead
  of `origin/main` at that point — the twelve from the prior entry, plus
  the V2.1-B1 second corrective commit `a5d2371`. Neither `537c9a2` nor
  `0e1a208` was amended.
- **V2.1-B2 — what was built:** the first two hand-off paths connecting
  `projects.DemoSelection` (anonymous, session-bound) to
  `leads.FormDraft` (account-bound), with no UI, auto-save endpoint,
  restore/delete surface, or `Lead`-submission change.
  `leads/form_draft_service.py` gained two new functions:
  `ensure_active_draft(*, owner, form_type)` (race-safe "make sure one
  active draft exists," creating an empty one only if needed — never
  touches `fields`/`current_step`/`demo_snapshot` on an existing draft)
  and `ensure_active_draft_with_demo_snapshot(*, owner, form_type,
  demo_selection)` (the same "ensure," plus attaching a validated
  snapshot, both under one owner-locked transaction — unlike
  `attach_demo_snapshot`, this never raises `no_active_draft`, since it
  creates the draft itself when none exists). `leads/demo_handoff.py`
  (new module): `store_pending_demo_selection(request, selection)` writes
  only `{"demo_selection_id": <int>, "form_type": "leads_contact"}` into
  `request.session["leads:pending_demo_selection"]` — never
  `public_token`/`session_key`/`submission_token`, never the snapshot
  itself — and skips the write when the marker already matches, so a
  replayed `?demo=` link does not keep dirtying the session.
  `pop_pending_demo_selection_id(request)` always pops the marker and
  returns the id only if the marker is a well-formed dict scoped to
  `form_type == "leads_contact"`; anything else (wrong shape, wrong
  form_type, absent) returns `None`. `handle_resolved_demo_selection(request,
  selection)` is the single dispatch point called by the view with an
  already-`_session_demo_selection`-validated selection: an anonymous
  visitor gets a marker stored; an authenticated non-staff customer gets
  `ensure_active_draft_with_demo_snapshot` called immediately (rejections
  are logged and swallowed — this hand-off is a convenience, never a hard
  requirement for the contact page to render); a staff/superuser account
  gets neither. `leads/signals.py` (new module):
  `attach_pending_demo_selection_on_login`, a `user_logged_in` receiver
  (`dispatch_uid="leads.attach_pending_demo_selection_on_login"`,
  registered from `leads/apps.py`'s new `LeadsConfig.ready()` — mirrors
  the existing `accounts.apps.AccountsConfig.ready()` pattern exactly, and
  keeps `accounts` fully unaware that `leads` is listening) that: pops the
  pending marker *before* checking staff/superuser status (so a stray
  marker can never survive a staff login and later leak into a different
  customer's subsequent login on the same physical session); returns
  silently if there is no marker, the popped id doesn't resolve to a real
  `DemoSelection` row, or the user is staff/superuser; otherwise calls
  `ensure_active_draft_with_demo_snapshot`, logging and swallowing a
  `DraftValidationError` (a final, non-retryable rejection) or restoring
  the marker on any other exception (a presumed-transient failure, so the
  customer's next authenticated request can retry) — either way, login
  itself is never blocked or failed. `leads/views/contact.py`:
  `LeadCreateView` gained a `_resolved_demo_selection()` helper that
  memoizes the existing `_session_demo_selection(self.request)` lookup
  per view instance (so `get_initial`/`get_context_data` share one query
  instead of two) and, on the first successful resolution only, calls
  `handle_resolved_demo_selection`. `get_initial`/`get_context_data` now
  call this helper instead of the module-level function directly.
  `form_valid` is byte-for-byte unchanged (still calls
  `_session_demo_selection(self.request)` directly) — deliberately left
  untouched per this phase's explicit review constraint, so `Lead`
  submission itself has zero behavioural change.
- **V2.1-B2 — why session rotation doesn't break the link:**
  `django.contrib.auth.login()` takes one of two paths depending on prior
  session state: a previously-anonymous session gets `cycle_key()`, which
  **preserves session data** while minting a new key — so a marker
  written before `login()` survives into the `user_logged_in` receiver
  untouched; a session that already belonged to a *different*
  authenticated user gets `flush()` instead, which **wipes all session
  data** before the new login proceeds — so a marker can never survive
  into a different account's login. This is exactly Django's own,
  already-trusted session-fixation defence; no new code was needed to
  get the account-switch protection required by this phase; it was
  proven, not assumed, by the account-switch test below.
- **V2.1-B2 — security review:** the marker never holds
  `public_token`/`session_key`/`submission_token` or the snapshot itself
  (only an internal integer id + a fixed form_type string) — verified by
  tests inspecting the raw session payload after every marker-writing
  path. `demo_selection` is re-validated and re-read fresh from the
  database by every function that touches it (unchanged from the prior
  corrective phase), so a caller-controlled object is never trusted.
  Staff/superuser accounts never receive a `FormDraft` from either hand-off
  path (verified for both login and the already-authenticated view path).
  No log statement in `leads/signals.py` or `leads/demo_handoff.py`
  interpolates any value, id, token, or payload — both are fixed strings.
  `accounts` was not modified at all: it fires the same `user_logged_in`
  signal it always has, unaware that `leads` is now listening. No new
  admin registration, no new public/auto-save endpoint, no new URL. `git
  status --short`/`git diff --stat` confirm only `leads/apps.py`,
  `leads/form_draft_service.py`, `leads/test_form_draft.py`, and
  `leads/views/contact.py` were modified (plus this documentation file),
  and `leads/demo_handoff.py`/`leads/signals.py`/`leads/test_demo_handoff.py`
  are new files — no `accounts/*`, `management_portal/*`, template,
  JavaScript, or migration touched, and `LeadCreateView.form_valid` is
  byte-for-byte identical to before.
- **V2.1-B2 — test level:** `leads/test_form_draft.py` gained 12 new
  tests: `EnsureActiveDraftTests` (5 — creates an empty draft when none
  exists; returns an existing draft completely unmodified; repeated calls
  never create a second draft; a stale draft is expired and replaced;
  anonymous owner rejected) and `EnsureActiveDraftWithDemoSnapshotTests`
  (6 — creates a draft with the snapshot when none existed; never raises
  `no_active_draft` unlike `attach_demo_snapshot`; preserves
  `fields`/`current_step` on an existing draft; repeated calls are
  idempotent; a deleted `DemoSelection` is rejected without writing;
  never touches another owner's draft), plus 1 new PostgreSQL-only race
  test (see below). New file `leads/test_demo_handoff.py` (25 tests):
  `PendingDemoMarkerHelperTests` (6, direct unit tests of the marker
  helpers — correct shape, skip-when-unchanged, malformed/wrong-form-type/
  absent all return `None`); `ContactViewDemoHandoffTests` (6 — anonymous
  visit stores a marker with no token/session_key in it; an invalid or
  foreign-session token never creates or overwrites an existing marker;
  exactly one `DemoSelection` query per request via
  `CaptureQueriesContext`; an authenticated non-staff customer gets the
  snapshot synced immediately and idempotently; staff get neither draft
  nor marker; an authenticated customer cannot attach another session's
  `DemoSelection`); `LoginSignalHandoffTests` (12 — normal login attaches
  the snapshot and clears the marker; session-key rotation doesn't break
  the link; existing `fields`/`current_step` survive the attach; the
  receiver called twice directly never duplicates the draft; a malformed
  marker or a since-deleted `DemoSelection` is cleared with login still
  succeeding; a mocked transient exception leaves login unharmed and
  restores the marker for retry; a mocked `DraftValidationError` leaves
  login unharmed and does *not* restore the marker; staff and superuser
  logins never receive a customer's pending selection; the flush-path
  account-switch scenario — a session already carrying a different
  user's `SESSION_KEY` before a new login — never transfers the marker;
  no forbidden token appears in the resulting draft or session);
  `RegistrationHandoffTests` (1 — registration's automatic post-signup
  login attaches the snapshot exactly like a normal login). On SQLite:
  `leads` app alone: 107 tests, 101 passed, 6 correctly skipped.
  `accounts`+`projects`+`management_portal`: 234 tests, all passing (2
  skips) — confirming no regression in registration, login, phone
  verification, or email verification, and no change to
  `management_portal`'s own behaviour. Full project suite: 655 tests
  total, 646 passed, 9 correctly skipped
  (all PostgreSQL-only; up from 618 total/8 skips at `a5d2371` by exactly
  the 37 new tests this phase added: 25 in `test_demo_handoff.py` + 12 in
  `test_form_draft.py`). `manage.py check` (0 issues), `makemigrations
  --check --dry-run` ("No changes detected" — no model or migration
  change in this phase), and `git diff --check` (clean) all passed.
- **V2.1-B2 — PostgreSQL evidence, and one unrelated pre-existing issue
  found along the way:** `leads.test_form_draft.FormDraftPostgresRaceTests`
  gained
  `test_concurrent_ensure_and_attach_converge_to_one_draft_with_the_snapshot`
  — two threads call `ensure_active_draft_with_demo_snapshot` for the same
  owner at (as close as Python threading allows) the same instant,
  synchronized via `threading.Barrier(2)` with independent database
  connections, simulating a double-tab login race; result every run:
  exactly one `FormDraft` row, holding the snapshot, status `"open"`. Ran
  the full `FormDraftPostgresRaceTests` class (now 6 tests) once plus 5
  additional repeats against the same isolated local PostgreSQL 16
  `test_arvion_ci_local` database used throughout this project (never the
  permanent `arvion_ci_local`) — all clean. Also ran `accounts`+`leads`+
  `projects` against that same real PostgreSQL database (201 tests, all
  passing — confirming the new signal/handoff wiring has no
  PostgreSQL-specific regression). A separate run adding
  `management_portal` to that same command (341 tests total) surfaced one
  **pre-existing, unrelated** failure —
  `assessments/services.py`'s `revoke_assessment_access` does
  `ExamEntitlement.objects.select_for_update().select_related("attempt")`,
  and PostgreSQL rejects `SELECT ... FOR UPDATE` on the nullable side of
  an outer join produced by that `select_related`. This is not caused by,
  and not fixed as part of, this phase — it lives entirely in
  `assessments/services.py` (never touched here), was not introduced by
  any commit in this session, and was only ever discovered because this
  is the first time this project's `management_portal` suite happened to
  be run against a real PostgreSQL engine rather than SQLite. Left
  unfixed and flagged below as a risk for a human to prioritize; the
  `management_portal` suite passes cleanly on SQLite (its normal test
  backend) and was not otherwise touched by this phase.
- **V2.1-B2 — migration status:** none created or needed;
  `makemigrations --check --dry-run` reported "No changes detected." No
  model field changed; `leads.FormDraft`'s schema (from `537c9a2`) is
  unmodified.
- **Git boundary (as of `757f7a4`, historical — see the accurate,
  up-to-date count directly below):** `main` was fourteen commits ahead
  of `origin/main` at that point — the thirteen from the prior entry,
  plus `757f7a4`. No prior commit was amended.
- **V2.1-B2 first corrective — root cause and fix:** `leads/signals.py` only
  had the two-line receiver refactored; all of the actual logic moved
  into a new, single, safe orchestration function in
  `leads/demo_handoff.py`.
  1. **P1 — an unhandled `DatabaseError` fetching `DemoSelection` could
     turn a real login into a 500.** The old code was: pop the marker,
     then (outside any `try`) run
     `DemoSelection.objects.select_related("template").filter(pk=...)
     .first()`. Fixed by moving this fetch inside `leads.demo_handoff
     .consume_pending_demo_selection` — the new single orchestration
     function both the login receiver and the new retry path call — with
     its own dedicated `try`/`except Exception`: on failure, a fixed
     message is logged (no id, no token, no payload) and the marker is
     restored via a new, narrow, validated helper,
     `_restore_pending_demo_selection_id(request, demo_selection_id)`
     (writes the marker directly from the already-known, already-
     type-checked id — never from caller-supplied data, and never by
     hand-assembling a session dict inline at the call site). A malformed
     marker, a foreign-form-type marker, a staff/superuser account, or a
     genuinely-deleted `DemoSelection` still all correctly result in no
     restoration (those are final, non-retryable outcomes, unchanged from
     `757f7a4`). `leads/signals.py`'s receiver is now a two-line trigger
     that only calls `consume_pending_demo_selection(request, user)` —
     it no longer imports `DemoSelection`, constructs a query, or touches
     `request.session` directly at all.
  2. **P2 — the promised retry path did not exist.** `757f7a4`'s own
     documentation and final report claimed a transient failure's marker
     "is retried on the customer's next authenticated request," but there
     was no code anywhere that ever re-consumed a surviving marker outside
     the login moment itself — an authenticated customer whose login-time
     attach failed transiently had no way to ever recover it. Fixed by a
     new, narrowly-scoped function, `leads.demo_handoff
     .maybe_retry_pending_demo_selection(request)`, wired into exactly one
     place: `LeadCreateView._resolved_demo_selection()`, only in the
     `elif` branch taken when there is no explicit `?demo=` in the URL at
     all (an explicit, valid demo link always wins instead — see below —
     and an explicit but invalid/foreign one deliberately does *not* fall
     back to an old marker, so a bad link can never silently resurrect
     unrelated stale data). The function itself checks
     authenticated+non-staff+non-superuser and a plain
     `PENDING_DEMO_SESSION_KEY in request.session` membership test (no
     query at all when no marker exists) before delegating to the same
     `consume_pending_demo_selection` orchestration the login receiver
     uses — so first attempt and retry share one code path and one set of
     error/restore semantics, and this can never become a general
     middleware or add a query to any other page on the site.
  Also: a successful **explicit** `?demo=` attach (the
  `handle_resolved_demo_selection` path) now calls a new
  `clear_pending_demo_selection(request)` afterward, discarding any
  stale old marker so it can never later be retried and attach
  unrelated data (rule: an explicit, valid demo in the URL both wins over
  and clears an old marker). `handle_resolved_demo_selection` itself
  gained a second `except Exception` clause alongside its existing
  `except DraftValidationError` — its docstring's "never raises" claim
  had no coverage for a transient `DatabaseError` from
  `ensure_active_draft_with_demo_snapshot`, which would have 500'd the
  contact page for an already-authenticated customer exactly like the
  signals.py bug did for login; both exception types are now logged
  (fixed messages) and swallowed so the page always still renders.
- **V2.1-B2 first corrective — test level:** `leads/test_demo_handoff.py` grew
  from 25 to 35 tests (10 new): `test_database_error_looking_up_demo_
  selection_does_not_block_login` (mocks `DemoSelection.objects
  .select_related` to raise a real `django.db.DatabaseError` — confirms
  `auth_login` does not raise, the user is genuinely authenticated
  (`SESSION_KEY` present), the marker survives with its exact original
  id/form_type, and no `FormDraft` is created); a new
  `RetryPendingDemoSelectionOnContactPageTests` class (8 tests) covering:
  a pending marker is attached and cleared on the next `?demo=`-less
  authenticated visit; repeated visits after a successful retry stay
  idempotent (still exactly one `FormDraft`); a marker pointing at a
  since-deleted `DemoSelection` is cleared with the page still rendering
  and no draft created; a mocked transient error during retry leaves the
  marker intact and the page still renders (200, not 500); an explicit,
  valid `?demo=` wins over an old marker, attaches the *new* selection,
  and clears the old marker; an explicit but invalid/foreign `?demo=`
  does **not** fall back to retrying the old marker (which is left
  completely untouched for a later, param-free retry); staff and
  superuser visits never trigger the retry even with a marker present;
  no `public_token`/`session_key`/`submission_token` appears in the
  draft, session, or rendered response after a successful retry. Plus a
  new PostgreSQL-only class, `RealTransactionErrorRecoveryTests` (1
  test, see below). The two existing transient-error tests in
  `LoginSignalHandoffTests` were updated to patch
  `leads.demo_handoff.ensure_active_draft_with_demo_snapshot` instead of
  the now-removed `leads.signals.ensure_active_draft_with_demo_snapshot`
  import. `leads` app total: 117 tests, 110 passed, 7 correctly skipped
  (up from 107 total/6 skips at `757f7a4`, by exactly the 10 new tests —
  9 regular + 1 PostgreSQL-only). `accounts` app: 73 tests, all passing
  (2 skips) — confirming no regression in registration, login, phone
  verification, or email verification. `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected" — no model or
  migration change), and `git diff --check` (clean) all passed. Full
  project suite: 665 tests total, 655 passed, 10 correctly skipped (all
  PostgreSQL-only; up from 655 total/9 skips at `757f7a4` by exactly the
  10 new tests this phase added).
- **V2.1-B2 first corrective — PostgreSQL evidence:** the instruction for this
  phase was explicit that a mocked Python exception (used throughout
  `test_demo_handoff.py` for portability) is not evidence about
  PostgreSQL's own transaction behaviour, since it never touches the
  database at all. `RealTransactionErrorRecoveryTests` (new,
  `@unittest.skipUnless(connection.vendor == "postgresql", ...)`) forces
  a **genuine, server-side** error mid-transaction instead: it patches
  `FormDraft.objects.create` so that, when called inside
  `ensure_active_draft_with_demo_snapshot`'s own `transaction.atomic()`
  block, it runs a real `SELECT 1/0` against the actual PostgreSQL
  connection (a genuine `DataError: division by zero` from the server,
  not a Python-level mock) before re-raising. Result: `auth_login` still
  does not raise, the marker is restored with the exact original id/
  form_type, no `FormDraft` is created, and — critically — the database
  connection is left perfectly usable afterward: the test immediately
  performs a second, real (unmocked) call to
  `consume_pending_demo_selection` on the *same* connection and it
  succeeds cleanly, proving Django's `transaction.atomic()` rolled the
  aborted transaction all the way back rather than leaving the
  connection in PostgreSQL's "current transaction is aborted, commands
  ignored until end of transaction block" state. Ran against the same
  isolated local PostgreSQL 16 `test_arvion_ci_local` database used
  throughout this project (never the permanent `arvion_ci_local`), 4
  times total (once plus 3 additional repeats) — all clean. Also
  re-ran `accounts`+`leads`+`projects` against that same real PostgreSQL
  database (211 tests, all passing, 0 skips — every test that would skip
  on SQLite runs for real here) — confirming the new
  orchestration/retry wiring has no PostgreSQL-specific regression. The
  `assessments/services.py` PostgreSQL incompatibility found during the
  V2.1-B2 phase (`revoke_assessment_access`'s `select_for_update()` on an
  outer join) is **still present, still unrelated, still not touched by
  this or any other commit in this session** — flagged again here so it
  is not lost or quietly dropped from the record; a human still needs to
  prioritize it separately from this FormDraft work.
- **V2.1-B2 first corrective — migration status:** none created or needed;
  `makemigrations --check --dry-run` reported "No changes detected." No
  model or schema change — this phase is service/signal/view/test code
  only.
- **Git boundary (as of `2cd1032`, historical — see the accurate,
  up-to-date count directly below):** `main` was fifteen commits ahead of
  `origin/main` at that point — the fourteen from the prior entry, plus
  `2cd1032`. No prior commit was amended.
- **V2.1-B2 second corrective — root cause and fix:** the fetch's
  `try`/`except` added in `2cd1032` was structured as:
  ```python
  try:
      selection = DemoSelection.objects.select_related("template").filter(pk=selection_id).first()
  except Exception:
      ...restore marker...
  ```
  Catching a Python exception this way stops it from propagating, but it
  does nothing about the underlying *database* transaction state.
  PostgreSQL itself aborts a transaction the instant any statement inside
  it fails; recovering requires an explicit `ROLLBACK` (or, inside a
  larger transaction, a `ROLLBACK TO SAVEPOINT`) — something Django's
  `transaction.atomic()` only ever issues automatically when an exception
  actually *propagates out of* an `atomic()` block. Since the query above
  was never inside one, no rollback-to-savepoint ever happened; under
  `ATOMIC_REQUESTS=True` the *outer*, per-request transaction was left
  marked as needing a rollback, and the next real query anywhere in that
  same request — proven empirically below — fails with
  `django.db.utils.InternalError: current transaction is aborted, commands
  ignored until end of transaction block` (`psycopg`'s
  `InFailedSqlTransaction` surfaced through Django). Fixed by wrapping
  only the lookup itself in its own `transaction.atomic()`, with the
  `try`/`except` kept *outside* that block:
  ```python
  try:
      with transaction.atomic():
          selection = DemoSelection.objects.select_related("template").filter(pk=selection_id).first()
  except Exception:
      ...restore marker...
  ```
  This way, a real failure inside the `atomic()` block propagates out of
  it first, so Django's own `atomic()` machinery issues the `ROLLBACK TO
  SAVEPOINT` (nested inside the outer `ATOMIC_REQUESTS` transaction) or a
  full `ROLLBACK` (if this is the outermost atomic, e.g. when called
  directly outside a view) *before* our `try`/`except` ever sees the
  exception — leaving the surrounding request transaction perfectly
  usable for whatever queries come after. All previously-verified
  behaviour is unchanged: the marker is still popped before this lookup
  runs; a restored marker still carries the exact original
  `demo_selection_id`/`form_type`; login/registration still never raises;
  staff/superuser still never receive a marker; a genuinely-deleted
  `DemoSelection` is still a final outcome with no restoration; a
  `DraftValidationError` from the attach step is still final and
  unrestored; a transient attach-step failure still restores the marker
  (unchanged — that step already had its own internal
  `transaction.atomic()` inside `ensure_active_draft_with_demo_snapshot`,
  which is why only the lookup needed this fix); no log message anywhere
  in `leads/demo_handoff.py` interpolates a token, session key,
  submission token, snapshot, id, or any other payload value; an explicit,
  valid demo link still wins over an old marker; `LeadCreateView.form_valid`
  remains completely untouched (this phase only edited
  `leads/demo_handoff.py` and its own test file).
- **V2.1-B2 second corrective — the bug reproduced, then fixed and
  re-verified:** before finalizing the fix, it was temporarily reverted
  and the new PostgreSQL test below (with the fix in place, it passes)
  was re-run against that reverted code — it failed exactly as predicted,
  with `django.db.utils.InternalError: current transaction is aborted,
  commands ignored until end of transaction block` raised from a plain
  `User.objects.filter(...).exists()` call made *after* the simulated
  lookup failure, inside the same outer transaction. The fix was then
  restored and the same test re-verified passing. This confirms the test
  actually exercises the bug rather than trivially passing regardless.
- **V2.1-B2 second corrective — test level:** a new PostgreSQL-only test
  class was added to `leads/test_demo_handoff.py`,
  `RealTransactionErrorDuringLookupRecoveryTests` — kept **alongside**,
  not instead of, `2cd1032`'s existing `RealTransactionErrorRecoveryTests`
  (which forces a real error in the *attach* step and remains unchanged
  and still passing; the two exercise genuinely different code paths).
  The new test: opens an outer `transaction.atomic()` block standing in
  for Django's own `ATOMIC_REQUESTS` per-request wrapping; inside it,
  patches `DemoSelection.objects.select_related` so that, when
  `consume_pending_demo_selection` calls it during `auth_login()`, it
  executes a real `SELECT 1/0` against the actual PostgreSQL connection
  (a genuine server-side `DataError`, not a mocked Python exception);
  asserts `auth_login` does not raise; **while still inside the same
  outer `atomic()` block**, runs a real, unmocked `User.objects.filter(
  pk=user.pk).exists()` query and asserts it succeeds (this is the
  specific assertion that fails with `InFailedSqlTransaction`/
  `TransactionManagementError`-shaped errors without the fix, and passes
  cleanly with it); after the outer transaction closes normally, asserts
  the user is genuinely authenticated (`SESSION_KEY` present), the marker
  survived with its exact original id/form_type, and no `FormDraft` was
  created; then, on the same connection with no mock active, calls
  `consume_pending_demo_selection` again for a real retry and confirms
  the snapshot attaches successfully. `leads.test_demo_handoff` +
  `leads.test_form_draft` on PostgreSQL: 106 tests, all passing (the new
  test plus all of `2cd1032`'s and earlier phases' tests, none skipped —
  every SQLite-skip-guarded test runs for real here). `leads` app on
  SQLite: 118 tests total (up from 117 at `2cd1032` by exactly this one
  new test, which correctly skips there), 7 skips unchanged (SQLite
  cannot force a genuine server-side transaction abort). `accounts` app:
  73 tests, all passing (2 skips) — confirming no regression in
  registration, login, phone verification, or email verification. Full
  project suite (SQLite): 666 tests total, 655 passed, 11 correctly
  skipped (all PostgreSQL-only; up from 665 total/10 skips at `2cd1032`
  by exactly this one new test). `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected" — no model or
  migration change), and `git diff --check` (clean) all passed.
- **V2.1-B2 second corrective — PostgreSQL evidence:** run against the
  same isolated local PostgreSQL 16 `test_arvion_ci_local` database used
  throughout this project (never the permanent `arvion_ci_local`). The
  new `RealTransactionErrorDuringLookupRecoveryTests` test was run once,
  then 5 additional repeats — all clean. `leads.test_demo_handoff` +
  `leads.test_form_draft` together (106 tests) also passed cleanly on the
  same database. The `assessments/services.py` PostgreSQL incompatibility
  found during the V2.1-B2 phase (`revoke_assessment_access`'s
  `select_for_update()` on an outer join) remains **present, unrelated,
  and untouched by any commit in this session** — recorded again here so
  it is never lost or quietly dropped from the project record; it still
  needs separate human prioritization.
- **V2.1-B2 second corrective — migration status:** none created or
  needed; `makemigrations --check --dry-run` reported "No changes
  detected." No model or schema change — this phase touched only
  `leads/demo_handoff.py` and `leads/test_demo_handoff.py`.
- **Git boundary (current, accurate as of this phase's own commit):**
  `main` is sixteen commits ahead of `origin/main` — the fifteen listed
  above, plus this V2.1-B2 second corrective commit. No prior commit is
  amended.
- **Prior phase's change (kept for reference; unaffected by this
  design-only phase; one function in one file):** `writeDemoContext` in
  `core/static/core/js/wizard-engine.js` now clears the one-shot
  `sessionStorage` redirect guard (`demoRedirectGuardKey`) immediately
  after it successfully persists a validated demo pointer. Root cause: the
  guard was only ever cleared by `clearDemoContext()` (the failure/decline/
  clear paths), never by the success path — so after the *first* automatic
  reconstruction succeeded, the guard stayed at `"1"` in that tab's
  `sessionStorage` forever, silently disabling every later reconstruction
  attempt in the same tab. The fix is scoped to exactly the success case:
  `writeDemoContext` is the single function that represents "a valid,
  consented demo pointer now exists for this page," called both from the
  top-of-wizard sync block (after a direct or reconstructed `?demo=` visit
  resolves) and from the consent-accept handler — clearing the guard there
  covers both call sites without duplicating the fix. The guard is
  untouched (stays set, correctly preventing a second attempt) for as long
  as the outcome of a redirect is still undetermined, and was already
  correctly cleared by `clearDemoContext()` on every failure/decline/clear
  path — so this fix only affects the previously-broken success path.
- **Test level (P1 fix phase, unaffected by V2.1's design-only work):**
  `leads` + `projects` = 33 tests, all still passing
  (unchanged from the prior phase — no new Python-testable surface; this
  fix is entirely inside a client-side JS function). Verified empirically
  with the browser-automation skill against a throwaway local dev server
  (disposable DemoTemplate/DemoSelection/session created via `manage.py
  shell`, deleted afterward; no migration run — the dev DB was already
  fully migrated): (الف) valid link + consent → bare URL → first
  reconstruction succeeds, guard reads back as absent (`null`) immediately
  after; (ب) same tab, bare URL visited a **second** time → reconstruction
  succeeds again (this is the exact case that was broken before the fix);
  a **third** visit also succeeded, confirming stability rather than a
  one-off; (ج) a bogus/foreign token → neutral message shown, demo pointer
  cleared, general draft (`rvion-draft:leads-contact`) confirmed still
  present and unchanged, and a bare-URL revisit afterward stayed bare (no
  stale-pointer resurrection, no loop); (د) no consent ever granted → demo
  pointer never written, bare-URL visit stays bare; consent granted then
  the pointer backdated 8 days (expired) → bare-URL visit stays bare and
  the expired pointer is cleared. `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected"), and
  `git diff --check` (clean) all passed.
- **Prior phases, kept for reference:** `b3952a4` added the same-device
  `?demo=` reconstruction feature this phase fixes a defect in — the
  leads-contact form's existing localStorage draft mechanism can
  reconstruct a lost `?demo=` link on the same device/session, entirely
  opt-in and scoped by `wizardName === "leads-contact"` so CRM/Clinic
  wizards are untouched; the token is never server-rendered into the DOM,
  only a safe bilingual label (`data-demo-label`); server-side session
  validation (`_session_demo_selection`) is unmodified; an invalid/foreign
  token clears only the dedicated demo pointer, never the general draft;
  a genuinely-expired (>7 days) draft shows a dismissible message instead
  of vanishing silently. See git history on
  `core/static/core/js/wizard-engine.js`, `leads/views/contact.py`, and
  `leads/templates/leads/contact.html` for full detail if needed again.
  `777acf9` mirrored a Lead's demo choice onto its `CustomerCase` as a
  structured, bilingual, frozen `CaseDocument` snapshot, reusing the
  existing case/document/revision/activity machinery with no new model —
  see git history for detail if needed again. `fbe3320` added a
  dry-run-by-default
  `cleanup_demo_selections` management command (deletes only
  `DemoSelection` rows both unattached to any Lead and stale past a
  configurable retention window, `--apply` required for a real delete) and,
  as a P2 fix, moved `CATEGORY_LABELS_EN`/`demo_config_labels` into a
  neutral `projects/demo_labels.py`. `af6e0ac` added a bilingual "Demo
  selection" card and list filter/indicator to the request-list/detail
  dashboard pages. Before that, two P1s in the demo-to-enquiry hand-off
  were corrected and empirically verified (stale-token resubmit recovery;
  `IntegrityError` recovery safe under `ATOMIC_REQUESTS = True`). See git
  history on `projects/views/projects.py` (`DemoConfigureView`) and
  `management_portal/cases.py` for full detail if needed again.
- **Last commit:** this V2.1-B2 second corrective phase's own commit
  (see `git log`) — a separate commit on top of `2cd1032`, which is not
  amended.
- **Next action:** V2.1-B1 (both corrective phases included), V2.1-B2,
  and both V2.1-B2 corrective phases are all done and fully verified — a
  visitor's demo selection now reliably
  survives login/registration and lands on their account's `FormDraft` as
  a safe snapshot, and an already-authenticated customer gets the same
  sync immediately on the contact page. Still missing before this feature
  is customer-visible: an auto-save endpoint for `fields`/`current_step`
  as the visitor progresses through the wizard, a restore/delete UI on
  the contact page and account dashboard, and the atomic final-submission
  step (`FormDraft` → `Lead`, `open`/`submitting` → `submitted`,
  `submitted_lead` set) — all still Phase B3/C/D, per the original V2.1
  plan, and still gated on the explicit human decisions flagged under
  "V2.1 — decisions requiring explicit human approval" above (free-text/
  contact-info consent layer, final `FormDraft` retention confirmation —
  7 days is now implemented and now actually reachable via login, not
  just proposed — whether to nudge guests to sign in, and
  `cleanup_demo_selections`/`cleanup_form_drafts` scheduling), plus the
  still-deferred session/ownership authorization check on which
  `DemoSelection` a caller may attach via `attach_demo_snapshot`/
  `ensure_active_draft_with_demo_snapshot` directly (not a concern for the
  two hand-off paths built in this phase, both of which only ever pass in
  a selection already validated by `_session_demo_selection`'s own
  session-key match). One **unrelated, pre-existing** issue was found
  incidentally while regression-testing this phase's changes on
  PostgreSQL — `assessments/services.py`'s `revoke_assessment_access`
  cannot run its `select_for_update()` query on PostgreSQL due to an
  outer join from `select_related("attempt")` — flagged for a human to
  prioritize separately; it does not block this phase and was not touched
  here. The earlier, separate V2 idea (a time-boxed, signed
  continuation link) remains superseded by the login-based approach unless
  explicitly reopened. Resumable order drafts beyond leads-contact
  (CRM/Clinic) remain `NOT_STARTED`. Re-run the release gate on the exact
  deployable revision before any production action, including applying
  `0004_activesession` and `0006_formdraft_and_more` to any real database.

## Phase ledger

| Phase | Status | Evidence |
| --- | --- | --- |
| Single-primary-agent alignment | `VERIFIED` | Framework workflow/recovery/test/stop guides read; local `AGENTS.md` replaced with the real single-agent instructions; no active delegated work existed. |
| Interactive demo customizer (`06812d2`) | `VERIFIED` (local) | Targeted tests, route probes, diff/migration checks, and browser flow passed. |
| Pre-design and ordering discovery | `VERIFIED` | Current demo-to-lead flow, session boundary, existing controls, data gaps, and operator visibility were mapped without changing production code. Customer matching uses normalized exact phone/email, not fuzzy matching. |
| Reliable hand-off from demo to enquiry | `VERIFIED` (local) | Both P1s from the prior `PARTIAL` checkpoint were corrected and empirically verified — the ATOMIC_REQUESTS failure was reproduced before the fix and re-checked after it. Full targeted suite (26 tests), `check`, migration dry-run and `git diff --check` all passed. Not pushed, deployed, or migrated on production. |
| Structured display of demo selection in the management dashboard (`af6e0ac`) | `VERIFIED` (local) | 158-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. Not pushed, deployed, or migrated on production. |
| Lifecycle and safe cleanup of abandoned demo selections (`fbe3320`) | `VERIFIED` (local) | 164-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. `--apply` never run outside the test database. Not pushed, deployed, or migrated on production. |
| Structured customer-case hand-off (`777acf9`) | `VERIFIED` (local) | 172-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change; reused the existing CaseDocument/CaseDocumentRevision/CaseActivity machinery end to end. Not pushed, deployed, or migrated on production. |
| Resumable order drafts — design report | `VERIFIED` | Compared 4 options (local-only, server draft for logged-in users, signed continuation link, staged combination) across security/privacy/complexity/recovery; recommended a staged V1→V2 path; flagged server-side contact storage and sending a link to the customer as decisions needing explicit human approval. Design only, no code changed. |
| Resumable order drafts — V1 (same-device continuation) (`b3952a4`) | `VERIFIED` (local), P1-corrected | Initially verified, then found `PARTIAL` when a P1 surfaced (permanent redirect guard, see next row); superseded by the P1 fix phase below, now `VERIFIED` again. |
| Resumable order drafts — V1 P1 fix (permanent redirect guard) | `VERIFIED` (local) | See "This phase's change" and "Test level" above. One-line root cause, one-function fix (`writeDemoContext` now clears the one-shot guard on success). `leads`+`projects` (33 tests) still pass; `check`, migration dry-run (no migration run), and `git diff --check` all passed. Browser-verified: two consecutive same-tab reconstructions both succeed (the exact case that was broken); invalid/foreign token still clears only the demo pointer with no loop; no-consent and expired-storage cases still never reconstruct. `b3952a4` was not amended; this is a separate corrective commit. |
| Resumable order drafts — V2 (signed continuation link) | `NOT_STARTED` | Superseded by the definitive product decision behind V2.1 (login-based cross-device drafts + single active session per account); not going to be built unless explicitly reopened. |
| Resumable order drafts — V2.1 design (login-based cross-device drafts + single session) | `VERIFIED` (design-only) | Read `accounts.User`/login-logout/password-reset/middleware/session backend and the `DemoSelection` session-bound flow in full. Decided delete-on-login single-session enforcement (fail-closed, reuses the existing `select_for_update()` race-safety pattern from `PhoneVerificationView`) over a version/registry counter (fail-open). Designed the `FormDraft` data contract, the privacy boundary (no free text/contact info by default; separate consent required), bilingual UX flows for all 6 named scenarios, a 5-phase implementation plan (foundation → draft model → UI → atomic submission → tests/release) each with its own migration/tests/rollback/risk, and 5 explicit human-approval decisions. No code, migration, or commit made. |
| Resumable order drafts — V2.1-A (single-session foundation) (`08bd910`) | `VERIFIED` (local), corrected | Initially verified, then found `PARTIAL` (unconditional write lock on every request; non-atomic courtesy marker) — see the corrective-phase row below, which fixes and re-verifies it. |
| Resumable order drafts — V2.1-A corrective (fast path + atomic marker + legacy-race PostgreSQL proof) | `VERIFIED` (local) | See "V2.1-A corrective phase" entries above. Fast lock-free path for the matching-session case; only a mismatch pays for `select_for_update(User)`, with a re-check under the lock. Courtesy marker consumed atomically via `cache.delete()`'s return value. Closed the previously-missing legacy-session PostgreSQL race test (6 runs, all clean). 6 new `SingleSessionTests` + 1 new PostgreSQL test (23 + 3 total in those classes), `accounts`+`core` (147 tests), and the full 560-test project suite all pass. `check`, migration dry-run (no migration needed or made), and `git diff --check` all passed. `08bd910` not amended. |
| Resumable order drafts — V2.1-B1 (`FormDraft` model + service + demo-snapshot relocation) (`537c9a2`) | `VERIFIED` (local), corrected | Initially verified, then found `PARTIAL`: arbitrary caller-supplied `demo_snapshot` accepted verbatim; ordinary field saves silently wiped an existing snapshot; `get_active_draft` wrote on read, racing `upsert_active_draft`; validation errors leaked raw attacker-controlled values/keys. See the corrective-phase row below, which fixes and re-verifies it. |
| Resumable order drafts — V2.1-B1 first corrective (safe snapshot attach/clear, read-only expiry check, opaque validation errors, single retention constant) (`0e1a208`) | `VERIFIED` (local), corrected again | Initially verified, then found `PARTIAL` a second time (see the second-corrective row below): attach/clear did not extend `expires_at`; an expired-draft status transition could be rolled back by a same-transaction `DraftValidationError`; `attach_demo_snapshot` trusted the caller's in-memory `DemoSelection` instead of re-reading it; snapshot validation checked only the key set, not each value's type/length. Also contained a documentation bug (own note, not a code defect): its "test level" entry misstated `leads.test_form_draft`'s result as "47 passed, 3 skips" when the correct breakdown is 47 total = 44 passed + 3 skips — corrected in place above and in this ledger row's own text. `attach_demo_snapshot`/`clear_demo_snapshot` replace raw `demo_snapshot=` passthrough (with a fixed 12-key snapshot-shape allowlist check before every write); `upsert_active_draft` preserves an existing snapshot by default; `get_active_draft` is fully read-only (no UPDATE, no `select_for_update` — proven directly via `CaptureQueriesContext` + a patched `select_for_update` that raises if called); `DraftValidationError` messages are fixed, opaque, code-tagged strings with no raw value/key interpolation; `DRAFT_RETENTION_DAYS` now lives in one place (`leads/models/form_draft.py`), imported by the service. 16 new tests + 1 updated test in `leads.test_form_draft` (47 tests total: 44 passed, 3 skips), `leads`+`projects`+`management_portal` (220 tests, 3 skips), full project suite (607 tests total: 601 passed, 6 skips — all PostgreSQL-only). New PostgreSQL regression test `test_concurrent_expired_read_cannot_clobber_a_racing_renewal` (1 run + 5 repeats, all clean) alongside the 2 pre-existing race tests. `check` (0 issues), migration dry-run ("No changes detected" — no new migration), and `git diff --check` (clean) all passed. `537c9a2` not amended. |
| Resumable order drafts — V2.1-B1 second corrective (retention on attach/clear, expired-transition commit ordering, distrustful DemoSelection reload, full snapshot value validation) | `VERIFIED` (local) | See "V2.1-B1 second corrective" entries above. `attach_demo_snapshot`/`clear_demo_snapshot` now extend `expires_at` by exactly 7 days on success; the `no_active_draft` rejection is raised only after the write transaction has committed, so a concurrently-discovered expiry transition always survives; `DemoSelection` is always re-read fresh from the database by pk (with `select_related("template")`) before a snapshot is ever built from it, so a locally mutated or since-deleted instance can never leak into a stored snapshot; snapshot validation now checks every value's type and length and requires the two feature lists to match in length, not just the key set. 11 new tests (9 in `DemoSnapshotAttachClearTests`, 2 new PostgreSQL-only race tests), `leads.test_form_draft` (58 tests total: 53 passed, 5 skips), `leads`+`projects`+`management_portal` (231 tests, 5 skips), `management_portal.tests.DemoSelectionCaseHandoffTests` re-run explicitly (8 tests, unchanged), full project suite (618 tests total: 610 passed, 8 skips — all PostgreSQL-only). 2 new PostgreSQL race tests plus the 3 pre-existing ones (5 total), run once plus 5 additional repeats, all clean. `check` (0 issues), migration dry-run ("No changes detected" — no new migration), and `git diff --check` (clean) all passed. Neither `537c9a2` nor `0e1a208` amended. |
| Resumable order drafts — V2.1-B2 (pre-login session marker + login-signal hand-off + already-authenticated sync, both into `FormDraft`) (`757f7a4`) | `VERIFIED` (local), corrected | Initially verified, then found `PARTIAL`: the `DemoSelection` fetch in `leads/signals.py` sat outside any `try`/`except`, so a transient `DatabaseError` there would have turned a real login into a 500; and the documented "retries on the customer's next authenticated request" claim had no actual retry code behind it anywhere. See the corrective-phase row below, which fixes and re-verifies both. |
| Resumable order drafts — V2.1-B2 first corrective (safe DemoSelection-fetch orchestration + real contact-page retry path) (`2cd1032`) | `VERIFIED` (local), corrected again | Initially verified, then found `PARTIAL` a second time: the fetch's `try`/`except` did not wrap the query in a `transaction.atomic()`, so a genuine PostgreSQL error there aborted the outer `ATOMIC_REQUESTS` transaction without ever being rolled back to a savepoint — the next query in the same request would fail with `InFailedSqlTransaction`/`InternalError`. See the second-corrective row below, which fixes and re-verifies it with a real, reproduced-then-fixed PostgreSQL test. New `leads.demo_handoff.consume_pending_demo_selection` is the single safe orchestration (pop → staff-check → fetch → attach, restoring the marker only on a presumed-transient failure) shared by the login receiver (now a 2-line trigger) and the new `maybe_retry_pending_demo_selection`, wired into `LeadCreateView._resolved_demo_selection()` only when there is no explicit `?demo=` at all. An explicit, valid `?demo=` still always wins and now also clears any stale old marker on success; an explicit invalid/foreign one still never falls back to the old marker. `handle_resolved_demo_selection` gained a second `except Exception` so a transient error there can no longer 500 the contact page either. 10 new tests, `leads` app (117 tests total: 110 passed, 7 skips), `accounts` (73 tests, 2 skips), full project suite (665 tests total: 655 passed, 10 skips). `757f7a4` not amended. |
| Resumable order drafts — V2.1-B2 second corrective (wrap the DemoSelection lookup in its own transaction.atomic() so a real PostgreSQL error there can never poison the outer ATOMIC_REQUESTS transaction) | `VERIFIED` (local) | See "V2.1-B2 second corrective" entries above. The lookup query in `consume_pending_demo_selection` now runs inside its own `with transaction.atomic():`, with the `try`/`except` kept outside that block, so a real database error there triggers Django's own savepoint rollback before the exception is caught — leaving the surrounding request transaction (login/registration under `ATOMIC_REQUESTS`) fully usable afterward. The bug was reproduced first (temporarily reverting the fix made the new test fail with exactly `InternalError: current transaction is aborted`), then the fix was restored and the same test re-verified passing. New PostgreSQL-only `RealTransactionErrorDuringLookupRecoveryTests`, kept alongside (not replacing) `2cd1032`'s existing attach-step `RealTransactionErrorRecoveryTests`: forces a real `SELECT 1/0` at the exact lookup call site inside an outer `transaction.atomic()` standing in for `ATOMIC_REQUESTS`, proves a real query immediately afterward inside the same outer transaction still succeeds, proves the user is authenticated, the marker survives intact, no `FormDraft` is created, and a subsequent real retry on the same connection attaches the snapshot successfully. Run once plus 5 repeats on the same isolated local PostgreSQL 16 `test_arvion_ci_local` database (never the permanent one) — all clean. `leads.test_demo_handoff`+`leads.test_form_draft` on PostgreSQL: 106 tests, all passing. `leads` app on SQLite: 118 tests (7 skips); `accounts`: 73 tests (2 skips) — no regression in registration/login/phone-verification/email-verification. The unrelated, pre-existing `assessments/services.py` PostgreSQL incompatibility remains flagged, unfixed, and not hidden. `check` (0 issues), migration dry-run ("No changes detected"), and `git diff --check` (clean) all passed. `2cd1032` not amended. |
| Resumable order drafts — V2.1 Phases B3–E (auto-save endpoint, draft restore/delete UI, atomic final submission) | `NOT_STARTED` | Requires explicit human approval on the still-open decisions above before Phase B3 begins; depends on the now-`VERIFIED` Phase B1+B2 foundation. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
