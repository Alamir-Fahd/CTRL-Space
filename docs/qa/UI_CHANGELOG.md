# CTRL+SPACE — UI changelog (this audit pass, 2026-11-13)

## Files modified
- `frontend/css/app.css` — 3 rules changed (`.content main`, `.topin`, `footer div`), plus the already-dead unused `main{}` rule updated for consistency (never actually applied, see `UI_DIMENSIONS_AUDIT.md`).

## Components modified
- Desktop site's page shell (sidebar + content container) — the container that wraps every single desktop-site screen, so the fix applies uniformly everywhere rather than screen-by-screen.

## Change detail
```diff
- .topin{max-width:1180px;margin:0 auto;...}
+ .topin{max-width:min(1520px,94vw);margin:0 auto;...}

- main{max-width:1180px;margin:0 auto;...}          /* dead rule, never wins the cascade — updated for consistency only */
+ main{max-width:min(1520px,94vw);margin:0 auto;...}

- .content main{flex:1;width:100%;max-width:1180px;margin:0 auto}   /* the rule that actually applies */
+ .content main{flex:1;width:100%;max-width:min(1520px,94vw);margin:0 auto}

- footer div{max-width:1180px;margin:0 auto;...}
+ footer div{max-width:min(1520px,94vw);margin:0 auto;...}
```

## Responsive improvements delivered
Desktop-site content (every screen) now uses up to 1520px of width on large monitors instead of a flat 1180px, scaling fluidly via `min(1520px, 94vw)` rather than jumping at a fixed breakpoint. Most visible improvement: the Experiment Comparison table's columns are meaningfully less cramped on laptop/desktop screens.

## Screenshots captured (this pass, local scratch directory, not committed to the repo)
30 page×viewport combinations (5 pages × 6 viewports) for the general overflow sweep, plus 5 widths of the actual comparison-results view, plus 3 widths of the admin dashboard, plus 2 widths of the mobile app client at desktop sizes — 40 screenshots total, all inspected (not just overflow-checked) for at least the wide-desktop case of each screen.

## Tests executed
- 38 automated `scrollWidth`/`clientWidth` overflow checks — 0 failures.
- Desktop E2E suite (`scripts/run_e2e.sh`) — 19/19 after the change.
- One real `getBoundingClientRect()` measurement confirming the fix actually took effect (1180px → 1520px).

## Remaining issues / out of scope
- No remaining layout defects found. The one visual anomaly investigated (admin "ghost watermark") was a test-script timing issue, not an application bug — see `VISUAL_REGRESSION_REPORT.md`.
- Did not add new dashboard content to fill the Admin Overview's unused card whitespace at 1920px (would be a feature/content change, not a dimension fix).
- Did not touch the mobile app's CSS (`frontend/app/app.css`) — it has no desktop-width problem to fix; its centered, bounded-width behavior on large screens is correct by design.
- Real on-screen-keyboard occlusion and physical-device rotation remain untested (browser-automation limitation, previously disclosed).
