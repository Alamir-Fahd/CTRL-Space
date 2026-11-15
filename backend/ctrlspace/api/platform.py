"""Platform features: profile & settings, activity, notes list, learning studio, challenges,
community (rooms, posts, comments, reporting, moderation), admin user management,
experiment approval and privacy-conscious analytics."""
import json
import re
from datetime import date, datetime, timedelta, timezone

from flask import current_app, g, jsonify, make_response, request

from . import COOKIE, admin_required, body, current_user, err, int_arg, ip, login_required, page
from ..db import audit, now
from ..services import auth
from ..services import experiments as exps

THEMES = ('system', 'light', 'dark')
ACTIVITY = {'report': ('viewed_report', 'report'), 'experiment': ('viewed_experiment', 'experiment'),
            'ask': ('asked', None), 'compare': ('compared', None)}
METRIC = {'ask': 'ask', 'search': 'search', 'compare': 'compare', 'register_user': 'signup',
          'create_post': 'post', 'attempt_challenge': 'challenge_attempt', 'complete_lesson': 'lesson_completed'}


def bump(name):
    g.db.execute('INSERT INTO metrics (day,name,count) VALUES (?,?,1) ON CONFLICT(day,name) DO UPDATE SET count=count+1',
                 (date.today().isoformat(), name))


def prefs_of(uid):
    row = g.db.execute('SELECT prefs FROM users WHERE id=?', (uid,)).fetchone()
    try:
        return json.loads(row[0]) if row else {}
    except ValueError:
        return {}


def user_public(r):
    keys = r.keys()
    return {'id': r['id'], 'name': r['name'], 'email': r['email'], 'role': r['role'], 'created_at': r['created_at'],
            'bio': r['bio'] if 'bio' in keys else None, 'interests': json.loads(r['interests']) if 'interests' in keys and r['interests'] else [],
            'category': r['category'] if 'category' in keys else None, 'is_demo': bool(r['is_demo']) if 'is_demo' in keys else False,
            'institution': r['institution'] if 'institution' in keys else None}


def name_of(uid):
    r = g.db.execute('SELECT name FROM users WHERE id=?', (uid,)).fetchone()
    return r[0] if r else 'Deleted user'


def ref_title(kind, rid):
    if kind == 'report':
        r = g.db.execute("SELECT title FROM reports WHERE id=? AND status='approved'", (rid,)).fetchone()
    elif kind == 'experiment':
        r = g.db.execute("SELECT name FROM experiments WHERE id=? AND status='published'", (rid,)).fetchone()
    else:
        return None
    return r[0] if r else None


