import bot.db as db
import bot.report_generator as report_generator
from bot.utils import format_local_datetime
from bot.db_user import add_user, deactivate_user


def insert_today(title, link, content="", source="S"):
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO news (title, link, source, published_at, content) VALUES (?, ?, ?, datetime('now'), ?)",
        (title, link, source, content),
    )
    conn.commit()
    conn.close()


def test_build_report_empty_returns_none():
    assert report_generator.build_report([]) is None


def test_build_report_escapes_fields_and_handles_missing_values():
    text = report_generator.build_report([
        {"title": "A & B <c>", "link": "https://x/?a=1&b=2", "source": "Src <1>", "content": "<p>Ciao</p>", "published_at": "2025-10-05 10:00:00"},
        {"title": None, "link": None, "source": None, "content": None, "published_at": None},
    ])
    assert "2 notizie trovate" in text
    assert "<b>A &amp; B &lt;c&gt;</b>" in text
    assert '<a href="https://x/?a=1&amp;b=2">Src &lt;1&gt;</a> — ' + format_local_datetime("2025-10-05 10:00:00") in text
    assert "<i>Ciao</i>" in text
    assert "Titolo non disponibile" in text
    assert "Sorgente sconosciuta" in text


def test_generate_report_to_target_chat(sent_messages):
    insert_today("Oggi", "https://x/today", "contenuto")
    report_generator.generate_report(target_chat_id=99)
    assert len(sent_messages) == 1
    assert sent_messages[0]["chat_id"] == 99
    assert "<b>Oggi</b>" in sent_messages[0]["text"]


def test_generate_report_no_news_broadcasts_placeholder(sent_messages):
    add_user(1)
    add_user(2)
    deactivate_user(2)
    report_generator.generate_report()
    assert [m["chat_id"] for m in sent_messages] == [1]
    assert "Nessuna notizia" in sent_messages[0]["text"]


def test_generate_report_broadcast_to_active_users(sent_messages):
    insert_today("Oggi", "https://x/today")
    add_user(1)
    add_user(2)
    add_user(3)
    deactivate_user(3)
    report_generator.generate_report()
    assert sorted(m["chat_id"] for m in sent_messages) == [1, 2]


def test_generate_report_without_users_sends_nothing(sent_messages):
    insert_today("Oggi", "https://x/today")
    report_generator.generate_report()
    assert sent_messages == []
