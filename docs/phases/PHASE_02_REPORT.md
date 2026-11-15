# Phase 02 — System architecture and technical planning

**Source requirements:** `PHASE(2)/PHASE_02_NOTES.txt`
**Report date:** 2026-11-12

## What was analyzed
The checklist in the phase notes, the existing code, and what can actually run in the build environment (no pip/npm network; Flask, pdfplumber, Playwright present).

## What was implemented
Architecture chosen and documented: Python + Flask modular monolith, SQLite, BM25 search, provider-adapter RAG, no-build frontend. Each choice has a reason, including the deviations from the phase notes (Flask for FastAPI, plain JS for React).

## Files created or modified
`docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DATA_SOURCES.md`

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Frontend choice | **COMPLETE** | ES-module SPA; React not installable offline (deviation documented) |
| Backend: Python + FastAPI | **PARTIALLY COMPLETE** | Python + Flask: same layering, FastAPI unavailable offline |
| Database: PostgreSQL | **PARTIALLY COMPLETE** | SQLite now; PostgreSQL upgrade path documented |
| Vector search: pgvector | **NOT IMPLEMENTED** | BM25 only; not needed at 34 passages (Phase 6 made it optional) |
| PDF extraction: PyMuPDF | **PARTIALLY COMPLETE** | pdfplumber (Phase 4 fallback); PyMuPDF not installed |
| One visualization library | **COMPLETE** | Inline SVG charts, no library |
| One AI provider + embedding model | **PARTIALLY COMPLETE** | Adapter supports anthropic/openai/ollama; owner picks one. No embeddings |
| Two pipelines designed | **COMPLETE** | ARCHITECTURE.md "Evidence pipelines" |
| API contracts for all listed endpoints | **COMPLETE** | API.md; all 10 Phase 2 endpoints exist (+21 more) |
| Diagrams | **PARTIALLY COMPLETE** | Component diagram and ask sequence in text; no rendered diagrams |
| Docs ARCHITECTURE, TECH_STACK, API_CONTRACTS, DATA_FLOW, ADR | **PARTIALLY COMPLETE** | Merged into ARCHITECTURE.md (decision table = ADR) and API.md |

## Tests performed
Architecture validated by building it: all 31 routes run under the backend test suite.

## Remaining problems
Rendered diagrams for the presentation.

## Dependencies for the next phase
Canonical schema (Phase 3).
