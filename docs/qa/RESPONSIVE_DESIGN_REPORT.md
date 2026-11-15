# CTRL+SPACE — responsive design report

## Viewports actually tested this pass
390×844 (mobile baseline), 768×1024 / 1024×768 (tablet portrait/landscape), 1366×768 (laptop), 1440×900 (desktop), 1920×1080 (wide desktop) — against the desktop site. The 320–430px mobile range and the mobile app client's own 320–1280px sweep were already extensively covered in prior sessions (`docs/MASTER_CHECKLIST.md` §0, `docs/qa/MOBILE_TEST_REPORT.md`) and were spot-checked again, not fully re-run, since nothing in this pass touched mobile-width CSS.

## What changed
One targeted change: `.content main`, `.topin`, `footer div` in `frontend/css/app.css` — `max-width:1180px` (flat) → `max-width:min(1520px,94vw)` (scales with viewport, capped). This is a `min()`-based fluid pattern, consistent with what this audit's own Part 4 suggested (`clamp()`/`min()` for fluid dimensions) rather than a fixed pixel override.

## Why `min(1520px, 94vw)` and not something else
- `94vw` guarantees the container can never exceed 94% of the viewport, so it cannot cause horizontal overflow at any width, including the odd intermediate sizes between named breakpoints.
- `1520px` caps how wide it gets on very large monitors, so it doesn't stretch indefinitely on a 4K display.
- At laptop widths (1280–1366px) this is nearly a no-op (94vw ≈ 1203–1284px vs. the old flat 1180px) — the fix is scoped to where the problem actually was (1440px+), not a wholesale redesign.
- Paragraph-level text elements already had their own smaller `ch`-based max-widths nested inside this container (52–80ch), so widening the outer container doesn't make body text harder to read — it only gives more room to things that don't have their own cap, like the comparison table.

## Breakpoints already in place (unchanged)
`frontend/css/app.css` has an existing `@media (max-width:860px)` breakpoint for the sidebar → mobile nav transition; the mobile app (`frontend/app/app.css`) is mobile-first with no desktop breakpoint at all by design (intentionally stays phone-width on desktop). Neither was touched.

## Verification
- Measured `main`'s actual rendered width via `getBoundingClientRect()` before (1180px) and after (1520px) at a 1920px viewport — a real DOM measurement, not a visual guess.
- Re-screenshotted the comparison-results view (3 experiments selected, the most column-dense real view in the app) at 768/1024/1366/1440/1920px — zero overflow, visibly less cramped at the wide end.
- Re-ran the full desktop E2E suite (`scripts/run_e2e.sh`) after the change: **19/19, 0 console errors** — confirms the fix didn't break any interaction, form, or navigation test.
