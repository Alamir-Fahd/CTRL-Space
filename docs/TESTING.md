# Testing

All results below were produced by running the commands on 2026-11-12 (Python 3.12.3, Flask 3.1, Chromium via Playwright 1.63, Ubuntu container). Raw outputs are in `reports/`.

| Suite | Command | Result |
|---|---|---|
| Backend unit + integration | `python -m unittest discover -s tests -v` | **86 / 86 passed** (`reports/backend_tests.txt`) |
| Browser end-to-end | `bash scripts/run_e2e.sh` | **19 / 19 passed, 0 console errors** (launch, journeys A–F, every screen, structured assistant, comparison levels, gaps, demo mode, mobile), passed on 3 consecutive runs after the last code change. In the previous version one run printed an uncaptured snapshot, so an intermittent timing failure can't be ruled out (`reports/e2e.txt`, screenshots in `e2e/screenshots/`) |
| Retrieval evaluation | `python scripts/evaluate.py` | 12 answerable: gate pass 12/12, **mean recall@6 0.958, MRR 0.854**; 4 unsupported: **4/4 refused** (`eval/results.json`) |
| Legacy Phase 8 engine | `python -m unittest discover -s tests -t .` (in the original Phase 8 package) | 55 / 55 passed |

## What the backend suite covers

Health and stats; report listing, sorting, filtering, ranking and validation; hidden pending reports; no leak of admin-only fields; error shape and request IDs; search normalisation and ranking; unverified passages excluded; assistant grounded answer with fabricated citations removed; evidence gate blocks the AI call; model-declared insufficiency; invalid JSON and provider outage handled honestly; no-provider mode; input validation; rate limit; experiment states (missing ≠ zero); comparison warnings, unit mismatch and chartable fields; SQL integrity constraints; idempotent seeding; password hashing; registration validation and duplicates; cookie flags and session revocation; login failure and rate limiting; hashed tokens; collections CRUD, export and cross-user isolation; note limits; NTRS import end to end with a scripted NTRS and real generated PDFs (pending status, unverified passages, review, approval, search, audit, random storage names); non-PDF, metadata-only, bad ID, 404, ID mismatch, retries; chunk sizes; admin authorization (401/403); refusing to delete cited passages; security headers; no source disclosure; 64 KB body limit; production cookie requirement.

## End-to-end journeys

Home with live stats · ask with evidence · off-topic refusal · library search + filter + report detail + NTRS link · select three experiments and compare (warnings, chart, citation dialog) · experiment detail with missing values · register (weak password rejected), create collection, add report, save note, export Markdown and check its content · non-admin denied (UI and API 403) · admin wrong password then sign-in, overview, reports, review, audit log · unknown route and missing report · mobile home and compare with no horizontal scroll.

## v2 additions covered

Categories and temperature field; profile, preferences, password change (other sessions revoked), account deletion; activity history and recent items; notes list; lessons only cite verified passages (and seeding rejects unknown citations); challenge answers never sent to the browser, server-side grading, progress; community posts, replies, shared references, reporting, moderation hide/restore with audit; admin cannot change own role, last-admin protection, disabled accounts lose sessions and can’t sign in; experiment approval blocked by unverified evidence; analytics table holds no user IDs or text; v1 → v2 database migration in place.

## Competition release covered

Question analysis (fact / comparison / interpretation / prediction, variables, programs); evidence coverage rules (insufficient / partially / well supported, missing variables, hypotheses-only, single report, prediction cap); numeric grounding of generated text; structured AI answer with per-section citation validation and backward compatibility; refusal when the direct answer has no valid citation; retrieval-only structured evidence; unit normalization that keeps the original; comparison levels (context warnings, statement types, relationships only from findings of two or more experiments); corpus-scoped gaps that never claim verified absence; research brief; demo preflight; AI provider check.

## v3 additions covered

Discovery filters (year, material with escaped wildcards, evidence availability, sorting); oxygen basis, apparatus, measurement grouping, needs-verification state; saved items; experiment notes; comparison export; sessions list and revoke; history opt-out; personal data export; lesson objectives, related reports and navigation; challenge metadata and status; post editing; community recent; system health; extraction flagging; experiment rejection; upgrading an existing database never restores a passage an admin removed.

## Defects found and fixed during testing

| Defect | Fix |
|---|---|
| Experiments list empty: `"published"` in SQL double quotes resolved to the `reports.published` column | All SQL string literals switched to single quotes |
| Plurals not matched (`flames` → `flam`) | Rewritten stemmer; regression test `test_normalisation` |
| Library ranked reports by matched-word count | Ranks by best passage BM25 scores + title match |
| Markdown export could be cancelled (blob URL revoked immediately) | Revoke after 10 s |
| Collection items exported out of order | Order by insertion |
| Mobile header wrapped the logo and cut off the menu | Two-row mobile header |
| Duplicate "Not extracted" labels; unclear chart wording | Copy fixes |
| `create-admin` could not reset a password | Resets password and signs out sessions |
| v3: upgrading a database where an admin had removed a passage cited by a lesson crashed startup | Upgrade seeding is tolerant; passages cited by lessons/challenges can be flagged but not deleted |
| v3: material filter LIKE escaping was broken | Escape character changed to `!`; regression test |
| v2: E2E selectors clicked the share banner’s “Remove” button instead of “Post discussion” | Test fixed (app behaviour was correct) |

## Not tested

