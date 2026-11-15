# Phase 06 — Scientific search engine

**Source requirements:** `PHASE(6)/` docs and `flamelab_phase06.zip`
**Report date:** 2026-11-12

## What was analyzed
Phase 6 chunking, normalization and ranking design; its evaluation set was explicitly synthetic.

## What was implemented
BM25 index over verified passages of approved reports, with normalisation (plurals, hyphens, domain synonyms such as O2→oxygen, quench→extinction), filters by program and passage type, pagination, and rebuild on admin changes. Library ranks reports by their best passage scores. A frozen 16-question evaluation set built from the real corpus replaces the synthetic one.

## Files created or modified
`backend/ctrlspace/services/search.py`, `eval/retrieval_eval.json`, `scripts/evaluate.py`

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Page-preserving chunks | **COMPLETE** | locator on every passage |
| Ranked keyword search with filters | **COMPLETE** | test_ranked_results_and_validation |
| Unverified/pending content excluded | **COMPLETE** | tests unverified + pending |
| Real evaluation | **COMPLETE** | eval/results.json: recall@6 0.958, MRR 0.854, 4/4 refusals |
| Semantic search | **NOT IMPLEMENTED** | Optional in Phase 6 |

## Tests performed
Search tests (3) + evaluation script. Two ranking bugs found and fixed: plural stemming (flames≠flame) and word-count report ranking.

## Remaining problems
EV-05 found 1 of 2 expected passages; EV-11's relevant passage ranked 4th. Corpus is small.

## Dependencies for the next phase
Retriever for the assistant (Phase 7).
