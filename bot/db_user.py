"""Utenti. La chiave interna è users.id; telegram_id ed email sono identità
opzionali (un utente può avere entrambe). Le funzioni con parametro telegram_id
sono l'API usata dai comandi Telegram; quelle con user_id servono al layer web
e al core."""
from datetime import datetime
from bot.db import get_conn

ALERT_MODES = ("instant", "digest")   # instant = alert a ogni fetch; digest = solo nel report
USER_COLUMNS = ("id, telegram_id, username, email, email_verified, keywords, active, "
                "notify_telegram, notify_email, alert_mode, digest_time, last_digest_date, consent_version, consent_at, created_at")


def _split_keywords(raw):
    return [kw.strip() for kw in (raw or "").split(",") if kw.strip()]


def _row_to_user(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "telegram_id": row["telegram_id"],
        "username": row["username"],
        "email": row["email"],
        "email_verified": bool(row["email_verified"]),
        "keywords": _split_keywords(row["keywords"]),
        "active": bool(row["active"]),
        "notify_telegram": bool(row["notify_telegram"]),
        "notify_email": bool(row["notify_email"]),
        "alert_mode": row["alert_mode"] or "instant",
        "digest_time": row["digest_time"],
        "last_digest_date": row["last_digest_date"],
        "consent_version": row["consent_version"],
        "consent_at": row["consent_at"],
        "created_at": row["created_at"],
    }


def _fetch_user(where, params):
    conn = get_conn()
    row = conn.execute(f"SELECT {USER_COLUMNS} FROM users WHERE {where}", params).fetchone()
    conn.close()
    return _row_to_user(row)


def _exec(sql, params):
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    conn.close()
    return cur.rowcount


# --- lettura --------------------------------------------------------------

def get_user(telegram_id):
    """Utente per telegram_id, oppure None se non registrato."""
    return _fetch_user("telegram_id=?", (telegram_id,))


def get_user_by_id(user_id):
    return _fetch_user("id=?", (user_id,))


def get_user_by_email(email):
    return _fetch_user("email=?", ((email or "").strip().lower(),))


def get_users(active_only=True):
    conn = get_conn()
    sql = f"SELECT {USER_COLUMNS} FROM users"
    if active_only:
        sql += " WHERE active=1"
    rows = conn.execute(sql + " ORDER BY id").fetchall()
    conn.close()
    return [_row_to_user(r) for r in rows]


def user_id_for_telegram(telegram_id):
    """users.id per un telegram_id, oppure None."""
    user = get_user(telegram_id)
    return user["id"] if user else None


# --- registrazione --------------------------------------------------------

