"""
QuantInsight Pro - Bootstrap Admin Account
=============================================

One-time script to create the admin user.

Usage:
    python -m admin.bootstrap_admin

License: MIT
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.database import UserDB


def bootstrap_admin(username: str = 'admin', password: str = '18969081266*'):
    """Create admin account if it doesn't exist"""
    db = UserDB()

    # Check if admin already exists
    user = db.verify_user(username, password)
    if user:
        print(f'Admin user "{username}" already exists (id={user["id"]})')
        # Ensure admin flag
        with db._conn() as conn:
            conn.execute("UPDATE users SET is_admin=1 WHERE username=?", (username,))
        print('Admin flag confirmed.')
        return

    # Check if username exists with different password
    with db._conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if row:
            print(f'User "{username}" exists, promoting to admin...')
            from auth.database import _hash_password
            conn.execute(
                "UPDATE users SET is_admin=1, password_hash=? WHERE username=?",
                (_hash_password(password), username)
            )
            print('Done.')
            return

    # Create new admin user
    from auth.database import _hash_password
    from datetime import datetime
    now = datetime.now().isoformat()
    pw_hash = _hash_password(password)

    with db._conn() as conn:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at, is_admin, trial_used) "
            "VALUES (?,?,?,?,1,0)",
            (username, 'admin@insightquant.com', pw_hash, now)
        )
    print(f'✅ Admin user created: {username}')
    print(f'   Password: {password}')
    print('   ⚠️  Please change the password after first login!')


if __name__ == '__main__':
    bootstrap_admin()
