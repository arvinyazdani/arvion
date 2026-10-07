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
| P3-1 | NOT_STARTED | No blog publishing/content/TOC work, no article or permanent draft created. |
| P3-2 | NOT_STARTED | No invented FAQ or audience copy; database/copy inventory deferred. |
| P3-3 | NOT_STARTED | No unique demo introductions supplied/applied; no noindex change. |
| P3-4 | NOT_STARTED | No entity page/footer edits. |
| P3-5 | NOT_STARTED | H1 proposal deferred at stop boundary; homepage untouched. |
| P4-1 | BLOCKED | OWNER DECISION DEFERRED; analytics, language session behavior and cache policy must not change. |
| P4-2 | VERIFIED (measurement only) | Four valid local mobile Lighthouse runs, LCP/CLS/TBT/CSS below; no optimization or production claim. |
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
