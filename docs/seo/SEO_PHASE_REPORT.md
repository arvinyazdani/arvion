# SEO phase report — Rvion

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
