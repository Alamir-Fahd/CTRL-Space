# CTRL+SPACE — Missing and Incomplete Features

Statuses are from code inspection on 2026-11-12, not from documentation claims.
`IMPLEMENTED` = code exists and is wired · `PARTIAL` = code exists but unwired, untested here, or missing a required piece · `NOT IMPLEMENTED` · `BLOCKED` (external dependency).

## 1. Core objectives (Phase 01 confirmed requirements)

| Req | Feature | Status | Evidence | What is missing |
|---|---|---|---|---|
| CR-F1 | Search NASA reports | PARTIAL | P5 substring search over `report_pages`; P6 ranked keyword engine | No pages exist to search; P6 not mounted in P5; filters/sort/pagination only partly in P5 |
| CR-F2 | Answer questions from evidence | NOT IMPLEMENTED | P5 `/api/ask` returns `answer: null` by design; P7 is a plan | Provider adapter, evidence gate, prompt, citation validator, eval |
| CR-F3 | Compare real experiments | PARTIAL | P8 engine works (55 tests) | **0 experiments**; P5 `/compare` uses its own wrong-domain model, not P8 |
| CR-F4 | Display reports | PARTIAL | P9 Library + ReportDetail pages; P5 report endpoints | No report content; FE/BE contracts unverified |
| CR-F5 | Traceable citations | PARTIAL | P3 composite FKs, P8 `SourceRef(page, locator, quote)` | No pages, no citation-to-page viewer |

## 2. Feature areas from the master prompt

### A. Research Discovery
| Feature | Status | Notes |
|---|---|---|
| Keyword search | PARTIAL | P5 + P6, unintegrated |
| Filters / sorting / pagination | PARTIAL | P5 has limit/offset; P6 has filters by year/doc type/center |
| Categories / materials | NOT IMPLEMENTED | |
| Timeline / discovery feed | NOT IMPLEMENTED | Handoff "Phase 4 research features" — Node track, code absent |
| Report details + source metadata | PARTIAL | Metadata for 5 records only, not API-verified |
| Verified source links | PARTIAL | 5 NTRS citation URLs known |

### B. Scientific Evidence
| Feature | Status | Notes |
|---|---|---|
| PDF download | BLOCKED | P4 code ready; no network |
| Page-level text extraction | PARTIAL | P4 code; tested only on generated PDFs |
| OCR for scanned pages | NOT IMPLEMENTED | P4 flags `needs_ocr` only |
| Evidence passages / chunks | PARTIAL | P6 chunker; P3 `passages` table |
| Experiment records & measurements | PARTIAL | P8 model + validation; empty dataset |
| Units & missing-data states | IMPLEMENTED (P8) | Verified by tests |
| Evidence review / approval workflow | PARTIAL | P8 `verification_status`; P4 report approval; no UI |

### C. Research Workspace
| Feature | Status |
|---|---|
| Saved reports / collections | NOT IMPLEMENTED in archive (CLAIMED in Node track) |
| Research notes | NOT IMPLEMENTED |
| Experiment comparison UI | PARTIAL (P9 ComparePage + DataTable + BarChart) |
| Research exports | NOT IMPLEMENTED |

### D. Learning and Community
Educational studio, challenges, attempts, research rooms, posts, moderation, permissions — **NOT IMPLEMENTED anywhere**. Handoff itself lists them as later phases. Recommended out of hackathon MVP scope (decision D-4).

### E. Administration
| Feature | Status |
|---|---|
| Admin auth | PARTIAL (P5 API key, fail-closed) |
| Report ingestion endpoint | PARTIAL (P5 returns 501 until wired to P4) |
| Reindex | IMPLEMENTED (P5, page_count only) |
| Admin dashboard UI | NOT IMPLEMENTED |
| Audit logs | PARTIAL (P4 `processing_log`, P3 `ingestion_records`; no read API) |
| User management | NOT IMPLEMENTED (no accounts in Track A) |
| Analytics | NOT IMPLEMENTED |

### F. AI (Phase 7)
All NOT IMPLEMENTED: retrieval-to-prompt context, generation, citation validation, insufficient-evidence gate, research summaries, question generation, AI evaluation. BLOCKED on provider decision (D-3) and real data.

## 3. Platform / quality

| Item | Status |
|---|---|
| CTRL+SPACE branding | NOT IMPLEMENTED (all FLAMELAB) |
| Logo-derived assets without NASA insignia | NOT IMPLEMENTED |
| Root README, install/run guide | NOT IMPLEMENTED |
| Unified `.env.example` | PARTIAL (3 separate ones) |
| `.gitignore` | NOT IMPLEMENTED |
| Docker / deployment | NOT IMPLEMENTED |
| CI | NOT IMPLEMENTED |
| Integration / E2E tests | NOT IMPLEMENTED |
| Scientific evaluation set | NOT IMPLEMENTED (protocol only; must come from real PDFs) |
| Performance measurements | NOT IMPLEMENTED |
| Security audit with evidence | NOT IMPLEMENTED |
| PWA | NOT IMPLEMENTED |
| Android / native app | NOT IMPLEMENTED — and not in any approved plan |

## 4. Known defects found during audit

| ID | Location | Defect | Severity |
|---|---|---|---|
| DEF-01 | P5 `models/report.py` `Experiment` | Biology fields (`organism`, `assay_type`) — wrong domain for combustion | High |
| DEF-02 | P5 `services/compare_service.py` | Compares stored fields with an `identical` flag; ignores units, missing-value states, conditions — violates integrity rules 6–7 | High |
| DEF-03 | P3/P4/P5/P8 | Four incompatible schemas; no module reads another's data | Critical (blocks integration) |
| DEF-04 | P4 | Source code exists only inside a markdown file | Medium |
| DEF-05 | P9 `api/client.ts` vs P5 `routes/reports.py`, `routes/experiments.py` | **Verified mismatch:** frontend expects bare arrays (`Report[]`, `ExperimentSummary[]`); backend returns `Page[...]` envelopes with `items`. Frontend sends `/reports?query=`; backend list endpoint accepts only paging params. The Library and Compare pages would break against the real API. | High |
| DEF-06 | LOGO | NASA insignia in brand artwork | High (compliance) |
| DEF-07 | P4 | Weekly NTRS `redistributions` check required by NASA's terms not implemented | Medium |
