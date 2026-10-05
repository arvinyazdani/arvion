# Public demo ordering UI contract

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
- Persian and English use the active page locale. Customer brand values are
  user content, not interface translation. Fictional sample art is decorative.
- No changes to permissions, billing, legal text, account concurrency or
  retention policy. No customer data needed for visual QA.
