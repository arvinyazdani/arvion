# SEO phase report — Rvion

Date: 2026-10-07. Overall status: **PARTIAL — independent SEO work resumed**.
Single primary agent; self-review, not independent review.
Source request: `/Users/rwin/Documents/claud/rvionai.com-audit/AGENT-PROMPT.md`.
Baseline: `6977b30`; production runtime remains `63abbcd`.
Implementation commit: `4d22cc1` (`fix(seo): publish public assessment briefings in sitemap`).
This SHA applies to P1-1 and the partial P1-2/diagnostic evidence below. The report
hash finalization is a separate documentation-only checkpoint, not further implementation.

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
| P2-1 | NOT_STARTED | No Organization/WebSite graph work before Phase 1 resolves. |
| P2-2 | NOT_STARTED | No visible breadcrumb/schema changes. |
| P2-3 | NOT_STARTED | No Service schema/Offer added. |
| P2-4 | NOT_STARTED | No CRM SoftwareApplication or fabricated exam Course/ratings. |
| P2-5 | NOT_STARTED | No blog schema/model/migration change; author and modification metadata approval remains needed. |
| P2-6 | VERIFIED (local) | Template-only unique titles/descriptions use demo title/category/tagline/fit label; protected view untouched; contract passes. |
| P2-7 | NOT_STARTED | No schema-contract extension; no sample graph invented for the report. |
| P3-1 | NOT_STARTED | No blog publishing/content/TOC work, no article or permanent draft created. |
| P3-2 | NOT_STARTED | No invented FAQ or audience copy; database/copy inventory deferred. |
| P3-3 | NOT_STARTED | No unique demo introductions supplied/applied; no noindex change. |
| P3-4 | NOT_STARTED | No entity page/footer edits. |
| P3-5 | NOT_STARTED | H1 proposal deferred at stop boundary; homepage untouched. |
| P4-1 | BLOCKED | OWNER DECISION DEFERRED; analytics, language session behavior and cache policy must not change. |
| P4-2 | NOT_STARTED | No Lighthouse run or before/after performance numbers; no CSS consolidation. |
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