def register_platform(app):
    @app.after_request
    def _track(resp):
        # Personal activity (only for signed-in users, visible only to them) + anonymous daily counters.
        try:
            ep = request.endpoint
            if resp.status_code < 400 and ep in METRIC and 'db' in g:
                bump(METRIC[ep])
            u = current_user() if (resp.status_code == 200 and ep in ACTIVITY) else None
            if u and prefs_of(u['id']).get('history', True):
                action, kind = ACTIVITY[ep]
                if ep == 'report':
                    rid, label = request.view_args['rid'], ref_title('report', request.view_args['rid'])
                elif ep == 'experiment':
                    rid, label = request.view_args['eid'], ref_title('experiment', request.view_args['eid'])
                elif ep == 'ask':
                    rid, label = None, str((request.get_json(silent=True) or {}).get('question', ''))[:200]
                else:
                    rid, label = None, ', '.join((request.get_json(silent=True) or {}).get('experiment_ids', []))[:200]
                g.db.execute('INSERT INTO activity (user_id,at,action,ref_kind,ref_id,label) VALUES (?,?,?,?,?,?)',
                             (u['id'], now(), action, kind, rid, label))
                g.db.execute('DELETE FROM activity WHERE user_id=? AND id NOT IN (SELECT id FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 200)', (u['id'], u['id']))
            g.db.commit()
        except Exception:  # tracking must never break a response
            current_app.logger.exception('activity tracking failed')
        return resp

    # ---------------- profile & settings
    @app.get('/api/me')
    @login_required
    def me_profile():
        u = current_user()
        r = g.db.execute('SELECT * FROM users WHERE id=?', (u['id'],)).fetchone()
        q = lambda s: g.db.execute(s, (u['id'],)).fetchone()[0]
        return jsonify(user=user_public(r), prefs={'theme': 'system', 'history': True, **prefs_of(u['id'])},
                       counts={'collections': q('SELECT COUNT(*) FROM collections WHERE user_id=?'),
                               'notes': q('SELECT COUNT(*) FROM notes WHERE user_id=?'),
                               'lessons_completed': q('SELECT COUNT(*) FROM lesson_progress WHERE user_id=?'),
                               'challenges_passed': q('SELECT COUNT(DISTINCT challenge_id) FROM challenge_attempts WHERE user_id=? AND passed=1'),
                               'posts': q("SELECT COUNT(*) FROM posts WHERE user_id=? AND status='visible'")})

    @app.patch('/api/me')
    @login_required
    def me_update():
        d = body()
        u = current_user()
        if 'name' in d:
            name = d['name']
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
                err(422, 'validation_error', 'Name must be 1 to 60 characters.', {'name': 'length'})
            g.db.execute('UPDATE users SET name=? WHERE id=?', (name.strip(), u['id']))
        if 'bio' in d:
            if not isinstance(d['bio'], str) or len(d['bio']) > 500:
                err(422, 'validation_error', 'Bio must be up to 500 characters.', {'bio': 'length'})
            g.db.execute('UPDATE users SET bio=? WHERE id=?', (d['bio'].strip(), u['id']))
        if 'interests' in d:
            it = d['interests']
            if not isinstance(it, list) or len(it) > 8 or not all(isinstance(x, str) and 1 <= len(x.strip()) <= 40 for x in it):
                err(422, 'validation_error', 'Up to 8 research interests, each 1 to 40 characters.', {'interests': 'invalid'})
            g.db.execute('UPDATE users SET interests=? WHERE id=?', (json.dumps([x.strip() for x in it]), u['id']))
        if 'category' in d:
            if d['category'] not in (None, '') and d['category'] not in auth.CATEGORIES:
                err(422, 'validation_error', 'Choose a valid category.', {'category': 'invalid'})
            g.db.execute('UPDATE users SET category=? WHERE id=?', (d['category'] or None, u['id']))
        if 'institution' in d:
            if not isinstance(d['institution'], str) or len(d['institution']) > 120:
                err(422, 'validation_error', 'Institution must be up to 120 characters.', {'institution': 'length'})
            g.db.execute('UPDATE users SET institution=? WHERE id=?', (d['institution'].strip() or None, u['id']))
        if 'prefs' in d:
            p = d['prefs']
            notif = p.get('notify', {})
            if not isinstance(p, dict) or set(p) - {'theme', 'history', 'notify', 'onboarded'} or p.get('theme', 'system') not in THEMES \
                    or not isinstance(p.get('history', True), bool) or not isinstance(p.get('onboarded', True), bool) \
                    or not isinstance(notif, dict) or set(notif) - {'replies', 'moderation', 'system'} or not all(isinstance(v, bool) for v in notif.values()):
                err(422, 'validation_error', 'Preferences support theme (system, light, dark) and history (true/false).')
            if p.get('history') is False:
                g.db.execute('DELETE FROM activity WHERE user_id=?', (u['id'],))
            g.db.execute('UPDATE users SET prefs=? WHERE id=?', (json.dumps({**prefs_of(u['id']), **p}), u['id']))
        g.db.commit()
        g.pop('user', None)
        return me_profile()

    @app.post('/api/me/password')
    @login_required
    def me_password():
        d = body()
        u = current_user()
        if not auth.LIMITER.allow(f'pw:{u["id"]}', 5, 900):
            err(429, 'rate_limited', 'Too many attempts. Wait 15 minutes.')
        row = g.db.execute('SELECT pw_hash FROM users WHERE id=?', (u['id'],)).fetchone()
        if not auth.check_password(str(d.get('current_password') or ''), row[0]):
            err(422, 'validation_error', 'Current password is incorrect.', {'current_password': 'incorrect'})
        errors = auth.validate_signup(u['email'], u['name'], d.get('new_password'))
        if errors:
            err(422, 'validation_error', errors['password'], {'new_password': errors['password']})
        g.db.execute('UPDATE users SET pw_hash=? WHERE id=?', (auth.hash_password(d['new_password']), u['id']))
        keep = auth.tok_hash(request.cookies.get(COOKIE, ''))
        g.db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?', (u['id'], keep))   # sign out other devices
        g.db.commit()
        return jsonify(ok=True, message='Password changed. Other devices were signed out.')

    @app.delete('/api/me')
    @login_required
    def me_delete():
        u = current_user()
        if not auth.check_password(str(body().get('password') or ''), g.db.execute('SELECT pw_hash FROM users WHERE id=?', (u['id'],)).fetchone()[0]):
            err(422, 'validation_error', 'Password is incorrect.', {'password': 'incorrect'})
        if u['role'] == 'admin' and g.db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0] <= 1:
            err(409, 'last_admin', 'You are the only administrator. Promote someone else first.')
        g.db.execute('DELETE FROM users WHERE id=?', (u['id'],))   # cascades: sessions, notes, collections, activity, posts
        g.db.commit()
        audit(g.db, 'self', 'user.deleted', str(u['id']))
        resp = make_response(jsonify(ok=True))
        resp.delete_cookie(COOKIE, path='/')
        return resp

    @app.get('/api/me/activity')
    @login_required
    def me_activity():
        limit = int_arg('limit', 30, 1, 200)
        rows = g.db.execute('SELECT at,action,ref_kind,ref_id,label FROM activity WHERE user_id=? ORDER BY id DESC LIMIT ?',
                            (current_user()['id'], limit)).fetchall()
        return jsonify(items=[dict(r) for r in rows])

    @app.delete('/api/me/activity')
    @login_required
    def me_activity_clear():
        g.db.execute('DELETE FROM activity WHERE user_id=?', (current_user()['id'],))
        g.db.commit()
        return jsonify(ok=True)

    @app.get('/api/me/recent')
    @login_required
    def me_recent():
        rows = g.db.execute("SELECT ref_kind, ref_id, MAX(at) AS at FROM activity WHERE user_id=? AND ref_id IS NOT NULL "
                            "GROUP BY ref_kind, ref_id ORDER BY at DESC LIMIT 6", (current_user()['id'],)).fetchall()
        items = [{'kind': r['ref_kind'], 'id': r['ref_id'], 'title': ref_title(r['ref_kind'], r['ref_id']), 'at': r['at']} for r in rows]
        return jsonify(items=[i for i in items if i['title']])

    @app.get('/api/notes')
    @login_required
    def notes_list():
        rows = g.db.execute("SELECT n.report_id, n.text, n.updated_at, r.title FROM notes n JOIN reports r ON r.id=n.report_id "
                            "WHERE n.user_id=? ORDER BY n.updated_at DESC", (current_user()['id'],)).fetchall()
        return jsonify(items=[dict(r) for r in rows])

    # ---------------- learning studio
    def lesson_out(r, full=False):
        u = current_user()
        done = bool(u and g.db.execute('SELECT 1 FROM lesson_progress WHERE user_id=? AND lesson_id=?', (u['id'], r['id'])).fetchone())
        d = {k: r[k] for k in ('id', 'title', 'level', 'minutes', 'summary', 'topic')} | {'completed': done, 'objectives': json.loads(r['objectives'] or '[]')}
        if full:
            secs = json.loads(r['body'])
            for s in secs:
                s['evidence'] = [dict(p) | {'source_url': f"https://ntrs.nasa.gov/citations/{p['report_id']}"} for p in g.db.execute(
                    f"SELECT p.id, p.report_id, p.locator, p.kind, p.text, r.title AS report_title FROM passages p JOIN reports r ON r.id=p.report_id "
                    f"WHERE p.verified=1 AND p.id IN ({','.join('?' * len(s['evidence']))})", s['evidence'])]
            d['sections'] = secs
            d['challenges'] = [dict(c) for c in g.db.execute('SELECT id,title FROM challenges WHERE lesson_id=?', (r['id'],))]
            rids = list(dict.fromkeys(e['report_id'] for s_ in secs for e in s_['evidence']))
            d['related_reports'] = [{'id': x, 'title': ref_title('report', x)} for x in rids if ref_title('report', x)]
            order = [x[0] for x in g.db.execute('SELECT id FROM lessons ORDER BY position')]
            i = order.index(r['id'])
            nav = lambda j: dict(g.db.execute('SELECT id,title FROM lessons WHERE id=?', (order[j],)).fetchone()) if 0 <= j < len(order) else None
            d['prev'], d['next'] = nav(i - 1), nav(i + 1)
        return d

    @app.get('/api/lessons')
    def lessons():
        return jsonify(items=[lesson_out(r) for r in g.db.execute('SELECT * FROM lessons ORDER BY position')])

    @app.get('/api/lessons/<lid>')
    def lesson(lid):
        r = g.db.execute('SELECT * FROM lessons WHERE id=?', (lid,)).fetchone()
        if not r:
            err(404, 'not_found', 'Lesson not found.')
        return jsonify(lesson_out(r, True))

    @app.post('/api/lessons/<lid>/complete')
    @login_required
    def complete_lesson(lid):
        if not g.db.execute('SELECT 1 FROM lessons WHERE id=?', (lid,)).fetchone():
            err(404, 'not_found', 'Lesson not found.')
        g.db.execute('INSERT OR IGNORE INTO lesson_progress VALUES (?,?,?)', (current_user()['id'], lid, now()))
        g.db.commit()
        return jsonify(ok=True)

    # ---------------- challenges
    def best(cid, uid):
        r = g.db.execute('SELECT MAX(score), COUNT(*), MAX(passed) FROM challenge_attempts WHERE challenge_id=? AND user_id=?', (cid, uid)).fetchone()
        return {'best_score': r[0], 'attempts': r[1], 'passed': bool(r[2])}

    @app.get('/api/challenges')
    def challenges():
        u = current_user()
        out = []
        for r in g.db.execute('SELECT * FROM challenges ORDER BY position'):
            d = {k: r[k] for k in ('id', 'title', 'summary', 'pass_score', 'lesson_id', 'difficulty')} | {'questions': len(json.loads(r['body']))}
            if u:
                d['progress'] = best(r['id'], u['id'])
                d['status'] = 'passed' if d['progress']['passed'] else 'attempted' if d['progress']['attempts'] else 'not_started'
            out.append(d)
        return jsonify(items=out)

    @app.get('/api/challenges/<cid>')
    def challenge(cid):
        r = g.db.execute('SELECT * FROM challenges WHERE id=?', (cid,)).fetchone()
        if not r:
            err(404, 'not_found', 'Challenge not found.')
        qs = [{'id': q['id'], 'prompt': q['prompt'], 'options': q['options']} for q in json.loads(r['body'])]   # answers never sent
        u = current_user()
        d = {k: r[k] for k in ('id', 'title', 'summary', 'pass_score', 'lesson_id', 'difficulty', 'objective', 'background', 'instructions')} | {'questions': qs}
        srcs = list(dict.fromkeys(q['source'] for q in json.loads(r['body'])))
        rids = list(dict.fromkeys(x[0] for x in g.db.execute(f"SELECT report_id FROM passages WHERE id IN ({','.join('?' * len(srcs))})", srcs)))
        d['related_reports'] = [{'id': x, 'title': ref_title('report', x)} for x in rids if ref_title('report', x)]
        if u:
            d['progress'] = best(cid, u['id'])
            d['history'] = [dict(x) for x in g.db.execute('SELECT score,total,passed,at FROM challenge_attempts WHERE challenge_id=? AND user_id=? ORDER BY id DESC LIMIT 10', (cid, u['id']))]
        return jsonify(d)

    @app.post('/api/challenges/<cid>/attempts')
    @login_required
    def attempt_challenge(cid):
        r = g.db.execute('SELECT * FROM challenges WHERE id=?', (cid,)).fetchone()
        if not r:
            err(404, 'not_found', 'Challenge not found.')
        if not auth.LIMITER.allow(f'chal:{current_user()["id"]}', 30, 600):
            err(429, 'rate_limited', 'Too many attempts. Take a short break.')
        qs = json.loads(r['body'])
        answers = body().get('answers')
        if not isinstance(answers, dict) or set(answers) != {q['id'] for q in qs} or \
                not all(isinstance(answers[q['id']], int) and not isinstance(answers[q['id']], bool) and 0 <= answers[q['id']] < len(q['options']) for q in qs):
            err(422, 'validation_error', 'Answer every question.')
        results, score = [], 0
        for q in qs:
            ok = answers[q['id']] == q['answer']
            score += ok
            p = g.db.execute('SELECT p.id,p.report_id,p.locator,p.text,r.title AS report_title FROM passages p JOIN reports r ON r.id=p.report_id WHERE p.id=? AND p.verified=1', (q['source'],)).fetchone()
            results.append({'id': q['id'], 'correct': ok, 'your_answer': answers[q['id']], 'correct_answer': q['answer'],
                            'source': (dict(p) | {'source_url': f"https://ntrs.nasa.gov/citations/{p['report_id']}"}) if p else None})
        passed = score >= r['pass_score']
        g.db.execute('INSERT INTO challenge_attempts (user_id,challenge_id,answers,score,total,passed,at) VALUES (?,?,?,?,?,?,?)',
                     (current_user()['id'], cid, json.dumps(answers), score, len(qs), int(passed), now()))
        g.db.commit()
        return jsonify(score=score, total=len(qs), passed=passed, pass_score=r['pass_score'], results=results), 201

    # ---------------- community
    def post_out(p, me):
        reported = bool(me and g.db.execute('SELECT 1 FROM post_reports WHERE post_id=? AND user_id=?', (p['id'], me['id'])).fetchone())
        hidden = p['status'] != 'visible'
        return {'id': p['id'], 'author_id': p['user_id'], 'room_id': p['room_id'], 'parent_id': p['parent_id'], 'title': None if hidden else p['title'],
                'body': {'hidden': 'This post was hidden by a moderator.', 'deleted': 'This post was deleted by its author.'}.get(p['status'], p['body']),
                'status': p['status'], 'author': name_of(p['user_id']), 'mine': bool(me and me['id'] == p['user_id']),
                'ref': ({'kind': p['ref_kind'], 'id': p['ref_id'], 'title': ref_title(p['ref_kind'], p['ref_id'])} if p['ref_kind'] and not hidden else None),
                'created_at': p['created_at'], 'edited_at': p['edited_at'], 'reported_by_me': reported,
                'replies': g.db.execute("SELECT COUNT(*) FROM posts WHERE parent_id=? AND status='visible'", (p['id'],)).fetchone()[0]}

    @app.get('/api/rooms')
    def rooms():
        rows = g.db.execute("SELECT r.*, (SELECT COUNT(*) FROM posts p WHERE p.room_id=r.id AND p.parent_id IS NULL AND p.status='visible') AS threads "
                            "FROM rooms r ORDER BY position").fetchall()
        return jsonify(items=[dict(r) for r in rows])

    @app.get('/api/rooms/<rid>/posts')
    def room_posts(rid):
        room = g.db.execute('SELECT * FROM rooms WHERE id=?', (rid,)).fetchone()
        if not room:
            err(404, 'not_found', 'Room not found.')
        limit, offset = int_arg('limit', 20, 1, 50), int_arg('offset', 0, 0, 100000)
        total = g.db.execute("SELECT COUNT(*) FROM posts WHERE room_id=? AND parent_id IS NULL AND status<>'deleted'", (rid,)).fetchone()[0]
        rows = g.db.execute("SELECT * FROM posts WHERE room_id=? AND parent_id IS NULL AND status<>'deleted' ORDER BY id DESC LIMIT ? OFFSET ?",
                            (rid, limit, offset)).fetchall()
        return jsonify({**page([post_out(p, current_user()) for p in rows], total, limit, offset), 'room': dict(room)})

    @app.get('/api/posts/<int:pid>')
    def post_detail(pid):
        p = g.db.execute('SELECT * FROM posts WHERE id=? AND parent_id IS NULL', (pid,)).fetchone()
        if not p:
            err(404, 'not_found', 'Post not found.')
        me = current_user()
        replies = g.db.execute("SELECT * FROM posts WHERE parent_id=? AND status<>'deleted' ORDER BY id", (pid,)).fetchall()
        return jsonify(post=post_out(p, me), replies=[post_out(r, me) for r in replies],
                       room=dict(g.db.execute('SELECT * FROM rooms WHERE id=?', (p['room_id'],)).fetchone()))

    def validate_post(d, reply=False):
        text = d.get('body')
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
            err(422, 'validation_error', 'Write 1 to 4000 characters.', {'body': 'length'})
        title = d.get('title')
        if not reply and (not isinstance(title, str) or not 3 <= len(title.strip()) <= 140):
            err(422, 'validation_error', 'Title must be 3 to 140 characters.', {'title': 'length'})
        kind, rid = d.get('ref_kind'), d.get('ref_id')
        if kind is not None:
            if kind not in ('report', 'experiment') or not isinstance(rid, str) or not ref_title(kind, rid):
                err(422, 'validation_error', 'The shared report or experiment was not found.', {'ref': 'invalid'})
        return (title.strip() if title else None), text.strip(), kind, rid if kind else None

    @app.post('/api/rooms/<rid>/posts')
    @login_required
    def create_post(rid):
        if not g.db.execute('SELECT 1 FROM rooms WHERE id=?', (rid,)).fetchone():
            err(404, 'not_found', 'Room not found.')
        if not auth.LIMITER.allow(f'post:{current_user()["id"]}', 10, 600):
            err(429, 'rate_limited', 'You are posting too quickly. Wait a few minutes.')
        title, text, kind, ref = validate_post(body())
        cur = g.db.execute('INSERT INTO posts (room_id,user_id,title,body,ref_kind,ref_id,created_at) VALUES (?,?,?,?,?,?,?)',
                           (rid, current_user()['id'], title, text, kind, ref, now()))
        g.db.commit()
        return jsonify(post_out(g.db.execute('SELECT * FROM posts WHERE id=?', (cur.lastrowid,)).fetchone(), current_user())), 201

    @app.post('/api/posts/<int:pid>/replies')
    @login_required
    def reply(pid):
        p = g.db.execute("SELECT * FROM posts WHERE id=? AND parent_id IS NULL AND status='visible'", (pid,)).fetchone()
        if not p:
            err(404, 'not_found', 'Post not found.')
        if not auth.LIMITER.allow(f'post:{current_user()["id"]}', 10, 600):
            err(429, 'rate_limited', 'You are posting too quickly. Wait a few minutes.')
        _, text, kind, ref = validate_post(body(), reply=True)
        cur = g.db.execute('INSERT INTO posts (room_id,user_id,parent_id,body,ref_kind,ref_id,created_at) VALUES (?,?,?,?,?,?,?)',
                           (p['room_id'], current_user()['id'], pid, text, kind, ref, now()))
        if p['user_id'] != current_user()['id']:
            from ..db import notify
            notify(g.db, p['user_id'], 'replies', f"{current_user()['name']} replied to your discussion", (p['title'] or '')[:120], f"/app/community/post/{pid}")
        g.db.commit()
        bump('post')
        return jsonify(post_out(g.db.execute('SELECT * FROM posts WHERE id=?', (cur.lastrowid,)).fetchone(), current_user())), 201

    @app.delete('/api/posts/<int:pid>')
    @login_required
    def delete_post(pid):
        p = g.db.execute('SELECT * FROM posts WHERE id=?', (pid,)).fetchone()
        if not p or p['user_id'] != current_user()['id']:
            err(404, 'not_found', 'Post not found.')
        g.db.execute("UPDATE posts SET status='deleted', body='[deleted]', title=NULL, ref_kind=NULL, ref_id=NULL WHERE id=?", (pid,))
        g.db.commit()
        return jsonify(ok=True)

    @app.post('/api/posts/<int:pid>/report')
    @login_required
    def report_post(pid):
        p = g.db.execute("SELECT * FROM posts WHERE id=? AND status='visible'", (pid,)).fetchone()
        if not p:
            err(404, 'not_found', 'Post not found.')
        if p['user_id'] == current_user()['id']:
            err(422, 'validation_error', 'You can’t report your own post.')
        reason = body().get('reason')
        if reason not in ('spam', 'harassment', 'misinformation', 'off_topic', 'other'):
            err(422, 'validation_error', 'Choose a reason: spam, harassment, misinformation, off_topic or other.')
        g.db.execute('INSERT OR IGNORE INTO post_reports VALUES (?,?,?,?,0)', (pid, current_user()['id'], reason, now()))
        g.db.commit()
        return jsonify(ok=True)

    # ---------------- admin: moderation
    @app.get('/api/admin/moderation')
    @admin_required
    def moderation_queue():
        rows = g.db.execute("SELECT p.*, COUNT(pr.user_id) AS reports, GROUP_CONCAT(DISTINCT pr.reason) AS reasons FROM posts p "
                            "JOIN post_reports pr ON pr.post_id=p.id AND pr.resolved=0 GROUP BY p.id ORDER BY reports DESC, p.id").fetchall()
        return jsonify(items=[{'id': r['id'], 'room_id': r['room_id'], 'parent_id': r['parent_id'], 'title': r['title'], 'body': r['body'],
                               'status': r['status'], 'author': name_of(r['user_id']), 'reports': r['reports'], 'reasons': r['reasons'],
                               'created_at': r['created_at']} for r in rows])

    @app.post('/api/admin/posts/<int:pid>/moderate')
    @admin_required
    def moderate(pid):
        action = body().get('action')
        if action not in ('hide', 'restore', 'dismiss'):
            err(422, 'validation_error', 'action must be hide, restore or dismiss.')
        if not g.db.execute('SELECT 1 FROM posts WHERE id=?', (pid,)).fetchone():
            err(404, 'not_found', 'Post not found.')
        if action == 'hide':
            g.db.execute("UPDATE posts SET status='hidden' WHERE id=? AND status='visible'", (pid,))
            from ..db import notify
            owner = g.db.execute('SELECT user_id, parent_id FROM posts WHERE id=?', (pid,)).fetchone()
            notify(g.db, owner['user_id'], 'moderation', 'A moderator hid one of your posts', 'It was reported and reviewed against the community rules.', f"/app/community/post/{owner['parent_id'] or pid}")
        elif action == 'restore':
            g.db.execute("UPDATE posts SET status='visible' WHERE id=? AND status='hidden'", (pid,))
        g.db.execute('UPDATE post_reports SET resolved=1 WHERE post_id=?', (pid,))
        g.db.commit()
        audit(g.db, current_user()['email'], f'post.{action}', str(pid))
        return jsonify(ok=True)

    # ---------------- admin: users
    @app.post('/api/admin/users/<int:uid>')
    @admin_required
    def manage_user(uid):
        d = body()
        target = g.db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
        if not target:
            err(404, 'not_found', 'User not found.')
        me = current_user()
        if uid == me['id']:
            err(409, 'self_change', 'You can’t change your own role or status here.')
        active_admins = g.db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0]
        if 'role' in d:
            if d['role'] not in ('user', 'admin'):
                err(422, 'validation_error', 'role must be user or admin.')
            if target['role'] == 'admin' and d['role'] == 'user' and active_admins <= 1:
                err(409, 'last_admin', 'At least one active administrator is required.')
            g.db.execute('UPDATE users SET role=? WHERE id=?', (d['role'], uid))
            audit(g.db, me['email'], f'user.role.{d["role"]}', target['email'])
        if 'disabled' in d:
            if not isinstance(d['disabled'], bool):
                err(422, 'validation_error', 'disabled must be true or false.')
            g.db.execute('UPDATE users SET disabled=? WHERE id=?', (int(d['disabled']), uid))
            if d['disabled']:
                g.db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            audit(g.db, me['email'], 'user.disabled' if d['disabled'] else 'user.enabled', target['email'])
        g.db.commit()
        r = g.db.execute('SELECT id,email,name,role,disabled,created_at FROM users WHERE id=?', (uid,)).fetchone()
        return jsonify(dict(r))

    # ---------------- admin: experiment approval
    def publish_problems(eid):
        """An experiment may be published only if every reported value cites a verified passage of an approved report."""
        rows = g.db.execute("SELECT f.field, p.verified, r.status FROM experiment_fields f LEFT JOIN passages p ON p.id=f.passage_id "
                            "LEFT JOIN reports r ON r.id=p.report_id WHERE f.experiment_id=? AND f.state='reported'", (eid,)).fetchall()
        return [r['field'] for r in rows if not r['verified'] or r['status'] != 'approved']

    @app.get('/api/admin/experiments')
    @admin_required
    def admin_experiments():
        items = exps.list_experiments(g.db, include_drafts=True)
        for e in items:
            e['blocking_fields'] = publish_problems(e['id'])
        return jsonify(items=items)

    @app.post('/api/admin/experiments/<eid>/status')
    @admin_required
    def experiment_status(eid):
        st = body().get('status')
        if st not in ('published', 'draft'):
            err(422, 'validation_error', 'status must be published or draft.')
        if not g.db.execute('SELECT 1 FROM experiments WHERE id=?', (eid,)).fetchone():
            err(404, 'not_found', 'Experiment not found.')
        if st == 'published':
            bad = publish_problems(eid)
            if bad:
                err(409, 'unverified_evidence', 'Every reported value must cite a verified passage from an approved report.', {'fields': bad})
        g.db.execute('UPDATE experiments SET status=? WHERE id=?', (st, eid))
        g.db.commit()
        audit(g.db, current_user()['email'], f'experiment.{st}', eid)
        return jsonify(ok=True)

    # ---------------- admin: analytics (aggregate counters only)
    @app.get('/api/admin/analytics')
    @admin_required
    def analytics():
        days = int_arg('days', 30, 1, 365)
        since = (date.today() - timedelta(days=days - 1)).isoformat()
        rows = g.db.execute('SELECT day,name,count FROM metrics WHERE day>=? ORDER BY day', (since,)).fetchall()
        totals = {}
        for r in rows:
            totals[r['name']] = totals.get(r['name'], 0) + r['count']
        series = {}
        for r in rows:
            series.setdefault(r['name'], {})[r['day']] = r['count']
        return jsonify(days=days, since=since, totals=totals, daily=series,
                       content={'reports': g.db.execute("SELECT COUNT(*) FROM reports WHERE status='approved'").fetchone()[0],
                                'collections': g.db.execute('SELECT COUNT(*) FROM collections').fetchone()[0],
                                'posts': g.db.execute("SELECT COUNT(*) FROM posts WHERE status='visible'").fetchone()[0],
                                'open_reports': g.db.execute('SELECT COUNT(DISTINCT post_id) FROM post_reports WHERE resolved=0').fetchone()[0]},
                       privacy='Daily counts only. No user IDs, questions or search terms are stored for analytics.')

    register_v3(app, post_out, validate_post)


