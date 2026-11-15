"""Mobile-app endpoints: AI conversations (history, follow-up context, report scope, export), notifications,
admin-issued password resets, NASA Image and Video Library search (cached), public profiles, AI comparison."""
import hashlib
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from flask import current_app, g, jsonify, make_response, request

from . import admin_required, body, current_user, err, int_arg, login_required
from ..db import audit, notify, now
from ..services import assistant, auth
from ..services import experiments as exps
from ..services.search import tokens

FOLLOW_UP = re.compile(r'\b(it|its|they|them|this|that|these|those|there|same|why|how about|what about|and)\b', re.I)
NASA_IMAGES = 'https://images-api.nasa.gov/search'
PSI_SEARCH = 'https://psi.nasa.gov/geode-py/ws/repo/search'
PSI_INVESTIGATION = 'https://psi.nasa.gov/geode-py/ws/repo/investigations/{}'
PSI_LANDING = 'https://psi.nasa.gov/physci/repo/data/investigations/{}'
PSI_THUMB = 'https://psi.nasa.gov/geode-py/ws/investigations/{}/image'
PSI_ACCESSION = re.compile(r'^PSI-\d{1,5}$')


def _psi_investigation(d):
    files = [{'name': f.get('file_name'), 'size': f.get('file_size'), 'url': f.get('remote_url')}
             for f in (d.get('added') or []) if f.get('visible', True) and not f.get('restricted') and f.get('file_name')]
    return {'accession': d.get('accession'), 'title': d.get('title'), 'objective': d.get('objective'), 'approach': d.get('approach'),
            'research_area': d.get('researchArea'), 'sub_research_area': d.get('subResearchArea'), 'project_type': d.get('projectType'),
            'flight_platform': d.get('flightProgram') or d.get('missionName'), 'managing_center': d.get('managingNasaCenter'),
            'start_date': d.get('investigationStartDate'), 'end_date': d.get('investigationEndDate'),
            'doi': d.get('doi'), 'license_name': d.get('licenseName'), 'license_link': d.get('licenseLink'),
            'version': d.get('version'),
            'publications': [{'title': p.get('title'), 'authors': p.get('authorList'), 'doi': p.get('doi') or None,
                               'status': (p.get('status') or {}).get('annotationValue')} for p in (d.get('publications') or []) if p.get('title')],
            'files': files, 'file_count': len(files),
            'thumbnail': PSI_THUMB.format(d.get('accession')) if d.get('accession') else None,
            'landing_url': PSI_LANDING.format(d.get('accession')) if d.get('accession') else None}


def _psi_item(src):
    person = src.get('Person') or {}
    pi = ' '.join(filter(None, [person.get('First Name'), person.get('Middle Initials'), person.get('Last Name')])).strip()
    acc = src.get('Accession', '')
    return {'accession': acc, 'title': src.get('Title', ''), 'pi': pi or None,
            'keywords': [k.strip() for k in re.split(r'\s{2,}|,', src.get('Keywords') or '') if k.strip()],
            'research_area': src.get('Research Area'), 'sub_research_area': src.get('SubResearch Area') or None,
            'project_type': src.get('Project Type'), 'flight_platform': src.get('Flight Platform') or None,
            'start_date': src.get('Investigation Start Date'), 'end_date': src.get('Investigation End Date'),
            'sponsoring_agency': src.get('Sponsoring Agency'), 'monitoring_center': src.get('Monitoring Center'),
            'objectives': src.get('Objectives'), 'approach': src.get('Approach'),
            'thumbnail': PSI_THUMB.format(acc) if acc else None, 'landing_url': PSI_LANDING.format(acc) if acc else None}


def _answer_text(a):
    return a['answer'] if a.get('status') == 'answered' else {'insufficient_evidence': 'Insufficient evidence', 'evidence_only': 'Retrieval-only: verified evidence shown'}.get(a.get('status'), '')


