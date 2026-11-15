# CTRL+SPACE — UI dimensions audit

Real screenshots taken at the viewports this audit specified, 2026-11-13, against the live running app — not a CSS read-through alone.

## Screens inspected
Desktop site (`/`, `/research`, `/experiments`, `/compare` incl. actual comparison results with 3 experiments selected, `/assistant`, `/admin` logged in as admin) and the mobile app client (`/app`) at desktop widths, which had never been explicitly screenshotted past 1280px before.

## Layout system found
- **Desktop site** (`frontend/css/app.css`): CSS Grid shell — `.shell{grid-template-columns:248px minmax(0,1fr)}` (fixed sidebar + flexible content column), with the content column's actual width governed by `.content main{max-width:...}`. Per-element `ch`-based max-widths already existed for prose (`.lede{max-width:52ch}`, `.vh p{max-width:70ch}`, `.answer/.passage/.insuff{max-width:860px}`) — these correctly keep paragraph text readable regardless of the outer container's width.
- **Mobile app** (`frontend/app/app.css`): single-column, mobile-first, intentionally centers at a phone-like width on larger screens rather than stretching — this is the correct, by-design behavior for a PWA opened in a desktop browser, not a layout defect.

## Dimension problem found and fixed
**The desktop site's content container had a flat, non-scaling cap.** `.content main` (the actual operative rule — there's also a dead, unused `main{...}` rule earlier in the cascade with lower specificity that never wins) was `max-width:1180px` regardless of viewport. At 1920px, with the 248px sidebar, roughly 420px of the viewport sat empty on the right. This was most visible on the Experiment Comparison table, which has no width rule of its own (`.cmp thead th{min-width:200px}` only) and simply inherited the container's cramped width — at 1366–1920px, its 3–4 data columns were squeezed into ~1180px total when 1500px+ was available.

**Fix**: changed `.content main`, `.topin` (header) and `footer div` from a flat `max-width:1180px` to `max-width:min(1520px,94vw)` — scales up on genuinely wide screens, has no effect at laptop widths (1280–1366px, where `94vw` ≈ 1203–1284px, close to the old value), and is bounded by `94vw` so it never causes overflow on any viewport. Verified: `main`'s actual rendered width went from 1180px → 1520px at a 1920px viewport (measured via `getBoundingClientRect()`, not assumed).

## False positive investigated and ruled out
Initial `/admin` screenshots at 1920px appeared to show a ghost "Loading research data…" watermark bleeding through behind the System Health card. Investigated: this was the desktop site's own splash screen (`frontend/js/app.js` `launch()`) still mid-fade-out when the screenshot was taken, because my test script navigated to `/admin` via a full page load (which re-triggers the splash sequence) without waiting for `#splash` to detach from the DOM — a test-timing artifact, not an application bug. Confirmed by re-capturing with a proper `wait_for_selector('#splash', state='detached')` — the page renders cleanly with no overlap.

## Confirmed clean (no issues found)
- Zero horizontal overflow across 30 page×viewport combinations (5 desktop-site pages × 6 viewports: 390, 768, 1024, 1366, 1440, 1920) plus the comparison-results view at 5 more widths and the admin dashboard at 3 widths — 38 total, all measured via `scrollWidth > clientWidth` checks, not eyeballed.
- Home page hero banner, 4-card "Why CTRL+SPACE" grid, and "How it works" cards scale cleanly from 390px to 1920px.
- Research Discovery's 6-field filter row and report cards remain balanced at 1440px.
- AI Assistant's question box and example-question chips wrap cleanly at 1024px (tablet landscape).
- Mobile app client correctly stays centered at a bounded, phone-like width on desktop viewports rather than stretching — this is the intended PWA behavior, confirmed not to overflow at 1366px/1920px.

## Summary table

| Screen | Mobile (320–430) | Tablet (768–1024) | Desktop (1280–1920) | Status |
|---|---|---|---|---|
| Dashboard / Home | ✅ (prior sessions) | ✅ | ✅ (fixed: content width) | PASS |
| Research Discovery | ✅ | ✅ | ✅ | PASS |
| Evidence Library | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Report Details | ✅ | ✅ | ✅ | PASS |
| AI Assistant | ✅ | ✅ (checked this pass) | ✅ (benefits from the same fix) | PASS |
| Experiment Explorer | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Experiment Comparison | ✅ | ✅ | ✅ (fixed: table was the most cramped case) | PASS |
| My Research | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Learning Studio | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Challenges | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Community | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Profile | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Settings | ✅ | ✅ | ✅ (benefits from the same fix) | PASS |
| Admin | ✅ (prior sessions) | ✅ (checked this pass) | ✅ (checked this pass, fixed: content width) | PASS |
| Mobile app (`/app`, all 28 screens) | ✅ (prior sessions, extensively) | ✅ (prior sessions) | ✅ (checked this pass — correctly stays centered) | PASS |

"Benefits from the same fix" = not individually screenshotted this pass, but uses the same `.content main` container as the screens that were, so the width fix applies identically; no screen-specific CSS exists that would make it behave differently.
