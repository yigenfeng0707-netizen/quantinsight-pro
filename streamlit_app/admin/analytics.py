"""
QuantInsight Pro - Analytics Queries
=======================================

Reusable analytics query functions for admin dashboard.
All functions accept a UserDB instance and return structured data.

License: MIT
"""

from datetime import datetime, timedelta
from typing import Optional


def get_user_retention_cohort(db, weeks: int = 8) -> list:
    """
    Cohort retention analysis: for each registration week,
    what % of users returned in subsequent weeks.
    """
    now = datetime.now()
    cutoff = (now - timedelta(weeks=weeks)).isoformat()

    with db._conn() as conn:
        rows = conn.execute("""
            SELECT
                u.id as user_id,
                DATE(u.created_at) as reg_date,
                DATE(lh.login_time) as login_date
            FROM users u
            LEFT JOIN login_history lh ON u.id = lh.user_id
            WHERE u.created_at >= ?
        """, (cutoff,)).fetchall()

    if not rows:
        return []

    data = [dict(r) for r in rows]
    # Group by registration week
    cohorts = {}
    for row in data:
        reg = datetime.fromisoformat(row['reg_date'])
        week_num = (now - reg).days // 7
        cohort_key = f'Week {weeks - week_num}'
        if cohort_key not in cohorts:
            cohorts[cohort_key] = {'registered': set(), 'active_weeks': {}}
        cohorts[cohort_key]['registered'].add(row['user_id'])
        if row['login_date']:
            login = datetime.fromisoformat(row['login_date'])
            active_week = (login - reg).days // 7
            if active_week not in cohorts[cohort_key]['active_weeks']:
                cohorts[cohort_key]['active_weeks'][active_week] = set()
            cohorts[cohort_key]['active_weeks'][active_week].add(row['user_id'])

    result = []
    for cohort, info in sorted(cohorts.items()):
        total = len(info['registered'])
        row_data = {'cohort': cohort, 'registered': total}
        for w in range(weeks + 1):
            active = len(info['active_weeks'].get(w, set()))
            row_data[f'week_{w}'] = f'{active/total*100:.0f}%' if total else '0%'
        result.append(row_data)
    return result


def get_feature_usage_breakdown(db) -> list:
    """Get detailed feature usage breakdown per page"""
    with db._conn() as conn:
        rows = conn.execute("""
            SELECT page, action, COUNT(*) as cnt
            FROM usage_log
            GROUP BY page, action
            ORDER BY cnt DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_peak_usage_hours(db, days: int = 7) -> list:
    """Get peak usage hours over the last N days"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with db._conn() as conn:
        rows = conn.execute("""
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as actions
            FROM usage_log
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
        """, (cutoff,)).fetchall()
    return [dict(r) for r in rows]


def get_user_engagement_score(db) -> list:
    """
    Calculate engagement score per user based on:
    - Login frequency (weight: 0.3)
    - Page visits (weight: 0.4)
    - Recency (weight: 0.3)
    """
    with db._conn() as conn:
        rows = conn.execute("""
            SELECT
                u.id,
                u.username,
                COUNT(DISTINCT DATE(lh.login_time)) as login_days,
                (SELECT COUNT(*) FROM usage_log ul WHERE ul.user_id = u.id) as total_actions,
                MAX(lh.login_time) as last_seen
            FROM users u
            LEFT JOIN login_history lh ON u.id = lh.user_id
            GROUP BY u.id
            ORDER BY total_actions DESC
        """).fetchall()

    results = []
    now = datetime.now()
    for r in rows:
        r = dict(r)
        recency_days = (now - datetime.fromisoformat(r['last_seen'])).days if r['last_seen'] else 999
        recency_score = max(0, 100 - recency_days * 3)
        login_score = min(100, r['login_days'] * 15)
        action_score = min(100, r['total_actions'] * 5)
        engagement = login_score * 0.3 + action_score * 0.4 + recency_score * 0.3
        results.append({
            'user_id': r['id'],
            'username': r['username'],
            'login_days': r['login_days'],
            'total_actions': r['total_actions'],
            'last_seen': r['last_seen'][:10] if r['last_seen'] else 'Never',
            'engagement_score': round(engagement, 1),
        })
    return sorted(results, key=lambda x: x['engagement_score'], reverse=True)
