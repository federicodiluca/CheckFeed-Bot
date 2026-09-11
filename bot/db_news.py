from bot.db import get_conn
from bot.logger import log
from bot.utils import local_day_bounds_utc, parse_rss_datetime

MAX_CONTENT_LEN = 20000


def add_news(title, link, source, published_at, content=""):
    """Inserisce una news. Ritorna True se è nuova, False se già presente o in errore."""
    content = content or ""
    if len(content) > MAX_CONTENT_LEN:
        content = content[:MAX_CONTENT_LEN]

    conn = get_conn()
    cur = conn.cursor()
    try:
        published_at = parse_rss_datetime(published_at)  # formato SQLite UTC standard
        cur.execute("""
        INSERT OR IGNORE INTO news (title, link, source, published_at, content)
        VALUES (?, ?, ?, ?, ?)
        """, (title, link, source, published_at, content))
        conn.commit()
        return cur.rowcount > 0  # True se nuova, False se ignorata
    except Exception as e:
        log(f"❌ Errore inserimento news: {e}")
        return False
    finally:
        conn.close()


def get_recent_news(limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, source, published_at, content
        FROM news
        ORDER BY datetime(published_at) DESC, id DESC
        LIMIT ?
    """, (int(limit),))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_news(now=None):
    """Restituisce tutte le news pubblicate nel giorno locale corrente
    (published_at è in UTC: i confini del giorno vengono convertiti)."""
    start_utc, end_utc = local_day_bounds_utc(now)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, source, published_at, content
        FROM news
        WHERE datetime(published_at) >= datetime(?) AND datetime(published_at) < datetime(?)
        ORDER BY datetime(published_at) DESC, id DESC
    """, (start_utc, end_utc))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cleanup_old_news(days=7):
    """Elimina le news con fetched_at più vecchio di `days` giorni. Ritorna il numero di righe eliminate."""
    conn = get_conn()
    cur = conn.cursor()
    # fetched_at è in UTC (CURRENT_TIMESTAMP): confrontiamo con datetime('now'), anch'esso UTC
    cur.execute(
        "DELETE FROM news WHERE datetime(fetched_at) < datetime('now', ?)",
        (f"-{int(days)} days",),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    log(f"🧽 Pulite {deleted} notizie più vecchie di {days} giorni.")
    return deleted
