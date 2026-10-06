# Public demo ordering UI contract

## Reference storefront variant (phase 2)

One fixture catalog/transient basket serves preview/full: product detail →
finish/size/quantity → basket → delivery/review → sample completion → original
design settings. No Lead, payment or real order is created. Cart never enters
the design enquiry/storage; reload resets it and this boundary is visible.
Native dialogs provide title/heading focus, inert background, Escape and
opener restoration. Desktop splits; phones stack/scroll within viewport.
Native selects retain the established platform-owned popup policy.
Inline quantity errors are associated with their fields. Invalid edits cannot
advance; stock checks include the basket's existing quantity. FA/EN copy and
numbers use explicit Toman units. Empty/no-results/unavailable states offer
recovery. Payment-off hides checkout and explains enabling it; catalog-off
disables the basket opener and closes store dialogs. These local actions
introduce no remote loading/offline/session workflow; real enquiry keeps its
existing server/session/idempotency authority.

Scope: home → gallery → live sample → enquiry. This does not redefine the
assessment, contract, authentication or admin workflows. Visual context:
`DESIGN.md`. Maintained domain evidence: `projects/models/demo.py`,
`projects/views/projects.py`, `leads/views/contact.py`, `projects/tests.py` and
`leads/tests.py`; these remain authoritative for validation and isolation.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | native select/radio/checkbox | demo-configurator.js | platform native popup; authored radio labels | keyboard and phone browser |
| Form | existing DemoConfigureView and demo-configurator.js | server validated session-bound selections | preview enquiry form | projects + leads tests |
| Scrollbar | global token baseline and editor CSS | runtime tokens + demo-studio.css | stable desktop settings gutter | computed styles and phone scrolling |
| CRUD | DemoConfigureView → LeadCreateView | unique submission_token; session isolation | create selection then existing enquiry | idempotency/isolation tests |

## Outcomes and recovery

- Sector goals: `sector_catalog.py` resolves six categories into three existing
  `projects/demo_briefs.py` goal values each. The same canonical brief select
  owns buttons, visible chapter, URL/session state and submitted enquiry.
  With no chosen goal, an illustrative first chapter appears with a
  visible undecided notice; it does not silently set a goal. Reset/clearing
  restores that state. The hero above the controls is not rewritten (avoids
  changing its height and moving the active controls). Unknown/foreign goals remain
  rejected by the existing server. Recommendations are explanatory only and
  show whether the existing feature checkbox is selected. They never mutate it.
  Detail disclosures are native; goal buttons use pressed states and retain
  focus. Without JS, all chapters/details remain readable, goal buttons remain
  disabled and the existing order select stays authoritative. These previews
  collect no health, address, payment or contact data and create no booking,
  enrollment or product order. Only the unchanged design form submits.

- Homepage journey: `home-studio.js` owns only decorative chapter switching;
  `home_journey.html` owns real navigation and copy. No scroll interception,
  account mutation or submission. Desktop stage follows the visible chapter;
  mobile graphics stay in normal document flow. JavaScript failure leaves
  every real link usable; reduced motion removes transitions.
- Scene button affordance: visible border/fill and minimum 44px height. Native
  disclosure summaries use the same touch target; bold hero actions must retain
  inverse text contrast despite the hero's higher-specificity text rules.

- Home sample switch is transient browsing, not an order mutation. No account
  or storage is required. No JS leaves the first sample and full library usable.
- Demo choices use the existing query/sessionStorage state. Server POST remains
  authoritative; the redesign never creates a new draft or data lifecycle.
- Only Continue submits the design choices. No illustrative booking, basket or
  jewellery interaction creates a real order/payment/medical record.
- Invalid/stale selections reuse existing localized inline recovery. Duplicate
  submissions reuse the same idempotency contract, not a new UI heuristic.
- Sample filters/search are intentionally transient illustrative datasets;
  clearing restores the current category and focuses search. IME composition
  does not trigger incomplete filtering. No remote search requests.
- Native illustrative selects accept platform popup appearance/locale. No date
  picker, authored combobox, toast provider or destructive operation is added.
- Mobile settings: modal sheet, inert background, bounded scroll, Escape,
  focus trap and return to the actual opener; desktop is a nonmodal region.
  Native disclosure summaries participate in the focus trap. Colour/style is
  initially expanded; capabilities and enquiry details can be opened separately.
- Enquiry preferences are optional bounded choices: category-specific goal,
  scope, content readiness and preferred timeline. Native select popups remain
  platform-owned. A timeline is a preference, not a delivery promise. Unknown
  values are rejected by the server; free text/contact data is never stored in
  this preference object. Older submissions retain their original JSON shape.
- Preferences survive full-preview/return and changed-token recovery. They are
  resolved into bilingual frozen labels on the case and shown in manager detail
  and plaintext export. Account-bound snapshots accept the optional bilingual
  label pair with strict row-count, key and length validation; legacy snapshots
  remain valid. Session ownership and submission tokens are unchanged.
- Persian and English use the active page locale. Customer brand values are
  user content, not interface translation. Fictional sample art is decorative.
- No changes to permissions, billing, legal text, account concurrency or
  retention policy. No customer data needed for visual QA.
