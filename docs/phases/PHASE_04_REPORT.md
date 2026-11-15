# Phase 04 — NASA data ingestion

**Source requirements:** `PHASE(4)/FLAMELAB_PHASE04_FULL.md`, API PDF
**Report date:** 2026-11-12

## What was analyzed
The 18 files embedded in the Phase 4 markdown (client, extraction, ingest, quality), the NTRS limits it documented, and the 5 priority reports.

## What was implemented
NTRS client ported to the canonical schema: rate spacing 1.8 s, retries with backoff on 429/5xx, eligibility check, PDF selection, `%PDF-` signature check, 60 MB cap, SHA-256 duplicate detection, random file names, never overwrite, page extraction with OCR flag, chunking into unverified passages, pending report status, admin review workflow. **Real data:** 6 reports and 34 verbatim passages were retrieved from NTRS on 2026-11-12 and verified by hand (via the web fetch tool, since code-level network access was blocked).

## Files created or modified
`backend/ctrlspace/services/ingest.py`, admin routes, `run.py ingest`, `data/seed/corpus.json`

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Search/metadata/download endpoints | **COMPLETE** | NTRSClient; ingestion tests |
| Respect documented rate limits | **COMPLETE** | min_interval 1.8 s |
| Approval gate | **COMPLETE** | Imports are pending; passages unverified until reviewed |
| Page numbers preserved | **COMPLETE** | report_pages + locator 'p. N'; test checks page 2 |
| Never overwrite originals; duplicates | **COMPLETE** | exclusive create, SHA-256 check |
| Reject non-PDF / non-redistributable | **COMPLETE** | tests `test_rejects_non_pdf_and_metadata_only_and_bad_ids` |
| Live smoke test against NTRS | **BLOCKED** | Build environment has no network from code. Run `python run.py ingest 20210011385` on a connected machine |
| Download the 5 priority PDFs | **BLOCKED** | Same; their verified passages were captured instead |
| Weekly redistributions check | **NOT IMPLEMENTED** | Documented in DATA_SOURCES.md |
| OCR | **NOT IMPLEMENTED** | Pages flagged `needs_ocr` only |

## Tests performed
5 ingestion tests with a scripted fake NTRS and real generated PDFs (success path, non-PDF, metadata-only, 404, id mismatch, retries, chunk sizes).

## Remaining problems
The importer's live behaviour against NTRS is unverified. Field paths for authors/dates in NTRS JSON are read defensively and may come back empty.

## Dependencies for the next phase
Search index rebuild on approval (Phase 6).
