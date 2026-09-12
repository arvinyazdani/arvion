# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** V2.1-A corrective — remove the write lock from the
  normal per-request path and make the courtesy-message marker
  consumption atomic (fixing two defects found in the just-committed
  `08bd910`).
- **Last verified phase (code):** this corrective phase, on top of the
  V2.1-A single-session foundation (`08bd910`).
- **Status:** `VERIFIED` (local). `08bd910` was initially `VERIFIED` for
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
- **Git boundary:** `main` will be ten commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, `af6e0ac`,
  `fbe3320`, `777acf9`, `b3952a4`, `a4cb60b`, `08bd910`, and this
  corrective phase's own commit) once committed below. `08bd910` is not
  amended — this is a separate commit on top of it.
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
- **Last commit:** this corrective phase's own commit (see `git log`) — a
  separate commit on top of `08bd910 feat: enforce one active session per
  customer account`, which is not amended.
- **Next action:** Phase A (single-session foundation) of the V2.1 plan is
  now done, corrected, and fully verified (including the previously-
  missing legacy-session PostgreSQL race proof). Await explicit human
  decisions on the
  still-open items from the design record below (free-text/contact-info
  consent layer, `FormDraft` retention period, whether to nudge guests to
  sign in, and `cleanup_demo_selections`/`cleanup_form_drafts`
  scheduling) before starting Phase B (`FormDraft` model + demo-selection
  snapshot integration). No `FormDraft` model, form-save wiring, or draft
  UI exists yet — do not assume otherwise from the "V2.1-A" name. The
  earlier, separate V2 idea (a time-boxed, signed continuation link)
  remains superseded by the login-based approach unless explicitly
  reopened. Resumable order drafts beyond leads-contact (CRM/Clinic)
  remain `NOT_STARTED`. Re-run the release gate on the exact deployable
  revision before any production action, including applying
  `0004_activesession` to any real database.

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
| Resumable order drafts — V2.1 Phases B–E (`FormDraft`, demo hand-off, draft UI, atomic submission) | `NOT_STARTED` | Requires explicit human approval on the open decisions above before Phase B begins; depends on the now-`VERIFIED` (and corrected) Phase A foundation. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
