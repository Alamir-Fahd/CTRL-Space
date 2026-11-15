"""Accounts and sessions. PBKDF2-SHA256 (stdlib) password hashing, random session tokens stored only as
SHA-256 hashes, HttpOnly + SameSite=Strict cookie. No default credentials: admins are created by CLI."""
import hashlib
import hmac
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

ITER = 310_000
EMAIL = re.compile(r'^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,24}$')


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, ITER)
    return f'pbkdf2_sha256${ITER}${salt.hex()}${dk.hex()}'


def check_password(pw: str, stored: str) -> bool:
    try:
        algo, it, salt, dk = stored.split('$')
        calc = hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), int(it))
        return algo == 'pbkdf2_sha256' and hmac.compare_digest(calc.hex(), dk)
    except (ValueError, TypeError):
        return False


DUMMY = hash_password('timing-equaliser-not-a-real-password')
CATEGORIES = ('astronaut', 'student', 'researcher', 'educator', 'other')
DEMO_EMAIL = 'demo.student@ctrlspace.local'
DEMO_PASSWORD = 'Demo@12345'


def validate_signup(email, name, pw, category=None):
    errors = {}
    if not isinstance(email, str) or not EMAIL.match(email.strip()):
        errors['email'] = 'Enter a valid email address.'
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
        errors['name'] = 'Name must be 1 to 60 characters.'
    if not isinstance(pw, str) or len(pw) < 10 or len(pw) > 200:
        errors['password'] = 'Password must be 10 to 200 characters.'
    elif pw.lower() == pw or not re.search(r'\d', pw):
        errors['password'] = 'Use at least one capital letter and one number.'
    if category not in (None, '') and category not in CATEGORIES:
        errors['category'] = 'Choose a valid category.'
    return errors


def ensure_demo_account(con):
    """Idempotent: creates the public NASA Space Apps demo account once. Never overwrites an existing
    account (including if a real user already registered that email), never runs in production unless
    explicitly opted in (see create_app)."""
    if con.execute('SELECT 1 FROM users WHERE email=?', (DEMO_EMAIL,)).fetchone():
        return
    con.execute('INSERT INTO users (email,name,pw_hash,role,created_at,category,is_demo) VALUES (?,?,?,?,?,?,1)',
                (DEMO_EMAIL, 'Demo Student', hash_password(DEMO_PASSWORD), 'user',
                 datetime.now(timezone.utc).replace(microsecond=0).isoformat(), 'student'))
    con.commit()


def tok_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(con, user_id: int, hours: int) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    con.execute('INSERT INTO sessions VALUES (?,?,?,?)', (tok_hash(token), user_id, now.isoformat(), (now + timedelta(hours=hours)).isoformat()))
    con.commit()
    return token


def user_for_token(con, token):
    if not token or len(token) > 100:
        return None
    r = con.execute('SELECT u.id,u.email,u.name,u.role,u.category,u.is_demo,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND u.disabled=0',
                    (tok_hash(token),)).fetchone()
    if not r or r['expires_at'] < datetime.now(timezone.utc).isoformat():
        return None
    return {'id': r['id'], 'email': r['email'], 'name': r['name'], 'role': r['role'], 'category': r['category'], 'is_demo': bool(r['is_demo'])}


class RateLimiter:
    """In-memory sliding window. Single-instance limitation documented in SECURITY.md."""
    def __init__(self):
        self.hits, self.lock = {}, threading.Lock()

    def allow(self, key: str, limit: int, window: int) -> bool:
        t = time.monotonic()
        with self.lock:
            q = [x for x in self.hits.get(key, []) if t - x < window]
            if len(q) >= limit:
                self.hits[key] = q
                return False
            q.append(t)
            self.hits[key] = q
            return True

    def reset(self):
        with self.lock:
            self.hits.clear()


LIMITER = RateLimiter()
