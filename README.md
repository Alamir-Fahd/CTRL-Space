# CTRL+SPACE — NASA fire research explorer

> **Start here:** open this folder in VS Code and follow [`docs/VSCODE_CLAUDE_SETUP.md`](docs/VSCODE_CLAUDE_SETUP.md). Claude Code reads [`CLAUDE.md`](CLAUDE.md). Status of every requirement: [`docs/MASTER_CHECKLIST.md`](docs/MASTER_CHECKLIST.md); full chat history: [`docs/CONVERSATION_LOG.md`](docs/CONVERSATION_LOG.md).

CTRL+SPACE is a web application for exploring NASA research on combustion and fire in microgravity. You can search NASA reports, ask research questions and get answers built only from verified report passages, and compare experiments side by side with their sources. Missing data is shown as missing, never guessed.

Built for the NASA Space Apps 2026 challenge *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data* — the official title, verified against the live challenge page; "SI" is the challenge's own term for "super intelligence," not "AI" as earlier drafts of this document said.

> CTRL+SPACE is an independent student project. It is **not affiliated with, endorsed or certified by NASA**. All sources are public records from the NASA Technical Reports Server (NTRS).

![Home](e2e/screenshots/01-home-desktop.png)

## Mobile app

**Android APK and iOS app:** see [`docs/NATIVE_BUILDS.md`](docs/NATIVE_BUILDS.md). One click in GitHub Actions builds the APK and an iOS simulator build in the cloud; no SDK needed on your computer. **Arabic:** Settings → Language → العربية (right-to-left interface; NASA sources stay verbatim in English).


Open **http://127.0.0.1:8000/app** on a phone (or install it). It is a dedicated mobile client, separate from the desktop site, with 28 screens. See `docs/MOBILE_ARCHITECTURE.md` and the screenshot gallery in `docs/gallery/`.


CTRL+SPACE installs on phones as an app (home-screen icon, full screen, bottom tab bar, offline reading of opened reports). Android APK options and steps: [`docs/MOBILE_APP.md`](docs/MOBILE_APP.md).

## What it does

| Area | Features |
|---|---|
| **Ask** | Evidence-grounded research assistant. Retrieves verified passages, refuses when evidence is weak (before any AI call), validates every citation, links each point to report + page on NTRS. |
| **Discovery & Evidence Library** | Report search by keyword, topic, program and sort; separate passage search by type. 6 NTRS reports (BASS-II, Saffire), ranked search, program filter, sort, pagination, report details, verified passages, links to the NTRS record and original PDF. |
| **Experiments** | 8 ISS / Cygnus experiments. Every value carries its source passage; missing values are marked *Not reported* or *Not extracted*. |
| **Compare** | 2–4 experiments side by side, with warnings for different programs/hardware, flow configuration, missing values and unit mismatches. Charts only when units match. |
| **Collections** | Accounts, private notes on reports, collections of reports and experiments, Markdown export. |
| **Learning Studio** | 5 lessons on combustion and microgravity. Team-written explanations, each backed by verified NASA passages; progress tracking. |
| **Challenges** | 3 quizzes graded on the server (answers never sent to the browser), with the source passage shown for every answer; attempts and best scores. |
| **Community** | 4 research rooms, discussions, replies, sharing reports and experiments, reporting posts, moderation. |
| **Profile & settings** | Profile with activity and progress, name, theme (system/light/dark), password change (signs out other devices), account deletion. |
| **Admin** | NTRS import, evidence review, experiment approval (blocked unless every value cites verified evidence), report approval, moderation queue, user management (roles, disable), privacy-conscious analytics, audit and ingestion logs. |

## Requirements

- Python 3.10 or newer (tested on 3.12)
- Internet access only for NTRS imports and cloud AI providers. Everything else works offline.

## Install and run

```bash
cd ctrl-space
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # Windows: copy .env.example .env
python run.py create-admin you@example.com "Your Name"
python run.py serve
```

Open **http://127.0.0.1:8000**. Routes: `/`, `/research`, `/library`, `/assistant`, `/experiments`, `/compare`, `/my-research`, `/studio`, `/challenges`, `/community`, `/profile`, `/settings`, `/admin` (see `docs/SCREENS.md`). The database is created and seeded from `data/seed/corpus.json` on first start.

