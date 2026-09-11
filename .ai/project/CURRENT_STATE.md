# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** Lifecycle and safe cleanup of abandoned demo selections.
- **Last verified phase:** Lifecycle and safe cleanup of abandoned demo selections (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` will be five commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, the
  "structured dashboard display" phase commit `af6e0ac`, and this phase's
  commit) once committed below.
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, production
  migration, and running `--apply` outside the test database remain outside
  the current authorization — this phase's own `--apply` flag was only ever
  exercised inside `manage.py test`'s in-memory database; the real local
  dev database was only ever queried read-only via the default dry-run.
- **This phase's change (no model or migration change):** new management
  command `projects/management/commands/cleanup_demo_selections.py` deletes
  `DemoSelection` rows that are BOTH unattached to any Lead
  (`leads__isnull=True` — the reverse of `Lead.demo_selection`, the only
  foreign key onto this model anywhere in the project, confirmed by a
  project-wide grep before writing the query) AND stale
  (`updated_at__lt=now-older_than_days`, default 30 days; `updated_at`
  rather than `created_at` so a selection someone is still actively
  reconfiguring is never mistaken for abandoned). Dry-run by default
  (reports a count only, deletes nothing); `--apply` is required to delete
  for real; `--older-than-days` (validated: must be a positive integer, a
  zero/negative value raises `CommandError` before touching the database)
  overrides the 30-day default; deletion is batched (`--batch-size`,
  default 500) and each batch's actual `DELETE` re-applies the full
  eligibility filter (not just the previously-fetched id list), so a
  selection that gets attached to a Lead in the gap between listing a
  batch's ids and deleting them is never removed. Command output reports
  only a count, the retention window, and the dry-run/apply policy — never
  a token, session key, brand, or any other selection content (verified by
  `test_output_never_contains_token_session_key_or_brand`, which plants a
  selection with a distinctive session key and brand string and asserts
  neither the raw values nor the field names `public_token`/`session_key`
  appear in captured stdout). Also cleans up a P2 architectural dependency
  found during the prior phase: `management_portal/views.py` was importing
  `CATEGORY_LABELS_EN`/`_labels` from `projects.views.projects` (a
  view-layer, not a shared, module). Both symbols moved verbatim (no
  behaviour, wording, or URL change) into a new neutral module
  `projects/demo_labels.py` (`CATEGORY_LABELS_EN`, `demo_config_labels`);
  `projects/views/projects.py` now imports them back under their original
  local names so its own code is unchanged, and `management_portal/views.py`
  imports directly from `projects.demo_labels` — confirmed by grep that no
  file anywhere still imports from `projects.views.projects` outside that
  module's own test-mock target string (unrelated, patches
  `DemoSelection.objects.filter`, not a label).
- **Test level:** `management_portal` + `projects` + `leads` = 164 tests,
  all passing (6 new this phase, in a new `DemoSelectionCleanupCommandTests`
  class in `projects/tests.py`: dry-run reports a stale unattached
  selection without deleting it; `--apply` deletes that same record in the
  test database only; a selection attached to a Lead is never reported or
  deleted even at 365 days old; a fresh unattached selection survives
  `--apply`; `--older-than-days 0` and `--older-than-days -5` both raise
  `CommandError` and leave the database untouched; command stdout contains
  no token, session key, or brand string). `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected" — confirmed no
  model change was needed), and `git diff --check` (clean) all passed. The
  command's `--apply` path was only ever run inside `manage.py test`'s
  isolated in-memory database; against the real local dev database only the
  read-only default dry-run was run once, reporting 0 eligible rows.
- **Prior phases, kept for reference:** the "structured dashboard display"
  phase (`af6e0ac`) added a bilingual "Demo selection" card and list
  filter/indicator to the management dashboard, never exposing
  `public_token`/`session_key` there either. Before that, two P1s in the
  demo-to-enquiry hand-off were corrected and empirically verified: (1) a
  stale `submission_token` resubmitted from the same session with changed
  data now redirects with the visitor's values preserved and a freshly
  re-minted token; (2) the post-`IntegrityError` winning-row lookup happens
  outside a nested `transaction.atomic()` scoped to just the insert, so
  recovery stays reliable under `ATOMIC_REQUESTS = True`. See git history
  on `projects/views/projects.py` (`DemoConfigureView`) for full detail if
  needed again.
- **Last commit (before this phase):** `af6e0ac feat: show structured,
  bilingual demo-selection details in the management dashboard`.
- **Next action:** Await an explicit request to commit/push/deploy this
  phase, or begin the next approved product phase. Nothing from the
  original discovery-phase gap list is known to remain unaddressed at this
  point. Consider whether `cleanup_demo_selections` should be scheduled
  (e.g. cron/Celery beat) once deploy is authorized — this phase only
  built and verified the command itself, not any scheduling. Re-run the
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
| Lifecycle and safe cleanup of abandoned demo selections | `VERIFIED` (local) | See "This phase's change" and "Test level" above — 164-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. `--apply` never run outside the test database. Not pushed, deployed, or migrated on production. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
