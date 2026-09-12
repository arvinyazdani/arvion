# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** P1 fix — permanent redirect guard in the leads-contact demo continuation (V1).
- **Last verified phase:** P1 fix for the redirect guard (this phase); supersedes the `PARTIAL` status `b3952a4` was left in.
- **Status:** `VERIFIED` (local) — the P1 found in `b3952a4` is fixed and
  empirically re-verified in a real browser (see below). History: the
  one-shot `sessionStorage` redirect guard
  (`rvion-draft:leads-contact:demo-redirect-guard`) was set to `"1"` on the
  first reconstruction and never cleared on a successful re-resolution, so
  a second visit to the bare URL in the same tab never redirected again —
  defeating the same-device continuation goal that phase exists for.
- **Git boundary:** `main` will be eight commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, `af6e0ac`,
  `fbe3320`, `777acf9`, `b3952a4`, and this phase's commit) once committed
  below.
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, production
  migration, and CRM/Clinic wizard changes remain outside the current
  authorization/scope. No customer data was touched; a throwaway
  DemoTemplate/DemoSelection used to empirically verify the browser
  behaviour was created and deleted from the local dev sqlite database
  during this phase (never committed — `db.sqlite3` is gitignored). No
  migration was run this phase — the local dev database was already fully
  migrated from the prior phase's one-time sync
  (`projects.0006_demoselection_submission_token`, applied in the V1
  phase); that earlier local migration is kept only as historical record
  in this file and was neither repeated nor rolled back.
- **This phase's change (no model, migration, or CRM/Clinic change; one
  function in one file):** `writeDemoContext` in
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
- **Test level:** `leads` + `projects` = 33 tests, all still passing
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
- **Last commit (before this phase):** `b3952a4 feat: reconstruct a lost
  demo link on the same device for the contact form`.
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
| Resumable order drafts — V1 (same-device continuation) (`b3952a4`) | `VERIFIED` (local), P1-corrected | Initially verified, then found `PARTIAL` when a P1 surfaced (permanent redirect guard, see next row); superseded by the P1 fix phase below, now `VERIFIED` again. |
| Resumable order drafts — V1 P1 fix (permanent redirect guard) | `VERIFIED` (local) | See "This phase's change" and "Test level" above. One-line root cause, one-function fix (`writeDemoContext` now clears the one-shot guard on success). `leads`+`projects` (33 tests) still pass; `check`, migration dry-run (no migration run), and `git diff --check` all passed. Browser-verified: two consecutive same-tab reconstructions both succeed (the exact case that was broken); invalid/foreign token still clears only the demo pointer with no loop; no-consent and expired-storage cases still never reconstruct. `b3952a4` was not amended; this is a separate corrective commit. |
| Resumable order drafts — V2 (signed continuation link) | `NOT_STARTED` | Requires explicit human approval first: it involves either server-side storage of contact info or sending a link to the customer (SMS/email), both flagged as out-of-agent-authority decisions in the design report. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
