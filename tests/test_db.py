from datetime import datetime, timedelta, timezone

import bot.db as db
from bot.db_news import add_news, cleanup_old_news, get_recent_news, get_today_news
from bot.db_user import (
    activate_user,
    add_user,
    deactivate_user,
    get_user,
    get_users,
    update_keywords,
)


# --- users ----------------------------------------------------------------

def test_add_user_is_idempotent_and_updates_username():
    assert add_user(1, "alice") is True
    assert add_user(1, "alice2") is False
    assert get_user(1)["username"] == "alice2"
    assert add_user(1, None) is False
    assert get_user(1)["username"] == "alice2"  # username None non sovrascrive


def test_get_user_unknown_returns_none():
    assert get_user(999) is None


def test_new_user_has_empty_keyword_list_not_blank_string():
    add_user(1)
    assert get_user(1)["keywords"] == []
    assert get_users() == [{"telegram_id": 1, "keywords": []}]


def test_update_keywords_roundtrip_strips_blanks():
    add_user(1)
    update_keywords(1, [" scuola ", "", "GRADUATORIA FINALE", "  "])
    assert get_user(1)["keywords"] == ["scuola", "GRADUATORIA FINALE"]


def test_activate_deactivate_and_active_only_filter():
    add_user(1)
    add_user(2)
    deactivate_user(2)
    assert [u["telegram_id"] for u in get_users()] == [1]
    assert sorted(u["telegram_id"] for u in get_users(active_only=False)) == [1, 2]
    assert get_user(2)["active"] is False
    activate_user(2)
    assert sorted(u["telegram_id"] for u in get_users()) == [1, 2]


# --- news -----------------------------------------------------------------

def test_add_news_dedupes_on_link():
    assert add_news("T1", "https://x/1", "S", "Mon, 29 Sep 2025 10:05:28 +0000", "c") is True
    assert add_news("T1 bis", "https://x/1", "S", "Mon, 29 Sep 2025 10:05:28 +0000", "c") is False
    rows = get_recent_news()
    assert len(rows) == 1
    assert rows[0]["title"] == "T1"
    assert rows[0]["published_at"] == "2025-09-29 10:05:28"


def test_add_news_truncates_long_content_and_accepts_none():
    add_news("T", "https://x/1", "S", "", "x" * 30000)
    add_news("T2", "https://x/2", "S", None, None)
    by_link = {r["link"]: r for r in get_recent_news()}
    assert len(by_link["https://x/1"]["content"]) == 20000
    assert by_link["https://x/2"]["content"] == ""
    assert by_link["https://x/2"]["published_at"]  # fallback a "now"


def test_get_recent_news_orders_by_published_desc_and_limits():
    add_news("old", "https://x/old", "S", "Mon, 01 Sep 2025 10:00:00 +0000")
    add_news("new", "https://x/new", "S", "Mon, 29 Sep 2025 10:00:00 +0000")
    add_news("mid", "https://x/mid", "S", "Mon, 15 Sep 2025 10:00:00 +0000")
    assert [r["title"] for r in get_recent_news(limit=2)] == ["new", "mid"]
    assert get_recent_news(limit=0) == []


def test_get_today_news_uses_current_instant_by_default():
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO news (title, link, source, published_at) VALUES "
        "('today', 'https://x/t', 'S', datetime('now')),"
        "('yesterday', 'https://x/y', 'S', datetime('now', '-1 day')),"
        "('tomorrow', 'https://x/tm', 'S', datetime('now', '+1 day'))"
    )
    conn.commit()
    conn.close()
    assert [r["title"] for r in get_today_news()] == ["today"]


def test_get_today_news_uses_local_day_boundaries():
    """Il 'giorno' è quello locale (come l'intestazione del report), non quello UTC.
    Con TZ +02:00 il 5 ottobre locale va dalle 22:00 UTC del 4 alle 22:00 UTC del 5."""
    conn = db.get_conn()
    conn.executemany(
        "INSERT INTO news (title, link, source, published_at) VALUES (?, ?, 'S', ?)",
        [
            ("before", "https://x/1", "2025-10-04 21:59:59"),
            ("first", "https://x/2", "2025-10-04 22:00:00"),
            ("last", "https://x/3", "2025-10-05 21:59:59"),
            ("after", "https://x/4", "2025-10-05 22:00:00"),
        ],
    )
    conn.commit()
    conn.close()
    now = datetime(2025, 10, 5, 1, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert [r["title"] for r in get_today_news(now=now)] == ["last", "first"]


def test_cleanup_old_news_uses_fetched_at():
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO news (title, link, source, published_at, fetched_at) VALUES "
        "('keep', 'https://x/k', 'S', datetime('now'), datetime('now', '-2 days')),"
        "('drop', 'https://x/d', 'S', datetime('now'), datetime('now', '-10 days'))"
    )
    conn.commit()
    conn.close()
    assert cleanup_old_news(days=7) == 1
    assert [r["title"] for r in get_recent_news()] == ["keep"]