def add_user(telegram_id, username=None):
    """Registra un utente Telegram. Ritorna True se creato, False se già esistente
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


def create_web_user(email, password_hash, alert_mode="digest", consent_version=None):
    """Registra un utente dal web. Ritorna l'utente creato, o None se l'email è già usata.
    Default: report giornaliero via email, nessun alert immediato.
    consent_version: versione dell'informativa privacy accettata (registrata con timestamp)."""
    email = (email or "").strip().lower()
    if not email or alert_mode not in ALERT_MODES:
        raise ValueError("email o alert_mode non validi")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return None
    now = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO users (email, password_hash, keywords, active, notify_telegram, notify_email, alert_mode,
                           consent_version, consent_at, created_at)
        VALUES (?, ?, '', 1, 0, 1, ?, ?, ?, ?)
    """, (email, password_hash, alert_mode, consent_version, now if consent_version else None, now))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)


def link_telegram(user_id, telegram_id, username=None):
    """Collega un account Telegram a un utente (es. registrato dal web).
    Ritorna False se quel telegram_id appartiene già a un altro utente."""
    other = get_user(telegram_id)
    if other and other["id"] != user_id:
        return False
    _exec("UPDATE users SET telegram_id=?, username=COALESCE(?, username), notify_telegram=1 WHERE id=?",
          (telegram_id, username, user_id))
    return True


# --- stato / preferenze ---------------------------------------------------

def set_active(user_id, active):
    _exec("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))


def activate_user(telegram_id):
    _exec("UPDATE users SET active=1 WHERE telegram_id=?", (telegram_id,))


def deactivate_user(telegram_id):
    _exec("UPDATE users SET active=0 WHERE telegram_id=?", (telegram_id,))


def _clean_keywords(keywords):
    return [kw.strip() for kw in keywords if kw and kw.strip()]


def set_keywords(user_id, keywords):
    _exec("UPDATE users SET keywords=? WHERE id=?", (",".join(_clean_keywords(keywords)), user_id))


def update_keywords(telegram_id, keywords):
    _exec("UPDATE users SET keywords=? WHERE telegram_id=?", (",".join(_clean_keywords(keywords)), telegram_id))


def set_preferences(user_id, notify_telegram=None, notify_email=None, alert_mode=None, digest_time=None):
    """Aggiorna solo i campi passati (non None). digest_time: 'HH:MM' o '' per usare il default globale."""
    fields, params = [], []
    if notify_telegram is not None:
        fields.append("notify_telegram=?"); params.append(1 if notify_telegram else 0)
    if notify_email is not None:
        fields.append("notify_email=?"); params.append(1 if notify_email else 0)
    if alert_mode is not None:
        if alert_mode not in ALERT_MODES:
            raise ValueError(f"alert_mode non valido: {alert_mode}")
        fields.append("alert_mode=?"); params.append(alert_mode)
    if digest_time is not None:
        fields.append("digest_time=?"); params.append(digest_time or None)
    if not fields:
        return
    _exec(f"UPDATE users SET {', '.join(fields)} WHERE id=?", params + [user_id])


def set_last_digest_date(user_id, day):
    """Segna che il digest del giorno `day` ('YYYY-MM-DD') è stato inviato all'utente."""
    _exec("UPDATE users SET last_digest_date=? WHERE id=?", (day, user_id))


def set_password_hash(user_id, password_hash):
    _exec("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))


def get_password_hash(user_id):
    conn = get_conn()
    row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row["password_hash"] if row else None


def set_email_verified(user_id, verified=True):
    _exec("UPDATE users SET email_verified=? WHERE id=?", (1 if verified else 0, user_id))


# --- GDPR: consenso, export, cancellazione ---------------------------------

def set_consent(user_id, version):
    _exec("UPDATE users SET consent_version=?, consent_at=? WHERE id=?", (version, datetime.now().isoformat(), user_id))


def revoke_consent(user_id):
    """Revoca del consenso: niente più invii (active=0) e consenso azzerato. I dati restano
    finché l'utente non cancella l'account (o riacconsente)."""
    _exec("UPDATE users SET consent_version=NULL, consent_at=NULL, active=0 WHERE id=?", (user_id,))


def delete_user(user_id):
    """Cancellazione definitiva (diritto all'oblio): utente, preferenze fonti e log invii.
    Le fonti aggiunte dall'utente restano (sono dati pubblici) ma senza riferimento a lui."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM deliveries WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM user_sources WHERE user_id=?", (user_id,))
    cur.execute("UPDATE sources SET added_by=NULL WHERE added_by=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0


def export_user_data(user_id):
    """Tutti i dati personali dell'utente in forma leggibile (portabilità)."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    conn = get_conn()
    follows = [dict(r) for r in conn.execute(
        "SELECT s.id AS source_id, s.name, s.url, us.follow FROM user_sources us JOIN sources s ON s.id=us.source_id WHERE us.user_id=?",
        (user_id,))]
    deliveries = [dict(r) for r in conn.execute(
        "SELECT news_id, channel, kind, sent_at FROM deliveries WHERE user_id=? ORDER BY sent_at", (user_id,))]
    conn.close()
    return {"user": user, "source_preferences": follows, "deliveries": deliveries}
