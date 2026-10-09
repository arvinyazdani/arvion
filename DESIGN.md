---
version: alpha
name: Rvion
description: A website-first design studio with live business-specific samples and a quiet ordering workspace.
colors:
  primary: "#ff6b35"
  ink: "#0b1220"
  background: "#f4f1ea"
  surface: "#ffffff"
  muted: "#5f6878"
  focus: "#b9380d"
typography:
  sans:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
  latin:
    fontFamily: "Segoe UI, Tahoma, Arial, sans-serif"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace"
rounded:
  sm: "10px"
  md: "14px"
  lg: "22px"
spacing:
  section: "80px"
  compact-section: "42px"
components:
  primary-action:
    height: "44px"
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
  preview-art:
    rounded: "{rounded.md}"
    backgroundColor: "{colors.surface}"
---
# Rvion design context

## Editorial reader — 2026-10-09

Public articles use a content-driven header, a 700px desktop reading column,
18px/1.95 body text and a separate 17px phone layout. The existing published
body and SEO summary remain authoritative; presentation removes only an exact
duplicated title prefix. Heading IDs are generated after sanitization, with a
sticky desktop contents rail and a collapsed native disclosure on phones.
Callouts use an accent border and quiet tint, never a decorative warning icon.
Code remains literal, LTR and independently scrollable. Font preloads and image
dimensions reserve the final geometry. Copy-link is disabled until its local
enhancement initializes; denied clipboard access reveals a selectable link.
No tracking, cookie, publication, author or modified-date policy is introduced.
New cover candidates use navy #12161f, ivory #f4f1ea, grey #a9b0bd and orange
#ff6b35; central safe-area line illustrations are versioned assets, not an
implicit production replacement. Owner visual approval remains separate from
the primary agent's technical self-review.

Phase 4 enquiry receipt uses existing card/border/text/action tokens, a
two-column definition list on desktop and a single readable column on phones.
Values wrap rather than hiding overflow; the separate-tab settings action has
a 48px minimum target and explicit recovery instructions. FA/EN labels are
resolved from shared sector data; technical hex colours remain ASCII. Light
and dark palettes follow the global theme, not the sample's private palette.

## Overview

North Star: a working design showroom, not a software feature brochure. The
customer can recognise their business, see a direction and change it before
enquiring. The user explicitly prioritised website orders on 2026-10-05;
assessments keep a clearly labelled separate route. Brand: آرویون / Rvion.

Hybrid register: the home/gallery are expressive brand surfaces; the editor is
a restrained product form. Its signature is original category-specific vector
art, shared between the home, gallery and live preview, rather than anonymous
gradient mockups. No invented clients, ratings, or success statistics.

Audience: nontechnical Persian/English customers, often on phones. The homepage
leads with website selection, then process, custom systems and assessments.
Anti-references: admin-looking marketing pages, generic feature-card walls,
tiny nested phone mockups on phones, and endless animated decorative blobs.

Runtime ownership is **Model B**: `core/static/core/css/tokens.css` is canonical.
This document mirrors it; no generated token system or new dependency is added.

