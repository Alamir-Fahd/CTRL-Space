"""HTTP layer: validation, auth checks, JSON shapes. Business logic lives in services/.
Error shape everywhere: {"error": {"code", "message", "details", "request_id"}}."""
import functools
import json
import os
import re

from flask import current_app, g, jsonify, make_response, request
from werkzeug.exceptions import HTTPException

from .. import ROOT, VERSION
from ..db import audit, now
from ..services import assistant, auth, experiments as exps, ingest as ing
from ..services.search import INDEX

PUBLIC_REPORT_COLS = ('id,title,doc_type,published,report_number,program,center,authors,rights,source_url,pdf_url,'
                      'loc_kind,status,provider,retrieved_at')
COOKIE = 'cs_session'


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def err(status, code, message, details=None):
    raise ApiError(status, code, message, details)


def body():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.content_length:
        if not request.is_json:
            err(415, 'unsupported_media_type', 'Send JSON with Content-Type: application/json.')
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            err(400, 'invalid_json', 'Request body must be a JSON object.')
        return data
    return {}


def int_arg(name, default, lo, hi):
    raw = request.args.get(name)
    if raw is None:
        return default
    if not re.fullmatch(r'\d{1,6}', raw) or not lo <= int(raw) <= hi:
        err(422, 'validation_error', f'{name} must be an integer between {lo} and {hi}.', {name: raw[:20]})
    return int(raw)


def current_user():
    if 'user' not in g:
        g.user = auth.user_for_token(g.db, request.cookies.get(COOKIE))
    return g.user


def login_required(fn):
    @functools.wraps(fn)
    def w(*a, **k):
        if not current_user():
            err(401, 'unauthenticated', 'Sign in to use this feature.')
        return fn(*a, **k)
    return w


def admin_required(fn):
    @functools.wraps(fn)
    def w(*a, **k):
        u = current_user()
        if not u:
            err(401, 'unauthenticated', 'Sign in as an administrator.')
        if u['role'] != 'admin':
            err(403, 'forbidden', 'Administrator access is required.')
        return fn(*a, **k)
    return w


def ip():
    return request.remote_addr or 'unknown'


def page(items, total, limit, offset):
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


def report_public(row, con):
    d = {k: row[k] for k in PUBLIC_REPORT_COLS.split(',')}
    d['passage_count'] = con.execute('SELECT COUNT(*) FROM passages WHERE report_id=? AND verified=1', (row['id'],)).fetchone()[0]
    d['page_count'] = con.execute('SELECT COUNT(*) FROM report_pages WHERE report_id=?', (row['id'],)).fetchone()[0]
    d['indexed'] = d['passage_count'] > 0
    d['keywords'] = json.loads(row['keywords'] or '[]')
    d['abstract'] = row['abstract']
    d['categories'] = [r[0] for r in con.execute('SELECT category FROM report_categories WHERE report_id=? ORDER BY category', (row['id'],))]
    return d


