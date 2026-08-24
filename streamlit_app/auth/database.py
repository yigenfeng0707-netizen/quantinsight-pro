"""
QuantInsight Pro - User Database (SQLite)
==========================================

Tables:
- users: user accounts with trial tracking
- login_history: login audit log
- usage_log: page/feature usage tracking
- activation_codes: admin-generated activation codes
- registration_attempts: IP-based rate limiting

License: MIT
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

try:
    import bcrypt
except ImportError:
    bcrypt = None

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'users.db')


def _hash_password(password: str) -> str:
    if bcrypt:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # Fallback: SHA-256 + salt (less secure but works without bcrypt)
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()
    return f'sha256:{salt}:{h}'


def _verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith('sha256:'):
        _, salt, h = stored_hash.split(':')
        return hashlib.sha256(f'{salt}{password}'.encode()).hexdigest() == h
    if bcrypt:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    return False


class UserDB:
    """SQLite user database"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    trial_used INTEGER DEFAULT 0,
                    trial_started_at TEXT,
                    is_active INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    login_time TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    page TEXT,
                    timestamp TEXT NOT NULL,
                    details_json TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS activation_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    created_by INTEGER,
                    is_used INTEGER DEFAULT 0,
                    used_by INTEGER,
                    used_at TEXT,
                    created_at TEXT NOT NULL,
                    note TEXT,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS registration_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    attempt_time TEXT NOT NULL
                );
            """)

    def create_user(self, username: str, password: str, email: str = '') -> dict:
        now = datetime.now().isoformat()
        pw_hash = _hash_password(password)
        with self._conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash, created_at, trial_started_at) VALUES (?,?,?,?,?)",
                    (username, email, pw_hash, now, now)
                )
                user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                return {'ok': True, 'user_id': user_id}
            except sqlite3.IntegrityError:
                return {'ok': False, 'error': '用户名已存在'}

    def verify_user(self, username: str, password: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
            ).fetchone()
            if row and _verify_password(password, row['password_hash']):
                return dict(row)
        return None

    def get_user(self, user_id: int) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            return dict(row) if row else None

    def update_trial(self, user_id: int, used: bool = True):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET trial_used=?, trial_started_at=COALESCE(trial_started_at, ?) WHERE id=?",
                (1 if used else 0, now, user_id)
            )

    def log_login(self, user_id: int, ip: str = '', ua: str = ''):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO login_history (user_id, login_time, ip_address, user_agent) VALUES (?,?,?,?)",
                (user_id, datetime.now().isoformat(), ip, ua)
            )

    def log_usage(self, user_id: int, action: str, page: str = '', details: str = ''):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO usage_log (user_id, action, page, timestamp, details_json) VALUES (?,?,?,?,?)",
                (user_id, action, page, datetime.now().isoformat(), details)
            )

    def get_all_users(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, username, email, created_at, is_admin, trial_used, is_active FROM users ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_user_stats(self, user_id: int) -> dict:
        with self._conn() as conn:
            logins = conn.execute(
                "SELECT COUNT(*) as cnt FROM login_history WHERE user_id=?", (user_id,)
            ).fetchone()['cnt']
            actions = conn.execute(
                "SELECT COUNT(*) as cnt FROM usage_log WHERE user_id=?", (user_id,)
            ).fetchone()['cnt']
            last_login = conn.execute(
                "SELECT MAX(login_time) as t FROM login_history WHERE user_id=?", (user_id,)
            ).fetchone()['t']
            return {'login_count': logins, 'action_count': actions, 'last_login': last_login}

    def check_registration_rate(self, ip: str, max_per_day: int = 20) -> bool:
        """Returns True if registration is allowed (per IP / session id)."""
        # Never treat the old shared placeholder as a real bucket
        if not ip or ip in ('0.0.0.0', '127.0.0.1', 'unknown'):
            return True
        cutoff = (datetime.now() - timedelta(days=1)).isoformat()
        with self._conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM registration_attempts WHERE ip_address=? AND attempt_time>?",
                (ip, cutoff)
            ).fetchone()['cnt']
            if count >= max_per_day:
                return False
            conn.execute(
                "INSERT INTO registration_attempts (ip_address, attempt_time) VALUES (?,?)",
                (ip, datetime.now().isoformat())
            )
            return True

    # ---- Activation Codes ----

    def create_activation_code(self, created_by: int, note: str = '') -> str:
        code = secrets.token_hex(8).upper()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO activation_codes (code, created_by, created_at, note) VALUES (?,?,?,?)",
                (code, created_by, datetime.now().isoformat(), note)
            )
        return code

    def redeem_activation_code(self, code: str, user_id: int) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM activation_codes WHERE code=? AND is_used=0", (code.upper(),)
            ).fetchone()
            if not row:
                return {'ok': False, 'error': '激活码无效或已使用'}
            conn.execute(
                "UPDATE activation_codes SET is_used=1, used_by=?, used_at=? WHERE id=?",
                (user_id, datetime.now().isoformat(), row['id'])
            )
            conn.execute(
                "UPDATE users SET trial_used=0 WHERE id=?", (user_id,)
            )
            return {'ok': True}

    def get_all_activation_codes(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT ac.*, u.username as used_by_name FROM activation_codes ac "
                "LEFT JOIN users u ON ac.used_by = u.id ORDER BY ac.id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def revoke_activation_code(self, code_id: int):
        with self._conn() as conn:
            conn.execute("UPDATE activation_codes SET is_used=1 WHERE id=? AND is_used=0", (code_id,))

    # ---- Analytics ----

    def get_dau_wau_mau(self) -> dict:
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        week_ago = (now - timedelta(days=7)).isoformat()
        month_ago = (now - timedelta(days=30)).isoformat()
        with self._conn() as conn:
            dau = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as cnt FROM login_history WHERE login_time>=?", (today,)
            ).fetchone()['cnt']
            wau = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as cnt FROM login_history WHERE login_time>=?", (week_ago,)
            ).fetchone()['cnt']
            mau = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as cnt FROM login_history WHERE login_time>=?", (month_ago,)
            ).fetchone()['cnt']
            total = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active=1").fetchone()['cnt']
            return {'dau': dau, 'wau': wau, 'mau': mau, 'total_users': total}

    def get_login_history_all(self, limit: int = 100) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT lh.*, u.username FROM login_history lh "
                "JOIN users u ON lh.user_id = u.id ORDER BY lh.login_time DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_page_popularity(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT page, COUNT(*) as visits FROM usage_log "
                "GROUP BY page ORDER BY visits DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_registration_trend(self, days: int = 30) -> list:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM users "
                "WHERE created_at>=? GROUP BY DATE(created_at) ORDER BY day",
                (cutoff,)
            ).fetchall()
            return [dict(r) for r in rows]
