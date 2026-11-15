# Phase 07 — RAG research assistant

**Source requirements:** `PHASE (7)/FLAMELAB_Phase07_Notes.txt`
**Report date:** 2026-11-12

## What was analyzed
The 10-step plan: validation, retrieval, relevance gate, context, generation, citation validation, prompt rules, answer format, insufficient-evidence behaviour, evaluation.

## What was implemented
Full pipeline in `services/assistant.py`. Provider adapter (none/anthropic/openai/ollama) via env vars. All 10 scientific prompt rules plus a rule that passage text is data, not instructions. Hard gate before the LLM. JSON output, citation validation, report metadata attached from the database. Errors (timeout, HTTP, bad JSON) degrade to `evidence_only`, never to an unsupported answer. Stateless (no conversation history), per the plan's default.

## Files created or modified
`backend/ctrlspace/services/assistant.py`, `/api/ask`, Ask page

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| Query validation | **COMPLETE** | test_validation |
| Reuse existing search | **COMPLETE** | INDEX.search(verified_only=True) |
| Relevance gate before LLM | **COMPLETE** | test_gate_blocks_llm_for_unsupported_questions (provider never called) |
| Citation validation | **COMPLETE** | test_grounded_answer_and_fabricated_citation_removed |
| Insufficient-evidence status | **COMPLETE** | model-side and gate-side tests |
| Error handling, no key leaks | **COMPLETE** | 400/415/422/429 for bad requests. Provider timeout/HTTP/bad-JSON failures deliberately return 200 with `status: evidence_only` + `error_code` (instead of the planned 502/504) so the user still gets the verified evidence; test `test_bad_json_and_provider_failures_are_honest` |
| Approved provider configured | **BLOCKED** | Owner must choose and supply a key (or install Ollama) |
| Evaluation with real model | **BLOCKED** | No provider reachable in the build environment |
| Docs RAG_ARCHITECTURE, PROMPT_DESIGN, CITATION_VALIDATION, AI_EVALUATION | **PARTIALLY COMPLETE** | Covered in ARCHITECTURE.md (ask sequence), SECURITY.md, TESTING.md |

## Tests performed
8 assistant tests with scripted providers.

## Remaining problems
Answer quality has never been measured with a real model. Do this before claiming anything about AI accuracy.

## Dependencies for the next phase
Frontend Ask page (Phase 9).
