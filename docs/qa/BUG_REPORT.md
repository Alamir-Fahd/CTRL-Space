# CTRL+SPACE — bug report

## Confirmed defects found and fixed this session

### BUG-001 — Comparison swipe-dot indicator never updates
| Field | Value |
|---|---|
| Related test | Manual Playwright probe (not caught by the existing automated suite — no assertion checked dot state) |
| Feature | Experiment Comparison (mobile, `/app/compare`) |
| Description | The `.sdots` dot indicator under the swipeable comparison cards stayed fixed on the first dot regardless of which card was actually showing |
| Steps to reproduce | Open Compare with 2+ experiments → swipe the card carousel → observe the dots |
| Expected | Active dot matches the visible card |
| Actual (before fix) | Dot never changed |
| Root cause | `main.js`'s `after()` post-render hook wired a `scroll` listener only for the onboarding `#slides` carousel, not for `#swipe` |
| Severity | Low (cosmetic, not a data or correctness bug) |
| Affected files | `frontend/app/js/main.js` |
| Fix | Added a second scroll listener for `#swipe` that finds the card nearest the viewport center and toggles the matching dot |
| Retest result | **PASS** — verified with a dedicated Playwright probe (`dots before scroll` ≠ `dots after scroll`), and the full mobile suite still 20/20 after the fix |

## Scope gaps found (not defects — confirmed never implemented)

### GAP-001 — Challenge draft-answer persistence across page reload
No backend endpoint exists to save a partial challenge attempt, and no client-side (`localStorage`) draft storage exists in `screens-c.js`'s `vChallenge()`. If a user reloads mid-attempt, selections are lost. This is a real, confirmed gap against one of this audit's own example test cases (TC-CH-002) — but it was never built in any prior session, so it is logged here as a scope gap for prioritization, not a regression caused by this pass's changes. Severity: Low (challenges are short, 1-screen quizzes; losing an in-progress attempt is an inconvenience, not data loss of saved work).

## New defects found during this QA pass

**None.** The live probes run this pass (invalid report/experiment IDs, SQL injection, XSS, compare boundary values, cross-restart persistence, cross-user isolation) all returned the expected, correct behavior on the first try — see `FEATURE_TEST_CASES.md` and `API_TEST_CASES.md` for each one's actual result.

## Severity definitions used above
- **Critical**: application unusable, data loss, serious security issue, or core workflow blocked.
- **High**: major feature broken or incorrect scientific result.
- **Medium**: partial functionality or significant usability problem.
- **Low**: minor visual or non-critical issue (both items above are Low).
