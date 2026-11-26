# AfyaHer design system and homepage direction

## Intent

A calm learning workspace with editorial clarity: the page begins the product.
Contemporary African innovation is expressed through useful, lightweight mobile
interaction and careful language, not decorative cultural motifs, stock portraits
or invented claims about African women. Brand fit is a design hypothesis to test.

## Existing foundation

Keep the AfyaHer wordmark, system sans-serif body, Georgia editorial headings,
Lucide icons, visible focus, skip link, shared navigation and existing routes.
Other screens retain the established cream/plum/mauve palette. This is a focused
homepage direction, not a migration of the entire product's visual system.

## Homepage palette

Scoped under `.clarity-home` in `frontend/app/globals.css`:

| Role | Value | Use |
| --- | --- | --- |
| Ink | `#193e36` | Headings, primary action, finder masthead |
| Muted | `#50625b` | Secondary text |
| Paper | `#fffdf8` | Finder and topic links |
| Rule | `#d6dad1` | Editorial separators; not control boundaries |
| Clay | `#9b4930` | Headline emphasis, small accent |
| Control boundary | `#6e8175` | Search field against white |
| Urgent text / surface | `#683321` / `#f6e9dd` | Static guidance with a text label and border |
| Trust surface | `#e8ede4` | Product limitations and source policy |

Color does not carry meaning alone. Disabled controls remain legible; visible
focus and forced-colors borders support alternate rendering. Formal WCAG 2.2 AA
conformance requires a full audit; do not equate these choices with certification.

## Typography, spacing and layout

Use installed system fonts: Georgia/Times for editorial headings, Arial/Helvetica
for body and controls. No font or image download is required. Responsive hero
heading up to 4.8rem, body around 1rem, supporting text 0.7–0.9rem. The actual
search input stays 1rem to avoid mobile input zoom. Short uppercase kickers are
supporting labels, not instructions.

Reuse the 1120px container. At desktop, pair editorial introduction with an
interactive guide finder. At 760px and below, stack them; retain direct condition
links and the urgent shortcut before the finder. Remove its decorative masthead
on mobile to bring the field forward. At 1000px, reduce gap and padding. Three
pathways use divided columns, becoming rows on mobile; avoid nested card grids.
Use a 4/8-based spacing rhythm with 20–26px panel padding. Corner radii 5–12px;
one offset solid shadow gives the finder depth without glass or gradients.

## Interaction and accessibility

One form action: Find a guide. Enter and pointer submission behave identically.
A visible label and described privacy/availability note explain the input. Empty
input disables submission; a 100-character limit bounds it. Results use a polite
live region. Clearing restores the default question links. Editing clears stale
results. No result is a medical interpretation. Every path resolves to an
existing page; no accounts, dead community buttons or invented approved sources.

Direct urgent guidance uses a named aside and an anchor target with tabindex -1.
It always exists and never depends on search terms. Retain the existing source
reference and warning that the notice cannot assess or rule out an emergency.

Interactive controls/rows target at least 44px. The existing reduced-motion
preference disables motion. This homepage introduces no decorative animation;
state changes are immediate. Focus scroll margins account for bottom navigation.
Use semantic headings, normal links and native input behavior, without custom
combobox keyboard handling. Test mobile navigation overlap and 200% zoom.

## Impeccable process

Consulted official docs on 12 November 2026:
- https://impeccable.style/docs/
- https://impeccable.style/docs/improve-design/
- https://impeccable.style/docs/context/
- https://impeccable.style/docs/critique/
- https://impeccable.style/docs/harden/

No Impeccable installation was found in the provided skill catalogue, local skill
paths or frontend binary directory. No installer, slash command, detector or
Impeccable skill was executed. Applied its documented context → critique →
focused refinement → edge-case review approach manually. PRODUCT.md captures
product boundaries; this document captures visual/interaction choices. Do not
represent these hand-authored files as generated Impeccable metadata.
