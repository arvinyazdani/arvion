# Rvion code-mark — concept v1

Status: owner selected the concepts for local integration (2026-10-11).
Created with the built-in image generation tool, not the fallback CLI.
Concept history below remains unchanged; production-facing local integration
now uses a clean vector reconstruction, not these large concept bitmaps.

## Integrated asset ownership

- `core/templates/core/includes/code_mark.html`: approved silhouette rebuilt
  as a deterministic R/code vector; live `Rvion` text uses the local font stack.
- `core/static/core/icons/app-icon-maskable.svg`: same path, square orange/ink
  master with generous safe margins. `core/static/core/favicon.svg`: rounded tile.
- `scripts/build_brand_icons.cjs`: compiles the master into PNG192/512/iOS180
  using development sharp. No application/runtime dependency was added.
  Example: `NODE_PATH=<development-node_modules> node scripts/build_brand_icons.cjs`.
- Header/footer, loader/install guide, assessment/receipt, management and
  standalone customer shells reuse the vector. Service-worker shell cache v6.
- Original concepts retained as design evidence; they are never loaded by UI.
- Installed-device icon refresh is OS-controlled and not physically verified;
  existing iOS installations may require removing/re-adding after deployment.
  No production replacement/deployment is performed in this phase.

## Deliverables

- `app-icon-concept.png`:1254×1254, full-bleed orange, dark R/code mark,
  no wordmark, intended for a later iOS/Android mask-safe export.
- `logo-light-concept.png`:1983×793, orange mark + dark `Rvion` wordmark
  on warm ivory. This is NOT a transparent asset or an SVG.

The R connects the brand name to custom coding through angle-bracket cutouts
and a diagonal leg. Palette targets retain the site's orange #ff6b35,
ink #0b1220 and ivory #f4f1ea; generated bitmap colours are not asserted to be
pixel-exact tokens. The two selected outputs were visually inspected. A separate
transparent generation was rejected for edge artefacts and is not included.

At the original concept handoff, production preparation was still separate:
vector master, light/dark checks, small-size/PWA exports and integration. The
integration section above supersedes that historical status. No originality/
trademark clearance claim is made. Concept-only work needed no runtime tests;
integration verification is recorded in CURRENT_STATE.md.

## Final generation prompts

### App icon

Use case: logo-brand. Asset type: a single square production-intent app icon concept for Rvion, a Persian/English bespoke website and CRM programming studio (Persian brand آرویون). Create one original, extremely clean, premium flat geometric monogram. The mark must clearly read as a capital R at small sizes, with the language of code subtly built into its shape: a strong upright stem, angular softened upper bowl, and a decisive diagonal forward-slash leg, accompanied by balanced minimal angle-bracket cuts integrated into the geometry, not a generic R surrounded by separate icons. Think considered custom typographic engineering, not clip art. One bold dark ink #0b1220 symbol on a uniform full-bleed orange #ff6b35 square background. Optical centering, broad solid strokes, generous 22% outer safe-area for iOS/Android masks, large open negative space, perfectly crisp vector-like edges. The graphic fills a square canvas edge-to-edge in orange: do not draw a smaller rounded icon tile, the OS supplies the corner mask. No text or wordmark in this app icon; no border, no frame, no shadow, no texture, no glow, no gradient, no mockup, no perspective, no 3D, no watermark. Original distinctive shape, restrained and trustworthy, recognisable as R and programming.

### Light logo (app icon supplied as geometry reference)

Use case: logo-brand. A clean horizontal logo asset for Rvion software development studio, on a completely uniform warm ivory #f4f1ea background. Use input image1 only as the exact R monogram geometry reference: preserve its bold R silhouette and both angle-bracket negative-space cuts, but render the standalone R in pure flat orange #ff6b35; all cut-outs must be the same clean ivory as the background. Put the exact word "Rvion" (capital R, lowercase v i o n) on the right in solid dark ink #0b1220, carefully kerned bold contemporary geometric sans-serif with softened squared details, a distinct i dot and clear lowercase letters. Symbol height roughly 1.5 times word cap height. Optically balance and center one horizontal lockup, ample clean margin, wide 2.5:1-ish canvas. Highest priority: immaculate smooth vector-like edges and perfectly uniform flat color; absolutely NO specks, NO red flecks, NO noise, NO gradients, NO textures, NO shadows, NO outline, NO glow. No rounded-square tile around the mark. No tagline, no decorative elements, no mockup, no watermark, no additional words. This logo must visibly be the same identity as the supplied app icon, recolored for a light website header.
