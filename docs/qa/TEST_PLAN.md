# CTRL+SPACE — test plan

## Scope
Full-stack verification of CTRL+SPACE (Flask + SQLite + vanilla JS, desktop site + `/app` mobile client + Android native shell) against its actual implemented behavior, ahead of NASA Space Apps 2026 judging.

## Environment
- Windows 11, Python 3.11.9, Node 24.16.0, Android SDK + emulator (Pixel_8 AVD), Chromium via Playwright.
- Database: fresh-seeded SQLite (`data/ctrlspace.db`), seeded from `data/seed/corpus.json` (6 reports, 36 verified passages, 8 experiments).
- Server: `run.py serve --host 0.0.0.0 --port 8000`, restarted multiple times during this pass (including a deliberate kill/restart for persistence testing).
- AI provider: `CTRLSPACE_AI_PROVIDER=none` at the start of this pass (see `AI_TEST_REPORT.md` for what changed).

## Tools
- `unittest` + Flask test client (backend, 90 tests).
- Playwright + Chromium (`e2e/*.py`, 65 tests: desktop, mobile app, Arabic, PWA, device sweep).
- `curl` + `python3 -m json.tool` for live manual API/security probes against the running server.
- `adb` for the Android emulator verification.

## Entry criteria
Dependencies installed, `.env` present, database seeded, server reachable at `/api/health`. All met at the start of this pass.

## Exit criteria
Every feature area in `FEATURE_INVENTORY.md` has real executed evidence (automated test, live probe, or explicit BLOCKED/NOT TESTED with a stated reason) — not source-code inspection alone.

## What counts as PASS
A test passes only when the actual observed behavior (an assertion result, an HTTP status, a rendered screenshot, a console-error list) matches the expected behavior — not when a page merely loads without throwing.

## What is explicitly out of scope / honestly blocked
- **Real LLM inference** — blocked at the start of this pass (no provider configured); being resolved live, see `AI_TEST_REPORT.md`.
- **Physical device testing** — browser/emulator only throughout (Chromium device emulation + one real Android emulator run). Never reported as physical-device testing.
- **iOS build** — no Mac/Xcode on this machine.
- **Challenge draft-answer persistence across reload** — confirmed not implemented (neither client- nor server-side). This is a scope gap against one example test case in the master prompt, not a regression; it was never built.

## Mocked vs. real integrations, explicitly separated
- **Mocked** (test doubles, deterministic, no network): `FakeProvider` (assistant.py tests), `MediaOpener`/`PsiOpener` (NASA Image Library / PSI tests) — used only inside `tests/test_backend.py`, never presented as live results.
- **Real, live, no mock**: every `e2e/*.py` run (real Chromium hitting the real running Flask server), every `curl` probe in this QA pass (real HTTP against the real running server), the real Android emulator run, the real `scripts/evaluate.py` benchmark run.
