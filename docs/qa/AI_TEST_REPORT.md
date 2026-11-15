# CTRL+SPACE — AI test report

Three distinct categories, kept strictly separate per this audit's own rule: **never report a mocked test as a real LLM test.**

## 1. Mocked AI tests (deterministic test doubles, no network — backend test suite only)
These use `FakeProvider` (a Python object substituted via `create_app(provider=...)`) to test the assistant pipeline's logic deterministically, without needing a real model:

| Test | What it verifies |
|---|---|
| `test_grounded_answer_and_fabricated_citation_removed` | A citation the fake model invents that doesn't match retrieved evidence is stripped before reaching the user |
| `test_gate_blocks_llm_for_unsupported_questions` | The evidence gate blocks the LLM call entirely when retrieval is too weak — the model is never even asked |
| `test_model_says_insufficient` | When the model itself says it can't answer, that's surfaced honestly |
| `test_bad_json_and_provider_failures_are_honest` | Malformed model output or a provider exception produces an honest error, not a silent fake answer |
| `test_numeric_grounding` | Numbers in generated text that don't appear in the cited passage are flagged |
| `test_structured_answer_with_numeric_check` | The 7-section structured answer (direct answer, explanation, evidence, conditions, sources, limitations, coverage) is built correctly from the fake model's output |
| `test_ai_comparison` | The Compare screen's AI summary follows the same fake-model-grounding rules |

All 7 are real, passing, automated tests — but they are **not** evidence that a real model works; they prove the pipeline's safety logic works regardless of which model is plugged in.

## 2. Evidence-only tests (real retrieval, no LLM — this is the actual default mode, `CTRLSPACE_AI_PROVIDER=none`)
| Test | What it verifies |
|---|---|
| `test_no_provider_returns_evidence_only` | With no provider configured, `/api/ask` still returns real retrieved evidence, grouped by type, clearly labeled "retrieval-only" |
| `test_retrieval_only_brief` | The research-brief generator works the same way without a provider |
| `test_prompt_contains_only_verified_passages_and_rules` | If a provider *were* configured, the prompt sent to it would only ever contain verified passages — checked by inspecting the constructed prompt text |
| `test_coverage_rules`, `test_question_analysis` | Evidence-coverage labeling and question analysis, both provider-independent |
| `test_anonymous_ask_not_persisted` | Anonymous (signed-out) questions work but aren't saved |

This is the mode the live application has actually been running in for almost this entire session (confirmed via `/api/health` → `"ai_provider":"none"` and `run.py check-ai` → `not_configured`). Everything above is real and live-verified, just not LLM-backed.

## 3. Real LLM inference — RESOLVED, real results below

**Was BLOCKED at the start of this QA pass** (no Anthropic/OpenAI key, no local model). Resolved with the owner's explicit go-ahead ("install all what you want"): installed Ollama via `winget`, pulled `llama3.1` (4.9 GB, real download — one early attempt hit severe throttling on a GitHub release asset and was worked around by using `--ignore-scripts` for the separate npm/Capacitor issue earlier in the session; this model pull itself just took a while, ~35 minutes at fluctuating 0.1–3 MB/s). Set `CTRLSPACE_AI_PROVIDER=ollama`, `CTRLSPACE_AI_MODEL=llama3.1` in `.env`, restarted the server.

**`run.py check-ai` result**: first attempt timed out at 120s — that was the model's one-time cold load into memory (confirmed by a direct `curl` to Ollama's own API immediately after, which returned in 2.6s with `load_duration` of 6ms, i.e. already warm). Second attempt: **`status: ok`, latency 3187 ms, "Provider answered with valid JSON."** This is a genuine, live, end-to-end success — not assumed, not mocked.

### 30-question real-inference benchmark — actually run against the live corpus, 2026-11-13

| Category | Results | Notes |
|---|---|---|
| **A. Scientific knowledge** (5) | 4 answered, 1 honestly refused | The one refusal ("how is heat transferred to unburned material ahead of a spreading flame") was blocked by the evidence gate *before* the LLM was even called — retrieval didn't find a strong enough match, so the system correctly chose not to guess |
| **B. NASA experiments** (5) | 4 answered, 1 honestly refused | "Narrow Channel Validation test" — evidence was retrieved (6 passages) but the model itself judged it insufficient to answer confidently, rather than stretching the evidence |
| **C. Comparison** (5) | 5 answered | All cited real report IDs; spot-checked one answer's full text (below) |
| **D. Evidence and citations** (5) | 4 answered, 1 honestly refused | "Large-scale spacecraft flammability tests" report (20170008805) exists in the corpus but wasn't retrieved strongly enough to pass the gate for that phrasing — a real BM25 recall limitation, not a fabrication risk (it refused rather than guessing) |
| **E. Insufficient evidence** (5 — deliberately unanswerable specifics) | 4 refused outright, 1 "answered" with an honest "not specified in the passages" | See the detailed trace below — this is correct behavior, not a defect |
| **F. Out of scope** (5 — unrelated questions) | **5/5 correctly refused**, all blocked pre-LLM by the evidence gate (0 evidence retrieved) | The system never even asked the model about the capital of France, cake recipes, Mars weather, the World Cup, or pasta carbonara |

