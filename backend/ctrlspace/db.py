"""SQLite persistence. Canonical schema reconciling Phase 03 (reports/pages/passages/experiments),
Phase 04 (ingestion log), Phase 08 (field states) and the handoff (users, collections, audit).
Integrity rules are enforced in the schema itself where SQLite allows it."""
import json
import os
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY CHECK (id GLOB '[0-9]*' AND length(id) BETWEEN 8 AND 12),
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),
  doc_type TEXT, published TEXT, report_number TEXT, program TEXT, center TEXT, authors TEXT, rights TEXT,
  source_url TEXT NOT NULL, pdf_url TEXT,
  loc_kind TEXT NOT NULL DEFAULT 'page' CHECK (loc_kind IN ('page','section','slide','abstract')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  provider TEXT NOT NULL DEFAULT 'NTRS', retrieved_at TEXT NOT NULL,
  raw_metadata TEXT,               -- admin-only, never returned by public endpoints
  file_sha256 TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS report_pages (
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL CHECK (page_number >= 1),
  text TEXT NOT NULL DEFAULT '', is_empty INTEGER NOT NULL DEFAULT 0, needs_ocr INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (report_id, page_number)
);
CREATE TABLE IF NOT EXISTS passages (
  id TEXT PRIMARY KEY,
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  locator TEXT NOT NULL CHECK (length(trim(locator)) > 0),
  kind TEXT NOT NULL CHECK (kind IN ('finding','method','condition','hypothesis','context','unreviewed')),
  text TEXT NOT NULL CHECK (length(trim(text)) > 0),
  verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
  verified_by TEXT, verified_at TEXT, origin TEXT NOT NULL DEFAULT 'manual', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_passages_report ON passages(report_id);
CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY CHECK (id GLOB '[a-z0-9]*'),
  name TEXT NOT NULL, program TEXT, lead TEXT, platform TEXT,
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','published'))
);
-- Missing is never zero: no numeric default anywhere; a 'reported' value must cite a passage.
CREATE TABLE IF NOT EXISTS experiment_fields (
  experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
  field TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('reported','not_reported','unknown','unavailable','not_applicable','not_extracted')),
  value_text TEXT, num_value REAL, num_unit TEXT, reason TEXT,
  passage_id TEXT REFERENCES passages(id),
  PRIMARY KEY (experiment_id, field),
  CHECK (state <> 'reported' OR (passage_id IS NOT NULL AND value_text IS NOT NULL)),
  CHECK (state = 'reported' OR num_value IS NULL),
  CHECK (num_value IS NULL OR num_unit IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL,
  pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL, expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS collections (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 80), created_at TEXT NOT NULL, UNIQUE (user_id, name)
);
CREATE TABLE IF NOT EXISTS collection_items (
  collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('report','experiment')), ref_id TEXT NOT NULL, added_at TEXT NOT NULL,
  PRIMARY KEY (collection_id, kind, ref_id)
);
CREATE TABLE IF NOT EXISTS notes (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  text TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, report_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
  target TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS ingestion_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, report_id TEXT, step TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok','warning','error','skipped')), message TEXT
);
CREATE TABLE IF NOT EXISTS report_categories (
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE, category TEXT NOT NULL, PRIMARY KEY (report_id, category)
);
CREATE TABLE IF NOT EXISTS activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  at TEXT NOT NULL, action TEXT NOT NULL, ref_kind TEXT, ref_id TEXT, label TEXT
);
CREATE INDEX IF NOT EXISTS ix_activity_user ON activity(user_id, id);
-- Privacy-conscious analytics: daily counters only, no user IDs, no query text.
CREATE TABLE IF NOT EXISTS metrics (day TEXT NOT NULL, name TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, name));
CREATE TABLE IF NOT EXISTS lessons (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, level TEXT, minutes INTEGER, summary TEXT, body TEXT NOT NULL, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS lesson_progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  completed_at TEXT NOT NULL, PRIMARY KEY (user_id, lesson_id)
);
CREATE TABLE IF NOT EXISTS challenges (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, lesson_id TEXT REFERENCES lessons(id), summary TEXT, pass_score INTEGER NOT NULL,
  body TEXT NOT NULL, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS challenge_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  challenge_id TEXT NOT NULL REFERENCES challenges(id) ON DELETE CASCADE, answers TEXT NOT NULL,
  score INTEGER NOT NULL, total INTEGER NOT NULL, passed INTEGER NOT NULL, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, position INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, parent_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
  title TEXT, body TEXT NOT NULL CHECK (length(trim(body)) BETWEEN 1 AND 4000),
  ref_kind TEXT CHECK (ref_kind IS NULL OR ref_kind IN ('report','experiment')), ref_id TEXT,
  status TEXT NOT NULL DEFAULT 'visible' CHECK (status IN ('visible','hidden','deleted')), created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_posts_room ON posts(room_id, id);
CREATE TABLE IF NOT EXISTS post_reports (
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reason TEXT NOT NULL, at TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (post_id, user_id)
);
CREATE TABLE IF NOT EXISTS saved_items (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, kind TEXT NOT NULL CHECK (kind IN ('report','experiment')),
  ref_id TEXT NOT NULL, saved_at TEXT NOT NULL, PRIMARY KEY (user_id, kind, ref_id)
);
CREATE TABLE IF NOT EXISTS experiment_notes (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  experiment_id TEXT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
  text TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, experiment_id)
);
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL, report_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user','assistant')), content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT, link TEXT, created_at TEXT NOT NULL, read_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications(user_id, id);
CREATE TABLE IF NOT EXISTS password_resets (
  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_by TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT
);
CREATE TABLE IF NOT EXISTS media_cache (query TEXT NOT NULL, page INTEGER NOT NULL, payload TEXT NOT NULL, fetched_at TEXT NOT NULL, PRIMARY KEY (query, page));
CREATE TABLE IF NOT EXISTS psi_cache (term TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS psi_investigation_cache (accession TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS answer_feedback (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  rating TEXT NOT NULL CHECK (rating IN ('up','down')), created_at TEXT NOT NULL, PRIMARY KEY (user_id, message_id)
);
CREATE TABLE IF NOT EXISTS saved_answers (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  saved_at TEXT NOT NULL, PRIMARY KEY (user_id, message_id)
);
CREATE TABLE IF NOT EXISTS client_errors (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL, message TEXT NOT NULL, source TEXT, route TEXT, user_agent TEXT
);
"""
SCHEMA_VERSION = 7


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(path: str) -> sqlite3.Connection:
    if path != ':memory:':
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('PRAGMA journal_mode = WAL') if path != ':memory:' else None
    return con


def _columns(con, table):
    return {r[1] for r in con.execute(f'PRAGMA table_info({table})')}


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    # v1 -> v2 migration: columns added to existing tables (new tables are created above)
    def add(table, col, decl):
        if col not in _columns(con, table):
            con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {decl}')
    add('reports', 'keywords', "TEXT NOT NULL DEFAULT '[]'")
    add('reports', 'abstract', 'TEXT')
    add('passages', 'flag_reason', 'TEXT')
    add('lessons', 'topic', 'TEXT')
    add('lessons', 'objectives', "TEXT NOT NULL DEFAULT '[]'")
    for col in ('difficulty', 'objective', 'background', 'instructions'):
        add('challenges', col, 'TEXT')
    add('posts', 'edited_at', 'TEXT')
    add('collections', 'description', 'TEXT')
    add('users', 'bio', 'TEXT')
    add('users', 'interests', "TEXT NOT NULL DEFAULT '[]'")
    add('users', 'category', 'TEXT')
    add('users', 'is_demo', 'INTEGER NOT NULL DEFAULT 0')
    add('users', 'institution', 'TEXT')
    add('experiments', 'psi_accession', 'TEXT')
    cols = _columns(con, 'users')
    if 'disabled' not in cols:
        con.execute('ALTER TABLE users ADD COLUMN disabled INTEGER NOT NULL DEFAULT 0')
    if 'prefs' not in cols:
        con.execute("ALTER TABLE users ADD COLUMN prefs TEXT NOT NULL DEFAULT '{}'")
    row = con.execute('SELECT version FROM schema_version').fetchone()
    if not row:
        con.execute('INSERT INTO schema_version VALUES (?)', (SCHEMA_VERSION,))
    elif row[0] < SCHEMA_VERSION:
        con.execute('UPDATE schema_version SET version=?', (SCHEMA_VERSION,))
    con.commit()


def seed(con: sqlite3.Connection, corpus_path: str) -> dict:
    """Idempotent: re-running never duplicates rows and never overwrites admin edits."""
    with open(corpus_path, encoding='utf-8') as fh:
        c = json.load(fh)
    t = now()
    n = {'reports': 0, 'passages': 0, 'experiments': 0}
    for r in c['reports']:
        cur = con.execute(
            'INSERT OR IGNORE INTO reports (id,title,doc_type,published,report_number,program,center,authors,rights,'
            'source_url,pdf_url,loc_kind,status,retrieved_at,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (r['id'], r['title'], r['doc_type'], r['published'], r['report_number'], r['program'], r['center'],
             r['authors'], r['rights'], r['source_url'], r['pdf_url'], r['loc_kind'], 'approved', c['retrieved_at'], t))
        n['reports'] += cur.rowcount
        con.execute("UPDATE reports SET keywords=?, abstract=COALESCE(abstract, ?) WHERE id=? AND keywords='[]'",
                    (json.dumps(r.get('keywords', [])), r.get('abstract'), r['id']))
        for cat in r.get('categories', []):
            con.execute('INSERT OR IGNORE INTO report_categories VALUES (?,?)', (r['id'], cat))
    for p in c['passages']:
        cur = con.execute(
            'INSERT OR IGNORE INTO passages (id,report_id,locator,kind,text,verified,verified_by,verified_at,origin,created_at) '
            'VALUES (?,?,?,?,?,1,?,?,?,?)',
            (p['id'], p['report_id'], p['locator'], p['kind'], p['text'], 'seed: checked against NTRS source',
             c['retrieved_at'], 'seed', t))
        n['passages'] += cur.rowcount
    for e in c['experiments']:
        cur = con.execute('INSERT OR IGNORE INTO experiments (id,name,program,lead,platform,report_id,status) VALUES (?,?,?,?,?,?,?)',
                          (e['id'], e['name'], e['program'], e['lead'], e['platform'], e['report_id'], 'published'))
        n['experiments'] += cur.rowcount
        for k, f in e['fields'].items():
            con.execute('INSERT OR IGNORE INTO experiment_fields (experiment_id,field,state,value_text,num_value,num_unit,reason,passage_id) '
                        'VALUES (?,?,?,?,?,?,?,?)',
                        (e['id'], k, f['state'], f['value'], f['num_value'], f['num_unit'], f['reason'], f['passage_id']))
    con.commit()
    learning = os.path.join(os.path.dirname(corpus_path), 'learning.json')
    if os.path.exists(learning):
        seed_learning(con, learning)
    return n


def seed_learning(con, path, strict=True):
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)
    known = {r[0] for r in con.execute('SELECT id FROM passages WHERE verified=1')}
    for i, l in enumerate(d['lessons']):
        for s in l['sections']:
            missing = set(s['evidence']) - known
            if missing and strict:
                raise ValueError(f'Lesson {l["id"]} cites unknown passages {missing}')
        con.execute('INSERT INTO lessons (id,title,level,minutes,summary,body,position,topic,objectives) VALUES (?,?,?,?,?,?,?,?,?) '
                    'ON CONFLICT(id) DO UPDATE SET title=excluded.title, level=excluded.level, minutes=excluded.minutes, summary=excluded.summary, '
                    'body=excluded.body, position=excluded.position, topic=excluded.topic, objectives=excluded.objectives',
                    (l['id'], l['title'], l['level'], l['minutes'], l['summary'], json.dumps(l['sections']), i, l.get('topic'), json.dumps(l.get('objectives', []))))
    for i, ch in enumerate(d['challenges']):
        for q in ch['questions']:
            if (strict and q['source'] not in known) or not 0 <= q['answer'] < len(q['options']):
                raise ValueError(f'Challenge {ch["id"]}/{q["id"]} is invalid')
        con.execute('INSERT INTO challenges (id,title,lesson_id,summary,pass_score,body,position,difficulty,objective,background,instructions) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, lesson_id=excluded.lesson_id, summary=excluded.summary, '
                    'pass_score=excluded.pass_score, body=excluded.body, position=excluded.position, difficulty=excluded.difficulty, '
                    'objective=excluded.objective, background=excluded.background, instructions=excluded.instructions',
                    (ch['id'], ch['title'], ch['lesson'], ch['summary'], ch['pass_score'], json.dumps(ch['questions']), i,
                     ch.get('difficulty'), ch.get('objective'), ch.get('background'), ch.get('instructions')))
    for i, r in enumerate(d['rooms']):
        con.execute('INSERT OR IGNORE INTO rooms VALUES (?,?,?,?)', (r['id'], r['name'], r['description'], i))
    con.commit()


def audit(con, actor: str, action: str, target: str = None, detail: str = None) -> None:
    con.execute('INSERT INTO audit_log (at,actor,action,target,detail) VALUES (?,?,?,?,?)', (now(), actor, action, target, detail))
    con.commit()


def upgrade_seed(con, corpus_path):
    """For existing databases: add seed content introduced by newer versions without re-adding anything an
    admin deleted. Never inserts passages or experiments; only report metadata, categories, missing experiment
    fields (only if their cited passage still exists and is verified) and learning content."""
    with open(corpus_path, encoding='utf-8') as fh:
        c = json.load(fh)
    known = {r[0] for r in con.execute('SELECT id FROM passages WHERE verified=1')}
    for r in c['reports']:
        con.execute("UPDATE reports SET keywords=?, abstract=COALESCE(abstract, ?) WHERE id=? AND keywords='[]'",
                    (json.dumps(r.get('keywords', [])), r.get('abstract'), r['id']))
        for cat in r.get('categories', []):
            if con.execute('SELECT 1 FROM reports WHERE id=?', (r['id'],)).fetchone():
                con.execute('INSERT OR IGNORE INTO report_categories VALUES (?,?)', (r['id'], cat))
    exps = {r[0] for r in con.execute('SELECT id FROM experiments')}
    for e in c['experiments']:
        if e['id'] not in exps:
            continue
        for k, f in e['fields'].items():
            if f['passage_id'] and f['passage_id'] not in known:
                continue
            con.execute('INSERT OR IGNORE INTO experiment_fields (experiment_id,field,state,value_text,num_value,num_unit,reason,passage_id) '
                        'VALUES (?,?,?,?,?,?,?,?)', (e['id'], k, f['state'], f['value'], f['num_value'], f['num_unit'], f['reason'], f['passage_id']))
    con.commit()
    learning = os.path.join(os.path.dirname(corpus_path), 'learning.json')
    if os.path.exists(learning):
        seed_learning(con, learning, strict=False)


def notify(con, user_id, kind, title, body=None, link=None):
    """In-app notification for a real event. Respects the user's per-kind preference (default on)."""
    r = con.execute('SELECT prefs FROM users WHERE id=?', (user_id,)).fetchone()
    try:
        prefs = json.loads(r[0]) if r else {}
    except ValueError:
        prefs = {}
    if prefs.get('notify', {}).get(kind, True) is False:
        return
    con.execute('INSERT INTO notifications (user_id,kind,title,body,link,created_at) VALUES (?,?,?,?,?,?)', (user_id, kind, title, body, link, now()))
