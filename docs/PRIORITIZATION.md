# Feature prioritization (competition release)

Date: 2026-11-12. Scores 1 (low) – 5 (high). **Feasibility** includes the build environment: no internet, so no model downloads and no calls to AI providers. Stable baseline preserved as `CTRL_SPACE_STABLE_v3.1_BACKUP.zip` before any change.

| Feature | Sci. value | Innovation | Feasibility | Time (5 = fast) | Competition impact | Data available | Reliability | Integration (5 = simple) | Decision |
|---|---|---|---|---|---|---|---|---|---|
| **MUST HAVE** | | | | | | | | | |
| AI provider configuration + verification (`check-ai`, admin test) | 4 | 2 | 5 | 5 | 4 | — | 5 | 5 | Build now; real-provider run only on a connected machine |
| Reliable RAG: question analysis → retrieval → evidence evaluation → structured answer | 5 | 4 | 5 | 4 | 5 | 5 | 4 | 4 | Build now |
| Evidence coverage (well / partially / insufficiently supported) | 5 | 4 | 5 | 4 | 5 | 5 | 5 | 4 | Build now (deterministic rules, not a probability) |
| Citation validation + numeric grounding (numbers must appear in cited passages) | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 4 | Build now |
| Comparison intelligence (3 levels, statement types, context warnings) | 5 | 4 | 5 | 4 | 5 | 4 | 5 | 4 | Build now |
| Variable normalization (original unit kept, normalized unit + method, value type) | 4 | 3 | 5 | 4 | 3 | 3 | 5 | 4 | Build now, API-level, no DB migration |
| Retrieval-only structured fallback | 5 | 3 | 5 | 5 | 5 | 5 | 5 | 5 | Build now (demo must not depend on an external service) |
| Demo mode + preflight check | 3 | 2 | 5 | 5 | 5 | 5 | 5 | 5 | Build now |
| **SHOULD HAVE** | | | | | | | | | |
| Research gap analysis (corpus-scoped, typed gaps) | 4 | 4 | 5 | 4 | 4 | 4 | 4 | 4 | Build now |
| Research brief generator (Markdown, cited) | 4 | 3 | 5 | 5 | 4 | 5 | 5 | 5 | Build now |
| Semantic search (bge-m3 / MiniLM) | 3 | 3 | **1** | 3 | 3 | 5 | ? | 3 | **Blocked here**; benchmark harness ready, BM25 recall@6 = 0.958 on 36 passages leaves little headroom |
| Hybrid retrieval | 3 | 3 | **1** | 3 | 3 | 5 | ? | 3 | Blocked (needs embeddings); revisit when corpus grows |
| Cross-encoder reranking (bge-reranker-v2-m3) | 3 | 3 | **1** | 3 | 2 | 5 | ? | 3 | Blocked; only add if the benchmark shows a gain |
| Automatic experiment extraction | 4 | 4 | 2 | 1 | 3 | 2 | 2 | 2 | Not now: needs a model plus human verification; risk of fabricated-looking values |
| Advanced visualizations | 3 | 3 | 4 | 3 | 4 | 2 | 4 | 3 | Not now: too few numeric values to chart honestly |
| **NICE TO HAVE** | | | | | | | | | |
| Knowledge graph | 3 | 4 | 3 | 2 | 4 | 2 | 3 | 2 | Future |
| Flame science explorer, AI tutor, AI-generated quizzes | 2–3 | 3 | 3 | 2 | 3 | 3 | 2 | 3 | Future; AI quizzes risk unverified answers |
| More workspace / community features | 2 | 1 | 5 | 4 | 1 | — | 5 | 4 | Future |

Decision rule applied: build what adds scientific value and can be verified here; build smaller working versions of large items (gap analysis is rule-based, not AI); defer anything that needs unavailable infrastructure or risks unverified scientific output.
