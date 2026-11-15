# CTRL+SPACE — log of the project chat

Every request in order, what was delivered, and the decisions made. Status of each requirement: `MASTER_CHECKLIST.md`.

| # | Request | Delivered | Decisions / notes |
|---|---|---|---|
| 1 | Analyze the uploaded NASA.zip | Audit: two incompatible stacks, four data models, missing code, zero real NASA content, logo with NASA insignia; Phase 8 tests 55/55 | `docs/audit/` |
| 2 | “Make the app” | v1 single-page artifact (superseded) | |
| 3 | Full web app with all phases | v2 Flask + SQLite app: search, evidence assistant, experiments, compare, accounts, community, admin; real NTRS content | Real sources only; verified passages |
| 4 | Continue: package and document | Final report, 14 phase reports, docs, tests | |
| 5 | Review a 14-screen product sequence | Review given | |
| 6 | “Complete all app” | Completed screens and flows | |
| 7 | Screen-by-screen spec (Angular/Node/MongoDB) | v3 matched screen by screen | **Owner: keep Flask; keep Learning Studio, Challenges, Community** |
| 8 | “Run the app in the emulator” | Chromium device emulation (no Android emulator possible); 5 mobile bugs fixed | |
| 9 | Competition “final quality” instructions | v4: prioritization, structured evidence-first assistant, coverage, numeric checks, comparison levels, gaps, brief, demo mode, preflight, model-evaluation report | No unmeasured model claims; dense models blocked offline |
| 10 | “Run the app” | Ran from ZIP; demo journey OK; version fix | |
| 11 | “I want it as a mobile app, not web” | Installable PWA: service worker, offline, tab bar, install button | |
| 12 | “Is this a full mobile app?” | Honest answer: installable web app, not native | |
| 13 | Mobile master prompt + reference image | v5: dedicated mobile app `/app` in the reference style; backend v4 (conversations, notifications, resets, NASA images, profiles, AI comparison) | |
| 14 | “Ultimate” 28-page spec (React Native/Expo) | 28 pages in `/app`; extra pages and AI actions; gallery of real screenshots | React Native not buildable here (no npm) |
| 15 | Continue | Arabic interface with RTL, measured coverage | Science stays English verbatim |
| 16 | “Make one APK and one iOS” | Capacitor Android+iOS project, icons/splash, GitHub Actions cloud builds, build guide | No APK/iOS built here (no SDK/Xcode) |
| 17 | Professional mobile upgrade spec + full checklist + run | Live run, full test sweep, `MASTER_CHECKLIST.md` | Libraries in that spec mostly not adopted (see checklist §10) |
| 18 | Everything for VS Code + Claude | `CLAUDE.md`, `.vscode/`, this log, setup guide, final ZIP | |
| 19 | Open the final ZIP in a real VS Code/Windows setup and do what's good for the app | Set up `.venv` and ran every documented test suite for real on Windows (not re-reading prior notes); found `MASTER_CHECKLIST.md` wrongly marked six already-built features as missing (stop generation, swipeable comparison, pull-to-refresh, page transitions, “My Research” tab, search suggestions) and corrected it; found and fixed one real UI bug (swipe-dot indicator never updated) and two real Windows-only bugs (Unicode console crash in `e2e/*.py`; `run_e2e.sh` using the wrong Python) | Owner hadn't picked a specific task, so the highest-value unblocked work was verifying the checklist against the actual code/tests rather than trusting it, since it's the document every future session (human or Claude) relies on |
| 20 | From-scratch rebuild prompt, then NASA Combustion Science data integration, then a Flutter/Dart native rewrite prompt, then NASA Space Apps judging-criteria optimization — "finish everything then run the app in the emulator" | Added a Scientific Visualization Lab (`/app/viz`); discovered and integrated PSI's real (undocumented but public) JSON search API via Playwright network capture, not scraping rendered HTML — Combustion Research Hub (`/app/combustion`), with 3 hand-written, sourced fire-safety case studies (Apollo 1, Apollo 13, Mir) and 3 NASA Spinoff tech-transfer summaries; Research Impact Dashboard (`/api/impact`) and Judge Mode (`/app/judge`); `docs/JUDGING_CRITERIA.md` self-assessment, including what was explicitly *not* built and why; built and ran the real Android debug APK on the already-installed Pixel_8 emulator (earlier docs wrongly assumed no SDK was available on every machine) | Declined the from-scratch and Flutter rewrites without being asked to — they'd have discarded this session's and prior sessions' tested work and reversed the owner's own locked-in stack decision; flagged for the owner instead of guessing. Declined a fabricated user-efficiency study, a knowledge graph and a contradiction detector as not honestly buildable or not worth the UI cost at this corpus size (8 experiments) — documented, not silently skipped |

## Standing rules agreed in the chat
- Never fabricate NASA data, citations, values, AI answers or test results; mark what was not tested.
- Physical-device testing is never claimed; all mobile testing so far is Chromium emulation.
- Nothing is submitted to NASA Space Apps without the owner’s explicit approval.
