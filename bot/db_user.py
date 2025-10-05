from datetime import datetime
from bot.db import get_conn

def add_user(telegram_id, username=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE telegram_id=?", (telegram_id,))
    if cur.fetchone():
        conn.close()
        return False

    cur.execute("""
        INSERT INTO users (telegram_id, username, keywords, active, created_at)
        VALUES (?, ?, ?, 1, ?)
    """, (telegram_id, username, "", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True


def activate_user(telegram_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET active=1 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def deactivate_user(telegram_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET active=0 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def get_users(active_only=True):
    conn = get_conn()
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT telegram_id, keywords FROM users WHERE active=1")
    else:
        cur.execute("SELECT telegram_id, keywords FROM users")
    rows = cur.fetchall()
    conn.close()
    return [{"telegram_id": row["telegram_id"], "keywords": (row["keywords"] or "").split(",")} for row in rows]


def update_keywords(telegram_id, keywords):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET keywords=? WHERE telegram_id=?", (",".join(keywords), telegram_id))
    conn.commit()
    conn.close()