### Turn on AI answers (optional)

Without an AI provider, the assistant still searches and returns the verified evidence, but writes no answer. To enable answers, set these in `.env` and restart:

```ini
CTRLSPACE_AI_PROVIDER=anthropic     # or openai, or ollama (local, free, no key)
CTRLSPACE_AI_MODEL=<model name>
CTRLSPACE_AI_API_KEY=<your key>     # stays on the server; never sent to the browser
```

For a free local option, install [Ollama](https://ollama.com), run `ollama pull llama3.1`, then set `CTRLSPACE_AI_PROVIDER=ollama` and `CTRLSPACE_AI_MODEL=llama3.1`.

### Import more NASA reports

Sign in as admin → **Admin → Import from NTRS** → enter an NTRS ID (for example `20210011385`, the BASS-II Summary Report). Or from the command line: `python run.py ingest 20210011385`.

Imported reports start as **pending**, and their extracted passages are **unverified**. They can't back an AI answer or an experiment value until you check each passage against the PDF and verify it in **Admin → Review passages**, then approve the report.

## Commands

| Command | Purpose |
|---|---|
| `python run.py serve [--host H] [--port P]` | Start the application |
| `python run.py create-admin EMAIL "NAME"` | Create or promote an admin (no default accounts exist) |
| `python run.py ingest NTRS_ID` | Import a report from NASA NTRS |
| `python run.py reset-db` | Delete the local database and re-seed |
| `python run.py check-ai` | Verify the configured AI provider end to end (status, latency) |
| `python run.py preflight` | Competition demo readiness checklist |
| `python scripts/benchmark_retrieval.py` | Retrieval benchmark (BM25; dense models and reranker when installed) |
| `python -m unittest discover -s tests -v` | Backend tests (73) |
| `bash scripts/run_e2e.sh` | Browser end-to-end tests (needs `python -m playwright install chromium`) |
| `python scripts/evaluate.py` | Retrieval evaluation and latency, writes `eval/results.json` |

## Project layout

```
backend/ctrlspace/       Flask app (modular monolith)
  __init__.py            app factory, config, security headers, static frontend
  db.py                  SQLite schema (integrity rules enforced in SQL), seeding, audit
  api/__init__.py        31 HTTP endpoints, validation, auth checks, error format
  services/              search (BM25), assistant (RAG + citation validation),
                         experiments (comparison rules), auth, ingest (NTRS + PDF)
frontend/                single-page app, no build step: index.html, js/, css/, assets/
data/seed/corpus.json    verified NASA corpus: 6 reports, 36 passages, 8 experiments
data/seed/learning.json  lessons, challenges and community rooms (seed-time check: every citation must exist)
tests/                   backend unit + integration tests
e2e/                     Playwright journeys and screenshots
eval/                    frozen retrieval evaluation set and latest results
docs/                    architecture, API, security, testing, deployment, phase reports
run.py / wsgi.py         CLI and production entry point
```

## Documentation

Start with [`CTRL_SPACE_FINAL_REPORT.md`](CTRL_SPACE_FINAL_REPORT.md). Then see [`docs/`](docs/): `PRIORITIZATION.md`, `MODEL_EVALUATION.md`, `SCREENS.md` (screen inventory, routes, journeys), `ARCHITECTURE.md`, `API.md`, `DATA_SOURCES.md`, `SECURITY.md`, `TESTING.md`, `DEPLOYMENT.md`, `USER_GUIDE.md`, `DEMO_SCRIPT.md`, `SETUP_REPORT.md` (stack/environment/API/cost audit), `JUDGING_CRITERIA.md` (NASA Space Apps scoring self-assessment), `QA_VERIFICATION_REPORT.md` (full audit: live persistence test, injection probes, device sweep, real vs. blocked test counts), `docs/qa/` (formal test-case documentation: feature inventory, test plan, 175 traced test cases, bug report, regression/mobile/AI reports, final dashboard, UI dimensions/responsive/visual-regression audit), and `docs/phases/` for all 14 phase reports.
