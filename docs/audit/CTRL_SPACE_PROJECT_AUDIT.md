# CTRL+SPACE — Project Audit (Initial Analysis)

Audit date: 2026-11-12 · Source: `NASA.zip` (1,774,074 bytes, 62 entries, 5 nested ZIPs, 168 extracted source files)
Method: every folder and nested archive extracted and read; code inspected; tests executed where the sandbox allowed.

Status legend: **VERIFIED** (seen in code or proven by a run) · **CLAIMED** (stated in a document, not proven here) · **ABSENT** (looked for, not found).

---

## 1. Executive summary

1. **The archive does not contain one project. It contains two incompatible tracks.**
   - *Track A — "Phase documents" (Python):* Phases 3, 4, 5, 6, 8 ship Python code (FastAPI, SQLAlchemy, Alembic, PostgreSQL/SQLite, numpy). Phase 9 ships a React 18 + TypeScript + Vite frontend. This matches the original project PDF and the Challenge Guide.
   - *Track B — "Team handoff" (Node):* `FlameLab_Complete_Team_Handoff.md` declares **Angular + Node.js/Express 5/TypeScript + MongoDB/Mongoose** as the *current* decision, and explicitly forbids reverting to React/FastAPI/PostgreSQL. It reports three committed backend phases (`a247483`, `cc3ff49`, `210feb6`) with 428 passing tests in `D:\FlameLab`.
   - **None of the Track B code is in the archive.** No `package.json` for a Node backend, no Mongoose models, no Angular project. Track B is CLAIMED only.
2. **The Track A modules were each built in isolation and are not integrated.** Phases 3, 4, 5 and 8 each define their own, mutually incompatible data model (Section 4). Each document says so itself ("no earlier-phase code was available").
3. **There is zero real NASA content in the project.** 0 PDFs downloaded, 0 pages extracted, 0 experiments (`experiments.json` = `{"experiments": []}`), 0 evaluation entries. Only metadata for 5 NTRS records (read from record pages, not the API).
4. **Phases 2, 7, 10, 13 contain only plans/checklists; Phases 11, 12, 14 contain templates** whose own headers say no test was run, no measurement taken and no status verified.
5. **The project goal conflicts with the handoff on AI.** The selected challenge is *Flame in Freefall: AI-Powered Fire Safety Insights* — AI is the core of the challenge. The handoff says AI is "intentionally postponed" until the owner designs it. Phase 7 (RAG) exists as a plan and is blocked on an AI-provider decision.
6. **The logo contains the official NASA insignia ("meatball")** in its top-left corner. The project's own rules (handoff §4.10, Phase 14 claims policy) forbid implying NASA endorsement; NASA's insignia has restricted usage. A variant without the insignia is needed for the app, icon and slides.
7. **"CTRL+SPACE" appears nowhere in any document or source file**; all branding is FlameLab/FLAMELAB. The rebrand is new work.

## 2. What was actually verified by running code

| Module | Command | Result |
|---|---|---|
| Phase 8 experiment engine (stdlib only) | `python3 -m unittest discover -s tests -t .` | **55/55 passed (VERIFIED, 2026-11-12)** |
| Phase 6 search core | `import chunking, normalize, query, index, retrieval` | Imports OK; test suite not runnable (needs pytest) |
| Phase 3 DB, Phase 5 API, Phase 6 API, Phase 4 ingest | — | **Not runnable here**: FastAPI, SQLAlchemy, Alembic, pydantic, pytest absent |
| Phase 9 React frontend | — | **Not runnable here**: no `node_modules`, npm registry unreachable |

Sandbox facts: Python 3.12.3, Node v22, numpy, pdfplumber, reportlab, requests available. `pip install` and `npm` fail (DNS: "Name or service not known"); outbound network to `ntrs.nasa.gov` is not available from code. No Android emulator, no browser automation.

Test counts reported inside the documents (CLAIMED, not reproduced): Phase 4 "63 passed, 1 skipped"; Track B Phase 3 "428/428".

## 3. Phase-by-phase reality check

| Phase | Title (from the documents) | What is in the archive | Real status |
|---|---|---|---|
| 01 | Audit & Requirements | 5 markdown docs | Docs say the repo was unavailable; all features UNKNOWN. Requirements CR-F1..F5 are the only confirmed ones. |
| 02 | Architecture & Technical Planning | Checklist only (`PHASE_02_NOTES.txt`) | **NOT DONE.** None of the 5 required docs (ARCHITECTURE, TECH_STACK, API_CONTRACTS, DATA_FLOW, ADR) exist. Checklist proposes React/FastAPI/PostgreSQL/pgvector/PyMuPDF. |
| 03 | Database | SQLAlchemy models, 2 Alembic migrations, tests, 3 docs | Code present, well-designed (composite FKs, "missing ≠ zero"). Not executed here. Standalone, not used by any other phase. |
| 04 | NASA Data Ingestion | One 106 KB markdown with 18 embedded files | Code exists only *inside markdown*. Own SQLite schema. NTRS client written against the official OpenAPI doc but **never reached NTRS**. 0/5 PDFs. |
| 05 | Backend API | FastAPI app, 60 files, tests | Code present. Own models; `Experiment` has `organism`/`assay_type` (biology fields — wrong domain). `/api/ask` returns `answer: null` by design. `/api/ingest` returns 501. |
| 06 | Search Engine | Python package, tests, eval harness | BM25-style keyword retrieval with page-preserving chunks. Reads any DB via a configurable column mapping. Eval set explicitly SYNTHETIC. |
| 07 | RAG Research Assistant | Plan only | **NOT DONE.** Blocked on AI provider + repo. |
| 08 | Experiment Extraction & Comparison | Python package, 55 tests, schema SQL | **Best-verified module.** Typed values with `NOT_REPORTED/UNKNOWN/…` states, unit handling, source refs. Ships with empty dataset. |
| 09 | Frontend | React 18 + Vite app, 36 files | Code present; 6 routes. API contract in `types.ts` marked as an assumption. Branding FLAMELAB. Not built here. |
| 10 | Frontend/Backend Integration | Plan only | **NOT DONE.** |
| 11 | QA & Testing | Test plan + results template | Results doc: "Tests executed: 0". |
| 12 | Performance & Security | 3 templates | "TEMPLATE. No measurements", "no item verified". |
| 13 | Deployment & Docs | Checklist only | **NOT DONE.** |
| 14 | Submission | 5 drafts | All status cells "Unknown / [TO VERIFY]". |