**Citation integrity check**: every single citation across all 30 answers referenced one of the 6 real corpus report IDs. **Zero fabricated or mismatched citations.**

### Detailed trace: the one ambiguous-looking result, actually inspected
Question "How many astronauts were aboard the ISS during the BASS-II tests?" (designed to be unanswerable) came back `status: answered` rather than `insufficient_evidence`. Pulled the full response: the generated text reads *"The number of astronauts aboard the ISS during the BASS-II tests is not specified in the passages,"* with the limitations field saying the same thing, citing the (tangentially relevant) passages it had actually retrieved. **This is correct, honest behavior** — "answered" here means "the model engaged and gave a grounded response," and the grounded response was an honest admission of missing data, not a fabricated number. Not a defect; recorded here specifically so it isn't mistaken for one later.

### Spot-checked answer quality
"What materials were tested in the BASS-II experiment?" → *"PMMA rods were tested in the BASS-II experiment."* Limitations: *"The passages do not specify the exact geometry, pressure, or platform conditions."* Disclaimer: *"AI-generated from the listed passages only. It is a reading aid, not primary evidence."* — concise, grounded, honest about what it doesn't know.

### What this proves
- The RAG pipeline works end-to-end with a real model: retrieval → evidence gate → generation → citation validation → structured answer.
- The evidence gate genuinely prevents low-confidence answers from ever reaching the LLM (5/5 out-of-scope questions, several in-scope-but-weakly-matched ones).
- Zero fabricated citations across 30 real questions.
- The one question designed to trip up the system (a plausible-sounding but unanswerable question) was handled honestly rather than either refusing unnecessarily or inventing a number.
- A real retrieval-recall gap was found (one real report wasn't matched for one phrasing) — logged as a genuine, minor finding, not swept aside: BM25 recall is measured at 0.958 on the frozen 12-question benchmark (`eval/results.json`), so misses on *other* phrasings are expected and consistent with that number, not a surprise.

### Full raw results
All 30 full JSON responses (not just the summary table) were saved during this run for anyone who wants to audit the complete text of every answer; available on request rather than inlined here given their length.

### Confirmed in the actual UI, not just via the API
Ran the same "What materials were tested in the BASS-II experiment?" question through the real mobile assistant screen (`/app/assistant`) in a real browser. The rendered result: a `AI · ollama` mode badge, a `Well supported` coverage label, the answer text clearly marked `AI-generated explanation` and separated from a `Cited NASA evidence` section, a clickable citation button carrying the exact real passage (NTRS 20160000593, locator "Material Ignition and Suppression Test", the exact quoted sentence about PMMA rod diameters and oxygen concentrations), and zero console errors. This confirms the pipeline works end-to-end through the actual interface a user would see, not only through a raw API call.

### Finding: the fast E2E suite is intentionally tuned for `ai_provider=none`, and that's correct, not a bug
With `ollama` left live in `.env`, re-running the full mobile E2E suite produced 4 failures — 3 hardcoded `expect(...).to_contain_text('Retrieval-only')` assertions (now legitimately false, since a real answer renders instead) and 1 timeout (`wait_for_selector`, 10s default — too short for a ~50s real local-model generation). This mirrors exactly how the *backend* test suite is already built: it always uses `FakeProvider` or no provider for fast, deterministic runs, and never makes a real network/model call inside the automated suite. Rather than slow down or complicate the whole E2E suite to tolerate a 50×-slower real model, **`.env` was reverted to `CTRLSPACE_AI_PROVIDER=none`** after this benchmark — restoring the documented, regression-tested baseline (confirmed: mobile suite back to 20/20 immediately after reverting). The real-AI evidence captured above is not lost; it's a deliberate, separate, targeted verification pass, the same way `scripts/evaluate.py`'s benchmark is separate from the fast backend suite.

**Ollama + `llama3.1` remain installed and ready on this machine.** To re-enable real AI answers at any time: set `CTRLSPACE_AI_PROVIDER=ollama` and `CTRLSPACE_AI_MODEL=llama3.1` in `.env`, restart the server. `ollama list` confirms the model is present; `run.py check-ai` confirms connectivity (expect the first call after a cold start to take 60–120s while the model loads into memory — this is normal, not a hang, as this benchmark discovered firsthand).
