from datetime import datetime
from bot.db import get_conn


def _split_keywords(raw):
    return [kw.strip() for kw in (raw or "").split(",") if kw.strip()]


def add_user(telegram_id, username=None):
    """Registra un nuovo utente. Ritorna True se creato, False se già esistente
    (in tal caso aggiorna lo username)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE telegram_id=?", (telegram_id,))
    if cur.fetchone():
        if username:
            cur.execute("UPDATE users SET username=? WHERE telegram_id=?", (username, telegram_id))
            conn.commit()
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


def get_user(telegram_id):
    """Ritorna {telegram_id, username, keywords, active} oppure None se non registrato."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, username, keywords, active FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "telegram_id": row["telegram_id"],
        "username": row["username"],
        "keywords": _split_keywords(row["keywords"]),
        "active": bool(row["active"]),
    }


def get_users(active_only=True):
    conn = get_conn()
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT telegram_id, keywords FROM users WHERE active=1")
    else:
        cur.execute("SELECT telegram_id, keywords FROM users")
    rows = cur.fetchall()
    conn.close()
    return [{"telegram_id": row["telegram_id"], "keywords": _split_keywords(row["keywords"])} for row in rows]


def update_keywords(telegram_id, keywords):
    clean = [kw.strip() for kw in keywords if kw and kw.strip()]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET keywords=? WHERE telegram_id=?", (",".join(clean), telegram_id))
    conn.commit()
    conn.close()
