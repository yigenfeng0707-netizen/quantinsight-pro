"""
QuantInsight Pro - Bootstrap Admin Account
=============================================

One-time script to create the admin user.

Usage:
    python -m admin.bootstrap_admin                      # 密码来自 ADMIN_PASSWORD 环境变量
    python -m admin.bootstrap_admin --password <新密码>   # 显式指定（推荐）
    ADMIN_PASSWORD=xxx python -m admin.bootstrap_admin    # 环境变量方式

若均未提供，将生成随机密码并打印一次（不会写入任何文件）。

License: MIT
"""

import sys
import os
import secrets
import string
import argparse

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.database import UserDB


def _generate_password(length: int = 16) -> str:
    """生成随机强密码（大小写字母 + 数字，无易混淆符号）"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def bootstrap_admin(username: str = 'admin', password: str = None):
    """Create admin account if it doesn't exist"""
    if not password:
        password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        password = _generate_password()
        print('未指定密码，已生成随机密码（仅显示一次，请立即保存/修改）：')

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

    # Check if username exists with different password -> reset it
    with db._conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if row:
            print(f'User "{username}" exists, resetting password & promoting to admin...')
            from auth.database import _hash_password
            conn.execute(
                "UPDATE users SET is_admin=1, password_hash=? WHERE username=?",
                (_hash_password(password), username)
            )
            print('Done.')
            print(f'   New password: {password}')
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
    parser = argparse.ArgumentParser(description='Bootstrap admin account')
    parser.add_argument('--username', default='admin', help='admin 用户名')
    parser.add_argument('--password', default=None, help='密码（缺省读 ADMIN_PASSWORD 环境变量，否则随机生成）')
    args = parser.parse_args()
    bootstrap_admin(username=args.username, password=args.password)
