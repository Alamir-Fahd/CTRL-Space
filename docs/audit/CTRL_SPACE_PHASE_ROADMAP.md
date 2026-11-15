# CTRL+SPACE — 14-Phase Roadmap and Dependency Map

Phase titles and requirements are taken from the documents in each `PHASE(n)` folder. Status is what the archive actually contains (see audit).

## 1. Dependency map

```
P01 Audit & Requirements
 └─► P02 Architecture & Tech Planning ──────────────── (decides stack for everything below)
      └─► P03 Database schema
           └─► P04 NASA ingestion (NTRS → PDF → pages)
                ├─► P05 Backend API ◄─────────────┐
                ├─► P06 Search (chunks, ranking) ─┤
                │    └─► P07 RAG assistant ───────┤  needs P06 retriever + AI provider
                └─► P08 Experiments & comparison ─┘  needs real pages for evidence refs
                         └─► P09 Frontend (UI against P05 contracts)
                              └─► P10 Integration (FE ↔ BE, workflows A/B/C)
                                   └─► P11 QA & scientific evaluation
                                        └─► P12 Performance & security
                                             └─► P13 Deployment & docs
                                                  └─► P14 Demo & submission (owner approval gate)
```

Critical path: **P02 decision → P03 canonical schema → P04 real data**. Without real report pages, P06 has nothing to index, P07 has nothing to cite, P08 has nothing to extract, and P11 cannot evaluate.

## 2. Phase table

| # | Title | Exists in archive | Gap to close | Depends on | Can run in this sandbox? |
|---|---|---|---|---|---|
| 01 | Audit & Requirements | Docs (design-only) | Replace UNKNOWNs with this audit's findings | — | Yes (done now) |
| 02 | System Architecture & Planning | Checklist | Write ARCHITECTURE, TECH_STACK, API_CONTRACTS, DATA_FLOW, ADRs; **owner picks stack** | P01 | Docs yes; decision needs owner |
| 03 | Database | Code + migrations | Merge P8 value model into P3; drop P5's bio fields; one schema for all modules | P02 | Code yes; run needs SQLAlchemy |
| 04 | NASA Data Ingestion | Code inside markdown | Unpack to files; point at canonical schema; **live NTRS smoke test; download 5 priority PDFs** | P03 | No network → **blocked** |
| 05 | Backend API | FastAPI app | Rewire to canonical schema; implement ingest backend; fix `/compare` to use P8 engine | P03, P04 | Needs FastAPI |
| 06 | Scientific Search | Package | Map `SourceMapping` to canonical tables; mount under P05; replace synthetic eval with real one | P04 | Core yes; API needs FastAPI |
| 07 | RAG Assistant | Plan | Provider adapter, evidence gate, citation validator, `/api/ask` generation, eval | P06, AI provider | Needs provider + network |
| 08 | Experiment Extraction & Comparison | Package, 55 tests ✔ | Populate dataset from real pages (human-reviewed); DB-backed repository | P03, P04 | Yes |
| 09 | Frontend | React app | Rebrand CTRL+SPACE; align `types.ts` to P05; design system from logo | P05 | Needs npm |
| 10 | Integration | Plan | Shared client, CORS, workflows A/B/C end-to-end tests | P05–P09 | Needs both runtimes |
| 11 | QA & Testing | Plan + empty results | Execute plan; build frozen eval set from real reports | P10, real data | Partially |
| 12 | Performance & Security | Templates | Measure, audit, fill with evidence | P10 | Partially |
| 13 | Deployment & Docs | Checklist | Env files, Dockerfile (if approved), 9 docs, release check | P12 | Docs yes; deploy no |
| 14 | Demo & Submission | Drafts | Fill from real results; deck, video; **owner approval before any submission** | P13 | Docs only |

## 3. Proposed execution order once unblocked

1. **Owner decisions** (stack, AI provider, logo variant, scope) — see `CTRL_SPACE_TECHNICAL_DECISIONS.md` §4.
2. P02 documents + P03 canonical schema (can be done here, offline).
3. P04 live run **on the team's machine** (needs internet): `smoke` → `ingest --priority` → 5 PDFs → page text. Or upload the 5 PDFs and use `import-local`.
4. P05/P06/P08 merged into one FastAPI app (one repository, one schema).
5. Human-reviewed extraction of experiment values from the real PDFs (P08 requires `verification_status`).
6. P07 RAG on top of P06 retriever.
7. P09 rebrand + P10 integration.
8. P11–P14.

## 4. Environment needed per phase

| Need | Phases |
|---|---|
| Internet (NTRS) | 04, 07 (if cloud LLM), 11 live tests, 13 |
| `pip install` | 03, 04, 05, 06, 07, 10–13 |
| `npm install` | 09, 10, 11 E2E, 13 |
| Browser / emulator | 10, 11 E2E, 14 screenshots |
| Human scientific reviewer | 08 data, 11 evaluation |

This sandbox has none of the first four. Claude Code on your own machine (Windows, `D:\FlameLab`) has all of them.
