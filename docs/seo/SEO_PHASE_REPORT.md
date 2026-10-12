# SEO phase report — Rvion

## Piece 2 — phase5 final verification (2026-10-10)

Status: scoped implementation/local evidence VERIFIED; programme PARTIAL for
the unchanged strict gallery audit, owner visual acceptance and Piece1 public
activation gate. Final serial recovery:`.venv/bin/python manage.py test --parallel 1
--verbosity 1` →1160 tests, OK(skipped=27),338.248s. Log:
/tmp/rvion-piece2-20261010/full-suite-recovery.log. Skips are retained existing
backend-specific conditions, not added to hide failures. No claim of PostgreSQL
or actual-device execution. Final checkpoint commit is the phase5 commit that
contains this section (resolve with Git log, no fabricated forward hash).

Scope: local order studio, one-shot path introductions and official assessment
options. Implementation commits:9437671, c333c99, 5c2b223. Single primary agent;
self-review, not independent review. No push/deploy/SSH/migration. Protected
gallery files, customer records and preserved stash/bundle unchanged.

Corrections: pausing motion now leaves a fully visible preview (not an entrance
animation frozen at opacity zero); desktop step targets are at least44px;
step changes cancel old overlay timers; missing studio CSS restores the simple
form; exam validation restores each option's descriptive association. The final
form distinguishes a neutral functional carrier from the customer's actual
colour/look; no gallery style is falsely presented as the selected visual style.
The first targeted run caught a missing local `choices` variable in the clinic
summary; corrected and26/26 targeted tests passed. Later25 home/handoff tests
passed after correcting three stale home expectations to the already-approved
unified /start/ gateway (no production route changed to satisfy these tests).

Evidence: /tmp/rvion-piece2-20261010/matrix.json and40 JPEG views:
5 stages x390/1280px xfa/en xlight/dark. DOM checks: no horizontal overflow,
preview opacity1, no enabled button below44px tolerance, no Persian characters
in the English studio. Representative screenshots inspected. English project
intro completed to studio; browser studio→contact form preserved choices, with
no customer submission. Feature-bearing handoff and session/idempotency/error
cases are covered in disposable Django test databases, not a browser-created
production/customer record. Actual iPhone/Safari and subjective owner acceptance
remain unverified; this is not a pixel-identical/reference acceptance claim.

Seven new JS/CSS assets total20847 gzip bytes (<35KiB). Three mobile Lighthouse
runs on /fa/start/: CLS0/0/0, TBT93/96/83ms, LCP4005.33/3922.79/3919.79ms.
JSON files:lighthouse-1/2/3.json in the evidence directory. Temporary local
PerformanceObserver also recorded zero shifts/long tasks on three loads; its
script was removed before these Lighthouse runs and is not committed. These
measurements do NOT supersede Piece1's control-relative public activation gate.

