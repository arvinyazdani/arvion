# Rvion current state

- **Project:** Rvion
- **Workflow:** single primary agent
- **Current phase:** Structured hand-off of a Lead's demo selection into its customer case.
- **Last verified phase:** Structured customer-case hand-off (this phase).
- **Status:** `VERIFIED` (local)
- **Git boundary:** `main` will be six commits ahead of `origin/main`
  (`06812d2`, `dc68011`, the "reliable hand-off" phase commit, `af6e0ac`,
  `fbe3320`, and this phase's commit) once committed below.
- **Active delegated work:** none.
- **Known blockers:** none for this bounded phase. Push, deploy, and
  production migration remain outside the current authorization; no
  customer data was changed — only local test-database fixtures.
- **This phase's change (no model or migration change):** a Lead's demo
  choice is now mirrored onto its `CustomerCase` as a structured,
  bilingual, frozen `CaseDocument` snapshot, reusing the existing
  case/document/revision/activity machinery end to end — no new model.
  `management_portal/cases.py`: `_upsert_document` gained an optional
  `data=` param (falls back to its previous `snapshot(instance)` behaviour
  when omitted, so every existing caller is unchanged) so a caller can
  supply already-resolved structured data instead of a raw
  `model_to_dict`. New `_demo_selection_snapshot(selection)` resolves the
  template title, category, chosen brand, colour, personality, and
  features into a flat dict with explicit `_fa`/`_en` suffixes (e.g.
  `theme_fa`/`theme_en`) plus the demo template's `slug` — never
  `public_token` or `session_key`, and never a live reference, so the
  record stays fully readable even after `cleanup_demo_selections`
  eventually removes the underlying anonymous selection. New
  `sync_demo_selection_document(case, lead)` upserts this as a
  `CaseDocument` anchored to **the Lead itself**
  (`content_type=Lead, object_id=lead.pk, kind="attachment"` — distinct
  from the `kind="initial"` document already used for the Lead's own raw
  snapshot, so no collision with the existing unique constraint), not to
  the anonymous `DemoSelection` row; this is what makes a later,
  legitimate change to `lead.demo_selection` update the *same* document in
  place (new `CaseDocumentRevision`) rather than leaving a stale duplicate
  behind. It's a no-op when the lead has no `demo_selection`, so a plain
  Lead gains no empty section or noise. `management_portal/signals.py`:
  `new_lead` now captures the `CustomerCase` that `sync_source_case`
  already returns and passes it straight to `sync_demo_selection_document`
  — no extra case lookup query. `management_portal/workspace_views.py`:
  `workspace_detail` picks the demo document out of the case's
  already-`prefetch_related`d `documents` (matched by its fixed title
  string, zero extra queries), excludes it from the generic
  flattened-snapshot document list (which would otherwise interleave the
  `_fa`/`_en` keys in one table), and builds a `demo_card` dict from the
  frozen snapshot alone — reading `lang`-appropriate keys only, so the
  live `DemoSelection`/`DemoTemplate` rows are never touched at render
  time, and the "view public demo template" link is built from the
  snapshot's stored `slug`. `workspace_detail.html`: a new
  `{% if demo_card %}` "Demo selection" `<section class="m-panel">`
  (reusing the existing `.m-panel`/`.m-details`/`.m-detail-actions`
  classes — no new CSS) placed right after the hero and **before** the
  `{% if not proposal %}` gate, so it is visible even when no
  `ContractProposal`/workspace has been created yet for the case (the rest
  of that page's document list is gated behind an active proposal; demo
  visibility deliberately is not, since a manager needs to see it on a
  fresh Lead-only case too) — links to the original request
  (`request_detail`, shown only when `case.kind == "lead"` and a source
  object id exists) and to the public demo template, never to a private
  selection link or token. `request_detail.html`'s existing
  "Prepare & send to customer" link to `workspace_detail` (added in an
  earlier phase, conditioned on `customer_case` existing) already
  satisfies the "clear bilingual path back to the case" requirement and
  was left untouched — confirmed still present and passing.
- **Test level:** `management_portal` + `projects` + `leads` = 172 tests,
  all passing (8 new this phase, in a new `DemoSelectionCaseHandoffTests`
  class in `management_portal/tests.py`: a Lead with a demo selection
  creates a structured snapshot with all six fields correctly resolved in
  both languages; re-saving the Lead twice and re-invoking the sync
  function directly both leave exactly one `CaseDocument` and one
  `CaseActivity` and one `CaseDocumentRevision` (checksum-based
  idempotency, not just a `created` flag); re-pointing `lead.demo_selection`
  at a different `DemoSelection` updates the *same* document in place and
  leaves exactly two revisions, the old checksum still retrievable; a Lead
  with no demo selection creates neither a demo document nor a demo
  activity; the document's raw JSON snapshot and the rendered case page
  both contain neither the raw `public_token`/session-key values nor the
  field names `public_token`/`session_key` themselves; the case page
  contains both the original request's URL and the public demo template's
  URL; an anonymous (non-staff) request to the case page still gets a
  `302` redirect to login, unchanged from before this phase; and a
  `CaptureQueriesContext` regression test proving the case page's query
  count does not grow after five more unrelated `CaseDocument` rows are
  added to the same case). `manage.py check` (0 issues),
  `makemigrations --check --dry-run` ("No changes detected" — confirmed no
  model change was needed), and `git diff --check` (clean) all passed.
- **Prior phases, kept for reference:** `fbe3320` added a dry-run-by-default
  `cleanup_demo_selections` management command (deletes only
  `DemoSelection` rows that are both unattached to any Lead and stale past
  a configurable retention window, `--apply` required for a real delete,
  batch-safe re-checked eligibility at delete time) and, as a P2 fix,
  moved `CATEGORY_LABELS_EN`/`demo_config_labels` out of
  `projects.views.projects` into a neutral `projects/demo_labels.py` so
  `management_portal` no longer reaches into another app's view layer —
  this phase's new `_demo_selection_snapshot` helper reuses that same
  neutral module. `af6e0ac` added a bilingual "Demo selection" card and
  list filter/indicator to the request-list/detail dashboard pages, never
  exposing `public_token`/`session_key` there either. Before that, two P1s
  in the demo-to-enquiry hand-off were corrected and empirically verified:
  (1) a stale `submission_token` resubmitted from the same session with
  changed data now redirects with the visitor's values preserved and a
  freshly re-minted token; (2) the post-`IntegrityError` winning-row lookup
  happens outside a nested `transaction.atomic()` scoped to just the
  insert, so recovery stays reliable under `ATOMIC_REQUESTS = True`. See
  git history on `projects/views/projects.py` (`DemoConfigureView`) for
  full detail if needed again.
- **Last commit (before this phase):** `fbe3320 feat: add safe lifecycle
  cleanup for abandoned demo selections`.
- **Next action:** Await an explicit request to commit/push/deploy, or
  begin the next planned phase: resumable order drafts (needs its own
  privacy and recovery design — not started). Consider scheduling
  `cleanup_demo_selections` (cron/Celery beat) only after explicit
  operational approval; no scheduling exists yet. Re-run the release gate
  on the exact deployable revision before any production action.

## Phase ledger

| Phase | Status | Evidence |
| --- | --- | --- |
| Single-primary-agent alignment | `VERIFIED` | Framework workflow/recovery/test/stop guides read; local `AGENTS.md` replaced with the real single-agent instructions; no active delegated work existed. |
| Interactive demo customizer (`06812d2`) | `VERIFIED` (local) | Targeted tests, route probes, diff/migration checks, and browser flow passed. |
| Pre-design and ordering discovery | `VERIFIED` | Current demo-to-lead flow, session boundary, existing controls, data gaps, and operator visibility were mapped without changing production code. Customer matching uses normalized exact phone/email, not fuzzy matching. |
| Reliable hand-off from demo to enquiry | `VERIFIED` (local) | Both P1s from the prior `PARTIAL` checkpoint were corrected and empirically verified — the ATOMIC_REQUESTS failure was reproduced before the fix and re-checked after it. Full targeted suite (26 tests), `check`, migration dry-run and `git diff --check` all passed. Not pushed, deployed, or migrated on production. |
| Structured display of demo selection in the management dashboard (`af6e0ac`) | `VERIFIED` (local) | 158-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. Not pushed, deployed, or migrated on production. |
| Lifecycle and safe cleanup of abandoned demo selections (`fbe3320`) | `VERIFIED` (local) | 164-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change. `--apply` never run outside the test database. Not pushed, deployed, or migrated on production. |
| Structured customer-case hand-off | `VERIFIED` (local) | See "This phase's change" and "Test level" above — 172-test full suite, `check`, migration dry-run and `git diff --check` all passed. No model/migration change; reused the existing CaseDocument/CaseDocumentRevision/CaseActivity machinery end to end. Not pushed, deployed, or migrated on production. |
| Resumable order drafts | `NOT_STARTED` | Requires a separate privacy and recovery design after the customer-case hand-off is verified. |
| Push/deploy of `06812d2` and later phases | `NOT_STARTED` | Explicit production authorization has not been given in this task. |
