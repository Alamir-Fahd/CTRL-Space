#!/usr/bin/env python3
"""Reproducible retrieval benchmark on real questions and verified NASA passages (eval/retrieval_eval.json).

Always measures the production BM25 retriever. If `sentence-transformers` is installed, it also measures:
  --embedders sentence-transformers/all-MiniLM-L6-v2 BAAI/bge-m3      (dense retrieval)
  --reranker BAAI/bge-reranker-v2-m3                                   (re-ranks the BM25 top 20)
Nothing is reported for a model that was not actually run.  Usage:  python scripts/benchmark_retrieval.py [--embedders ...] [--reranker ...]"""
import argparse, json, os, statistics, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ctrlspace import create_app
from ctrlspace.services.search import INDEX

ap = argparse.ArgumentParser()
ap.add_argument('--embedders', nargs='*', default=['sentence-transformers/all-MiniLM-L6-v2', 'BAAI/bge-m3'])
ap.add_argument('--reranker', default='BAAI/bge-reranker-v2-m3')
ap.add_argument('--k', type=int, default=6)
args = ap.parse_args()
create_app({'DATABASE': ':memory:'})
items = [i for i in json.load(open(os.path.join(ROOT, 'eval', 'retrieval_eval.json')))['items'] if not i.get('refuse')]
docs = [d['row'] for d in INDEX.docs if d['row']['verified']]


def score(rank_fn, name):
    rec, mrr, lat = [], [], []
    for it in items:
        t = time.perf_counter(); top = rank_fn(it['q'])[:args.k]; lat.append((time.perf_counter() - t) * 1000)
        rec.append(len([e for e in it['expect'] if e in top]) / len(it['expect']))
        mrr.append(next((1 / (i + 1) for i, x in enumerate(top) if x in it['expect']), 0))
    return {'retriever': name, 'n_questions': len(items), f'recall@{args.k}': round(sum(rec) / len(rec), 3), 'MRR': round(sum(mrr) / len(mrr), 3),
            'median_latency_ms': round(statistics.median(lat), 2)}


results, skipped = [score(lambda q: [h['id'] for h in INDEX.search(q, limit=50, verified_only=True)['results']], 'BM25 (production)')], []
try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
    import numpy as np
except ImportError:
    skipped.append('sentence-transformers is not installed: dense retrieval and reranking were NOT evaluated (pip install sentence-transformers).')
else:
    texts = [d['text'] for d in docs]; ids = [d['id'] for d in docs]
    for name in args.embedders:
        try:
            m = SentenceTransformer(name); t0 = time.perf_counter(); E = m.encode(texts, normalize_embeddings=True); load = time.perf_counter() - t0
            def dense(q, m=m, E=E):
                v = m.encode([q], normalize_embeddings=True)[0]; return [ids[i] for i in np.argsort(-E @ v)]
            r = score(dense, f'Dense: {name}'); r['corpus_encode_s'] = round(load, 2); results.append(r)
        except Exception as e:  # model download or memory failure is reported, never hidden
            skipped.append(f'{name}: {type(e).__name__}: {e}')
    try:
        ce = CrossEncoder(args.reranker)
        def rerank(q):
            cand = [h for h in INDEX.search(q, limit=20, verified_only=True)['results']]
            s = ce.predict([(q, h['text']) for h in cand]); return [cand[i]['id'] for i in np.argsort(-s)]
        results.append(score(rerank, f'BM25 top-20 + rerank: {args.reranker}'))
    except Exception as e:
        skipped.append(f'{args.reranker}: {type(e).__name__}: {e}')
out = {'run_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'corpus_passages': len(docs), 'results': results, 'not_evaluated': skipped}
json.dump(out, open(os.path.join(ROOT, 'eval', 'benchmark_results.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
