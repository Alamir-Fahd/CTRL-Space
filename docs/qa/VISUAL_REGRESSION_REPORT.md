# CTRL+SPACE — visual regression report

## Before/after comparison performed
Real Playwright screenshots, not descriptions, captured before and after the `.content main` width fix, at matching viewports. Saved to a local scratch directory during this session (not committed — they're working artifacts, not test fixtures the repo needs to carry forward).

| Screen | Viewport | Before | After | Verification method |
|---|---|---|---|---|
| Home | 1920×1080 | `main` = 1180px, ~420px empty right margin | `main` = 1520px, balanced margin | `getBoundingClientRect()` + visual screenshot |
| Compare (3 experiments selected) | 1920×1080 | Table columns cramped against the old cap | Noticeably wider columns, text wraps more naturally | Visual screenshot, before/after |
| Compare (3 experiments selected) | 768/1024/1366/1440 | — | 0 overflow at every size | `scrollWidth` vs `clientWidth` check |
| Admin dashboard | 1920×1080 | *(false positive investigated — see below)* | Clean, no overlap | Visual screenshot after fixing the test's own wait condition |
| Research Discovery | 1440×900 | Not previously screenshotted at this width | Clean, 6-field filter row balanced | Visual screenshot |
| AI Assistant | 1024×768 | Not previously screenshotted at this width | Clean, chips wrap into 2 rows | Visual screenshot |
| Mobile app (`/app`) | 1366×800, 1920×1000 | Not previously screenshotted past 1280px | Correctly stays centered, phone-width — by design, not a bug | Visual screenshot + overflow check |

## False positive caught and ruled out before being reported as a bug
First-pass admin screenshots at 1920px appeared to show a stray "Loading research data…" watermark overlapping the System Health card. Before reporting this as a defect, investigated the cause: the test script navigated to `/admin` via a full page load without waiting for the desktop site's splash screen (`#splash`) to finish its fade-out and `remove()` from the DOM (`frontend/js/app.js`'s `launch()` keeps it for up to ~1.3s). Fixed the *test script* to wait for `#splash` to detach, re-captured, and the page was clean. This is recorded here specifically so it isn't mistaken for a real UI bug in the application — it was not; the application was never actually broken.

## Regression tests re-run after the CSS change
| Suite | Result |
|---|---|
| Desktop E2E (`scripts/run_e2e.sh`) | **19/19**, 0 console errors |
| Horizontal-overflow checks (automated, this pass) | **38/38** page×viewport combinations, 0 overflow |

Mobile app, Arabic, PWA, and backend suites were not re-run for this specific change because it touched only `frontend/css/app.css` (the desktop site's stylesheet) — the mobile app has its own separate stylesheet (`frontend/app/app.css`) that was not modified, and no backend code changed. This is stated explicitly rather than claiming a full re-run that wouldn't have exercised the changed code anyway.

## Remaining visual items not changed (and why)
- The Admin Overview's "System Health" card has some unused whitespace below its content at 1920px — acceptable, not a layout bug (nothing overflows, clips, or misaligns); filling it would mean adding new content/widgets, which is outside this audit's "fix layout problems" scope and risks the "don't add decorative elements" rule.
- A true on-screen-keyboard occlusion test and physical-device rotation test were not performed (browser automation limitation, disclosed in `docs/qa/MOBILE_TEST_REPORT.md`).
