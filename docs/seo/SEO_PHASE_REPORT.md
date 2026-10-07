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

## Updated public HTML URLs (source changes, not deployed)

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
