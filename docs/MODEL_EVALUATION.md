# Model evaluation and selection

Rule followed: no model is called better without a measurement. Build environment: no internet, so **no AI provider could be called and no embedding or reranking model could be downloaded**. Everything marked "not measured" must be run on a connected machine before the competition.

## 1. Retrieval (measured)

`python scripts/benchmark_retrieval.py` — 12 real questions with expected verified passages (`eval/retrieval_eval.json`, frozen before the system was tuned), 36 verified passages.

| Retriever | recall@6 | MRR | Median latency | Status |
|---|---|---|---|---|
| BM25 (production) | **0.958** | **0.854** | 0.07 ms | Measured 2026-11-12 |
| Dense: sentence-transformers/all-MiniLM-L6-v2 | — | — | — | Not measured (library unavailable offline) |
| Dense: BAAI/bge-m3 | — | — | — | Not measured |
| BM25 top-20 + BAAI/bge-reranker-v2-m3 | — | — | — | Not measured |

The same script measures the three model rows automatically once `pip install sentence-transformers` works, and writes `eval/benchmark_results.json`. **Decision:** keep BM25. With recall@6 already 0.958 on this corpus, a dense model or reranker can improve at most one missed passage; add one only if the benchmark shows a gain, and re-evaluate when the corpus grows past a few hundred passages.

Facts from the model cards that matter for the choice (not performance claims): MiniLM-L6-v2 is about 22 M parameters, 384-dimensional, English, fast on CPU. bge-m3 is about 568 M parameters, 1024-dimensional and multilingual (relevant if questions in Arabic are supported later), and needs considerably more memory. The reranker adds a model call per candidate passage.

## 2. Language model (not measured here)

| Provider | Already integrated | Works offline | Notes for the demo |
|---|---|---|---|
| Anthropic Claude | Yes (`CTRLSPACE_AI_PROVIDER=anthropic`) | No | Needs a key and stable internet at the venue |
| OpenAI | Yes (`openai`) | No | Same |
| Ollama (local model) | Yes (`ollama`) | Yes | No venue internet needed; answer quality depends on the local model and laptop |

**Decision procedure on the team machine (do this before choosing):**

1. Configure a provider in `.env`, then `python run.py check-ai` (or Admin → Check AI provider): it must report `ok` and a latency.
2. Ask the 12 questions in `eval/retrieval_eval.json` through the app. For each answer record: did every point cite a retrieved passage, did any "Check number" warning appear, was the direct answer correct according to the cited passage, latency.
3. Ask the 4 off-topic questions: each must be refused.
4. Pick the provider with the most correct, fully cited answers; break ties on latency and venue reliability. Keep retrieval-only mode as the fallback.

No result from this procedure exists yet, so this document makes no claim about which model is better.

## 3. What protects answer quality regardless of model

Hard evidence gate before any model call; only verified passages are sent; ten scientific prompt rules; JSON structure (direct answer, explanation, evidence, conditions, limitations); citations must match retrieved passages (others removed); numbers must appear in their cited passages (otherwise flagged); evidence coverage computed by the app, not the model; retrieval-only fallback on any provider failure.