def register(app):
    from .platform import register_platform
    register_platform(app)
    from .intelligence_routes import register_intelligence
    register_intelligence(app)
    from .mobile_routes import register_mobile
    register_mobile(app)
    @app.errorhandler(ApiError)
    def _api(e):
        return jsonify(error={'code': e.code, 'message': e.message, 'details': e.details, 'request_id': g.get('request_id')}), e.status

    @app.errorhandler(HTTPException)
    def _http(e):
        if not request.path.startswith('/api/'):
            return e
        code = {404: 'not_found', 405: 'method_not_allowed', 413: 'payload_too_large'}.get(e.code, 'http_error')
        return jsonify(error={'code': code, 'message': e.description, 'details': None, 'request_id': g.get('request_id')}), e.code

    @app.errorhandler(Exception)
    def _crash(e):
        app.logger.exception('Unhandled error %s', g.get('request_id'))
        return jsonify(error={'code': 'internal_error', 'message': 'Something went wrong on the server.', 'details': None,
                              'request_id': g.get('request_id')}), 500

    # ---------------- health & stats
    @app.get('/api/health')
    def health():
        ok = g.db.execute('SELECT 1').fetchone()[0] == 1
        return jsonify(status='ok' if ok else 'degraded', version=VERSION, database='ok' if ok else 'error',
                       ai_provider=current_app.extensions['provider'].name, indexed_passages=len(INDEX.docs))

    @app.get('/api/stats')
    def stats():
        c = g.db
        q = lambda s: c.execute(s).fetchone()[0]
        return jsonify(reports=q('SELECT COUNT(*) FROM reports WHERE status=\'approved\''),
                       indexed_reports=q('SELECT COUNT(DISTINCT p.report_id) FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.verified=1 AND r.status=\'approved\''),
                       verified_passages=q('SELECT COUNT(*) FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.verified=1 AND r.status=\'approved\''),
                       experiments=q('SELECT COUNT(*) FROM experiments WHERE status=\'published\''),
                       programs=[r[0] for r in c.execute('SELECT DISTINCT program FROM reports WHERE status=\'approved\' AND program IS NOT NULL ORDER BY 1')],
                       categories=[r[0] for r in c.execute('SELECT DISTINCT rc.category FROM report_categories rc JOIN reports r ON r.id=rc.report_id WHERE r.status=\'approved\' ORDER BY 1')],
                       lessons=q('SELECT COUNT(*) FROM lessons'), challenges=q('SELECT COUNT(*) FROM challenges'),
                       retrieved_at=q('SELECT MAX(retrieved_at) FROM reports'))

    @app.get('/api/impact')
    def impact():
        c = g.db
        q = lambda s: c.execute(s).fetchone()[0]
        statuses = {'answered': 0, 'evidence_only': 0, 'insufficient_evidence': 0, 'other': 0}
        for (content,) in c.execute("SELECT content FROM messages WHERE role='assistant'"):
            try:
                s = json.loads(content).get('status', 'other')
            except (TypeError, ValueError):
                s = 'other'
            statuses[s if s in statuses else 'other'] += 1
        eval_path = os.path.join(ROOT, 'eval', 'results.json')
        validation = None
        if os.path.exists(eval_path):
            with open(eval_path, encoding='utf-8') as f:
                e = json.load(f)
            validation = {'run_at': e.get('run_at'), 'corpus_passages': e.get('corpus_passages'),
                          'answerable_questions': e.get('answerable', {}).get('n'), 'recall_at_6': e.get('answerable', {}).get('mean_recall@6'),
                          'mrr': e.get('answerable', {}).get('MRR'), 'gate_pass_rate': e.get('answerable', {}).get('gate_pass_rate'),
                          'unsupported_questions': e.get('unsupported', {}).get('n'), 'correctly_refused': e.get('unsupported', {}).get('correctly_refused'),
                          'source': 'scripts/evaluate.py, a frozen 16-question benchmark (12 answerable from indexed passages, 4 deliberately unsupported)'}
        return jsonify(
            research=dict(reports_indexed=q("SELECT COUNT(DISTINCT p.report_id) FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.verified=1 AND r.status='approved'"),
                          verified_passages=q("SELECT COUNT(*) FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.verified=1 AND r.status='approved'"),
                          experiments=q("SELECT COUNT(*) FROM experiments WHERE status='published'"),
                          questions_processed=q("SELECT COUNT(*) FROM messages WHERE role='user'"),
                          evidence_grounded_answers=statuses['answered'] + statuses['evidence_only'],
                          insufficient_evidence_answers=statuses['insufficient_evidence'],
                          active_sessions=c.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > ?', (now(),)).fetchone()[0],
                          registered_users=q('SELECT COUNT(*) FROM users')),
            validation=validation,
            disclaimer='“Questions processed” and “evidence-grounded answers” are lifetime counts for this running instance, not a controlled user study. '
                       'No efficiency comparison against manual research has been run; that would require real test subjects.',
            retrieved_at=now())

    # ---------------- reports
    @app.get('/api/reports')
    def reports():
        limit, offset = int_arg('limit', 20, 1, 100), int_arg('offset', 0, 0, 100000)
        q = (request.args.get('q') or '').strip()[:200]
        sort = request.args.get('sort') or ('relevance' if q else 'date')
        if sort not in ('relevance', 'date', 'oldest', 'title', 'indexed'):
            err(422, 'validation_error', 'sort must be relevance, date, oldest, title or indexed.')
        years = {}
        for k in ('year_from', 'year_to'):
            v = request.args.get(k)
            if v:
                if not re.fullmatch(r'(19|20)\d\d', v):
                    err(422, 'validation_error', f'{k} must be a 4-digit year.')
                years[k] = v
        evidence = request.args.get('evidence') or None
        if evidence not in (None, 'verified', 'pages', 'metadata_only'):
            err(422, 'validation_error', 'evidence must be verified, pages or metadata_only.')
        material = (request.args.get('material') or '').strip()[:60] or None
        program = request.args.get('program') or None
        where, args = ['status=\'approved\''], []
        if 'year_from' in years:
            where.append('published >= ?'); args.append(years['year_from'])
        if 'year_to' in years:
            where.append('published < ?'); args.append(str(int(years['year_to']) + 1))
        if evidence == 'verified':
            where.append('id IN (SELECT report_id FROM passages WHERE verified=1)')
        elif evidence == 'pages':
            where.append('id IN (SELECT report_id FROM report_pages)')
        elif evidence == 'metadata_only':
            where.append('id NOT IN (SELECT report_id FROM passages WHERE verified=1) AND id NOT IN (SELECT report_id FROM report_pages)')
        if material:
            where.append("id IN (SELECT e.report_id FROM experiments e JOIN experiment_fields f ON f.experiment_id=e.id "
                         "WHERE e.status='published' AND f.field='material' AND f.state='reported' AND f.value_text LIKE ? ESCAPE '!')")
            args.append('%' + material.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%')
        if program:
            where.append('program=?'); args.append(program)
        category = request.args.get('category') or None
        if category:
            where.append('id IN (SELECT report_id FROM report_categories WHERE category=?)'); args.append(category)
        order = {'oldest': 'published ASC', 'title': 'title COLLATE NOCASE', 'indexed': 'created_at DESC, published DESC'}.get(sort, 'published DESC')
        rows = g.db.execute(f'SELECT * FROM reports WHERE {" AND ".join(where)} ORDER BY {order}', args).fetchall()
        if q:
            # Rank reports by their best verified passages (BM25) plus title/author matches.
            from ..services.search import tokens
            qt = set(tokens(q))
            per = {}
            for h in INDEX.search(q, limit=100000, verified_only=True)['results']:
                per.setdefault(h['report_id'], []).append(h['score'])
            def score(r):
                meta = len(qt & set(tokens(f"{r['title']} {r['program'] or ''} {r['authors'] or ''}")))
                return sum(sorted(per.get(r['id'], []), reverse=True)[:3]) + 2.0 * meta
            scored = [(score(r), r) for r in rows]
            keep = [(s_, r) for s_, r in scored if s_ > 0]
            rows = [r for s_, r in (sorted(keep, key=lambda x: -x[0]) if sort == 'relevance' else keep)]
        items = [report_public(r, g.db) for r in rows[offset:offset + limit]]
        return jsonify(page(items, len(rows), limit, offset))

    def get_report_row(rid):
        if not re.fullmatch(r'\d{8,12}', rid):
            err(400, 'invalid_id', 'Report IDs are 8 to 12 digits.')
        r = g.db.execute('SELECT * FROM reports WHERE id=?', (rid,)).fetchone()
        u = current_user()
        if not r or (r['status'] != 'approved' and not (u and u['role'] == 'admin')):
            err(404, 'not_found', 'Report not found.')
        return r

    @app.get('/api/reports/<rid>')
    def report(rid):
        r = get_report_row(rid)
        d = report_public(r, g.db)
        d['passages'] = [dict(p) for p in g.db.execute(
            'SELECT id,locator,kind,text,verified FROM passages WHERE report_id=? AND verified=1 ORDER BY rowid', (rid,))]
        d['experiments'] = [dict(e) for e in g.db.execute('SELECT id,name FROM experiments WHERE report_id=? AND status=\'published\'', (rid,))]
        u = current_user()
        if u:
            n = g.db.execute('SELECT text FROM notes WHERE user_id=? AND report_id=?', (u['id'], rid)).fetchone()
            d['my_note'] = n[0] if n else ''
        return jsonify(d)

    @app.get('/api/reports/<rid>/pages')
    def report_pages(rid):
        get_report_row(rid)
        limit, offset = int_arg('limit', 20, 1, 100), int_arg('offset', 0, 0, 100000)
        total = g.db.execute('SELECT COUNT(*) FROM report_pages WHERE report_id=?', (rid,)).fetchone()[0]
        rows = g.db.execute('SELECT page_number,text,is_empty,needs_ocr FROM report_pages WHERE report_id=? ORDER BY page_number LIMIT ? OFFSET ?',
                            (rid, limit, offset)).fetchall()
        return jsonify(page([dict(r) for r in rows], total, limit, offset))

    # ---------------- search & ask
    @app.get('/api/search')
    def search():
        q = (request.args.get('q') or '').strip()
        if not 2 <= len(q) <= 300:
            err(422, 'validation_error', 'q must be 2 to 300 characters.')
        limit, offset = int_arg('limit', 10, 1, 50), int_arg('offset', 0, 0, 10000)
        kind = request.args.get('kind') or None
        if kind and kind not in assistant.KIND_LABEL:
            err(422, 'validation_error', 'Unknown passage kind.')
        res = INDEX.search(q, limit, offset, verified_only=True, program=request.args.get('program') or None, kind=kind)
        items = [{k: h[k] for k in ('id', 'report_id', 'title', 'locator', 'kind', 'text', 'program', 'score', 'matched_terms')} for h in res['results']]
        return jsonify({**page(items, res['total'], limit, offset), 'terms': res['terms']})

    @app.post('/api/ask')
    def ask():
        if not auth.LIMITER.allow(f'ask:{ip()}', 20, 300):
            err(429, 'rate_limited', 'Too many questions. Wait a few minutes and try again.')
        d = body()
        q = d.get('question')
        if not isinstance(q, str) or not 3 <= len(q.strip()) <= 400:
            err(422, 'validation_error', 'Questions must be 3 to 400 characters.', {'question': 'length'})
        top_k = d.get('top_k', 6)
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 2 <= top_k <= 8:
            err(422, 'validation_error', 'top_k must be an integer from 2 to 8.')
        provider = current_app.extensions['provider']
        g.lock.release()                      # don't hold the DB lock during a slow LLM call
        try:
            res = assistant.answer(q.strip(), provider, top_k)
        finally:
            g.lock.acquire()
        return jsonify(res)

    # ---------------- experiments & compare
    @app.get('/api/experiments')
    def experiments():
        items = exps.list_experiments(g.db, request.args.get('program') or None)
        return jsonify(page(items, len(items), len(items), 0))

    @app.get('/api/experiments/<eid>')
    def experiment(eid):
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', eid):
            err(400, 'invalid_id', 'Invalid experiment ID.')
        e = exps.get_experiment(g.db, eid)
        if not e:
            err(404, 'not_found', 'Experiment not found.')
        return jsonify(e)

    @app.post('/api/compare')
    def compare():
        ids = body().get('experiment_ids')
        if not isinstance(ids, list) or not 2 <= len(ids) <= 4 or not all(isinstance(i, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', i) for i in ids):
            err(422, 'validation_error', 'experiment_ids must list 2 to 4 experiment IDs.')
        if len(set(ids)) != len(ids):
            err(422, 'validation_error', 'experiment_ids must not repeat.')
        res, missing = exps.compare(g.db, ids)
        if missing:
            err(404, 'not_found', 'Some experiments were not found.', {'missing': missing})
        return jsonify(res)

    # ---------------- auth
    def set_cookie(resp, token):
        resp.set_cookie(COOKIE, token, httponly=True, samesite='Strict', secure=current_app.config['COOKIE_SECURE'],
                        max_age=current_app.config['SESSION_HOURS'] * 3600, path='/')
        return resp

    @app.post('/api/auth/register')
    def register_user():
        if not auth.LIMITER.allow(f'reg:{ip()}', 10, 3600):
            err(429, 'rate_limited', 'Too many sign-ups from this address. Try again later.')
        d = body()
        email, name, pw, category = d.get('email'), d.get('name'), d.get('password'), d.get('category') or None
        institution = (d.get('institution') or '').strip()[:120] or None
        errors = auth.validate_signup(email, name, pw, category)
        if errors:
            err(422, 'validation_error', 'Please correct the highlighted fields.', errors)
        try:
            cur = g.db.execute('INSERT INTO users (email,name,pw_hash,role,created_at,category,institution) VALUES (?,?,?,?,?,?,?)',
                               (email.strip().lower(), name.strip(), auth.hash_password(pw), 'user', now(), category, institution))
        except Exception:
            err(409, 'email_taken', 'An account with this email already exists.', {'email': 'taken'})
        from ..db import notify
        notify(g.db, cur.lastrowid, 'system', 'Welcome to CTRL+SPACE', 'Every answer here is backed by a verified NASA passage. Start with the demo journey or ask a question.', '/app/assistant')
        g.db.commit()
        token = auth.create_session(g.db, cur.lastrowid, current_app.config['SESSION_HOURS'])
        return set_cookie(make_response(jsonify(user={'id': cur.lastrowid, 'email': email.strip().lower(), 'name': name.strip(), 'role': 'user', 'category': category}), 201), token)

    @app.post('/api/auth/login')
    def login():
        d = body()
        email = str(d.get('email') or '').strip().lower()[:254]
        if not auth.LIMITER.allow(f'login:{ip()}', 10, 300) or not auth.LIMITER.allow(f'login:{email}', 5, 300):
            err(429, 'rate_limited', 'Too many sign-in attempts. Wait 5 minutes.')
        u = g.db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        ok = auth.check_password(str(d.get('password') or ''), u['pw_hash'] if u else auth.DUMMY)
        if not (u and ok):
            err(401, 'invalid_credentials', 'Email or password is incorrect.')
        if u['disabled']:
            err(403, 'account_disabled', 'This account has been disabled by an administrator.')
        token = auth.create_session(g.db, u['id'], current_app.config['SESSION_HOURS'])
        if u['role'] == 'admin':
            audit(g.db, u['email'], 'admin.login')
        return set_cookie(make_response(jsonify(user={'id': u['id'], 'email': u['email'], 'name': u['name'], 'role': u['role'],
                                                       'category': u['category'] if 'category' in u.keys() else None,
                                                       'is_demo': bool(u['is_demo']) if 'is_demo' in u.keys() else False})), token)

    @app.post('/api/auth/logout')
    def logout():
        t = request.cookies.get(COOKIE)
        if t:
            g.db.execute('DELETE FROM sessions WHERE token_hash=?', (auth.tok_hash(t),))
            g.db.commit()
        resp = make_response(jsonify(ok=True))
        resp.delete_cookie(COOKIE, path='/')
        return resp

    @app.get('/api/auth/me')
    def me():
        return jsonify(user=current_user())

    # ---------------- collections & notes
    def own_collection(cid):
        c = g.db.execute('SELECT * FROM collections WHERE id=? AND user_id=?', (cid, current_user()['id'])).fetchone()
        if not c:
            err(404, 'not_found', 'Collection not found.')
        return c

    def collection_out(c):
        items = []
        for it in g.db.execute('SELECT kind,ref_id,added_at FROM collection_items WHERE collection_id=? ORDER BY added_at, rowid', (c['id'],)):
            if it['kind'] == 'report':
                r = g.db.execute('SELECT title FROM reports WHERE id=? AND status=\'approved\'', (it['ref_id'],)).fetchone()
            else:
                r = g.db.execute('SELECT name AS title FROM experiments WHERE id=? AND status=\'published\'', (it['ref_id'],)).fetchone()
            if r:
                items.append({'kind': it['kind'], 'id': it['ref_id'], 'title': r['title'], 'added_at': it['added_at']})
        return {'id': c['id'], 'name': c['name'], 'description': c['description'] if 'description' in c.keys() else None, 'created_at': c['created_at'], 'items': items}

    @app.get('/api/collections')
    @login_required
    def collections():
        rows = g.db.execute('SELECT * FROM collections WHERE user_id=? ORDER BY created_at', (current_user()['id'],)).fetchall()
        return jsonify(items=[collection_out(c) for c in rows])

    @app.post('/api/collections')
    @login_required
    def create_collection():
        d_ = body(); name = d_.get('name'); desc = d_.get('description')
        if desc is not None and (not isinstance(desc, str) or len(desc) > 300):
            err(422, 'validation_error', 'Description must be up to 300 characters.', {'description': 'length'})
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            err(422, 'validation_error', 'Name must be 1 to 80 characters.', {'name': 'length'})
        if g.db.execute('SELECT COUNT(*) FROM collections WHERE user_id=?', (current_user()['id'],)).fetchone()[0] >= 50:
            err(422, 'limit_reached', 'You can have up to 50 collections.')
        try:
            cur = g.db.execute('INSERT INTO collections (user_id,name,created_at,description) VALUES (?,?,?,?)', (current_user()['id'], name.strip(), now(), (desc or '').strip() or None))
        except Exception:
            err(409, 'duplicate', 'You already have a collection with this name.')
        g.db.commit()
        return jsonify(collection_out(g.db.execute('SELECT * FROM collections WHERE id=?', (cur.lastrowid,)).fetchone())), 201

    @app.patch('/api/collections/<int:cid>')
    @login_required
    def update_collection(cid):
        own_collection(cid)
        d = body()
        if 'name' in d:
            if not isinstance(d['name'], str) or not 1 <= len(d['name'].strip()) <= 80:
                err(422, 'validation_error', 'Name must be 1 to 80 characters.', {'name': 'length'})
            try:
                g.db.execute('UPDATE collections SET name=? WHERE id=?', (d['name'].strip(), cid))
            except Exception:
                err(409, 'duplicate', 'You already have a collection with this name.')
        if 'description' in d:
            if not isinstance(d['description'], str) or len(d['description']) > 300:
                err(422, 'validation_error', 'Description must be up to 300 characters.')
            g.db.execute('UPDATE collections SET description=? WHERE id=?', (d['description'].strip() or None, cid))
        g.db.commit()
        return jsonify(collection_out(g.db.execute('SELECT * FROM collections WHERE id=?', (cid,)).fetchone()))

    @app.get('/api/collections/<int:cid>')
    @login_required
    def get_collection(cid):
        return jsonify(collection_out(own_collection(cid)))

    @app.delete('/api/collections/<int:cid>')
    @login_required
    def delete_collection(cid):
        own_collection(cid)
        g.db.execute('DELETE FROM collections WHERE id=?', (cid,))
        g.db.commit()
        return jsonify(ok=True)

    @app.post('/api/collections/<int:cid>/items')
    @login_required
    def add_item(cid):
        c = own_collection(cid)
        d = body()
        kind, ref = d.get('kind'), d.get('id')
        if kind not in ('report', 'experiment') or not isinstance(ref, str):
            err(422, 'validation_error', 'kind must be report or experiment, with an id.')
        table, cond = ('reports', 'status=\'approved\'') if kind == 'report' else ('experiments', 'status=\'published\'')
        if not g.db.execute(f'SELECT 1 FROM {table} WHERE id=? AND {cond}', (ref,)).fetchone():
            err(404, 'not_found', f'{kind.title()} not found.')
        g.db.execute('INSERT OR IGNORE INTO collection_items VALUES (?,?,?,?)', (cid, kind, ref, now()))
        g.db.commit()
        return jsonify(collection_out(c)), 201

    @app.delete('/api/collections/<int:cid>/items/<kind>/<ref>')
    @login_required
    def remove_item(cid, kind, ref):
        c = own_collection(cid)
        g.db.execute('DELETE FROM collection_items WHERE collection_id=? AND kind=? AND ref_id=?', (cid, kind, ref))
        g.db.commit()
        return jsonify(collection_out(c))

    @app.get('/api/collections/<int:cid>/export')
    @login_required
    def export_collection(cid):
        c = collection_out(own_collection(cid))
        lines = [f'# {c["name"]}', '', 'Exported from CTRL+SPACE. Sources: NASA Technical Reports Server. CTRL+SPACE is not affiliated with or endorsed by NASA.', '']
        for it in c['items']:
            if it['kind'] == 'report':
                lines += [f'## {it["title"]}', f'- NTRS: https://ntrs.nasa.gov/citations/{it["id"]}']
                n = g.db.execute('SELECT text FROM notes WHERE user_id=? AND report_id=?', (current_user()['id'], it['id'])).fetchone()
                if n:
                    lines.append(f'- My notes: {n[0]}')
            else:
                e = exps.get_experiment(g.db, it['id'])
                lines.append(f'## {e["name"]} ({e["program"]})')
                for f in e['field_order']:
                    v = e['fields'][f['key']]
                    src = f' (NTRS {v["source"]["report_id"]}, {v["source"]["locator"]})' if v['source'] else ''
                    lines.append(f'- {f["label"]}: {v["value"] if v["state"] == "reported" else v["state_label"]}{src}')
            lines.append('')
        resp = make_response('\n'.join(lines))
        resp.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        safe = re.sub(r'[^A-Za-z0-9_-]+', '-', c['name'])[:40] or 'collection'
        resp.headers['Content-Disposition'] = f'attachment; filename="ctrl-space-{safe}.md"'
        return resp

    @app.put('/api/notes/<rid>')
    @login_required
    def put_note(rid):
        get_report_row(rid)
        text = body().get('text')
        if not isinstance(text, str) or len(text) > 5000:
            err(422, 'validation_error', 'Notes must be text up to 5000 characters.')
        if text.strip():
            g.db.execute('INSERT INTO notes VALUES (?,?,?,?) ON CONFLICT(user_id,report_id) DO UPDATE SET text=excluded.text, updated_at=excluded.updated_at',
                         (current_user()['id'], rid, text, now()))
        else:
            g.db.execute('DELETE FROM notes WHERE user_id=? AND report_id=?', (current_user()['id'], rid))
        g.db.commit()
        return jsonify(ok=True)

    # ---------------- admin
    @app.get('/api/admin/overview')
    @admin_required
    def admin_overview():
        q = lambda s: g.db.execute(s).fetchone()[0]
        return jsonify(users=q('SELECT COUNT(*) FROM users'), admins=q('SELECT COUNT(*) FROM users WHERE role=\'admin\''),
                       reports={s: q(f'SELECT COUNT(*) FROM reports WHERE status=\'{s}\'') for s in ('approved', 'pending', 'rejected')},
                       passages_verified=q('SELECT COUNT(*) FROM passages WHERE verified=1'),
                       passages_pending=q('SELECT COUNT(*) FROM passages WHERE verified=0'),
                       experiments=q('SELECT COUNT(*) FROM experiments'),
                       ai_provider=current_app.extensions['provider'].name)

    @app.get('/api/admin/reports')
    @admin_required
    def admin_reports():
        rows = g.db.execute('SELECT * FROM reports ORDER BY created_at DESC').fetchall()
        return jsonify(items=[report_public(r, g.db) | {'unverified_passages': g.db.execute('SELECT COUNT(*) FROM passages WHERE report_id=? AND verified=0', (r['id'],)).fetchone()[0]} for r in rows])

    @app.post('/api/admin/reports/<rid>/status')
    @admin_required
    def set_report_status(rid):
        get_report_row(rid)
        st = body().get('status')
        if st not in ('approved', 'rejected', 'pending'):
            err(422, 'validation_error', 'status must be approved, rejected or pending.')
        g.db.execute('UPDATE reports SET status=? WHERE id=?', (st, rid))
        g.db.commit()
        audit(g.db, current_user()['email'], f'report.{st}', rid)
        INDEX.build(g.db)
        return jsonify(ok=True)

    @app.get('/api/admin/passages')
    @admin_required
    def pending_passages():
        limit, offset = int_arg('limit', 25, 1, 100), int_arg('offset', 0, 0, 100000)
        total = g.db.execute('SELECT COUNT(*) FROM passages WHERE verified=0').fetchone()[0]
        rows = g.db.execute('SELECT p.id,p.report_id,p.locator,p.kind,p.text,p.flag_reason,r.title FROM passages p JOIN reports r ON r.id=p.report_id '
                            'WHERE p.verified=0 ORDER BY p.report_id, p.rowid LIMIT ? OFFSET ?', (limit, offset)).fetchall()
        return jsonify(page([dict(r) for r in rows], total, limit, offset))

    @app.post('/api/admin/passages/<pid>/review')
    @admin_required
    def review_passage(pid):
        d = body()
        action, kind = d.get('action'), d.get('kind')
        p = g.db.execute('SELECT * FROM passages WHERE id=?', (pid,)).fetchone()
        if not p:
            err(404, 'not_found', 'Passage not found.')
        if action == 'verify':
            if kind not in ('finding', 'method', 'condition', 'hypothesis', 'context'):
                err(422, 'validation_error', 'Choose what the passage is: finding, method, condition, hypothesis or context.')
            g.db.execute('UPDATE passages SET verified=1, kind=?, verified_by=?, verified_at=? WHERE id=?', (kind, current_user()['email'], now(), pid))
        elif action == 'reject':
            if g.db.execute('SELECT 1 FROM experiment_fields WHERE passage_id=?', (pid,)).fetchone():
                err(409, 'in_use', 'An experiment value cites this passage; change that value first.')
            tag = f'%"{pid}"%'
            if g.db.execute('SELECT 1 FROM lessons WHERE body LIKE ? UNION SELECT 1 FROM challenges WHERE body LIKE ?', (tag, tag)).fetchone():
                err(409, 'in_use', 'A lesson or challenge cites this passage; it can be flagged but not deleted.')
            g.db.execute('DELETE FROM passages WHERE id=?', (pid,))
        else:
            err(422, 'validation_error', 'action must be verify or reject.')
        g.db.commit()
        audit(g.db, current_user()['email'], f'passage.{action}', pid, kind)
        INDEX.build(g.db)
        return jsonify(ok=True)

    @app.post('/api/admin/ingest')
    @admin_required
    def admin_ingest():
        rid = str(body().get('ntrs_id') or '').strip()
        client = current_app.extensions['ntrs'] or ing.NTRSClient(current_app.config['NTRS_BASE'])
        try:
            res = ing.ingest(g.db, client, rid, current_app.config['STORAGE_DIR'])
        except ing.IngestError as e:
            g.db.commit()
            audit(g.db, current_user()['email'], 'ingest.failed', rid, e.code)
            err(e.status, e.code, str(e))
        audit(g.db, current_user()['email'], 'ingest.ok', rid, f'{res["pages"]} pages')
        INDEX.build(g.db)
        return jsonify(res), 201

    @app.post('/api/admin/reindex')
    @admin_required
    def reindex():
        n = INDEX.build(g.db)
        audit(g.db, current_user()['email'], 'search.reindex', None, f'{n} passages')
        return jsonify(indexed_passages=n)

    @app.get('/api/admin/audit')
    @admin_required
    def audit_log():
        limit, offset = int_arg('limit', 50, 1, 200), int_arg('offset', 0, 0, 100000)
        total = g.db.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
        rows = g.db.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
        return jsonify(page([dict(r) for r in rows], total, limit, offset))

    @app.get('/api/admin/ingestion-log')
    @admin_required
    def ingestion_log():
        rows = g.db.execute('SELECT * FROM ingestion_records ORDER BY id DESC LIMIT 100').fetchall()
        return jsonify(items=[dict(r) for r in rows])

    @app.get('/api/admin/users')
    @admin_required
    def users():
        rows = g.db.execute('SELECT id,email,name,role,disabled,created_at FROM users ORDER BY id').fetchall()
        return jsonify(items=[dict(r) for r in rows])
