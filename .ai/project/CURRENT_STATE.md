# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** V1 — same-device draft continuation for the leads-contact form.
- **Last verified phase:** V1 draft continuation (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` will be seven commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, `af6e0ac`,
  `fbe3320`, `777acf9`, and this phase's commit) once committed below.
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, production
  migration, and CRM/Clinic wizard changes remain outside the current
  authorization/scope. No customer data was touched; a throwaway
  DemoTemplate/DemoSelection/Lead used to empirically verify the browser
  behaviour was created and deleted from the local dev sqlite database
  during this phase (never committed — `db.sqlite3` is gitignored). The
  local dev database also had one pre-existing, already-committed migration
  (`projects.0006_demoselection_submission_token`, from an earlier phase)
  applied to it, since it was missing and blocked creating a `DemoSelection`
  for the browser check; this created no new migration file.
- **This phase's change (no model, migration, or CRM/Clinic change):** the
  leads-contact form's existing localStorage draft mechanism
  (`core/static/core/js/wizard-engine.js`) can now reconstruct a lost
  `?demo=` link on the same device/session, entirely opt-in and scoped by
  `wizardName === "leads-contact"` so CRM/Clinic wizards execute byte-for-
  byte as before (confirmed by re-running `leads`+`projects`, both green,
  and by code trace: every new branch is gated behind that one check).
  `leads/views/contact.py`'s `get_context_data` now also sets
  `demo_context = {"label": ...}` (the demo template's bilingual title
  only) when `_session_demo_selection` resolves — `_session_demo_selection`
  itself, the actual token/session validation, is untouched.
  `leads/templates/leads/contact.html` renders that label as a
  `data-demo-label` attribute on the form — **never** the token or
  session_key. The token itself is never server-rendered into the DOM at
  all: the client reads it exclusively from `location.search` (the URL the
  browser is already showing, the same pre-existing `?demo=` channel — not
  a new exposure). New dedicated localStorage key
  `rvion-draft:leads-contact:demo` (`{token, label, savedAt}`), separate
  from the general draft's field allowlist, gated by the same per-form
  consent key and a UUID-shape check on write and read. On a page load with
  no `?demo=` param, a valid, non-expired, consented local pointer triggers
  exactly one `location.replace` to re-append `?demo=<token>` (guarded by a
  one-shot sessionStorage flag against loops), which re-runs the existing,
  unmodified server-side session-bound resolution. When that resolution
  fails (invalid/foreign/expired), only the dedicated demo key is cleared —
  the general draft fields are untouched. A silent-expiry gap was closed:
  a genuinely-expired (>7 days) draft now shows a dismissible message
  instead of vanishing without explanation, gated the same way. Every
  clear/disable control, the restore banner's discard button, and the
  successful-submit path now also clear the dedicated demo key. A real bug
  was caught during self-review before testing: the initial expiry check
  read the draft's age *after* `readDraft()` had already deleted the aged
  entry, so it always saw nothing — fixed by peeking the raw age before
  calling `readDraft()`.
- **Test level:** `leads` + `projects` = 33 tests, all passing (2 new this
  phase in `leads/tests.py`: a resolved, session-bound demo renders
  `data-demo-label` with the correct bilingual title and the response body
  contains neither the raw token, the raw session key, nor the strings
  `public_token`/`session_key`; an unresolved/foreign demo renders no
  `data-demo-label` at all). The client-side half (redirect reconstruction,
  consent-gated writes, expiry banner, clear/disable propagation) has no
  JS test framework in this project, so it was verified empirically with
  the browser-automation skill against a throwaway local dev server (a
  disposable DemoTemplate/DemoSelection/session created via `manage.py
  shell`, deleted afterward): (1) first visit with a valid link — banner
  shown, after accepting, localStorage held exactly the general draft, the
  demo pointer `{token, label, savedAt}`, and consent — no name/phone/
  email/session_key anywhere; (2) revisiting the bare URL with no `?demo=`
  — the page auto-redirected to the URL with `?demo=<token>` reappended,
  and the server re-resolved it; (3) a fresh browser context (no cookies,
  foreign session) with the same token — neutral notice shown, no
  `data-demo-label`, no local pointer; (4) the same primed session visited
  with a bogus token — the demo pointer was cleared while the general
  draft's fields survived unchanged; (5) backdating both keys by 8 days —
  the expiry message appeared and both keys cleared, consent itself
  untouched; (6) the "clear draft" and "disable local storage" buttons each
  cleared both keys; (7) a real, full multi-step submission redirected to
  the thanks page and cleared both keys. `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected"), and
  `git diff --check` (clean) all passed.
- **Prior phases, kept for reference:** `777acf9` mirrored a Lead's demo
  choice onto its `CustomerCase` as a structured, bilingual, frozen
  `CaseDocument` snapshot, reusing the existing case/document/revision/
  activity machinery with no new model — see git history for detail if
  needed again. `fbe3320` added a dry-run-by-default
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
- **Last commit (before this phase):** `777acf9 feat: hand off a Lead's
  demo selection into its customer case`.
- **Next action:** Await an explicit request to commit/push/deploy, or
  begin the next planned increment: V2 (a time-boxed, signed continuation
  link for cross-device recovery, from the earlier design report) — this
  requires explicit human approval before any work, since it involves
  either server-side storage of contact info or sending a link to the
  customer, both flagged in that report as decisions outside this agent's
  authority. Resumable order drafts beyond leads-contact (CRM/Clinic) also
  remain `NOT_STARTED`. Consider scheduling `cleanup_demo_selections`
  (cron/Celery beat) only after explicit operational approval. Re-run the
  release gate on the exact deployable revision before any production
  action.

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
| Resumable order drafts — V1 (same-device continuation) | `VERIFIED` (local) | See "This phase's change" and "Test level" above. `leads`+`projects` (33 tests) all passed; CRM/Clinic wizards untouched (gated by wizard name, re-verified green); `check`, migration dry-run, and `git diff --check` all passed. Client-side redirect/consent/expiry/clear behaviour empirically verified via the browser-automation skill against a throwaway local dev server and disposable fixtures (deleted afterward, never committed). No model/migration/CRM/Clinic change. Not pushed or deployed. |
| Resumable order drafts — V2 (signed continuation link) | `NOT_STARTED` | Requires explicit human approval first: it involves either server-side storage of contact info or sending a link to the customer (SMS/email), both flagged as out-of-agent-authority decisions in the design report. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
