# Phase 03 — Database

**Source requirements:** `PHASE(3)/` docs and `flamelab-db-phase03.zip`
**Report date:** 2026-11-12

## What was analyzed
Phase 3 SQLAlchemy models and migrations; the incompatible models of Phases 4, 5 and 8.

## What was implemented
One canonical SQLite schema merging Phase 3 tables with Phase 8 field states and the handoff's users/collections/audit. Integrity rules are SQL `CHECK` constraints. Idempotent seeding from `data/seed/corpus.json`. Phase 5's biology fields (`organism`, `assay_type`) dropped.

## Files created or modified
`backend/ctrlspace/db.py`, `data/seed/corpus.json`

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| reports / report_pages / passages / experiments / measurements | **COMPLETE** | db.py SCHEMA |
| Missing ≠ zero | **COMPLETE** | CHECK constraints; test `test_number_requires_unit_and_reported_state` |
| Units preserved | **COMPLETE** | num_value requires num_unit; value_text keeps the source wording |
| Provenance on every value | **COMPLETE** | reported requires passage_id; test `test_reported_value_requires_source` |
| Ingestion records | **COMPLETE** | ingestion_records table, admin ingestion log |
| Migrations (Alembic) | **PARTIALLY COMPLETE** | schema_version table; no migration tool yet (DEPLOYMENT.md) |
| pgvector embeddings | **NOT IMPLEMENTED** | Optional in Phase 3; not used |

## Tests performed
`SchemaIntegrity` tests (4) incl. idempotent seeding.

## Remaining problems
No PostgreSQL support yet.

## Dependencies for the next phase
Ingestion writes into this schema (Phase 4).
