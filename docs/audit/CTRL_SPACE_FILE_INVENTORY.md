# CTRL+SPACE — File Inventory

Source: `NASA.zip`, 62 entries (2,831,856 bytes uncompressed). Every file below was opened and read on 2026-11-12. Nested ZIPs were extracted; line counts cover `.py`, `.ts`, `.tsx`, `.sql`.

## 1. Top level

| Folder | Files | Kind | Role |
|---|---|---|---|
| `LOGO/` | 1 JPEG, 1254×1254 | Image | Official CTRL+SPACE artwork. Flaming hand rising over Earth, meteor streaks, orbital HUD lines (LAT/LON/ALT/V readout, "ORBIT / TRAJECTORY / RE-ENTRY"), wordmark `ctrl + space` bottom-right in white with a red "+". **Contains the NASA insignia top-left.** Palette: space-black, flame orange/yellow, electric blue and red orbit lines. |
| `material we have/` | 1 MD, 3 PDF | Docs | See §2 |
| `PHASE(1)` … `PHASE(14)` | 14 folders (note: `PHASE (7)` has a space) | Mixed | See §3 |

## 2. `material we have/`

| File | Size | Type | Content |
|---|---|---|---|
| `FlameLab_Complete_Team_Handoff.md` | 27,857 | Markdown | "Current" decisions: Angular, Node/Express 5/TS, MongoDB. Reports Phases 1–3 of a Node backend (auth, reports, evidence, experiments, NTRS import) with commit hashes and 428 tests — **code not included**. Scientific-integrity rules (14). Selected feature IDs 1–75 (wording not available). AI postponed. |
| `NASA_Space_Apps_2026_Challenge_Guide.pdf` | 59,052 | PDF, 12 pp, text layer | Team-written guide (ReportLab), not the official NASA page. Rates 14 challenges; **#8 "Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data"** is the team's top pick. Strong solution = RAG over NTRS + structured extraction + comparison dashboard. Data: NTRS, NASA PSI, FLEX, BASS, Saffire, ACME. |
| `give me al the api i will need it.pdf` | 608,096 | PDF, 6 pp, Arabic/English | NTRS API endpoints (health, citations/search, citations/{id}, downloads, autocomplete, redistributions, pubspace/search), search parameters, Python sample, proposed internal FastAPI endpoints (`/api/health … /api/reindex`), example `/api/ask` and `/api/compare` payloads, optional AI APIs (OpenAI, Anthropic, Gemini, HF, Ollama). |
| `this is the project so can you give me all the res.pdf` | 1,329,776 | PDF, 20 pp, Arabic | Original concept: "FlameLab — NASA Fire Research Explorer", web app with Search / Compare / Understand; fields to extract per report; RAG explanation; stack React + TS + Tailwind, Python + FastAPI, PostgreSQL/SQLite + FAISS, Recharts/Plotly, PyMuPDF. |

## 3. Phase folders

