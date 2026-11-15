"""Competition-release endpoints: AI provider check, research gaps, research briefs, demo preflight."""
import os
import re

from flask import current_app, g, jsonify, make_response, request

from . import admin_required, body, current_user, err
from ..db import audit, now
from ..services import assistant, auth
from ..services import experiments as exps
from ..services import intelligence as intel
from ..services.search import INDEX

DEMO_REPORTS = ['20160000593', '20150019858', '20240007488']
DEMO_EXPERIMENTS = ['bass2-smmrf', 'saffire6-3']
DEMO_QUESTIONS = ['How does oxygen concentration affect flame spread in microgravity?',
                  'What happens to flames at very low airflow?', 'What is the oxygen margin of safety for PMMA rods?']


def _brief_md(question, ans, cmp):
    L = ['# CTRL+SPACE research brief', '', f'Generated {now()} UTC. Mode: ' +
         ('AI answer from cited passages' if ans and ans['status'] == 'answered' else 'retrieval-only (no generated answer)') +
         '. Sources: NASA Technical Reports Server. CTRL+SPACE is not affiliated with or endorsed by NASA.', '']
    if ans:
        c = ans['coverage']
        L += [f'## Question', '', question, '', f"**Evidence coverage:** {c['label']} ({c['passages']} passages from {len(c['reports'])} report(s)). {c['definition']}", '']
        if ans['status'] == 'answered':
            s = ans['sections']
            L += ['## Direct answer (AI-generated)', '', s['direct_answer'][0]['text'], '']
            for key, title in (('explanation', 'Scientific explanation'), ('evidence', 'Experimental evidence'), ('conditions', 'Experimental conditions')):
                if s[key]:
                    L += [f'## {title}', ''] + [f"- {i['text']} [" + '; '.join(f"NTRS {x['report_id']}, {x['locator']}" for x in i['citations']) + ']' for i in s[key]] + ['']
            if s['limitations']:
                L += ['## Limitations', '', s['limitations'], '']
        elif ans['status'] == 'insufficient_evidence':
            L += ['## Result', '', 'Insufficient scientific evidence was found in the available research collection to provide a reliable answer.', '']
        b = ans['brief']
        for key, title in (('findings', 'Reported findings (verbatim)'), ('conditions', 'Reported test conditions (verbatim)'), ('hypotheses', 'Hypotheses (not results)')):
            if b[key]:
                L += [f'## {title}', ''] + [f"> {e['text']}\n>\n> — NTRS {e['report_id']}, {e['locator']}" for e in b[key]] + ['']
        L += ['## Notes on the evidence', ''] + [f'- {n}' for n in c['notes']] + ['']
    if cmp:
        L += ['## Experiment comparison', '', '| Field | ' + ' | '.join(e['name'] for e in cmp['experiments']) + ' |', '|---|' + '---|' * len(cmp['experiments'])]
        L += ['| ' + r['label'] + ' | ' + ' | '.join((c['value'] if c['state'] == 'reported' else c['state_label']).replace('|', '/') for c in r['cells']) + ' |' for r in cmp['rows']]
        L += ['', '### Why these results are hard to compare', ''] + [f"- **{w['title']}.** {w['message']}" for w in cmp['levels']['level2']]
        L += ['', '### What the sources report', ''] + [f"- {f['experiment']} — {f['statement_type']}: “{f['text']}” (NTRS {f['report_id']}, {f['locator']})" for f in cmp['levels']['level3']['findings']]
        L += ['', cmp['levels']['level3']['rule'], '']
    srcs = {}
    for e in (ans['evidence'] if ans else []):
        srcs[e['report_id']] = e
    if srcs:
        L += ['## Sources', ''] + [f"- {e['report_title']} — https://ntrs.nasa.gov/citations/{rid}" for rid, e in srcs.items()]
    return '\n'.join(L) + '\n'