Research: [Shopify theme design requirements](https://shopify.dev/docs/storefronts/themes/store/requirements)
support business-specific structure, realistic content and understandable
settings; [Framer's template marketplace](https://www.framer.com/marketplace/templates/)
informed browse/preview separation. These are design references, not copied code
or a change to our Django stack.

Homepage journey reference (2026-10-05): [Apple's iPhone landing page](https://www.apple.com/iphone/)
was read and visually inspected for focused chapters, large graphical subjects
and clearly differentiated actions, not copied assets or typography.
[WebKit's scroll animation guide](https://webkit.org/blog/17101/a-guide-to-scroll-driven-animations-with-just-css/)
informed progressive enhancement and reduced-motion behavior. Rvion uses its
own lightweight illustrations and an IntersectionObserver, not scroll hijacking,
video downloads or a new animation dependency. Three paths remain distinct:
website design (primary), tailored CRM/clinic systems, and assessments.

## Colors

Orange is the action accent, ink the primary text, paper the light canvas.
Shared semantic tokens remap dark mode. On detail pages the chosen demo accent
tints the whole studio canvas; the site header, page and global footer share
that same canvas, while the Rvion logo keeps its brand orange. Live demo palettes are separately owned
by `PALETTES` in `demo-configurator.js`; their light sample canvases deliberately
stay light inside dark studio chrome, making the prospective site legible.
Vector art uses fixed illustrative materials; a restrained tint follows the
selected accent, while buttons/text use calculated contrast colours.

## Typography

Locally hosted Vazirmatn handles Persian; established Latin and mono stacks
handle English and technical metadata. No network font dependencies. Marketing
titles have a distinct scale; product instructions stay modest. Persian body
line-height 1.9–2, hero headings 1.3. Italic styling is not applied to Persian.

## Layout

Reuse the existing shell (1160px max; editor expands to 1400px). Home: two-column introduction/showroom,
then a three-column library; phones get stacked introduction and full-width
samples. The public demo gallery is a single editorial showroom: a clear
introduction, direct category anchors and an asymmetric, art-led concept grid
that gives the website/storefront samples first attention. The grid becomes one
legible column on phones, with category navigation remaining thumb-scrollable.
Editor: sample plus a compact settings rail on desktop; at 760px and below the
existing modal sheet is the canonical editor. Samples use container queries
so their layout follows their actual width, not the outer viewport alone.
Marketing sections use 80px desktop/42px phone rhythm. Existing data and
session-bound order handoff remain authoritative.

The homepage offers immediate route buttons before its hero. Its three-chapter
journey uses a bounded sticky graphical stage on desktop; phones receive one
in-flow graphic per chapter with no sticky obstruction. All copy and real links
are available without JavaScript. Reduced motion disables graphical transitions.
Demo collections own explicit grid tracks; phone dish names and prices occupy
separate rows, and all scene buttons/disclosure triggers have a 44px minimum
height, visible borders and an explicit selected state.

Detail pages prioritise the sample, not repeated studio titles. Phones receive
an edge-to-edge sample, a five-colour quick strip and one obvious settings
action. Settings are native disclosures: colour/style, capabilities and enquiry
details. Seven categories have two domain-specific editorial sections, an
expandable FAQ and a sample footer with real anchors. The public footer has
one owner (`footer-studio.css`), compact navigation, contact and preserved legal
links; it is not a second marketing landing page.

## Elevation & Depth

Only the showroom/editor chrome uses elevation. Art and library content use
shape, composition and dividers; no card-within-card shadow towers. Dark mode
preserves visible boundaries and an orange primary action.

## Shapes

Runtime sm/md/lg radii map to 10/14/22px. Industrial demo personality deliberately
uses square corners, ruled edges and offset shadow; luxury uses generous space
and restrained buttons. These are sample variants, not global rebrands.

## Components

Public journal (2026-10-08): `blog/includes/card.html` and `journal.css` own
the shared cover/title/date/estimated-reading-time presentation across home,
list and related articles. Desktop home gives one latest article a larger
cover and two compact rows; phones retain the lead cover and thumb-sized rows.
The article library uses a three-column desktop grid, two columns on tablets,
and one full-width column on phones. Search/topic/page state stays in GET URLs.
The reading page uses a bounded sticky contents rail and <=760px body on desktop;
phones use an in-flow native collapsible contents list and 16px text, never a
sticky overlay. Sanitized headings get generated anchors; article wording is
unchanged. All semantic colors/font/motion resolve through core/tokens.css.
21st.dev's sumonadotwork Blog Cards informed text-led hierarchy; no React runtime,
remote font, hidden-hover cover or additional animation dependency was adopted.
No fabricated author, popularity, customer claims or read tracking is introduced.

Public shell phase 1 (2026-10-06): header actions use a quiet navigation row,
one orange project CTA, and native collapsible preferences (language/theme/sound).
Phones keep five quick destinations and an accessible menu with 52px primary
rows; preferences expand in-flow rather than creating a second overlay.
`public-shell.css` owns these public-shell refinements, scoped by
`data-public-shell` so standalone contract/exam/management shells keep their
geometry. Public actions share 48px controls and 14px corners, subtle colour
feedback instead of jumping shadows, local fonts and 16px form inputs.
The footer retains all legal/contact links, readable metadata and a full-width
phone CTA. The body owns the bottom-bar safe inset; the footer does not add a
second duplicate inset. No sample theme/personality or order data contract changes.

| Role | Runtime owner | Consumers |
|---|---|---|
| Brand/action | tokens.css: --action-brand-* | home primary CTA |
| Text/surface/focus | tokens.css semantic roles | home and editor chrome |
| Art | projects/demo_scenes/art.html + demo-studio.css | home/gallery/editor/full |
| Demo gallery | projects/demo_gallery.html + demo-gallery.css | public concept discovery |
| Demo theme/personality | demo-configurator.js | preview and full sample |
| Sample hero | projects/demo_scenes/hero.html | editor/full |
| Settings sheet | demo-configurator.js | phone editor |
| Category detail content | projects/demo_briefs.py + demo_scenes/story.html | preview/full |
| Order preferences | projects/demo_briefs.py | server validation, manager export/case |
| Public footer | core/includes/footer.html + footer-studio.css | public shell |
| Reference store | storefront_catalog.py + demo_store tag + storefront.css | ecommerce preview/full |
| Sample basket | storefront-model.js + storefront.js | ecommerce, memory-only |
| Sector goal chapters | sector_catalog.py + demo_sector tag + sector-experience.css | six non-store sectors, preview/full |

Reference shop phase 2: six home objects with original material illustrations,
not fake photography, ratings or discounts. Native product dialogs split art
and specifications on desktop; phones get a full-width stacked sheet. Finishes
and sizes update prices and dimensions. Cart/delivery/review/completion remain
sample-only, separate from the real design enquiry. Dialog actions inherit the
live sample palette and local fonts; the sample stays deliberately light in
dark studio chrome. All products remain visible on phones. Select popup
geometry is platform-owned; intrinsic selects/art must not expand the dialog.

Sector phase 3: restaurant, portfolio, corporate, clinic, learning and jewellery
each expose three domain-specific directions, backed by the existing enquiry
goal—not a second settings model. A plate, frame, blueprint, care cross, book
and faceted mark accompany readable fictional specification panels; these
are illustrations, not real assets/credentials. Fact labels, units, numbers,
lesson copy and quotation boundaries follow the page locale. Desktop splits
specifications/content; phones stack full-width, wrapping goal buttons with
48px minimum targets. Native disclosures keep the detail density manageable.
Selected goals update the chapter headline and direction immediately; the
hero above the controls stays stable to avoid scroll jumps. Capability
suggestions show current selection status and lead to the existing settings
sheet (or back to preview from full mode), never silently enabling features.
Live palette contrast remains owned by demo-configurator.js. Sector motion is
a short opacity/4px arrival, disabled with reduced motion; no scroll hijack.

Actions are semantic links/buttons with hover, pressed and visible focus.
Theme/personality are radio-like choices; features remain checkboxes.
The submit button preserves its existing idempotent server flow and busy
disable. Native selects/colour chooser remain platform-owned by deliberate
choice; custom popup geometry is not promised. See `UX-CONTRACT.md`.

Motion: a subtle art scale on intentional hover; no autoplay carousel, no
blocking introduction. Reduced motion disables transforms/transitions in the
new surfaces. Existing icon sprite remains canonical; ↗ signals navigation.

## Do's and Don'ts

- Do show a recognisable business scenario before editor jargon.
- Do label all content as fictional and keep interactions visibly sample-only.
- Do keep a single live state and send the same choices with the enquiry.
- Don't mix English interface copy into Persian or vice versa.
- Don't advertise estimates or contracts as final prices.
- Don't claim that vector illustrations are real photographs/client work.
