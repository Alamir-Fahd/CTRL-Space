# Phase 08 — Experiment extraction and comparison

**Source requirements:** `PHASE(8)/` docs and `flamelab_phase08.zip`
**Report date:** 2026-11-12

## What was analyzed
Phase 8's value model (value, unit, kind, source ref, basis) and comparison methodology; its dataset was empty.

## What was implemented
8 real experiments (5 BASS-II, 3 Saffire VI) with 10 fields each; values only from verified passages; field states with reasons. Comparison service: different-program, flow-configuration, missing-value and unit-mismatch warnings; numeric comparison only for single values in the same unit.

## Files created or modified
`backend/ctrlspace/services/experiments.py`, seed corpus experiments

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Real experiments, no fabricated values | **COMPLETE** | Every reported field has a passage_id (enforced by SQL) |
| Distinguish reported / not reported / not extracted | **COMPLETE** | test_list_and_detail_states |
| No comparison of incompatible units | **COMPLETE** | test_compare_warnings_units_and_chartable |
| Condition warnings | **COMPLETE** | different_programs, flow_configuration tests |
| Extraction automation | **NOT IMPLEMENTED** | Values were extracted by hand; Phase 8 also required human verification |
| Oxygen basis (mole/volume) | **NOT IMPLEMENTED** | Sources mostly don't state it; not captured |

## Tests performed
4 experiment tests; E2E compare journey.

## Remaining problems
Many fields are *Not extracted* because the numbers exist only in figures.

## Dependencies for the next phase
Frontend comparison page.