def register_intelligence(app):
    @app.get('/api/gaps')
    def gaps():
        return jsonify(intel.research_gaps(g.db, exps))

    @app.post('/api/analyze')
    def analyze():
        q = body().get('question')
        if not isinstance(q, str) or not 3 <= len(q.strip()) <= 400:
            err(422, 'validation_error', 'Questions must be 3 to 400 characters.')
        return jsonify(intel.analyze_question(q.strip()))

    @app.post('/api/brief')
    def brief():
        if not auth.LIMITER.allow(f'brief:{request.remote_addr}', 10, 300):
            err(429, 'rate_limited', 'Too many briefs. Wait a few minutes.')
        d = body()
        q, ids = d.get('question'), d.get('experiment_ids')
        if q is None and ids is None:
            err(422, 'validation_error', 'Give a question, 2–4 experiment_ids, or both.')
        if q is not None and (not isinstance(q, str) or not 3 <= len(q.strip()) <= 400):
            err(422, 'validation_error', 'Questions must be 3 to 400 characters.')
        if ids is not None and (not isinstance(ids, list) or not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids) or not all(isinstance(i, str) for i in ids)):
            err(422, 'validation_error', 'experiment_ids must list 2 to 4 different experiment IDs.')
        cmp = None
        if ids:
            cmp, missing = exps.compare(g.db, ids)
            if missing:
                err(404, 'not_found', 'Some experiments were not found.', {'missing': missing})
        g.lock.release()
        try:
            ans = assistant.answer(q.strip(), current_app.extensions['provider']) if q else None
        finally:
            g.lock.acquire()
        resp = make_response(_brief_md(q, ans, cmp))
        resp.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename="ctrl-space-research-brief.md"'
        return resp

    @app.post('/api/admin/ai/check')
    @admin_required
    def ai_check():
        g.lock.release()
        try:
            res = assistant.check_provider(current_app.extensions['provider'])
        finally:
            g.lock.acquire()
        audit(g.db, current_user()['email'], 'ai.check', res['provider'], f"{res['status']} {res['latency_ms']} ms")
        return jsonify(res)

    @app.get('/api/demo/preflight')
    def preflight():
        checks = []
        add = lambda name, ok, detail, level='fail': checks.append({'check': name, 'status': 'ok' if ok else level, 'detail': detail})
        add('Database', g.db.execute('PRAGMA quick_check').fetchone()[0] == 'ok', 'SQLite integrity check')
        for rid in DEMO_REPORTS:
            r = g.db.execute("SELECT status, (SELECT COUNT(*) FROM passages p WHERE p.report_id=reports.id AND p.verified=1) n FROM reports WHERE id=?", (rid,)).fetchone()
            add(f'Report {rid}', bool(r and r['status'] == 'approved' and r['n'] > 0), f"{r['n']} verified passages" if r else 'missing')
        for eid in DEMO_EXPERIMENTS:
            e = exps.get_experiment(g.db, eid)
            add(f'Experiment {eid}', e is not None, 'published' if e else 'missing or unpublished')
        add('Search index', len(INDEX.docs) > 0, f'{len(INDEX.docs)} passages indexed')
        for q in DEMO_QUESTIONS:
            okg, strong, why = assistant.evidence_gate(INDEX.search(q, limit=25, verified_only=True))
            add(f'Demo question: {q}', okg, f'{len(strong)} supporting passages' if okg else why)
        frontend = current_app.config['FRONTEND_DIR']
        for a in ('assets/hero.jpg', 'js/app.js', 'css/app.css'):
            add(f'Asset {a}', os.path.exists(os.path.join(frontend, a)), 'present' if os.path.exists(os.path.join(frontend, a)) else 'missing')
        pname = current_app.extensions['provider'].name
        add('AI provider configured', pname != 'none',
            f'{pname}' if pname != 'none' else 'none: the demo runs in retrieval-only mode (verified evidence, no generated answer)', 'warn')
        worst = 'fail' if any(c['status'] == 'fail' for c in checks) else 'warn' if any(c['status'] == 'warn' for c in checks) else 'ok'
        return jsonify(status=worst, mode='ai' if pname != 'none' else 'retrieval_only', checks=checks, questions=DEMO_QUESTIONS,
                       experiments=DEMO_EXPERIMENTS, reports=DEMO_REPORTS,
                       note='Run “Check AI provider” in Admin before presenting to verify the live provider.')
