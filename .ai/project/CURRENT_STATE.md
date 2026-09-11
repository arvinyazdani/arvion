# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** Reliable hand-off from demo to enquiry.
- **Last verified phase:** Reliable hand-off from demo to enquiry (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` will be three commits ahead of `origin/main`
  (`06812d2`, `dc68011`, and this phase's commit) once committed below.
  `.ai/project/CURRENT_STATE.md` is tracked (first added in `dc68011`).
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, and
  production migration remain outside the current authorization.
- **P1 corrections made this phase (both empirically verified, not just
  reasoned about):**
  1. *Back/edit/resubmit no longer forces an avoidable error.* A stale
     `submission_token` resubmitted from the **same session** with
     **changed** data is still rejected server-side (the original row is
     left untouched, no second row is created — required so a token keeps
     naming exactly one recorded choice), but the redirect now carries the
     visitor's just-submitted values back as query parameters (the
     configurator already restores state from these on load) and lands on a
     freshly re-minted token, so nothing is silently lost and an immediate
     retry succeeds. A dedicated `pageshow`/`persisted` listener reloads a
     back-forward-cache-restored page before the visitor can act on it, so
     in the normal, JavaScript-enabled path this fallback is not reached at
     all — the second submission already carries a token the server has
     never seen and succeeds immediately (verified by
     `test_real_back_then_change_with_a_fresh_token_creates_a_second_valid_selection`).
     A different session reusing the token is unaffected: still a flat
     reject with nothing reflected back.
  2. *IntegrityError recovery is now safe under `ATOMIC_REQUESTS = True`.*
     Reproduced the exact failure first (a plain, unwrapped `.create()`
     inside an outer `transaction.atomic()` — what `ATOMIC_REQUESTS = True`
     imposes on every real request — leaves the connection in a state where
     the very next ordinary query raises `TransactionManagementError`,
     confirmed with a throwaway `manage.py shell` reproduction against this
     project's own models before writing any fix). The insert is now wrapped
     in its own `transaction.atomic()` savepoint; catching `IntegrityError`
     outside that block lets the surrounding transaction stay query-able.
     Verified twice: `test_integrity_error_inside_a_request_level_atomic_block_still_allows_recovery`
     wraps the whole request in an explicit `transaction.atomic()` (the same
     mechanism `ATOMIC_REQUESTS` uses) and asserts an ordinary query
     succeeds right after the caught error; the shell reproduction above was
     re-run against the fixed code and confirmed the same query then
     returns normally instead of raising.
- **Test level:** `projects.tests` + `leads.tests` = 26 tests, all passing
  (2 new this phase: the real-back-with-fresh-token success path, and the
  ATOMIC_REQUESTS-equivalent recovery test; 2 existing tests corrected to
  match the now-intended stale-token redirect and the race simulation
  rewritten to trigger a genuine unique-constraint violation instead of a
  self-recursing mock). `manage.py check`, `makemigrations --check
  --dry-run` (no model changes this phase — none expected), and
  `git diff --check` (no whitespace/conflict markers) all passed.
- **Last commit (before this phase):** `dc68011 fix: make demo-to-enquiry hand-off idempotent and session-safe`
- **This phase's change:** `projects/views/projects.py` (`DemoConfigureView`):
  same-session/mismatched-token redirect now preserves submitted values and
  re-mints a token instead of a bare `?invalid=1`; the winning-row lookup
  after `IntegrityError` now happens outside a nested `transaction.atomic()`
  scoped to just the insert. `projects/templates/projects/demo_preview.html`
  gains a neutral `?stale=1` notice distinct from the existing `?invalid=1`
  error. `projects/static/projects/js/demo-configurator.js` reloads a
  bfcache-restored page (`pageshow` + `event.persisted`) so the fallback
  above is rarely reached with JavaScript enabled; this is convenience only
  and the server enforces the real rule independently of it running.
  `projects/static/projects/css/demo-gallery.css` gets a `.demo-notice`
  style using the existing `--status-info-*` tokens. No model or migration
  change in this phase.
- **Next action:** Await an explicit request to commit/push/deploy this
  phase, or begin the next approved product phase (the structured
  operator-visibility and stale-row-cleanup gaps recorded in the discovery
  phase remain out of scope and unaddressed). Re-run the release gate on the
  exact deployable revision before any production action.

## Phase ledger

| Phase | Status | Evidence |
| --- | --- | --- |
| Single-primary-agent alignment | `VERIFIED` | Framework workflow/recovery/test/stop guides read; local `AGENTS.md` replaced with the real single-agent instructions; no active delegated work existed. |
| Interactive demo customizer (`06812d2`) | `VERIFIED` (local) | Targeted tests, route probes, diff/migration checks, and browser flow passed. |
| Pre-design and ordering discovery | `VERIFIED` | Current demo-to-lead flow, session boundary, existing controls, data gaps, and operator visibility were mapped without changing production code. Customer matching uses normalized exact phone/email, not fuzzy matching. |
| Reliable hand-off from demo to enquiry | `VERIFIED` (local) | Both P1s from the prior `PARTIAL` checkpoint are corrected and empirically verified (see above), not just reasoned about — the ATOMIC_REQUESTS failure was reproduced before the fix and re-checked after it. Full targeted suite (26 tests), `check`, migration dry-run and `git diff --check` all pass. Not pushed, deployed, or migrated on production. |
| Push/deploy of `06812d2` and this phase | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
