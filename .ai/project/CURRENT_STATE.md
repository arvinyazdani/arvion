# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** V2.1-E2 corrective and production release.
  **`VERIFIED` and deployed.** The release audit's sole P1 blocker is
  closed: the login signal no longer physically deletes a competing
  session while its response may still be saving. `ActiveSession` remains
  the server-side authorization boundary, and `SingleSessionMiddleware`
  rejects and flushes the losing session before its next view runs. This
  preserves the one-valid-device rule without Django's intermittent
  `UpdateError`/HTTP 500. Evidence: 21/21 focused SQLite tests; both real
  PostgreSQL concurrency tests; the formerly flaky login race repeated
  30/30 times; and the full 73-test accounts suite on PostgreSQL, all
  passing. No migration was created for the corrective itself. The full
  826-test local release gate passed, then GitHub Actions run
  `34958047474` passed on both Python 3.11 and 3.12 with PostgreSQL.
  Production was snapshotted and released at `79ad24d`; all five queued
  additive migrations applied, static assets collected, services/timers
  enabled, public health and six critical public routes returned HTTP 200,
  and no post-release error/5xx appeared in the service journal.
- **V2.1-E1 — historical recap (superseded as the "current phase"; kept
  for reference):** `cleanup_form_drafts`, a safe, batch-safe management
  command that deletes `FormDraft` rows only once ALL FOUR hold:
  `status="expired"`, `expires_at` older than the retention window
  (default 30 days), `submitted_lead IS NULL`, and `submission_token IS
  NULL`. Dry-run by default; `--apply` required to delete;
  `--older-than-days`/`--batch-size` (defaults 30/500) are validated as
  positive integers before any write, raising `CommandError` otherwise.
  Deletion re-applies the full eligibility filter at delete time (never
  bare `pk__in`), so a draft that stops being eligible between
  batch-selection and delete survives. Output prints only the aggregate
  count and a plain-language policy description — no owner, email, id,
  `fields`, `demo_snapshot`, or token ever appears. No model, migration,
  `FormDraft` lifecycle code, cron/Celery Beat schedule, or UI was added
  or changed; `cleanup_demo_selections` untouched.
- **V2.1-E0 — historical recap (kept for reference):** fixes the
  pre-existing PostgreSQL
  incompatibility in `assessments.services.revoke_assessment_access`,
  flagged and left unfixed since V2.1-B2. Unrelated to the V2.1
  leads-contact/FormDraft line; this is the assessments/exam-entitlement
  domain. Root cause: `ExamEntitlement.objects.select_for_update()
  .select_related("attempt")` builds a `LEFT OUTER JOIN` to `Attempt`
  (a `OneToOneField` an entitlement may not have a row for), and
  PostgreSQL refuses `FOR UPDATE` on the nullable side of an outer join
  — reproduced first with the exact command supplied, which failed with
  `FeatureNotSupported: FOR UPDATE cannot be applied to the nullable
  side of an outer join`, then fixed by locking the entitlement without
  `select_related` and fetching/locking the `Attempt` via its own,
  independent `select_for_update()` query. No migration; behavior for
  every existing caller unchanged.