Commands: manage.py test core.test_order_scene core.test_order_handoff leads.tests
(26 PASS); manage.py test core.test_home core.test_order_scene core.test_order_handoff
(25 PASS); all6 core/tests_js/*.test.cjs PASS; JS syntax PASS; manage.py check0;
makemigrations --check --dry-run:No changes detected; git diff --check clean.
Manifest unit command initially232 tests/3 failures, all stale home routes.
Full --parallel4 discovered1160 tests but stopped on traceback-pickling while
reporting a failure, so it is NOT a full passing gate. A serial recovery run is
recorded below; it is an explicit diagnostic recovery, not an unreported second
routine full run. Strict premium audit:FAIL,55 existing actionless-button
findings in unchanged gallery templates; no suppressions or protected-file edits.

Rollback: revert only the four scoped Piece2 implementation commits in reverse
order if needed; no database rollback. Keep RVION_ENTRY_ENABLED off. No cleanup
of customer data, existing stash, backup, media or secrets is authorized here.

Historical checkpoint (2026-10-09): entry CLS/audio diagnosis VERIFIED locally;
public activation BLOCKED on control-relative LCP/TBT. Latest owner instruction:
no push/deploy/migration. See final "Entry CLS/audio diagnosis" section. Changes
remain uncommitted on f7b404d; older release entries below are historical.

## Owner-authorized cleanup/release checkpoint (2026-10-09)

Status: cleanup VERIFIED; deployment BLOCKED on SSH connectivity, not on code.
Candidate6500491 contains the already-committed order implementation. No runtime
changes were added in this turn. Owner explicitly authorized commit/cleanup/deploy.

Unfinished protected gallery and article-editor work, including untracked files
and visual evidence, was preserved using an exact-path `git stash push --include-untracked`.
Stash:a8afc0d71357f038ba95ccc9cdd5a607900c45c8. `git bundle create` and `git bundle verify`
confirmed a standalone recoverable copy at
`/Users/rwin/Desktop/rwin-tech/arvion-workspace-preserved-20261009.bundle`.
39 archived files;437 insertions/51 deletions plus images. Working tree then clean.
No ignored secrets, database, media or backups removed. This work is NOT released.
Recovery:`git stash apply a8afc0d71357f038ba95ccc9cdd5a607900c45c8` after checking
the baseline/conflicts; bundle preserves the stash even if the local stash is lost.

Fresh clean-tree commands:
- `.venv/bin/python manage.py test core.test_order_paths core.test_order_gateway core.test_order_handoff core.test_order_ui leads.test_demo_order_path --verbosity 1`:35 tests OK.
  Logged QA-injected RuntimeError is the expected rollback test, not a failure.
- `.venv/bin/python manage.py check`:0 issues.
- `.venv/bin/python manage.py makemigrations --check --dry-run`:No changes detected.
- `.venv/bin/python -m pip check`:No broken requirements.
- `git diff --check`:clean. Prior full gate1133 tests/27 skips is below; no
  redundant full run for documentation-only cleanup.
- `curl --fail --silent --show-error --max-time 15 https://rvionai.com/health/`:
  HTTP200,{"status":"ok"}, existing production only.

SSH with existing key, IdentitiesOnly=yes, IPQoS=none and bounded connect timeout
failed before any remote command. No production backup, pull, migration, release,
restart or data change. Next:push/CI evidence then ops/release.sh through restored
SSH/console, validate snapshot catalog and live paths. Rollback of this checkpoint
is documentation-only; runtime remains6500491 until a real release succeeds.

Push650de2a succeeded; quality run37938191382 failed in the first parallel test
step. Exact primary finding:accounts.test_dashboard_draft.DashboardNoDraftStateTests.
test_customer_without_active_draft_sees_shortcut_and_no_draft_card still expected
`/fa/contact/` for a new order although the approved gateway now uses `/fa/start/`.
Local reproduction1 test FAILED confirms this is real, not ignored as CI noise.
Corrective change updates only this test/comment and anchors its assertion to
the account-compass CTA, avoiding accidental success from a footer/header link.
No production code, workflow or continuation behavior altered.
Targeted command:`.venv/bin/python manage.py test accounts.test_dashboard_draft core.test_order_ui --verbosity 1`:27 tests OK.
CI's subsequent closed-connection and traceback-pickling errors appeared after
the initial failure during parallel shutdown; a fresh full CI is required to
prove no independent failures remain. No tests skipped/removed to make it green.
SSH attempts remain unsuccessful (timeout/closed before command execution),
including a bounded secure curve25519/aes128-ctr retry; no VPN settings changed.
Our local server8164 and its review tab stopped; existing user tabs untouched.

## Unified order entry — final local acceptance (2026-10-09)

Status: VERIFIED for the committed, bounded local implementation. Owner visual
acceptance and production publication are NOT_STARTED; not a production claim.
Single primary agent; self-review, not independent review. No push/deploy/SSH,
database migration, external dependency or production/customer-data operation.

Before: several public order buttons entered different final forms directly,
three competing /start/ cards, and sample context was not presented consistently.
After: /start/ topic → existing sample/customisation or bounded brief → existing
domain final form → original reference-code URL with shared next-process steps.
The header's consultation entry also goes through /start/?consult=1; Samples,
service information, account Continue enquiry and historical URLs still work.

| Topic | Final form (consultation overrides to general) | General request type |
|---|---|---|
| ecommerce / jewelry | Lead | ecommerce; webapp when custom-portal add-on selected |
| restaurant / corporate / portfolio / education | Lead | website; webapp with custom-portal add-on |
| clinic | ClinicOrder, Persian | existing clinic domain |
| crm | CrmOrder, Persian | existing CRM domain |
| other | Lead | webapp |
| Not sure | Lead | consultation |
| Support | add-on on any topic | summary; support only without another topic |

Commit ledger:209b7b8 vocabulary;8924140 gateway;caa9d4d existing configurator
adapter;859762a summaries + shared confirmation (two tightly connected plan
steps combined in one scoped commit);671624e entry/navigation fixes. Final small
checkpoint uses subject `fix: polish order gateway and record scoped acceptance`.

Verification:
- Source/gateway first gate:12 tests OK; integration gate:19 tests OK.
- Final handoff/gateway gate:14 tests OK, including retry/idempotency/session
  isolation and real final submissions + CustomerCase for all three domains.
- Updated core/home/related/service contract gate:56 tests OK.
- New UI/handoff gate:14 tests OK; final template-only header/contrast refinement:
  `python manage.py test core.test_order_ui core.tests.CorePagesTests.test_public_shell_groups_settings_and_keeps_legal_destinations core.tests.CorePagesTests.test_public_and_staff_mobile_navigation_always_has_five_destinations --verbosity 1`:8 tests OK.
- Full suite ONCE, committed isolated candidate671624e (protected dirty work
  excluded), `/Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test --parallel 4 --verbosity 1`:
  **1133 tests, OK,27 existing skips,152.001s**. Candidate:
  `/tmp/rvion-order.MenaBr`; output:`full-suite.log`. Final refinement after this
  gate is template/CSS/test-only and covered by the8 targeted checks + browser;
  no Python production behavior changed afterward. No full-suite rerun.
- `manage.py check`:0 issues; `node --check projects/static/projects/js/demo-configurator.js`
  and `git diff --check`:clean. No permanent-database migration was run.
- Initial affected-app483-test run had9 obsolete route/copy/phone failures and
  one cascading related-link error, all corrected by explicit assertions of the
  new destinations/names;2 protected gallery metadata failures remain in the
  dirty working tree (fa/en titles differ from deployed baseline). No skip,
  snapshot weakening or protected-file correction used to bypass them.
- Two new UI fixture mistakes (already-seeded Service, Post's actual translated
  slug/hero_image field names) were corrected; application schema was not changed.

Browser evidence (local GET/selection navigation only; no permanent Lead/order
or contact-data submission):390×844 and1440×1000, FA/EN gateway, CRM builder,
other brief and general final form; FA specialist forms at both sizes. English
specialist cards clearly disclose their Persian form; English final endpoints
redirect as before, not falsely declared translated. All measured pages had
scrollWidth==viewport width. Additional320px English CRM/dark check:320==320;
visible choice targets66px tall. Dark desktop gateway also checked. Existing
sample actual journey:choose ecommerce → preview → check two add-ons → full
sample → Back to choices; both add-ons preserved and no browser error logs.
No new storage was used. Reduced-motion stylesheet removes new hover movement.
Mobile summary is collapsed by default so it does not bury the form.

Screenshot directory (local evidence, deliberately not committed):
`.ai/artifacts/unified-order-20261009/`:
`gateway-{fa,en}-{390,1440}.jpg`, `crm-{fa,en}-{390,1440}.jpg`,
`other-{fa,en}-{390,1440}.jpg`, `lead-{fa,en}-{390,1440}.jpg`,
`{crm-order,clinic-order}-fa-{390,1440}.jpg`, `preview-en-mobile.jpg`,
`gateway-en-desktop-dark.jpg`, `crm-en-320-dark.jpg`. Legacy captions/photos
are not generated or changed. Screenshots document UI, not load/concurrency proof.

Changed public HTML:shared public shell navigation/styles across existing pages;
`/{fa,en}/`, `/start/`, `/crm/`, `/services/`, `/services/<active-slug>/`,
`/projects/demos/<active-slug>/`, `/projects/demos/<active-slug>/full/`,
`/contact/`, `/contact/thanks/<code>/`,
`/account/dashboard/`; Persian `/crm-order/`, `/clinic-order/`,
`/crm-order/thanks/<code>/`, `/clinic-order/thanks/<code>/`.
No existing title/description/JSON-LD/canonical/
hreflang/sitemap contract changed; full clean-candidate SEO contracts passed.

Remaining boundaries/risks:
- Protected gallery/content-centre changes remain uncommitted and untouched.
  Gallery diff SHA256 still
  `b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba`.
  Stable #demo-options exists in committed HEAD gallery; per-demo anchors await
  that separate gallery work being committed/reviewed.
- Local permanent dev DB reports9 PRE-EXISTING unapplied migrations. These were
  not applied under the no-migration rule. Real submissions were verified only
  in temporary test databases; local preview is not a live POST smoke test.
- No real PostgreSQL concurrency run/CI/production smoke in this task. Existing
  server concurrency/idempotency service is reused;27 skipped gates are not
  represented as passing. No storage or session-policy change; P1-3/P4-1 DEFERRED.
- CRM/clinic cross-device continuation stays out of scope; the design-only draft
  proposal below needs owner privacy/schema approval before implementation.

Rollback:revert these scoped local commits in reverse order after release review,
preserving unrelated dirty edits. No schema rollback/data deletion is needed;
old final-form URLs, records, contracts and tracking codes remain unchanged.
No stop was needed:all sensitive policy/schema boundaries stayed deferred.

### Order phase6 — bounded entry/template cleanup

Home, service-order CTAs, CRM product-order CTAs, related-service discussion and
the account's new-order shortcut now lead to /start/; account Continue enquiry
still resumes /contact/ and information-only sample/service links still browse.
Home category fragments use the stable #demo-options, not uncommitted per-demo
anchors. Header/tabbar use Services/Samples consistently. Public phone links use
the existing Iranian normalizer and +98. Home teacher-assessment CTA uses the
actual assessment name; article covers below the fold are lazy including first.
No assessment logic, article body, metadata or protected gallery CSS changed.

Initial affected-app run:483 tests,16 existing PostgreSQL skips;11 failures +1
error. Nine outdated route/copy/phone expectations (including the cascading
IndexError after a related-link assertion) were updated to the deliberately
changed product contract, not removed; related-link bilingual/indexable checks
remain intact. Two failures are pre-existing protected gallery title drift (fa/en)
against the SEO baseline and are intentionally not fixed here. Focused retest of
the changed core/home/related-link/service expectations:56 tests OK. New UI +
handoff tests:14 tests OK. Full isolated candidate gate pending.

### Order phases4–5 — final forms and confirmations (local)

Existing final forms remain identity collectors. General requests preselect the
source request type/service; CRM/clinic receive a readable initial summary in
their existing additional_notes field, not new fields or storage. Clinic sample
details are resolved exclusively by the existing session-bound validator. No
FormDraft, model, CustomerCase signal or outbound message text changed.
Three real final submissions in the test database still create their respective
CustomerCase records and original tracking-code thank-you pages. All three
confirmation templates now share the same four-step next-process component.
The general confirmation's type label comes from existing localized form choices;
specialist confirmations stay Persian. Personal data is neither pre-collected nor
added to query/session/localStorage by this feature. The existing preview brand,
language session and safe draft contracts are not redesigned.
Targeted handoff/gateway:14 tests OK. Added retry coverage preserves add-ons after
stale-token edits; language-switch/edit links keep safe order choices. No migration.
Rollback: revert the scoped forms/confirmation commit; stored requests remain.

Shared authenticated drafts — DESIGN ONLY, NOT_STARTED:
Future CRM/clinic cross-device continuation needs an explicit new schema/ADR,
not reuse of general FormDraft's contract. Separate versioned allowlists by domain,
owner-bound permissions, optimistic revision checks, final-submit idempotency,
expiry/retention and bounded cleanup would be required. Keep contact/free-text
out of drafts by default; storing it needs an explicit owner privacy decision,
purpose/retention statement and consent plus delete/withdraw controls. Test owner
isolation, session eviction, concurrent edit/submit, expiry, interrupted networks,
consent withdrawal, and cleanup never deleting final records. Proposed seven-day
retention matches the current local safe drafts but is NOT a policy change.
No model, migration, storage extension or new consent flow implemented here.

### Order entry phase3 checkpoint — local integration

Existing DemoConfigureView remains authoritative for validation, ownership,
idempotency and race recovery. Preview/full navigation carries only allowlisted
categorical order context; two optional add-ons travel to the existing domain
form through the gateway POST adapter. Full-preview navigation preserves these
choices without new browser storage. CRM selects the existing9 modules and6
extension options; other-topic brief uses three existing fields, excluding timing
because final forms own their own timing/budget ranges. No protected file changed.
Targeted source/gateway/handoff checks:19 tests passed. Two initial test fixture
errors (unsupported theme `clay`, abbreviated category label) corrected to actual
catalogue values; production validation was not relaxed. Visual/final gate pending.
Rollback: revert scoped phase3 commit; no migration or stored-data rollback.

## Unified order entry — revised owner plan (2026-10-09)

Owner superseded the phase0 stop findings: collect contact data only once in
final forms; preserve existing safe drafts; defer cross-device CRM/clinic;
CRM builder uses query allowlists, no new demo category. Gallery/content edits
stay protected. Implementation proceeds without production access.

Phase1 VERIFIED: core/order_paths.py and core/test_order_paths.py. Nine topics,
two add-ons, consultation, existing demo capability labels, nine CRM feature
labels and six roadmap labels. Non-personal categorical allowlist drops unknown
query values; request_type precedence is tested. No storage/model/URL changes.
`python manage.py test core.test_order_paths --verbosity 1`: 4 tests OK.
Design skills used: Frontend Design and UI/UX Pro Max. The local design-system
search returned a suitable three-step funnel but an unsuitable restaurant palette
and fonts; retained project typography/palette instead. Mobile choices will use
visible 44px controls and progressive disclosure, no external dependencies.
Rollback phase1: revert its scoped local commit; no data migration needed.

Phase2 VERIFIED locally (visual gate pending): nine-card `/start/`, bounded
sample selection, consultation and final destination routing. Existing metadata
blocks unchanged. English CRM/clinic cards explicitly say their forms are Persian;
the existing English form redirects remain intact. Delegated demo POST adapter
is present for the next phase; it calls the existing configure view rather than
reimplementing validation/idempotency. No new anonymous storage is added.
`python manage.py test core.test_order_paths core.test_project_start core.test_order_gateway --verbosity 1`:
12 tests OK. Initial two test failures corrected: escaped ampersand in English
label, and existing LanguageViewMixin lang-session write (now asserts exactly
the pre-existing lang key, not a false cookie-free claim). Old start tests now
expect nine topic links instead of the superseded three final-form cards.
Files: core/order_gateway.py, core/views/base.py, project_start.html,
includes/order_gateway.html, project-start.css, test_project_start.py,
test_order_gateway.py. Domain/browser gate will run before final acceptance.

## Unified order entry — phase 0 discovery (2026-10-09)

Status: discovery VERIFIED; implementation BLOCKED at the explicit pre-change
gate. Baseline `e5f64b0`. Single primary agent. No product files changed, no
SSH/push/deploy/database migration. Existing gallery/content-editor work preserved
and excluded from this documentation checkpoint. Framework stop policy used to
avoid silently expanding the draft/privacy/schema contract.

### Entry map — current vs proposed (proposed, not implemented)

Localized paths below mean `/fa/` and `/en/`. Existing URLs are retained.

| Surface / source | Current entry and continuation | Proposed entry |
| --- | --- | --- |
| `core/templates/core/base.html` header + hamburger | Start → `project_start`; Samples → gallery; Contact → `leads:contact`; Services → list | Order CTAs → start; browsing/contact distinction retained |
| Same template, mobile tabbar | Start → start; Choose → gallery; Solutions → services; account/admin destination independent | Same destination labels as header; start for order initiation |
| `core/templates/core/includes/footer.html` | Start → start; samples, CRM product and service browsing links | Start remains unified; browsing links not converted into misleading order CTAs |
| `core/templates/core/home.html`, `core/views/base.py` | Hero consultation → contact; sample hero/cards → preview; category chips → gallery `#demo-<slug>`; service cards → detail or CRM product; CRM/clinic/custom entries → three forms; closing → start | Order actions → start with validated type/demo context; demo browsing remains explicit |
| `core/templates/core/project_start.html` | Three cards: CRM, clinic, custom → their forms directly; EN CRM/clinic intentionally switch to FA | Seven route cards, with sample/brief stage before destination form |
| `services/templates/services/list.html`, `detail.html`, `includes/related_demos.html` | Consultation → contact; service-specific CTA → contact `?service=`; related sample buttons → preview/gallery or CRM product | Order CTA → start with service/type context, sample browsing remains explicit |
| `core/templates/core/crm_product.html` | Product/roadmap discovery CTAs → CRM create | Start `?type=crm` |
| `projects/templates/projects/demo_gallery.html`, `demo_preview.html`, `includes/related_service.html` | Gallery cards → preview; POST configure → contact `?demo=<token>&request_type=...`; discuss project → contact | Preserve validated demo context through start; existing configure hand-off needs scoped integration |
| `accounts/templates/accounts/dashboard.html`, `login.html` | New enquiry → contact; continue saved enquiry → contact; login/signup preserve next destination | New order → start; continuation must go to its own saved form, not restart selection |
| `blog/templates/blog/detail.html`, `includes/home.html`, article bodies | Related solution → service/CRM page; body links also directly target clinic-order/CRM/contact and gallery | Article bodies and metadata frozen in this scope; downstream service CTAs can lead to start. Do not rewrite approved article wording |
| Existing thanks templates | Lead: services/home; CRM/clinic: home/contact | Common presentation only, retain each tracking URL and record |

### Shared fields and material differences

| Meaning | LeadForm | CrmOrderForm | ClinicOrderForm | Consequence |
| --- | --- | --- | --- | --- |
| Contact name | `name` | `contact_name` | `contact_name` | Must not silently replace contact person with account owner |
| Phone | `phone` (optional at model level; required for phone contact) | `phone` required | `phone` required | Preserve each final form's validation |
| Email/contact channel | `email_or_telegram` accepts either | `work_email` EmailField | `work_email` EmailField | Telegram is not an email; not a lossless automatic mapping |
| Business | `business_name` optional | `organization_name` required | `clinic_name` required | Not stored in existing safe draft |
| Website | `website_url` | `website` | `website` | Free-text URL excluded from safe draft |
| Budget | unsure, under50, 50–150, 150–500, over500 million | under100, 100–250, 250–500, over500, estimate/private | under150, 150–300, 300–600, over600, estimate/private | Ranges overlap but differ; cannot silently reinterpret a choice |
| Timeline | flexible, within1, 1–3, over3 months | under1, 1–2, 2–4, over4, unsure | under2, 2–4, 4–6, over6, unsure | Ask route-specific choice once; no nearest-range heuristic |
| Consent | `privacy_accept` | `privacy_accept` | `privacy_accept` | Never auto-check from a draft |

Lead has three wizard steps; CRM five; clinic six. CRM/clinic create and thanks
currently redirect English requests to Persian on create. Therefore the requested
old-URL 200 + fully English specialist journeys is NOT true today; it needs
view/template/form-label work after the gate, not a changed URL or model.

### Current data, completion and messaging map

- `projects/views/projects.py`: active DemoTemplate → server-minted submission
  token → validated POST DemoConfigureView → session-bound DemoSelection;
  normalized theme/personality/features/brief → contact. Seven existing categories:
  ecommerce, restaurant, portfolio, corporate, clinic, education, jewelry; NO CRM.
- `projects/sector_catalog.py`, `demo_briefs.py`, `demo_snapshots.py`: domain-specific
  scene/choices, four brief dimensions (goal/scope/content/timing), frozen bilingual
  snapshot. They are not a contact-data store or arbitrary CRM module store.
- `leads/demo_handoff.py` + `leads/signals.py`: existing anonymous pending selection
  marker → login consumes into account-bound leads_contact draft; authenticated
  contact request attaches/retries; invalid explicit demo never falls back.
- `leads/form_draft_service.py`, draft API + wizard engine: allowlisted categorical
  Lead selections only; 7-day retention, optimistic revision, same-account
  continuation. Finalization links idempotently to submitted Lead, not CrmOrder or
  ClinicOrder. `FormDraft.FORM_TYPES` contains only `leads_contact`, max step2.
- `leads/views/contact.py`: service/demo-derived initial values and bounded timing
  mapping; final Lead + existing notification email; `thanks/<code>/` (noindex).
  CRM/clinic views: final respective model, existing email, respective
  `thanks/<code>/` (noindex); no equivalent account draft/demo attachment exists.
- `management_portal/signals.py`: Lead/CrmOrder/ClinicOrder post_save → respective
  `sync_source_case` → CustomerCase documents/activity and sales notification.
  Lead alone also syncs demo snapshot. `management_portal/notifications.py`
  handles push/SMS and reminders from existing notifications. None needs altered
  message text merely for presentation/routing. No email or SMS sent in discovery.
- ADR-001 confirmed: keep three domain models; CustomerCase is operational union,
  NOT permission to use its final documents as an unfinished PII draft store.

### Stop-gate findings (before any implementation)

1. **Required decision — persistent shared contact fields.** Existing FormDraft
   explicitly forbids `name`, `phone`, `email_or_telegram`, `business_name`,
   `website_url`, `message`, `privacy_accept`. Its API/service rejects those
   fields even for logged-in users. Saving these to JSON anyway would breach
   the existing security contract. Adding CRM/clinic form types/step bounds or
   linking their completed records through this model requires schema/lifecycle
   work outside the prompt's no-model/no-migration boundary. New anonymous
   session/localStorage or URL parameters carrying PII are not alternatives.
2. **CRM module continuation.** Existing demo categories do not include CRM;
   the CRMProductView has **nine**, not eight, features plus six roadmap paths.
   The existing snapshot validator does not accept arbitrary module selections.
   Do not invent a CRM DemoTemplate category or disguise it as corporate.
   A display-only module builder is possible without schema; persisted arbitrary
   choices through the named existing services is not currently supported.
3. **Protected-file conflict.** All gallery order cards must be rebuilt from the
   proposed source, but gallery template/view have owner edits that must not be
   touched or committed. Existing main has `#demo-options`; specific `#demo-<slug>`
   targets depend on the dirty gallery. Adopt stable `#demo-options` later and test
   all fragments against the clean candidate, or open a scoped gallery integration.
4. **No sitemap/metadata change needed for the entry skeleton.** `/start/` already
   exists; stages can use validated query parameters. No new public URL has been
   approved, and title/description/schema/canonical/hreflang must stay unchanged.

### Six concurrent UI findings — confirmed, NOT changed

Home category fragment dependency; header/mobile labels differ; two home tel
targets use raw company.phone vs +98 footer; FA English-test CTA is less precise;
closing start selector is CRM-heavy; below-fold home article include passes
`featured=forloop.first`, causing eager/high-priority image. These can be fixed
later without changing exam logic, article wording or metadata. No CSS/UX
implementation or screenshot is claimed in this read-only phase.

### Evidence and decision to resume

Read-only executable check (no database queries/writes):
`python manage.py shell -c` imported model/service definitions and called
`normalize_fields` with synthetic inputs. Output:

```text
Draft form types: ['leads_contact']
CRM feature count: 9
Demo categories: ['ecommerce', 'restaurant', 'portfolio', 'corporate', 'clinic', 'education', 'jewelry']
leads_contact REJECTED forbidden_field
crm_order REJECTED unsupported_form_type
```

No regression/full/browser tests: no runtime code changed; discovery does not
claim current old routes return 200 or a rebuilt UI exists. `git diff --check`
is the documentation gate. No production read/write this phase.

Recommendation within strict boundaries: collect contact/business fields **once
in the final route-specific form**, not a separate common identity stage; retain
existing safe Lead draft behavior without claiming CRM/clinic cross-device save.
This needs owner's explicit reduced-scope acceptance. Alternatively, authorize
a separate authenticated-only draft/privacy design and the necessary migrations
for all three routes before implementing persistent shared data/module choices.
Also decide whether the existing gallery edits may receive scoped integration
without being included in this task's commits. Do not silently pick either.

Phase ledger: 0 VERIFIED (discovery); 1–5 NOT_STARTED; overall BLOCKED by the
above data/scope decisions. Next action: owner's scope decision, not deployment.
Rollback: documentation-only commit can be reverted; no data/UI to roll back.

## Homepage clarity — VERIFIED local; owner review NOT_STARTED (2026-10-09)

### Scope and checkpoint

Baseline 5559e45; implementation commit d2dce41 (16 scoped files). Single primary
agent; this is technical self-review, not independent review or a completed
five-second user study. No push, SSH, deployment, production access or
permanent database migration. P1-3/P4-1 remain DEFERRED. Earlier P3-5 is superseded
by the owner's approved bilingual hero. Overall SEO programme remains PARTIAL.

Implemented: visible offer/audience H1, two commitment-level CTAs within the phone
first fold, database-driven active service cards plus CRM, three featured samples
and all category links, explicit fictional-sample disclosure, compact existing
process, one custom-system band, one assessment band, real CompanyProfile identity,
existing journal and closing consultation CTA. Header has the six requested entries
and persistent project CTA. Phone has a separate layout, native sample scrolling
with a visible hint, two-column services, no decorative hero art and 44px+ targets.
No counters, testimonials, prices, invented customers or new performance promises.
English secondary section labels are direct neutral translations; owner may review
them, whereas the H1 and lead use the explicitly approved copy.

Home title, description and raw JSON-LD are byte-identical to baseline in FA and EN
(sequential local HTTP comparison), including existing metadata contract tests.
PWA sheet, welcome sound, mobile tabs and shared shell scripts remain untouched;
the retained install-guide trigger and delegated close/open behavior were checked.

Owned files: core/views/base.py; core/templates/core/{home,base}.html;
core/static/core/css/{home-studio,public-shell}.css; core/{tests.py,test_home.py,
tests_seo_contract.py}; DESIGN.md; UX-CONTRACT.md; this report; CURRENT_STATE.md;
PROJECT_STATUS.md. Removed confirmed-unused home-studio.js, home_journey.html and
home_journey_art.html. Kept shared demo-studio.css, demo art and journal components
because gallery/detail/reader surfaces still use them. No new assets/dependencies,
models or migrations. Three protected gallery files and unfinished editorial-desk
work are excluded; protected diff SHA256 stayed
`b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba`.

### Test evidence

Artefact root: /tmp/rvion-home.xbtPni (before/after isolated baseline archives).
Temporary test databases only; public fixture data is from existing seeds/drafts.
Candidate archive excludes unrelated dirty work without resetting/stashing it.

| Gate | Result |
| --- | --- |
| Red: initial core.test_home against old homepage | 9 tests: 5 failures, 3 errors, 1 pass; red.txt |
| Initial green: core.test_home | 9/9 OK; green-home.txt |
| Working-tree core.tests + core.test_home + blog.test_journal | 56/56 OK |
| Isolated core.tests + core.test_home + core.tests_seo_contract + blog | 122/122 OK |
| Final full candidate suite, once after the last two tests | 1109 tests, OK; 27 pre-existing PostgreSQL-only skips; full.txt |
| manage.py check / compileall -q core / pip check | 0 issues / success / no broken requirements |
| git diff --check | clean |
| designmd lint DESIGN.md | 0 errors; 2 existing unused-token warnings |

Exact commands used the project's /Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python:
`manage.py test core.test_home --verbosity 1`;
`manage.py test core.tests core.test_home blog.test_journal --verbosity 1`;
`manage.py test core.tests core.test_home core.tests_seo_contract blog --verbosity 1`;
final `PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps <python> manage.py test --parallel 4 --verbosity 1`.
Final suite ran in /tmp/rvion-home.xbtPni/after; 1082 executed tests passed.
No repeat full suite, CI, real PostgreSQL, physical iPhone or screen-reader study.

Existing tests changed explicitly: approved hero H1 replaces slogan-only assertion;
project CTA count 3→4 accounts for closing CTA; obsolete journey assertions now
check single custom/assessment bands and both exam briefings; seven featured-card
expectation becomes three cards plus all seven category links. Contextual SEO home
contract now checks the real service grid plus CRM instead of a duplicate appendix.
Eleven new tests cover bilingual copy, real/edited/inactive service data, slug/order
fallback, sample categories, empty catalogue, public identity, all required target
URLs (200 without redirects), unchanged metadata and retained header/shell.

### Browser and local performance

Twelve before and twelve after screenshots, each FA/EN × light/dark × 390/768/1440:
all listed below are under /tmp/rvion-home.xbtPni/.

| Language/theme | Before screenshots | After screenshots |
| --- | --- | --- |
| FA/light | before-fa-light-390.png, before-fa-light-768.png, before-fa-light-1440.png | after-fa-light-390.png, after-fa-light-768.png, after-fa-light-1440.png |
| FA/dark | before-fa-dark-390.png, before-fa-dark-768.png, before-fa-dark-1440.png | after-fa-dark-390.png, after-fa-dark-768.png, after-fa-dark-1440.png |
| EN/light | before-en-light-390.png, before-en-light-768.png, before-en-light-1440.png | after-en-light-390.png, after-en-light-768.png, after-en-light-1440.png |
| EN/dark | before-en-dark-390.png, before-en-dark-768.png, before-en-dark-1440.png | after-en-dark-390.png, after-en-dark-768.png, after-en-dark-1440.png |

browser-layout.json: zero page/header horizontal overflow in all 12 after states;
EN main has no Persian text. Both phone CTAs end before y459 (844px viewport);
services begin at y654 FA / y696 EN. Native samples scroll inside their region,
not the page. Keyboard outline 3px; mobile menu opens/closes and clears tab bar;
reduced-motion transition 0s / scroll auto; no browser console errors. A sibling
corporate service page also has zero mobile overflow after the header change.
contrast.json: checked text ratios 4.98–16.60 light / 6.60–13.33 dark, all >=4.5;
Lighthouse contrast and accessibility scores 1 in all three after runs. This is not
a whole-site WCAG certification.

Local Lighthouse 13.5 / Chrome 154, same fixtures, default simulated mobile throttle:
`CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' PATH=/opt/homebrew/bin:$PATH npx --yes lighthouse http://127.0.0.1:<port>/fa/ --quiet --chrome-flags='--headless --no-sandbox' --only-categories=performance,accessibility --output=json --output-path=<artefact>`
Three runs each: baseline port8153, candidate8154; before-lh-1..3.json / after-lh-1..3.json.

| Local measurement | Before runs | After runs | Median before → after |
| --- | --- | --- | --- |
| LCP ms | 4816.34, 4815.12, 4823.04 | 4527.80, 4520.39, 4670.03 | 4816.34 → 4527.80 |
| TBT ms | 882, 803, 719 | 923, 525, 603 | 803 → 603 |
| CLS | 0, 0, 0 | 0, 0, 0 | 0 → 0 |
| Render-blocking CSS count | 8, 8, 8 | 8, 8, 8 | 8 → 8 |

Median acceptance passes. First after TBT is worse than baseline median; variability
is not hidden. These are local comparisons, not production performance evidence.

### Tool limitations and risk triage

Premium strict audit raw result is NOT green: premium-audit.json has 10 findings.
Nine actionless-button findings are delegated data-attribute controls (eight existing
shared controls, one retained home install trigger); binding source and browser
behavior verify the actual handlers. One pre-existing WebKit-scrollbar finding
misses the standards scrollbar-color/width and forced-colors rules in tokens.css.
No fake inline handlers or weakened audit config were introduced. No genuine P0/P1
identified for this patch; raw tool output is retained, not relabeled as a clean run.
UI/UX catalogue searches for service-studio/mobile-clarity and hero/clear-CTA returned
no matches: no component research match is claimed. Approved brief, shared tokens,
frontend design guidance and browser evidence drove the implementation instead.

A concurrent local metadata probe hit an unchanged traffic-middleware SQLite write
lock (HTTP400 / OperationalError); the sequential probe then passed both languages
and both candidates. This temporary SQLite concurrency limitation is recorded,
not patched by changing deferred analytics/session behavior. No PostgreSQL release
concurrency result is claimed. No permanent data, article body/publication flags,
exam bank, registration or customer contract was modified.

### Owner review, remaining decisions and rollback

Five-second pack: owner-390-first-fold.png; owner-1440-first-fold.png;
owner-services.png, in the artefact root above. Ask without prompting answers:
1. What does this company sell? 2. Who is it for? 3. What would you click first?
Owner runs this test; no participant results or approval are claimed here.

Owner decisions needed: visual acceptance and any secondary EN microcopy changes;
existing sameAs/author/byline, dates/order and v2 cover approvals remain open from
earlier phases. No author model/migration. Publication NOT_STARTED by this task's
explicit restriction. After approval, a separate authorized release must preserve
dirty work, pass its own CI, restore SSH and use the backed-up official release path.

Rollback: revert this scoped homepage commit (and documentation checkpoint if
desired) back to 5559e45; no database/media rollback is needed. Do not reset the
working tree or revert unrelated editorial-desk/gallery work. Temporary screenshots
remain for owner review; only agent-created browser/test-server resources are closed.

## Editorial reader and coherent cover candidates — VERIFIED local / release BLOCKED (2026-10-09)

### Authority, scope and provenance

The owner's direct request authorizes a deployment retry after local tests/commits.
It supersedes the attachment's general no-deploy wording, but not its explicit
cover-approval boundary. **No v2 production hero_image assignment is authorized yet.**
No migrations, article wording/front matter, publication flags, author metadata,
analytics/session/cookie/cache policy, or protected gallery/editorial-desk changes.
P1-3/P4-1 remain DEFERRED. Single primary agent: technical self-review, not
independent review or owner visual acceptance.

Starting HEAD fcb4d0b; live-equivalent baseline 66a7cbf; local previous design
541c9ca. Reproducible isolated candidates were archived from these commits in
/tmp/rvion-reader.xBtbsP/{live,before,after}. The candidate contains only the owned
blog changes and home CSS version bump; unrelated dirty admin/gallery files are
excluded. Browser fixtures contain the four real source drafts plus an explicitly
synthetic bilingual code example (not a real translation or new published article).
Only temporary test databases were created/destroyed; no permanent SQLite or
production data was written.

### Task 1 — VERIFIED locally

Observed before: the live-equivalent article has an oversized title/dead space,
a repeated title in the summary, narrow/light stock cover, tag-only sidebar and
weak reading hierarchy. 541c9ca improves navigation but retains a long phone TOC,
repeated intro and large title; the two columns constrain the reading measure.

Implemented: content-height header with existing tag/category, exact-prefix-only
dek deduplication, real publication date and estimated reading time; 700px desktop
column, 18px/1.95 prose, 17px separate phone layout. Four actual article H1s
rendered in two desktop lines. CSS-only first-paragraph lead, distinct H2/H3,
real lists, tinted quotation callout, underlined links, LTR literal code and bdi
for Latin phrases. A parser processes the already-bleached HTML to add stable,
Persian-safe, duplicate-safe heading IDs without restoring unsafe attributes.
External links gain noopener, never a new target.

Contents: sticky desktop rail, collapsed native phone disclosure, current-section
highlight and reading progress. Cover geometry 1200x630/eager/high priority and a
neutral frame. Same-tag/published/same-language related posts, previous/next for
3+ available posts, contextual existing service link and copy-link with a
selectable-link recovery path. The corporate-cost CTA was corrected during
self-review to prefer its existing corporate-design link rather than the first
incidental ecommerce link. Copy stays disabled until its enhancement initializes.
The list uses one featured item plus a grid without duplicating the first item;
search/tag/pagination and intentional empty/single/no-cover states remain.

Files: blog/presentation.py; blog/views/{post_detail,post_list}.py;
blog/templates/blog/{detail,list}.html and includes/card.html;
blog/templatetags/blog_extras.py; blog/static/blog/{css/journal.css,js/reader.js};
blog/test_journal.py; core/templates/core/home.html (CSS version only); DESIGN.md.
The v2-only alt helper is blog/covers.py; v1/unknown images retain their existing
title-derived fallback, so new-image descriptions never misdescribe live v1 art.

Browser evidence: all five route cases at 390/768/1440 in light/dark (30 after
screens, 60 before), no document horizontal overflow. FA-only real article;
FA/EN chrome verified with the temporary code fixture and localized list, not by
inventing English versions of Persian-only articles. All four real article
titles/700px width checked at 1440. Phone TOC starts closed; code remains LTR/pre
and literal template syntax; copy succeeds. Injected clipboard rejection (QA
stub, not a real device permission test) exposes/focuses the selectable link and
reenables the button. Reduced-motion emulation gives auto scroll, no image
transition; reset afterward. Keyboard TOC focus has a 3px outline. Search renders
one real article and opens its matching service route; zero-result state offers
a clear recovery. No real iPhone or screen-reader certification is claimed.

Measured AA ratios from actual computed colors:
dark body 16.05, links 9.04, callout 12.44;
light body 16.60, links 6.01, callout 16.84 (all >=4.5).
Lighthouse color-contrast audit passes in all three final light-theme runs;
this is not a claim that every global shell accessibility issue is solved.

### Local Lighthouse — three valid mobile runs, NOT production

Chrome 154.0.8037.98, Lighthouse 13.5.0, default simulated Moto G Power.
Same real article/source cover on the isolated previous and final candidates.
The final benchmark ran after the test suite finished (no concurrent test load).

| Candidate | LCP median ms | TBT median ms | CLS median |
|---|---:|---:|---:|
| 541c9ca | 4516.35 | 732 | 0.10159 |
| final local reader | 4517.40 | 435 | 0 |

Final individual runs: LCP 4365.90/4517.40/4517.77 ms;
TBT 658/435/422 ms; CLS 0/0/0. LCP is effectively unchanged and remains
above the good threshold; TBT is lower in this sample but still not good.
No blanket speed or SEO ranking guarantee. Preloading the three existing
Vazirmatn font weights removed the observed font-related shift without touching
cache/session policy. v2 image performance is NOT included (covers are not swapped).

Artifacts: before-lh-1.json, before-lh-2-retry.json, before-lh-3.json;
final-lh-2.json, final-lh-3.json, final-lh-4.json in the same /tmp folder.
Excluded but retained: before-lh-2.json (NO_NAVSTART); initial after-lh-* runs
without preloads; after-preload-lh-* intermediate runs; final-lh-1.json overlapped
the full test suite and is not used in the final median.

Command (repeat 3 runs per candidate with distinct output files):
```sh
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' PATH=/opt/homebrew/bin:$PATH npx --yes lighthouse http://127.0.0.1:8155/fa/blog/corporate-website-cost-1405/ --quiet --chrome-flags='--headless --no-sandbox' --only-categories=performance,accessibility --output=json --output-path=/tmp/rvion-reader.xBtbsP/final-lh-2.json
```
Previous candidate used port 8154 and --only-categories=performance.

### Test evidence and review

- Initial new parser expectations: 7 tests, 2 failures (ordinal anchor expectations,
  and literal template text being bidi-wrapped). Both were corrected with real
  parser/escaping fixes; neither unsafe-content nor literal-code assertions weakened.
- Final targeted candidate:
  `/Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test blog core.tests_seo_contract --verbosity 1`
  — 81/81 OK, 12.243s, including 15 journal tests and whole-sitemap four-post fixture.
- Full suite run **once** at final code boundary:
  `PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps /Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test --parallel 4 --verbosity 1`
  in isolated after checkout — 1098 tests, 1071 passed, 27 PostgreSQL-only skipped,
  58.480s, OK. Log /tmp/rvion-reader.xBtbsP/full-suite.log.
  Expected injected SMTP/provider failures are log evidence, not test failures.
- check 0 issues; makemigrations --check --dry-run No changes detected;
  git diff --check clean; node --check blog/static/blog/js/reader.js passed.
- Premium strict scoped audit (brand-site, blog templates/static roots) 0 findings.
  First static finding correctly exposed a copy action enabled before enhancement;
  initialization now enables it only after binding. Existing projects-only manifest
  was not weakened/edited; no claim of a clean unrelated gallery-wide audit.
  Artifact blog-premium-audit.json and explicit scope blog-premium.json in /tmp.
- Real PostgreSQL/full CI for this new patch not run; no transactional/model change.
  Earlier 541c9ca quality run 37883116866 is now observed SUCCESS on both matrices
  through GitHub's public API, **not evidence for this new unpushed patch**.
- Self-review: source diff, sanitized text/links/code, four real titles, bilingual
  presentation, media preservation and scoped dependencies. Unrelated dirty work
  remains unchanged; protected-gallery diff SHA256
  b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba.

### Task 2 — VERIFIED prepared assets; owner visual approval pending

22 built-in generated candidates inspected, two initial candidates per article;
selected regenerated rounds for 01–04 (crop/frame), 06 (forbidden drawn hand)
and 07 (flat four-stage rather than plant/isometric motif). Never more than two
rounds per article. Selection, exact prompts and generated PNG provenance/date:
[ARTICLE_COVER_PROMPTS_V2.md](ARTICLE_COVER_PROMPTS_V2.md).
No stock assets, visible text/digits/logos/faces/hands, scoring guarantees,
surveillance or medical cross in the selected set. Common dark/ivory/grey/orange
palette, restrained linework, safe central composition. JPEG conversion/resampling
only, no scripted creative editing; source images retained in generated_images.

Final sRGB RGB JPEGs 1200x630 under blog/content_drafts/covers/, all with -v2 suffix.
Existing v1 files and production image references are unchanged by this task.
QA sheets /tmp/rvion-reader.xBtbsP/covers-v2-thumbnails.jpg (360px each, light
surround) and covers-v2-crops.jpg (centered 4:3, dark surround), both visually
inspected. Each individual thumbnail/crop is also retained as cover-N-360.jpg
and cover-N-4x3.jpg. Labels in the QA sheets are outside the actual assets.

| # | Filename stem (-v2.jpg) | No forbidden content | Series/colors | Clear idea | 360px | 4:3 | Both surrounds | Bytes <=150KB |
|---|---|---|---|---|---|---|---|---:|
| 1 | corporate-website-cost-1405 | YES | YES | YES | YES | YES | YES | 34804 |
| 2 | custom-website-vs-template | YES | YES | YES | YES | YES | YES | 40268 |
| 3 | custom-or-ready-made-crm | YES | YES | YES | YES | YES | YES | 30075 |
| 4 | english-teacher-assessment | YES | YES | YES | YES | YES | YES | 34559 |
| 5 | clinic-website-design-online-booking | YES | YES | YES | YES | YES | YES | 32706 |
| 6 | academy-website-structure-webinar | YES | YES | YES | YES | YES | YES | 31557 |
| 7 | enterprise-crm-development-cost-stages | YES | YES | YES | YES | YES | YES | 26793 |
| 8 | django-interview-questions-with-short-answers | YES | YES | YES | YES | YES | YES | 27943 |

Descriptive Persian/English one-sentence alt text is stored in blog/covers.py
COVER_ALTS keyed by the generated filename's article slug; only known -v2.jpg
assets use it. Tests cover all eight and prevent applying new descriptions to v1.
No new model field, schema, article publication or importer behavior changed.

### Task 3 — VERIFIED report; deployment retry BLOCKED

Implementation/assets/checkpoint commit: 0492c76
`feat(blog): refine editorial reader and prepare coherent v2 covers`.
Only the 25 explicitly scoped files were staged. Working tree still contains
the owner's unrelated gallery/editorial-desk work; it was not cleaned or committed.
This follow-up records the immutable implementation hash; no test rerun needed
for the documentation-only update.

A bounded read-only SSH retry with the existing rvion.pem, BatchMode,
IdentitiesOnly, IPQoS=none, ConnectTimeout=12 and server-alive limits returned
"Connection to 188.121.101.173 port 22 timed out". No hostname/source/status could
be read remotely. No pull, backup, release, migration, restart or image swap ran.
GitHub CLI itself has no active auth; prior CI status was read via the public API.
No new push/CI initiated after the first genuine deployment blocker.
Last verified production runtime remains 66a7cbf; current public /health/ returned
{"status": "ok"}, which is not a new-version deployment claim.

Rollback: revert this bounded reader/assets change (and use the normal backed-up
release path only after connectivity returns); no data/schema rollback needed.
For eventual v2 cover swap, preserve old media files and the old hero_image mapping
below so the image-reference-only write can be reversed independently.
P1-3/P4-1 remain DEFERRED, byline is design-only, no migration authorized.

### Exact v2 cover swap steps — PREPARED ONLY, do not run before visual approval

1. Deploy the verified source through the existing ops/release.sh after CI;
   do not import/publish articles 05–08 as part of the cover replacement.
2. Take a PostgreSQL custom-format snapshot and verify its catalog:
```sh
RVION_COVER_STAMP=$(date -u +%Y%m%d-%H%M%S)
sudo -u postgres pg_dump --format=custom --no-owner --no-privileges arvion | sudo tee /srv/arvion/backups/pre-cover-v2-$RVION_COVER_STAMP.dump >/dev/null
sudo chmod 0600 /srv/arvion/backups/pre-cover-v2-$RVION_COVER_STAMP.dump
sudo pg_restore --list /srv/arvion/backups/pre-cover-v2-$RVION_COVER_STAMP.dump
```
3. Execute the following only after approval. It changes only the four existing
   posts' hero_image and keeps old files; it does not publish anything:
```sh
sudo -u arvion bash -c 'set -a; source /srv/arvion/.env.production; set +a; DJANGO_SETTINGS_MODULE=arvion.settings.production /srv/arvion/.venv/bin/python /srv/arvion/manage.py shell' <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
from django.core.files.base import ContentFile
from django.db import transaction
from blog.models import Post

slugs = ['corporate-website-cost-1405', 'custom-website-vs-template',
         'custom-or-ready-made-crm', 'english-teacher-assessment']
source = Path('/srv/arvion/blog/content_drafts/covers')
stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
mapping_file = Path('/srv/arvion/backups') / ('hero-images-before-v2-' + stamp + '.json')
with transaction.atomic():
    posts = list(Post.objects.select_for_update().filter(slug_fa__in=slugs))
    assert len(posts) == 4, 'Stop: expected all four existing articles'
    assert all((source / (p.slug_fa + '-v2.jpg')).is_file() for p in posts)
    mapping_file.write_text(json.dumps({p.slug_fa: p.hero_image.name for p in posts}))
    mapping_file.chmod(0o600)
    for post in posts:
        name = post.slug_fa + '-v2.jpg'
        post.hero_image.save(name, ContentFile((source / name).read_bytes()), save=False)
        post.save(update_fields=['hero_image'])
print('Updated 4 covers; rollback mapping:', mapping_file)
PY
```
4. Check all four public article pages/media URLs, actual alt and OG image,
   JPEG byte/dimension match, and phone/theme appearance. If anything fails,
   restore only hero_image from the timestamped mapping inside transaction.atomic;
   keep old media files intact. No full database restore unless separately needed.
   Catalog inspection runs as root because the snapshot is intentionally 0600.

### Owner decisions / remaining risks

- Visual approval of reader layout and the eight v2 covers; live cover swap waits.
- Author public name/role/bio and real modification date policy require a separately
  authorized model field/migration; no invented identity or update date.
- Restore authorized server SSH/console access; then push this verified patch,
  wait for its own Python 3.11/3.12 CI, and run backed-up release/public smoke.
- Local LCP/TBT still need wider shell-performance work; this scope does not
  change deferred analytics/session/cookie/cache policy or sound startup.
- Browser emulation is not real-device/screen-reader/production-performance proof.

### Screenshot manifest

Base /tmp/rvion-reader.xBtbsP. live=66a7cbf; before=541c9ca; after=this reader.
fa-cost=corporate-website-cost-1405; fa/en-code=temporary code-fixture;
fa/en-list=localized list. List includes a temporary extra code fixture, which
tests the intentional no-cover featured state; the single-real-article search
journey separately validates a cover-bearing featured card.

live:

- /tmp/rvion-reader.xBtbsP/live-fa-cost-390-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-cost-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-cost-768-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-cost-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-cost-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-cost-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-list-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/live-fa-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/live-en-list-1440-dark.jpg

before:

- /tmp/rvion-reader.xBtbsP/before-fa-cost-390-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-cost-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-cost-768-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-cost-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-cost-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-cost-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-list-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/before-fa-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/before-en-list-1440-dark.jpg

after:

- /tmp/rvion-reader.xBtbsP/after-fa-cost-390-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-cost-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-cost-768-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-cost-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-cost-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-cost-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-list-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/after-fa-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-390-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-768-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-code-1440-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-390-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-390-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-768-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-768-dark.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-1440-light.jpg
- /tmp/rvion-reader.xBtbsP/after-en-list-1440-dark.jpg

Additional interaction evidence: after-mobile-code-interaction.jpg,
after-copy-recovery-mobile.jpg, after-mobile-empty.jpg,
after-desktop-reading.jpg, final-mobile-article-light.jpg in the same folder.
The empty-state first exact-string check omitted the period; a subsequent DOM
snapshot confirmed the correct "مقاله‌ای پیدا نشد." message and recovery link.
All paths are local QA artifacts, not production screenshots.

## Owner-authorized release and first four publications — VERIFIED deployment/data (2026-10-08)

Owner directly authorized publication, the custom dashboard article editor and
the next bundle. This overrides the pasted no-production restriction, not the
protected-gallery, privacy or assessment-bank confidentiality boundaries.

- Source: 66a7cbf pushed; quality CI 37833575777 SUCCESS. Its unchanged source
  retains the prior 1083-test/27-PostgreSQL-skip full-suite evidence. No fresh full
  suite was claimed for the uncommitted editorial desk.
- SSH initially timed out during key exchange. A recovered read confirmed runtime
  c722766, clean source and active arvion/nginx; previous stalled release had not
  run. Ubuntu's pull failed on .git/FETCH_HEAD ownership. Running the same pull as
  its existing owner arvion succeeded; no broad chmod/chown/reset was used.
- Exact release: `sudo -u arvion git -C /srv/arvion pull --ff-only origin main`,
  then `cd /srv/arvion && sudo bash ops/release.sh`. Exit 0; commit=66a7cbf health=ok.
  Snapshot `/srv/arvion/backups/pre-release-20261008-200201.dump` catalog validated
  with `pg_restore --list`. No migrations to apply; seeded banks unchanged.
- Before publication, repository-loaded metadata/tags/bodies were compared against
  each stored draft. Only article 04 had its known pre-a6da984 sentence; other
  bodies were already exact. Every cover existed. No unexpected owner edit.
- `import_blog_drafts --dry-run --update`: create 0 / update 4 / skip 0, no write.
  Actual `--update` and publication ran in one `transaction.atomic()` after a
  repeated locked preflight, preserving cover pointers and all English fields.
- IDs 1–4 published at real UTC `2026-10-08T20:03:07.537309+00:00`, not backdated.
  Four `article_publish` OperationalAudit rows use the owner's existing admin
  actor and record explicit authorization, release and backup identifiers.

Published URLs:

- https://rvionai.com/fa/blog/corporate-website-cost-1405/
- https://rvionai.com/fa/blog/custom-website-vs-template/
- https://rvionai.com/fa/blog/custom-or-ready-made-crm/
- https://rvionai.com/fa/blog/english-teacher-assessment/

An initial external probe timed out in Python TLS; its curl retry incorrectly
counted the language-switch anchor as an SEO alternate. The probe was corrected
to inspect only `<link>` tags; neither failure required product code changes.
Corrected external curl smoke PASSED all four: HTTP200, exactly one h1, exact
self canonical, existing cover URL, and no English SEO alternate. All four
are present in the live sitemap; public health returns {"status":"ok"}.
Search Console indexing has not been requested; no author field/migration added.

Editorial desk is PARTIAL/local: new article_forms/article_views/test_articles,
articles.css, articles/article_edit/article_preview/_article_field templates,
URL registrations and content-center entry. Twelve targeted tests and 115-test
management regression pass in an isolated temporary DB/candidate excluding
protected gallery changes. Mobile FA editor inspected at 390x844, scrollWidth
390; full bilingual/browser review and final full suite still pending. No panel
commit/push/deploy yet. Sources 05–08, their reviews and covers not completed.

Rollback: unpublish only these four article IDs after checking their current
revision/audit, preserving contents/covers/customer data. Reverting 66a7cbf source
uses the official release path. The validated pre-release dump is emergency
recovery evidence, NOT an instruction to overwrite a live DB with new user data.
Canonical state is CURRENT_STATE.md; no parallel status document created.


## Article claims / language-list indexing — VERIFIED (2026-10-08, local only)

Starting HEAD was dc4ad72, not the attachment's 416aa97: the intervening cover
asset commit is preserved. Production runtime c722766 is owner-supplied history,
not rechecked in this phase. Owner reports the four unpublished article URLs are
404; that is owner evidence, not a new agent probe. No production access allowed.
Single primary agent; three dirty gallery files excluded. P1-3/P4-1 DEFERRED.

### Task 1 — VERIFIED locally: article claim reconciliation

Evidence is current repository code/public templates, not a guarantee about
live question-bank contents or pedagogical validity. The following inventory
covers the article's assessment/monitoring/review/result/report/certificate
statements; educational recommendations are distinguished from product promises.
Article line references are blog/content_drafts/04-english-teacher-assessment.md.

| Article statement / location | Evidence or limitation | Decision |
|---|---|---|
| Title/summary, lines 3–4: guide to teacher assessment, interviews/demo, reading results | Article sections themselves; seed_assessment_banks.py:90–94 defines a teacher assessment | Keep; not accreditation |
| Lines 7, 11–17: combine assessment, structured interview and demo; interview limitations/research numbers | Employer advice and cited research, not an Rvion implementation promise | Keep; external research accuracy not independently re-audited |
| Lines 21–30: language accuracy; five proposed item domains; grammar explanation, vocabulary, critical reading, listening, editing | Explicitly a proposed non-standard framework; assessments/management/commands/seed_assessment_banks.py:90–94 public catalogue covers these domains | Keep; no claim of manual grading |
| Lines 34–37: pedagogical analysis / judge explanations and methods | Cited Richards material and employer framework; seed catalogue includes pedagogical analysis | Keep; real hiring predictive validity UNVERIFIABLE |
| Line 41: university qualification vs standard language scores vs teaching credentials; added value of custom assessment | General distinction, not Rvion-issued accreditation or standard certification | Keep |
| Lines 45–47: screening comparable applicants; demo costs and classroom observations | Employer recommendations; no measured Rvion cost/savings claim | Keep; benefit magnitude UNVERIFIABLE |
| Line 49 sentence 1: linked Rvion assessment targets grammar, vocabulary, reading, listening, editing, pedagogy | seed_assessment_banks.py:90–94 and public /fa/assessments/english-placement-a1-c1/about/ via briefing.html:19–27 | Keep; catalogue evidence, not new live verification |
| Line 49 sentence 2: not a substitute for interview/demo, may narrow the shortlist | Qualified recommendation, no guaranteed outcome | Keep |
| Line 53: remote unsupervised scores may involve outside assistance | General risk statement; no claim that monitoring proves it | Keep |
| Line 55 bold lead: monitoring gives indications, not a verdict | assessments/integrity.py:241–242 and briefing.html:32 explicitly avoid conclusive cheating verdicts | Keep |
| Line 55 sentence about human review before rejection | Contradicted as a universal description by integrity.py:65–81 automatic policy enforcement; assessments/test_copy_stop.py:40,82,189 cover preservation/reload/no scoring | Replace only this sentence |
| Remaining line 55: remote-proctoring research, no absolute guarantee | Cited external paper; general caution, not a new Rvion signal/threshold disclosure | Keep; independent literature audit not in scope |
| Line 56: examine answers/errors instead of only total score | Employer advice; ResultView assessments/views.py:914–974 supplies correct/selected answers and explanations | Keep |
| Line 57: ask applicants to explain answers at interview | Employer action, not a promise that Rvion supplies a human reviewer | Keep |
| Line 59 sentence 1: Rvion introduction mentions health monitoring and answer review | briefing.html:31–38; integrity_evidence_summary; ResultView above; management_portal/views.py:477,533–534 report evidence/policy separately | Keep; review here means answer review, not guaranteed staff adjudication |
| Line 59 sentence 2: ask what is recorded/who reviews/what applicant knows | Buyer due-diligence advice | Keep; no internal details added |
| Line 63: IF report is skill-separated, compare skill profiles and ask provider | Conditional buyer advice; ResultView prefetches skill_results__skill and exposes learning plan | Keep; no invented score scale or report format |
| Lines 64–67: define minimums, explain decision, trial period/classroom observations | Employer selection workflow, not automated product hiring decision | Keep |
| Lines 73–76: explain monitoring, equal conditions, provide technical path, no accent bias, give weakness summary | Employer fairness advice; test_copy_stop.py:135,170 covers appeal/retake; saved answers retained | Keep; no promise of human remediation response time |
| Line 80: may not need custom test for low-volume hiring; need someone to read results; child/specialist classes may need other items | Conditional suitability advice, no new product capability | Keep |
| Lines 84–89: checklist for skills/interview/demo/minimums/monitoring/review | Employer checklist summarizing advice, not Rvion personnel/services | Keep |
| Line 91: contact to discuss suitability | /fa/contact/ existing enquiry route; importer route test | Keep |
| Rvion certificates, prices, duration, score scale, human marking/accreditation | No such affirmative product claims in this draft; generic IELTS/TKT/CELTA examples are not Rvion credentials | Nothing to add |

Exactly one sentence changed (line 55); front matter, all other body bytes,
headings, links, citations and trailing newlines remain identical.

| Before | After |
|---|---|
| سامانه‌ای که الگوی غیرعادی را علامت می‌زند باید خروجی‌اش به بازبینی انسانی برسد، نه رد خودکار. | سامانه نشانه‌های سلامت آزمون را ثبت می‌کند؛ ادامه آزمون تابع قوانین اعلام‌شده آن است و علامت‌گذاری یک رفتار به‌تنهایی اثبات تقلب نیست. |

No signals, counters, thresholds or bypass instructions were added to the public
draft. Original body hashes remain pinned: test_import_drafts reverses only this
single allowed replacement before comparing article 04 to its original hash;
01–03 are still compared directly. Teacher title+brand 56 characters; summary
131. No public article, published status, author, date, cover or live record edited.

### Drafts 01–03 — bounded Rvion-claim inventory (no edits)

| Draft / Rvion statement | Evidence | Owner limitation |
|---|---|---|
| 01: quoted market prices are NOT Rvion's offer (line 18) | Explicit disclaimer; no Rvion price set | Owner must still approve external price figures/date |
| 01: e-commerce, maintenance and corporate-design services (38,55,59) | services/migrations/0004_service_sales_content.py:13,27,34; matching /fa/services/<slug>/ pages | Catalogue only; commercial scope/SLA/quotes UNVERIFIABLE |
| 01: six named demo domains, anonymous colour/style changes, send choices (61,92) | projects/views/projects.py:164,188; projects/tests.py demo-to-enquiry tests; persisted DemoSelection handoff | Verified repository flow, not real customer brands or deployed performance |
| 02: corporate/custom-webapp/maintenance services (13,45,55,82) | Same service migration, custom-web-application at line 20 | No promise that a template/WordPress delivery service is offered; such commercial offer UNVERIFIABLE |
| 02: six demo types, anonymous customization/request (86,101) | Same demo flow and /fa/contact/ | No real portfolio/customer-success claim |
| 03: customizable independently deployed CRM for customers/sales/services/operations (19,70) | core/templates/core/crm_product.html:3,5,7,13 public product description | Published positioning; real deployments/security efficacy UNVERIFIABLE from this site alone |
| 03: maintenance/custom web-app services and CRM discovery wizard (66,90,107) | Service seeds above, /fa/crm-order/ existing create route | Individual implementation/ownership/SLA guarantees require owner confirmation |

Task-1 red/green, isolated clean-HEAD candidate + only scoped changes:

```text
.venv/bin/python /tmp/rvion-seo-blog.09ler5/manage.py test blog.test_import_drafts.ImportBlogDraftTests.test_bodies_are_byte_identical_to_source_hashes_and_render_completely --verbosity 1
RED: 1 test, 1 failure (required neutral replacement absent).
.venv/bin/python /tmp/rvion-seo-blog.09ler5/manage.py test blog.test_import_drafts --verbosity 1
Intermediate: 27 tests, 1 failure: patch had removed a final blank line.
Restored that byte; repeated identical command: GREEN 27/27, zero skips.
```

Files at this checkpoint: article 04, blog/test_import_drafts.py, this report,
.ai/project/CURRENT_STATE.md. Commit a6da984:
`fix: reconcile teacher assessment draft with enforced exam policy`.
Rollback: revert only that scoped commit; no schema/data rollback needed.
At that checkpoint Tasks 2–3 were in progress; final results follow below.

### Tasks 2–3 — VERIFIED locally: populated language lists and approved copy

`blog.languages.indexable_list_languages()` uses the existing published query
(is_published and published_at not in the future) and requires both localized
slug and title. PostListView and StaticSitemap use that same rule. No cache,
cookie, session, analytics or database-schema policy was changed. Availability
is independent of q/tag/pagination; changes to publication are reflected on the
next request. The helper uses two bounded EXISTS queries, no per-post iteration.

| Public inventory | FA list | EN list | Blog-list alternates |
|---|---|---|---|
| Zero published translations | 200, noindex,follow, omitted from sitemap | Same | None, including no x-default |
| FA only | 200, indexable, in sitemap | 200, noindex,follow, omitted | Only FA + x-default FA |
| EN only | 200, noindex,follow, omitted | 200, indexable, in sitemap | Only EN + x-default EN |
| Both | 200, indexable, in sitemap | Same | FA, EN, x-default FA |

Every list keeps its own canonical, including an empty list. The base template
guards x-default when no alternate exists, preventing an empty href. On other
pages with existing alternates, rendered output is unchanged. No redirects,
robots.txt disallow or Search Console removal request were introduced.

What Google sees at `/en/blog/` with no English articles: BEFORE, an indexable
200 empty list advertised by sitemap and hreflang; AFTER this future release,
a 200 `noindex,follow` page, absent from sitemap and blog-list alternates. This
is a crawlable noindex request, not a guarantee of immediate deindexing. Once
an eligible English article is published, the list becomes indexable again.
Production still serves the previous implementation; no live check this phase.

Approved list copy (exact; both descriptions 119 characters):

| Language | Meta description | Lead |
|---|---|---|
| FA | راهنمای تصمیم‌گیری درباره طراحی سایت، CRM سازمانی و ارزیابی مهارت؛ هزینه‌ها، معیارها و اشتباه‌های رایج را مرور می‌کنیم. | راهنمایی برای تصمیم‌هایی که پیش از سفارش سایت، CRM یا ارزیابی مهارت باید بگیرید. |
| EN | Decision guides on website design, enterprise CRM and skills assessment: costs, selection criteria and common mistakes. | Guides for the decisions you make before ordering a website, a CRM or a skills assessment. |

Titles remain `دیدگاه‌ها | آرویون` / `Insights | Rvion`. H1, search/filter form,
article cards, empty state and pagination unchanged. Only the two `/fa/blog/`
and `/en/blog/` description entries changed in the golden fixture; direct JSON
comparison against dc4ad72 confirms every title and all other entries identical.
Whole-sitemap metadata uniqueness and non-target byte-preservation tests pass.

Exact affected outputs after an eventual release/update:

- `https://rvionai.com/fa/blog/`: approved description/lead, inventory-based
  robots/alternates (still 200; title/H1 unchanged).
- `https://rvionai.com/en/blog/`: same, English version.
- `https://rvionai.com/sitemap.xml`: includes each blog-list URL only when its
  language has eligible published content; post/detail publication rule unchanged.
- `https://rvionai.com/fa/blog/english-teacher-assessment/`: the one article-body
  sentence only AFTER an authorized draft update and owner publication; currently
  not changed by source release alone. Article title/summary/links remain unchanged.

Final test evidence (no invented browser/live/CI evidence):

```text
# Candidate built with git archive dc4ad72, then scoped files copied.
# Protected gallery diffs never copied into the candidate.
.venv/bin/python /tmp/rvion-seo-blog.09ler5/manage.py test core.tests_seo_contract.BlogListAvailabilityTests --verbosity 1
RED: 8 tests, 6 failures; unconditional sitemap languages + old copy reproduced.
# One initial combined label run from the project cwd failed test discovery:
# ImportError: candidate blog module vs project blog directory. No test executed.
# Corrected cwd, no product/test change needed:
cd /tmp/rvion-seo-blog.09ler5
/Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test core.tests_seo_contract blog --verbosity 1
GREEN: 66/66, zero skips, 11.610s.
/Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py check
0 issues.
PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps /Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test --parallel 4 --verbosity 1
FULL SUITE ONCE: 1083 tests, OK, 27 existing PostgreSQL-only skips, 57.613s.
git diff --check
Clean.
```

Python 3.9 local venv / isolated SQLite test databases. tblib is an existing
temporary test dependency for parallel traceback transport, not a repo dependency
change. Expected injected-error logs occurred inside passing failure-path tests;
missing candidate staticfiles warning is not a production static check. No test
was hidden/newly skipped. PostgreSQL, Python 3.11/3.12 and CI not run this phase.
No persistent db.sqlite3 touched, migration files created or migrations applied;
test runner only prepares/discards temporary test databases. No browser, live
HTTP, SSH, import command on permanent data, push, deploy or indexing performed.

Final files beyond Task 1: blog/languages.py, blog/views/post_list.py,
blog/templates/blog/list.html, core/sitemaps.py, core/templates/core/base.html,
core/tests_seo_contract.py (8 added tests), core/fixtures/seo_metadata_94c9c06.json,
this report and CURRENT_STATE. Local implementation commit subject:
`fix: index only populated blog languages and align approved copy` (hash in Git
and final handoff, rather than a self-referential pre-commit hash).

Protected gallery diff SHA256 still
`b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba`;
projects/static/projects/css/demo-gallery.css, projects/templates/projects/
demo_gallery.html, projects/views/projects.py untouched and uncommitted here.

### Task 4 — owner handoff / design only

UNVERIFIABLE / owner decisions, not silently converted into claims:

1. Author public name, actual authorship/reviewer role, optional bio/profile URL.
   No invented person/credential or claim of human marking/review service.
2. Real publication date for each article; real editorial modification date if
   one is exposed. A deployment/import date is not automatically an editorial date.
3. Article 01 external market-price figures and validity date; they are expressly
   not Rvion quotes. Service delivery guarantees/prices/support SLA remain unproven.
4. Article 02 recommendations on when NOT to choose custom development are kept;
   confirm editorial/commercial stance. No WordPress/template service invented.
5. Article 03 sanctions/access considerations and actual CRM delivery/security/
   independent-deployment commitments need owner's factual/commercial review.
6. Article 04 hiring predictive validity, actual savings, research interpretation
   and fairness judgments need editorial approval; code proves mechanics, not
   psychometric validation. External cited research was not re-audited here.

Byline/schema design ONLY: nullable editorial fields (e.g. author_name_fa/en,
optional public author_url, editorial_updated_at) or a nullable author relation
if multiple writers are planned. Render a Person author only with an approved
real public name; omit unsupported role/credentials/URL. Keep datePublished tied
to published_at; emit dateModified only for an actual editorial change. A future
additive migration must preserve existing articles/cover/publication fields and
default to absent values. No author model/schema/template/migration implemented.

Future production steps — NOT executed; require a new explicit release authority:

1. Review/push these scoped commits, ensure protected gallery work remains separate,
   and use the established `sudo bash /srv/arvion/ops/release.sh` release path with
   pre-release backup and health/public smoke. This task adds no migrations.
2. Before draft writes, retain an export/snapshot of current article records.
   From `/srv/arvion`, using the production service environment and interpreter:
   `python manage.py import_blog_drafts --dry-run --update`.
   Inspect counts and each planned update; do not use plain dry-run's skip output
   as evidence that --update has nothing to change.
3. Only after review: `python manage.py import_blog_drafts --update`.
   It skips ALL is_published=True records (including future scheduled ones),
   updates existing UNPUBLISHED Persian title/summary/body/tags only, and preserves
   cover, English fields, publication date and other editorial fields. Unchanged
   01–03 source bodies are not a license to overwrite separate owner edits unseen.
4. Read all four in `/admin/blog/post/`; confirm owner items above, article-04
   neutral policy wording and the four existing covers. Leave unapproved drafts
   unpublished. No OTP/counter/internal detection details added to public text.
5. Owner sets is_published and the real published_at for individually approved
   articles; inspect public pages, article/list sitemap and language alternates.
6. Request Search Console indexing only for those published public URLs; do not
   request indexing of the empty noindex English list or unpublished 404 articles.

Source rollback: revert the relevant local scoped commit(s), preserving user
gallery changes. No schema/data rollback now. After a future importer update,
source revert alone does not revert DB article text: restore only affected draft
fields from its retained pre-update export after review, not a blanket database
restore that could erase later customer activity. Release health/backup/public
checks remain future work. This local scope is VERIFIED; publication/release and
the wider SEO programme remain PARTIAL, P1-3/P4-1 DEFERRED.


## Article covers — VERIFIED (2026-10-08)

User authorized generating four covers and attaching them to the four existing
production drafts. Built-in image-generation tool used (not API/CLI fallback).
Visual inspection: coherent ivory/charcoal/orange editorial compositions,
legible main subjects, no price/score/credential claims or headline text.
Original PNGs remain under the tool's generated_images directory; final
project-bound JPEGs are stored in blog/content_drafts/covers/ and versioned.
Routine sips JPEG conversion (quality 82, width 1200) reduced transfer size;
no artistic edits or source article changes. No template/model/schema changes.

| File under blog/content_drafts/covers/ | Pixels | Bytes | Post ID |
| --- | --- | ---: | ---: |
| corporate-website-cost-1405-v1.jpg | 1200 × 627 | 125873 | 1 |
| custom-website-vs-template-v1.jpg | 1200 × 630 | 108854 | 2 |
| custom-or-ready-made-crm-v1.jpg | 1200 × 630 | 121822 | 3 |
| english-teacher-assessment-v1.jpg | 1200 × 630 | 120610 | 4 |

Snapshot before the data update:
/srv/arvion/backups/pre-article-covers-20261008-1400.dump.
pg_restore --list succeeded (catalog check, not a restore rehearsal).
Preflight found all four hero_image values empty and all posts unpublished;
no existing owner-uploaded cover was overwritten. Validated JPEG decoding,
width/height and the existing <1MB image validator before updates. Four
select_for_update rows in one atomic transaction, only hero_image saved.
Before/after comparisons of ALL other Post fields matched. Stored-file hashes
matched the uploaded assets; no article text, tags, timestamps or publication
status changed. All remain unpublished. Source runtime remains c722766.

Initial attachment attempt failed before any write: validate_image_size was
imported from blog.models, which does not export it. Corrected operational
script to import from blog.models.post; no repository code change needed.
An early public media check consequently returned 404 before attachment; the
FINAL post-attachment public HTTPS checks all passed 200, image/jpeg, valid
JPEG decoding, and exact byte/hash equality to stored files. No cache-policy
change or app restart was needed. No test suite run on production. Full tests
not repeated for an assets-only change; targeted validators/storage/field-
preservation/HTTP checks and generated-image visual inspection are the evidence.

Final media URLs:

- https://rvionai.com/media/articles/corporate-website-cost-1405-v1.jpg
- https://rvionai.com/media/articles/custom-website-vs-template-v1.jpg
- https://rvionai.com/media/articles/custom-or-ready-made-crm-v1.jpg
- https://rvionai.com/media/articles/english-teacher-assessment-v1.jpg

Publication remains BLOCKED on the prior owner/content decisions; setting a
cover does not approve or publish the content. Public media files are intended
cover illustrations and contain no customer data. Admin review at
https://rvionai.com/admin/blog/post/. No push or source deploy in this phase;
assets/status documentation committed locally. Three gallery diffs preserved.

Rollback: reset only these four hero_image pointers to their prior empty values
if explicitly authorized; keep the uploaded files for recovery and never
restore the whole database over subsequent customer activity without approval.

### Generation prompts (exact shared prefix + each subject)

```text
Use case: stylized-concept. Asset type: premium editorial blog cover for Rvion, a Persian web development and CRM brand. Generate a landscape image, 1200x630 aspect ratio, no text, letters, numbers, logos or watermark. Sophisticated tactile 3D editorial illustration, warm ivory background, charcoal/ink-blue objects, vivid orange accents (#ff6b35), restrained soft shadows, elegant studio lighting, cohesive real material detail, not a generic stock graphic. Large uncluttered central subject readable on a phone, generous safety margins; no important objects at edges.
```

**corporate-website-cost-1405**

```text
Subject: budgeting for a corporate website: an elegant upright browser-window architectural model with clean blank layout panels, beside a compact dark calculator with blank keys and a neat stack of unmarked metallic coins, connected by a subtle orange measuring line. Balanced editorial still life, tangible project planning rather than financial investment; no currency signs or price claims.
```

**custom-website-vs-template**

```text
Subject: choosing a ready-made template versus a bespoke website. Two distinct browser-window sculptures side by side: one a tidy rigid grid of matching modular ivory blocks; the other an expressive custom-fit composition of charcoal panels, curved orange shapes and carefully crafted asymmetrical modules. Equal visual dignity for both options, an orange connecting hinge suggesting a design choice, no winner or loser, no code or labels.
```

**custom-or-ready-made-crm**

```text
Subject: a customer relationship management system: a central sophisticated charcoal interface panel with clean unlabelled customer profile silhouettes and blank pipeline columns, connected to a few ivory customer cards through precise glowing orange connection paths. Clear organic organization and collaboration, physical cards suspended slightly above an ivory surface, no vendor logos, no padlock or surveillance imagery.
```

**english-teacher-assessment**

```text
Subject: thoughtful assessment of an English language teacher: a refined charcoal laptop with an abstract blank test interface, an open ivory book, understated dark headphones, and an orange check-shaped sculptural accent next to three subtle balanced skill bars. Intellectual, credible educational editorial still life, not a diploma or certified score. No alphabet, language text, flags, numeric results or claims.
```

## Article-draft production release/import — VERIFIED (2026-10-08)

Owner explicitly authorized deployment and production dry-run/import. Pushed
c56db13 + 2aaff43 + 8fb45a1 + c722766; deployed EXACT
c7227669a070ce3f70e8081d7ffdf11a67c53bc8. Previous runtime c33cf7f.
Protected gallery work remained excluded and its diff hash unchanged.
[Quality run 37784737288](https://github.com/arvinyazdani/arvion/actions/runs/37784737288)
SUCCESS on that SHA, both Python 3.11 and 3.12/PostgreSQL: checks, parallel and
shuffled full suites, source audits and syntax gates. No CI exception needed.

Server preflight: clean source, app/nginx active, 63G free, migration plan empty.
Fast-forward clean; official ops/release.sh completed commit=c722766 health=ok
at 2026-10-08T13:38:51+00:00. Snapshot BEFORE release and import:
/srv/arvion/backups/pre-release-20261008-133835.dump.
Root pg_restore --list succeeded (catalog validation, NOT a full restore test).
No migrations applied; dependency/settings checks successful, existing English
v5 and Python v3 banks unchanged, nginx valid, both services active.

Production importer used the app user/venv and sourced production environment,
not local settings. Inspected --dry-run BEFORE actual import:

```text
Would create: corporate-website-cost-1405
Would create: custom-website-vs-template
Would create: custom-or-ready-made-crm
Would create: english-teacher-assessment
DRY RUN — no database writes. Created: 4; updated: 0; skipped: 0. Unreviewed drafts only; no article was published.
```

Actual import: Created: 4; updated: 0; skipped: 0. A subsequent read-only
dry-run: Created: 0; updated: 0; skipped: 4. Server read-only assertions confirm
each body's/title's/summary's/tag set equals its repository draft, English
fields empty, is_published=False, published_at=NULL, and absent from PostSitemap.
Draft IDs 1–4 in source order, accessible to authorized owners at:

- /admin/blog/post/1/change/ — corporate-website-cost-1405.
- /admin/blog/post/2/change/ — custom-website-vs-template.
- /admin/blog/post/3/change/ — custom-or-ready-made-crm.
- /admin/blog/post/4/change/ — english-teacher-assessment.

Public HTTPS smoke from the server: 62/62 recorded pages pass 200/no redirects,
self-canonical, one H1, indexability, metadata quality/uniqueness; all prior 26
corrected outputs exact and 36 non-target outputs byte-unchanged. The draft rows
are absent from PostSitemap by direct server assertions. A separate public
sitemap/list/eight-draft-URL visibility probe could NOT run: both SSH attempts
timed out before executing its script. Therefore no production 404 assertion
is claimed (that behaviour passed locally); public draft visibility probe is
PARTIAL pending restored connectivity. Local-network smoke first failed with an
SSL handshake timeout; not counted as PASS. Same read-only checker succeeded
from the server's public HTTPS path. No CDN/cache/cookie/session changes made.
Bounded journal check since release: 0 error-marker lines; not a 15-minute
monitoring or load-test claim. Source worktree clean after import.

Evidence: /tmp/rvion-blog-release.log;
/tmp/rvion-blog-import-production-dry-run.log;
/tmp/rvion-blog-import-production.log;
/tmp/rvion-blog-live-smoke.log (local network failure);
/tmp/rvion-blog-server-public-smoke.log (62-page success); direct production
read-only record assertions and unsuccessful public-visibility SSH attempts
in this turn's tool evidence.

Publication — BLOCKED on owner/editorial decisions, NOT a deployment blocker:
no public article was published and no Search Console indexing request made.
Owner questions in original source files remain unanswered. In particular the
teacher-assessment article's human-review wording needs reconciliation with the
gift-attempt fifth-copy stop policy before publication; code tests cannot
approve that wording. Market prices, template recommendations/brand policy,
Salesforce/Zoho paragraph, assessment claims, author and dates still require
the owner's approval/review. Bodies were deliberately not edited in this release.
Use the admin links above to review; publish/index only AFTER resolving them.
P1-3/P4-1 remain DEFERRED. Overall SEO programme remains PARTIAL.

Rollback: preserve .env.production/.secrets/media/backups; inspect status before
returning committed source to c33cf7f through the reviewed release path. No schema
rollback is required. Four new draft rows should be preserved, not blindly
deleted or overwritten/restored: a full snapshot restore would also erase
subsequent unrelated customer activity and needs separate approval. No further
source release is needed for this documentation-only local checkpoint.

## Persian article drafts — VERIFIED (2026-10-08, local only)

Start: local c56db13, deployed c33cf7f. Phase A VERIFIED: language-safe lists,
detail/switch/canonical/hreflang, truthful tags, pagination and PostSitemap.
No schema/model changes. BlogPosting already uses the real language and needed
no alteration. The new whole-sitemap exception is narrowly fixture-based.
RED: 10 tests, 7 genuine failures (language availability, alternates, fake tag,
pagination); /tmp/rvion-blog-language-red.log. GREEN: blog plus complete SEO
contracts, 31 tests OK; /tmp/rvion-blog-language-green.log. An intermediate
template error (eager resolution of a missing default-filter argument) was
corrected with an explicit conditional; no failing tests were skipped.

Testing uses an isolated archive candidate /tmp/rvion-blog-candidate.uwgIs0
without the three protected gallery changes. An initial targeted discovery
invocation from the original cwd was rejected before tests ran; corrected cwd.
Only disposable Django test databases are used. Importer/render/full gates
are now verified below. No publication, persistent DB write, migration, push or
deploy. P1-3/P4-1 remain DEFERRED; analytics/sessions/cookies/cache untouched.
Protected gallery diff hash remains
b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba.

Phase A files: blog/languages.py, blog/views/post_list.py,
blog/views/post_detail.py, blog/templates/blog/list.html,
blog/templates/blog/detail.html, blog/test_language_contract.py,
core/templates/core/base.html, core/sitemaps.py, core/tests_seo_contract.py,
and the existing status records. Local commit: 2aaff43.
Rollback: revert only this phase's committed files before deployment; no DB
rollback exists or is needed. Never revert the protected gallery work.

### Phase B — importer and content rendering (local)

Four repository files under blog/content_drafts/ contain ONLY JSON-valued front
matter (slug_fa/title_fa/summary_fa/tags) and the exact Markdown after the source
`# BODY` delimiter. No source questions, research notes or editor comments were
imported. Source directory is read-only and unchanged:
/Users/rwin/Documents/claud/rvionai.com-audit/content-drafts/.
Byte comparison succeeded for all four bodies; SHA-256 expectations are pinned
in blog/test_import_drafts.py. No wording, prices, claims or sources were edited.

New files: blog/drafts.py; blog/management/__init__.py;
blog/management/commands/__init__.py;
blog/management/commands/import_blog_drafts.py; blog/test_import_drafts.py;
blog/content_drafts/01-cost-of-corporate-website.md;
blog/content_drafts/02-custom-vs-template.md;
blog/content_drafts/03-custom-vs-offtheshelf-crm.md;
blog/content_drafts/04-english-teacher-assessment.md. Existing status/report
records updated. No model, migration, renderer, admin or assessment code changed.

Importer validates the whole bundle before writing; only an explicit --update
may change an existing unpublished Persian draft's title/summary/body/tags.
Published (including future-scheduled) rows are skipped even with --update.
Existing English/editorial/publication-date/image fields are preserved.
New rows have all English fields NULL, is_published=False, published_at=NULL.
Unique slug and one atomic bundle transaction prevent partial imports. Existing
rows are locked for a real update; this is not a PostgreSQL concurrency proof.
No scheduler, automatic import or publication hook exists. --publish-style
options and front-matter publication/English keys are rejected.

Dry-run captured from a DISPOSABLE Django test database, not db.sqlite3:

```text
Would create: corporate-website-cost-1405
Would create: custom-website-vs-template
Would create: custom-or-ready-made-crm
Would create: english-teacher-assessment
DRY RUN — no database writes. Created: 4; updated: 0; skipped: 0. Unreviewed drafts only; no article was published.
Post count after dry-run: 0
```

| Draft | Title including brand | Description | h2 | h3 | Blockquotes | Internal hrefs | External hrefs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 01 corporate-website-cost-1405 | 49 | 122 | 7 | 5 | 1 | 5 | 1 |
| 02 custom-website-vs-template | 51 | 131 | 5 | 11 | 0 | 5 | 6 |
| 03 custom-or-ready-made-crm | 59 | 140 | 7 | 8 | 0 | 4 | 7 |
| 04 english-teacher-assessment | 56 | 131 | 9 | 2 | 0 | 4 | 7 |

Counts are occurrences, not distinct destinations (CRM repeats one external
href; assessment repeats its briefing link). Markdown heading/link counters
exactly match the sanitized Post.body_as_html HTML. No h1/table/img, raw &gt;,
or leaked Markdown markers; article 01's blockquote is intact. All titles <=60
and descriptions 110–140; no metadata contract violation. Existing renderer
needed no change.

Internal links retained verbatim:

- 01: /fa/services/ecommerce-platform/; /fa/services/maintenance-and-growth/;
  /fa/services/corporate-website-design/; /fa/projects/demos/; /fa/contact/.
- 02: /fa/services/corporate-website-design/; /fa/services/maintenance-and-growth/;
  /fa/services/custom-web-application/; /fa/projects/demos/; /fa/contact/.
- 03: /fa/crm/; /fa/services/maintenance-and-growth/;
  /fa/services/custom-web-application/; /fa/crm-order/.
- 04: /fa/assessments/english-placement-a1-c1/about/ (twice);
  /fa/assessments/; /fa/contact/.

The route smoke test supplies an English-exam fixture because operator-seeded
exam data is absent from a fresh test DB. An initial missing-fixture 404 was
diagnosed and corrected in TEST setup only, not by altering article links or
production routes. All internal targets return 200 with their normal fixtures.
External href preservation is verified, not external availability or accuracy.
Test-only publication of all four articles exercises every inherited whole-
sitemap contract; the fa-only hreflang exception is explicitly limited to these
four named slugs plus the phase-A fixture. No missing translation is fabricated.

### Phase C — owner handoff / publication decisions

UNREVIEWED DRAFTS. Neither this work nor the tests constitute editorial,
financial, legal or educational approval. Nothing was published or written to
any persistent database. These files are ready for a FUTURE authorized release,
not deployed in this phase. No publishing command/flag is provided.

After that future deployment, owner runs in the release's configured Django
environment (production settings/venv/environment, not a bare local default):

1. `python manage.py import_blog_drafts --dry-run` — inspect create/skip counts.
2. `python manage.py import_blog_drafts` — create the four unpublished drafts.
   Existing slugs are skipped; inspect them rather than blindly adding --update.
3. In /admin/ open each Post. Review title, summary, exact body, tags and sources.
   Author name is NOT modelled; no author/schema byline was invented here.
4. Only after approving its content set that post's is_published and published_at
   explicitly. A future date delays public visibility until that time. Confirm
   the FA detail/list/sitemap and the English-list language-switch fallback.
5. After the page is public request indexing of its exact FA URL in Google
   Search Console URL Inspection. Do not request indexing while it is a draft.

Owner decisions needed BEFORE publication:

- Author byline: approve actual identity and whether bilingual byline fields or
  an author relation is wanted. That needs a separately authorized model change
  and migration; design consideration ONLY, not implemented.
- Publication dates/order/timezone for the four articles; no automatic dates.
- CRM sanctions paragraph: verify current vendor terms and wording, including
  Salesforce/Zoho claims. No legal/compliance validity was established here.
- Teacher-assessment claims: educational review, actual competencies measured,
  and consistency with the CURRENT copy-monitoring policy (gift attempt can be
  stopped at the fifth copy event). Source wording about human review must not
  misrepresent that behaviour. No wording change without owner review.
- Cost/article product-policy claims and cited third-party numbers/statistics
  also need editorial fact-checking; body preservation does not endorse them.

Rollback for B: before importing, revert the scoped importer/content commit
only. After any future import, do NOT delete Posts automatically: preserve
editorial edits, inspect ownership/publication state and obtain data-change
authorization. No migration rollback required. Phase-A route safety can be
reverted separately only after considering any subsequently published fa-only
articles. Protected gallery work is never part of rollback.

Phase B targeted GREEN: blog + core.tests_seo_contract, 58/58 tests OK,
/tmp/rvion-blog-import-green.log. Covers import idempotency, explicit update,
scheduled/published preservation, all publication flags, front-matter allowlist,
zero-write dry-run, transaction rollback after an injected tag failure,
unpublished visibility and test-published whole-sitemap contracts. Check zero
issues; makemigrations --check --dry-run: No changes detected, with the check's
database explicitly set to :memory:. git diff --check clean. Local Python 3.9 /
SQLite evidence, not a new CI/Python 3.11/3.12/PostgreSQL validation.

### Final verification and commit checkpoint — VERIFIED locally

- Phase A commit: 2aaff43, language-safe public article contracts.
- Phase B commit: 8fb45a1, four unreviewed source-identical drafts and importer.
- Phase C: this final documentation-only checkpoint; no further product change.
- Full suite executed EXACTLY ONCE at the end, on the isolated clean candidate:
  `python manage.py test --parallel 4 --verbosity 1` — 1075 tests in 98.980s,
  OK (27 existing PostgreSQL-only tests skipped on SQLite), exit 0.
  /tmp/rvion-blog-full.log. 1048 executed tests passed, not 1075 executed tests.
  Temporary tblib from prior QA support was used for parallel diagnostics; no
  dependency/project configuration change. Logged simulated exceptions belong
  to intentional fault-injection tests, not new test failures. An absent
  candidate staticfiles-directory warning is expected; no visual/live-page or
  static-asset deployment verification is claimed.
- Candidate and repository: all 16 changed implementation/test/content file
  byte comparisons match. No protected gallery file was included in the
  candidate or these commits. Final protected diff hash equals the start hash.
- Final source-file hashes equal the initial hashes and all four repository
  bodies equal the exact source BODY bytes. No external source file edited.
- Final git diff --check clean; no model/schema/migration changes. All database
  writes/publication fixtures existed only inside disposable Django test DBs,
  which were destroyed afterward. No persistent import was run.
- No push, deployment, CI run, production migration, author-field addition,
  live publication or Search Console request. Deployed version remains the
  previously recorded c33cf7f; no server action in this phase.
- No technical BLOCKED/P0/P1 found within this bounded phase. Article content
  remains unreviewed; owner decisions above are prerequisites to publication,
  not silently waived by passing code tests. Overall SEO programme remains
  PARTIAL and P1-3/P4-1 remain DEFERRED.

## Metadata production release — VERIFIED (2026-10-08)

Owner explicitly requested deployment. Candidate c33cf7f (implementation e70cdd8)
was pushed to main; protected gallery diffs remain local and excluded.
Previous production source 94c9c06. Preflight worktree clean, health OK,
migration plan empty, available disk 63G. [Quality run 37775751122](https://github.com/arvinyazdani/arvion/actions/runs/37775751122)
completed SUCCESS for both Python 3.11 and 3.12 with PostgreSQL, parallel and
shuffled suites and remaining quality gates, on exact SHA
c33cf7f5ae52a15246bda145693b460654c8e284.

First source fast-forward hit root-owned directories core/templatetags and
docs/seo. HEAD remained 94c9c06 with partial checkout changes made by this
attempt. Fixed ownership ONLY for those two directories and the report file,
archived that attempt to backups/metadata-interrupted-merge-c33cf7f.tar.gz
(plus its new public fixture JSON), restored ONLY the known attempt-created
tracked changes to HEAD, preserved the generated fixture in backups, checked
the source clean and retried fast-forward. No user/customer files were reset.
The first attempt never ran release/restart; the retry succeeded.

Official ops/release.sh completed commit=c33cf7f health=ok. Snapshot:
/srv/arvion/backups/pre-release-20261008-122634.dump. Root pg_restore --list
succeeded (catalog validation, not a full restoration test). An initial attempt
as postgres lacked permission to read the owner-restricted dump; permissions
were preserved and validation rerun as root, not loosened.
Dependencies and deploy checks passed; no migrations to apply; English v5 and
Python v3 banks already existed, no question records changed. Static assets
unchanged, nginx valid, app/nginx active, source worktree clean, local health OK.
Bounded post-release journal error-marker count 0; not 15-minute monitoring.

Public read-only HTTPS smoke PASSED for all 62 recorded sitemap paths: 200/no
redirect, self-canonical, one H1/indexable, global quality/uniqueness. All 26
target title/descriptions exactly match the AFTER table below; all 36 non-target
values match the 94c9c06 baseline as UTF-8 bytes, including the 11 short pages.
The live /sitemap.xml inventory was separately asserted equal to those 62 paths.
No account, payment, form, contract, SMS or notification action was performed.
Evidence: /tmp/rvion-metadata-release.log (permission failure),
/tmp/rvion-metadata-release-retry.log (success), /tmp/rvion-metadata-live-smoke.log.
Protected local gallery diff hash unchanged:
b60bd5ef5b115893aecd5fe3ca330e72cedccc4c2bd48a8b85891d9e8c665aba.
P1-3/P4-1 remain DEFERRED. Overall SEO programme remains PARTIAL.

Rollback: inspect server status, preserve .env.production/.secrets/media/backups,
return ONLY clean committed source to 94c9c06 and restart the application through
the reviewed release path. This metadata-only release needs no database rollback.
The deployment record is a subsequent local documentation checkpoint, not a
second production release; runtime remains c33cf7f.

## Generated-metadata correction — VERIFIED (local), owner option A (2026-10-08)

Owner decision: description length 90–155 applies ONLY to the 26 requested
demo-preview/exam-briefing instances. Punctuation, middle ellipsis, adjacent
repetition, title <=60 and uniqueness remain whole-sitemap contracts.
P1-3/P4-1 remain DEFERRED: no analytics, sessions, cookies or caching changes.

Baseline: deployed 94c9c06; local start 9fb815f. Used primary-workflow QUICK_FIX
and engineering:debug (reproduce/isolate/fix/regression), single primary agent.
No push, deploy or migration against any persistent database.

### Scope and implementation

- Only the title/description blocks and tag-library imports in
  projects/templates/projects/demo_preview.html and
  assessments/templates/assessments/briefing.html changed.
- New core/templatetags/seo_metadata.py strips HTML/whitespace and terminal
  punctuation from source parts BEFORE joining. It selects whole candidate
  compositions, never truncates words/sentences, and preserves stored data.
- Titles first discard the live-sample qualifier if necessary, then shorten
  category labels; website/category repetition is removed before composition.
- Demo descriptions use the existing complete tagline and enquiry instruction
  instead of appending the longer fit phrase. Briefings fall back to their
  existing monitoring/answer-review topic rather than slicing the exam overview.
  No new capabilities/claims introduced; body copy/visible names remain unchanged.
- Actual 26 outputs: title length <=60; description length 91–119, all unique.

### Red / green and preservation evidence

- Previous global-scope red evidence (119 failures) remains historical below.
- Owner-adjusted RED, BEFORE product edits: 2 tests in 3.506s, 95 failing quality
  subtests. The other test (all 36 non-target production pages unchanged) passed.
  Command: .venv/bin/python manage.py test
  core.tests_seo_contract.WholeSitemapContractTests.test_generated_metadata_quality_entire_sitemap
  core.tests_seo_contract.WholeSitemapContractTests.test_every_non_target_live_page_metadata_is_byte_unchanged
  --verbosity 1. Log: /tmp/rvion-seo-metadata-option-a-red.log.
- GREEN: core.tests_seo_contract, 18 tests, OK (9.109s; repeated targeted run
  9.347s also OK; final target-inventory assertion covered by the full gate). Log:
  /tmp/rvion-seo-metadata-option-a-green.log.
- check: zero issues; makemigrations --check --dry-run: No changes detected.
  This is a schema-drift diagnostic, NOT a migration execution.
- Full suite ONCE at the final gate: 1039 tests in 101.988s, OK, 27 PostgreSQL-only
  skips on SQLite (1012 executed/passed), exit 0. Command:
  `PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps /Users/rwin/Desktop/rwin-tech/arvion/.venv/bin/python manage.py test --parallel 4 --verbosity 1`
  from the isolated candidate archive. Log: /tmp/rvion-seo-metadata-option-a-full.log.
  The existing test-only tblib dependency enables parallel failure reporting;
  no project dependency changed. Logged injected-provider errors belong to
  expected negative-path tests, not additional failing tests.
- New immutable fixture core/fixtures/seo_metadata_94c9c06.json contains the 62
  public title/description values from the owner's 2026-10-07 live audit.
  Every non-target path is present and compared as UTF-8 bytes without test-side
  whitespace normalization. All 36 match, including the 11 short About/service
  descriptions. The live verifier originally decoded HTML entities/normalized
  whitespace; the RED and GREEN preservation tests confirmed those recorded
  values equal the actual rendered non-target strings byte for byte.
- For every row below, BEFORE was independently re-rendered from the exact
  94c9c06 template with the same public catalogue data and matched the live
  snapshot exactly. AFTER is actual Django response metadata, not a hand-written
  proposal.
- A pre-existing breadcrumb assertion failed when real Python exam catalogue
  wording replaced the fake slug title: "&" is correctly HTML-escaped. Fixed
  the test to look for escape(item['name']), not unescaped raw text in HTML.
  This corrects test representation only; schema/template behaviour unchanged.
- Tests cover terminal punctuation/HTML, whole shorter-topic fallback, no source
  mutation, all 26 target paths visited, whole-sitemap quality/uniqueness and the
  non-target byte-preservation assertion.
- No visual/layout change: response-head checks are the relevant evidence; no
  new mobile screenshot, PostgreSQL/concurrency, CI or production claim.

### Protected dirty work and reproducible test boundary

The three user-owned gallery files were not edited, staged or committed:
projects/static/projects/css/demo-gallery.css,
projects/templates/projects/demo_gallery.html, projects/views/projects.py.
The pre-existing dirty gallery template changes its OWN two metadata entries,
so testing the raw working tree would legitimately fail deployed-preservation
for those entries. Tests instead ran on a disposable HEAD archive plus ONLY
this phase's candidate files, /tmp/rvion-metadata-candidate.jDvCIL.
The archive excludes all three protected diffs. This is not a test exception:
the preservation assertion remains intact and the tested candidate matches what
will be committed. Temporary test databases only; no project db.sqlite3/server
database touched.

### Exact 26-row before/after table

| URL | Title before | Title after | Description before | Description after |
| --- | --- | --- | --- | --- |
| https://rvionai.com/fa/projects/demos/roshna-clinic/ | طراحی سایت کلینیک با نمونه زنده کلینیک و نوبت‌دهی \| آرویون | طراحی سایت کلینیک با نمونه زنده کلینیک و نوبت‌دهی \| آرویون | کلینیک و نوبت‌دهی؛ نوبت‌دهی، معرفی پزشک و محتوای آگاه‌کننده.. برای کلینیک با معرفی پزشک، محتوای آگاه‌کننده و نوبت‌دهی؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | کلینیک و نوبت‌دهی؛ نوبت‌دهی، معرفی پزشک و محتوای آگاه‌کننده. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/parsa-advisory/ | طراحی سایت وب‌سایت شرکتی با نمونه زنده شرکت خدمات حرفه‌ای \| آرویون | طراحی سایت شرکتی با نمونه زنده شرکت خدمات حرفه‌ای \| آرویون | شرکت خدمات حرفه‌ای؛ اعتمادسازی، خدمات و مسیر ساده تماس.. برای شرکت خدماتی که اعتماد، خدمات و تماس روشن اولویت دارد؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | شرکت خدمات حرفه‌ای؛ اعتمادسازی، خدمات و مسیر ساده تماس. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/northline-group/ | طراحی سایت وب‌سایت شرکتی با نمونه زنده برند شرکتی \| آرویون | طراحی سایت شرکتی با نمونه زنده برند شرکتی \| آرویون | برند شرکتی؛ هویت جسور برای معرفی تیم و راهکارها.. برای شرکت خدماتی که اعتماد، خدمات و تماس روشن اولویت دارد؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | برند شرکتی؛ هویت جسور برای معرفی تیم و راهکارها. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/nava-market/ | طراحی سایت فروشگاه اینترنتی با نمونه زنده فروشگاه مینیمال \| آرویون | طراحی سایت فروشگاه اینترنتی: فروشگاه مینیمال \| آرویون | فروشگاه مینیمال؛ فروش آرام و متمرکز روی محصول.. برای فروش مستقیم محصول با مسیر خرید کوتاه و واضح؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | فروشگاه مینیمال؛ فروش آرام و متمرکز روی محصول. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/orbit-shop/ | طراحی سایت فروشگاه اینترنتی با نمونه زنده فروشگاه پرانرژی \| آرویون | طراحی سایت فروشگاه اینترنتی: فروشگاه پرانرژی \| آرویون | فروشگاه پرانرژی؛ کاتالوگ سریع برای محصول‌های شاخص.. برای فروش مستقیم محصول با مسیر خرید کوتاه و واضح؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | فروشگاه پرانرژی؛ کاتالوگ سریع برای محصول‌های شاخص. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/ariana-academy/ | طراحی سایت آموزش با نمونه زنده آکادمی و وبینار \| آرویون | طراحی سایت آموزش با نمونه زنده آکادمی و وبینار \| آرویون | آکادمی و وبینار؛ دوره، مسیر یادگیری و تجربه عضویت.. برای آکادمی، دوره آنلاین یا مجموعه برگزارکننده وبینار؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | آکادمی و وبینار؛ دوره، مسیر یادگیری و تجربه عضویت. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/sarvin-atelier/ | طراحی سایت طلافروشی و جواهرات با نمونه زنده گالری طلا و جواهر \| آرویون | طراحی سایت طلافروشی و جواهرات: گالری طلا و جواهر \| آرویون | گالری طلا و جواهر؛ هر قطعه، داستانی برای ماندن.. برای طلافروشی و برندی که اصالت، ساخت سفارشی و مشاوره را آنلاین ارائه می‌کند؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | گالری طلا و جواهر؛ هر قطعه، داستانی برای ماندن. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/linea-studio/ | طراحی سایت پورتفولیو با نمونه زنده استودیوی خلاق \| آرویون | طراحی سایت پورتفولیو با نمونه زنده استودیوی خلاق \| آرویون | استودیوی خلاق؛ نمونه‌کارهایی که داستان هر پروژه را تعریف می‌کنند.. برای متخصص یا استودیویی که باید کیفیت کار را سریع اثبات کند؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | استودیوی خلاق؛ نمونه‌کارهایی که داستان هر پروژه را تعریف می‌کنند. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/atlas-profile/ | طراحی سایت پورتفولیو با نمونه زنده پورتفولیو شخصی \| آرویون | طراحی سایت پورتفولیو با نمونه زنده پورتفولیو شخصی \| آرویون | پورتفولیو شخصی؛ معرفی شفاف مهارت، تجربه و راه تماس.. برای متخصص یا استودیویی که باید کیفیت کار را سریع اثبات کند؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | پورتفولیو شخصی؛ معرفی شفاف مهارت، تجربه و راه تماس. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/saffron-table/ | طراحی سایت رستوران و کافه با نمونه زنده منوی رستوران \| آرویون | طراحی سایت رستوران و کافه: منوی رستوران \| آرویون | منوی رستوران؛ منوی دیجیتال با حس گرم و اشتهابرانگیز.. برای رستوران و کافه‌ای که منو، رویداد و رزرو را یکجا می‌خواهد؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | منوی رستوران؛ منوی دیجیتال با حس گرم و اشتهابرانگیز. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/fa/projects/demos/mora-cafe/ | طراحی سایت رستوران و کافه با نمونه زنده کافه و رزرو \| آرویون | طراحی سایت رستوران و کافه با نمونه زنده کافه و رزرو \| آرویون | کافه و رزرو؛ یک تجربه صمیمی برای منو، رویداد و رزرو.. برای رستوران و کافه‌ای که منو، رویداد و رزرو را یکجا می‌خواهد؛ نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. | کافه و رزرو؛ یک تجربه صمیمی برای منو، رویداد و رزرو. نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید. |
| https://rvionai.com/en/projects/demos/roshna-clinic/ | Clinic website design: live Clinic and booking sample \| Rvion | Clinic website design: Clinic and booking \| Rvion | Clinic and booking: Bookings, practitioners and helpful content.. For clinics combining practitioner profiles, guidance and appointment booking. Customise this sample and send a design enquiry. | Clinic and booking: Bookings, practitioners and helpful content. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/parsa-advisory/ | Corporate website website design: live Professional services sample \| Rvion | Corporate website design: Professional services \| Rvion | Professional services: Trust, services and a direct contact path.. For service companies prioritising trust, offers and a clear contact path. Customise this sample and send a design enquiry. | Professional services: Trust, services and a direct contact path. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/northline-group/ | Corporate website website design: live Corporate brand sample \| Rvion | Corporate website design: Corporate brand \| Rvion | Corporate brand: A bold identity for teams and solutions.. For service companies prioritising trust, offers and a clear contact path. Customise this sample and send a design enquiry. | Corporate brand: A bold identity for teams and solutions. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/nava-market/ | E-commerce website design: live Minimal storefront sample \| Rvion | E-commerce website design: Minimal storefront \| Rvion | Minimal storefront: A calm product-first storefront.. For direct product sales with a short, clear purchase path. Customise this sample and send a design enquiry. | Minimal storefront: A calm product-first storefront. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/orbit-shop/ | E-commerce website design: live Bold commerce sample \| Rvion | E-commerce website design: live Bold commerce sample \| Rvion | Bold commerce: A fast catalogue for standout products.. For direct product sales with a short, clear purchase path. Customise this sample and send a design enquiry. | Bold commerce: A fast catalogue for standout products. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/ariana-academy/ | Education & webinar website design: live Academy and webinars sample \| Rvion | Education website design: Academy and webinars \| Rvion | Academy and webinars: Courses, learning journeys and membership.. For academies, online courses and webinar-led education. Customise this sample and send a design enquiry. | Academy and webinars: Courses, learning journeys and membership. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/sarvin-atelier/ | Jewellery boutique website design: live Jewellery atelier sample \| Rvion | Jewellery boutique website design: Jewellery atelier \| Rvion | Jewellery atelier: A keepsake with a story of its own.. For jewellery brands presenting authenticity, custom craft and consultation online. Customise this sample and send a design enquiry. | Jewellery atelier: A keepsake with a story of its own. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/linea-studio/ | Portfolio website design: live Creative studio sample \| Rvion | Portfolio website design: Creative studio \| Rvion | Creative studio: Work that tells the story behind every project.. For experts or studios that need to prove the quality of their work quickly. Customise this sample and send a design enquiry. | Creative studio: Work that tells the story behind every project. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/atlas-profile/ | Portfolio website design: live Personal portfolio sample \| Rvion | Portfolio website design: Personal portfolio \| Rvion | Personal portfolio: A clear home for expertise, work and contact.. For experts or studios that need to prove the quality of their work quickly. Customise this sample and send a design enquiry. | Personal portfolio: A clear home for expertise, work and contact. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/saffron-table/ | Restaurant & cafe website design: live Restaurant menu sample \| Rvion | Restaurant & cafe website design: Restaurant menu \| Rvion | Restaurant menu: A warm, appetite-led digital menu.. For restaurants and cafés combining menus, events and reservations. Customise this sample and send a design enquiry. | Restaurant menu: A warm, appetite-led digital menu. Customise this sample and send a design enquiry. |
| https://rvionai.com/en/projects/demos/mora-cafe/ | Restaurant & cafe website design: live Cafe and reservations sample \| Rvion | Restaurant website design: Cafe and reservations \| Rvion | Cafe and reservations: A friendly home for menus, events and bookings.. For restaurants and cafés combining menus, events and reservations. Customise this sample and send a design enquiry. | Cafe and reservations: A friendly home for menus, events and bookings. Customise this sample and send a design enquiry. |
| https://rvionai.com/fa/assessments/english-placement-a1-c1/about/ | پیش از شروع ارزیابی پیشرفته زبان انگلیسی مدرسان \| آرویون | پیش از شروع ارزیابی پیشرفته زبان انگلیسی مدرسان \| آرویون | راهنمای ارزیابی پیشرفته زبان انگلیسی مدرسان: غربالگری سطح بالای گرامر، دقت واژگانی، خواندن انتقادی، شنیدار، ویرایش و تحلیل آموزشی برای انتخاب مدرس.؛ آشنایی با پایش آزمون و بررسی پاسخ‌ها پیش از شروع. | راهنمای ارزیابی پیشرفته زبان انگلیسی مدرسان. پیش از شروع با پایش آزمون و بررسی پاسخ‌ها آشنا شوید. |
| https://rvionai.com/fa/assessments/python-django-professional/about/ | پیش از شروع ارزیابی تخصصی Python و Django \| آرویون | پیش از شروع ارزیابی تخصصی Python و Django \| آرویون | راهنمای ارزیابی تخصصی Python و Django: سنجش عملی Python، حل مسئله، دیتابیس، تست، امنیت و استقرار پروژه‌های Django.؛ آشنایی با پایش آزمون و بررسی پاسخ‌ها پیش از شروع. | راهنمای ارزیابی تخصصی Python و Django. پیش از شروع با پایش آزمون و بررسی پاسخ‌ها آشنا شوید. |
| https://rvionai.com/en/assessments/english-placement-a1-c1/about/ | Before you start Advanced English Teacher Assessment \| Rvion | Before you start Advanced English Teacher Assessment \| Rvion | Guide to Advanced English Teacher Assessment: Advanced screening of grammar, lexical precision, critical reading, listening, editing, and pedagogical analysis for te…. Learn about integrity monitoring and answer review before starting. | Guide to Advanced English Teacher Assessment. Learn about integrity monitoring and answer review before starting. |
| https://rvionai.com/en/assessments/python-django-professional/about/ | Before you start Professional Python & Django Assessment \| Rvion | Guide to Professional Python & Django Assessment \| Rvion | Guide to Professional Python & Django Assessment: A practical assessment of Python, problem solving, databases, testing, security, and Django deployment.. Learn about integrity monitoring and answer review before starting. | Guide to Professional Python & Django Assessment. Learn about integrity monitoring and answer review before starting. |

### Exact changed-HTML URL list

Only the following 26 production sitemap URLs change title and/or description;
the 36 other production sitemap URLs are unchanged:
- https://rvionai.com/fa/projects/demos/roshna-clinic/
- https://rvionai.com/fa/projects/demos/parsa-advisory/
- https://rvionai.com/fa/projects/demos/northline-group/
- https://rvionai.com/fa/projects/demos/nava-market/
- https://rvionai.com/fa/projects/demos/orbit-shop/
- https://rvionai.com/fa/projects/demos/ariana-academy/
- https://rvionai.com/fa/projects/demos/sarvin-atelier/
- https://rvionai.com/fa/projects/demos/linea-studio/
- https://rvionai.com/fa/projects/demos/atlas-profile/
- https://rvionai.com/fa/projects/demos/saffron-table/
- https://rvionai.com/fa/projects/demos/mora-cafe/
- https://rvionai.com/en/projects/demos/roshna-clinic/
- https://rvionai.com/en/projects/demos/parsa-advisory/
- https://rvionai.com/en/projects/demos/northline-group/
- https://rvionai.com/en/projects/demos/nava-market/
- https://rvionai.com/en/projects/demos/orbit-shop/
- https://rvionai.com/en/projects/demos/ariana-academy/
- https://rvionai.com/en/projects/demos/sarvin-atelier/
- https://rvionai.com/en/projects/demos/linea-studio/
- https://rvionai.com/en/projects/demos/atlas-profile/
- https://rvionai.com/en/projects/demos/saffron-table/
- https://rvionai.com/en/projects/demos/mora-cafe/
- https://rvionai.com/fa/assessments/english-placement-a1-c1/about/
- https://rvionai.com/fa/assessments/python-django-professional/about/
- https://rvionai.com/en/assessments/english-placement-a1-c1/about/
- https://rvionai.com/en/assessments/python-django-professional/about/

### Files / local commit / rollback

Files: the two templates above; core/templatetags/seo_metadata.py;
core/tests_seo_contract.py; core/fixtures/seo_metadata_94c9c06.json;
docs/seo/SEO_PHASE_REPORT.md; .ai/project/CURRENT_STATE.md; PROJECT_STATUS.md.
Local implementation commit: e70cdd8
`fix(seo): compose bounded demo and briefing metadata without truncation`
(parent 9fb815f). All five implementation/test/fixture files exactly matched the
tested candidate at commit time. This report and the two living checkpoints are
recorded in a separate local documentation commit referencing e70cdd8.
Rollback: revert this phase's scoped local implementation commit; no database
rollback required. Deployed 94c9c06 is unaffected. Protected gallery work must
remain excluded from any future release.
Remaining risk: no production/CI evidence for this unpushed change; constraints
validated against current catalogue/sitemap, not a guarantee for arbitrary future
unbounded copy. No known P0/P1 remains in this bounded local phase. Future
release requires explicit authorization; the wider SEO programme remains PARTIAL.


## Generated-metadata correction — BLOCKED on scope conflict (2026-10-07)

Starting local HEAD b45c2a8; deployed source remains 94c9c06. Explicit boundary:
fix demo previews/exam briefings only, but assert description length 90–155 on
EVERY sitemap URL. Both cannot pass simultaneously without owner clarification.
Saved live evidence from the owner's just-run verify_live.py:
/Users/rwin/Documents/claud/rvionai.com-audit/live_check_result.json (62 URLs).
Eleven other public descriptions fail the proposed minimum before this work:

| Public path | Existing description length |
| --- | ---: |
| /fa/about/ | 73 |
| /en/about/ | 73 |
| /fa/services/digital-product-consulting/ | 65 |
| /fa/services/corporate-website-design/ | 70 |
| /fa/services/custom-web-application/ | 80 |
| /fa/services/ecommerce-platform/ | 77 |
| /fa/services/maintenance-and-growth/ | 66 |
| /en/services/digital-product-consulting/ | 83 |
| /en/services/custom-web-application/ | 86 |
| /en/services/ecommerce-platform/ | 83 |
| /en/services/maintenance-and-growth/ | 89 |

Composition causes confirmed in source: demo_preview.html joins punctuated
tagline with a new period, prepends redundant category wording and long qualifier;
briefing.html adds a new separator after truncatechars:120, potentially ending
inside a sentence/adding an ellipsis. No production composition fix applied yet.

Red test added, unchanged assertions exactly covering the requested global scope:
core.tests_seo_contract.WholeSitemapContractTests.test_generated_metadata_quality_entire_sitemap.
Command: `.venv/bin/python manage.py test core.tests_seo_contract.WholeSitemapContractTests.test_generated_metadata_quality_entire_sitemap --verbosity 1`.
Result: 1 test, 119 failed subtests, 3.143s, exit 1; raw evidence
/tmp/rvion-seo-metadata-red.log. Failures include the two About pages and real
seeded Service descriptions, not only artificial fixtures or affected demos.
Additional fixture-length failures are not claimed as production defects.
The test extension remains uncommitted intentionally; no failing test committed,
removed, skipped or weakened. Report/state checkpoint alone is committed.
No green/full suite, before/after 26-row table, or changed-HTML URL list yet:
implementation has not started because the mandatory acceptance conflicts with
the explicit no-other-page-metadata boundary. Existing deployed metadata unchanged.
All three protected dirty gallery files preserved. No push/deploy/migration,
analytics/session/cookie/cache changes or customer writes.

Owner decision needed (recommended A):
A. Enforce 90–155 only for the 26 requested demo/exam metadata instances;
keep punctuation/repetition/title-size/uniqueness checks over the whole sitemap,
and assert all other metadata is unchanged. This changes the requested length
test scope only after explicit owner approval; it is NOT silently applied.
B. Keep the exact global 90–155 criterion and explicitly authorize composition
changes for the 11 About/service descriptions as well; use existing copy only.
Rollback: no product/data change. Remove only this agent's uncommitted test hunk
if the task is withdrawn; retain the red evidence and decision record.

Date: 2026-10-07. Overall status: **PARTIAL — independent SEO work resumed**.
Single primary agent; self-review, not independent review.
Source request: `/Users/rwin/Documents/claud/rvionai.com-audit/AGENT-PROMPT.md`.
Baseline: `6977b30`; production runtime now `94c9c06` (release evidence below).
Implementation commit: `4d22cc1` (`fix(seo): publish public assessment briefings in sitemap`).
This SHA applies to P1-1 and the partial P1-2/diagnostic evidence below. The report
hash finalization is a separate documentation-only checkpoint, not further implementation.

## Production release — VERIFIED (2026-10-07)

Explicit user instruction: «دپلوی کن». Committed source only was pushed;
three unrelated dirty gallery files remain local and uncommitted. Source release
94c9c0669b5abdc19fc4d7b0c0d885ccee7d5a3e, previous production 63abbcd.
[Quality run 37613465630](https://github.com/arvinyazdani/arvion/actions/runs/37613465630)
completed success for Python 3.11 and 3.12 on PostgreSQL, including parallel and
shuffled suites, dependency/migration drift, bank audit and JS/shell syntax gates.
Server worktree was clean before fast-forward; no reset/stash/untracked cleanup.
Real active Service/DemoTemplate link-target preflight found zero missing targets.
Production migrate --plan was empty; release migrate reported no migrations.

Official ops/release.sh completed commit=94c9c06 health=ok. Snapshot:
/srv/arvion/backups/pre-release-20261007-112920.dump. `pg_restore --list` exited
success; this validates the archive catalog, not a full restoration rehearsal.
Dependencies/check --deploy/nginx validation passed. Existing assessment bank
versions unchanged, static assets collected, application/nginx active. Local
health returned status=ok; recent journal error-marker count was 0 during this
bounded check, not a claim of long-running/15-minute monitoring or zero future errors.

Public HTTPS smoke: 36 FA/EN pages (home, service list, CRM, blog list, exams,
contact, five service details, seven linked demo previews) all 200 with no redirect,
indexable and correct Organization telephone. New related anchors present; FA
home emits three font preloads. Production 390px browser inspected service links:
all fit, scrollWidth=390, visible button boundaries. Existing notification prompt
dismissed without activating/sending a test; no customer form submitted.
Browser test tab closed and viewport reset. Anonymous HTTP smoke separately
checks pages without the browser's existing staff login.
Evidence logs: /tmp/rvion-seo-deploy.log, /tmp/rvion-seo-production-smoke.log.
No performance/ranking claim follows from release or HTTP status checks.

Rollback boundary: before source rollback inspect production status, preserve
.env.production/.secrets/media/backups; switch only committed source back to
63abbcd, collectstatic and restart/check services. No DB restoration/reverse
migration required by this schema-free release; never restore over customer
data without a separate recovery decision. Source backup commit and validated
database snapshot retained. SEO programme overall remains PARTIAL; deferred
owner decisions, copy proposals and startup main-thread work remain unresolved.
This release evidence checkpoint is documentation-only and local, after the
tested/pushed/deployed source SHA above; it does not change deployed runtime.

## Scope and stop boundary

The requested four-phase programme is **not complete**. The initial checkpoint below
stopped at P1-3; AGENT-PROMPT-2 now authorizes independent steps with OWNER DECISION
**DEFERRED**. Analytics, LanguageViewMixin session behavior and caching stay unchanged.
Current continuation evidence is recorded at the end of this report.

Historical first checkpoint: P1-1 is implemented and
locally verified. P1-2 has an exam-only contract, not the requested entire-sitemap
contract. Investigation of P1-3 exposed a second intentional session writer that
the prompt's proposed LanguageViewMixin edit cannot resolve. Per the supplied
stop rule and project business/privacy safeguards, implementation stops here.

The prompt's statement that SSH deployment is blocked is outdated: the prior
release succeeded. This task nevertheless explicitly prohibits push, deploy,
production migration and messaging, and none was performed for this SEO work.

## Evidence re-verified

### E1: sitemap was advertising an account-gated price page

Before: `ExamSitemap.location()` returned `assessments:detail`.
Live anonymous GET of `/fa/assessments/english-placement-a1-c1/` returned:

```http
HTTP/2 302
Location: /fa/account/register/?next=/fa/assessments/english-placement-a1-c1/
Vary: Cookie
X-Cache: BYPASS
Set-Cookie: sessionid=[REDACTED]; HttpOnly; Secure; SameSite=Lax
```

The new tests were run **before** the correction: 3 tests ran, with 3 failure
records (the public-URL test failed for both languages at 302 != 200, plus the
URL-set test). This is real red-before-green evidence, not a hypothetical claim.

After (local test database only): sitemap locations use `assessments:briefing`:

```text
https://rvionai.com/fa/assessments/seo-fixture/about/
https://rvionai.com/en/assessments/seo-fixture/about/
```

Both return 200, exactly one H1, indexable robots metadata and self canonical.
Each has fa/en/x-default alternates; inactive exams remain excluded and their
briefing remains 404. Lastmod still comes from Exam.updated_at. Anonymous access
to the price page remains 302, preserving the existing access boundary.

Representative local rendered metadata for the Persian fixture:

```html
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://rvionai.com/fa/assessments/seo-fixture/about/">
<link rel="alternate" hreflang="fa" href="https://rvionai.com/fa/assessments/seo-fixture/about/">
<link rel="alternate" hreflang="en" href="https://rvionai.com/en/assessments/seo-fixture/about/">
<link rel="alternate" hreflang="x-default" href="https://rvionai.com/fa/assessments/seo-fixture/about/">
```

### E2: two independent session writers, not one

Live anonymous GET `/fa/` (before SEO changes) returned 200 with
`Set-Cookie: sessionid=[REDACTED]`, `Vary: Cookie`, `X-Cache: BYPASS`.
There is **no cookieless after result**: neither the language mixin nor analytics
has been changed in this checkpoint. Do not describe cookie/cache work as fixed.

`core/views/lang.py` always assigns session['lang']. However,
`traffic/middleware.py::_record` also calls session.create() when a public visitor
has no session key, then uses a hash of that key for unique/online visitor records.
The diagnostic test replaces the home view with a plain HttpResponse (no language
write, no template or CSRF); analytics alone still creates one Session, a session
cookie and a unique visitor. Therefore even a correct conditional language write
cannot satisfy P1-3's no-session-cookie acceptance criterion.

Readers/writers reviewed: core language mixin/switch_language, accounts email
verification and dashboard, assessments._request_language, leads demo continuation,
Locale/Session middleware ordering, SINGLE_SESSION_ENFORCED middleware, traffic
analytics and its existing tests/privacy notice. The mixin also currently prefers
?lang over LANGUAGE_CODE despite its comment; prefix precedence must be corrected
and regression-tested when P1-3 is resumed. Authentication/session enforcement,
form CSRF and demo continuation must not be disabled to manufacture a green gate.

## Owner decisions needed — blocking first

1. **Anonymous analytics vs cookieless public pages.** Recommended for approval:
   count anonymous public page views without creating an identity; retain unique
   visitor/online tracking for existing sessions or users who later consent/login.
   Label those counts honestly as partial coverage, update the privacy notice and
   analytics tests, then implement the language change and caching allow-list.
   This changes the coverage of the dashboard's current anonymous unique/online
   counts. Alternative: retain current session-based anonymous counts and explicitly
   relax the no-cookie requirement; public cookie responses cannot be treated as
   universally shared-cacheable. No IP/UA fingerprinting or cookie stripping proposed.
2. Later: verify/approve marketing copy in KEYWORDS.md (the table itself says draft),
   supply unique demo introductions and real FAQ text, author identity and sameAs URLs.
   No claims of rankings, reviews, clients, legal facts or prices were invented.
3. Later: decide whether to approve a Blog Post updated_at/author migration. None
   was created here. Homepage H1 proposals require explicit approval before applying.

## Task ledger (all requested IDs)

Tests/commit evidence for implemented rows is in the shared sections below.
Unstarted rows have **no changed file, no commit, no test run, no before/after
claim**; their rollback boundary is N/A. Their status is not VERIFIED merely
because the audit describes an existing implementation.

| Task | Status | Files / evidence / reason |
| --- | --- | --- |
| P1-1 | VERIFIED (local) | core/sitemaps.py, core/test_seo_pwa.py, core/tests_seo_contract.py; active exam about URLs, preserved lastmod/access, red→green evidence above. |
| P1-2 | VERIFIED (local) | Entire emitted sitemap: anonymous 200/indexable/self canonical/H1/nonempty unique titles/descriptions/reciprocal alternates. Red: 50 subtest failures; now green. |
| P1-3 | BLOCKED | No production code changed. Independent traffic session writer reproduced; analytics/product coverage decision required. Diagnostic test is characterization, NOT cookieless acceptance. |
| P1-4 | VERIFIED (local) | Page-specific descriptions from visible content and exam fields, including assessment terms outside sitemap. |
| P1-5 | PARTIAL | Shared brand context, public title suffixes and og:site_name; protected gallery and embedded brand names retain correct existing spelling. |
| P1-6 | NOT_STARTED | Existing core.test_seo_pwa.SearchDiscoveryTests.test_private_workspaces_are_excluded_from_crawling explicitly requires X-Robots-Tag: noindex. Header retained under the prompt's safety condition; no assertion weakened. |
| P2-1 | VERIFIED (local) | One model-backed Organization/WebSite graph, real logo, no guessed sameAs/contact fields. |
| P2-2 | VERIFIED (local) | Matching visible bilingual breadcrumbs and BreadcrumbList; mobile wrap/desktop/local navigation checked. |
| P2-3 | VERIFIED (local) | Service detail: Service/provider/areaServed, no fabricated Offer or price. |
| P2-4 | VERIFIED (local) | CRM truthfully uses Service; exams use WebPage/BreadcrumbList, never Course/rating. |
| P2-5 | NOT_STARTED | No blog schema/model/migration change; author and modification metadata approval remains needed. |
| P2-6 | VERIFIED (local) | Template-only unique titles/descriptions use demo title/category/tagline/fit label; protected view untouched; contract passes. |
| P2-7 | VERIFIED (local) | Whole-sitemap JSON parsing, unique IDs/absolute URLs/type safety; 5 actual rendered graphs below. |
| P3-1 | NOT_STARTED | Implementation not authorized; readiness design/file/migration checklist VERIFIED below, no article created. |
| P3-2 | NOT_STARTED | Audience/FAQ proposal and existing-field inventory VERIFIED below; owner facts missing, no copy applied. |
| P3-3 | NOT_STARTED | Unique intro slot proposal VERIFIED below; no intros/model changes applied. |
| P3-4 | NOT_STARTED | Existing About/entity layout proposal VERIFIED below; no entity page/footer edits. |
| P3-5 | NOT_STARTED | Proposed bilingual H1/lead VERIFIED below, wording not applied. Home changed only for preload/links. |
| P4-1 | BLOCKED | OWNER DECISION DEFERRED; analytics, language session behavior and cache policy must not change. |
| P4-2 | PARTIAL | Diagnosis VERIFIED: 24 runs, median/spread below. Home CLS fix verified; main-thread/audio cost unresolved, no production claim. |
| P4-3 | NOT_STARTED | No first-paint PWA browser observation or change. |
| P4-4 | NOT_STARTED | No new image introduced; future image policy still to enforce. |

## Tests actually run

Interpreter: `.venv/bin/python` (Python 3.9.6/Django 4.2.30).

```sh
# Before correction — expected real failures, not skipped:
.venv/bin/python manage.py test core.tests_seo_contract.ExamSearchContractTests --verbosity 1
# 3 tests, 3 failure records as explained above.

# After correction:
.venv/bin/python manage.py test core.tests_seo_contract core.test_seo_pwa core.tests core.test_security_redirects traffic --verbosity 1
# 50/50 passed, zero skips; includes 4 new tests (3 exam contracts + analytics characterization).
.venv/bin/python manage.py check
# 0 issues
.venv/bin/python manage.py makemigrations --check --dry-run
# No changes detected
git diff --check
# clean
```

All data-writing tests used Django's temporary test database. No production or
permanent local database test fixtures were written. Live probes were ordinary
anonymous public HTTP reads; their response cookie values are not retained here.
Expected /health/ 503 log belongs to an existing failure-path test, not a failure.

Deliberately not run: six-domain LanguageViewMixin suite (mixin unchanged), full
suite (Phase 2/4 never reached), PostgreSQL concurrency (no schema/writer/locking
change), browser/Lighthouse (no visual/performance change), CI, production release.
Nothing missing is labeled PASS. Previous release evidence is not SEO evidence.

## Diff, risks and rollback

- Runtime patch: one reverse target in ExamSitemap. Existing sitemap regression
  assertion now requires /about/ and explicitly rejects the old price-page <loc>.
- New contract and diagnostic tests plus documentation; no model/migration,
  request/payment/assessment scoring/authorization changes.
- Three user-dirty gallery files are preserved and excluded from staging/commit.
- Roll back local SEO implementation commit `4d22cc1` to restore the old sitemap target;
  no database rollback required. That would reintroduce the indexing defect.
- Session creation/cache bypass remains unresolved, and the full metadata/schema/
  content/performance programme remains incomplete. No ranking/traffic gain claimed.

## Exact changed public URLs / re-crawl list

**HTML pages changed: none.** `/sitemap.xml` XML changes locally only: active exam
locations become `/{fa|en}/assessments/<active-slug>/about/` rather than the gated
detail URL. Existing briefing HTML, metadata, headers and UI are unchanged.
Production remains unchanged until a separately authorized deployment.

After a future approved deployment: validate the live sitemap's actual locations
and statuses, resubmit https://rvionai.com/sitemap.xml in Search Console, inspect
the English/Python about URLs. The three unknown demo URLs are not named in the
provided evidence; retrieve their exact names from Search Console before requesting
indexing. No Search Console/DNS/indexing request has been submitted by this task.

## Primary references consulted

- [Django session persistence](https://docs.djangoproject.com/en/4.2/topics/http/sessions/):
  session writes and middleware cookie behavior support the root-cause analysis.
- [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap):
  sitemap entries should represent the preferred crawlable URLs; sitemap submission
  itself is not evidence of ranking or indexing success.

## Continuation — AGENT-PROMPT-2

The user explicitly assigned execution to this same single primary agent.
No delegation or external messaging. OWNER DECISION = DEFERRED.
Whole-sitemap fixtures cover all five sitemap classes, all seven demo categories
with two variants each, differently named bilingual blog slugs, and both exam
types, alongside migrated seed content. Every emitted URL is crawled anonymously.
No duplicate title/description exceptions. FA-only discovery wizards are explicit
translation exceptions; their English redirects are no longer advertised as alternates.

Red evidence: `.venv/bin/python manage.py test core.tests_seo_contract.WholeSitemapContractTests --verbosity 1`
ran 2 tests, 50 subtest failures, no errors (log `/tmp/rvion-seo-contract-red.log`).
An initial test implementation error resolving localized URLs outside a language
override was corrected before recording this red result; it was not a product defect.
Metadata changes contain descriptive summaries only; legal provisions, fees,
exam questions, forms, customer records and privacy policy text remain unchanged.
P2-6's template-only metadata was moved into this coherent contract/metadata phase
because the required uniqueness gate exposes existing repeated category descriptions.
Do not commit a knowingly failing contract as an accepted implementation phase.

Metadata gate: `.venv/bin/python manage.py test core.tests_seo_contract core.test_seo_pwa core.tests core.test_security_redirects blog services projects leads --verbosity 1`
passed 375 tests (16 PostgreSQL-only skips). After adding a brand/terms test,
reran `.venv/bin/python manage.py test core.tests_seo_contract --verbosity 1`: 7/7 passed.
Check: 0 issues; migration drift: no changes; diff check: clean.
SQLite read-path evidence, not PostgreSQL concurrency or production.
Changed HTML: FA/EN company, blog list, contact, privacy, service terms, refund
policy, assessment terms, active exam briefings/demo previews; title suffixes
also affect home, about, service list/detail and blog detail. FA-only enquiry
head gains valid Persian/x-default alternates. No new claim needing approval.
Rollback: bounded metadata/contract commit in Git; no DB rollback required.

## Unified schema and navigation — current continuation

P2 graph uses a public-route allow-list, CompanyProfile context already loaded by
the page, one Organization/WebSite, stable absolute IDs, safe JSON script escaping,
and matching visible bilingual breadcrumbs. No private account/customer graph.
No invented sameAs, review/rating, Offer, price or exam Course. CRM uses Service.
Organization/Service deliberately do not use unsupported inLanguage; the linked
WebSite/WebPage/BlogPosting carry locale. References:
[Google structured data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data),
[Organization](https://schema.org/Organization), [Service](https://schema.org/Service),
[localized alternates](https://developers.google.com/search/docs/specialty/international/localized-versions).

The existing BlogPosting is consolidated into the same graph without adding an
author, image or modification claim (P2-5 remains NOT_STARTED). Its prior test now
resolves mainEntityOfPage to the actual WebPage URL, preserving canonical proof.
Focused schema/core/PWA: 51/51 passed. No migrations; check/drift/diff clean.
Full-suite first attempts exposed old CSS cache-version expectations and a compact
JSON formatting expectation: versions updated to the intentional v7, JSON remains
compact; no assertion skipped or business access weakened. Parallel failure
reporting initially lacked tblib; installed tblib 3.2.2 only into disposable
/tmp/rvion-seo-qa.3snpId/test-deps, not project requirements or production.

Visual proof is bounded to new navigation: Persian and English service at 390px,
Persian CRM order at 320px, English service at 1440px; screenshots inspected and
scrollWidth equals viewport. Long English crumbs wrap, current item is plain
aria-current text, ancestor links retain 44px targets. Clicking the CRM Home
breadcrumb stays on the local host (relative visible link; absolute schema URL).
No full-product UX acceptance or independent review is claimed. Premium strict
audit reported 55 errors (actionless-button detection on existing demo controls);
it is NOT a passing whole-product premium gate. Controls use JS data attributes,
but this SEO phase does not claim to have interactively dismissed all findings.
They remain recorded outside this scope, not hidden or rewritten in protected UI.

Final full suite: 1032 tests, OK (27 PostgreSQL-only skips), 105.334 seconds:
`PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps .venv/bin/python manage.py test --parallel 4 --verbosity 1`.
The earlier sequential run had 3 failures/1 error (two cache-version subtests,
one load-order version lookup, one JSON formatting check); all corrected and the
full suite rerun, no skips added. Local Python 3.9/SQLite; this is not a new
PostgreSQL/Python 3.11/3.12 CI or deployed-production proof.

Changed public HTML now includes all allow-listed public pages, not only the
historical sitemap-only change above. Paths with fa/en versions:
`/`, `/about/`, `/company/`, `/crm/`, `/services/`,
`/services/<published-slug>/`, `/blog/`, `/blog/<published-localized-slug>/`,
`/projects/demos/`, `/projects/demos/<active-slug>/`, `/assessments/`,
`/assessments/<active-slug>/about/`, `/assessments/terms/`, `/contact/`,
`/privacy/`, `/service-terms/`, `/refund-policy/`, `/start/`.
FA-only: `/fa/crm-order/`, `/fa/clinic-order/`. Dynamic paths must be enumerated
from the live sitemap after a future authorized release; this task does not ask
Google to recrawl QA fixtures. Private/noindex pages intentionally emit no graph.
Single-language-only blog rows are not a new fixture covered by this contract;
no claim of exhaustive arbitrary future content validation.

Five samples below are parsed actual HTTP output from the disposable runtime.
Exam seo-qa and blog seo-qa-fa are clearly synthetic QA-only records, never production.
Company fields come from the migrated existing CompanyProfile, not invented copy.

### Rendered /fa/

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://rvionai.com/#organization",
      "name": "آرویون",
      "alternateName": "Rvion",
      "url": "https://rvionai.com/",
      "logo": "https://rvionai.com/static/core/icons/icon-512.03c06f9d62f5.png",
      "areaServed": "IR",
      "legalName": "آروین توسعه تجارت هوشمند",
      "telephone": "09333021100",
      "identifier": "14015444540",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        "addressCountry": "IR",
        "postalCode": "1683445995"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://rvionai.com/#website",
      "name": "آرویون",
      "url": "https://rvionai.com/",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      }
    },
    {
      "@type": "WebPage",
      "@id": "https://rvionai.com/fa/#webpage",
      "url": "https://rvionai.com/fa/",
      "name": "خانه",
      "inLanguage": "fa",
      "isPartOf": {
        "@id": "https://rvionai.com/#website"
      }
    }
  ]
}
```

### Rendered /fa/services/corporate-website-design/

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://rvionai.com/#organization",
      "name": "آرویون",
      "alternateName": "Rvion",
      "url": "https://rvionai.com/",
      "logo": "https://rvionai.com/static/core/icons/icon-512.03c06f9d62f5.png",
      "areaServed": "IR",
      "legalName": "آروین توسعه تجارت هوشمند",
      "telephone": "09333021100",
      "identifier": "14015444540",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        "addressCountry": "IR",
        "postalCode": "1683445995"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://rvionai.com/#website",
      "name": "آرویون",
      "url": "https://rvionai.com/",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://rvionai.com/fa/services/corporate-website-design/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "خانه",
          "item": "https://rvionai.com/fa/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "راهکارها",
          "item": "https://rvionai.com/fa/services/"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "طراحی و توسعه وب‌سایت شرکتی",
          "item": "https://rvionai.com/fa/services/corporate-website-design/"
        }
      ]
    },
    {
      "@type": "WebPage",
      "@id": "https://rvionai.com/fa/services/corporate-website-design/#webpage",
      "url": "https://rvionai.com/fa/services/corporate-website-design/",
      "name": "طراحی و توسعه وب‌سایت شرکتی",
      "inLanguage": "fa",
      "isPartOf": {
        "@id": "https://rvionai.com/#website"
      },
      "breadcrumb": {
        "@id": "https://rvionai.com/fa/services/corporate-website-design/#breadcrumb"
      },
      "mainEntity": {
        "@id": "https://rvionai.com/fa/services/corporate-website-design/#service"
      }
    },
    {
      "@type": "Service",
      "@id": "https://rvionai.com/fa/services/corporate-website-design/#service",
      "name": "طراحی و توسعه وب‌سایت شرکتی",
      "serviceType": "طراحی و توسعه وب‌سایت شرکتی",
      "url": "https://rvionai.com/fa/services/corporate-website-design/",
      "areaServed": "IR",
      "provider": {
        "@id": "https://rvionai.com/#organization"
      }
    }
  ]
}
```

### Rendered /fa/crm/

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://rvionai.com/#organization",
      "name": "آرویون",
      "alternateName": "Rvion",
      "url": "https://rvionai.com/",
      "logo": "https://rvionai.com/static/core/icons/icon-512.03c06f9d62f5.png",
      "areaServed": "IR",
      "legalName": "آروین توسعه تجارت هوشمند",
      "telephone": "09333021100",
      "identifier": "14015444540",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        "addressCountry": "IR",
        "postalCode": "1683445995"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://rvionai.com/#website",
      "name": "آرویون",
      "url": "https://rvionai.com/",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://rvionai.com/fa/crm/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "خانه",
          "item": "https://rvionai.com/fa/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "CRM سازمانی",
          "item": "https://rvionai.com/fa/crm/"
        }
      ]
    },
    {
      "@type": "WebPage",
      "@id": "https://rvionai.com/fa/crm/#webpage",
      "url": "https://rvionai.com/fa/crm/",
      "name": "CRM سازمانی",
      "inLanguage": "fa",
      "isPartOf": {
        "@id": "https://rvionai.com/#website"
      },
      "breadcrumb": {
        "@id": "https://rvionai.com/fa/crm/#breadcrumb"
      },
      "mainEntity": {
        "@id": "https://rvionai.com/fa/crm/#service"
      }
    },
    {
      "@type": "Service",
      "@id": "https://rvionai.com/fa/crm/#service",
      "name": "CRM سازمانی",
      "serviceType": "CRM سازمانی",
      "url": "https://rvionai.com/fa/crm/",
      "areaServed": "IR",
      "provider": {
        "@id": "https://rvionai.com/#organization"
      }
    }
  ]
}
```

### Rendered /fa/assessments/seo-qa/about/

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://rvionai.com/#organization",
      "name": "آرویون",
      "alternateName": "Rvion",
      "url": "https://rvionai.com/",
      "logo": "https://rvionai.com/static/core/icons/icon-512.03c06f9d62f5.png",
      "areaServed": "IR",
      "legalName": "آروین توسعه تجارت هوشمند",
      "telephone": "09333021100",
      "identifier": "14015444540",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        "addressCountry": "IR",
        "postalCode": "1683445995"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://rvionai.com/#website",
      "name": "آرویون",
      "url": "https://rvionai.com/",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://rvionai.com/fa/assessments/seo-qa/about/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "خانه",
          "item": "https://rvionai.com/fa/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "آزمون‌ها",
          "item": "https://rvionai.com/fa/assessments/"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "آزمون نمونه بررسی سئو",
          "item": "https://rvionai.com/fa/assessments/seo-qa/about/"
        }
      ]
    },
    {
      "@type": "WebPage",
      "@id": "https://rvionai.com/fa/assessments/seo-qa/about/#webpage",
      "url": "https://rvionai.com/fa/assessments/seo-qa/about/",
      "name": "آزمون نمونه بررسی سئو",
      "inLanguage": "fa",
      "isPartOf": {
        "@id": "https://rvionai.com/#website"
      },
      "breadcrumb": {
        "@id": "https://rvionai.com/fa/assessments/seo-qa/about/#breadcrumb"
      }
    }
  ]
}
```

### Rendered /fa/blog/seo-qa-fa/

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://rvionai.com/#organization",
      "name": "آرویون",
      "alternateName": "Rvion",
      "url": "https://rvionai.com/",
      "logo": "https://rvionai.com/static/core/icons/icon-512.03c06f9d62f5.png",
      "areaServed": "IR",
      "legalName": "آروین توسعه تجارت هوشمند",
      "telephone": "09333021100",
      "identifier": "14015444540",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "تهران، نارمک شمالی، خیابان نیلفروشان، پلاک ۱، طبقه اول، واحد ۱",
        "addressCountry": "IR",
        "postalCode": "1683445995"
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://rvionai.com/#website",
      "name": "آرویون",
      "url": "https://rvionai.com/",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "خانه",
          "item": "https://rvionai.com/fa/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "دیدگاه‌ها",
          "item": "https://rvionai.com/fa/blog/"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "مقاله نمونه بررسی",
          "item": "https://rvionai.com/fa/blog/seo-qa-fa/"
        }
      ]
    },
    {
      "@type": "WebPage",
      "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#webpage",
      "url": "https://rvionai.com/fa/blog/seo-qa-fa/",
      "name": "مقاله نمونه بررسی",
      "inLanguage": "fa",
      "isPartOf": {
        "@id": "https://rvionai.com/#website"
      },
      "breadcrumb": {
        "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#breadcrumb"
      },
      "mainEntity": {
        "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#article"
      }
    },
    {
      "@type": "BlogPosting",
      "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#article",
      "url": "https://rvionai.com/fa/blog/seo-qa-fa/",
      "headline": "مقاله نمونه بررسی",
      "description": "این مقاله فقط در پایگاه داده موقت بررسی وجود دارد.",
      "inLanguage": "fa",
      "publisher": {
        "@id": "https://rvionai.com/#organization"
      },
      "mainEntityOfPage": {
        "@id": "https://rvionai.com/fa/blog/seo-qa-fa/#webpage"
      },
      "datePublished": "2026-10-07T09:59:20.919000+00:00"
    }
  ]
}
```


## Lighthouse mobile — measurement only

Lighthouse 13.5.0 (official npm), Chrome, default mobile simulated throttling.
Local runtime DEBUG=False, compressed-manifest static/WhiteNoise, isolated SQLite
and WSGI on 127.0.0.1:8142; no TLS/CDN/production DB. One valid run per page, not
a median or RUM/INP measurement. Other local tests shared CPU; results are directional.
Two initial home/blog runs failed NO_NAVSTART and are excluded rather than scored.
The raw successful reports are retained in /tmp/rvion-seo-qa.3snpId:
lighthouse-home-retry.json, lighthouse-service.json, lighthouse-blog-retry.json,
lighthouse-demo.json. Current working tree includes preserved user gallery edits;
these are not a clean-release or before/after comparison.
[Measurement reference](https://developer.chrome.com/docs/lighthouse/overview).

| Local path | Performance /100 | LCP ms | CLS | TBT ms |
| --- | ---: | ---: | ---: | ---: |
| /fa/ | 57 | 3072 | 0.280 | 869 |
| /fa/services/corporate-website-design/ | 96 | 2422 | 0.0085 | 0 |
| /fa/blog/ | 69 | 3120 | 0 | 1101 |
| /fa/projects/demos/saffron-table/ | 71 | 3201 | 0 | 723 |

Render-blocking CSS common to all four (hashed files; query versions retained):
tokens.css?v=5, site.css?v=40, components.css?v=7, public-shell.css?v=1,
footer-studio.css?v=2. Home additionally home-studio.css?v=3 and
projects/demo-studio.css?v=4 (7 total). Demo additionally demo-gallery.css?v=8,
demo-studio.css?v=4, sector-experience.css?v=1 (8 total). Blog/service each 5.
Exact hashed URLs remain in the raw JSON render-blocking-insight audit.
No CSS consolidation, loader, cache, image or font optimization was attempted.
Home layout shift and home/blog/demo main-thread blocking merit a later scoped
performance phase, not a ranking or production-speed claim.

## Read-only crawler diagnostic

**NO**: traffic/middleware.py:52–68 only filters method/status/content type/private
routes/prefixes; no known-crawler User-Agent exclusion. Lines 72–85 create session,
increment page/unique counts and update online records for eligible crawler GETs.
Proposal: after owner approval, exclude classified crawlers from human unique/online
analytics and avoid creating their analytics sessions. This alone does not remove
LanguageViewMixin's language session writes. No bot heuristic, middleware behavior,
cookie/privacy text or caching was changed. P1-3/P4-1 remain BLOCKED (DEFERRED).

## Boundaries and rollback

Metadata milestone: 93132bc; schema/navigation and measurement milestone e8a8aa2.
Revert the scoped local commits for source rollback; no schema/data rollback needed.
No permanent dev or production database changes, external SMS, push or deploy.
Three existing user gallery edits are preserved and excluded. Canonical report
and CURRENT_STATE are the continuation source; historical checkpoints above remain
history, not the current stage result.

## Follow-up 1 — telephone regression VERIFIED (local)

Starting HEAD 517211e; OWNER DECISION remains DEFERRED. Only schema serialization
normalizes an 11-digit local Iranian mobile to +98; existing international values
remain unchanged and empty values are omitted. CompanyProfile and visible text
are never modified. Corrected rendered Organization fragment:
`"@type":"Organization","telephone":"+989333021100"`.
Files: core/templatetags/seo.py, core/tests_seo_contract.py and existing checkpoints.
`.venv/bin/python manage.py test core.tests_seo_contract --verbosity 1`: 12/12 OK.
Blank legacy-profile fixture uses a test-DB queryset update, since model full_clean
correctly rejects new blank profiles; this does not change model validation.
No migration, push, deploy, messaging or permanent DB writes. Rollback: revert
the scoped telephone commit; stored company data needs no rollback.
Next: baseline audit provenance and idle 3-run performance medians.

## Follow-up 2 — premium audit baseline VERIFIED (comparison only)

Telephone commit: b431ad2. Disposable detached worktree created at exactly
6977b30: /tmp/rvion-seo-baseline-6977b30; main worktree was never stashed/reset.
Command: `.venv/bin/python /Users/rwin/.codex/plugins/cache/openai-curated-remote/frontend-design-premium/1.4.0/skills/frontend-design-premium/scripts/audit_project.py /tmp/rvion-seo-baseline-6977b30 --mode strict`.
Baseline and e8a8aa2-era audit both report exactly 55 errors, all
affordance.actionless-button. Same file/rule/message multiset and counts, and
every literal button's complete markup in all 10 flagged templates is byte-for-byte
identical between baseline and current code. Line numbers alone changed on preview
because its redundant breadcrumb was removed; selectors/attributes did not.
Counts: demo_full 3, demo_preview 7; scenes clinic 7, corporate 3, education 6,
footer 1, jewelry 2, portfolio 7, restaurant 7, storefront 12. No finding introduced
by 93132bc/e8a8aa2. Raw baseline audit retained at
/tmp/rvion-seo-qa.3snpId/baseline-6977b30-premium-audit.json; the clean disposable
baseline worktree was removed after moving that artifact, without force;
previous raw audit retained under /tmp/rvion-seo-qa.3snpId/premium-audit.json.

These are static action-detection false positives where a data attribute has an
explicit handler: demo-configurator.js data-demo-view/reset (244–245), config-open
(304), demo-action (339), demo-filter (399); storefront.js owns store controls.
Example restaurant filter has data-demo-filter and changes hidden item states;
reservation data-demo-action sets aria-pressed plus live summary; footer
data-config-open opens the existing settings region/sheet. No claim that every
possible runtime state was interactively audited. The strict auditor remains red,
not waived as a full premium gate; comparison itself is verified. Protected UI
unchanged. This phase is evidence-only, no product fix needed, no migrations.
Rollback: documentation-only; no runtime/data consequence.

## Follow-up 3 — P4-2 diagnosis VERIFIED; optimization PARTIAL (local)

Baseline comparison commit: 6ee23a1. Lighthouse 13.5.0, the same isolated
DEBUG=False runtime at 8142, default mobile simulated throttling. Three serial
runs per page before and after; agent tests/builds/browser work paused during
each batch. Other user apps/OS background activity were not controlled, so this
is not a guarantee of a completely idle machine or production/RUM performance.
Raw JSON, trace and devtoolslog: /tmp/rvion-seo-qa.3snpId/before-{home,service,blog,demo}-{1,2,3}*
and after-{home,service,blog,demo}-{1,2,3}*. No failed runs included.
Each cell below is median [min–max]; times in milliseconds.

| Page | Before LCP | After LCP | Before CLS | After CLS | Before TBT | After TBT | Score before → after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Home | 2726 [2721–2727] | 2584 [2481–2729] | .279 [.014–.279] | 0 [0–0] | 361 [0–384] | 654 [161–699] | 79 [71–84] → 81 [78–94] |
| Service | 2417 [2416–2417] | 2421 [2416–2421] | .0085 [.0068–.0085] | .0085 [.0068–.0085] | 279 [0–404] | 282 [0–450] | 90 [86–96] → 90 [85–96] |
| Blog | 2417 [2412–2423] | 2422 [2420–2473] | .0029 [.0029–.0029] | .0029 [.0027–.0029] | 273 [0–291] | 299 [0–520] | 90 [90–96] → 89 [82–96] |
| Demo | 2877 [2732–3031] | 2882 [2876–2886] | .0036 [.0021–.0037] | .0031 [.0031–.0031] | 355 [0–526] | 0 [0–0] | 82 [79–93] → 92 [92–92] |

Home before run 1: cls-culprits-insight (Lighthouse 13's replacement for the
legacy layout-shift-elements audit) identifies section.website-hero, width 388,
top 131, height 1172, shift score .2789797, and Vazirmatn Regular/Bold/Black.
Blog's small shift is its page-hero h1 (.0028887). Existing sample art reserves
its aspect ratio; no evidence supports arbitrary image/section min-heights.
[Web fonts can cause layout shifts](https://web.dev/articles/optimize-cls).

bootup-time/mainthread-work-breakdown: home run 1 style/layout 614ms, script
evaluation 80ms, HTML/CSS parsing 54ms. Home runs 2/3 script evaluation 590/614ms;
welcome-sound.js accounts for approximately 547/569ms. Blog runs 1/3 attribute
495/531ms to welcome-sound.js; run 1 style/layout 308ms. Document-attributed
layout work cannot be honestly assigned to one stylesheet. Service TBT is NOT
consistently zero: its sound script also costs 666/507ms in runs 1/2. The earlier
single-run inference that only page-specific code causes blocking is disproved.
[Audit interpretation](https://developer.chrome.com/docs/lighthouse/performance/bootup-time).
Changing welcome autoplay would change shared product behaviour, so was not done.

Seven home blocking stylesheets: tokens (fonts/tokens), site (base typography,
layout/reset), components (buttons/focus), public-shell (header/navigation),
home-studio (hero), demo-studio (visible hero sample art) are needed above fold.
footer-studio is below-fold but shared; no removal/reordering/consolidation.
Unused-byte estimates do not justify removing shared selectors/cascade rules.

One retained fix: FA home only preloads its three above-fold font weights via
a base font_preload block. EN, service, blog and demo have no new preloads.
Files: core/templates/core/{base,home}.html, core/tests_seo_contract.py.
Final rendered design checked before/after at FA/EN 390x844 and 1440x900;
no redesign, horizontal overflow or CSS order change. Three-run CLS consistently
fell to zero, so this is not a no-effect fix. Home TBT nevertheless worsened;
no overall speed, production or ranking improvement is claimed. Other-page
changes are noise, not attributed gains. Main-thread optimization remains PARTIAL.
`.venv/bin/python manage.py test core.tests_seo_contract core.tests --verbosity 1`:
45/45 OK; git diff --check clean. No migration/analytics/cache/loader change.
Rollback: revert only this font-preload milestone; no data rollback needed.
Owner decision needed for changing startup sound timing; deferred privacy tasks
P1-3/P4-1 stay BLOCKED and unchanged.

## Follow-up 4 — contextual linking VERIFIED (local); content proposals only

Font milestone e367e39; contextual-link milestone 6f64d2a. Applied only template anchors in core/home.html,
services/detail.html + services/includes/related_demos.html, and
projects/demo_preview.html + projects/includes/related_service.html.
Uses existing button/layout classes, no new CSS/JS/view/model/migration or claims.
Mappings use the existing seeded public slugs, not invented customers/case studies:
corporate → parsa-advisory/linea-studio; ecommerce → nava-market/sarvin-atelier;
custom applications → roshna-clinic/ariana-academy/saffron-table. Consulting and
maintenance → the active gallery; consulting/custom applications also → CRM.
Each demo category maps back to corporate/ecommerce/custom application service
and contact. Home links to services/CRM/exams. Full standalone noindex demos
remain untouched; linking concerns their indexable preview pages only.

core.tests_seo_contract asserts exact scoped anchor lists across 5 seeded service
routes and 7 demo categories plus home in FA/EN, identical structure, each target
200 without following redirects, no Location/noindex meta or header. Scope is
the new contextual links, not legitimate login links elsewhere in the shell.
`.venv/bin/python manage.py test core.tests_seo_contract services.tests projects.tests --verbosity 1`:
45/45 OK (11.603s). Check 0 issues; migration dry-run no changes; diff clean.
Browser: home/service/restaurant preview FA/EN at 390 and 1440, every new anchor
fits and document scrollWidth equals viewport. Screens inspected for FA mobile
service buttons and EN desktop preview buttons, keyboard focus visible. Real
service→restaurant navigation succeeded. Runtime sample filter shows only drinks,
reservation shows selected time/guest summary, settings button opens its sheet:
three concrete baseline-auditor false positives verified, not a blanket 55-control audit.

P2 maintenance limitation: associations are template constants as requested;
no live availability lookup was added. If an operator disables/renames one of
these seeded targets, update corresponding anchors or authorize a dynamic
published-only association layer; current fixture/isolated-runtime targets pass.
No production availability check was run. Plain contact is a separate enquiry
link, not a substitute for the existing selection-preserving order submission.
Rollback: this scoped template/test milestone only, no data rollback.

### P3-5 home wording — proposal VERIFIED; implementation NOT_STARTED

Input: /Users/rwin/Documents/claud/rvionai.com-audit/KEYWORDS.md, not evidence of
search volume, rank or current free/paid policy. Proposed H1 FA:
«طراحی سایت اختصاصی؛ سایت شما، با امضای خود شما.»
EN: “Custom website design. Unmistakably yours.”
Proposed lead FA: «نمونه‌ای متناسب با کسب‌وکارتان انتخاب و شخصی‌سازی کنید؛
سفارش طراحی سایت اختصاصی را با انتخاب‌های خودتان آغاز کنید.»
EN: “Choose and customise a sample for your business, then start your custom
website enquiry with your choices intact.” No cost/quality/rank guarantee.
Files if approved: core/templates/core/home.html, core/tests_seo_contract.py,
core/tests.py and canonical checkpoints. No migration. Approve both languages;
keep exactly one H1 and the existing brand slogan, not a keyword-stuffed second H1.

### P3-2 service audience + FAQ — proposal VERIFIED; implementation NOT_STARTED

Existing data supports consulting for new/existing products and MVP/redesign,
corporate presence/leads, ecommerce catalogue/cart/payment, custom operational
platforms, maintenance/growth. Audience paragraphs can be derived from each
Service.description_fa/en rather than inventing sectors or customer statistics.
Questions answerable from existing fields: “What will be delivered?” (deliverables),
“What are the stages?” (process), “How long?” (duration), “How to enquire?” (existing CTA).
Existing template says 50/50 payment and three months support; owner must confirm
whether these apply to EACH service before republishing them as FAQ commitments.
Missing owner copy, both languages: inclusions/exclusions, hosting/domain ownership,
ongoing support terms/SLA, content responsibility, revisions/acceptance, payment
exceptions and any price ranges. Do not answer these by guessing.
Files: services/templates/services/detail.html and a new
services/templates/services/includes/faq.html; services/tests.py/core/tests_seo_contract.py.
No migration for rendering existing fields; editable independent FAQs would require
approved Service bilingual FAQ fields in services/models/service.py + new migration,
services/admin.py and input validation/tests. No FAQ rich-result promise.

### P3-3 unique demo introductions — proposal VERIFIED; implementation NOT_STARTED

Current title/tagline/fit label already differ; propose one unique bilingual intro
per actual DemoTemplate, placed before preview, explaining business goal, sample
capabilities and discovery boundaries without pretending it is a delivered client site.
Owner supplies/approves 11 FA/EN intros (all current seeded demos), with none claiming
real revenue, bookings, credentials or customer results. Files if approved:
projects/models/demo.py (intro_fa/en), new projects migration (blank-compatible),
projects/admin.py, projects/views/projects.py (currently protected: separate permission
needed), projects/templates/projects/demo_preview.html, projects/tests.py,
core/tests_seo_contract.py. Do not auto-fill boilerplate and call it unique content.

### P3-4 About/entity — proposal VERIFIED; implementation NOT_STARTED

Existing pages: core/templates/core/about.html and company_info.html; existing
CompanyProfile: legal names, brand, registration/national ID, executive names,
phone, addresses/postal code, support hours, established_date_fa and domain.
Propose identity header → actual activities/services → profile-backed facts/contact
→ leadership → company-information link. Replace duplicated static names where
profile fields exist. Owner must verify leadership biography, “10 years”, partner
role and EN foundation year (model only stores a Persian date string), and supply
official social/profile URLs for sameAs, or leave it absent. Do not infer translated
legal forms or credentials. Files: core/templates/core/{about,company_info}.html,
core/views/base.py only if needed, core/tests.py, core/tests_seo_contract.py and
core/templatetags/seo.py if approved sameAs added. No migration for existing fields;
persistent bilingual biography/social URLs would need core/models/company.py,
core/admin.py, validation and a new core migration. No new duplicate About route.

### P3-1 / P2-5 blog readiness — proposal VERIFIED; implementation NOT_STARTED

Already present: bilingual slug/title/summary/body, published_at, hero_image, tags;
article published meta and BlogPosting datePublished. Missing: author and genuine
editorial modification date (do not fake with request time or deployment date).
Checklist: real author/byline and approved bio; visible published/updated dates;
estimated reading time from sanitized localized body; related published posts with
valid language slugs; accessible H2/H3 TOC with stable sanitized heading IDs;
no duplicated H1; image rights/alt/dimensions; real unique body; owner content review.
Files: blog/models/post.py, a new blog migration for author/updated metadata,
blog/admin.py, blog/views/post_detail.py, blog/templates/blog/{detail,list}.html,
blog/templates/blog/components/post_card.html, core/templatetags/seo.py,
core/sitemaps.py, blog/tests.py, core/tests_seo_contract.py. Reading time/related/TOC
alone need no migration; safe Markdown/bleach heading ID policy needs targeted tests.
Owner supplies author's public name/role/bio and identity URL if any, publication
approval and factual last editorial update for existing articles (or omit updated).
No article, schema author, model migration, FAQ or new wording applied this phase.

## Final gate and continuation boundary

`PYTHONPATH=/tmp/rvion-seo-qa.3snpId/test-deps .venv/bin/python manage.py test --parallel 4 --verbosity 1`
ran exactly once at the end: 1035 total, 1008 passed, 27 PostgreSQL-only skipped,
98.918s, OK, no failures. Log: /tmp/rvion-seo-final-suite.log. Expected injected
SMTP/provider/database exceptions in resilience tests are logged, not test failures.
Temporary tblib helper was already present from the previous gate; no dependency
or workflow change made. PostgreSQL, CI, production smoke, and Python 3.11/3.12
matrix were NOT run this phase; local pinned interpreter is Python 3.9.
`manage.py check`: 0 issues; `makemigrations --check --dry-run`: no changes;
`git diff --check`: clean. Tests create/destroy only temporary test databases.

Local milestones in order: b431ad2 (telephone), 6ee23a1 (baseline comparison),
e367e39 (font diagnosis/fix), 6f64d2a (contextual links/proposals).
Phone snippet was read from actual rendered JSON-LD in the isolated browser:
`{"@type":"Organization","telephone":"+989333021100"}`.
Canonical report, CURRENT_STATE and PROJECT_STATUS stay the only live records.
Premium instructions shaped the baseline-provenance and visual evidence checks,
not a UI redesign. Self-review is not independent review/customer acceptance.
Performance before/after belongs to the isolated font milestone; link additions
were made afterward and are not covered by a new Lighthouse batch. No hidden
claim that those local timings represent the final release or production.
All three protected user gallery diffs are preserved/excluded from our commits.
Disposable browser tab closed, viewport reset, agent's port-8142 process stopped;
user's existing port-8126 and browser tabs were untouched. QA artifacts retained.
No production/local permanent DB migration, push, deploy, SMS or customer write.
P1-3/P4-1 remain BLOCKED (OWNER DECISION DEFERRED), optional crawler changes absent.
The authorized independent work is done; entire SEO programme remains PARTIAL.
Source rollback is by the individual scoped commits; no data/schema rollback.

## Owner-approved publication of articles 05–08 — 2026-10-09

Status: VERIFIED / PUBLISHED (content only). Owner explicitly approved the
remaining four articles; earlier unpublished-only restriction superseded for
this publication. No article wording, importer behavior, model, or migration changed.

Files: four sources `blog/content_drafts/05-clinic-website-design.md`,
`06-academy-webinar-website.md`, `07-enterprise-crm-cost.md`,
`08-django-interview-questions.md`; `blog/test_import_drafts.py`; this report;
`.ai/project/CURRENT_STATE.md`. Each copied source compared byte-for-byte with
the owner's read-only external source. Existing v2 covers reused.

Test changes: eight-file body hash fixture; dry-run/repeat counts 4→8; tag count
8→20; Python/Django exam fixture for article08 internal URL; four Persian-only
slugs added to the existing sitemap contract fixture. Assertions not weakened.

Red: `.venv/bin/python manage.py test blog.test_import_drafts --verbosity 0`
ran 27 tests, ten failures: obsolete four-draft assumptions, missing exam fixture,
Persian-only alternates, and two unrelated metadata failures from protected dirty
gallery edits. Those protected files were NOT changed or committed.
Green: clean isolated candidate `/tmp/rvion-articles.KegGHP`, built from HEAD
plus only the article sources/tests. Commands using the repository interpreter:

```text
python manage.py test blog.test_import_drafts blog.test_language_contract --verbosity 1
36 tests OK
python manage.py test --parallel 4 --verbosity 0
1109 tests OK (27 existing skips), 73.632 seconds
```

Publication: bounded key-based SSH attempt timed out (exit255), no remote command
executed. Used the existing authenticated production `/admin/blog/post/add/`
form, with exact approved FA title/summary/body/slug/tags, empty English fields,
uploaded v2 cover, published checkbox, Today/Now date controls. Admin success
messages confirmed IDs5–8 and the list showed all8 published; previous IDs1–4
and their publication dates untouched. This generates Django's normal admin
addition log. No source release/push, importer invocation, production migration,
new server backup, or Search Console submission occurred in this turn.

Live verification: HTTP200 for each new detail page and its `/media/articles/`
cover; one H1 and self-canonical; eight unique article links in `/fa/blog/`; all
four new URLs in `/sitemap.xml`. Exact new public paths:

- `/fa/blog/clinic-website-design-online-booking/` — ID5, 15:37 Tehran.
- `/fa/blog/academy-website-structure-webinar/` — ID6, 15:38 Tehran.
- `/fa/blog/enterprise-crm-development-cost-stages/` — ID7, 15:38 Tehran.
- `/fa/blog/django-interview-questions-with-short-answers/` — ID8, 15:39 Tehran.

Public list and sitemap naturally changed with publication. Screenshot evidence:
`.ai/artifacts/articles-eight-published-20261009.png` (local, not committed).
Textual bank integrity check: normalized SequenceMatcher threshold0.78 against
FA/EN question prompts, 30 article questions, overlap numbers=[], count0; no
bank prompts or answers printed. This is not a proof against every semantic
paraphrase. Legal claims/source accuracy not independently certified in this
turn; publication reflects the owner's editorial approval, not legal advice.
P1-3/P4-1 remain DEFERRED.

Rollback: uncheck published for ONLY IDs5–8 (retain records and covers), verify
their public URLs disappear and list/sitemap exclude them. Local source rollback
can revert the scoped article-bundle commit; it does not undo production content.
No customer data deleted. Unrelated dirty gallery/editor files preserved.

## Updated public HTML URLs (source changes deployed in 94c9c06)

Base domain for every path below: https://rvionai.com; `{fa,en}` means both
localized versions, not a literal URL. Dynamic rows are active/published records,
not newly invented pages or a claim of current production availability.

- Font preloads/new contextual anchors: `/fa/`; home anchors also `/en/`.
- Service detail anchors: `/{fa,en}/services/<active-slug>/`, seeded slugs
  digital-product-consulting, corporate-website-design, custom-web-application,
  ecommerce-platform, maintenance-and-growth.
- Demo preview anchors: `/{fa,en}/projects/demos/<active-slug>/`, seeded slugs
  nava-market, orbit-shop, saffron-table, mora-cafe, linea-studio, atlas-profile,
  parsa-advisory, northline-group, roshna-clinic, ariana-academy, sarvin-atelier.
- Telephone schema-only change additionally affects public allow-listed graphs:
  `/{fa,en}/`, `/about/`, `/company/`, `/crm/`, `/services/`, `/projects/demos/`,
  `/blog/`, `/assessments/`, `/contact/`, `/privacy/`, `/service-terms/`,
  `/refund-policy/`, `/start/`, `/assessments/terms/` (each path after its language
  prefix), `/fa/crm-order/`, `/fa/clinic-order/`, and localized active service/demo
  details, published `/{fa,en}/blog/<localized-post-slug>/`, and
  `/{fa,en}/assessments/<active-exam-slug>/about/`, whenever their graph is emitted.
  Already international or absent company phones produce no changed telephone.
- No account/private contract/assessment-attempt/full standalone demo changes.

## Exact owner items waiting (nothing silently approved)

1. Privacy/anonymous analytics session and cache policy: P1-3/P4-1 DEFERRED;
   crawler exclusions require explicit approval, not implemented here.
2. Approve FA/EN proposed home H1/lead; approve unique intros for the 11 demos.
3. Confirm service-specific payment/support commitments; provide FA/EN hosting,
   ownership, scope exclusions, support/SLA, revisions/acceptance and payment
   exceptions for FAQ. Existing description/deliverables/process/duration need
   only editorial approval, not invented answers.
4. Verify company/leadership biography, experience, partner role, EN foundation
   date; supply official public social/profile URLs for sameAs, or omit it.
5. Supply author's public name, role, bio and optional identity URL; approve each
   article and its real editorial update date, or leave modification date absent.
6. Authorize proposed model migrations only if persistent demo intros, editable
   FAQs, company biography/social fields, or Post author/updated metadata are
   selected. None created/applied here. Protected projects/views/projects.py
   needs a separate scope opening for the proposed intro context.
7. Decide whether welcome-sound startup timing can change (lazy AudioContext)
   given measured main-thread cost; sound behavior unchanged in this scope.
8. If seeded services/demos will be disabled/renamed independently, authorize
   dynamic published-only related associations rather than template constants.
   Before any eventual release: verify these public targets on its real data.
# Entry animation — 2026-10-09 (local only)

**Final status: BLOCKED, not release-approved.** Automatic homepage display
is disabled by default; no production change. Implemented preview is available
only with DEBUG on loopback and `?entry_seek=0` (press Resume to play), unless
a future verified release explicitly enables RVION_ENTRY_ENABLED. Do not
enable it now. Earlier per-checkpoint statements below are historical evidence.

Scope: supplied entry-src.html, Piece 1 only. No push/deploy/SSH, models,
migrations, analytics/cookie-policy or protected gallery/content changes.

1. Old first-visit welcome removal: VERIFIED locally. Removed the inline
   session marker, welcome-pending CSS and initial-welcome JS. Renamed shared
   markup to route-loader/data-navigation-loader. Navigation delay (160ms),
   recovery (8 seconds), inert locking and pageshow recovery remain. Sound
   assets/buttons and notifications unchanged. Targeted CorePages/UI tests:
   41 passed; initial two failures were stale cache-version assertions, updated
   to the actual shared asset versions without weakening ordering assertions.
   JS syntax passed. Full entry/browser/performance gates remain NOT_STARTED.
   Rollback: revert this scoped commit; no data changes. Commit 501444b;
   final targeted run including new removal assertion: 42 passed.
2. Inert payload scaffold: VERIFIED locally; three tests pass. Reference
   markup extracted only up to pathIntro; no later flows copied. Django gettext
   owns both locales, with the source Persian text in core/locale/fa. No DB
   queries in the payload renderer. Staff/non-home excluded. No live homepage
   activation yet. Catalogue compiled with Django compilemessages; no migration.
   Commit 761a1a5.
3. Scene/camera: targeted source and Node contracts pass; browser acceptance
   still pending. Camera constants, scene dimensions, colours, 200 depth
   particles/50 room dust motes and all five panels copied from reference.
   Gateway begins 11.1s, final clock 12.5s. Adaptations: scoped CSS/IDs, site
   font, no animated leaf blur (explicit transform/opacity-only constraint),
   progress scaleX rather than width, deterministic particle velocity sampled
   from camera(t-1/60), timeline-clocked leaf animations. No later route flows.
   Inert JSON markup is not actual server DOM. Runtime remains unactivated.
   Commit cab3515.
4. Gateway/controls: implemented, browser gate pending. Navigation is a real
   link to localized start/assessments; both intro flows remain out of scope.
   Focus trap, restoration of original inert/aria-hidden values, immediate
   skip/Escape, pause, hidden-tab suspension, pagehide cleanup and reduced-motion
   change recovery included. RAF stops at 12.5s (reference runs forever).
   No body overflow mutation/scrollbar shift. Localhost-only entry_seek query
   pauses at a deterministic time for browser testing; ignored on production.
   Node syntax and deterministic scene contracts pass. No network/audio calls.
   Commit eade774.
5. Display/cooldown: PARTIAL overall, policy tests VERIFIED. Reload takes
   precedence over same-origin referrer; back_forward always excluded;
   reduced motion skips the intro entirely (uninterrupted access, no motion).
   Fourth start in 90s stores a 5-minute cooldown even though no assets load.
   Unavailable/corrupt storage cannot lock the homepage. Staff and non-home
   routes never receive the payload. CSS/JS load only after window load; an
   8-second asset timeout restores the regular page without an overlay.
   Shared loader consumers' cache versions updated together: components v8,
   site-shell v12; otherwise standalone shells could cache the obsolete loader
   selector. Their existing assertions now match this same shared version.

### Exact source / differences / preserved scope

Readable reference SHA256:
`ce6d1fb230fc0dca162ac85f41034804d26527132518804378edb98153a97eac`.
Copied only the entry scene/styles/timeline, not mock homepage, replay,
pathIntro, options, tutorial or database-driven content. Django gettext owns
the new copy; no client translation dictionary. Scoped IDs/classes prevent
site collisions; palette respects explicit rvion-theme or system preference.
Source constants and 11.1s gateway timing retained. Required differences are
listed above; animated blur is omitted, so background panels are sharper than
the prototype. This is NOT claimed as a visually identical/owner-approved
delivery. Source nested `.path span` styling also reduces CTA contrast and
title hierarchy; preserved rather than silently redesigned, still needs review.
The new intro invokes no sound. Existing welcome sound is an independent
startup module, not a connection to the removed overlay; its module, button
and notification sound remain byte-identical (existing sound can still run).

### Tests and browser evidence

- `.venv/bin/python manage.py test core.test_entry core.tests.CorePagesTests core.test_ui_system core.tests_seo_contract --verbosity 1`: **73 passed**.
- `node core/tests_js/entry_scene.test.cjs`: passed timing, deterministic seek,
  finite narrow-screen camera, no network/audio, no filter/width animation.
- `node core/tests_js/entry_policy.test.cjs`: passed admission, fourth-start
  persistence, cooldown expiry, malformed/unavailable storage, two-asset loader.
- `node core/tests_js/navigation_loader.test.cjs`: passed delayed reveal,
  background lock, pageshow/failsafe recovery, reduced motion and exclusions.
- `node --check core/static/core/js/{entry,site-shell}.js`: both passed separately.
- `manage.py check`: zero issues; `makemigrations --check --dry-run`: no changes;
  `git diff --check`: clean. No migration executed.
- Raw homepage metadata comparison against isolated b390e02, using identical
  copied local data: FA and EN title/description/JSON-LD/canonical/hreflang
  unchanged; normal homepage has neither overlay DOM nor entry JSON payload.
- 32 screenshot captures at .8/3.6/7.5/12.5s: fa/en × light/dark ×390×844 or
  1440×900. DOM: scrollWidth equals viewport in every capture, correct dir,
  controls >=44px, no Persian characters in EN. Representative views inspected
  (not claimed as full visual acceptance of every capture).
- Browser: six-step gateway focus cycle stays inside dialog, Escape returns
  the accessible homepage, pause/resume aria-pressed toggles; no console errors
  or warnings observed. Capture files: `/tmp/rvion-entry-20261009/screenshots/`.
- Full isolated committed-candidate suite **NOT_RUN**: stopped at explicit
  performance gate. It must run once after the blocker is fixed, not now.
- No push/CI/deploy/SSH, permanent migrations, protected gallery/editor edits,
  nginx/traffic changes, extra HTTP API/analytics or external assets.

### Size / performance gate — failed evidence retained

At final preview: entry.css 16,599 bytes raw / 4,419 gzip; entry.js 11,604 raw /
4,782 gzip (9,201 gzip total, comfortably below 30KB; slight final CSS byte
count can change with checkpoint comments). Font data was not copied.

Command used for each measurement: `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' PATH=/opt/homebrew/bin:$PATH npx --yes lighthouse http://127.0.0.1:PORT/fa/ --quiet --chrome-flags='--headless --no-sandbox' --only-categories=performance --output=json --output-path=/tmp/rvion-entry-20261009/NAME.json`.
Baseline first run on 8165 before edits, runs2/3 on isolated b390e02 at8166;
active after runs on8165. Same local database copy, Lighthouse mobile defaults.

| Capture | LCP ms | TBT ms | CLS |
|---|---:|---:|---:|
| before-1 | 4569.46 | 1623.31 | 0 |
| before-2 | 4121.43 | 1335.22 | 0 |
| before-3 | 4214.07 | 1277.99 | 0 |
| baseline median | 4214.07 | 1335.22 | 0 |
| after-1 active intro | 4673.05 | 1503.82 | 0.3531 |
| after-2 containment experiment | 4202.81 | 1275.18 | 0.7665 |

After-1 exceeded current before median by10.89% LCP/12.63% TBT. The second
attempt improved timings but still failed CLS; its containment change was
removed, not accepted. These are two different candidate revisions, NOT a
three-run after median. Per explicit stop condition, no third after or final
approval fabricated. Historical 4500/600/0 baseline was not reproduced: current
legacy welcome-sound startup dominates TBT (after-1 long task1357ms); sound
behavior remains out of scope. Main 3D room movement is attributed in the
layout-shift trace; ordinary page geometry/scrollWidth staying stable does NOT
satisfy the CLS gate. Normal automatic activation was disabled as containment.

### Server protection design ONLY — P1-3/P4-1 still DEFERRED

Propose an nginx `limit_req_zone` keyed by trusted real client address, applied
only to public HTML (e.g.2req/s plus a measured short burst), NOT static assets,
health, payment callbacks or authenticated workflows. First audit Arvan trusted
proxy/real-IP handling; incorrect trust can throttle all customers together or
allow spoofing. Trial logging/dry monitoring before enforcement, then rollback
by removing limit_req and reloading the prior validated nginx configuration.

Optional short anonymous-home cache (e.g.10s) requires a separate owner decision:
bypass any authenticated/session/CSRF/private response, never cache Set-Cookie
or customer-specific HTML, explicit locale/cache invalidation, purge on change.
Current middleware writes anonymous sessions/traffic, so safe caching requires
policy/architecture work beyond this intro. Do NOT implement it or change
analytics/cookies now. Rollback: remove home-cache rule and purge cache.

### Continuation / rollback

Resolve source-compatible compositor/CLS behavior and nested-span contrast
before automatic activation. Then complete three AFTER measurements, reference
visual comparison and full isolated suite once; owner visual acceptance remains
separate. Local preview is not deployment evidence. Commit list begins
501444b,761a1a5,cab3515,eade774; final guarded checkpoint is the commit titled
`feat: add entry admission guard with performance-blocked local preview`.
Rollback only these scoped commits in reverse, preserving all unrelated work;
do not reset the repository or apply the preserved stash blindly. No database
rollback required. Protected stash/bundle remain intact.

### Mobile entry gateway follow-up — 2026-10-09

Status: mobile layout VERIFIED locally; automatic rollout/deploy BLOCKED.
Owner now expressly authorized commit/deploy; this does not turn the failed
performance requirement into a passing result. Project card is first/top on
<=760px phones, assessment card below; desktop remains side by side. The
direct/reload admission policy is already implemented and was re-exercised in
a temporarily activated test server. Default activation remains disabled.

Files: core/static/core/css/entry.css; core/templatetags/entry_ui.py (CSSv2);
core/test_entry.py; core/tests_js/entry_scene.test.cjs; these two living reports.
Commit: `fix: stack mobile entry gateway actions and preserve CTA contrast`.
Targeted command: `.venv/bin/python manage.py test core.test_entry
core.tests.CorePagesTests core.test_ui_system core.tests_seo_contract --verbosity 1`
→73 passed. `node core/tests_js/entry_scene.test.cjs`, `entry_policy.test.cjs`
and `navigation_loader.test.cjs`→all passed. `manage.py check`→0 issues;
`git diff --check`→clean. Browser FA390, EN320 and EN1440: correct card order,
no horizontal overflow, readable CTA/title, direct entry/reload and dismissal.
Proof: /tmp/rvion-entry-20261009/mobile-gateway-stacked.jpg.

Performance diagnostic candidates (all reverted, NOT release evidence):

| Candidate | LCP ms | TBT ms | CLS | Result |
|---|---:|---:|---:|---|
| Paused WAAPI camera |4521.54|794|0.6671|FAIL |
| Zero-size room origin |4061.95|720|0.7548|FAIL |
| Zero-size world+room origins |4534.31|873|0.4109|FAIL |

The latter attribution moved to the laptop screen; changing empty-container
bounds alone did not solve the scene's layout instability. Source geometry and
camera code are restored. No measurement suppression or waived threshold.
One NO_NAVSTART run was rerun; no final three-run median/full suite was claimed.
Premium audit (strict) exited1:55 existing gallery findings, outside this diff,
not triaged or masked. No protected gallery files were touched.

Read-only SSH attempts: connection closed, then20-second bounded timeout.
No production command/release/migration/restart, push or deployment completed.
Next: fix the actual scene performance issue and finish the final gate, then
official snapshot-backed release with live checks when SSH is available.
Rollback: revert only this mobile correction commit; no database changes.

## Entry CLS/audio diagnosis — measured, not inferred (2026-10-09)

Status: diagnosis VERIFIED; fixes VERIFIED locally; activation/release BLOCKED.
Owner superseded deployment authorization and the earlier5% tolerance: no
push/deploy/migration, and final active LCP/TBT may not exceed no-intro control.
No new commit in this phase; HEAD f7b404d. Prior uncommitted projection/encoding
corrections preserved; no redesign or protected gallery changes.

### Method and control (step1)

Chrome/Lighthouse13.5, default mobile simulated throttling, same local data.
Serial successful runs; no concurrent agent browser/tests/builds during batches.
Other OS/user activity is not controlled; localhost is not production/RUM.
An initial control run failed NO_NAVSTART; retained as control-no-intro-1.json,
then the entire clean batch was restarted. Failed runs do not enter medians.

Common exact command, substituting PORT/NAME as listed:
`CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' PATH=/opt/homebrew/bin:$PATH npx --yes lighthouse http://127.0.0.1:PORT/fa/ --quiet --chrome-flags='--headless --no-sandbox' --only-categories=performance --output=json --output-path=/tmp/rvion-entry-20261009/NAME.json`.
Control8168: `RVION_ENTRY_ENABLED=off .venv/bin/python manage.py runserver 127.0.0.1:8168 --noreload`.
Active8167: same command with RVION_ENTRY_ENABLED=1 and port8167, process-only.
Before captures already existed from b390e02 before splash removal; they are
historical measurements, not freshly rerun or claimed simultaneous controls.

| Revision/capture | LCP ms | TBT ms | CLS |
|---|---:|---:|---:|
| Before removal, before-1 |4569.46|1623.31|0|
| Before removal, before-2 |4121.43|1335.22|0|
| Before removal, before-3 |4214.07|1277.99|0|
| **Before removal median** |**4214.07**|**1335.22**|**0**|
| After removal, intro OFF, control-no-intro-clean-1 |3932.35|725|0|
| After removal, intro OFF, control-no-intro-clean-2 |4054.95|761|0|
| After removal, intro OFF, control-no-intro-clean-3 |4051.90|698|0|
| **After removal, OFF median** |**4051.90**|**725**|**0**|

Conclusion: all six CLS values are zero; splash removal is not supported as
the cause of the observed intro shifts. Timing differences alone do not prove
that removal caused the TBT decrease (non-simultaneous measurements/OS noise).

### Source trace (step2)

Used PerformanceObserver({type:'layout-shift',buffered:true}) before page render
in a disposable f7b404d checkout, not product instrumentation. CPU4x,390x844,
normal full playback, no seek and no input.129 shift entries; every source was
inside #rvion-entry, zero homepage sources, zero hadRecentInput entries.
Full node/previousRect/currentRect/time JSON:
`/tmp/rvion-entry-20261009/original-layout-shift-sources.json`.
Counts below count source appearances, not additive CLS or distinct entries.

| data-entry-id | Appearances | First–last time ms |
|---|---:|---:|
| char |6|565.10–714.50|
| mug |6|565.10–714.50|
| room |100|749.90–4317.10|
| scr |23|933.90–4249.90|
| cap |1|2835.80|
| laptop |9|4649.20–4915.00|
| world |1|5732.20|

Examples (x,y,width,height): mug at565.10ms:
(345.011,399.321,26.195,28.758)→(366.507,399.116,23.493,28.843).
Screen at933.90ms: (0,125.547,390,464.804)→(0,124.904,390,465.713).
Caption at2835.80ms: (0,695.008,390,90)→(0,677.008,390,109.266).
Some room/laptop source rects are clipped to the full viewport and therefore
equal despite a non-zero entry.value; do not infer no shift from clipped rects.

Insertion observer:493.20ms, position=fixed/inset=0px, entry CSS already loaded.
Original loader appends JS only after stylesheet.onload, then constructs DOM;
no evidence for unstylized insertion/homepage reflow. Original camera rewrites
world.transform every frame, screen --tilt changes rotation, typed() replaces
glass.innerHTML; captions switch content and change intrinsic height. Source
measure() sets size variables at mount/resize, not on animation frames. No
font-family/font-size switch after ready exists in this code. Existing CSS
keyframes animate only transform/opacity. The 3D parent's projected paint bounds
and text relayout are implicated by source trace and isolation below, not by
an invented animated width/top rule.

### CSS-loaded/hidden theory and independent ablations (steps3–4)

In disposable checkout only: root inert template has hidden and inline
position:fixed;inset:0; hidden removed immediately before insertion AFTER CSS
load. This strengthens an ordering already present. No instrumentation script
in Lighthouse runs. These experimental changes are not product changes.

| Independent experiment | LCP ms | TBT ms | CLS | Conclusion |
|---|---:|---:|---:|---|
| Guarded insertion run1 |4665.19|1259.70|.67058|FAIL|
| Guarded insertion run2 |4373.26|1176|3.14751|FAIL|
| Guarded insertion run3 |4639.05|1272.63|.66812|FAIL|
| Disable typed text only |4184.35|1075.23|.03986|Large reduction, not zero|
| Disable captions only |4274.94|1208|.79321|Not sufficient|
| Suppress size-variable writes only |4382.94|1076|.64913|Not sufficient|
| System-font diagnostic only |4063.91|854.48|.76442|Not sufficient|

Ablations are single diagnostic runs, NOT three-run acceptance measurements or
proof of precise contribution percentages. Each resets all other features to
guarded original HEAD, not cumulative deletion. Captures: guarded-original-{1,2,3}
and ablation-{typed,caption,measure,font}.json; the last four URLs have temporary
?cls_probe=NAME, no entry_seek. User reference text/geometry is NOT removed.

Prior pending fix retains camera coordinates but projects moving visual planes
individually under static layout/paint-contained parents. This separates 3D
paint-bound propagation from text relayout; reserved5em caption height removes
the independently observed caption shift. Native browser post-fix full playback
observer:0 entries, CSS loaded/fixed inset at1616ms. Full zero-entry record:
`/tmp/rvion-entry-20261009/fixed-layout-shift-sources.json`.
Geometry reads/size variables are only mount/resize; animation writes transforms
and opacity (plus visibility/accessibility/content transitions), never animated
width/height/top/left/margin/font-size. No metric-observer suppression, iframe,
motion preference override, threshold waiver or removal of reference content.

Localized inert HTML is stdlib gzip/base64 encoded (<5KB payload) and native
decoded after CSS load. Codec absence/failure/deadline/navigation race leaves
the ordinary home accessible. No new request/library/HTTP cache/privacy policy.
Older Safari without DOMMatrix/DecompressionStream skips the intro; actual
older-device Safari coverage NOT_RUN.

### Audio timing change (step5) and final strict gate

Original after-1 bootup-time attributes total1356.816ms/scripting1355.912ms to
welcome-sound.js, not guessed from a generic document long task. Now no load-time
playWelcome call or AudioContext creation; first pointer/keydown/click unlocks.
Existing welcome four-second window/session/mute and toggle behavior retained;
late interaction unlocks future notifications but never auto-plays welcome.
Background notifications before interaction return false, not queued. Normal/
urgent frequencies, gains, resume, toggle labels/preferences are regression tested.
No audible aesthetic judgment or native phone-push audio proof is claimed.

Both final control and active use the new audio code and matching data/runtime;
all six are normal navigation, no seek/observer instrumentation/interaction.

| Final capture | LCP ms | TBT ms | CLS |
|---|---:|---:|---:|
| lazy-audio-control-1 |4192.87|178|0|
| lazy-audio-control-2 |4007.06|131|0|
| lazy-audio-control-3 |3971.50|0|0|
| **Control median** |**4007.06**|**131**|**0**|
| lazy-audio-active-1 |4250.09|247|0|
| lazy-audio-active-2 |4414.63|165|0|
| lazy-audio-active-3 |4351.70|77|0|
| **Active median** |**4351.70**|**165**|**0**|

New gate: **FAIL**. CLS0 in all three, but active LCP+8.60%, TBT+25.95% vs
the matched control. Sound absent from bootup-time's reported expensive-script
items; this is not a claim of zero total sound-script work. Despite substantially
lower overall TBT, do not activate on the superseded5% baseline gate. Setting
RVION_ENTRY_ENABLED defaults0; off/0 keeps payload absent. Preview1 is local only.

### Tests, files, rollback and continuation

`.venv/bin/python manage.py test core.test_entry core.tests.CorePagesTests core.test_ui_system core.tests_seo_contract --verbosity 1`:73/73 passed.
`node core/tests_js/{entry_scene,entry_policy,navigation_loader,welcome_sound}.test.cjs`
(each executed separately):all passed. Scene projection test is structural;
native geometry/zero CLS evidence is separate, not a mocked numerical proof.
`node --check` for entry/site-shell/welcome-sound:pass; `manage.py check`:0 issues;
`makemigrations --check --dry-run`:No changes detected; `git diff --check`:clean.
32 final captures FA/EN×light/dark×390/1440×.8/3.6/7.5/12.5:zero horizontal
overflow/invalid native matrices. Representative visuals inspected, not claimed
all-pixel comparison. Normal entry/reload, pause/resume/resize, Escape and reduced
motion verified; no console errors. Focused sound tests establish API/waveform,
not subjective hearing. No full isolated suite while release gate BLOCKED.

Files currently modified: core/static/core/{css/entry.css,js/entry.js,
js/site-shell.js,js/welcome-sound.js}; core/templatetags/entry_ui.py;
arvion/settings/base.py (default-off switch); core/test_entry.py;
core/tests_js/{entry_scene,entry_policy,welcome_sound}.test.cjs;
core/templates/core/{base,flow_base}.html; management_portal/v2/base.html;
contracts/contract_base.html; crm_orders/{specialist_wizard,specialist_done}.html
(shared version strings only); this report and CURRENT_STATE.md.
Protected gallery files/stash/bundle/customer records untouched. All changes
uncommitted; no push, deployment, production operation or permanent migration.
Read-only SSH started before the owner's new instruction was terminated before
completion. No later SSH attempted. No cron/background monitoring added.
Rollback: keep switchoff and restore only reviewed scoped hunks when authorized;
no broad reset or database rollback. Next permitted step is remaining LCP/TBT
diagnosis/optimization, then a fresh matched3+3 gate, not public activation now.

## Piece 2 — phase 1 server vocabulary (2026-10-10): VERIFIED locally / programme PARTIAL

Owner authorizes local commits only. No push/deploy/SSH/migration/new model.
The preceding Piece1 working tree was saved separately as328630f after73 Python
tests and four Node contracts passed. That supersedes its historical
"uncommitted" wording above, not its failed public LCP/TBT activation gate.

Phase1 files:core/order_paths.py, core/order_gateway.py, core/order_summary.py,
core/order_wizard.py, core/views/base.py,
core/templates/core/project_start.html,
core/templates/core/includes/order_gateway.html,
core/test_order_vocabulary.py, this report and CURRENT_STATE.md.
Associated local commit subject:`feat: add closed order-scene vocabulary and server catalogue`.

Palette8/look6 are explicit closed sets, independent of existing gallery
theme/personality semantics. Server JSON uses TOPICS/CATEGORY_FEATURE_KEYS/
demo_config_labels/crm_choices/ADDONS/CONSULTATION, never duplicate feature
inventories. Empty entry has no implicit preference. final_form_url revalidates
even direct callers. Topic links, fallback GET forms and consultation carry the
two preferences; final existing lead/specialist summary fields show bilingual
labels, not editable new fields. request_type precedence is unchanged.
Brand/phone/arbitrary query text is not included in the catalogue or handoff.

Red evidence BEFORE implementation:
`.venv/bin/python manage.py test core.test_order_vocabulary --verbosity 1`
7 tests:3 failures,3 errors,1 pass (missing allowlists/JSON/summary/handoff).
Green exact command:
`.venv/bin/python manage.py test core.test_order_vocabulary core.test_order_paths core.test_order_gateway core.test_order_handoff core.test_order_ui --verbosity 1`
32/32 OK,1.575s; disposable test DB destroyed. Also:
`.venv/bin/python manage.py check` →0 issues;
`.venv/bin/python manage.py makemigrations --check --dry-run` →No changes detected;
`git diff --check` →clean. No full-suite run at this small server-only checkpoint.

Browser gate BLOCKED: selecting known localhost8167 preview tab first required
an explicit browser; the explicit iab selection was denied by browser security
policy (reported protocol restriction despite the supplied http URL). No
workaround attempted. Therefore prototype journeys, new visual implementation,
screenshots, CLS/gzip measurements and phases2–5 are NOT verified or complete.
No new animation assets have been added or enabled. Need authorized browser
access before implementing exact visual parity with the owner's reference.
Do not confuse the earlier Piece1 screenshot/performance evidence with Piece2.

Protected gallery/article files, stash/bundle and permanent DB unchanged.
P1-3/P4-1 remain DEFERRED; no analytics/session/cookie/cache/CSP change.
Rollback:revert only this phase1 commit; no schema or data rollback required.
Next:reference browser journeys → wizard → introductions → DB-backed exam
options → accessibility/performance validation. Check feature-selection handoff
through the existing validated adapter; do not invent a free-text query channel.
# Piece 2 — phase2 order studio checkpoint (2026-10-10)

Status: implementation VERIFIED locally; final matrix/performance NOT_RUN.
Files: core/order_wizard.py, views/base.py, project_start.html, new scoped
order-scene.css, order-scene.js/state.js, test_order_scene.py and Node contract;
DESIGN/UX/current-state updated. Protected gallery files untouched.
Tests:37/37 targeted Python tests PASS (order scene/vocabulary/paths/gateway/
handoff/UI), Node state/edit/topic-reset/payload contract PASS; JS syntax PASS,
git diff --check clean. Initial new recovery test failed because seeded test
restaurant templates existed; isolated fixture deactivation corrected the test,
not product behaviour. First Node fixture had a missing bracket, corrected.
Browser: Chrome390×844 actual FA flow from palette through jewellery features
and review, then ecommerce review; topic labels, private brand text and real
capability names inspected. Review column-reverse clipping was reproduced and
replaced by normal-order flow; no horizontal overflow observed. Full matrix
and permanent screenshot evidence deferred to phase5, not claimed here.
No database migration/production access/push/deploy. Rollback only this phase's
scoped commit; no database rollback. Phase1 baseline efea14d retained.
# Piece 2 — phase3 path introduction checkpoint (2026-10-10)

Status: implementation VERIFIED locally. Phase2 commit9437671.
Files: assessments/catalogue.py; path_intro tag/assets/CSS/JS; entry CTA URLs,
project/list includes, order-scene coordination, targeted intro tests.
Commands: manage.py test core.test_path_intro core.test_entry core.test_order_scene
(12/12 PASS); node core/tests_js/path_intro.test.cjs and entry_scene.test.cjs
(PASS); node --check path-intro.js; diff check clean.
Chrome390px project opening inspected: fixed grid background, animated form,
six-step journey, skip always visible. Direct/reload omit the consumed flag.
The payload is scoped to two destinations; elsewhere no assets are emitted.
Public entrance is still default-off. No activation, migration or release.
Read-only local exam facts: English50/75, Python50/70,7 sections each; active
local pools200 each. These are DB values, not constants in the animation.
Prototype claims adjusted: no guarantee of AI scoring (actual scoring in
assessments/services.py is rule-based); page-exit/copy/timing evidence is not
conclusive cheating; welcome attempt requires an eligible new account, accepted
terms and one credit total (accounts/views.py and redeem_welcome_assessment).
Certificate verification and recorded-answer explanations exist in current
models/services/routes; no promise of a formal language qualification is made.
Rollback: revert scoped phase3 commit; no data rollback. Final visual/performance
matrix is still phase5, not implied by these representative checks.
# Piece 2 — phase4 official exam options (2026-10-10)

Status: implementation VERIFIED locally. Phase3 commitc333c99.
Files: assessments/catalogue.py/views.py/list.html, new exam-options CSS/JS,
core/test_exam_options.py; existing public-catalogue test fixture updated to
the owner-required official slug instead of exposing an arbitrary test exam.
Assertions strengthened: arbitrary/private slug must not be offered. Pricing,
checkout, attempts, bank contents and grading are untouched.
Tests: manage.py test core.test_exam_options core.test_path_intro
assessments.tests.AssessmentCommerceTests →40/40 PASS. Expected mocked SMTP
exception was logged in the recovery test; no actual email/SMS sent. Syntax
and diff clean. Constant3-query public facts helper tested; no question/answer
content returned. Unknown/external/inactive selections never redirect.
Browser: English mobile option selection correctly reached
/en/assessments/english-placement-a1-c1/about/, not the list or pricing.
Teacher focus is conditional on published bank version≥5, matching the curated
teacher_v5 upgrade; the title itself remains the owner's current DB wording.
Speaking/live teaching are explicitly not claimed. General English is absent.
Final mobile/desktop/theme/language matrix, gzip and full suite remain phase5.
No push/deploy/migration. Rollback this scoped commit; no data rollback.

## Piece 2 scene/motion corrective checkpoint — 2026-10-10

Status: implementation VERIFIED local; overall programme PARTIAL (existing
strict-gallery audit/public-intro activation gates unchanged). Single-agent
self-review, not independent approval. No SEO metadata or business flow changes.
Files: core order-scene.js/css, new order-scene-art.js/order-scene-motion.js,
project_start.html script loading, two new core/tests_js contracts, DESIGN.md,
UX-CONTRACT.md and existing status records. Reference is specification, not copied
runtime. Canonical warm contrast palette and actual feature catalogue retained.
Evidence: `python manage.py test core projects leads.tests --verbosity 1`:
232/232 PASS. `python manage.py test core.test_order_scene core.test_order_paths
--verbosity 1`:10/10 PASS. Node order_scene_motion.test.cjs (also state contract)
and order_scene_art.test.cjs PASS; syntax checks, manage.py check and diff clean.
Cycle cadence, eligibility/pause, stale callbacks/timer cleanup and closed query
payload tested. No full all-app suite rerun and no migration check requiring a DB
write. Permanent local database, customer records and production untouched.
Browser: actual Chrome responsive390x844/1280x800,fa,light/dark;60 own +60
reference screenshots at `/tmp/rvion-piece2-correction-20261010/`, index.html
provides eight side-by-side sheets. Palette code/page, six looks, topic before/
after, restaurant/clinic intro, booking/catalog motion, review inspected. Brand
live update, swipe, previous/next, pause, reduced motion, intro Skip and navigating
away during motion checked. Root-mounted mobile overlays fix paint containment
clipping found during comparison. Actual iPhone/Safari remains NOT_RUN.
Gzip: five studio assets23577 bytes; conservative10 assets33073 (<45000).
Final Lighthouse mobile: run1 CLS0.004297689/LCP4218ms/TBT88ms;
run2 CLS0.002625170/LCP4231ms/TBT239ms;
run3 CLS0.004220957/LCP3959ms/TBT44.5ms. JSONs final-lh-{1,2,3}.json in evidence
folder. Layout-shift sources are fallback project-start h1 and header brand;
reported cause Web font loaded (Vazirmatn), not os-* scene nodes. Not a zero-CLS
claim or waiver of the earlier control-relative activation gate.
Premium strict audit:55 unchanged pre-existing actionless gallery-button errors;
protected files intentionally untouched, so this gate is not PASS.
Local commit: the commit containing this checkpoint (see Git log).
Not run: SSH/push/deploy/migrations, customer handoff submission, full suite.
Rollback: revert only this correction commit; no data rollback is needed.

# International English editions — 2026-10-12

Status: VERIFIED, published online. Owner explicitly approved
publication of English adaptations for all8 existing FA articles. USD figures
are global benchmarks or clearly labelled workload calculations, NOT converted
Iranian prices, binding Rvion offers or changes to checkout. FA texts unchanged.
References checked2026-10-12: https://clutch.co/web-developers/pricing (rate context),
https://www.salesforce.com/sales/pricing/ (paid editions$25–$550/user/month),
https://syndicode.com/blog/how-to-build-a-crm/ (vendor$50k–$300k custom-build band).
Clutch-based workload ranges are our illustrations, not surveyed sector averages.
Medical/privacy references: HHS HIPAA overview; W3C WCAG2.2; applicable local legal
review required. Technical learning answers use official Django5.2, not bank items.
Files: eight blog/english_content/*.md; blog/english_editions.py; command
publish_english_articles; blog/test_english_editions.py; ops/publish_english_content.py;
this report and CURRENT_STATE. No gallery, template, image, model or migration edits.
Validation: manage.py test blog core.tests_seo_contract109/109; subsequently
manage.py test blog.test_english_editions11/11; check0; makemigrations --check
--dry-run no changes; py_compile and diff checks pass. No full-suite rerun for
content-only release; prior unrelated full-suite evidence is not reused as new.
Release: content-only import under existing production runtime, NOT deployment
of the unapproved home performance commits. Default no-write dry-run; existing
published rows required; all validations before atomic writes; existing EN URLs
cannot change; private backup readback and unchanged non-EN field/tag comparison.
Rollback: restore only slug_en/title_en/summary_en/body_en from before.json by pk
in an atomic transaction; keep FA/shared fields and runtime unchanged.
No push, migration, customer-data mutation, paid-price change or flags activation.
Content commit116daf0. Remote archive SHA256 verified; dry-run8 updates, apply8,
repeat0 updates/8 unchanged. Every non-EN field and tag ID preserved within the
locked transaction. Backup0600:
/srv/arvion/backups/english-116daf0-20261012T083621Z/before.json.
Runtime source remainsdab858f clean, env checksum unchanged, services active.
All eight live pages200, descriptions match, titles<=60, description90–155,
one h1, self canonical and FA hreflang; all cover URLs200 image/*. All8 EN URLs
in sitemap and listing. /tmp/rvion-english-live-results.json records the evidence.
Browser1280×800 EN listing8 cards;390×844 cost detailLTR, no Persian body or
horizontal overflow. Screenshots /tmp/rvion-english-{desktop,mobile}.png.
Final documentation commit also corrects an extra EOF blank line introduced in
116daf0; the initial staged diff check reported it (not a product/test failure).
No Search Console submission or physical-device claim. Public URLs:
- https://rvionai.com/en/blog/corporate-website-cost-2026/
- https://rvionai.com/en/blog/custom-website-vs-template/
- https://rvionai.com/en/blog/custom-or-ready-made-crm/
- https://rvionai.com/en/blog/english-teacher-assessment/
- https://rvionai.com/en/blog/clinic-website-design-online-booking/
- https://rvionai.com/en/blog/academy-website-structure-webinar/
- https://rvionai.com/en/blog/enterprise-crm-development-cost-stages/
- https://rvionai.com/en/blog/django-interview-questions-with-short-answers/