## 4. Data-model fragmentation (VERIFIED from code)

| Concept | Phase 3 (PostgreSQL) | Phase 4 (SQLite) | Phase 5 (FastAPI) | Phase 8 (JSON) |
|---|---|---|---|---|
| Report key | `nasa_report_id` | own `reports` table | `nasa_id` | `report_id: str` |
| Pages | `report_pages` | `pages` | `report_pages` | page refs only |
| Experiments | `experiments` + `experiment_measurements` | — | `experiments` with `organism`, `assay_type`, `mission` | dataclasses: material, geometry, fuel_thickness, O₂, pressure, temperature, flow_velocity… |
| Chunks | `passages` + optional pgvector | — | — | — |

Phase 6 is the only module designed to adapt (`SourceMapping`), and Phase 9's API types are a guess. **Integration requires choosing one canonical schema.** Phase 3 + Phase 8's value model is the strongest basis.

## 5. Requirement and document conflicts

| ID | Conflict | Older position | Newer position | Notes |
|---|---|---|---|---|
| X-1 | Backend | Python + FastAPI (P2, P5, project PDF, Challenge Guide) | Node + Express 5 + TS (handoff) | Only Python code exists in the archive. |
| X-2 | Frontend | React + TS (P1, P2, P9 code) | Angular (handoff) | Only React code exists. |
| X-3 | Database | PostgreSQL + pgvector / SQLite (P2–P5) | MongoDB + Mongoose (handoff) | |
| X-4 | AI timing | Phase 7 RAG; challenge is "AI-Powered" | "AI intentionally postponed" (handoff) | Challenge cannot be met without AI. |
| X-5 | Authentication | "No end-user accounts" (P12 security docs) | Full auth, Argon2id, sessions (handoff P2) | |
| X-6 | Scope | 4 objectives: search, ask, compare, display (P1) | ~58 selected feature IDs incl. community, challenges, rooms (handoff) | Feature-ID wording is not in the archive (handoff itself says so). |
| X-7 | Phase numbering | 14 phases (folders) | Handoff "Phase 4 = research features", "Phase 6 = admin" | The two tracks use different phase meanings. |
| X-8 | Name | FlameLab / FLAMELAB | CTRL+SPACE (master prompt, logo) | |

## 6. Assets that are genuinely valuable

- **Phase 8 comparison engine** — tested, domain-correct, encodes the scientific-integrity rules.
- **Phase 3 schema** — referential integrity across report → page → passage → measurement.
- **Phase 4 NTRS client** — rate-limit spacing (1.8 s), page-size clamp (100), 10 k cap, redistribution checks, never-overwrite originals. Needs one live smoke test.
- **Phase 6 retrieval** — page-preserving chunking, keyword ranking; suitable as the RAG retriever.
- **Phase 9 UI** — loading/empty/error states, accessible skip link, non-endorsement footer.
- **5 verified NTRS record IDs** with titles, report numbers and dates (`REPORT_CATALOG.md`).
- **The logo artwork.**

## 7. Hard blockers for this environment

| ID | Blocker | Impact |
|---|---|---|
| B-1 | No package installation (pip/npm offline) | Cannot run FastAPI/SQLAlchemy/pytest or build the React app; Node/Angular/Mongo stack equally impossible. |
| B-2 | No network access to NTRS from code | Cannot download real reports; therefore cannot extract real evidence, experiments or page numbers. |
| B-3 | No Android emulator, no browser automation | Cannot produce visual verification or screenshots of a running app. |
| B-4 | Stack decision (X-1..X-3) | Implementation must not start until the owner chooses. |
| B-5 | AI provider decision (X-4) | Phase 7 blocked. |

## 8. Recommendation

Adopt **Track A (Python/FastAPI + React)** as the implementation base, because it is the only code that exists, it matches the challenge brief and the original project PDF, and the Phase 8 engine is already verified. Treat the Node/Angular/Mongo handoff as the *requirements* source for scientific-integrity rules and feature areas, not as a stack — unless the `D:\FlameLab` repository is supplied, in which case re-audit before choosing. Details in `CTRL_SPACE_TECHNICAL_DECISIONS.md`.
