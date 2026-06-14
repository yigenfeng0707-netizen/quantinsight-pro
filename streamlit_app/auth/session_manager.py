"""
QuantInsight Pro - Session Manager
====================================

Handles login/logout, session timeout, trial enforcement.
Uses Streamlit session_state for session tracking.

License: MIT
"""

from datetime import datetime, timedelta
from typing import Optional


SESSION_TIMEOUT_HOURS = 8


class SessionManager:
    """Session manager for Streamlit auth"""

    def __init__(self, db):
        """
        Args:
            db: UserDB instance
        """
        self.db = db

    def login(self, session_state, username: str, password: str, ip: str = '', ua: str = '') -> dict:
        user = self.db.verify_user(username, password)
        if not user:
            return {'ok': False, 'error': '用户名或密码错误'}

        session_state.auth_user_id = user['id']
        session_state.auth_username = user['username']
        session_state.auth_is_admin = bool(user['is_admin'])
        session_state.auth_login_time = datetime.now().isoformat()
        session_state.auth_trial_used = bool(user['trial_used'])

        self.db.log_login(user['id'], ip, ua)
        return {'ok': True, 'user': user}

    def logout(self, session_state):
        for key in ['auth_user_id', 'auth_username', 'auth_is_admin',
                     'auth_login_time', 'auth_trial_used']:
            if key in session_state:
                del session_state[key]

    def is_authenticated(self, session_state) -> bool:
        if 'auth_user_id' not in session_state:
            return False
        # Check session timeout
        login_time = session_state.get('auth_login_time', '')
        if login_time:
            try:
                elapsed = datetime.now() - datetime.fromisoformat(login_time)
                if elapsed > timedelta(hours=SESSION_TIMEOUT_HOURS):
                    self.logout(session_state)
                    return False
            except Exception:
                pass
        return True

    def get_current_user(self, session_state) -> Optional[dict]:
        if not self.is_authenticated(session_state):
            return None
        return self.db.get_user(session_state.auth_user_id)

    def check_trial(self, session_state) -> bool:
        """Returns True if user has access (trial not exhausted or activated)"""
        if not self.is_authenticated(session_state):
            return False
        user = self.db.get_user(session_state.auth_user_id)
        if not user:
            return False
        if user['is_admin']:
            return True  # Admins always have access
        # trial_used=0 means either fresh (never used) or activated
        # We check if trial_started_at exists to differentiate
        if not user['trial_used']:
            return True
        return False  # Trial exhausted

    def consume_trial(self, session_state):
        """Mark trial as used for the current user"""
        if not self.is_authenticated(session_state):
            return
        self.db.update_trial(session_state.auth_user_id, used=True)
        session_state.auth_trial_used = True

    def log_page_visit(self, session_state, page: str):
        if self.is_authenticated(session_state):
            self.db.log_usage(session_state.auth_user_id, 'page_visit', page)
