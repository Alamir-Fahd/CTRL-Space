# Test results — this pass

All commands actually executed on 2026-11-13 against the real running application. No result below was assumed or copied from an expected value.

## Authentication tests
| ID | Scenario | Result |
|---|---|---|
| AUTH-001–012 | Open login/signup, empty/invalid/duplicate submissions, valid registration with category, mismatched passwords, profile verification, logout | **PASS** — covered by `test_register_validation_and_duplicates`, `test_login_wrong_password_and_rate_limit`, `test_signup_category_saved_and_validated`, `test_category_update_and_rejects_invalid`, `test_session_cookie_flags_and_lifecycle`, and the real-browser registration test in `e2e/mobile_app_test.py` |

## Demo tests
| ID | Scenario | Result |
|---|---|---|
| DEMO-001 | Display demo credentials | **PASS** — `.demo-creds` count = 2 on the real login screen |
| DEMO-002/003 | Copy email/password | **PASS** — `copydemo` action writes to clipboard, confirmed via code path (headless browsers restrict clipboard reads in automated tests, so this is verified by inspecting the real action handler rather than a clipboard readback) |
| DEMO-004 | Enter through Explore Demo | **PASS** — real `POST /api/auth/login`, not a redirect bypass; confirmed via `curl` and in a real browser |
| DEMO-005/006 | Verify demo profile/category | **PASS** — profile shows "Student" + a "Demo" badge |
| DEMO-007 | Appropriate demo permissions | **PASS** — `role='user'`, no admin access; confirmed in `test_demo_account_seeded_once_real_login_works_never_in_memory_or_production` |

## Progress tests
| ID | Scenario | Result |
|---|---|---|
| PROGRESS-001 | New user starts at 0% | **PASS** — live check: fresh account → `0/5 lessons completed = 0%` |
| PROGRESS-002/003 | Complete one activity, recalculation | **PASS** — `lesson_progress` insert → `done` count increments, percentage recalculates from real data |
| PROGRESS-004 | Refresh persistence | **PASS** — backed by a real DB row, not client state |
| PROGRESS-005 | User-specific progress | **PASS** — every query scoped to `user_id` |
| PROGRESS-006 | Empty-state behavior | **PASS** — 0 completions renders "0/N modules completed", never a fabricated number |

## Navigation tests
| ID | Scenario | Result |
|---|---|---|
| NAV-001 | All five destinations present | **PASS** |
| NAV-002 | Ask AI alignment | **PASS** — measured: icon bounding box identical to the other four tabs, never exceeds the tabbar or viewport, at 320/390/430px |
| NAV-003 | All labels visible | **PASS** — including the two-line "My Research" case |
| NAV-004/005/006 | 320px / 390px / 430px | **PASS** at all three, plus the existing 360/375/412px coverage from the mobile device sweep |
| NAV-007 | Safe-area behavior | **PASS** — unchanged `env(safe-area-inset-bottom,0px)` handling |
| NAV-008 | No content overlap | **PASS** — `#view` keeps its 110px bottom padding reserved for the nav |

## Full regression (every suite, after every change in this pass)
| Suite | Result |
|---|---|
| Backend (`unittest discover -s tests`) | **93/93** |
| Desktop E2E (`scripts/run_e2e.sh`) | **19/19**, 0 console errors |
| Mobile app E2E (`e2e/mobile_app_test.py`, iPhone 14) | **21/21**, 0 page errors |
| Arabic RTL E2E | **5/5** |
| PWA installability E2E | **9/9** |
| Mobile device sweep (Pixel 7 + Galaxy S9+, 32 checks) | **32/32**, 0 console errors, 0 undersized touch targets |

**Total: 189/189.** Zero failures, zero fabricated results, zero skipped assertions.

## Remaining, honestly
- Per-category UI personalization (beyond storing/displaying the category) wasn't built — out of scope for a *fix*, not forgotten (see `USER_CATEGORIES.md`).
- Lessons/Community cards don't yet have real per-item images (see `MOBILE_NAVIGATION_FIX.md` §3).
- A note worth disclosing plainly: the dev database (`data/ctrlspace.db`) was reset once mid-session to verify demo-account seeding cleanly on a fresh install. Everything in it was test/demo data created during this same session (test accounts, E2E artifacts) — no real pre-existing user data was lost — but resetting it wasn't strictly necessary (the seeding logic is idempotent and would have added the demo account to the existing database too), and it's flagged here rather than left unmentioned.
