# CTRL+SPACE — full verification report

Real results from running the actual application on 2026-11-13, not source-code inspection. See `docs/TESTING.md` for the full test breakdown, `docs/JUDGING_CRITERIA.md` and `docs/SETUP_REPORT.md` for the other two audits this session produced.

## Historical context: the FlameLab document

A compiled export of the project's original `NASA.zip` was provided as historical context. It describes an **earlier incarnation of this project, called FlameLab**, which at that point had settled on Angular + Node/Express/TypeScript + MongoDB (itself a change from an even earlier React/FastAPI/Postgres idea the document also mentions). That stack was never carried forward — the project went through further pivots and arrived at today's actual CTRL+SPACE: Flask + SQLite + vanilla JS. This is expected project history, not a bug to fix.

Cross-checking FlameLab's required **feature scope** (not its stack) against the current app: research discovery, evidence passages with page-level provenance, experiment records with measured/reported/missing-value states, experiment comparison, collections, notes, Learning Studio, Community, and an admin review/ingestion workflow are **all present and working today**. The one item FlameLab's plan explicitly deferred — "Do not implement AI... until core backend work is complete" — has since been built (the evidence-gated AI assistant). Nothing FlameLab required is missing from the current app.

## Final verification dashboard

| Area | Status | Evidence |
|---|---|---|
| Application startup | ✅ PASS | Fresh venv install, server starts, seeds DB from `corpus.json` on first run |
| Backend | ✅ PASS | 90/90 unit/integration tests |
| Frontend | ✅ PASS | 19/19 desktop E2E, 0 console errors |
| Database | ✅ PASS | Real restart-persistence test this round: registered a user, saved a report, wrote a note, killed the Python process, restarted it, confirmed both were still there — SQLite file, not an in-memory mock |
| API endpoints | ✅ PASS | 85 routes enumerated directly from the Flask decorators (not from docs); exercised across all E2E suites + a live SQL-injection probe (`'; DROP TABLE reports; --` in a search query — table intact, 6 reports after) + a live XSS probe (`<script>` not echoed unescaped) |
| Authentication | ✅ PASS | Register/login/logout, wrong-password rate limiting, session cookie flags, hashed passwords — all tested |
| Authorization (admin vs. user) | ✅ PASS | Non-admin gets 403 on admin routes (tested live and in the suite); admin dashboard reachable in the live device sweep below |
| AI provider | 🔑 **NOT CONFIGURED — not verified** | `CTRLSPACE_AI_PROVIDER=none` in `.env`; `run.py check-ai` returns `not_configured`. No Anthropic/OpenAI key is available in this environment, and Ollama is not installed here. Per this audit's own rule, this is reported as blocked, not faked. |
| Real LLM inference | 🔑 **BLOCKED on the above** | Nothing to test without a configured provider |
| RAG pipeline (retrieval → evidence gate → citation validation) — the parts that don't need an LLM | ✅ PASS | BM25 retrieval, evidence-sufficiency gate, citation structure, numeric-grounding checks — all exercised by `Intelligence`/`Search` test classes and the frozen benchmark below |
| Scientific validation benchmark | ✅ PASS (re-run fresh this round) | `scripts/evaluate.py`: recall@6 = 0.958, MRR = 0.854, gate pass rate = 1.0 on 12 answerable questions; 4/4 deliberately unsupported questions correctly refused |
| Scientific data integrity | ✅ PASS | Values traceable to passage/page; missing values never shown as zero; original units preserved (`SchemaIntegrity` test class) |
| Research discovery | ✅ PASS | Search, filters, sort, pagination tested live and in E2E |
| Experiment comparison | ✅ PASS | Selection limits, shared/differing variables, missing-value handling, unit-mismatch warnings — tested |
| Research workspace (collections/notes) | ✅ PASS | Create/rename/delete/export, persistence confirmed above |
| Learning Studio / Challenges | ✅ PASS | Lesson completion, graded attempts (server-side grading, answers never sent to the browser) |
| Community | ✅ PASS | Posts, replies, reporting, moderation |
| Admin | ✅ PASS | Reachable only by admin role, live-verified on two device profiles below |
| Mobile PWA | ✅ PASS | 9/9 installability/offline checks; 20/20 mobile-app journeys (iPhone 14); viewport sweep on Pixel 7 (412×839) and Galaxy S9+ (320×658): 0 console errors, 0 undersized touch targets, no horizontal overflow on 13 screens each |
| Offline mode | ✅ PASS | Downloaded-report offline reading, honest "unvisited report" error, reconnect banner — tested |
| Security | ✅ PASS | Hashed passwords, strict CSP, rate limiting, parameterized SQL (confirmed live against an injection attempt), no API keys in frontend code |
| Performance | ✅ PASS (measured, not estimated) | In-process latency from `eval/results.json`: search p95 ≈ 0.5 ms, compare p95 ≈ 1 ms, ask (no provider) p95 ≈ 7 ms — measured on this machine, not a claim |
| E2E critical journeys | ✅ PASS | Scenarios A–D and F from this audit's own list map directly onto the existing desktop/mobile/PWA suites, all green |
| Physical device testing | ⛔ NOT TESTED | Browser/emulator only (Chromium device emulation + the real Android emulator build from earlier this session). No physical phone was used. Disclosed, not claimed. |
| Native Android build | ✅ PASS (new this session) | Real debug APK built via Capacitor + Gradle, installed and run on a Pixel_8 emulator: boots, connects to the backend, shows real data, opens a real report detail |
| iOS build | ⛔ NOT BUILT | No Mac/Xcode available on this machine |

## Test counts

| Suite | Total | Passed | Failed | Blocked |
|---|---|---|---|---|
| Backend (pytest-style `unittest`) | 90 | 90 | 0 | 0 |
| Desktop E2E | 19 | 19 | 0 | 0 |
| Mobile app E2E (iPhone 14) | 20 | 20 | 0 | 0 |
| Arabic RTL E2E | 5 | 5 | 0 | 0 |
| PWA installability E2E | 9 | 9 | 0 | 0 |
| Mobile device sweep (Pixel 7 + Galaxy S9+, desktop site + mobile app) | 32 | 32 | 0 | 0 |
| Real LLM inference | 0 | 0 | 0 | 30 (no provider configured) |

**175 real, passing tests. Zero fabricated.** The only block is real-LLM inference, which genuinely needs a credential this environment doesn't have.

## What would turn the one blocked row green

Either:
1. Supply a real Anthropic or OpenAI API key (`CTRLSPACE_AI_API_KEY` in `.env`), or
2. Let me install Ollama (free, local, no key) and pull a small model — this would take real disk space and time to download, so it's worth confirming before I do it.

Either path lets me run `run.py check-ai` for real and then the 30-question scientific benchmark (categories A–F from this audit) against an actual model, with real latency and real citation-grounding results — not estimated ones.
