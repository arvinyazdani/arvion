# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** Structured display of demo selection in the management dashboard.
- **Last verified phase:** Structured display of demo selection in the management dashboard (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` will be four commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, and this
  phase's commit) once committed below.
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, and
  production migration remain outside the current authorization.
- **This phase's change (no model or migration change):**
  `management_portal/views.py` gains three small helpers —
  `_demo_category_label`, `_demo_selection_card` (bilingual, staff-facing;
  deliberately excludes `DemoSelection.public_token` and `.session_key` —
  verified by `test_detail_card_never_exposes_token_or_session_key`, which
  asserts both raw values and the field names themselves are absent from
  the rendered detail page and the plain-text export), and
  `_demo_selection_report_lines` (Persian-only, reused by both
  `request_detail`'s and `request_export`'s plain-text documents, which
  were already Persian-only before this phase and are left that way
  deliberately — mixing only their embedded demo section into English
  would have produced a worse, inconsistent document than leaving the
  whole thing Persian). `request_list` now runs
  `Lead.objects.select_related("demo_selection__template")` and exposes a
  three-state `?demo=` filter (empty / `only` / a specific
  `DemoTemplate.CATEGORY_CHOICES` key); CRM/clinic rows are skipped
  entirely (not queried) whenever any demo filter is active, since only a
  Lead can carry a `demo_selection`. `request_detail` passes a new
  `demo_card` context value (`None` when the lead has no demo selection).
  Templates: `request_list.html` gained a demo filter `<select>` and a
  small bilingual "Demo · <category>" badge per row; `request_detail.html`
  gained a standalone "Demo selection" `<section class="m-panel">` (outside
  the existing 2-column `.m-detail-grid`, matching the existing pattern for
  other full-width panels) shown only when `demo_card` is truthy, linking
  only to `projects:demo_preview` (the public, unconfigured template — never
  a link carrying the customer's saved choices). CSS: one new class,
  `.m-demo-flag`, added to `management_portal/v2/management.css` (bumped
  `?v=17`) using the existing `--status-info-surface`/`--status-info-text`
  tokens; no new CSS was needed for the card itself, which reuses the
  existing `.m-panel`/`.m-details`/`.m-detail-actions` classes.
- **Test level:** `management_portal` + `projects` + `leads` = 158 tests,
  all passing (8 new this phase, in a new `DemoSelectionDashboardTests`
  class: list indicator + `?demo=only` filter, `?demo=<category>` filter,
  demo-less request excluded from the filter, detail card shows all six
  structured fields, detail card leaks neither token nor session key in
  either the HTML detail page or the plain-text export, English render of
  the new card has no Persian labels (checked against the card's own HTML
  slice, not the page as a whole — the pre-existing, deliberately
  Persian-only "Full discovery details" panel sits on the same page and is
  intentionally excluded from that assertion), unauthorized user still
  gets `403` on both the list and the detail page, and a
  `CaptureQueriesContext` regression test proving the list's query count
  does not grow after five more demo-linked leads are added). `manage.py
  check` (0 issues), `makemigrations --check --dry-run` ("No changes
  detected" — confirmed no model change was needed), and `git diff --check`
  (clean) all passed.
- **Prior phase's P1 corrections (`dc68011` and the commit before this
  one), kept for reference:** (1) a stale `submission_token` resubmitted
  from the same session with changed data now redirects with the visitor's
  values preserved and a freshly re-minted token instead of a bare
  `?invalid=1`; a different session reusing the token still gets a flat
  reject. (2) the post-`IntegrityError` winning-row lookup now happens
  outside a nested `transaction.atomic()` scoped to just the insert, so
  recovery stays reliable under `ATOMIC_REQUESTS = True`. Both were
  reproduced and re-verified empirically at the time; see git history on
  `projects/views/projects.py` (`DemoConfigureView`) for the full detail if
  needed again.
- **Last commit (before this phase):** the "reliable hand-off from demo to
  enquiry" phase commit (see `git log`).
- **Next action:** Await an explicit request to commit/push/deploy this
  phase, or begin the next approved product phase (stale-row cleanup for
  abandoned/expired `DemoSelection` rows remains out of scope and
  unaddressed — the structured operator-visibility half of that discovery
  item is now done by this phase). Re-run the release gate on the exact
  deployable revision before any production action.

## Phase ledger

| Phase | Status | Evidence |
| --- | --- | --- |
| Single-primary-agent alignment | `VERIFIED` | Framework workflow/recovery/test/stop guides read; local `AGENTS.md` replaced with the real single-agent instructions; no active delegated work existed. |
| Interactive demo customizer (`06812d2`) | `VERIFIED` (local) | Targeted tests, route probes, diff/migration checks, and browser flow passed. |
| Pre-design and ordering discovery | `VERIFIED` | Current demo-to-lead flow, session boundary, existing controls, data gaps, and operator visibility were mapped without changing production code. Customer matching uses normalized exact phone/email, not fuzzy matching. |
| Reliable hand-off from demo to enquiry | `VERIFIED` (local) | Both P1s from the prior `PARTIAL` checkpoint were corrected and empirically verified — the ATOMIC_REQUESTS failure was reproduced before the fix and re-checked after it. Full targeted suite (26 tests), `check`, migration dry-run and `git diff --check` all passed. Not pushed, deployed, or migrated on production. |
| Structured display of demo selection in the management dashboard | `VERIFIED` (local) | See "This phase's change" and "Test level" above — 158-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. Not pushed, deployed, or migrated on production. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
