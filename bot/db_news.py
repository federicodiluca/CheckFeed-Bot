from datetime import datetime, timedelta
from bot.db import get_conn
from bot.logger import log
import sqlite3

from bot.utils import parse_rss_datetime


def add_news(title, link, source, published_at, content=""):
    conn = get_conn()
    cur = conn.cursor()

    # limito la lunghezza del content a 20k caratteri
    max_len = 20000
    content = content[:max_len] if content and len(content) > max_len else content
    
    try:
        published_at = parse_rss_datetime(published_at) # converto in formato SQLite UTC standard
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
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, source, published_at, content
        FROM news
        ORDER BY datetime(published_at) DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_news():
    """Restituisce tutte le news con published_at di oggi."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, source, published_at, content
        FROM news
        WHERE date(published_at) >= datetime('now', 'start of day')
        ORDER BY datetime(published_at) DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cleanup_old_news(days=7):
    conn = get_conn()
    cur = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    cur.execute("DELETE FROM news WHERE fetched_at < ?", (cutoff,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    log(f"🧽 Pulite {deleted} notizie più vecchie di {days} giorni.")
