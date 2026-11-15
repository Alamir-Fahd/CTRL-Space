#!/usr/bin/env python3
"""Retrieval + evidence-gate evaluation and latency measurement. Writes eval/results.json.
LLM answer quality is NOT measured here (no provider in the evaluation environment); see docs/TESTING.md."""
import json, os, statistics, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ctrlspace import create_app
from ctrlspace.services.assistant import evidence_gate
from ctrlspace.services.search import INDEX

app = create_app({'DATABASE': ':memory:'})
c = app.test_client()
items = json.load(open(os.path.join(ROOT, 'eval', 'retrieval_eval.json')))['items']
rows, rec, mrr, refuse_ok, answer_ok = [], [], [], [], []
for it in items:
    found = INDEX.search(it['q'], limit=25, verified_only=True)
    ok, strong, why = evidence_gate(found)
    top = [h['id'] for h in (strong or found['results'])][:6]
    if it.get('refuse'):
        refuse_ok.append(not ok); rows.append({'id': it['id'], 'gate': ok, 'pass': not ok, 'top6': top})
    else:
        hit = [e for e in it['expect'] if e in top]
        rank = next((i + 1 for i, x in enumerate(top) if x in it['expect']), None)
        rec.append(len(hit) / len(it['expect'])); mrr.append(1 / rank if rank else 0); answer_ok.append(ok)
        rows.append({'id': it['id'], 'gate': ok, 'recall@6': len(hit) / len(it['expect']), 'first_relevant_rank': rank, 'top6': top})

def lat(fn, n=40):
    ts = []
    for _ in range(n):
        t = time.perf_counter(); fn(); ts.append((time.perf_counter() - t) * 1000)
    ts.sort(); return {'p50_ms': round(statistics.median(ts), 2), 'p95_ms': round(ts[int(n * .95) - 1], 2), 'n': n}
perf = {'GET /api/search': lat(lambda: c.get('/api/search?q=oxygen flame spread microgravity')),
        'GET /api/reports?q=': lat(lambda: c.get('/api/reports?q=PMMA extinction')),
        'POST /api/compare (3)': lat(lambda: c.post('/api/compare', json={'experiment_ids': ['bass2-mist', 'saffire6-3', 'saffire6-4']})),
        'POST /api/ask (no provider)': lat(lambda: c.post('/api/ask', json={'question': 'How does oxygen affect flame spread?'}, environ_base={'REMOTE_ADDR': str(time.time_ns())})),
        'index rebuild': lat(lambda: INDEX.build(app.extensions['db']), 10)}
res = {'run_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'corpus_passages': len(INDEX.docs),
       'answerable': {'n': len(rec), 'gate_pass_rate': sum(answer_ok) / len(answer_ok), 'mean_recall@6': round(sum(rec) / len(rec), 3), 'MRR': round(sum(mrr) / len(mrr), 3)},
       'unsupported': {'n': len(refuse_ok), 'correctly_refused': sum(refuse_ok)},
       'latency_in_process': perf, 'items': rows}
json.dump(res, open(os.path.join(ROOT, 'eval', 'results.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'items'}, indent=1))
for r in rows:
    print(r)
