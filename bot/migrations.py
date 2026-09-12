"""Migrazioni dello schema SQLite, versionate con PRAGMA user_version.

Ogni migrazione riceve la connessione e deve essere idempotente rispetto allo
stato che trova (i DB creati da zero nascono già nella forma finale, quindi le
migrazioni controllano le colonne prima di agire).
"""


def column_exists(conn, table, column):
    return any(row["name"] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def table_exists(conn, table):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _v1_multi_channel(conn):
    """Da 'utente = telegram_id' a 'utente = users.id' con canali/frequenza.
    - users: telegram_id nullable, nuove colonne email/password/notifiche
    - user_sources: telegram_id -> user_id
    - sources.added_by: telegram_id -> user_id
    - news.source_id (DB molto vecchi)
    """
    if not column_exists(conn, "news", "source_id"):
        conn.execute("ALTER TABLE news ADD COLUMN source_id INTEGER")

    legacy_users = not column_exists(conn, "users", "email")
    if legacy_users:
        conn.executescript("""
            CREATE TABLE users_v1 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                email TEXT UNIQUE,
                password_hash TEXT,
                email_verified INTEGER NOT NULL DEFAULT 0,
                keywords TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                notify_telegram INTEGER NOT NULL DEFAULT 1,
                notify_email INTEGER NOT NULL DEFAULT 0,
                alert_mode TEXT NOT NULL DEFAULT 'instant',
                digest_time TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users_v1 (id, telegram_id, username, keywords, active, created_at)
                SELECT id, telegram_id, username, keywords, COALESCE(active, 1), created_at FROM users;
            DROP TABLE users;
            ALTER TABLE users_v1 RENAME TO users;
        """)

    if table_exists(conn, "user_sources") and column_exists(conn, "user_sources", "telegram_id"):
        conn.executescript("""
            CREATE TABLE user_sources_v1 (
                user_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                follow INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, source_id)
            );
            INSERT OR IGNORE INTO user_sources_v1 (user_id, source_id, follow)
                SELECT u.id, us.source_id, us.follow
                FROM user_sources us JOIN users u ON u.telegram_id = us.telegram_id;
            DROP TABLE user_sources;
            ALTER TABLE user_sources_v1 RENAME TO user_sources;
        """)

    if legacy_users:
        # added_by conteneva il telegram_id: lo rimappiamo su users.id
        conn.execute("""
            UPDATE sources SET added_by = (SELECT id FROM users u WHERE u.telegram_id = sources.added_by)
            WHERE added_by IS NOT NULL
        """)


MIGRATIONS = [
    (1, _v1_multi_channel),
]


def get_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def run_migrations(conn):
    """Applica in ordine le migrazioni mancanti. Ritorna la lista delle versioni applicate."""
    current = get_version(conn)
    applied = []
    for version, migrate in MIGRATIONS:
        if current >= version:
            continue
        migrate(conn)
        conn.execute(f"PRAGMA user_version = {int(version)}")
        conn.commit()
        applied.append(version)
        current = version
    return applied