def register_v3(app, post_out, validate_post):
    """Spec-alignment features (v3)."""
    from ..services import ingest as ing
    from ..services.search import INDEX
    import os

    # ---------- saved reports / experiments (separate from collections)
    @app.get('/api/saved')
    @login_required
    def saved_list():
        out = []
        for r in g.db.execute('SELECT kind, ref_id, saved_at FROM saved_items WHERE user_id=? ORDER BY saved_at DESC', (current_user()['id'],)):
            t = ref_title(r['kind'], r['ref_id'])
            if t:
                out.append({'kind': r['kind'], 'id': r['ref_id'], 'title': t, 'saved_at': r['saved_at'],
                            'source_url': f"https://ntrs.nasa.gov/citations/{r['ref_id']}" if r['kind'] == 'report' else None})
        return jsonify(items=out)

    @app.post('/api/saved')
    @login_required
    def save_item():
        d = body()
        if d.get('kind') not in ('report', 'experiment') or not isinstance(d.get('id'), str) or not ref_title(d['kind'], d['id']):
            err(422, 'validation_error', 'Choose an existing report or experiment.')
        g.db.execute('INSERT OR IGNORE INTO saved_items VALUES (?,?,?,?)', (current_user()['id'], d['kind'], d['id'], now()))
        g.db.commit()
        return jsonify(ok=True), 201

    @app.delete('/api/saved/<kind>/<ref>')
    @login_required
    def unsave_item(kind, ref):
        g.db.execute('DELETE FROM saved_items WHERE user_id=? AND kind=? AND ref_id=?', (current_user()['id'], kind, ref))
        g.db.commit()
        return jsonify(ok=True)

    # ---------- experiment notes (report notes already exist)
    @app.put('/api/experiment-notes/<eid>')
    @login_required
    def put_exp_note(eid):
        if not ref_title('experiment', eid):
            err(404, 'not_found', 'Experiment not found.')
        text = body().get('text')
        if not isinstance(text, str) or len(text) > 5000:
            err(422, 'validation_error', 'Notes must be text up to 5000 characters.')
        uid = current_user()['id']
        if text.strip():
            g.db.execute('INSERT INTO experiment_notes VALUES (?,?,?,?) ON CONFLICT(user_id,experiment_id) DO UPDATE SET text=excluded.text, updated_at=excluded.updated_at', (uid, eid, text, now()))
        else:
            g.db.execute('DELETE FROM experiment_notes WHERE user_id=? AND experiment_id=?', (uid, eid))
        g.db.commit()
        return jsonify(ok=True)

    @app.get('/api/experiment-notes/<eid>')
    @login_required
    def get_exp_note(eid):
        r = g.db.execute('SELECT text FROM experiment_notes WHERE user_id=? AND experiment_id=?', (current_user()['id'], eid)).fetchone()
        return jsonify(text=r[0] if r else '')

    @app.get('/api/research-notes')
    @login_required
    def all_notes():
        uid = current_user()['id']
        rows = [{'kind': 'report', 'id': r['report_id'], 'title': r['title'], 'text': r['text'], 'updated_at': r['updated_at']} for r in g.db.execute(
            'SELECT n.report_id, n.text, n.updated_at, r.title FROM notes n JOIN reports r ON r.id=n.report_id WHERE n.user_id=?', (uid,))]
        rows += [{'kind': 'experiment', 'id': r['experiment_id'], 'title': r['name'], 'text': r['text'], 'updated_at': r['updated_at']} for r in g.db.execute(
            'SELECT n.experiment_id, n.text, n.updated_at, e.name FROM experiment_notes n JOIN experiments e ON e.id=n.experiment_id WHERE n.user_id=?', (uid,))]
        return jsonify(items=sorted(rows, key=lambda x: x['updated_at'], reverse=True))

    # ---------- comparison export (Markdown, units and sources preserved)
    @app.post('/api/compare/export')
    def compare_export():
        ids = body().get('experiment_ids')
        if not isinstance(ids, list) or not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids) or not all(isinstance(i, str) for i in ids):
            err(422, 'validation_error', 'experiment_ids must list 2 to 4 different experiment IDs.')
        res, missing = exps.compare(g.db, ids)
        if missing:
            err(404, 'not_found', 'Some experiments were not found.', {'missing': missing})
        cell = lambda c: (f"{c['value']} (NTRS {c['source']['report_id']}, {c['source']['locator']})" if c['state'] == 'reported' else c['state_label']).replace('|', '/')
        lines = ['# CTRL+SPACE experiment comparison', '', f'Exported {now()[:10]}. Values are shown exactly as reported, with sources. Missing values are never zero. '
                 'CTRL+SPACE is not affiliated with or endorsed by NASA.', '']
        for grp, title in (('condition', 'Conditions'), ('measurement', 'Measurements and results')):
            lines += [f'## {title}', '', '| Field | ' + ' | '.join(e['name'] for e in res['experiments']) + ' |', '|---|' + '---|' * len(res['experiments'])]
            lines += ['| ' + r['label'] + ' | ' + ' | '.join(cell(c) for c in r['cells']) + ' |' for r in res['rows'] if r['group'] == grp]
            lines.append('')
        lines += ['## Scientific comparison notes', ''] + [f"- {w['message']}" for w in res['warnings']] + ['', res['methodology']]
        resp = make_response('\n'.join(lines))
        resp.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename="ctrl-space-comparison.md"'
        return resp

    # ---------- sessions and data export
    @app.get('/api/me/sessions')
    @login_required
    def sessions():
        mine = auth.tok_hash(request.cookies.get(COOKIE, ''))
        rows = g.db.execute('SELECT token_hash, created_at, expires_at FROM sessions WHERE user_id=? ORDER BY created_at DESC', (current_user()['id'],)).fetchall()
        return jsonify(items=[{'id': r['token_hash'][:16], 'created_at': r['created_at'], 'expires_at': r['expires_at'], 'current': r['token_hash'] == mine} for r in rows])

    @app.delete('/api/me/sessions/<sid>')
    @login_required
    def revoke_session(sid):
        if not re.fullmatch(r'[0-9a-f]{16}', sid):
            err(400, 'invalid_id', 'Invalid session ID.')
        n = g.db.execute('DELETE FROM sessions WHERE user_id=? AND substr(token_hash,1,16)=?', (current_user()['id'], sid)).rowcount
        g.db.commit()
        if not n:
            err(404, 'not_found', 'Session not found.')
        return jsonify(ok=True)

    @app.get('/api/me/export')
    @login_required
    def export_my_data():
        uid = current_user()['id']
        q = lambda sql: [dict(r) for r in g.db.execute(sql, (uid,))]
        data = {'exported_at': now(), 'user': user_public(g.db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()), 'preferences': prefs_of(uid),
                'collections': q('SELECT c.name, i.kind, i.ref_id, i.added_at FROM collections c LEFT JOIN collection_items i ON i.collection_id=c.id WHERE c.user_id=?'),
                'saved': q('SELECT kind, ref_id, saved_at FROM saved_items WHERE user_id=?'),
                'report_notes': q('SELECT report_id, text, updated_at FROM notes WHERE user_id=?'),
                'experiment_notes': q('SELECT experiment_id, text, updated_at FROM experiment_notes WHERE user_id=?'),
                'activity': q('SELECT at, action, ref_kind, ref_id, label FROM activity WHERE user_id=?'),
                'lessons_completed': q('SELECT lesson_id, completed_at FROM lesson_progress WHERE user_id=?'),
                'challenge_attempts': q('SELECT challenge_id, score, total, passed, at FROM challenge_attempts WHERE user_id=?'),
                'posts': q("SELECT room_id, parent_id, title, body, created_at FROM posts WHERE user_id=? AND status<>'deleted'")}
        resp = make_response(json.dumps(data, indent=1, ensure_ascii=False))
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename="ctrl-space-my-data.json"'
        return resp

    # ---------- community: recent activity and editing own posts
    @app.get('/api/community/recent')
    def community_recent():
        me = current_user()
        rows = g.db.execute("SELECT * FROM posts WHERE parent_id IS NULL AND status='visible' ORDER BY id DESC LIMIT 6").fetchall()
        shared = g.db.execute("SELECT * FROM posts WHERE status='visible' AND ref_kind IS NOT NULL ORDER BY id DESC LIMIT 6").fetchall()
        rooms = {r['id']: r['name'] for r in g.db.execute('SELECT id,name FROM rooms')}
        return jsonify(posts=[post_out(p, me) | {'room_name': rooms.get(p['room_id'])} for p in rows],
                       shared=[{'post_id': p['parent_id'] or p['id'], 'ref': post_out(p, me)['ref'], 'room_name': rooms.get(p['room_id']), 'author': name_of(p['user_id'])} for p in shared])

    @app.patch('/api/posts/<int:pid>')
    @login_required
    def edit_post(pid):
        p = g.db.execute("SELECT * FROM posts WHERE id=? AND status='visible'", (pid,)).fetchone()
        if not p or p['user_id'] != current_user()['id']:
            err(404, 'not_found', 'Post not found.')
        d = body()
        title, text, _, _ = validate_post({'title': d.get('title', p['title']), 'body': d.get('body', p['body'])}, reply=p['parent_id'] is not None)
        g.db.execute('UPDATE posts SET title=?, body=?, edited_at=? WHERE id=?', (title if p['parent_id'] is None else None, text, now(), pid))
        g.db.commit()
        return jsonify(post_out(g.db.execute('SELECT * FROM posts WHERE id=?', (pid,)).fetchone(), current_user()))

    # ---------- admin: system health, failed imports, flag extraction, reject experiment
    @app.get('/api/admin/health')
    @admin_required
    def system_health():
        storage = current_app.config['STORAGE_DIR']
        try:
            os.makedirs(storage, exist_ok=True)
            writable = os.access(storage, os.W_OK)
        except OSError:
            writable = False
        out = {'database': g.db.execute('PRAGMA quick_check').fetchone()[0], 'schema_version': g.db.execute('SELECT version FROM schema_version').fetchone()[0],
               'search_index_passages': len(INDEX.docs), 'ai_provider': current_app.extensions['provider'].name, 'storage_writable': writable,
               'pages_needing_ocr': g.db.execute('SELECT COUNT(*) FROM report_pages WHERE needs_ocr=1').fetchone()[0], 'ntrs': 'not_checked'}
        if request.args.get('check_ntrs') == '1':
            client = current_app.extensions['ntrs'] or ing.NTRSClient(current_app.config['NTRS_BASE'], retries=0, timeout=8)
            try:
                client._get(f"{client.base}/citations/20160000593")
                out['ntrs'] = 'reachable'
            except ing.IngestError as e:
                out['ntrs'] = f'unreachable ({e.code})'
        return jsonify(out)

    @app.get('/api/admin/failed-imports')
    @admin_required
    def failed_imports():
        rows = g.db.execute("SELECT report_id, MAX(at) AS at, step, message FROM ingestion_records WHERE status='error' AND report_id IS NOT NULL "
                            "AND report_id NOT IN (SELECT report_id FROM ingestion_records WHERE status='ok' AND step='extract') GROUP BY report_id ORDER BY at DESC").fetchall()
        return jsonify(items=[dict(r) for r in rows])

    @app.post('/api/admin/passages/<pid>/flag')
    @admin_required
    def flag_passage(pid):
        reason = body().get('reason')
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 300:
            err(422, 'validation_error', 'Describe the problem in 3 to 300 characters.')
        if not g.db.execute('SELECT 1 FROM passages WHERE id=?', (pid,)).fetchone():
            err(404, 'not_found', 'Passage not found.')
        g.db.execute('UPDATE passages SET verified=0, flag_reason=? WHERE id=?', (reason.strip(), pid))
        g.db.commit()
        audit(g.db, current_user()['email'], 'passage.flagged', pid, reason.strip())
        INDEX.build(g.db)
        return jsonify(ok=True)

    @app.post('/api/admin/experiments/<eid>/reject')
    @admin_required
    def reject_experiment(eid):
        reason = body().get('reason')
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 300:
            err(422, 'validation_error', 'Give a reason in 3 to 300 characters.')
        if not g.db.execute('SELECT 1 FROM experiments WHERE id=?', (eid,)).fetchone():
            err(404, 'not_found', 'Experiment not found.')
        g.db.execute("UPDATE experiments SET status='draft' WHERE id=?", (eid,))
        g.db.commit()
        audit(g.db, current_user()['email'], 'experiment.rejected', eid, reason.strip())
        return jsonify(ok=True)