| Phase | Files | Nested archive | Code (lines) | Tests | Notes |
|---|---|---|---|---|---|
| 1 | `PROJECT_OVERVIEW`, `REQUIREMENTS`, `FEATURE_INVENTORY`, `EXISTING_IMPLEMENTATION`, `OPEN_QUESTIONS` (.md) | — | 0 | — | Design-only audit; 16 features all UNKNOWN; 12 open questions. |
| 2 | `PHASE_02_NOTES.txt` | — | 0 | — | Checklist; deliverables absent. |
| 3 | `DATABASE_SCHEMA`, `DATA_DICTIONARY`, `DATABASE_MIGRATIONS` (.md) | `flamelab-db-phase03.zip` → `flamelab-db/` (21 files) | 1,386 | 4 files | SQLAlchemy 2, Alembic `0001_initial_schema`, `0002_pgvector_embeddings`, `units.py`. |
| 4 | `FLAMELAB_PHASE04_FULL.md` (106,717) | none — **18 files embedded in markdown** | ~2,000 (embedded) | 3 files embedded | `flamelab_ingest/` NTRS client, PDF extraction (pdfplumber/PyMuPDF), CLI, quality report; `data/seed/priority_reports.json` (5 records). |
| 5 | — | `flamelab_phase05_backend.zip` → `flamelab/` (60 files) | 1,640 | 9 files | FastAPI app: health, reports, search, ask, experiments, compare, stats, admin; repositories/services layering; `X-API-Key` admin. |
| 6 | `SEARCH_ENGINE`, `CHUNKING_STRATEGY`, `SEARCH_EVALUATION` (.md) | `flamelab_phase06.zip` → `flamelab_search/` (25 files) | 1,483 | 6 files | Chunking, normalization, inverted index, retrieval, optional semantic layer (disabled), FastAPI wrapper, synthetic eval harness. |
| 7 | `FLAMELAB_Phase07_Notes.txt` | — | 0 | — | RAG plan; blocked on provider. |
| 8 | `COMPARISON_METHODOLOGY`, `EXPERIMENT_DATA_MODEL`, `EXPERIMENT_EXTRACTION`, `SCIENTIFIC_VALIDATION` (.md) | `flamelab_phase08.zip` → `flamelab_phase08/` (26 files) | 1,883 | 7 files | Stdlib-only. Models, units, extraction, validation, comparison, SVG visualization, WSGI + FastAPI apps, `schema/experiments.sql`, empty `experiments.json`. **55/55 tests pass.** |
| 9 | `FRONTEND_ARCHITECTURE`, `UI_COMPONENTS`, `USER_FLOWS` (.md) | `flamelab-frontend.zip` → `flamelab-frontend/` (36 files) | 1,022 | 5 files | React 18, react-router 6, Vite 5, Vitest; pages Home, Assistant, Compare, Library, ReportDetail, ExperimentDetails; plain-CSS tokens. |
| 10 | `FLAMELAB_Phase10_Plan.txt` | — | 0 | — | Integration plan; workflows A/B/C defined. |
| 11 | `TEST_PLAN`, `TEST_RESULTS`, `SCIENTIFIC_EVALUATION`, `KNOWN_ISSUES` (.md) | — | 0 | — | Plan is detailed; results: 0 executed. |
| 12 | `PERFORMANCE_REPORT`, `SECURITY_AUDIT`, `SECURITY_CONFIGURATION` (.md) | — | 0 | — | Templates / target-state specs. |
| 13 | `FLAMELAB_Phase13_Notepad.txt` | — | 0 | — | Deployment checklist; 9 docs to create. |
| 14 | `DEMO_SCRIPT`, `FINAL_PROJECT_DESCRIPTION`, `FINAL_PROJECT_STATUS`, `PRESENTATION_OUTLINE`, `SUBMISSION_CHECKLIST` (.md) | — | 0 | — | Drafts with `[TO VERIFY]` throughout. |

**Total real source code: ≈ 9,400 lines across 6 Python/TS modules. Total real NASA data files: 0.**

## 4. Duplicates

- Phase 3, 6, 8 and 9 markdown docs at folder level are copies of the `docs/` inside their ZIPs.
- Unit handling exists twice: `flamelab_db/units.py` (P3) and `flamelab/experiments/units.py` (P8).
- Three `reports` table definitions (P3, P4, P5) and two `experiments` definitions (P3, P5) plus P8's model.
- Two FastAPI wrappers for search/experiments (P6 `api.py`, P8 `fastapi_app.py`) besides the P5 app.

## 5. Absent (searched for, not found)

Node/Express backend · Angular app · MongoDB models · any `.git` history · `CLAUDE.md` · any NASA PDF · any extracted page text · any experiment record · Dockerfile / compose · CI config · `.gitignore` · root README · CTRL+SPACE branding · Tailwind config (P9 uses plain CSS) · chart library (P9 uses custom SVG).