- Any real AI provider (no network in the build environment). **No claim is made about answer quality.**
- Live NASA NTRS imports (same reason).
- Windows: commands are standard Python, but were run on Linux only.
- A possible intermittent E2E failure (see above): if a journey fails, rerun and keep the FAIL screenshot in `e2e/screenshots/`.
- Load and concurrency beyond single-user use; backend-down banner in the browser; screen-reader testing.

## Troubleshooting

- `ModuleNotFoundError: flask` → activate the virtual environment and `pip install -r requirements.txt`.
- Assistant shows "No AI answer was generated" → set `CTRLSPACE_AI_PROVIDER` in `.env` and restart.
- Import fails with "NTRS could not be reached" → check internet access to ntrs.nasa.gov; NASA limits requests to 500 per 15 minutes.
- Locked out of admin → `python run.py create-admin EMAIL "Name"` with a new password.
- Start over → `python run.py reset-db` (deletes accounts and imports).

## Mobile device emulation (v3.1)

`python e2e/mobile_devices.py BASE_URL ADMIN_EMAIL ADMIN_PASSWORD` runs the app in **Chromium mobile device emulation** (Pixel 7 and Galaxy S9+ profiles: real viewport, pixel density, touch input and Android Chrome user agent). This is browser emulation, **not an Android emulator**: none was available in the build environment (no Android SDK, no KVM, no internet). Result: all steps pass on both devices with no console errors (`reports/mobile_devices.txt`, screenshots in `e2e/screenshots/mobile/`). A separate check found no sideways scrolling or zoom-out on 36 device/screen combinations (Galaxy S9+, Pixel 7, iPhone 14).

Defects found by this run and fixed: a filter dropdown and a long URL made pages wider than the phone, so Chrome zoomed the whole page out and taps landed off-target; on 320 px phones the top bar did the same on every page; checkboxes were 13 px (now 20 px with 40 px tap areas); in-page actions re-rendered the page and lost the scroll position; the fix for that briefly risked replacing text being typed, so typed text and focus are now preserved across refreshes.

### Running on a real Android emulator (team machine)

1. Install Android Studio → Device Manager → create a Pixel device → start it.
2. On your computer: `python run.py serve` (port 8000).
3. `adb reverse tcp:8000 tcp:8000`, then open Chrome in the emulator at **http://localhost:8000**. (Without `adb reverse`, use http://10.0.2.2:8000, but Chrome then can’t install the app because it isn’t a secure origin.)
4. Chrome menu → **Add to Home screen / Install app** to run CTRL+SPACE full-screen like a native app.


## Installable mobile app (v4.1)

`python e2e/pwa_test.py BASE_URL` on a Pixel 7 profile: **9 / 9 passed, no page errors** (`reports/pwa.txt`): Chromium installability check reports no errors, manifest parses cleanly, service worker controls the app, bottom tab bar, offline launch into a saved report with banner, honest error for an unvisited report offline, recovery online, install instructions in Settings. Phone suite still passes on Pixel 7 and Galaxy S9+ with the tab bar. Not tested: installation on a physical phone or Android emulator, and APK builds (no Android SDK or internet here).

Defect found and fixed: offline, the app stopped at the launch screen waiting for Retry/Continue; an installed app with saved data now opens straight into offline mode.


## Mobile application `/app` (v5)

`python e2e/mobile_app_test.py BASE_URL "iPhone 14"` and `"Pixel 7"`: **18 / 18 journeys passed on each, no page errors** (`reports/mobile_app_iphone.txt`, `reports/mobile_app_pixel.txt`). Covers all 28 screens: splash and backend check, onboarding persistence, registration validation (confirm password, terms, show/hide), login errors, password recovery without account enumeration, discover + search results + filter sheet, research details (save, offline download, citations), AI assistant (report scope, follow-ups, history, export), AI analysis, library (NASA images shown honestly as needing internet), collections (create, rename, describe), experiments and results, compare (all tabs incl. AI summary in retrieval-only mode), workspace and autosaving notes editor, learning, notifications, profile, edit profile, settings, offline (downloaded report readable offline, banner, reconnection), demo, about, help, tab navigation with back button, touch targets ≥ 36 px on every button, no horizontal overflow.

Defects found and fixed: the shared API client crashed on pages without the desktop offline banner (every mobile request failed); the chat composer let content show through above the tab bar and hid the scope button; the remove-scope button was 26 px (now 44 px); follow-up suggestions could be empty; history lacked per-conversation export; an outdated desktop test pinned the schema version.

Not tested: physical iPhone/Android devices, an Android emulator, native builds, live NASA Image Library and live AI providers (no internet here). All mobile results are **Chromium device emulation**.


## Arabic interface (v5.2)

`python e2e/mobile_ar_test.py BASE_URL`: **5 / 5 passed, no page errors** (`reports/mobile_arabic.txt`): language switch from onboarding, RTL layout, Arabic validation messages and tab bar, assistant labels in Arabic around verbatim English evidence, comparison notes in Arabic with no overflow, switching back to English. A coverage scan of every screen (signed in and out, all tabs) found no untranslated interface text; the remaining English strings are NASA titles, verbatim passages, experiment values, names and lesson/challenge content, which stay English by design. Fixed during testing: mixed-direction punctuation in user messages, one untranslated comparison label.

## Native packages

No APK or iOS build was produced or tested here (no SDK/Xcode/internet). The Capacitor project and GitHub Actions workflows are syntax-checked only (valid JSON and YAML).

## Full regression at v5.2

Backend 86/86 · desktop E2E 19/19 · website on phones (Pixel 7, Galaxy S9+) passing · installable app 9/9 · mobile app 18/18 on iPhone 14 and Pixel 7 · Arabic 5/5. All Chromium emulation.