def register_mobile(app):
    # ---------------- AI conversations
    @app.post('/api/assistant/ask')
    def assistant_ask():
        if not auth.LIMITER.allow(f'ask:{request.remote_addr}', 20, 300):
            err(429, 'rate_limited', 'Too many questions. Wait a few minutes and try again.')
        d = body()
        q, cid, rid = d.get('question'), d.get('conversation_id'), d.get('report_id')
        if not isinstance(q, str) or not 3 <= len(q.strip()) <= 400:
            err(422, 'validation_error', 'Questions must be 3 to 400 characters.')
        q = q.strip()
        if rid is not None and (not isinstance(rid, str) or not g.db.execute("SELECT 1 FROM reports WHERE id=? AND status='approved'", (rid,)).fetchone()):
            err(404, 'not_found', 'Report not found.')
        u = current_user()
        prev = None
        if cid is not None:
            if not u:
                err(401, 'unauthenticated', 'Sign in to continue a saved conversation.')
            conv = g.db.execute('SELECT * FROM conversations WHERE id=? AND user_id=?', (cid, u['id'])).fetchone() if isinstance(cid, int) else None
            if not conv:
                err(404, 'not_found', 'Conversation not found.')
            rid = rid or conv['report_id']
            last = g.db.execute("SELECT content FROM messages WHERE conversation_id=? AND role='user' ORDER BY id DESC LIMIT 1", (cid,)).fetchone()
            prev = last[0] if last else None
        # Context: a short or referring follow-up is retrieved together with the previous question.
        follow = bool(prev and (len(tokens(q)) <= 4 or FOLLOW_UP.search(q)))
        rq = f'{prev} {q}' if follow else None
        g.lock.release()
        try:
            res = assistant.answer(q, current_app.extensions['provider'], 6, retrieval_query=rq, report_id=rid)
        finally:
            g.lock.acquire()
        res['context_used'] = {'follow_up': follow, 'previous_question': prev if follow else None, 'report_scope': rid}
        if u:
            t = now()
            if cid is None:
                cid = g.db.execute('INSERT INTO conversations (user_id,title,report_id,created_at,updated_at) VALUES (?,?,?,?,?)', (u['id'], q[:80], rid, t, t)).lastrowid
            g.db.execute('INSERT INTO messages (conversation_id,role,content,created_at) VALUES (?,?,?,?)', (cid, 'user', q, t))
            res['message_id'] = g.db.execute('INSERT INTO messages (conversation_id,role,content,created_at) VALUES (?,?,?,?)', (cid, 'assistant', json.dumps(res), t)).lastrowid
            g.db.execute('UPDATE messages SET content=? WHERE id=?', (json.dumps(res), res['message_id']))
            g.db.execute('UPDATE conversations SET updated_at=? WHERE id=?', (t, cid))
            g.db.commit()
            res['conversation_id'] = cid
        return jsonify(res)

    @app.get('/api/conversations')
    @login_required
    def conversations():
        rows = g.db.execute('SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id AND m.role=\'user\') n FROM conversations c WHERE user_id=? ORDER BY updated_at DESC LIMIT 50', (current_user()['id'],)).fetchall()
        return jsonify(items=[{'id': r['id'], 'title': r['title'], 'report_id': r['report_id'], 'questions': r['n'], 'updated_at': r['updated_at']} for r in rows])

    def own_conv(cid):
        c = g.db.execute('SELECT * FROM conversations WHERE id=? AND user_id=?', (cid, current_user()['id'])).fetchone()
        if not c:
            err(404, 'not_found', 'Conversation not found.')
        return c

    @app.get('/api/conversations/<int:cid>')
    @login_required
    def conversation(cid):
        c = own_conv(cid)
        msgs = [{'id': m['id'], 'role': m['role'], 'created_at': m['created_at'], 'content': m['content'] if m['role'] == 'user' else {**json.loads(m['content']), 'message_id': m['id']}}
                for m in g.db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id', (cid,))]
        return jsonify(id=c['id'], title=c['title'], report_id=c['report_id'], messages=msgs)

    @app.delete('/api/conversations/<int:cid>')
    @login_required
    def delete_conversation(cid):
        own_conv(cid)
        g.db.execute('DELETE FROM conversations WHERE id=?', (cid,)); g.db.commit()
        return jsonify(ok=True)

    @app.get('/api/conversations/<int:cid>/export')
    @login_required
    def export_conversation(cid):
        c = own_conv(cid)
        L = [f"# {c['title']}", '', 'CTRL+SPACE research conversation. Answers come only from verified NASA passages; AI text is a reading aid, not primary evidence. Not affiliated with or endorsed by NASA.', '']
        for m in g.db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id', (cid,)):
            if m['role'] == 'user':
                L += [f"## Q: {m['content']}", '']
                continue
            a = json.loads(m['content'])
            L += [f"**Evidence coverage:** {a.get('coverage', {}).get('label', '—')} · **Mode:** {a.get('mode', '—')}", '']
            if a.get('status') == 'answered':
                L += [a['answer'], ''] + [f"- {p['text']} [" + '; '.join(f"NTRS {x['report_id']}, {x['locator']}" for x in p['citations']) + ']' for p in a['points']] + ['']
            elif a.get('status') == 'insufficient_evidence':
                L += ['Insufficient scientific evidence was found in the available research collection to provide a reliable answer.', '']
            L += [f"> {e['text']}\n>\n> — NTRS {e['report_id']}, {e['locator']}" for e in a.get('evidence', [])] + ['']
        resp = make_response('\n'.join(L))
        resp.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename="ctrl-space-conversation.md"'
        return resp

    @app.post('/api/feedback')
    @login_required
    def feedback():
        d = body(); mid, rating = d.get('message_id'), d.get('rating')
        if not isinstance(mid, int) or rating not in ('up', 'down'):
            err(422, 'validation_error', 'message_id and rating (up/down) are required.')
        m = g.db.execute("SELECT m.id FROM messages m JOIN conversations c ON c.id=m.conversation_id WHERE m.id=? AND c.user_id=? AND m.role='assistant'", (mid, current_user()['id'])).fetchone()
        if not m:
            err(404, 'not_found', 'Answer not found.')
        g.db.execute('INSERT INTO answer_feedback VALUES (?,?,?,?) ON CONFLICT(user_id,message_id) DO UPDATE SET rating=excluded.rating', (current_user()['id'], mid, rating, now()))
        g.db.commit()
        return jsonify(ok=True)

    @app.post('/api/answers/<int:mid>/save')
    @login_required
    def save_answer(mid):
        m = g.db.execute("SELECT m.id FROM messages m JOIN conversations c ON c.id=m.conversation_id WHERE m.id=? AND c.user_id=? AND m.role='assistant'", (mid, current_user()['id'])).fetchone()
        if not m:
            err(404, 'not_found', 'Answer not found.')
        g.db.execute('INSERT OR IGNORE INTO saved_answers VALUES (?,?,?)', (current_user()['id'], mid, now())); g.db.commit()
        return jsonify(ok=True)

    @app.delete('/api/answers/<int:mid>/save')
    @login_required
    def unsave_answer(mid):
        g.db.execute('DELETE FROM saved_answers WHERE user_id=? AND message_id=?', (current_user()['id'], mid)); g.db.commit()
        return jsonify(ok=True)

    @app.get('/api/answers/saved')
    @login_required
    def saved_answers():
        out = []
        for r in g.db.execute('SELECT s.message_id, s.saved_at, m.content, m.conversation_id, (SELECT content FROM messages q WHERE q.conversation_id=m.conversation_id AND q.role=\'user\' AND q.id<m.id ORDER BY q.id DESC LIMIT 1) question '
                              'FROM saved_answers s JOIN messages m ON m.id=s.message_id WHERE s.user_id=? ORDER BY s.saved_at DESC', (current_user()['id'],)):
            a = json.loads(r['content'])
            out.append({'message_id': r['message_id'], 'conversation_id': r['conversation_id'], 'question': r['question'], 'saved_at': r['saved_at'],
                        'status': a.get('status'), 'mode': a.get('mode'), 'coverage': (a.get('coverage') or {}).get('label'),
                        'answer': a.get('answer'), 'sources': sorted({e['report_id'] for e in a.get('evidence', [])})})
        return jsonify(items=out)

    # ---------------- client error monitoring (first-party; no third-party service required)
    @app.post('/api/client-errors')
    def client_error():
        if not auth.LIMITER.allow(f'cerr:{request.remote_addr}', 30, 600):
            return jsonify(ok=True)                                   # silently drop floods
        d = body()
        msg = str(d.get('message') or '')[:500]
        if not msg:
            err(422, 'validation_error', 'message is required.')
        g.db.execute('INSERT INTO client_errors (at,kind,message,source,route,user_agent) VALUES (?,?,?,?,?,?)',
                     (now(), str(d.get('kind') or 'error')[:20], msg, str(d.get('source') or '')[:300], str(d.get('route') or '')[:200], request.headers.get('User-Agent', '')[:200]))
        g.db.execute('DELETE FROM client_errors WHERE id NOT IN (SELECT id FROM client_errors ORDER BY id DESC LIMIT 1000)'); g.db.commit()
        return jsonify(ok=True), 201

    @app.get('/api/admin/client-errors')
    @admin_required
    def client_errors():
        return jsonify(items=[dict(r) for r in g.db.execute('SELECT * FROM client_errors ORDER BY id DESC LIMIT 100')])

    # ---------------- notifications
    @app.get('/api/notifications')
    @login_required
    def notifications():
        uid = current_user()['id']
        rows = g.db.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 50', (uid,)).fetchall()
        unread = g.db.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND read_at IS NULL', (uid,)).fetchone()[0]
        return jsonify(unread=unread, items=[dict(r) for r in rows])

    @app.post('/api/notifications/read')
    @login_required
    def notifications_read():
        ids = body().get('ids')
        uid = current_user()['id']
        if ids == 'all':
            g.db.execute('UPDATE notifications SET read_at=? WHERE user_id=? AND read_at IS NULL', (now(), uid))
        elif isinstance(ids, list) and all(isinstance(i, int) for i in ids) and len(ids) <= 100:
            g.db.executemany('UPDATE notifications SET read_at=? WHERE id=? AND user_id=?', [(now(), i, uid) for i in ids])
        else:
            err(422, 'validation_error', 'ids must be "all" or a list of notification IDs.')
        g.db.commit()
        return jsonify(ok=True)

    # ---------------- password reset (no email service: admin-issued one-time links)
    @app.post('/api/auth/forgot')
    def forgot():
        if not auth.LIMITER.allow(f'forgot:{request.remote_addr}', 5, 3600):
            err(429, 'rate_limited', 'Too many requests. Try again later.')
        email = str(body().get('email') or '').strip().lower()[:254]
        u = g.db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if u:
            for a in g.db.execute("SELECT id FROM users WHERE role='admin' AND disabled=0"):
                notify(g.db, a['id'], 'system', 'Password reset requested', f'For {email}. Issue a one-time reset link in Admin → Users if the request is genuine.', '/admin')
            g.db.commit()
        return jsonify(message='If an account exists for this email, an administrator has been notified. CTRL+SPACE has no email service, so an administrator will give you a one-time reset link.')

    @app.post('/api/admin/users/<int:uid>/reset-link')
    @admin_required
    def reset_link(uid):
        u = g.db.execute('SELECT email FROM users WHERE id=?', (uid,)).fetchone()
        if not u:
            err(404, 'not_found', 'User not found.')
        token = secrets.token_urlsafe(32)
        exp = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        g.db.execute('DELETE FROM password_resets WHERE user_id=?', (uid,))
        g.db.execute('INSERT INTO password_resets VALUES (?,?,?,?,NULL)', (hashlib.sha256(token.encode()).hexdigest(), uid, current_user()['email'], exp))
        g.db.commit()
        audit(g.db, current_user()['email'], 'user.reset_link', u['email'])
        return jsonify(url=f'/app/reset?token={token}', expires_at=exp, note='Shown once. Give it to the user privately; it expires in 1 hour and works once.')

    @app.post('/api/auth/reset')
    def reset_password():
        d = body()
        tok, pw = str(d.get('token') or ''), d.get('password')
        r = g.db.execute('SELECT * FROM password_resets WHERE token_hash=?', (hashlib.sha256(tok.encode()).hexdigest(),)).fetchone()
        if not r or r['used_at'] or r['expires_at'] < datetime.now(timezone.utc).isoformat():
            err(400, 'invalid_token', 'This reset link is invalid or has expired. Ask an administrator for a new one.')
        u = g.db.execute('SELECT email, name FROM users WHERE id=?', (r['user_id'],)).fetchone()
        errors = auth.validate_signup(u['email'], u['name'], pw)
        if errors:
            err(422, 'validation_error', errors['password'], {'password': errors['password']})
        g.db.execute('UPDATE users SET pw_hash=? WHERE id=?', (auth.hash_password(pw), r['user_id']))
        g.db.execute('UPDATE password_resets SET used_at=? WHERE token_hash=?', (now(), r['token_hash']))
        g.db.execute('DELETE FROM sessions WHERE user_id=?', (r['user_id'],))
        g.db.commit()
        return jsonify(ok=True, message='Password changed. Sign in with your new password.')

    # ---------------- NASA Image and Video Library (official API, no key), cached for offline use
    @app.get('/api/media/search')
    def media_search():
        q = (request.args.get('q') or '').strip()
        if not 2 <= len(q) <= 80:
            err(422, 'validation_error', 'q must be 2 to 80 characters.')
        page = int_arg('page', 1, 1, 20)
        key = q.lower()
        cached = g.db.execute('SELECT payload, fetched_at FROM media_cache WHERE query=? AND page=?', (key, page)).fetchone()
        fresh = cached and cached['fetched_at'] > (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        if fresh:
            return jsonify({**json.loads(cached['payload']), 'cached': True})
        url = NASA_IMAGES + '?' + urllib.parse.urlencode({'q': q, 'media_type': 'image', 'page': page})
        opener = current_app.extensions.get('media_opener') or urllib.request.urlopen
        g.lock.release()
        try:
            with opener(urllib.request.Request(url, headers={'User-Agent': 'CTRL-SPACE/5'}), timeout=12) as r:
                raw = json.loads(r.read(2_000_000).decode())
            ok = True
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, OSError):
            ok = False
        finally:
            g.lock.acquire()
        if not ok:
            if cached:
                return jsonify({**json.loads(cached['payload']), 'cached': True, 'stale': True})
            err(503, 'requires_internet', 'NASA Image Library needs an internet connection. Nothing is saved for this search yet.')
        items = []
        for it in (raw.get('collection') or {}).get('items', [])[:24]:
            d = (it.get('data') or [{}])[0]
            thumb = next((l.get('href') for l in it.get('links') or [] if l.get('render') == 'image' or str(l.get('href', '')).endswith('.jpg')), None)
            if not d.get('nasa_id') or not thumb or not thumb.startswith('https://images-assets.nasa.gov/'):
                continue
            items.append({'nasa_id': d['nasa_id'], 'title': str(d.get('title', ''))[:200], 'description': re.sub(r'<[^>]+>', '', str(d.get('description', '')))[:600],
                          'date_created': str(d.get('date_created', ''))[:10], 'center': d.get('center'), 'thumb': thumb,
                          'details_url': f"https://images.nasa.gov/details/{urllib.parse.quote(d['nasa_id'])}"})
        payload = {'query': q, 'page': page, 'items': items, 'total': ((raw.get('collection') or {}).get('metadata') or {}).get('total_hits'),
                   'source': 'NASA Image and Video Library (images-api.nasa.gov)', 'retrieved_at': now(),
                   'usage': 'NASA imagery is generally not copyrighted, but check each item’s details page; use does not imply NASA endorsement.'}
        g.db.execute('INSERT OR REPLACE INTO media_cache VALUES (?,?,?,?)', (key, page, json.dumps(payload), now())); g.db.commit()
        return jsonify({**payload, 'cached': False})

    # ---------------- NASA Physical Sciences Informatics (PSI) Data Repository, cached for offline use
    @app.get('/api/psi/search')
    def psi_search():
        q = (request.args.get('q') or 'combustion').strip()
        if not 2 <= len(q) <= 80:
            err(422, 'validation_error', 'q must be 2 to 80 characters.')
        key = q.lower()
        cached = g.db.execute('SELECT payload, fetched_at FROM psi_cache WHERE term=?', (key,)).fetchone()
        fresh = cached and cached['fetched_at'] > (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        if fresh:
            return jsonify({**json.loads(cached['payload']), 'cached': True})
        url = PSI_SEARCH + '?' + urllib.parse.urlencode({'term': q, 'source': 'psi', 'type': 'investigation', 'sort': 'Public Release Date', 'order': 'desc'})
        opener = current_app.extensions.get('psi_opener') or urllib.request.urlopen
        g.lock.release()
        try:
            with opener(urllib.request.Request(url, headers={'User-Agent': 'CTRL-SPACE/5'}), timeout=12) as r:
                raw = json.loads(r.read(3_000_000).decode())
            ok = True
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, OSError):
            ok = False
        finally:
            g.lock.acquire()
        if not ok:
            if cached:
                return jsonify({**json.loads(cached['payload']), 'cached': True, 'stale': True})
            err(503, 'requires_internet', 'NASA PSI Data Repository needs an internet connection. Nothing is saved for this search yet.')
        hits = ((raw.get('hits') or {}).get('hits')) or []
        items = [_psi_item(h['_source']) for h in hits if h.get('_source')]
        payload = {'query': q, 'items': items, 'total': (raw.get('hits') or {}).get('total'),
                   'source': 'NASA Physical Sciences Informatics (PSI) Data Repository', 'source_url': 'https://psi.nasa.gov/physci/repo/search?q=' + urllib.parse.quote(q),
                   'retrieved_at': now(),
                   'usage': 'Cite investigations by their PSI accession ID (see “Cite this Investigation” on each investigation’s page at psi.nasa.gov). Not affiliated with or endorsed by NASA.'}
        g.db.execute('INSERT OR REPLACE INTO psi_cache VALUES (?,?,?)', (key, json.dumps(payload), now())); g.db.commit()
        return jsonify({**payload, 'cached': False})

    @app.get('/api/psi/investigation/<accession>')
    def psi_investigation(accession):
        accession = accession.upper()
        if not PSI_ACCESSION.match(accession):
            err(422, 'validation_error', 'PSI accession IDs look like PSI-26.')
        cached = g.db.execute('SELECT payload, fetched_at FROM psi_investigation_cache WHERE accession=?', (accession,)).fetchone()
        fresh = cached and cached['fetched_at'] > (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        if fresh:
            return jsonify({**json.loads(cached['payload']), 'cached': True})
        opener = current_app.extensions.get('psi_opener') or urllib.request.urlopen
        g.lock.release()
        try:
            with opener(urllib.request.Request(PSI_INVESTIGATION.format(accession), headers={'User-Agent': 'CTRL-SPACE/5', 'Accept': 'application/json'}), timeout=12) as r:
                raw = json.loads(r.read(5_000_000).decode())
            ok = bool(raw.get('accession'))
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, OSError):
            ok = False
        finally:
            g.lock.acquire()
        if not ok:
            if cached:
                return jsonify({**json.loads(cached['payload']), 'cached': True, 'stale': True})
            err(503, 'requires_internet', 'NASA PSI Data Repository needs an internet connection, and this investigation was never viewed before so nothing is saved offline.')
        payload = {**_psi_investigation(raw), 'source': 'NASA Physical Sciences Informatics (PSI) Data Repository', 'retrieved_at': now(),
                   'usage': 'Cite this investigation by its PSI accession ID and DOI (see "Cite this Investigation" on its page at psi.nasa.gov). Not affiliated with or endorsed by NASA.'}
        g.db.execute('INSERT OR REPLACE INTO psi_investigation_cache VALUES (?,?,?)', (accession, json.dumps(payload), now())); g.db.commit()
        return jsonify({**payload, 'cached': False})

    # ---------------- public profiles
    @app.get('/api/users/<int:uid>')
    def public_profile(uid):
        u = g.db.execute('SELECT id,name,role,created_at,disabled FROM users WHERE id=?', (uid,)).fetchone()
        if not u or u['disabled']:
            err(404, 'not_found', 'User not found.')
        q = lambda s: g.db.execute(s, (uid,)).fetchone()[0]
        posts = [dict(r) for r in g.db.execute("SELECT id,title,room_id,created_at FROM posts WHERE user_id=? AND parent_id IS NULL AND status='visible' ORDER BY id DESC LIMIT 10", (uid,))]
        return jsonify(id=u['id'], name=u['name'], role='Administrator' if u['role'] == 'admin' else 'Researcher', joined=u['created_at'][:10],
                       contributions={'discussions': q("SELECT COUNT(*) FROM posts WHERE user_id=? AND parent_id IS NULL AND status='visible'"),
                                      'replies': q("SELECT COUNT(*) FROM posts WHERE user_id=? AND parent_id IS NOT NULL AND status='visible'"),
                                      'shared_research': q("SELECT COUNT(*) FROM posts WHERE user_id=? AND ref_kind IS NOT NULL AND status='visible'"),
                                      'challenges_passed': q('SELECT COUNT(DISTINCT challenge_id) FROM challenge_attempts WHERE user_id=? AND passed=1')},
                       recent_discussions=posts)

    # ---------------- AI comparison grounded in the experiments' own source passages
    @app.post('/api/compare/ai')
    def compare_ai():
        ids = body().get('experiment_ids')
        if not isinstance(ids, list) or not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids) or not all(isinstance(i, str) for i in ids):
            err(422, 'validation_error', 'experiment_ids must list 2 to 4 different experiment IDs.')
        cmp_, missing = exps.compare(g.db, ids)
        if missing:
            err(404, 'not_found', 'Some experiments were not found.', {'missing': missing})
        pids = sorted({c['source']['passage_id'] for r in cmp_['rows'] for c in r['cells'] if c.get('source')})
        rows = g.db.execute(f"SELECT p.id,p.report_id,p.locator,p.kind,p.text,r.title FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.verified=1 AND p.id IN ({','.join('?' * len(pids))})", pids).fetchall()
        ev = [assistant.evidence_payload({**dict(r), 'score': 0}) for r in rows]
        provider = current_app.extensions['provider']
        base = {'experiments': cmp_['experiments'], 'evidence': ev, 'context_warnings': cmp_['levels']['level2'], 'rule': cmp_['levels']['level3']['rule'], 'provider': provider.name}
        if provider.name == 'none':
            return jsonify({**base, 'status': 'retrieval_only', 'reason': 'No AI provider is configured; the comparison tables and notes are shown without a generated summary.'})
        names = '; '.join(e['name'] for e in cmp_['experiments'])
        ctx = '\n'.join(f'[{e["passage_id"]}] ({assistant.KIND_LABEL[e["kind"]]}) NTRS {e["report_id"]}, {e["locator"]}: """{e["text"]}"""' for e in ev)
        warn = '\n'.join(f"- {w['title']}: {w['message']}" for w in cmp_['levels']['level2'])
        g.lock.release()
        try:
            raw = provider.generate(assistant.SYSTEM_RULES, f'Compare these experiments: {names}.\nKnown differences that limit comparison:\n{warn}\n'
                                    f'Do not claim that any condition caused a difference unless a passage states it.\n\nPassages:\n{ctx}\n\n{assistant.STRUCTURE}')
        except assistant.ProviderError as e:
            return jsonify({**base, 'status': 'retrieval_only', 'reason': str(e)})
        finally:
            g.lock.acquire()
        try:
            j = assistant.parse_json(raw)
        except (ValueError, json.JSONDecodeError):
            return jsonify({**base, 'status': 'retrieval_only', 'reason': 'The AI response was not valid JSON, so it was discarded.'})
        by_id = {e['passage_id']: e for e in ev}; warnings = []
        sections = {k: assistant._items(j.get(k), set(by_id), by_id, warnings, k)[0] for k in ('direct_answer', 'explanation', 'evidence', 'conditions')}
        if not sections['direct_answer']:
            return jsonify({**base, 'status': 'retrieval_only', 'reason': 'The AI summary had no valid citation, so it was discarded.'})
        return jsonify({**base, 'status': 'answered', 'sections': {**sections, 'limitations': str(j.get('limitations') or '')}, 'warnings': warnings,
                        'disclaimer': 'AI-generated from the experiments’ own source passages. Not primary evidence.'})
