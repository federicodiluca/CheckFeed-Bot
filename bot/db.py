import os
import sqlite3

# Percorso del database: sovrascrivibile con CHECKFEED_DB_PATH.
DB_PATH = os.environ.get("CHECKFEED_DB_PATH", "data/checkfeed.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == column for row in cur.fetchall())


def init_db():
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        keywords TEXT,
        active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        link TEXT UNIQUE NOT NULL,
        source TEXT,
        published_at DATETIME,
        content TEXT,
        fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Fonti: da config.json (origin='config') o aggiunte dagli utenti (origin='user').
    # type: 'rss' (feed) oppure 'html' (pagina scrapata).
    # default_follow: 1 = seguita da tutti salvo esclusione, 0 = opt-in.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL DEFAULT 'rss',
        origin TEXT NOT NULL DEFAULT 'config',
        added_by INTEGER,
        enabled INTEGER NOT NULL DEFAULT 1,
        default_follow INTEGER NOT NULL DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Override per utente: follow=1 segue, follow=0 esclude. Assente = default della fonte.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_sources (
        telegram_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL,
        follow INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (telegram_id, source_id)
    )
    """)

    # Migrazione: news.source_id (i DB creati prima non ce l'hanno)
    if not _column_exists(cur, "news", "source_id"):
        cur.execute("ALTER TABLE news ADD COLUMN source_id INTEGER")

    conn.commit()
    conn.close()
