# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** Reliable hand-off from demo to enquiry.
- **Last verified phase:** Reliable hand-off from demo to enquiry (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` is one local commit ahead of `origin/main` before
  this phase's commit; the working tree was clean when this checkpoint's
  phase began. `.ai/` itself remains untracked (as in prior checkpoints).
- **Active delegated work:** none.
- **Known blockers:** none. Push, deploy, and production migration are outside
  the current authorization.
- **Test level:** `projects.tests` + `leads.tests` = 24 tests, all passing
  (10 new/updated: fresh-token-per-render, same-token resubmit → one row,
  new token → new row, cross-session token rejected, edited-data-same-token
  rejected, simulated create()-race falls back to the winning row, missing
  token rejected, bilingual non-blocking notice on invalid/foreign token in
  both languages, and the notice leaking nothing about the other session).
  `manage.py check`, `makemigrations --check --dry-run` (no drift beyond the
  generated migration), and `git diff --check` (no whitespace/conflict
  markers) all passed. The new migration was generated but was **not**
  applied to the local `db.sqlite3`; Django's test runner applies it only to
  its own ephemeral test database.
- **Last commit (before this phase):** `06812d2 feat: replace project showcase with live demo customizer`
- **This phase's change:** `DemoSelection.submission_token` (unique, nullable
  for backward compatibility) plus `projects/migrations/0006_demoselection_submission_token.py`.
  `DemoConfigureView` now requires a server-minted `submission_token`
  (`DemoPreviewView` mints one on every GET) and treats it as a one-shot key:
  identical token+session+data reuses the existing row; a different session
  or edited data with the same token is rejected without creating a row or
  revealing the other selection. `leads:contact` shows a neutral bilingual,
  non-blocking notice when `?demo=` cannot be resolved, without saying why.
- **Next action:** Await an explicit request to commit/push/deploy, or begin
  the next approved product phase (e.g. the structured operator-visibility
  and stale-row-cleanup gaps recorded in the discovery phase, which remain
  out of scope for this bounded change). Re-run the release gate on the exact
  deployable revision before any production action.

## Phase ledger

| Phase | Status | Evidence |
| --- | --- | --- |
| Single-primary-agent alignment | `VERIFIED` | Framework workflow/recovery/test/stop guides read; local `AGENTS.md` replaced with the real single-agent instructions; no active delegated work existed. |
| Interactive demo customizer (`06812d2`) | `VERIFIED` (local) | Targeted tests, route probes, diff/migration checks, and browser flow passed. |
| Pre-design and ordering discovery | `VERIFIED` | Current demo-to-lead flow, session boundary, existing controls, data gaps, and operator visibility were mapped without changing production code. Customer matching uses normalized exact phone/email, not fuzzy matching. |
| Reliable hand-off from demo to enquiry | `VERIFIED` (local) | `submission_token` idempotency (create/resubmit/cross-session/edited-data/race paths) and the bilingual session-loss notice are implemented and covered by 10 new/updated tests; full targeted suite (24 tests), `check`, migration dry-run and `git diff --check` all pass. Not pushed, deployed, or migrated on production. |
| Push/deploy of `06812d2` and this phase | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
