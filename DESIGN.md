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
samples. Editor: sample plus a compact settings rail on desktop; at 760px and below the
existing modal sheet is the canonical editor. Samples use container queries
so their layout follows their actual width, not the outer viewport alone.
Marketing sections use 80px desktop/42px phone rhythm. Existing data and
session-bound order handoff remain authoritative.

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

| Role | Runtime owner | Consumers |
|---|---|---|
| Brand/action | tokens.css: --action-brand-* | home primary CTA |
| Text/surface/focus | tokens.css semantic roles | home and editor chrome |
| Art | projects/demo_scenes/art.html + demo-studio.css | home/gallery/editor/full |
| Demo theme/personality | demo-configurator.js | preview and full sample |
| Sample hero | projects/demo_scenes/hero.html | editor/full |
| Settings sheet | demo-configurator.js | phone editor |
| Category detail content | projects/demo_briefs.py + demo_scenes/story.html | preview/full |
| Order preferences | projects/demo_briefs.py | server validation, manager export/case |
| Public footer | core/includes/footer.html + footer-studio.css | public shell |

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