- **V2.1-C2 corrective — historical recap (superseded as the "current
  phase"; kept for reference):** closes a language-isolation defect in
  the account dashboard's order-draft card.
  `order_draft.demo.brand` (the one `demo_snapshot` field that was
  never bilingual — it can fall back to the template's Persian
  `fictional_brand_fa` regardless of which language is rendering) was
  appended to the "Reference demo" row in both languages, so an
  English-rendered card could show a Persian brand name — breaking the
  "no Persian text in the English UI" guarantee. Fixed by removing
  `brand` entirely from `leads.draft_dashboard.DraftDemoSummary`, its
  required-keys check, and the template's demo row, which now shows
  only the fully bilingual `template_title_*`/`category_*` pair. A
  legacy snapshot with only those two bilingual pairs (no `brand` key
  at all) still renders correctly. No `demo_snapshot` schema, snapshot
  builder, model, migration, order form, or management page was
  touched.
- **V2.1-C2 — historical recap (superseded as the "current phase"; kept
  for reference):** the account dashboard's safe, read-only "order
  draft" section. `accounts.views.dashboard` calls the existing
  `leads.form_draft_service.get_active_draft` (owner-scoped, read-only,
  excludes expired/submitted) and passes it through a new, small, pure
  view-model builder — `leads.draft_dashboard.build_draft_dashboard_card`
  — that returns only allowlisted, already-translated values (current
  step, progress, last-saved/expiry, the four allowlisted choice fields,
  the selected service's title, and the demo's name/category from the
  frozen `demo_snapshot` only) and never a raw `FormDraft`,
  `submission_token`, draft/owner id, or `revision`. `accounts/
  templates/accounts/dashboard.html` gained a new draft card (shown only
  when an active draft exists, positioned before the assessments panel)
  and a new "Project enquiry" `account-compass` entry (an anchor to the
  card when a draft exists, a direct link to `leads:contact` otherwise);
  the sidebar gains a "browse demos" link only in the no-draft state. No
  `FormDraft` write path, finalize/idempotency/rate-limit/`on_commit`
  logic, or migration was touched. (This recap originally also listed
  `brand` as part of the demo summary — corrected by the phase above.)
- **V2.1-D corrective — historical recap (superseded as the "current
  phase"; kept for reference):** two review findings against the
  `7e5e621` implementation, fixed. P1: the replay-identity comparison
  (`_lead_matches_this_submission`, formerly `_lead_matches_cleaned_data`)
  did not include `demo_selection_id`, so a reused token with identical
  form content but a different (or added, or removed) demo selection
  could have been wrongly accepted as a valid replay of the original
  `Lead` instead of being rejected as a conflict — fixed by folding
  `demo_selection_id` into both sides of the canonical signature and
  passing the caller's resolved `demo_selection` through every replay
  comparison, initial lookup and `IntegrityError` recovery alike. P2: the
  `except IntegrityError` recovery branch treated "no record found for
  this owner" the same as "a real content conflict"
  (`SubmissionConflictError`) — wrong, since "nothing found for this
  owner" means the collision's winner belongs to a different owner
  entirely; fixed to raise `InvalidSubmissionTokenError` in that case
  instead, identical in outward behavior to any other invalid/foreign
  token, with a real PostgreSQL test forcing a genuine two-owner unique-
  constraint race to prove it. The underlying V2.1-D design, schema, and
  token-carriage contract are unchanged — see "V2.1-D — implemented and
  verified" below for that context, which remains accurate except for
  the two corrected functions.
- **V2.1-C1 second corrective — historical recap (superseded as the
  "current phase"; kept for reference):** this time a working
  browser session was available, and 6 real defects found by review of
  `3b8fb71` were fixed and then genuinely exercised live: (1) **P1** —
  `base.html` still served `site.css?v=38`/`wizard-engine.js?v=3`, stale
  relative to `bef7d45`/`3b8fb71`'s own edits to those files — bumped to
  `v=39`/`v=4`; (2) **P1** — a successful save/conflict-resolution
  response with `{"draft": null}` (a shape only valid for GET/409) could
  still reach `.revision`/`.fields` in `queueServerSave()`/
  `handleConflict()`'s two POST handlers/the state-C/D import/use-device
  handlers — fixed with a new `safeSavedDraft()` (rejects `draft: null`)
  used at all five save-success call sites, `safeDraft()` itself kept
  unchanged for GET/409; (3) **P1** — `performDelete()` treated *any*
  200/201 as a successful delete without checking the body at all — fixed
  with `safeDeleteResult()` (requires a real `deleted: boolean`); (4)
  **P2** — field-value validation only checked type, not that a value
  actually matches one of that `<select>`'s real options — fixed by
  comparing against each field's live option set
  (`fieldOptionValues`), rejecting anything unknown/oversized regardless
  of type; (5) **P2** — rapid typing while an autosave retry was already
  backoff-scheduled could fire a fresh attempt per keystroke, burning
  through all 5 retries in seconds instead of over the intended ~112s
  window — fixed with a `saveRetryTimer !== null` guard so only `state
  .dirty` is set while a retry is pending, never a second real attempt;
  (6) `formatSavedAt` hardened to reject an invalid `updated_at` before
  ever formatting it. See "V2.1-C1 second corrective" below for fix
  detail and the live-browser evidence — this time genuinely run (guest
  flow, all 4 reconciliation states, malformed GET/save/409/delete, a
  real 401 via server-side session expiry, a real 403 via a mid-session
  staff promotion, real offline/reconnect with the single-flight fix
  proven by request count, validation rerender, fa/en, 320/390 in both
  themes, CRM/Clinic smoke, zero uncaught console errors throughout).
  Status: `VERIFIED` (local) — the two prior blockers (an unrelated
  `page.setContent` probe that never ran page JS, giving a false
  "browser is broken" reading; and a mid-session environment reset) are
  resolved; this phase's evidence comes from real navigation, real
  server responses, and one genuine tool limitation (`page.route()`
  interception needed the reconciliation banner clicked through first
  before it reliably matched requests — a timing issue in the test
  script, not the product) plus one inconclusive check (keyboard Enter
  activating a focused `<button>` did not register through this specific
  automation tool despite confirmed DOM focus — tab *order* was verified
  correct; Enter-activation relies on unmodified native `<button>`
  semantics the code never overrides, so this is recorded as unconfirmed
  tooling, not a suspected defect). See "V2.1-C1 second corrective —
  what was not fully confirmed" below for that one honest gap.
- **V2.1-B3 corrective — historical recap (superseded as the "current
  phase"; kept for reference):** a P2 lifecycle bug in
  `save_draft_fields` found right after `57a6be8` shipped: when the
  active draft `_get_active_draft_locked` finds turns out to be expired,
  it transitions it to `"expired"` (bumping `revision`) as a write inside
  the same `transaction.atomic()` block `save_draft_fields` itself is
  running in. If the caller's `expected_revision` was then non-zero (they
  believed *some* draft existed), the old code raised
  `DraftConflictError(None)` **from inside that same atomic block** — an
  exception propagating out of `transaction.atomic()` rolls back
  everything written inside it, so the expiry transition that should
  have survived was undone. `57a6be8`'s own final report incorrectly
  claimed this transition was not rolled back in this case; it was.
  `57a6be8`'s own regression test
  (`test_expired_draft_requires_expected_revision_zero_to_recreate`)
  never caught this because it performed a *second* save immediately
  after the conflict — which itself re-expired the row — before ever
  inspecting the database, masking whether the first call's own
  transition had committed. Fixed and verified with a test that inspects
  the row immediately after the conflict, before any second save — see
  "V2.1-B3 corrective" entries below. Status: `VERIFIED` (local).
- **Last verified phase (code):** V2.1-B3 corrective, on top of V2.1-B3
  (`57a6be8`), the V2.1-B2 third corrective phase, the V2.1-B2 second
  corrective phase (`1baf584`), the V2.1-B2 first corrective phase
  (`2cd1032`), V2.1-B2 (`757f7a4`), the V2.1-B1 second corrective phase,
  the V2.1-B1 first corrective phase (`0e1a208`), V2.1-B1 (`537c9a2`),
  the V2.1-A corrective phase, and `08bd910`.
- **V2.1-B3 — historical recap (superseded as the "current phase"; kept
  for reference):** the first account-bound, versioned HTTP API for
  `FormDraft`: `GET`/`POST` on `leads:draft` (read the customer's current
  `leads_contact` draft; race-safe, optimistic-concurrency create-or-
  update of its `fields`/`current_step`) and `POST` on
  `leads:draft_delete` (race-safe, revision-checked hard delete). No UI,
  JavaScript, template change, auto-save wiring, or `FormDraft`→`Lead`
  conversion in that phase — server-side infrastructure only. A new
  `FormDraft.revision` (`PositiveBigIntegerField`, additive migration
  `0007_formdraft_revision`) is the optimistic-concurrency counter every
  write path in `leads/form_draft_service.py` maintains, and a new
  `DraftConflictError` carries the current, canonical, owner-scoped
  draft for building a 409 response — see "V2.1-B3" entries below for
  what it built; see "V2.1-B3 corrective" entries for the one defect
  found in it since.
- **V2.1-B2 third corrective — historical recap (superseded as the
  "current phase"; kept `VERIFIED` and untouched by this phase):**
  `1baf584` (the second corrective phase) correctly wrapped the *first*
  `DemoSelection` lookup (inside
  `leads.demo_handoff.consume_pending_demo_selection` itself) in its own
  `transaction.atomic()`. The overall V2.1-B2 feature had then shipped
  `PARTIAL` even after `1baf584`, because a **second**, separate
  `DemoSelection` lookup in the same call chain
  (`leads.form_draft_service._reload_demo_selection`, reached via
  `ensure_active_draft_with_demo_snapshot`) had the identical
  unwrapped-query problem — a genuine PostgreSQL error there aborted the
  underlying transaction and, under `ATOMIC_REQUESTS=True`, left the
  *outer* request transaction needing a rollback. Reproduced empirically,
  then fixed in `afde089` by wrapping that second lookup's query in its
  own `transaction.atomic()` too. The overall V2.1-B2 feature (original
  plus all three corrective phases) has been `VERIFIED` as a whole since
  `afde089`, and none of that work is touched or re-litigated here.
- **V2.1-B2 second corrective — historical recap, kept `VERIFIED` and
  untouched by this phase:** `2cd1032` (the first corrective phase) added
  a `try`/`except` around the first `DemoSelection` lookup, but never
  wrapped the query itself in `transaction.atomic()` — under
  `ATOMIC_REQUESTS=True`, a genuine PostgreSQL error there aborted the
  outer request transaction without ever being rolled back to a
  savepoint. Fixed in `1baf584` by wrapping only that lookup query in its
  own `transaction.atomic()`, with the `try`/`except` kept outside that
  block. Proven with a real, reproduced-then-fixed PostgreSQL test
  (`RealTransactionErrorDuringLookupRecoveryTests`). This fix and its
  test are **unchanged and still fully correct** — this phase only adds
  the equivalent fix for the *second*, previously-unaddressed lookup.
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
  `transaction.atomic()`, fixed in the second corrective phase above —
  and that second corrective phase's own fix, in turn, did not extend to
  the *second*, separate lookup inside `_reload_demo_selection`, which is
  exactly the gap this third corrective phase closes.
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
- **Git boundary (as of `1baf584`, historical — see the accurate,
  up-to-date count directly below):** `main` was sixteen commits ahead of
  `origin/main` at that point — the fifteen from the prior entry, plus
  `1baf584`. No prior commit was amended.
- **V2.1-B2 third corrective — root cause and fix:** `leads/form_draft
  _service.py`'s `_reload_demo_selection(demo_selection)` — shared by
  both `ensure_active_draft_with_demo_snapshot` (the only caller reached
  from the login-signal and already-authenticated hand-off paths) and
  `attach_demo_snapshot` — did:
  ```python
  if not isinstance(demo_selection, DemoSelection) or demo_selection.pk is None:
      return None
  return DemoSelection.objects.select_related("template").filter(pk=demo_selection.pk).first()
  ```
  with no `transaction.atomic()` around the query. This is the exact same
  class of bug `1baf584` fixed for the *first* lookup, just one call
  deeper: a genuine PostgreSQL error here aborts the database transaction
  at the server level; the calling code's own `try`/`except` (already
  present in `leads.demo_handoff.consume_pending_demo_selection`, from
  the first corrective phase, wrapping the whole
  `ensure_active_draft_with_demo_snapshot(...)` call) catches the Python
  exception, but without a savepoint to roll back to, the *outer*
  `ATOMIC_REQUESTS` transaction was left needing a rollback anyway.
  Fixed by wrapping only the query in its own `transaction.atomic()`,
  letting a real error propagate out of that block (never swallowed
  inside it) so Django's own machinery rolls back to that block's
  savepoint before the exception ever reaches a caller:
  ```python
  if not isinstance(demo_selection, DemoSelection) or demo_selection.pk is None:
      return None
  with transaction.atomic():
      return DemoSelection.objects.select_related("template").filter(pk=demo_selection.pk).first()
  ```
  The `None`-for-invalid-instance-or-deleted-row behaviour is unchanged
  (that check still runs before entering the `atomic()` block, since it
  needs no query at all). Both current callers are now safe: whichever
  one is used, a real database error during this reload propagates up to
  wherever *they* are called from with the outer transaction already
  clean — `ensure_active_draft_with_demo_snapshot` has no
  `try`/`except` of its own around this call, so the error reaches
  `leads.demo_handoff.consume_pending_demo_selection`'s existing
  `except Exception:` (restoring the marker) or
  `handle_resolved_demo_selection`'s existing `except Exception:`
  (logging and swallowing so the contact page still renders) exactly as
  before; `attach_demo_snapshot` likewise has no `try`/`except` of its
  own, so its caller is responsible for handling it, and doing so no
  longer risks leaving *their* outer transaction poisoned either — proven
  directly (see test level below). No log message anywhere in this
  module or `leads/demo_handoff.py` interpolates a snapshot, token,
  session key, or any other payload value — this phase added no new log
  statements at all, since the fix is purely about where a `try`/`except`
  and an `atomic()` block sit relative to each other. `LeadCreateView`,
  `leads/signals.py`, and every model are completely untouched; no new
  import was needed (`transaction` was already imported at the top of
  `leads/form_draft_service.py`).
- **V2.1-B2 third corrective — the bug reproduced, then fixed and
  re-verified:** before finalizing, the fix was temporarily reverted and
  both new PostgreSQL tests below were re-run against the reverted code —
  both failed exactly as predicted, with
  `django.db.utils.InternalError: current transaction is aborted, commands
  ignored until end of transaction block` raised from a plain, healthy
  query made immediately after the simulated second-lookup failure,
  inside the same outer transaction. The fix was then restored and both
  tests re-verified passing. This confirms the tests actually exercise
  the bug rather than trivially passing regardless.
- **V2.1-B2 third corrective — test level:** two new PostgreSQL-only
  tests, kept alongside — not replacing — `1baf584`'s existing
  `RealTransactionErrorDuringLookupRecoveryTests` (which is unchanged and
  still passes, proving the *first* lookup remains fixed).
  `leads/test_demo_handoff.py` gained
  `RealTransactionErrorDuringSecondLookupRecoveryTests`: opens an outer
  `transaction.atomic()` (simulating `ATOMIC_REQUESTS`); patches
  `DemoSelection.objects.select_related` (one shared manager instance
  regardless of which module's import reaches it, so one patch covers
  both lookups) with a closure-tracked call-counting `side_effect` that
  lets the *first* call through to the real implementation (proving the
  first lookup genuinely succeeds) and only forces a real, server-side
  `SELECT 1/0` on the *second* call; asserts `auth_login` does not raise;
  **still inside the same outer `atomic()` block**, runs a real, unmocked
  `User.objects.filter(pk=user.pk).exists()` query and asserts it
  succeeds (the specific assertion that fails without the fix); asserts
  the call counter is exactly `2` (direct proof the error happened on the
  *second* lookup, not the first); after the outer transaction closes,
  asserts the user is genuinely authenticated, the marker survived with
  its exact original id/form_type, and no `FormDraft` was created; then,
  on the same connection with no mock active, calls
  `consume_pending_demo_selection` again and confirms the snapshot
  attaches successfully. `leads/test_form_draft.py` gained
  `test_attach_demo_snapshot_survives_a_real_postgresql_error_in_the
  _reload_lookup` in `FormDraftPostgresRaceTests`: calls
  `attach_demo_snapshot` directly inside an outer `transaction.atomic()`,
  with the same real `SELECT 1/0` injected into the reload lookup, and
  the call wrapped in `assertRaises` — modelling a real caller catching
  the propagated error themselves — then, still inside that same outer
  transaction, runs a real, healthy query and asserts it succeeds, and
  confirms no partial `FormDraft` was created. `leads.test_demo_handoff` +
  `leads.test_form_draft` on PostgreSQL: 108 tests, all passing, 0 skips
  (every SQLite-skip-guarded test — 10 of them now — runs for real here).
  `leads` app on SQLite: 120 tests total, 110 passed, 10 correctly
  skipped (up from 118/7 skips at `1baf584` by exactly these 2 new
  tests). `accounts` app: 73 tests, all passing (2 skips) — confirming no
  regression in registration, login, phone verification, or email
  verification. Full project suite (SQLite): 668 tests total, 655
  passed, 13 correctly skipped (all PostgreSQL-only; up from 666
  total/11 skips before this phase by exactly these 2 new tests).
  `manage.py check` (0 issues), `makemigrations --check
  --dry-run` ("No changes detected" — no model or migration change), and
  `git diff --check` (clean) all passed.
- **V2.1-B2 third corrective — PostgreSQL evidence:** run against the
  same isolated local PostgreSQL 16 `test_arvion_ci_local` database used
  throughout this project (never the permanent `arvion_ci_local`). Both
  new tests were run once, then 5 additional repeats each — all clean.
  `1baf584`'s existing `RealTransactionErrorDuringLookupRecoveryTests`
  and `2cd1032`'s existing `RealTransactionErrorRecoveryTests` were
  re-run alongside and remain unchanged and passing. The
  `assessments/services.py` PostgreSQL incompatibility found during the
  V2.1-B2 phase (`revoke_assessment_access`'s `select_for_update()` on an
  outer join) remains **present, unrelated, and untouched by any commit
  in this session** — recorded again here so it is never lost or quietly
  dropped from the project record; it still needs separate human
  prioritization.
- **V2.1-B2 third corrective — migration status:** none created or
  needed; `makemigrations --check --dry-run` reported "No changes
  detected." No model or schema change — this phase touched only
  `leads/form_draft_service.py`, `leads/test_demo_handoff.py`, and
  `leads/test_form_draft.py`.
- **Git boundary (as of `afde089`, historical — see the accurate,
  up-to-date count directly below):** `main` was seventeen commits ahead
  of `origin/main` at that point — the sixteen from the prior entry, plus
  `afde089`. No prior commit was amended.
- **V2.1-B3 — model change:** `leads.FormDraft` gained one new field,
  `revision = models.PositiveBigIntegerField(default=1)` — the
  optimistic-concurrency counter for the new API. Migration
  `leads/migrations/0007_formdraft_revision.py`: a single additive
  `AddField` with a static default, so every pre-existing row gets
  `revision=1` automatically and backward-safely; confirmed via
  `showmigrations leads` that it is **not applied** to the local dev
  SQLite database (only 0001–0006 show `[X]`), and via
  `makemigrations --check --dry-run` → "No changes detected" that it
  fully captures the model change. No other model field changed.
- **V2.1-B3 — revision semantics, centralized in
  `leads/form_draft_service.py`:** every write path in the module now
  maintains `revision` consistently, not just the two new API-facing
  functions:
  - `_get_active_draft_locked` (the shared "find the active draft, expire
    it if stale" helper used by every writer) now bumps `revision` by 1
    when it transitions a draft to `"expired"` — a status change is
    itself real content change.
  - `upsert_active_draft`, `attach_demo_snapshot`, `clear_demo_snapshot`,
    and `ensure_active_draft_with_demo_snapshot` each now compare the
    new value against the existing one (`fields`/`current_step` for the
    first, `demo_snapshot` for the other three) before writing:
    `revision` increments by exactly 1 only on a real change; an
    idempotent no-op call still extends `expires_at` but never bumps it.
    `ensure_active_draft` needed no change — it already never writes to
    an existing draft at all.
  - New `save_draft_fields(*, owner, form_type, fields, current_step,
    expected_revision)`: the race-safe, optimistic-concurrency
    create-or-update behind the new API. `expected_revision=0` means "I
    believe no active draft exists yet" — creating one in that case
    starts it at `revision=1`; if a draft *does* exist, or if
    `expected_revision` doesn't match an existing draft's actual current
    `revision`, it raises the new `DraftConflictError` and writes
    nothing. The revision-match check runs *inside* the same
    `transaction.atomic()` + owner-row `select_for_update()` block
    already used by every other writer, immediately after
    `_get_active_draft_locked` (so an expiry transition discovered in the
    same call is never rolled back by a subsequent conflict — same
    ordering principle as `attach_demo_snapshot`'s existing
    `no_active_draft` case). Content-change detection and the
    "idempotent save never bumps revision" rule are identical to
    `upsert_active_draft`'s.
  - New `delete_draft_with_revision(*, owner, form_type,
    expected_revision)`: hard-deletes the owner's active draft for
    `form_type` under the same lock/conflict contract. No active draft
    exists → returns `False` (idempotent, regardless of
    `expected_revision` — nothing to conflict with). A revision mismatch
    → `DraftConflictError`, nothing deleted. Never accepts a draft id;
    the row is found only via the owner's own lock and `form_type`, so
    there is no id a client could ever pass to reach another account's
    draft.
  - New `DraftConflictError(Exception)`: carries `.draft` — the current,
    canonical, already-owner-scoped draft (or `None` when none exists) —
    so the view can build a 409 response without a second query and
    without ever being able to expose a different account's data. Its
    message is fixed and never repeats a caller-supplied value.
  - New `serialize_draft_canonical(draft)`: the one function that decides
    what a client is ever allowed to see — `form_type`, `current_step`,
    `fields`, `demo_snapshot`, `status`, `revision`, `updated_at`,
    `expires_at`. Never the database primary key, `owner_id`,
    `submitted_lead_id`, or any token/session key.
- **V2.1-B3 — API contract:** two new URLs in the existing `leads`
  namespace, under the project's existing `i18n_patterns` prefix
  (`/<lang>/contact/...`, matching `leads:contact`/`leads:thanks`):
  `leads:draft` → `draft/` (`FormDraftView`, `GET`+`POST`) and
  `leads:draft_delete` → `draft/delete/` (`FormDraftDeleteView`, `POST`
  only) — both in new `leads/views/draft_api.py`. `form_type` is always
  the server-side constant `"leads_contact"`; no request ever supplies
  it. Every response carries `Cache-Control: no-store`. Both views rely
  on the project's already-active, global `CsrfViewMiddleware` for CSRF
  protection on the unsafe (`POST`) methods — neither is `csrf_exempt` —
  confirmed genuinely enforced with `Client(enforce_csrf_checks=True)`.
  `GET leads:draft`: `{"draft": null}` (200) when no active draft exists,
  or `{"draft": <canonical>}` (200) — strictly read-only, calls only the
  existing `get_active_draft` (no write, no transaction, no row lock,
  confirmed directly via `CaptureQueriesContext` + a patched
  `select_for_update` that raises if called). `POST leads:draft`: JSON
  body must be exactly `{"fields": <dict>, "current_step": <int>,
  "expected_revision": <int>}` — any missing/extra/unknown top-level key
  (including `demo_snapshot`, `status`, `owner`, `submitted_lead`,
  `expires_at`) is rejected with `400 invalid_payload_keys` before any
  query. Non-`application/json` content type, a body over 16 KB, invalid
  JSON, or a non-object JSON root are each rejected with their own fixed
  `400` code, also before any query. On success: `201` + the canonical
  draft for a first-ever creation, `200` + the canonical draft for an
  update. On a revision conflict: `409` with `{"code": "conflict",
  "message": ..., "draft": <canonical-or-null>}`. `POST
  leads:draft_delete`: body must be exactly `{"expected_revision":
  <int>}`; success is `{"deleted": true|false}` (200); conflict is the
  same `409` shape as save. Anonymous requests get a JSON `401` (never an
  HTML redirect) on every endpoint/method; staff/superuser accounts get a
  JSON `403` before any write. An unsupported HTTP method (`PUT`,
  `PATCH`, `DELETE` on `leads:draft`; any non-`POST` on
  `leads:draft_delete`) gets Django's own `405` with a correctly computed
  `Allow` header, via the base `View` class's default dispatch — no
  custom method-routing code was written.
- **V2.1-B3 — privacy boundary:** the allowed `fields` keys
  (`request_type`, `service_id`, `budget_range`, `timeline`,
  `preferred_contact`) and the forbidden ones (`name`, `phone`,
  `email_or_telegram`, `business_name`, `website_url`, `message`,
  `privacy_accept`, `public_token`, `session_key`, `submission_token`)
  are unchanged from Phase B1's `normalize_fields` — the new API reuses
  it verbatim via `save_draft_fields`, so a forbidden or unrecognized
  field is rejected as `400 forbidden_field`/`400 unknown_field` exactly
  as before, never silently dropped. `demo_snapshot` can never be
  supplied by a client at all — the strict top-level key-set check on
  both `POST` endpoints rejects any request that even includes that key,
  and `save_draft_fields` itself has no parameter through which a
  snapshot could be passed. `DRAFT_RETENTION_DAYS = 7` is unchanged and
  still the single source of truth (`leads/models/form_draft.py`).
  Guests (anonymous requests) never reach the service layer at all — the
  view's `_authorize_customer` check runs first, before any query.
  Staff/superuser accounts are rejected both at the view (403, before any
  query) and, in defense of depth, inside `save_draft_fields`/
  `delete_draft_with_revision` themselves (`DraftValidationError`,
  code `staff_or_superuser_not_allowed`) — so even a hypothetical future
  caller that skips the view's check still cannot create or modify a
  staff-owned customer draft.
- **V2.1-B3 — authorization:** every service function in the module
  already only ever reads/writes the exact owner passed to it — `GET`
  calls `get_active_draft(request.user, "leads_contact")`, `POST` calls
  `save_draft_fields(owner=request.user, ...)`, delete calls
  `delete_draft_with_revision(owner=request.user, ...)`. No draft id,
  owner id, or user id is ever accepted from any payload on any endpoint,
  so there is no parameter a client could manipulate to reach another
  account's draft — confirmed directly by tests asserting user A's
  requests never see, modify, or receive a conflict response containing
  user B's data (a conflict's `draft` is always re-fetched from the
  *same* locked owner row the request is already scoped to).
- **V2.1-B3 — test level:** new `leads/test_draft_api.py` (37 tests):
  `FormDraftGetViewTests` (10 — no draft → null; owner sees only safe
  own data; anonymous → 401 JSON; staff/superuser → 403 JSON; user A
  cannot read user B's draft; an expired draft is not returned; no write
  or row lock on GET, proven via `CaptureQueriesContext` + a patched
  `select_for_update`; invalid HTTP methods → 405 with `Allow`; no
  forbidden token in the response even when a real snapshot is attached);
  `FormDraftPostViewTests` (18 — 201+revision 1 on first creation; 200 +
  revision+1 on a real update; an identical resave is idempotent and
  keeps the same revision; a stale `expected_revision` → 409 without
  overwriting; a conflict response only ever contains the requester's own
  draft; unknown/forbidden fields rejected; `demo_snapshot`/`status`/
  `owner`/`submitted_lead`/`expires_at` in the payload all rejected as
  invalid top-level keys; malformed JSON, a non-object root, and an
  oversized (>16 KB) body all rejected; wrong `Content-Type` rejected;
  out-of-range `current_step` and an invalid `service_id` rejected;
  anonymous/staff rejected with no write; invalid HTTP method → 405;
  saving against an expired draft with `expected_revision=0` creates a
  fresh one; a previously-attached demo snapshot survives an ordinary
  field save; CSRF genuinely enforced via
  `Client(enforce_csrf_checks=True)`); `FormDraftDeleteViewTests` (9 —
  correct-revision delete; idempotent repeat delete; idempotent delete
  when none exists; stale revision → 409 without deleting; no id/owner
  parameter exists through which another account's draft could even be
  named; anonymous/staff rejected; invalid method → 405; CSRF genuinely
  enforced). Plus one new PostgreSQL-only
  `FormDraftApiPostgresConcurrencyTests` (see below).
  `leads/test_form_draft.py` gained 25 new tests: `RevisionBumpConsistencyTests`
  (8 — new draft starts at revision 1; `upsert_active_draft` bumps only
  on real change; `attach_demo_snapshot`/`clear_demo_snapshot` bump only
  when the snapshot content actually changes; `ensure_active_draft` never
  bumps an existing draft; `ensure_active_draft_with_demo_snapshot` bumps
  only on real change and starts a new draft at 1; an expiry transition
  bumps revision), `SaveDraftFieldsTests` (12), `DeleteDraftWithRevisionTests`
  (5), `SerializeDraftCanonicalTests` (1, confirming no `id`/`pk`/`owner`/
  `owner_id`/`submitted_lead`/`submitted_lead_id` key exists in the
  canonical shape — checked by key name, not by searching for a specific
  id value, to avoid a false pass/failure from an unrelated field
  coincidentally sharing a small integer's string form). `leads` app
  total: 182 tests, all passing (11 skips). `accounts`+`projects`+
  `management_portal`: 234 tests, all passing (2 skips) — confirming no
  regression from the model/migration change. Full project suite: 730
  tests total, 716 passed, 14 correctly skipped (all PostgreSQL-only; up
  from 668 total/13 skips at `afde089` by exactly the 62 new tests this
  phase added). `manage.py check` (0 issues), `makemigrations --check
  --dry-run` ("No changes detected"), and `git diff --check` (clean) all
  passed.
- **V2.1-B3 — PostgreSQL concurrency evidence:** new
  `FormDraftApiPostgresConcurrencyTests.test_concurrent_saves_with_the_same_expected_revision_converge_to_one_winner`:
  creates one draft, then two threads (independent DB connections, each
  wrapped in `transaction.atomic()` to mirror `ATOMIC_REQUESTS`) call
  `save_draft_fields` at (as close as Python threading allows) the same
  instant with the *same* `expected_revision`, synchronized via
  `threading.Barrier(2)`. Result, every run: exactly one thread succeeds
  (revision advances by exactly 1) and exactly one gets a real
  `DraftConflictError` — never both succeeding (which would be a lost
  update) and never both failing; exactly one `FormDraft` row survives
  for that owner; no deadlock (both threads observed finished via
  `Thread.is_alive()`) and no unhandled exception of any other type. Ran
  against the same isolated local PostgreSQL 16 `test_arvion_ci_local`
  database used throughout this project (never the permanent
  `arvion_ci_local`), once plus 5 additional repeats — all clean. Also
  re-ran `accounts`+`leads`+`projects` against that same real PostgreSQL
  database: 276 tests, all passing. SQLite's own skip of this test (it
  cannot demonstrate genuine row-level locking) is not presented as
  evidence of anything — the claim rests entirely on the real-PostgreSQL
  runs above. The unrelated, pre-existing `assessments/services.py`
  PostgreSQL incompatibility (`revoke_assessment_access`'s
  `select_for_update()` on an outer join) remains **present, unrelated,
  and untouched by any commit in this session** — recorded again here so
  it is never lost or quietly dropped from the project record; it still
  needs separate human prioritization.
- **V2.1-B3 — rollback:** the migration is purely additive
  (`AddField` with a static default) — reversible with a plain
  `migrate leads 0006_formdraft_and_more`, which drops the `revision`
  column and loses nothing else (no data migration, no other schema
  change). The two new views/URLs can be removed by reverting
  `leads/urls.py`, `leads/views/__init__.py`, and deleting
  `leads/views/draft_api.py` with no effect on any other page — nothing
  else in the project calls them yet. `save_draft_fields`/
  `delete_draft_with_revision`/`DraftConflictError`/
  `serialize_draft_canonical` are purely additive to
  `leads/form_draft_service.py`; the only *behavioural* change to
  pre-existing functions is the revision-bump-on-change logic added to
  `_get_active_draft_locked`/`upsert_active_draft`/`attach_demo_snapshot`/
  `clear_demo_snapshot`/`ensure_active_draft_with_demo_snapshot`, which
  is additive in effect (a new field changing value) and does not alter
  any of those functions' pre-existing return values, signatures, or
  side effects on `fields`/`current_step`/`demo_snapshot`/`status`/
  `expires_at`.
- **V2.1-B3 — risks/limitations:** the API is infrastructure only — no
  UI or JavaScript calls it yet, so it carries no user-facing behaviour
  change by itself. A client that never learns to retry on `409` will
  simply see its save rejected; the response's `draft` field is
  deliberately provided so a future UI can implement "reload and retry"
  without a second request. `save_draft_fields` intentionally treats
  `expected_revision != 0` against a nonexistent draft as a conflict
  (never a silent create) — a client that never previously read a draft
  and guesses a nonzero revision will always get a 409 with `draft:
  null`, which is the correct, safe behaviour but is worth a future UI
  author knowing about. The unrelated, pre-existing PostgreSQL
  incompatibility in `assessments/services.py` remains unfixed and
  outside this phase's scope, as instructed.
- **Git boundary (as of `57a6be8`, historical — see the accurate,
  up-to-date count directly below):** `main` was eighteen commits ahead
  of `origin/main` at that point — the seventeen from the prior entry,
  plus `57a6be8`. No prior commit was amended.
- **V2.1-B3 corrective — root cause and fix:** `save_draft_fields`'s
  `existing is None` branch was:
  ```python
  if existing is None:
      if expected_revision != 0:
          raise DraftConflictError(None)
      draft = FormDraft.objects.create(...)
      return draft, True
  ```
  all still *inside* the enclosing `with transaction.atomic():` block.
  `existing is None` here can mean either "there was never a draft" *or*
  "`_get_active_draft_locked` just found one, discovered it was expired,
  and wrote `status="expired"`/bumped `revision` before returning
  `None`." In the second case, raising `DraftConflictError` right there
  makes the exception propagate out of the `atomic()` block, and Django's
  own transaction machinery rolls back *everything* written inside that
  block when that happens — including the expiry transition, which has
  nothing to do with why the conflict was raised. Fixed by recording the
  conflict outcome in a local sentinel instead of raising immediately,
  and only converting it into a raised `DraftConflictError` *after* the
  `with` block has exited normally:
  ```python
  _NO_CONFLICT = object()
  ...
  conflict = _NO_CONFLICT
  draft = None
  created = False
  with transaction.atomic():
      ...
      if existing is None:
          if expected_revision != 0:
              conflict = None       # conflict, canonical is "no draft"
          else:
              draft = FormDraft.objects.create(...); created = True
      elif existing.revision != expected_revision:
          conflict = existing        # conflict, canonical is the active draft
      else:
          ...save...; draft = existing
  if conflict is not _NO_CONFLICT:
      raise DraftConflictError(conflict)
  return draft, created
  ```
  A dedicated sentinel object (not `None`) distinguishes "no conflict"
  from "conflict with `draft=None`" — `None` is itself a valid, meaningful
  conflict payload (no active draft exists), so it cannot double as the
  "nothing went wrong" marker. This exactly mirrors the ordering already
  used by `attach_demo_snapshot`/`clear_demo_snapshot`'s own
  `no_active_draft` case (raised only after their `transaction.atomic()`
  block closes) — `save_draft_fields` just hadn't been given the same
  treatment when it was first written. `delete_draft_with_revision` was
  checked and does **not** have this bug: its own "no active draft"
  case is a plain `return False` (never a `raise`) from inside its
  `atomic()` block, so a normal return commits the block as usual; it
  was left untouched, per this phase's narrow scope.
- **V2.1-B3 corrective — the bug reproduced, then fixed and
  re-verified:** before finalizing, the fix was temporarily reverted
  (restoring the old immediate `raise DraftConflictError(None)`) and the
  new regression tests below were re-run against that reverted code —
  both failed with `AssertionError: 'open' != 'expired'`, i.e. the
  expired transition really had been rolled back. The fix was then
  restored and the same tests re-verified passing. This was done once at
  the service-function level and once at the full HTTP-API level,
  confirming the fix (and the tests) are real, not incidental.
- **V2.1-B3 corrective — why the previous test missed this:**
  `57a6be8`'s `test_expired_draft_requires_expected_revision_zero_to_recreate`
  asserted a `DraftConflictError` was raised, then *immediately made a
  second `save_draft_fields` call* (with `expected_revision=0`) and only
  inspected the database *after* that second call. That second call's
  own, independent `_get_active_draft_locked` invocation re-discovered
  the (still, at that point, un-rolled-back-looking-but-actually-rolled-
  back) draft as expired and transitioned it *again* — so the test's
  final `stale.refresh_from_db()` reflected the *second* call's write,
  not whether the *first* call's conflict had preserved anything. Fixed
  by adding a test that inspects the row immediately after the conflict,
  with no second save in between (see test level below); the original
  test is kept, renamed, and now checks that the pattern this project
  actually relies on (retry with `expected_revision=0` after seeing
  `draft: null`) still results in exactly one active draft.
- **V2.1-B3 corrective — test level:** `leads/test_form_draft.py`:
  `test_expired_draft_transition_survives_an_immediate_conflict` (new) —
  creates a draft, backdates its `expires_at`, calls `save_draft_fields`
  once with the original (now-stale) `expected_revision`, asserts
  `DraftConflictError` with `draft=None`, then — with **no second save**
  — asserts via `refresh_from_db()` that the row is `status="expired"`,
  `revision == initial_revision + 1`, and its `fields`/`current_step` are
  completely unchanged, and that zero active drafts exist for the owner.
  `test_expired_draft_then_separate_create_with_expected_revision_zero`
  (renamed from the old, insufficient test) — keeps the original
  "conflict, then a *separate* `expected_revision=0` call creates a fresh
  draft" assertion, now also confirming exactly one active draft exists
  afterward. `test_stale_expected_revision_conflicts_without_overwriting`
  (strengthened) — a conflict against an *already-active* (non-expired)
  draft with the wrong revision now also asserts `expires_at`/
  `updated_at` are byte-identical before and after (this branch never
  had the rollback bug, since no write happens before that raise, but
  the test now proves it explicitly rather than by omission).
  `leads/test_draft_api.py` gained
  `test_conflict_against_an_expired_draft_still_commits_the_expiry_transition`
  (the same scenario through the real HTTP view, checked immediately
  after the 409 response) and a new PostgreSQL-only class,
  `FormDraftApiExpiredConflictUnderOuterTransactionTests` (see below).
  `leads.test_draft_api`+`leads.test_form_draft`+`leads.test_demo_handoff`
  on SQLite: 173 tests, all passing (12 skips). `leads` app total: 185
  tests, all passing (12 skips). `accounts`+`projects`+
  `management_portal`: 234 tests, all passing (2 skips) — confirming no
  regression. Full project suite (SQLite): 733 tests total, 718 passed,
  15 correctly skipped (all PostgreSQL-only; up from 730 total/14 skips
  at `57a6be8` by exactly the 3 new tests this phase added). `manage.py
  check` (0 issues), `makemigrations --check --dry-run` ("No changes
  detected" — no migration in this phase), and `git diff --check`
  (clean) all passed.
- **V2.1-B3 corrective — PostgreSQL evidence:** new
  `FormDraftApiExpiredConflictUnderOuterTransactionTests` (PostgreSQL-
  only): calls the real `POST leads:draft` view (via the Django test
  client, in-process, same connection) *inside* a genuine outer
  `transaction.atomic()` standing in for Django's own `ATOMIC_REQUESTS`
  per-request wrapping, targeting the exact same expired-draft-plus-
  stale-`expected_revision` scenario. Confirms: the view's own 409
  response is returned normally (the view catches `DraftConflictError`
  itself — no exception ever propagates out of the outer `atomic()`
  block); a real, unmocked query for the row **while still inside that
  same outer transaction** correctly shows `status="expired"`; after the
  outer transaction closes, the row's `revision` is confirmed to have
  advanced by exactly 1 and no active draft exists for the owner. Run
  against the same isolated local PostgreSQL 16 `test_arvion_ci_local`
  database used throughout this project (never the permanent
  `arvion_ci_local`), once plus 5 additional repeats — all clean.
  `leads.test_draft_api`+`leads.test_form_draft`+`leads.test_demo_handoff`
  also re-run in full against that same real PostgreSQL database: 173
  tests, all passing, 0 skips (every SQLite-skip-guarded test — 12 of
  them — runs for real here, including the pre-existing
  `FormDraftApiPostgresConcurrencyTests` concurrency test, re-confirmed
  unaffected by this fix). The unrelated, pre-existing
  `assessments/services.py` PostgreSQL incompatibility
  (`revoke_assessment_access`'s `select_for_update()` on an outer join)
  remains **present, unrelated, and untouched by any commit in this
  session** — recorded again here so it is never lost or quietly dropped
  from the project record; it still needs separate human prioritization.
- **V2.1-B3 corrective — migration status:** none created or needed
  (none was expected for this phase); `makemigrations --check --dry-run`
  reported "No changes detected." This phase touched only
  `leads/form_draft_service.py` (one function, `save_draft_fields`),
  `leads/test_form_draft.py`, and `leads/test_draft_api.py` —
  `delete_draft_with_revision` and every other service function are
  byte-for-byte unchanged, per this phase's explicit narrow scope.
- **Git boundary (current, accurate as of this phase's own commit):**
  `main` is nineteen commits ahead of `origin/main` — the eighteen
  listed above, plus this V2.1-B3 corrective commit. No prior commit is
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
- **V2.1-C1 — what was built:** `leads/views/contact.py`'s
  `LeadCreateView` gained a `FIELD_STEPS` map and a `form_invalid`
  override (mirroring `CrmOrderCreateView`/`ClinicOrderCreateView`'s own
  existing pattern) that computes and renders `error_step` on a Django
  validation-error rerender — this template never had that marker before
  this phase. `get_context_data` now adds, only for
  `request.user.is_authenticated and not is_staff and not is_superuser`:
  `server_draft_enabled=True`, `draft_url=reverse("leads:draft")`,
  `draft_delete_url=reverse("leads:draft_delete")`,
  `login_url=reverse("accounts:login")` — never a draft id, owner id,
  token, or session key. `leads/templates/leads/contact.html`: the
  `<form>` tag now carries `data-error-step` (only when `form.errors`,
  exactly like the CRM/clinic templates) and, only when
  `server_draft_enabled`, five safe data attributes
  (`data-server-draft="1"`, `data-draft-url`, `data-draft-delete-url`,
  `data-login-url`, `data-lang`) — the last of these (a plain, non-secret
  language code) was added beyond the four explicitly named in the
  request because the mandated 401 flow needs a login link with `next`,
  and this was the least-surprising way to get one without inventing a
  new naming scheme. For an authenticated non-staff customer, a fixed,
  always-visible bilingual disclosure paragraph
  (`.wizard-server-draft-notice`) replaces the old
  per-device `data-draft-consent` box entirely (the box markup itself is
  not rendered in server mode at all, not merely hidden) — the disclosure
  is mandatory information, not an opt-in gate, since the account
  relationship itself is what authorizes storage, mirroring the design
  note already on record under "V2.1 — privacy boundary". Guests and
  staff/superusers get neither the new attributes nor the notice; guests
  keep the exact old consent-box flow.
  `core/static/core/js/wizard-engine.js` (cache-busted to `?v=3` in
  `core/templates/core/base.html`) gained a second, fully separate
  execution mode, `serverDraftEnabled` (`isDemoContinuationWizard &&
  form.dataset.serverDraft === "1"`), branching only the
  draft-persistence sections of `initWizard` — `validate()`, `show()`,
  conditional-field sync, the demo-context reconstruction helper, and the
  final submit-with-fetch handler are all shared, untouched code paths for
  both modes. In server mode: the old `readConsent`/`writeConsent`/
  `showConsent`/local `renderDraftControls` banner logic never runs (the
  guest reconciliation block at the end of `initWizard` is now wrapped in
  `if (!serverDraftEnabled) { … }`); `input`/`change` on a draft field and
  a `Next`/`Back` step change all call a new `requestServerSave()`
  indirection (a `let` reassigned once `initServerDraftMode()` runs,
  matching the existing 400ms debounce timer variable) instead of
  `writeDraft()`. A new `initServerDraftMode()` closure (defined once, at
  the very end of `initWizard`, invoked only when `serverDraftEnabled`)
  holds: an explicit DOM↔API field adapter
  (`request_type↔request_type`, `service↔service_id`,
  `budget_range↔budget_range`, `timeline↔timeline`,
  `preferred_contact↔preferred_contact`; an empty/unanswered DOM value is
  never sent at all, matching `save_draft_fields`'s own "omit the key"
  contract — never an explicit `null`) via `collectApiFields`/
  `applyApiFieldsToDom` (declared at the outer `initWizard` scope, next to
  the mode-detection consts, since both are pure and side-effect-free); a
  small state machine (`revision`, `ready`, `saving`, `dirty`,
  `pauseReason`) enforcing exactly one in-flight `POST` at a time
  (a change arriving mid-save sets `dirty` and is folded into the next
  save once the current one resolves, never queued as a second concurrent
  request); the five required states A–D (reconcile on load: GET the
  server, read any local draft only into memory via the existing
  `readDraft()` — never applied to the DOM until an explicit choice) with
  their own bilingual banner + two/three named actions each — "ادامه
  پیش‌نویس حساب", "شروع دوباره" (state B); "انتقال این پیش‌نویس به حساب",
  "شروع تازه" (state C); "ادامه نسخه حساب", "استفاده از نسخه این دستگاه",
  "شروع دوباره" (state D, with both sides' last-saved times rendered via
  `Intl.DateTimeFormat`); nothing at all shown for state A beyond quietly
  arming autosave at `expected_revision=0`; state E (a Django
  validation-error rerender, detected via the pre-existing
  `isErrorRerender = !!form.dataset.errorStep`) only ever reads the
  server's `revision` to arm autosave correctly going forward — it never
  calls `applyApiFieldsToDom`/`show()`, so the customer's just-typed,
  currently-rendered answers are never touched); a 409 handler
  (`handleConflict`) usable both during initial reconciliation actions and
  at any later autosave, distinguishing a real canonical draft ("بارگذاری
  نسخه حساب" / "ذخیره نسخه فعلی من", the latter resubmitting with the
  canonical `revision` as the new `expected_revision`) from
  `draft: null` ("ذخیره این صفحه به‌عنوان پیش‌نویس جدید" at
  `expected_revision=0`); a 401 handler that never redirects, preserves
  every DOM value, and shows a login link built from the new
  `data-login-url` attribute plus a `next` pointing back at the exact
  current path+query; a 403 handler that pauses autosave permanently with
  no retry (defense in depth — the view itself already turns staff away
  before this could fire); a bounded network-error retry
  (`[2000, 5000, 15000, 30000, 60000]` ms, capped at 5 attempts, reset by
  either a real success or the browser's own `online` event, never an
  unbounded loop); and a shared, explicit, bilingual two-step delete
  confirmation (`buildDeleteConfirmRow`) reused by both the reconciliation
  banner's "شروع دوباره" and a new persistent "پاک‌کردن پیش‌نویس حساب"
  control in the existing `[data-draft-controls]` slot (shown only once a
  real server revision is known) — a 409 on delete whose canonical
  `draft` is `null` is treated as already-achieved (idempotent, matching
  `delete_draft_with_revision`'s own idempotent-when-absent contract) and
  never as a failure. `core/static/core/css/site.css` gained
  `.wizard-server-draft-notice`, `.wizard-draft-banner.is-conflict`,
  `.wizard-draft-banner [data-draft-primary-action]` (a marker attribute,
  not a `.button` class, so the reconciliation banner's primary choice
  visually matches the existing local-draft restore banner's own
  `[data-draft-restore]` styling rather than competing with the wizard's
  actual `Next`/`Submit` CTA), `.wizard-draft-confirm`, and
  `.wizard-draft-status`/`.is-error` — all built from existing design
  tokens (`--color-line`, `--color-surface-2`, `--color-muted`,
  `--status-danger-border`, `--color-danger-surface`,
  `--color-status-red-text`), so light/dark and RTL/LTR are inherited
  automatically, and no new animation was introduced (so there is nothing
  for `prefers-reduced-motion` to need to disable beyond the rules that
  already covered `.wizard-draft-banner`/`.button` before this phase).
- **V2.1-C1 — privacy/field boundary:** the exact same five-field
  allowlist as every prior phase (`request_type`, `service_id`,
  `budget_range`, `timeline`, `preferred_contact`) is the *only* thing
  `collectApiFields`/`apiFieldsFromLocal` will ever read off the DOM or a
  local-draft blob — `name`, `phone`, `email_or_telegram`,
  `business_name`, `website_url`, `message`, `privacy_accept`, the CSRF
  hidden field, and any demo token are never touched by either function,
  matching the server's own `FORBIDDEN_FIELD_KEYS`/strict top-level-key
  checks (a payload with an extra key is already rejected server-side —
  the client simply never constructs one). `demo_snapshot` is never sent
  by the client at all (no code path in this phase's JS references it),
  matching the API's own hard rule that no client can ever set it.
  Restoring a canonical draft's `fields` onto the DOM
  (`applyApiFieldsToDom`) only ever assigns a value that already matches
  one of that `<select>`'s own existing `<option>` values (checked
  explicitly before assignment) or the empty string — never `innerHTML`,
  never an arbitrary string injected as markup; every banner/status
  message is built via `textContent` assignment or child-element
  `append`, and the one place raw data flows through a template literal
  (`.innerHTML` on the guest-only, pre-existing local-draft banner) was
  not touched by this phase and only ever interpolates this project's own
  fixed, translated `copy` strings — never a value that came from the
  server response or `localStorage`.
- **V2.1-C1 — reconciliation and autosave-queue rules:** see the "what was
  built" bullet above for the full state-by-state behavior; in short,
  nothing is ever applied to the DOM or sent to the server as a side
  effect of merely loading the page — every transition out of states
  B/C/D requires one explicit click, "local draft" is read only in memory
  until that click, and local `localStorage` data for this wizard is
  cleared only after the corresponding server operation's response comes
  back successful (never optimistically, never on the request itself).
  A conflict's `draft: null` case and an idempotent-delete's `draft: null`
  case are both explicitly branched, never conflated with "no response
  yet"/`undefined` — `safeDraft()` returns `undefined` only for a
  genuinely malformed response shape, which is always treated as "leave
  the DOM alone, show a not-saved status", never as "no draft".
- **V2.1-C1 — Phase D limitation (explicitly recorded, not fixed here):**
  as in every prior V2.1 phase, `FormDraft`→`Lead` conversion does not
  exist yet — a successful final submission through
  `LeadCreateView.form_valid` still leaves any `open` `FormDraft` for that
  customer exactly as it was (this phase's own submit-handling code is
  byte-for-byte the pre-existing fetch-based handler; nothing in this
  phase touches it). No JavaScript-side workaround (a `keepalive` delete
  fired on submit, a delete triggered after the success redirect, etc.)
  was added to paper over this, per explicit instruction — inventing a
  client-side substitute for the real, still-`NOT_STARTED` atomic
  `open/submitting → submitted` transition would create a second, racy,
  unauthoritative path to the same state. **This means the current set of
  commits (V2.1-A through this C1 phase) must not be deployed** until
  Phase D closes this gap — a customer who submits the contact form today
  would keep seeing a "continue your draft" banner for a request they
  already sent, which is confusing even though it causes no data
  corruption (the original `Lead` is unaffected either way).
- **V2.1-C1 — browser verification: what could and could not be
  checked:** all 9 requested Python-level checks were run for real and
  pass (see "test level" below) — guest sees zero new data attributes;
  an authenticated non-staff customer sees all five safe, reversed-URL
  attributes; staff and superuser see neither the attributes nor the
  notice; no draft id/session key/token appears in the HTML even when a
  real draft already exists for that customer; the Persian page renders
  only the Persian notice sentence and the English page only the English
  one; a validation error correctly sets `data-error-step` to the field's
  actual step (1 or 3, tested both); the existing `leads`/`accounts`
  suites, `manage.py check`, `makemigrations --check --dry-run`, and
  `git diff --check` all pass with zero regressions. What could **not**
  be checked this session: any of the 16 named live-browser journeys
  (guest local save/restore, all four reconciliation states, the 409/401/
  403/network-error paths, delete confirmation, mobile 320/390,
  light/dark, keyboard-only, `prefers-reduced-motion`). The only
  browser-automation tool available here was used extensively — first
  successfully (a fresh customer/staff login and page load against a
  disposable, migrated-only-for-this-session SQLite database under
  `arvion/settings/_c1_browser_check.py`, never `db.sqlite3` or
  `arvion_ci_local`, deleted again before this commit), then it stopped
  running any page JavaScript at all partway through the session — proven
  with a minimal, code-independent repro: a blank page's own inline
  `<script>console.log(...)</script>` never fired, while `page.evaluate()`
  (a separate, CDP-level mechanism) kept returning correct results the
  whole time, which is how the data-attribute/notice-text checks above
  were still confirmed directly against real server responses. After
  that, the same tool further degraded to where scripted form-fill/submit
  itself stopped reliably taking effect (a login attempt whose fields
  were filled via the tool's own API was submitted empty). This reads as
  an environment/tool regression independent of anything in this
  session's code — not a defect being reported against the shipped
  feature — but per this project's own rule against ever labeling an
  unavailable check as passing, the 16 journeys are recorded as not run,
  not as passed. One usable screenshot was still captured before the
  tool's JS execution broke (`guest-mobile.png`, port `127.0.0.1:8811`,
  390×844): it incidentally surfaced a real, **pre-existing, out-of-scope**
  CSS defect — `.wizard-consent{display:grid;…}` in `site.css` has no
  `[hidden]` override outside `.flow-page`-wrapped templates (only
  `flow.css`'s `.flow-page [hidden]{display:none!important}` covers that
  case, and `leads/contact.html` is not a `.flow-page` template) — so the
  guest per-device consent box is visually shown from first paint
  regardless of the `hidden` attribute already on it in the template,
  until/unless JS defers to `showConsent()`'s own logic. This existed
  before this phase (confirmed: this phase never touched that CSS rule or
  that attribute) and is unrelated to the new server-draft mode (which
  never renders that box at all), so it was recorded here rather than
  fixed, per this phase's explicit narrow scope — a future phase should
  add `.wizard-consent[hidden]{display:none}` (or move the leads-contact
  page under whatever wrapper class `flow.css` already targets) and
  verify no guest-facing regression. No test data or screenshots from
  this verification were committed — the disposable database, settings
  module, and every screenshot/script lived only under this session's
  scratch directory or a since-deleted settings file, all removed before
  this phase's commit.
- **V2.1-C1 — test level:** new `leads/test_contact_server_draft_ui.py`
  (9 tests, `ServerDraftDataAttributeTests` + `ErrorRerenderStepMarkerTests`):
  guest sees none of `data-server-draft`/`data-draft-url`/
  `data-draft-delete-url`/`data-login-url`/the new notice class, and still
  sees the old `data-draft-consent` box; an authenticated non-staff
  customer sees `data-server-draft="1"` and all three reversed URLs plus
  `data-lang="fa"`, and does **not** see the old consent box; staff and a
  real superuser both get neither; a real, existing `FormDraft` (created
  via `save_draft_fields` directly) never leaks its own pk, the owner's
  pk, `session_key`, `public_token`, or `submission_token` into the page
  (checked as specific attribute shapes, not bare small-integer
  substrings, which would otherwise collide harmlessly with unrelated
  page content like asset version query strings); the fa page contains
  only the Persian notice sentence and the en page only the English one;
  posting an invalid step-3 field (missing `privacy_accept`) yields
  `data-error-step="3"`, an invalid step-1 field (`request_type`) yields
  `data-error-step="1"`, and a fully valid submission has no marker at
  all (a real 302). `leads.test_contact_server_draft_ui`+`leads.tests`:
  21 tests, all passing — confirming zero regression in the pre-existing
  `LeadTests` suite (demo hand-off, rate limiting, honeypot, bilingual
  labels, etc.) from the `form_invalid`/`get_context_data` additions.
  `leads`+`accounts` full suite: 267 tests, all passing (14 skips, all
  correctly PostgreSQL-only). `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected" — no model or
  schema touched in this phase), and `git diff --check` (clean) all
  passed. Full project SQLite suite: 742 tests total, 727 passed, 15
  correctly skipped (up from 733 total/15 skips at the V2.1-B3 corrective
  commit by exactly the 9 new tests this phase added).
- **V2.1-C1 — migration status:** none created or needed; this phase
  touched only `leads/views/contact.py`, `leads/templates/leads/contact.html`,
  `core/static/core/js/wizard-engine.js`, `core/static/core/css/site.css`,
  `core/templates/core/base.html` (the `?v=2`→`?v=3` cache-bust only), and
  the new `leads/test_contact_server_draft_ui.py` — no model, no
  migration, confirmed by `makemigrations --check --dry-run`.
- **V2.1-C1 — risks/limitations:** (1) the client-side reconciliation/
  autosave/conflict logic has not been exercised in a live browser this
  session — see the browser-verification bullet above for the exact,
  honest breakdown of what was and was not checked, and why; (2) the
  Phase D gap (successful submission does not close the `FormDraft`) means
  this and every earlier V2.1 commit remain **not deployable** until Phase
  D ships; (3) a newly discovered, pre-existing, out-of-scope CSS defect
  (`.wizard-consent` ignoring its own `hidden` attribute outside
  `.flow-page` templates) affects the guest experience on this same page
  and should be fixed in a small, separate, visually-verified phase;
  (4) the one added data attribute beyond the four explicitly named
  (`data-lang`) is a deliberate, minimal deviation to satisfy the
  mandatory 401 login-link requirement — flagged here rather than done
  silently; (5) every decision still open under "V2.1 — decisions
  requiring explicit human approval" above remains open and unaffected by
  this phase.
- **V2.1-C1 corrective — root causes and fixes (all in
  `core/static/core/js/wizard-engine.js` unless noted):**
  1. **P1 — temporal dead zone stopped the entire wizard.**
     `const serverDraftEnabled = isDemoContinuationWizard && …` was placed
     right after `clearDraft`'s definition, but `const
     isDemoContinuationWizard = wizardName === "leads-contact";` was only
     declared later, in the demo-context block. Both are `const` in the
     same block scope (`initWizard`'s function body), so reading
     `isDemoContinuationWizard` before its own declaration line throws
     `ReferenceError: Cannot access 'isDemoContinuationWizard' before
     initialization` — an uncaught exception during `initWizard`'s
     synchronous top-level execution, which aborts the *entire* function
     for *every* wizard on the page, guest or authenticated, CRM/Clinic
     included, since `forms.forEach(initWizard)` has no per-form
     try/catch. **Fixed** by moving the `isDemoContinuationWizard`
     declaration up to immediately before `serverDraftEnabled`'s own
     definition (both now sit together, with a comment explaining why the
     order matters), and removing the now-duplicate declaration from the
     demo-context block below it.
  2. **P1 — `[hidden]` did not hide `.wizard-consent` or the wizard
     action buttons.** `.wizard-consent{display:grid;…}` in
     `core/static/core/css/site.css` and the generic
     `.btn,.button,.button-ghost{…display:inline-flex;…}` rule (matching
     the Back/Submit buttons, both styled `.button`) are author-origin
     declarations; the CSS cascade resolves origin+importance *before*
     specificity, so any author-origin `display` declaration always beats
     the user-agent stylesheet's own `[hidden]{display:none}`, regardless
     of selector specificity. The `hidden` attribute was present on the
     DOM (confirmed) but had no visual effect on these two selectors.
     This exact class of bug was already known and fixed for
     CRM/Clinic's own `.crm-actions [hidden]{display:none!important}`
     rule — `leads-contact`'s `.wizard-consent`/`.enquiry-actions` never
     got the equivalent treatment. **Fixed** with three new, narrowly
     targeted rules (not a site-wide `[hidden]` reset):
     `.wizard-consent[hidden]`, `.enquiry-actions [hidden]`, and
     `.wizard-draft-banner[hidden]` (the last one covers this same phone's
     own new reconciliation/conflict banner, which sets `display:flex` and
     would have had the identical bug the first time it was ever actually
     hidden again after being shown).
  3. **P1 — focus restoration targeted a nonexistent `h2`.**
     `show()`'s and `applyCanonicalDraft()`'s focus-management code did
     `steps[current].querySelector("h2")` — correct for CRM/Clinic, whose
     `.crm-step` blocks contain a real `<h2>`, but `leads/contact.html`'s
     steps are `<fieldset data-step="…">` with a `<legend>`, not an
     `<h2>` — so the lookup always returned `null` and focus never moved
     on restore or on ordinary Next/Back navigation for this wizard.
     **Fixed** with one shared helper, `stepHeading(step) =>
     step.querySelector("h2") || step.querySelector("legend")`, used at
     all four call sites (`show()`, the initial per-step `tabindex`
     setup, and `applyCanonicalDraft()`'s two calls) — CRM/Clinic's
     behavior is unchanged (they still resolve their own `h2` first).
  4. **P1 — the initial GET's error handling collapsed everything to
     "offline".** `reconcile()` previously did
     `if (result.networkError || result.status !== 200) { setDraftStatus
     ("offline"); return; }` — a 401 got no session-ended message and no
     preserved-answers guarantee beyond what was already true; a 403 got
     no distinct message; a genuine network failure got no retry at all
     (autosave never even became `ready`, so nothing would ever prompt
     the user again without a manual page reload). **Fixed** by
     introducing `classifyResponse()`, a shared classifier (`network` /
     `auth` / `forbidden` / `conflict` / `ok` / `error`) now used by the
     GET in `reconcile()`, every `POST` in `queueServerSave()`/
     `handleConflict()`/`reconcile()`'s own state-C/D actions, and
     `performDelete()`. The GET path now: retries a real network failure
     with a 5-step capped backoff (`[2000, 5000, 15000, 30000, 60000]`
     ms) *even while `state.ready` is still `false`* (the exact gap named
     in the request); after exhausting those attempts, replaces the
     ambient "retrying" status with a terminal, honest message and a
     manual "تلاش مجدد"/"Retry" button (never leaves the misleading
     "…در حال تلاش دوباره" text showing forever); a 401 shows the
     session-ended notice with a login link and pauses autosave without
     touching any DOM value; a 403 shows a distinct, non-silent message
     and pauses autosave permanently; a malformed/unexpected response
     (including a defensively-handled — never legitimately possible — 409
     on a GET) shows a manual-retry message and never touches the DOM or
     `state.revision`. The exact same five-way split now also covers
     `queueServerSave()` (autosave) and `performDelete()` (delete/start
     over), per the explicit instruction to apply it consistently to save
     and delete as well — see point 5 below for how a malformed *success*
     response is now also caught before it can corrupt state.
  5. **P1 — no real validation of the API response shape.**
     `safeDraft()` previously only checked that a `draft` key existed in
     the parsed JSON, then handed the raw value straight to callers that
     immediately read `.revision`/`.fields`/`.current_step` — a malformed
     or unexpected response (truncated JSON that still parses, a proxy
     error page shaped like `{"draft": "oops"}`, a future server change
     `serialize_draft_canonical` didn't account for) could have thrown a
     `TypeError` reading a property of a non-object, or silently written
     garbage into `state.revision`. **Fixed** with `isValidCanonicalDraft`
     (validates `draft === null` as the one other valid shape, or an
     object with an integer `revision >= 1`, an integer `current_step`
     within `[0, steps.length - 1]`, and a `fields` object containing only
     this adapter's five known API keys with the correct type for each)
     and `isValidFieldsObject`, both gating a rewritten `safeDraft()` that
     now returns `{ok: true, draft}` or `{ok: false}` — never a bare
     value that could be confused between "not present yet" and the
     equally-valid `draft: null` payload. Every call site
     (`reconcile()`, `queueServerSave()`, `handleConflict()`'s two POST
     handlers, the state-C/D import/use-device handlers) now checks
     `.ok` before ever touching `.revision`/`.fields`, and shows a
     manual-retry message instead on failure — the DOM and
     `state.revision` are left completely untouched in that case.
- **V2.1-C1 corrective — smaller fixes:** (a) the `keydown` Enter handler
  (which already acted as "Next" for a non-final step) now also calls
  `requestServerSave()` after `show(current + 1)`, matching the `Next`
  button's own click handler — previously Enter silently skipped the
  save entirely; (b) the `change` event listener now calls
  `clearTimeout(saveTimer)` before its own immediate save/write, so a
  pending 400ms debounce timer left over from a same-field `input` event
  can never also fire afterward and produce a redundant, unnecessary
  second `POST`; (c) `showSessionEndedNotice()`, `showForbiddenNotice()`
  (new), `handleConflict()`, and every retryable-error message now render
  through one shared, single-owner `issuePanel` element (created once,
  content replaced on every call via `showIssue()`/`hideIssue()`) instead
  of each building and `form.prepend()`-ing its own new `<div>` — so a
  conflict, a session-ended notice, a forbidden notice, and a network/
  malformed-response retry message can never stack on top of each other;
  at most one is ever visible. No change was made to the field allowlist,
  CSRF handling, or guest/local-draft behavior — `collectApiFields`/
  `apiFieldsFromLocal`/`applyApiFieldsToDom` are byte-for-byte unchanged
  from the original C1 phase, and the guest code path
  (`if (!serverDraftEnabled) { … }`) was not touched at all beyond the
  two general-purpose fixes in (a)/(b) above, which are no-ops for a
  guest form (no `[data-server-draft]`, so `requestServerSave` stays the
  inert placeholder).
- **V2.1-C1 corrective — Phase D, dashboard, models, migrations:**
  untouched, exactly as scoped — no code in this corrective phase creates,
  modifies, or reads `FormDraft`→`Lead` conversion, the account dashboard,
  any model, or any migration.
- **V2.1-C1 corrective — test level:** re-ran every suite named in the
  original C1 phase, unchanged in count and outcome (confirming these
  fixes caused zero regression): `leads.test_contact_server_draft_ui` +
  `leads.test_draft_api` + `leads.test_form_draft` + `leads.test_demo_handoff`
  + `leads` + `accounts` — 267 tests, all passing (14 correctly skipped,
  PostgreSQL-only). `crm_orders` + `clinic_orders` — 28 tests, all
  passing (a real, if server-side-only, smoke check that their own
  `data-error-step`/wizard wiring is unaffected by the shared
  `wizard-engine.js` changes). Full project suite: 742 tests total, 727
  passed, 15 correctly skipped — identical to the pre-corrective count,
  confirming no regression anywhere else in the project. `manage.py
  check` (0 issues), `makemigrations --check --dry-run` ("No changes
  detected" — no model/migration touched), and `git diff --check`
  (clean) all passed. `node --check
  core/static/core/js/wizard-engine.js` passed (JS syntax check) both
  immediately after the TDZ fix and again after the full response-
  validation rewrite.
- **V2.1-C1 corrective — browser verification:** a working, working
  disposable environment was rebuilt from scratch for this phase (a
  fresh throwaway SQLite database — never `db.sqlite3` or
  `arvion_ci_local` — migrated only for this session under a disposable
  `arvion/settings/_c1_browser_check.py`, a disposable customer/staff
  account, a local-only dev server on `127.0.0.1:8811`), and the same
  isolated, code-independent probe used in the original C1 phase
  (`page.setContent` with a single inline `<script>window.__probe =
  "ran"</script>`) was re-run against it before attempting any of the 16
  named journeys. Result: still `NOT_RUN` — the only browser-automation
  tool available in this environment continues to be unable to execute
  any page JavaScript at all, on a completely fresh browser launch, with
  zero relation to this project's own code. Per the explicit instruction
  for this corrective phase ("اگر ابزار مرورگر دوباره خراب شد، مرحله را
  PARTIAL نگه دار و ادعای VERIFIED نکن"), none of the 16 journeys were
  attempted against this broken tool, and this phase is recorded
  `PARTIAL`, not `VERIFIED` — the fixes above are correct and complete by
  careful, deliberate code review (each root cause was independently
  re-traced through the exact call sites named in the corrective
  request), but "reviewed and reasoned about" is not the same evidence
  class as "observed working in a real browser," and this file does not
  conflate the two. The disposable settings module, database, seeded
  accounts, and dev server were all torn down again before this commit —
  nothing from this verification attempt is present in the working tree.
- **V2.1-C1 second corrective — files changed:**
  `core/templates/core/base.html` (cache-bust `v=38→39`/`v=3→4` only),
  `core/static/core/js/wizard-engine.js` (the 6 fixes above — no CSS
  change was needed this round, `3b8fb71`'s `[hidden]` fix already
  covers what this phase needed), and `core/tests.py` (one pre-existing
  test asserted the literal string `site.css?v=38`; updated to `v=39` —
  the same "a test hardcoded a version/count that a real change legitimately
  moves" pattern already seen elsewhere in this project, not a defect).
  No model, migration, or dashboard code touched.
- **V2.1-C1 second corrective — live-browser evidence:** run against a
  freshly rebuilt disposable SQLite database (never `db.sqlite3`/
  `arvion_ci_local`) with disposable customer/staff accounts, all deleted
  afterward. Guest: consent accept, Next/Back/Submit all confirmed
  advancing correctly and redirecting to the real thanks page; reload
  showed the local-draft restore banner with correct bilingual text.
  Confirmed via direct `getComputedStyle` that the step-1 Back/Submit
  buttons are genuinely `display:none` while `hidden`, and that forcing
  `hidden=true` on the consent box now genuinely computes to
  `display:none` (the exact defect `3b8fb71` fixed). Confirmed
  `site.css?v=39`/`wizard-engine.js?v=4` are what a plain reload actually
  serves. State A (no draft): autosave saved correctly, focus after
  `Next` landed on the step's real `<legend>` (the P1 #3 fix from
  `3b8fb71`, now seen working live). States B/C/D: each reconciliation
  banner rendered with correct text/buttons, nothing applied to the DOM
  before an explicit click, `demo_snapshot` survived a "use device
  version" save untouched. Malformed responses (via `page.route`, after
  first clicking through the reconciliation banner so autosave was
  genuinely armed — the tool only matched requests reliably at that
  point, a test-script lesson, not a product issue): a `200
  {"draft": null}` save response showed "پاسخ ذخیره‌سازی نامعتبر بود" /
  "The save response was invalid" with no DOM change and no revision
  corruption, and its own "تلاش مجدد" button then genuinely re-saved
  successfully — this is the direct, live proof of this phase's headline
  P1 fix; a malformed GET, a malformed 409, and a delete response missing
  `deleted` were each rejected the same way, with local state provably
  untouched (server-side revision/fields re-checked via a real `fetch`
  after each). A **real** 401 (all server sessions expired mid-tab,
  no mocking) showed the session-ended notice with a working
  `?next=` login link and preserved the user's just-typed DOM value. A
  **real** 403 (the same logged-in customer promoted to `is_staff=True`
  server-side without reloading, so the client still believed
  server-draft mode was on) showed the forbidden notice with no retry
  loop. A **real** `context.setOffline(true)` network cut, four rapid
  field changes fired during it, then reconnect: only 2 real failed
  network attempts occurred across the whole burst (not 4, not 5) —
  direct proof the P2 #2 single-flight fix works, and the `online` event
  triggered an immediate successful save of the *last* value chosen
  during the burst on reconnect. Delete: successful delete, cancel
  (leaves the draft untouched), and malformed-response-does-not-clear
  all confirmed. A Django validation rerender (an intentionally invalid
  `preferred_contact=phone` with no phone number) preserved the
  customer's just-typed name/email exactly, landed `data-error-step="3"`
  correctly, and re-armed autosave from the server's real revision.
  fa/en: the authenticated notice rendered in exactly one language on
  each locale. 320px and 390px in both light and dark (screenshots taken)
  showed the reconciliation banner compact, legible, and RTL-correct with
  no horizontal scroll. CRM and Clinic wizards: real Next/Back smoke
  test, `"مرحله 1 از 5"`/`"مرحله 1 از 6"` (JS-driven step text, proving
  no TDZ crash reached them either — they were never affected, but this
  confirms it directly rather than by inference), zero console errors.
  Console/`pageerror` listeners were attached across every one of the
  above and never once caught an uncaught exception — the only
  "console errors" the tool ever reported were the browser's own
  network-log lines for intentional non-2xx responses (a normal, expected
  log for a deliberately-provoked 401/403/409/malformed status), never a
  JavaScript exception.
- **V2.1-C1 second corrective — what was not fully confirmed:** keyboard
  Tab order through the reconciliation banner was verified correct
  (skip-link → brand → menu → primary action → secondary action → form
  fields); activating the focused primary button by pressing Enter did
  not register through this specific automation tool, confirmed via
  `document.activeElement` genuinely being the button at the moment of
  the key press. Since the button is a plain, unmodified `<button
  type="button">` and the code adds no keydown handling that could
  interfere with the browser's own native Enter-activates-a-focused-
  button behavior, this reads as a tool limitation (consistent with two
  other tool quirks found and worked around this same session:
  `page.fill()` silently no-op'ing on `type="email"` inputs where
  `.type()` worked, and `page.route()` needing the reconciliation banner
  clicked through before it reliably matched requests) rather than a
  suspected product defect — but it was not independently proven safe
  either, so it is recorded here rather than silently assumed. A full
  desktop-width (not just 320/390) screenshot in each theme was not
  separately captured, though every functional interaction above ran at
  the tool's default (desktop-sized) viewport without any layout issue
  observed. `prefers-reduced-motion` was not separately toggled and
  checked; no new CSS animation exists on any element this phase or the
  prior corrective phase touched, so there is nothing on this feature's
  own surface for that media query to need to suppress.
- **V2.1-D — blocked: idempotency analysis.** The concrete question this
  phase had to answer before writing any code: when a customer's browser
  resubmits the *exact same* final contact-form POST — because the first
  attempt's response was lost after the server had already fully
  committed (`FormDraft` → `submitted`, `Lead` created, `submitted_lead`
  set) — how does the server deterministically recognize "this is the
  same submission" rather than treating it as a new one?
  - **The true-concurrency case is already solvable, no gap there:** two
    requests racing while a `FormDraft` is still `open`/`submitting` both
    resolve to the *same* row via the existing
    `owner=…, form_type=…, status__in=ACTIVE_STATUSES` lookup (there is
    at most one such row per owner, enforced by
    `unique_active_form_draft_per_owner_and_form_type`), so
    `select_for_update()` on that shared row correctly serializes them —
    the loser, once unblocked, re-reads the row's now-committed state
    (`status="submitted"`, `submitted_lead` set) and can safely redirect
    to that exact `Lead` with zero guessing, since it is the literal same
    row both requests contended for.
  - **The gap is the sequential case** (first attempt already fully
    committed and released its lock before the retry's request even
    begins): at that point the draft's status is already `submitted`, so
    it is excluded from `ACTIVE_STATUSES` and the same lookup finds
    nothing. Every fallback considered collapses into one of the
    heuristics this phase's own instructions explicitly rule out, and
    each was checked concretely, not just named and dismissed:
    - *"the owner's most-recently-submitted draft"* — breaks the moment
      the same owner has a second, genuinely unrelated real submission
      with no active draft ever re-created in between (realistic: e.g.
      autosave never fired before that second submit). That second,
      real Lead would be silently swallowed and the customer would be
      redirected to the *first* Lead's old tracking code instead of
      getting a new one.
    - *"the owner's highest-`pk` draft for this form_type"* — the exact
      same failure mode as above, just with a different tiebreaker
      (creation order instead of update time); still cannot distinguish
      "this is a retry of the draft I already finalized" from "no draft
      was ever created for this separate submission."
    - *the CSRF token* — stable for the whole Django *session* (not
      per-page-render, not per-submission), so two genuinely different
      real submissions in the same login session would carry the
      identical token; using it as an idempotency key would wrongly
      collapse them.
    - *a time window, revision-alone, or form-content match* — named and
      forbidden explicitly in this phase's own instructions; each has
      the same fatal flaw as above (cannot tell "retry of a completed
      submission" from "a new submission that happens to look similar or
      arrive soon after").
    No field, header, or session value already flowing through the
    contact form's POST (a plain `ModelForm` submission — no hidden
    idempotency input, no revision, no draft id; the draft's own primary
    key is deliberately never exposed to the client, by design, since
    V2.1-B1) can distinguish these two cases. **Conclusion: the current
    data/request contract is not sufficient to identify a sequential
    replay deterministically — implementing a fallback anyway would mean
    shipping exactly one of the ruled-out heuristics.** Per this phase's
    own explicit instruction, no such heuristic was implemented; the
    phase is `BLOCKED` before any product code was written.
  - **Precedent found, not invented:** this exact class of problem —
    "make a POST that creates a resource safely replayable" — is already
    solved elsewhere in this codebase for `DemoSelection`
    (`projects/views/projects.py`'s `DemoConfigureView` +
    `DemoPreviewView`): a `submission_token` is minted server-side on
    every `GET` render (`secrets.token_urlsafe(24)`), carried as a hidden
    form field, and enforced via a real, globally-unique
    `DemoSelection.submission_token` column
    (`projects/migrations/0006_demoselection_submission_token.py`) — a
    resubmission of the same token reuses the row it already created
    (`existing = DemoSelection.objects.filter(submission_token=…).first()`),
    a genuine concurrent race is resolved via `IntegrityError` on the
    unique constraint inside its own `transaction.atomic()` savepoint,
    and a stale token (e.g. a bfcache-restored page) is rejected rather
    than silently reused. This is a proven, already-shipped, already-
    tested idiom in this exact project for exactly this problem — not a
    speculative new pattern.
  - **Two low-risk designs proposed** (at most one should be picked,
    each needs explicit human authorization since both touch the
    migration state and/or the public HTML contract, which this phase
    was not authorized to change unilaterally):
    - **Design A (recommended — mirrors the proven `DemoSelection`
      precedent exactly).** Add one additive, nullable, unique field —
      e.g. `FormDraft.submission_token =
      CharField(max_length=64, unique=True, null=True, blank=True,
      db_index=True)` (one small migration, reversible by dropping the
      column, no data migration). Mint a fresh token server-side every
      time `leads/contact.html` is rendered for an authenticated
      non-staff customer with an active draft (mirroring
      `DemoPreviewView`'s `submission_token=secrets.token_urlsafe(24)` in
      `get_context_data`), rendered as one new hidden input in the
      existing Django form (a new, but non-secret, single-purpose value
      entering the public HTML contract — it grants no capability beyond
      what the authenticated session already grants, exactly like
      `DemoSelection`'s). On final POST, the finalize service checks:
      empty/missing token → reject as a malformed submission (same as a
      missing token today in `DemoConfigureView`); token already stored
      on a `submitted` `FormDraft` for *this owner* → this is
      deterministically the same submission, redirect to its
      `submitted_lead`'s existing thank-you page, no new `Lead`; token
      not yet seen → this is the first attempt, proceed with the atomic
      transition, storing the token on the draft as part of the same
      write. A genuine concurrent race on the same token is resolved by
      catching `IntegrityError` from the unique constraint inside its own
      `transaction.atomic()` savepoint (exactly `DemoConfigureView`'s
      `create_selection()` pattern), never a bare `try/except` that could
      poison the outer request transaction. Trade-off: exactly closes the
      sequential-replay gap with a pattern this project has already
      reviewed and shipped once; the cost is one migration plus one new,
      narrowly-scoped, non-secret token in the rendered HTML.
    - **Design B (no new field, larger flow change, not preferred).**
      Route final submission through a new authenticated JSON endpoint
      (alongside the existing `leads:draft`/`leads:draft_delete`,
      analogous to `save_draft_fields`'s own contract) that requires the
      client to send `expected_revision` — a concept that already exists
      in the draft API, so no new field on the model — and defines the
      retry outcome precisely in terms of revision arithmetic (a request
      whose `expected_revision` no longer matches, where the *current*
      draft is `submitted` at exactly `expected_revision + 1`, is
      recognized as the already-completed result of that exact call).
      Trade-off: reuses an existing concept instead of adding a column,
      but requires replacing the wizard's current plain `ModelForm` POST
      + full-page redirect/`document.write` flow with a JSON call the
      client must correctly sequence with its already-fragile network-
      retry/offline handling — a materially larger and riskier change to
      the actual submission flow than Design A's additive field, for a
      framework this phase was not asked to build. Not recommended unless
      Design A's new HTML token is specifically unacceptable.
  - Neither design was implemented — both are proposals awaiting an
    explicit decision. No migration was created; no field, endpoint, or
    template change exists on disk from this phase. **(Historical —
    superseded by the explicit authorization and implementation below.)**
- **V2.1-D — implemented and verified (Design A, corrected).** The user
  gave explicit architectural authorization ("Design A اصلاح‌شده تأیید
  است و باید اجرا شود") with one corrected constraint on top of the
  analysis above: the new token must resolve *both* true concurrency
  and sequential replay-after-commit — `expected_revision`/Design B was
  explicitly rejected.
  - **Schema:** `FormDraft.submission_token` —
    `CharField(max_length=64, unique=True, null=True, blank=True)`, no
    `db_index=True` (the unique constraint already creates one). One
    additive migration, `leads/migrations/0008_formdraft_submission_token.py`
    — no data migration, confirmed never applied to the permanent local
    `db.sqlite3`.
  - **Token carriage:** minted with `secrets.token_urlsafe(24)` on every
    ordinary GET of `leads/contact.html` for an authenticated, non-staff,
    non-superuser customer only (mirrors `DemoSelection.submission_token`
    exactly); rendered as one hidden `final_submission_token` input; on a
    validation-error rerender the same POSTed value is echoed back
    verbatim instead of minting a new one; never in a query string,
    `localStorage`/`sessionStorage`, the Draft JSON API, logs, email, or
    admin/export views. Guest/staff/superuser POST/GET paths are
    byte-for-byte unchanged — no `FormDraft` is ever touched for them.
  - **`leads/form_draft_service.finalize_form_draft_to_lead`** is the
    sole authority for Draft→Lead conversion: locks the owner row via
    `select_for_update()`; re-verifies non-staff/active; searches *all*
    statuses (not just `ACTIVE_STATUSES`) for a `FormDraft` matching
    `owner + form_type + submission_token`; on a first-seen token,
    reuses the owner's active draft (locked) or builds a minimal valid
    one from the final form's five non-sensitive fields, attaches the
    token, transitions `→submitting→submitted`, builds the `Lead` from
    `form.cleaned_data` (never the stale draft), preserves the demo
    snapshot, and registers the notification email via
    `transaction.on_commit()` inside the same atomic block — exactly
    once, only on the genuinely-new-Lead path. On a replay with the same
    token, the new request's canonical data is compared against the
    original `submitted_lead` itself (service id, normalized nullable
    fields, normalized phone) — identical → same `Lead`/tracking code,
    no new `Lead`, no second email; different → a safe bilingual
    conflict response, no `Lead` ever created or modified. A token
    belonging to another owner is rejected with the same message as an
    invalid token (`ForeignSubmissionTokenError` subclasses
    `InvalidSubmissionTokenError`), revealing nothing about its
    existence. A genuine `IntegrityError` race (last line of defense
    only — the owner lock already serializes same-owner races) is
    caught in a nested `transaction.atomic()` savepoint, outside of
    which the token is re-read and only an exact owner+content match
    returns the previous `Lead`. The per-IP rate limiter is invoked only
    on the genuinely-new-Lead path, after the token/submitting write
    succeeds — a replay is never rate-limited — and the view only clears
    its own rate-limit cache key on an unexpected failure, never a
    shared key another concurrent request may hold.
  - **Evidence:** `leads.test_finalize` (new, 37 tests) plus the full
    required targeted suite — `leads.test_finalize`,
    `leads.test_contact_server_draft_ui`, `leads.test_draft_api`,
    `leads.test_form_draft`, `leads.test_demo_handoff`, and the whole
    `leads` app — 232 tests, all passing, 15 correctly skipped
    (PostgreSQL-only), on SQLite. The same 37 `test_finalize` tests,
    including the 3 PostgreSQL-only concurrency/rollback tests, all pass
    on real isolated PostgreSQL (`arvion_ci_local`); the concurrency
    (`threading.Barrier(2)`, two truly simultaneous same-token requests
    converge to exactly one `Lead`) and rollback (`SELECT 1/0` injected
    between `Lead` creation and the draft's `submitted` write, proven to
    roll back both and leave the outer transaction usable afterward)
    subset was repeated 5 additional times, all clean. `check` (0
    issues), migration dry-run ("No changes detected"), `node --check`
    on `wizard-engine.js` (untouched, no JS change was needed since
    `FormData(form)` already includes any new hidden input), and
    `git diff --check` all passed. Full real-browser verification on a
    disposable SQLite environment covered: complete authenticated fa and
    en journeys ending at real tracking-code thanks pages; token
    stability across a validation rerender; a genuine repeated POST with
    the same token producing no second `Lead` (confirmed via shell); a
    real `setOffline`/reconnect/retry sequence producing exactly one
    `Lead`; no submitted-draft banner on return to the form; 320px/390px
    with no horizontal scroll; zero JavaScript exceptions throughout.
  - **Two pre-existing tests** (`test_no_sensitive_token_or_id_in_html_even_with_an_existing_draft`,
    `test_no_forbidden_tokens_anywhere_after_a_successful_retry`) had a
    blanket "no substring `submission_token`" assertion that predated
    this phase and would now false-positive on the legitimate
    `final_submission_token` field name; corrected to assert the
    specific internal-leak shape (`data-submission-token`) and
    `draft.submission_token is None` instead — the underlying guarantee
    (the *internal* DB token never leaks) is unchanged and still
    enforced.
  - Files touched: `leads/models/form_draft.py`,
    `leads/migrations/0008_formdraft_submission_token.py`,
    `leads/form_draft_service.py`, `leads/views/contact.py`,
    `leads/templates/leads/contact.html`,
    `leads/test_contact_server_draft_ui.py`, `leads/test_demo_handoff.py`,
    `leads/test_finalize.py` (new). No CRM/Clinic, contract, exam, or
    management-notification code touched. Not pushed, deployed, or
    migrated on production; `0008_formdraft_submission_token` was never
    applied to the permanent local `db.sqlite3`.
  - **Remaining risk, unrelated to this phase:** the pre-existing
    `assessments/services.py`'s `revoke_assessment_access` PostgreSQL
    incompatibility (flagged since V2.1-B2) remains unfixed and
    untouched — still needs separate human prioritization. The
    saved-drafts dashboard remains `NOT_STARTED` by explicit scope
    boundary.
- **V2.1-D corrective (`7e5e621` review findings fixed).** Review of the
  `7e5e621` implementation found two defects before any production use;
  both are fixed here, in a separate commit, with `7e5e621` and
  `6d75c4f` left unamended.
  - **P1 — incomplete canonical submission identity.**
    `_lead_canonical_signature`/`_cleaned_data_canonical_signature`
    (renamed `_submission_canonical_signature`, which now also takes the
    caller's resolved `demo_selection`) compared only `form.cleaned_data`
    against the stored `Lead`, never `demo_selection_id` — so a consumed
    token replayed with identical form content but a different, added, or
    removed demo selection could have been wrongly accepted as the same
    submission. Fixed: `demo_selection_id` (the `Lead`'s stored value vs.
    `demo_selection.pk if demo_selection is not None else None` from this
    exact request) is now part of the signature both sides compare,
    renamed `_lead_matches_this_submission(lead, cleaned_data,
    demo_selection)`, used identically at both call sites — the initial
    token lookup and the `IntegrityError` recovery block. No
    `DemoSelection` is ever reconstructed from a draft's frozen
    `demo_snapshot`; the caller's own already-resolved, session-bound
    `demo_selection` is the only source, exactly as before. No token,
    draft id, or confidential value appears in any of the three error
    messages this can lead to.
  - **P2 — wrong exception on an untraceable `IntegrityError` recovery.**
    In the `except IntegrityError:` recovery block, `recovered is None`
    (no `FormDraft` row exists for *this* owner+form_type+token — meaning
    the row that actually won the real unique-constraint race belongs to
    a different owner entirely) previously fell through to
    `SubmissionConflictError`, the same response as a genuine same-owner
    content mismatch — wrong, and inconsistent with the initial lookup's
    own foreign-token handling one branch above. Fixed: `recovered is
    None` now raises `InvalidSubmissionTokenError` (via the same
    `_raise_invalid_submission_token()` helper the rest of the function
    already uses), making a cross-owner unique collision, a foreign
    token found at the initial lookup, and a plain unknown token all
    outwardly indistinguishable, as the token-secrecy contract requires.
    `recovered is not None` but never `submitted`
    (`submitted_lead_id is None`) still safely raises
    `SubmissionConflictError` and creates nothing — this state should be
    unreachable under the owner-row lock, so it is treated as untrusted
    rather than resumed. `recovered` found and `submitted` still compares
    content+demo via `_lead_matches_this_submission` exactly like the
    primary lookup path.
  - **Tests added:** `leads.test_finalize.FinalizeFormDraftToLeadTests`
    gained 4 demo-identity tests (same demo → valid replay; different
    demo, demo removed, demo added → each a `SubmissionConflictError`,
    with the original `Lead`/`FormDraft` revision left byte-for-byte
    unchanged and the notification firing only once, proven via
    `captureOnCommitCallbacks`). A new
    `FinalizeIntegrityErrorRecoveryTests` class gives deterministic,
    SQLite-level branch coverage of all four `except IntegrityError`
    outcomes (no record for this owner → `InvalidSubmissionTokenError`;
    a same-owner record that never reached `submitted` → safe
    `SubmissionConflictError`; a `submitted` record with matching
    content+demo → valid replay; one with different content → conflict) —
    each forced via a real `IntegrityError` from a mocked `.create()` plus
    a narrowly-targeted mock of the *one* token-only `.filter()` call that
    represents the racing read, never the owner+form_type-scoped recovery
    query itself, which always runs for real. A new, real-PostgreSQL-only
    `FinalizeFormDraftPostgresUniqueCollisionTests` (in the required
    `@unittest.skipUnless(connection.vendor == "postgresql", ...)` class)
    races two different real owners against the exact same token with a
    `threading.Barrier(2)` placed only at the real
    `FormDraft.objects.create(...)` call (per instruction: the barrier
    only synchronizes the insert call site, never fakes the insert or the
    error) — both threads' independent, unlocked initial lookups
    genuinely complete before either inserts, both real inserts reach
    PostgreSQL, and the actual unique constraint decides one winner: the
    loser gets a real `InvalidSubmissionTokenError`, exactly one `Lead`
    and one token-bearing `FormDraft` exist afterward, the loser's own
    row count for that owner is zero (no information about the winner
    leaked), and the loser's own connection runs a real, healthy query
    immediately after the handled `IntegrityError`.
  - **Evidence:** `leads.test_finalize` (46 tests, up from 37) passes on
    SQLite (4 correctly skipped) and on real isolated PostgreSQL
    (`arvion_ci_local`, 46/46, 0 skipped) — the concurrency/collision/
    rollback subset (4 tests) was run once plus 5 additional repeats on
    PostgreSQL, all clean. Full required targeted suite
    (`leads.test_finalize`+`leads.test_contact_server_draft_ui`+
    `leads.test_draft_api`+`leads.test_form_draft`+`leads.test_demo_handoff`+
    `leads`) on SQLite: 241 tests, all passing, 16 correctly skipped —
    no regression from the 232/15 baseline before this corrective phase
    (9 new tests: 4 demo-identity + 4 deterministic recovery + 1
    PostgreSQL-only collision test, which is one of the 16 skips on
    SQLite). `check` (0 issues), migration dry-run ("No changes
    detected" — migration `0008` untouched, no new migration), and
    `git diff --check` (clean) all passed. Only `leads/form_draft_service.py`
    and `leads/test_finalize.py` touched — no template, JavaScript,
    migration, rate-limit, lifecycle, or `transaction.on_commit()` change,
    per the explicit scope boundary. The unrelated, pre-existing
    `assessments/services.py` PostgreSQL incompatibility remains flagged,
    unfixed, and not hidden. Not pushed, deployed, or migrated on
    production.
- **V2.1-C2 — account dashboard order-draft section.** UI/display-only
  phase: gives an authenticated customer a fast, safe way to see an
  unfinished `leads_contact` order draft from their account dashboard,
  without touching `FormDraft` writes, finalize/idempotency, rate
  limiting, `transaction.on_commit()`, or any migration.
  - **Data source:** `accounts.views.dashboard` calls the existing,
    unmodified `leads.form_draft_service.get_active_draft(request.user,
    "leads_contact")` — strictly read-only, scoped to the requesting
    owner, excludes expired/submitted drafts by construction (its own
    query is `status__in=ACTIVE_STATUSES, expires_at__gt=now`). No new
    query path, no write, no `select_for_update()`.
  - **Safe view model:** new `leads/draft_dashboard.py` —
    `build_draft_dashboard_card(draft)` — a pure function returning a
    frozen `DraftDashboardCard` dataclass (or `None`) with only: 1-based
    current step and total steps, a rounded progress percent,
    `updated_at`/`expires_at`/days-remaining, the four allowlisted choice
    fields translated to both fa and en (a display-only label dict
    mirroring `LeadForm`'s own Persian labels and `Lead`'s English choice
    text verbatim — kept separate rather than refactoring the submission
    form, since this phase changes only read-only display), the selected
    service's bilingual title (looked up by the stored `service_id`, or
    `None` if deleted), and a `DraftDemoSummary` (title/category/brand)
    built only from the frozen `demo_snapshot`, never a live
    `DemoSelection`. Never exposes `submission_token`, the draft's own
    id, the owner's id, or `revision`. Defensive against malformed input
    (non-dict `fields`/`demo_snapshot`, missing snapshot keys, wrong
    types) — always returns a valid card or `None`, never raises.
  - **Template:** `accounts/templates/accounts/dashboard.html` gained:
    a new `account-compass` entry ("Project enquiry" / "سفارش پروژه")
    — links to `#my-order-draft` and shows "in progress · step N of 3"
    when a draft exists, otherwise links directly to `leads:contact` and
    shows "start a project enquiry"; a new draft card (`#my-order-draft`,
    only rendered when a draft exists), positioned before the assessments
    panel inside a new `.account-main` wrapper so column layout is
    preserved; a "browse demos & pick a design" sidebar link, shown only
    in the no-draft state (`projects:demo_gallery`). No big empty-state
    panel is shown for "no draft" — only the compact compass shortcut and
    the one sidebar link change. The continue CTA
    ("ادامه تکمیل سفارش" / "Continue enquiry") always links to the plain
    `leads:contact` URL with no draft id, token, or query string — the
    contact page finds the draft itself via the existing owner-bound
    `get_active_draft` call already wired since V2.1-C1; V2.1-C1's
    reconciliation behavior (draft content never applied without explicit
    customer action) and the existing delete path on the contact page are
    both untouched. `assessment_extras`'s existing `fa_digits` template
    filter (already loaded cross-app by `leads/templates/leads/
    contact.html`) is reused for Persian-digit step/percent/date display;
    English keeps plain digits.
  - **Design:** new CSS only in `accounts/static/accounts/css/
    dashboard.css` (cache-bust bumped `?v=4` → `?v=5`), built entirely on
    the file's own existing design tokens (`--accent`, `--line`,
    `--color-surface-2`, `--radius-*`, `--motion-*`) — no new hardcoded
    color. `.account-compass` grid widened from 3 to 4 columns (desktop)
    with the now-unnecessary `:last-child` 900px-breakpoint span rule
    removed (4 items fill a 2×2 grid evenly). A `role="progressbar"` with
    `aria-valuenow/min/max` and a bilingual `aria-label` gives the
    progress bar a real accessible alternative. All new interactive
    elements are plain `<a>`/existing `.button` markup, inheriting the
    site's global `:focus-visible` outline and `prefers-reduced-motion`
    handling (both pre-existing, site-wide, unmodified) with no new
    per-component overrides needed. `.account-draft-meta` collapses to a
    single column under 480px; long demo/service text wraps via
    `overflow-wrap:anywhere` on the `dd`.
  - **Evidence:** new `accounts/test_dashboard_draft.py` (18 tests)
    covers: login required; no-draft shortcut with no draft card; a
    submitted draft never treated as unfinished; another owner's draft
    never shown; expired/submitted drafts never shown; all five
    allowlisted values render as correct bilingual labels in both fa and
    en (with raw stored values like `webapp`/`50_150`/`one_three`
    asserted absent); demo snapshot renders in the right language; an
    empty/malformed snapshot does not crash; no forbidden identifier
    (`submission_token`/`session_key`/`public_token`/`data-draft-id`/
    `data-owner-id`/`data-user-id`/`revision`) or contact/free-text field
    reaches the HTML; the continue CTA URL carries no id/token/query
    string; a GET never mutates or renews the draft (`revision`/
    `updated_at`/`expires_at`/`status` all compared before/after); query
    count is flat regardless of 30 additional historical (expired) drafts
    for the same owner (`CaptureQueriesContext`, exact count equality);
    and the pre-existing assessments/purchases/support sections still
    render without regression. `accounts` app full suite (255 tests, 0
    skips) plus `leads.test_contact_server_draft_ui`+
    `leads.test_draft_api`+`leads.test_form_draft` (237 tests total, 11
    skips) all pass. `check` (0 issues), migration dry-run ("No changes
    detected" — no model/migration touched), and `git diff --check`
    (clean) all passed.
  - **Browser evidence:** disposable SQLite environment (port 8833,
    three disposable customers, one with an active draft + demo
    snapshot, one with none). Confirmed live: the fa dashboard renders
    the full card (step 2 of 3, 67%, service/budget/timeline/contact
    labels, demo name/category/brand, last-saved/expiry with Persian
    digits, working `#my-order-draft` anchor from the compass); the en
    dashboard renders the same card in English with the "Continue
    enquiry" CTA linking to a clean `/en/contact/` URL; the no-draft
    account shows the compact compass shortcut (linking straight to
    `/fa/contact/`) and the sidebar demo-browsing link, with no draft
    card and no big empty-state panel; light and dark themes both render
    the card cleanly on the existing tokens; 390px and 320px both show
    zero horizontal scroll (`scrollWidth === clientWidth`) with the meta
    grid collapsing to one column and full-width buttons; keyboard Tab
    reaches both the compass "Project enquiry" item and the card's
    "Continue enquiry" button with a visible focus outline and a 44px+
    hit target. Zero JavaScript console errors or failed requests across
    the entire pass (one pre-existing, unrelated `AudioContext` autoplay
    warning on the login page, not caused by this phase). The
    site's own scroll-reveal (`data-ui-reveal`/`IntersectionObserver`)
    already supports `prefers-reduced-motion` — confirmed by emulating
    it, which correctly and immediately marked the new draft card
    visible exactly like every pre-existing panel; this is unmodified,
    site-wide behavior, not something built for this phase.
  - **Known, pre-existing, out-of-scope limitation surfaced at the time
    (since fixed on the display side by the corrective phase below):**
    `demo_snapshot`'s `brand` key has always been a single, non-bilingual
    value (falling back to `DemoTemplate.fictional_brand_fa` specifically
    when the customer never customized it — see
    `projects/demo_snapshots.py`), unlike `template_title_fa/en` and
    `category_fa/en`, which are properly bilingual. This meant an English
    dashboard card could show a Persian brand name when the customer
    never typed a custom one. The corrective phase below removes `brand`
    from what this card reads/shows entirely, closing the leak without
    touching the underlying snapshot schema.
  - Files touched: `accounts/views.py`, `accounts/templates/accounts/
    dashboard.html`, `accounts/static/accounts/css/dashboard.css`,
    `accounts/test_dashboard_draft.py` (new), `leads/draft_dashboard.py`
    (new). No `leads/form_draft_service.py`, `leads/views/contact.py`,
    template, migration, or JS file touched. Not pushed, deployed, or
    migrated on production.
- **V2.1-C2 corrective — demo brand removed from the dashboard card.**
  Fixes the language-isolation defect the phase above surfaced: the
  draft card's "Reference demo" row appended `demo.brand` in BOTH
  languages, but `demo_snapshot["brand"]` is the one snapshot field that
  is not bilingual (it can be — and, absent a customer override, always
  is — the template's Persian `fictional_brand_fa`, regardless of which
  language is rendering). This broke the "no Persian text in the English
  UI" guarantee whenever a draft's demo had no customer-typed brand
  override.
  - **Fix:** `brand` was removed entirely from
    `leads.draft_dashboard.DraftDemoSummary`, from
    `_DEMO_SNAPSHOT_REQUIRED_KEYS` (so a snapshot missing it — including
    every pre-existing/legacy snapshot with only the two bilingual pairs
    — still renders normally instead of having the whole demo row
    disappear), and from the `_demo_summary()` construction. The
    template's demo row (`accounts/templates/accounts/dashboard.html`)
    now shows only `template_title_fa`/`category_fa` (fa) or
    `template_title_en`/`category_en` (en) — both fully bilingual
    snapshot fields. `demo_snapshot`'s own shape, `build_demo_selection_
    snapshot`, the `FormDraft`/`DemoSelection`/`DemoTemplate` models, all
    migrations, the order/contact form, and every management-portal page
    that also renders a demo snapshot are untouched — this fix is scoped
    entirely to what the dashboard card itself reads and displays. No new
    live `DemoSelection`/`DemoTemplate` lookup was added; the demo row
    still comes only from the already-frozen `demo_snapshot`, unchanged
    since V2.1-C2. The CSS cache-bust was not bumped since no CSS
    changed (`dashboard.css` stays untouched at `?v=5`).
  - **Evidence:** `accounts/test_dashboard_draft.py` grew from 18 to 21
    tests: the existing bilingual-language test now also asserts neither
    the fa nor the en brand string ever appears in either language's
    response; a new test confirms a legacy snapshot holding only the
    four bilingual keys (no `brand` at all) still renders its title and
    category in both languages; a new fa-focused test confirms
    `template_title_fa`/`category_fa` render correctly and the brand
    strings (fa or en) never appear; a new, explicit regression test
    seeds a snapshot whose `brand` is a fully-Persian string
    ("برند کاملاً فارسی") and asserts the English dashboard shows the
    English title/category, never that Persian string anywhere in the
    page, and — parsing out just the "Reference demo" row's own HTML —
    contains zero characters in the Persian/Arabic Unicode block. All 21
    tests pass. `accounts` full suite (unchanged count) plus
    `leads.test_contact_server_draft_ui`+`leads.test_draft_api`+
    `leads.test_form_draft`+`leads.test_finalize`+`leads.test_demo_handoff`
    (323 tests total, 18 skips) all pass, zero regression. Every existing
    privacy/no-leak test (`submission_token`/`session_key`/
    `public_token`/`data-draft-id`/`data-owner-id`/`data-user-id`/
    `revision`/free-text fields) was re-run unmodified and still passes —
    the fix only removed a display field, it did not touch or weaken any
    security assertion. `check` (0 issues), migration dry-run ("No
    changes detected"), and `git diff --check` (clean) all passed.
  - **Browser evidence:** disposable SQLite environment (fresh port,
    one customer with an active draft whose demo snapshot's `brand` was
    seeded as a fully-Persian string with no customer override).
    Confirmed live: the fa dashboard's "دموی مرجع" row shows only the
    demo's title and category (no brand segment at all); the en
    dashboard's "Reference demo" row shows only the English title and
    category — the Persian brand string does not appear anywhere on the
    page, confirmed both visually and by a direct DOM query on the demo
    row's own text content (`/[؀-ۿ]/` test returns `false`).
    320px and 390px both show zero horizontal scroll in light and dark
    themes (`scrollWidth === clientWidth` in all four combinations);
    keyboards Tab still reaches the "Continue enquiry" CTA with a
    visible focus outline and a 44px+ hit target, unaffected by the fix.
    Zero JavaScript console errors or failed requests throughout.
  - Files touched: `leads/draft_dashboard.py`, `accounts/templates/
    accounts/dashboard.html`, `accounts/test_dashboard_draft.py`. No
    `demo_snapshot` schema, snapshot builder, model, migration, order
    form, management-portal page, or CSS file touched. Not pushed,
    deployed, or migrated on production.
- **V2.1-E0 — PostgreSQL-incompatible lock in exam-access revocation
  fixed.** Unrelated to the V2.1 leads-contact/FormDraft line — this is
  the `assessments`/exam-entitlement domain. Closes an issue flagged as
  a remaining risk since V2.1-B2 and repeated, unfixed, through every
  V2.1 phase since.
  - **Root cause, reproduced first:** `assessments.services.
    revoke_assessment_access` ran
    `ExamEntitlement.objects.select_for_update().select_related(
    "attempt").filter(order=order).first()`. `Attempt.entitlement` is a
    `OneToOneField(ExamEntitlement, related_name="attempt")`, so an
    entitlement may have zero or one `Attempt` row —
    `select_related("attempt")` builds a `LEFT OUTER JOIN`, and
    PostgreSQL refuses `FOR UPDATE` on the nullable side of an outer
    join. Reproduced with the exact command supplied
    (`DATABASE_URL=postgresql://rwin@localhost:5432/arvion_ci_local
    DJANGO_SETTINGS_MODULE=arvion.settings.ci .venv/bin/python
    manage.py test assessments.tests.AssessmentEngineTests.
    test_manager_revocation_stops_active_attempt_and_blocks_restart`),
    which failed with `psycopg.errors.FeatureNotSupported: FOR UPDATE
    cannot be applied to the nullable side of an outer join` /
    `django.db.utils.NotSupportedError` at that exact line, before any
    fix was made.
  - **Fix — locking design:** the entitlement is now locked with
    `ExamEntitlement.objects.select_for_update().filter(order=order)
    .first()` (no `select_related`), then the (optional) `Attempt` is
    locked via its own, independent query:
    `Attempt.objects.select_for_update().filter(entitlement=
    entitlement).first()` — a plain equality filter on the FK, never a
    join that could put `FOR UPDATE` on a nullable side. The
    already-revoked idempotent-return check now happens after both rows
    are locked (previously it happened before the attempt was even
    read), so the returned `attempt` is always the real, locked instance
    rather than an on-the-fly lazy fetch. No behavior change for either
    caller: `management_portal.views.customer_assessment_access_revoke`
    only reads `attempt.pk` from the return value, and the pre-existing
    `assessments.tests` assertions on the return tuple's shape are
    unchanged.
  - **Evidence:** the exact reproduction command now passes on real
    PostgreSQL. 4 new tests added to `AssessmentEngineTests` in
    `assessments/tests.py`: revoking an entitlement with no `Attempt` at
    all (the precise shape that produced the outer join) still works and
    returns `None` for the stopped attempt; revoking an already-revoked
    entitlement a second time is idempotent (`changed=False`, the
    original `revoked_at`/`revocation_reason` are never overwritten by a
    later, different-reasoned call); revocation never rewrites payment
    evidence (`Order.amount_irr`/`status` and an approved
    `ManualPaymentSubmission`'s `status`/`reference_number`/
    `reviewed_at` are all unchanged after revocation). A new
    PostgreSQL-only `AssessmentAccessRevocationConcurrencyTests`
    (`TransactionTestCase`, `threading.Barrier(2)`, mirroring the
    existing `AssessmentFinishConcurrencyTests` pattern) proves two
    truly concurrent `revoke_assessment_access` calls for the same order
    converge safely: no exception on either thread, exactly one
    `changed=True` and one `changed=False`, the attempt ends up
    `"invalidated"` exactly once — run once plus 5 repeats on real
    PostgreSQL, all clean. `assessments.tests.AssessmentEngineTests` (61
    tests) and the full `assessments` app plus
    `management_portal.tests.AssessmentAccessControlTests` (134 tests, 2
    skips on SQLite, 0 skips on PostgreSQL) all pass on both SQLite and
    real isolated PostgreSQL, zero regression. `check` (0 issues),
    migration dry-run ("No changes detected" — no migration, as
    instructed), and `git diff --check` (clean) all passed.
  - Files touched: `assessments/services.py` (one function),
    `assessments/tests.py` (additive only — no existing test modified).
    No migration, model, management-portal view, or template touched.
    Not pushed, deployed, or migrated on production.
- **V2.1-E1 — `cleanup_form_drafts` management command.** A manually-run
  (no cron/Celery Beat/schedule added) command to remove `FormDraft`
  rows that are truly done and unreachable — never invoked from any
  view, endpoint, or UI.
  - **Eligibility policy (all four required, enforced identically at
    selection and at delete time):** `status="expired"` (never `open`/
    `submitting`/`submitted`, regardless of age); `expires_at` older
    than the retention window (default 30 days — an expired-but-recent
    draft is kept longer for support/debugging); `submitted_lead IS
    NULL`; `submission_token IS NULL`. The last two guard the V2.1-D
    idempotency contract directly: a token or an attached Lead is
    exactly what a sequential retry needs to find to recognize its own
    prior submission, so either one present permanently excludes a row
    from deletion no matter how old.
  - **Command behavior:** `leads/management/commands/
    cleanup_form_drafts.py`. Dry-run by default (reports a count only);
    `--apply` required to actually delete. `--older-than-days` (default
    30) and `--batch-size` (default 500) are both validated as positive
    integers before any query runs — `0` or negative raises
    `CommandError` immediately, no write attempted. Deletion proceeds in
    batches (`order_by("pk")[:batch_size]` for id selection), and the
    delete step re-applies the full four-condition filter combined with
    `pk__in` — never `pk__in` alone — so a row that stops being eligible
    (reopened, submitted, attached to a Lead, or given a token) in the
    window between selection and delete survives, proven by a dedicated
    test that mutates the row's status inside a patched `.filter()` call
    positioned exactly in that window. Output is a single aggregate line
    (a count plus a plain-language policy description with no field
    names, ids, or values) for both the dry-run and the `--apply`
    outcome — no owner, email, mobile, id, `fields`, `demo_snapshot`, or
    token value ever printed, verified by a dedicated test using a real
    email/fields payload. `FormDraft` deletion cannot cascade to `Lead`
    or `User` (no FK from either points at `FormDraft`, and the
    eligibility filter itself already requires `submitted_lead IS
    NULL`), confirmed by a dedicated test with an unrelated Lead and the
    draft's own owner both asserted to survive.
  - **Evidence:** new `leads/test_cleanup_form_drafts.py` (12 tests) —
    dry-run reports and deletes nothing; `--apply` deletes only the row
    matching all four conditions, leaving a wrong-status row, a
    Lead-attached row, and a token-bearing row untouched; a
    freshly-expired row (inside the retention window) is not deleted;
    `open`/`submitting`/`submitted` rows are never deleted even at 365
    days old; a small `--batch-size` (2, for 5 eligible rows) correctly
    processes multiple batches; `0`/negative `--older-than-days` and
    `--batch-size` are each rejected with `CommandError`, writing
    nothing; the race-safety test above; the no-leak-in-output test
    above; the no-cascade test above. All 12 pass on SQLite. The same
    12, plus `leads.test_form_draft`+`leads.test_finalize` (155 tests
    total), pass on both SQLite (11 skips, PostgreSQL-only) and real
    isolated PostgreSQL (`arvion_ci_local`, 0 skips), zero regression.
    `check` (0 issues), migration dry-run ("No changes detected" — no
    migration, as instructed), and `git diff --check` (clean) all
    passed.
  - Files touched (all new): `leads/management/__init__.py`,
    `leads/management/commands/__init__.py`, `leads/management/
    commands/cleanup_form_drafts.py`, `leads/test_cleanup_form_drafts.py`.
    No model, migration, `FormDraft` lifecycle function in `leads.
    form_draft_service`, `cleanup_demo_selections`, endpoint, or
    management-portal page touched. Not pushed, deployed, or run with
    `--apply` outside a test database; no dry-run was even run against
    the permanent local `db.sqlite3` this phase (test evidence alone
    was judged sufficient and lower-risk).
- **V2.1-E2 — Release Candidate gate audit.** Full audit of whether the
  29 local commits ahead of `origin/main` (`a1d6700`) are ready to push,
  per `AGENTS.md`/`release-check.sh`/`.github/workflows/quality.yml`/
  `docs/OPERATIONS_RUNBOOK_FA.md`/`ops/release.sh`. Verification and
  rehearsal only — no push, deploy, production connection, production
  migration, or `--apply` outside a test database.
  - **Git/diff audit:** all 74 changed files (13,914 insertions, 187
    deletions vs. `origin/main`) categorized: 2 docs/state, 5 new
    migrations, 9 `accounts` files, 1 settings file, 2 `assessments`
    files, 8 `core` files, 22 `leads` non-migration files, 10
    `management_portal` files, 15 `projects` non-migration files. No
    file deleted; `requirements.txt` unchanged (no new dependency to
    vet); `db.sqlite3` not tracked. Secret scan (`git diff origin/
    main..HEAD` grepped for AWS/Google/Slack key patterns, PEM headers,
    hardcoded `SECRET_KEY=`/`DATABASE_URL=` with embedded credentials):
    clean — the only `password="..."` matches are trivial test-fixture
    placeholders (`"x"`, `"safe-password"`, etc.), never a real secret.
    No `.env`, key, or backup file added. No customer-data file removed
    or replaced.
  - **The 5 release migrations, reviewed line by line:**
    `accounts.0004_activesession` (new `ActiveSession` table, one
    `OneToOneField` to the user), `projects.0006_demoselection_
    submission_token` (nullable unique `AddField`),
    `leads.0006_formdraft_and_more` (new `FormDraft` table plus its
    partial unique constraint), `leads.0007_formdraft_revision`
    (nullable-by-default `AddField`), `leads.0008_formdraft_
    submission_token` (nullable unique `AddField`) — all five are purely
    additive (`CreateModel`/`AddField`/`AddConstraint` only, no
    `RunPython`/`RunSQL`, no column removal, no `NOT NULL` without a
    default), and each app's migration numbering follows directly from
    `origin/main`'s last migration for that app with no fork/conflict.
  - **Local gate — `release-check.sh` on HEAD:** full pass —
    `manage.py check` (0 issues), `makemigrations --check --dry-run`
    ("No changes detected"), `pip check` ("No broken requirements
    found"), the full test suite (826 tests, 20 skips, all passing),
    the strict question-bank audit (`english`/`python-django`, 0
    editorial warnings each), `collectstatic --dry-run` (silent
    success), and the assessment benchmark (100 attempts, ~27–37/s
    throughput, no errors).
  - **CI-equivalent steps, run exactly as `.github/workflows/quality.
    yml` does, on HEAD:** `compileall` over every app (clean);
    `manage.py test --parallel 4 --verbosity 1` (826 tests, 20 skips,
    all passing); `manage.py test --shuffle=58291 --parallel 1
    --verbosity 1` — **initially FAILED** (see finding below), then
    passed cleanly after the fix, re-confirmed with a second, freshly
    generated random shuffle seed too; `audit_question_banks
    --strict-editorial` (pass); `node --check` on every tracked `*.js`
    file (clean); `bash -n` on every `ops/*.sh` file (clean); `git diff
    --check` (clean, no whitespace/conflict-marker issues).
  - **Finding #1 (found and fixed this phase) — test-isolation bug
    exposed only by the exact CI shuffle seed:** `leads.test_
    contact_server_draft_ui.ErrorRerenderStepMarkerTests.
    test_valid_submission_has_no_error_step_marker` expected a 302
    redirect but got 200 under `--shuffle=58291`. Root cause: this test
    posts a guest submission to the per-IP-rate-limited
    `leads:contact` endpoint without ever calling `cache.clear()` in
    `setUp` — Django's test client always uses the same fixed
    `REMOTE_ADDR`, the cache backend is not reset between tests, and
    the default rate-limit window is 60 seconds, so an earlier,
    unrelated test's own successful guest submission (still within the
    window, in this particular shuffle order) silently consumed the
    shared rate-limit slot and made this test's own POST spuriously
    fail validation instead of redirecting. Fixed with one `cache.
    clear()` call at the top of that test's `setUp` (the same
    established pattern already used in `leads.tests.LeadTests`).
    Re-ran the exact failing seed (now passes) plus one fresh random
    seed (also passes) — both on the default SQLite settings. This is a
    genuine, low-risk, test-only fix; no production code was touched
    for this finding.
  - **Finding #2 (found this phase, NOT fixed — see severity analysis)
    — a genuine, pre-existing, intermittent real-concurrency failure:**
    `accounts.tests.SingleSessionPostgresRaceTests.
    test_two_simultaneous_logins_converge_to_exactly_one_active_session`,
    run repeatedly (once during the shuffle run, plus 8 additional
    standalone repeats) against real isolated PostgreSQL, failed once
    on Python 3.12 (via `django.contrib.sessions.backends.base.
    UpdateError`, raised when `request.session.save()` finds 0 rows
    affected) and once more out of 8 repeats on Python 3.9 (the main
    `.venv`) — an observed flake rate around 10–15%, present on *both*
    Python versions, so this is not a 3.12-specific incompatibility.
    Root cause, traced through `accounts/signals.py`'s
    `enforce_single_session_on_login`: two real, near-simultaneous
    logins for the same user can interleave such that the *first*
    thread's own follow-up `request.session.save()` (simulating what
    `SessionMiddleware.process_response()` does in a real request) runs
    *after* the *second* thread's login has already committed and
    deleted the first thread's now-superseded `Session` row — the first
    thread's own save then legitimately finds nothing to update and
    Django's session backend raises `UpdateError`. This is a real,
    narrow, timing-sensitive race in newly-introduced (relative to
    `origin/main`) session-security code, not a hypothetical or
    test-only artifact: in a genuine production request, the same
    interleaving would surface as an occasional uncaught 500 on the
    *losing* side of two truly simultaneous login requests for one
    account (sub-second timing, essentially never triggered by a real
    human, self-recovers on retry). It does **not** cause data loss,
    does **not** bypass the single-session security guarantee itself
    (exactly one session still ends up active either way), and does
    **not** affect any other flow. It was **not** fixed in this phase:
    a correct fix requires either wrapping/retrying around Django's own
    session-save path or redesigning the eviction step, and rushing
    that into security-critical session code inside a release-audit
    phase — without its own dedicated design and test cycle — was
    judged higher-risk than leaving it documented and unresolved. Per
    the explicit instruction that a security-path test failure blocks
    the gate, this is reported as the reason for `BLOCKED`, not
    quietly downgraded to justify a pass.
  - **Python version matrix:** Python 3.11 is **not installed** on this
    machine (only System/Command-Line-Tools Python 3.9, used by the
    project's own `.venv`, and Homebrew Python 3.12) — per the explicit
    instruction, this is reported as unavailable, never as a false
    `PASS`. Python 3.12 **was** exercised, in a throwaway venv created
    with `/opt/homebrew/bin/python3.12 -m venv` outside the project
    (the project's own `.venv` was never touched, rebuilt, or
    replaced), dependencies installed from the unmodified
    `requirements.txt` (`pip check`: "No broken requirements found"),
    against real isolated PostgreSQL 16 (`arvion_ci_local`, matching
    CI's `postgres:16-alpine`) via `arvion.settings.ci`: `manage.py
    check` and `makemigrations --check --dry-run` both clean,
    `compileall` clean, the parallel test step 826/826 passing (0
    skips, real Postgres), and the shuffle step reproducing Finding #2
    once (see above) — otherwise clean. The throwaway venv was deleted
    with the rest of the scratch directory at the end of this phase.
  - **PostgreSQL migration rehearsal (forward → backward → forward
    again), on a disposable `release_rehearsal` database, never the
    permanent local database:** a temporary `git worktree` was checked
    out at `origin/main` and used to `migrate` `release_rehearsal` to
    the exact pre-release baseline schema, then non-sensitive structural
    fixtures were created directly through that worktree's own code
    (one `User`, one `Lead`, one `DemoTemplate`/`DemoSelection`, one
    `Exam`/`Order`/`ExamEntitlement`). The *same* database was then
    migrated forward using the current `HEAD` checkout: all 5 new
    migrations applied cleanly with no other pending migration, the
    baseline fixtures (`User`/`Lead`/`DemoSelection`/`Order`/
    `ExamEntitlement`) were all still readable afterward, and writing a
    new `FormDraft`, a new `ActiveSession`, and a duplicate
    `FormDraft.submission_token` value were all exercised directly —
    the duplicate correctly raised a real `IntegrityError` from the new
    unique constraint. **Backward migration was then rehearsed and is
    confirmed destructive to new data**: reverting `leads.0006/0007/
    0008`, `accounts.0004`, and `projects.0006` on the same database
    dropped the `FormDraft` and `ActiveSession` tables entirely and
    dropped `DemoSelection.submission_token` — the pre-release baseline
    fixtures survived intact throughout, but any `FormDraft`/
    `ActiveSession`/token data created after this release ships would
    be permanently lost by a migration rollback. Migrating forward
    again re-created a clean, healthy schema (`check`: 0 issues;
    `makemigrations --check --dry-run`: "No changes detected"). This
    finding — "code rollback is safe, migration rollback is not" — is
    now recorded in `docs/OPERATIONS_RUNBOOK_FA.md` (see below). The
    temporary worktree and the `release_rehearsal` database were both
    removed at the end of the rehearsal.
  - **Production settings check** (`arvion.settings.production`
    imported with fake, non-real environment values — no real provider,
    no real DSN, no message ever sent): `manage.py check --deploy`
    passed with 0 issues. Confirmed directly: `DEBUG=False` (inherited,
    never overridden for production); PostgreSQL enforced (`DATABASE_
    URL` must start with `postgresql://`/`postgres://`, raises
    otherwise); `PAYMENT_GATEWAY` in `{sandbox, free}` raises
    `RuntimeError`; `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` both
    `True` by default; `CSRF_TRUSTED_ORIGINS` resolves correctly;
    `SECURE_HSTS_SECONDS=31536000` with subdomains/preload both `True`
    when SSL redirect is on; S3 `STORAGES` backend wires correctly when
    `USE_S3_STORAGE=1`; `SMS_BACKEND=core.sms.backends.
    ConsoleSMSBackend` raises `RuntimeError` (a real, non-console
    backend is required); Sentry (`core/observability.py`) reads
    `SENTRY_RELEASE`/`SENTRY_DSN` from the environment and safely
    no-ops with an empty DSN (confirmed no real Sentry connection was
    attempted); the shared cache correctly resolves to Redis when
    `CACHE_URL` is set and to the documented file-based fallback
    (`/var/tmp/rvion-django-cache`) otherwise (both paths exercised);
    `/health/` is wired and reachable via `HealthCheckView`.
  - **Browser UAT**, on a disposable throwaway SQLite database (never
    the permanent local database), seeded with disposable accounts/
    exam/order/entitlement fixtures, torn down completely afterward.
    Confirmed live, end-to-end: (1) home → demo gallery → customize
    (brand/theme/personality/features) → "ادامه با این انتخاب" → the
    contact form pre-filled with the right `request_type`, all 3 steps
    completed, a real submission producing a real tracking code; (2) a
    page reload and a browser-history **back** to the bfcache-restored
    form, followed by a resubmit attempt, produced **zero** additional
    `Lead` rows (`Lead.objects.count()` stayed at 1 throughout); (3)
    guest consent banner for the local draft correctly offered and
    handled; (4) **registration is confirmed, live, to be a single
    step with no OTP anywhere in the flow** — the register page's own
    copy literally reads "بعد از ثبت فرم، بلافاصله وارد حساب خود
    می‌شوی" (immediately logged in after submitting), and submitting it
    redirected straight to the dashboard with "حساب شما ساخته شد و
    وارد شدید." and zero OTP screen; (5) logging in as the same account
    from a second, fully independent browser session correctly
    evicted the first session — navigating the first session afterward
    redirected to login with the exact courtesy message "این دستگاه از
    حساب شما خارج شد چون در جای دیگری وارد شدید."; (6) the second
    (surviving) session could reach the account-bound contact form with
    `data-server-draft="1"` and load its own account's draft — the
    draft that had been created by an incidental (correct) demo→login
    hand-off during registration; (7)/(8) full reconciliation-banner and
    conflict-UI mechanics were not separately re-driven by hand this
    round (the draft encountered was empty), and instead rely on the
    already-passing, extensive `leads.test_draft_api`/`leads.
    test_contact_server_draft_ui`/`leads.test_demo_handoff` automated
    coverage — recorded here as a real, disclosed gap rather than
    silently claimed as browser-verified; (9)/(10) likewise, the
    offline/retry and final-no-duplicate-Lead guarantees were not
    re-driven manually this round beyond what flow (2) above already
    proved live, relying otherwise on `leads.test_finalize`'s extensive,
    already-passing automated coverage (including real PostgreSQL
    concurrency); (11) the dashboard's own order-draft card rendered
    correctly for the authenticated customer ("سفارش پروژه … ناتمام ·
    مرحله ۱ از ۳"); (12) the English dashboard showed correct English
    labels throughout — the only Persian characters present were the
    customer's own name as typed at registration ("Hello, کاربر"), which
    is user-supplied identity data, not a translation-boundary defect,
    and is explicitly not the kind of leak V2.1-C2's corrective phase
    fixed; (13) a staff superuser, from the management portal, revoked
    a customer's exam access with a reason, and the UI immediately
    confirmed "دسترسی بسته شد و آزمون فعال متوقف گردید." with the
    attempt shown as "باطل‌شده" — this exercises the exact
    `revoke_assessment_access` function V2.1-E0 fixed; (14) the revoked
    customer's own browser session, on requesting the same attempt
    URL, was correctly shown "این آزمون بسته شده است / باطل‌شده" instead
    of being able to continue. **Visual/responsive:** the contact form
    and the dashboard both showed zero horizontal scroll at 320px and
    390px in both light and dark themes (`scrollWidth === clientWidth`
    in all four combinations checked per page); keyboard Tab produced a
    visible focus outline on every element spot-checked on the contact
    form. Zero JavaScript console errors or failed requests across the
    entire pass (aside from the same pre-existing, unrelated
    `AudioContext` autoplay warning already noted in prior phases).
  - **Documentation corrected:** `docs/OPERATIONS_RUNBOOK_FA.md`'s
    pre-release manual-check list previously said to check "ثبت‌نام،
    دریافت و ورود کد OTP" (registration, receiving and entering an OTP
    code) — stale relative to the actual code
    (`accounts.views.RegisterView.form_valid`'s own docstring: "Phone
    verification is deliberately out of the signup path"). Corrected to
    state plainly that registration is single-step with immediate
    login and no OTP, and that the OTP/`PhoneVerificationView`
    machinery remains in the codebase only for a separate,
    staff-initiated path — not the ordinary customer signup this
    checklist item is about. Also added: a short, new "Migrationهای
    این انتشار و ریسک rollback" section listing the 5 release
    migrations and stating plainly, per the rehearsal finding above,
    that reverting them destroys `FormDraft`/`ActiveSession`/token data
    (code rollback only, never migration rollback, is the safe
    recovery path); and a short "Cleanup commandهای این انتشار" section
    stating that both `cleanup_demo_selections` and the new
    `cleanup_form_drafts` are manual, dry-run-by-default, and carry no
    automatic schedule of any kind (unlike `cleanup_system_logs`, which
    already has its own daily timer) — no scheduled/cron/Celery Beat
    execution was added for either.
  - Files touched: `leads/test_contact_server_draft_ui.py` (Finding
    #1's one-line fix), `docs/OPERATIONS_RUNBOOK_FA.md` (documentation
    correction), `.ai/project/CURRENT_STATE.md`. No production code
    beyond the one test-isolation fix was changed; no migration created
    or run against a permanent database; nothing pushed, deployed, or
    connected to production.
- **Git boundary (current, accurate as of this phase's own commit):**
  `main` is thirty commits ahead of `origin/main` — the twenty-nine
  listed above (including the V2.1-E1 commit, `5374666`, itself on top
  of `2ab8515`/`1f85075`/`7628343`/`126c70b`/`7e5e621`/`6d75c4f`), plus
  this phase's own V2.1-E2 audit commit. No prior commit is amended.
- **Last commit:** this phase's own commit — the V2.1-E2 audit's only
  code/doc changes: `leads/test_contact_server_draft_ui.py`,
  `docs/OPERATIONS_RUNBOOK_FA.md`, and `.ai/project/CURRENT_STATE.md`;
  a separate commit on top of `5374666` (the V2.1-E1 commit), which is
  not amended.
- **Next action:** **Release is `BLOCKED`, not pushed.** Before this
  candidate can become `READY_TO_PUSH`, a human must decide how to
  handle the `SingleSessionPostgresRaceTests` login race (Finding #2
  above): either accept the documented, narrow, non-security-bypassing
  risk explicitly and proceed, or commission a dedicated follow-up
  phase to harden `accounts/signals.py`'s single-session login path
  against this exact interleaving (e.g. retrying or catching
  `UpdateError` at the right layer) with its own careful design and
  test cycle — this should **not** be rushed inside another audit
  phase. Separately and non-blocking: Python 3.11 should be installed
  and exercised on this machine (or accepted as `PARTIAL/READY_PENDING_
  CI` until GitHub Actions itself runs the real matrix) before treating
  the CI-parity claim as complete; the two browser-UAT gaps disclosed
  above (live reconciliation-banner/conflict-UI driving, and a fresh
  live offline/retry drive beyond what flow (2) already proved) can be
  closed in a future UAT pass if a human wants stronger manual coverage
  beyond the existing automated tests. V2.1-E0 and V2.1-E1 both remain
  done and fully verified — see their own entries above; nothing in
  this phase touched or re-litigated either. V2.1-C2 (implementation
  plus its corrective) remains done and fully verified. The
  saved-drafts dashboard's remaining scope (if any beyond the single
  active `leads_contact` draft card) and CRM/Clinic resumable-draft
  support both remain `NOT_STARTED`/out of scope, unless explicitly
  reopened. V2.1-B1 (both corrective phases), V2.1-B2 (all three
  corrective phases), V2.1-B3 (plus its corrective phase), V2.1-C1
  (plus both corrective phases), and V2.1-D (plus its corrective phase)
  remain done and fully verified — see their own entries above; nothing
  in this phase touched or re-litigated any of them. The earlier,
  separate V2 idea (a time-boxed, signed continuation link) remains
  superseded by the login-based approach unless explicitly reopened.
  Re-run the full release gate (this phase's own checklist, in full)
  on the exact deployable revision once Finding #2 is resolved, and
  immediately before any production action, including applying
  `0004_activesession`, `0006_formdraft_and_more`,
  `0007_formdraft_revision`, and `0008_formdraft_submission_token` to
  any real database.

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
| Resumable order drafts — V2.1-B2 (all corrective phases) — overall feature status before the third lookup fix (`757f7a4`→`2cd1032`→`1baf584`) | `PARTIAL` → corrected below | Each individual commit up to and including `1baf584` was independently `VERIFIED` for the specific defect it fixed, but the *feature as a whole* remained `PARTIAL` until the third corrective phase below closed the second, previously-unaddressed `DemoSelection` lookup inside `_reload_demo_selection`. `1baf584` itself, and its first-lookup fix and test, are unchanged and remain correct. |
| Resumable order drafts — V2.1-B2 third corrective (wrap `_reload_demo_selection`'s query in its own `transaction.atomic()`, safe for both `ensure_active_draft_with_demo_snapshot` and `attach_demo_snapshot`) | `VERIFIED` (local) — V2.1-B2 as a whole now `VERIFIED` | See "V2.1-B2 third corrective" entries above. `leads.form_draft_service._reload_demo_selection` now runs its query inside its own `transaction.atomic()`, letting a real database error propagate out (never swallowed inside) so Django rolls back to that savepoint before either caller's own exception handling ever sees it — closing the exact same class of bug `1baf584` fixed for the *first* lookup, one call deeper. Reproduced first (reverting the fix made both new tests fail with `InternalError: current transaction is aborted`), then fixed and re-verified. Two new PostgreSQL-only tests, kept alongside `1baf584`'s and `2cd1032`'s existing ones (all three real-transaction test classes now coexist): `RealTransactionErrorDuringSecondLookupRecoveryTests` (login-signal path, call-counter-proven second-lookup failure, healthy query inside the same outer transaction, marker restored, snapshot attaches on retry) and `test_attach_demo_snapshot_survives_a_real_postgresql_error_in_the_reload_lookup` (direct `attach_demo_snapshot` call, caller catches the propagated error, outer transaction still usable). `leads.test_demo_handoff`+`leads.test_form_draft` on PostgreSQL: 108 tests, all passing, 0 skips. `leads` app on SQLite: 120 tests (110 passed, 10 skips); `accounts`: 73 tests (71 passed, 2 skips) — no regression in registration/login/phone-verification/email-verification. Run once plus 5 repeats each on the same isolated local PostgreSQL 16 `test_arvion_ci_local` database (never the permanent one) — all clean. The unrelated, pre-existing `assessments/services.py` PostgreSQL incompatibility remains flagged, unfixed, and not hidden. `check` (0 issues), migration dry-run ("No changes detected"), and `git diff --check` (clean) all passed. No prior commit amended; only `leads/form_draft_service.py`, `leads/test_demo_handoff.py`, and `leads/test_form_draft.py` touched. |
| Resumable order drafts — V2.1-B3 (account-bound, revision-checked FormDraft API: GET/POST `leads:draft`, POST `leads:draft_delete`) (`57a6be8`) | `VERIFIED` (local), corrected | Initially verified, then found `PARTIAL`: `save_draft_fields` raised `DraftConflictError` from *inside* its own `transaction.atomic()` block when an expired draft's `expected_revision` no longer matched, rolling back the expiry transition `_get_active_draft_locked` had just committed within that same block. `57a6be8`'s own report incorrectly claimed this case did not roll back. See the corrective-phase row below, which fixes and re-verifies it with a test that inspects the row immediately after the conflict. |
| Resumable order drafts — V2.1-B3 corrective (defer `save_draft_fields`'s conflict raise until after its transaction commits, so an expiry transition always survives) | `VERIFIED` (local) | See "V2.1-B3 corrective" entries above. `save_draft_fields` now records a conflict outcome in a local `_NO_CONFLICT`-sentinel-guarded variable instead of raising immediately, and only raises `DraftConflictError` after its `transaction.atomic()` block has exited normally — mirroring `attach_demo_snapshot`/`clear_demo_snapshot`'s existing `no_active_draft` ordering. `delete_draft_with_revision` was checked and confirmed to not have this bug (its "no draft" case is a plain `return`, never a `raise`, from inside its own atomic block) — left untouched. Reproduced first (reverting the fix made the new tests fail with `'open' != 'expired'`, both at the service level and through the real HTTP view), then fixed and re-verified. New PostgreSQL-only `FormDraftApiExpiredConflictUnderOuterTransactionTests` proves the same scenario holds even when the real view is called inside a genuine outer `transaction.atomic()` standing in for `ATOMIC_REQUESTS` — the 409 is returned normally with no exception ever reaching the outer block, and the expiry transition is visible via a real query while still inside that same outer transaction. Run once plus 5 repeats — all clean; the pre-existing `FormDraftApiPostgresConcurrencyTests` concurrency test was re-confirmed unaffected. `leads.test_draft_api`+`leads.test_form_draft`+`leads.test_demo_handoff` (173 tests, 12 skips on SQLite; same 173 tests, 0 skips on real PostgreSQL); `leads` app (185 tests, 12 skips); `accounts`+`projects`+`management_portal` (234 tests, 2 skips) — no regression. No migration in this phase (none was expected); only `leads/form_draft_service.py` (one function), `leads/test_form_draft.py`, and `leads/test_draft_api.py` touched — `delete_draft_with_revision` and every other service function byte-for-byte unchanged. The unrelated, pre-existing `assessments/services.py` PostgreSQL incompatibility remains flagged, unfixed, and not hidden. `check` (0 issues), migration dry-run ("No changes detected"), and `git diff --check` (clean) all passed. `57a6be8` not amended. |
| Resumable order drafts — V2.1-C1 (leads-contact wizard wired to the account-bound FormDraft API: restore, autosave, conflict resolution, delete/start-over) (`bef7d45`) | `PARTIAL`, corrected | Initially `PARTIAL` (client-side logic unverified live); real browser testing then surfaced 5 real P1 defects (TDZ crash stopping the whole wizard, `[hidden]` not actually hiding two elements, focus targeting a nonexistent `h2`, GET error handling collapsing everything to "offline", no real response-shape validation). See the corrective-phase row below, which fixes all five and remains `PARTIAL` for the same live-verification reason. |
| Resumable order drafts — V2.1-C1 corrective (TDZ fix, `[hidden]` CSS fix, `legend`-aware focus helper, classified GET/save/delete error handling with honest retry exhaustion, real draft-response validation, Enter/change-event/duplicate-message smaller fixes) | `PARTIAL` (local) | See "V2.1-C1 corrective" entries above for full root-cause/fix detail. All five P1s fixed in `core/static/core/js/wizard-engine.js`; `.wizard-consent[hidden]`/`.enquiry-actions [hidden]`/`.wizard-draft-banner[hidden]` added to `core/static/core/css/site.css` (targeted, not a site-wide `[hidden]` reset). `leads.test_contact_server_draft_ui`+`leads.test_draft_api`+`leads.test_form_draft`+`leads.test_demo_handoff`+`leads`+`accounts` (267 tests, 14 skips), `crm_orders`+`clinic_orders` (28 tests, real smoke check their own wizard wiring is unaffected), full project suite (742 tests, 15 skips — identical to before this phase, zero regression). `manage.py check` (0 issues), migration dry-run ("No changes detected" — no model/migration touched), `git diff --check` (clean), and `node --check` on the edited JS file all passed. Live-browser verification was attempted again with a freshly rebuilt disposable environment; the same code-independent JS-execution probe used in the original C1 phase still returned `NOT_RUN` — the tool remains broken, unrelated to this project's code — so per explicit instruction this phase stays `PARTIAL`, not `VERIFIED`, even though the fixes are complete and self-reviewed. `bef7d45` not amended; a separate commit on top of it. |
| Resumable order drafts — V2.1-C1 second corrective (stale cache-bust, `draft:null`-on-save validation, delete-response validation, real-option field validation, single-flight offline retry, `updated_at` hardening) | `VERIFIED` (local) | See "V2.1-C1 second corrective" entries above. All 6 defects fixed in `wizard-engine.js`; cache-bust bumped in `base.html`; one pre-existing test's hardcoded version string updated in `core/tests.py`. Genuinely exercised in a real browser this time (guest flow; states A–D; malformed GET/save/409/delete; a real 401 via server-side session expiry; a real 403 via mid-session staff promotion; real `setOffline` network cut proving only 2 real attempts fire across a 4-change burst, not 4–5; validation rerender; fa/en; 320/390 light/dark; CRM/Clinic smoke) — zero uncaught console errors throughout. Targeted suite (295 tests, 14 skips) and full suite (742 tests, 15 skips) both pass; `check`, migration dry-run, `git diff --check`, `node --check` all pass. One honest residual gap: keyboard Enter-activation of the reconciliation banner's primary button did not register through this automation tool despite confirmed DOM focus — read as a tool limitation (two other unrelated tool quirks were found and worked around this same session), not a suspected defect, since the button is unmodified native `<button>` markup. `bef7d45`/`3b8fb71` not amended; a separate commit on top of `3b8fb71`. |
| Resumable order drafts — V2.1-D blocked analysis (`6d75c4f`) | `BLOCKED` → superseded below | See "V2.1-D — blocked: idempotency analysis" above (kept as historical record). Proven on paper before writing any code: the true-concurrency case is already solvable with the existing schema (shared-row locking), but a *sequential* retry arriving after the first attempt's transaction already committed cannot be told apart from a genuinely new, unrelated submission without one of the explicitly-forbidden heuristics (most-recent/highest-pk draft, CSRF token, time window, revision-alone, content match) — all individually traced through and shown to fail on a concrete counter-scenario. Two low-risk designs proposed (Design A: a `submission_token` field on FormDraft, mirroring the already-shipped, already-tested `DemoSelection.submission_token`/`DemoConfigureView` precedent; Design B: a JSON finalize endpoint keyed on `expected_revision`, larger flow change, not preferred). Neither implemented at that time; superseded by explicit authorization and the implementation below. |
| Resumable order drafts — V2.1-D (atomic, non-duplicating FormDraft→Lead conversion, Design A corrected) (`7e5e621`) | `VERIFIED` (local), corrected | Initially verified, then review found two defects: the replay-identity comparison omitted `demo_selection_id`, and the `IntegrityError` recovery branch raised the wrong exception when no record existed for the requesting owner. See the corrective-phase row below, which fixes and re-verifies both; the schema, token-carriage contract, and overall design described here (Added `FormDraft.submission_token`, nullable/unique, additive migration `0008_formdraft_submission_token`, never applied to the permanent local db; `leads/form_draft_service.finalize_form_draft_to_lead` as the sole Draft→Lead authority; owner-row locking; all-statuses token lookup; minimal-draft fallback; `IntegrityError` savepoint as last-resort race defense; `transaction.on_commit()` for exactly-once notification; rate limiter invoked only on the genuinely-new-Lead path; wired into `LeadCreateView` only for authenticated non-staff customers, guest/staff/superuser paths byte-for-byte unchanged) remain accurate and unchanged. Original evidence: `leads.test_finalize` (37 tests) plus the full targeted suite (232 tests, 15 skips) on SQLite; the same 37 tests including 3 PostgreSQL-only concurrency/rollback tests on real isolated PostgreSQL, repeated 5 additional times, all clean; full real-browser verification (fa/en journeys, token stability, no-duplicate-Lead on repeat POST/offline-retry, no submitted-draft banner on return, 320/390px, zero JS exceptions). |
| Resumable order drafts — V2.1-D corrective (canonical replay identity now includes `demo_selection_id`; `IntegrityError` recovery raises the correct exception for a no-match-for-this-owner collision) | `VERIFIED` (local) | See "V2.1-D corrective" above for full detail. P1: `_lead_matches_this_submission` (renamed from `_lead_matches_cleaned_data`) now compares `demo_selection_id` on both sides — the stored `Lead`'s value vs. the caller's resolved `demo_selection` for this exact request — at both the initial token lookup and the `IntegrityError` recovery block, so a reused token with a different/added/removed demo selection is correctly rejected as a conflict rather than accepted as a replay. P2: the recovery block now raises `InvalidSubmissionTokenError` (not `SubmissionConflictError`) when no `FormDraft` exists for the requesting owner+form_type+token — matching the initial lookup's own foreign-token handling and never revealing that a cross-owner collision occurred; a record found but never `submitted` still safely conflicts; a `submitted` record still compares via the corrected content+demo signature. `leads.test_finalize` grew from 37 to 46 tests (4 demo-identity, 4 deterministic `IntegrityError`-recovery-branch, 1 new real-PostgreSQL two-owner unique-collision race using a barrier placed only at the real insert call) — all pass on SQLite (4 skips) and on real isolated PostgreSQL (46/46, 0 skips), with the concurrency/collision/rollback subset (4 tests) run once plus 5 repeats, all clean. Full required targeted suite on SQLite: 241 tests, 16 skips, zero regression from the 232/15 baseline. `check`, migration dry-run ("No changes detected" — migration `0008` untouched), and `git diff --check` all passed. Only `leads/form_draft_service.py` and `leads/test_finalize.py` touched — no template/JS/migration/rate-limit/lifecycle/`on_commit` change. `7e5e621` and `6d75c4f` not amended. |
| Resumable order drafts — V2.1-C2 (account dashboard order-draft section) (`7628343`) | `VERIFIED` (local), corrected | Initially verified, then found to leak the non-bilingual `demo_snapshot.brand` field into both languages of the "Reference demo" row — see the corrective-phase row below, which fixes and re-verifies it. The rest of this phase's design (`accounts.views.dashboard` calling the existing, unmodified `get_active_draft`; `leads/draft_dashboard.py`'s `build_draft_dashboard_card` safe view model; the new `account-compass` "Project enquiry" entry, draft card, and no-draft-state sidebar link; a plain `leads:contact` continue CTA; no `FormDraft` API/finalize/idempotency/rate-limit/`on_commit`/migration touched) remains accurate and unchanged. |
| Resumable order drafts — V2.1-C2 corrective (demo `brand` removed from the dashboard card; language isolation restored) | `VERIFIED` (local) | See "V2.1-C2 corrective — demo brand removed from the dashboard card" above for full detail. `brand` removed from `DraftDemoSummary`, `_DEMO_SNAPSHOT_REQUIRED_KEYS`, and the demo row template — the row now shows only the fully bilingual `template_title_*`/`category_*` pair; a legacy snapshot with only those two bilingual pairs (no `brand` key) still renders correctly. No `demo_snapshot` schema, snapshot builder, model, migration, order form, or management-portal page touched; no new live `DemoSelection`/`DemoTemplate` lookup added; no CSS change, cache-bust untouched. `accounts/test_dashboard_draft.py` grew from 18 to 21 tests (legacy-snapshot-without-brand render check, fa title/category check, and an explicit Persian-brand-never-leaks-into-English regression test that parses the demo row's own HTML and asserts zero Persian/Arabic Unicode characters), all passing; every existing privacy/no-leak test re-run unmodified and still passing. `accounts` full suite plus `leads.test_contact_server_draft_ui`+`leads.test_draft_api`+`leads.test_form_draft`+`leads.test_finalize`+`leads.test_demo_handoff` (323 tests, 18 skips) all pass, zero regression. `check` (0 issues), migration dry-run ("No changes detected"), and `git diff --check` (clean) all passed. Full real-browser verification (fa/en with a fully-Persian-brand snapshot, light/dark, 320/390px no horizontal scroll, keyboard focus/44px target) on a disposable SQLite environment confirmed no Persian text anywhere in the English demo row. `7628343` not amended. |
| Resumable order drafts — V2.1 saved-drafts dashboard, beyond this single-draft-type card | `NOT_STARTED` | Out of this phase's scope; V2.1-C2 covers only the one active `leads_contact` draft. |
| V2.1-E0 — PostgreSQL-incompatible lock in `revoke_assessment_access` fixed | `VERIFIED` (local) | See "V2.1-E0 — PostgreSQL-incompatible lock in exam-access revocation fixed" above for full detail. Unrelated to the V2.1 leads-contact line — closes the `assessments/services.py` remaining risk flagged since V2.1-B2. Root cause reproduced first with the exact supplied command (`FeatureNotSupported: FOR UPDATE cannot be applied to the nullable side of an outer join`, from `select_for_update().select_related("attempt")`'s outer join to the nullable `Attempt` side); fixed by locking `ExamEntitlement` without `select_related` and fetching/locking `Attempt` via its own independent `select_for_update()` query. 4 new tests (no-attempt-yet revocation, idempotent double-revocation, payment-evidence preservation) plus a new PostgreSQL-only `AssessmentAccessRevocationConcurrencyTests` (two truly concurrent revocations converge to exactly one `changed=True`/one `changed=False`, attempt invalidated exactly once — run once plus 5 repeats, all clean). `assessments.tests.AssessmentEngineTests` (61 tests), full `assessments` app + `management_portal.tests.AssessmentAccessControlTests` (134 tests, 2 skips on SQLite, 0 on PostgreSQL) all pass on both SQLite and real isolated PostgreSQL, zero regression. `check` (0 issues), migration dry-run ("No changes detected" — no migration), and `git diff --check` (clean) all passed. Only `assessments/services.py` and `assessments/tests.py` touched. Not pushed, deployed, or migrated on production. |
| V2.1-E1 — `cleanup_form_drafts` management command | `VERIFIED` (local) | See "V2.1-E1 — `cleanup_form_drafts` management command" above for full detail. New `leads/management/commands/cleanup_form_drafts.py`: deletes a `FormDraft` only when `status="expired"` AND `expires_at` older than the retention window (default 30 days) AND `submitted_lead IS NULL` AND `submission_token IS NULL` — all four required, guarding the V2.1-D idempotency contract directly. Dry-run by default; `--apply` required to delete; `--older-than-days`/`--batch-size` (defaults 30/500) validated as positive integers before any write, else `CommandError`. Batch-safe: the delete step re-applies the full eligibility filter combined with `pk__in`, never `pk__in` alone, proven by a test that mutates a row's status inside a patched `.filter()` call positioned exactly between selection and delete. Output is one aggregate line (count + a plain-language, field-name-free policy description) — no owner/email/id/`fields`/`demo_snapshot`/token ever printed, proven by a dedicated test. No cascade to `Lead`/`User` on deletion, proven by a dedicated test. New `leads/test_cleanup_form_drafts.py` (12 tests) plus `leads.test_form_draft`+`leads.test_finalize` (155 tests total) pass on SQLite (11 skips) and real isolated PostgreSQL (0 skips), zero regression. `check` (0 issues), migration dry-run ("No changes detected" — no migration, as instructed), and `git diff --check` (clean) all passed. No cron/Celery Beat schedule, endpoint, UI, model, migration, `FormDraft` lifecycle code, or `cleanup_demo_selections` touched — all files new. `--apply` was run only against test databases; no dry-run was even attempted against the permanent local `db.sqlite3`. Not pushed, deployed, or run against production. |
| V2.1-E2 — Release Candidate gate audit (29→30 commits ahead of `origin/main`) | `BLOCKED` | See "V2.1-E2 — Release Candidate gate audit" above for full detail. Full local gate (`release-check.sh`), the exact CI steps (`compileall`, parallel test, strict question-bank audit, `node --check`, `bash -n`, `git diff --check`), the 5 release migrations reviewed and PostgreSQL-rehearsed forward/backward/forward-again, a production-settings `check --deploy` with fake credentials, and a live browser UAT of every reachable critical flow (funnel, no-duplicate resubmit, no-OTP registration, second-device session eviction, cross-device server draft, dashboard fa/en, admin exam-access revocation and its enforcement) all passed. One small, low-risk test-isolation bug (missing `cache.clear()` in `leads.test_contact_server_draft_ui.ErrorRerenderStepMarkerTests`, exposed only by the exact CI shuffle seed) was found and fixed. Blocking finding: `accounts.tests.SingleSessionPostgresRaceTests.test_two_simultaneous_logins_converge_to_exactly_one_active_session` fails intermittently (~10–15%) on real PostgreSQL on both Python 3.9 and 3.12 — a genuine, narrow, pre-existing real-thread-race in `accounts/signals.py`'s single-session login handling (`UpdateError` from Django's own session backend when a session row is deleted by a second concurrent login between the first login's own commit and its later `request.session.save()`). Low real-world impact (no data loss, no security-guarantee bypass, self-recovers on retry) but not fixed in this phase — deliberately left for a dedicated hardening phase rather than rushed into security-critical session code during an audit. Python 3.11 unavailable on this machine (3.12 was exercised in a disposable venv against real PostgreSQL, all green except the same Finding #2). Migration rollback of this release is confirmed destructive to new data (`FormDraft`/`ActiveSession`/token tables/columns dropped) — documented in `docs/OPERATIONS_RUNBOOK_FA.md`, which was also corrected to stop describing registration as requiring OTP. Not pushed, deployed, or connected to production; no `--apply`/migration was run outside disposable databases. |
| V2.1-E2 corrective — concurrent login response-save race | `VERIFIED` (local) | Removed physical `Session` deletion from the login signal. The locked `ActiveSession` pointer is authoritative; middleware rejects and flushes the loser before any protected view. This closes the intermittent Django `UpdateError` without allowing two valid devices. Evidence: focused SQLite 21/21; PostgreSQL race 30/30 repeated plus both concurrency cases; full PostgreSQL accounts suite 73/73. No migration. |
| Push/deploy of `06812d2` through `79ad24d` | `VERIFIED / DEPLOYED` | GitHub Actions run `34958047474` passed for Python 3.11 and 3.12 on PostgreSQL. Production snapshot `pre-release-20260915-103509.dump` was validated with `pg_restore --list`; release script applied all five queued migrations and completed health checks. Public health/home fa+en/demo/contact/login returned 200; no recent application error or 5xx. |
