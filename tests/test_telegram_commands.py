import pytest

import bot.db as db
import bot.telegram_commands as tc
from bot.db_user import add_user, get_user, update_keywords


def update(text, chat_id=1, username="alice", update_id=1):
    return {
        "update_id": update_id,
        "message": {"text": text, "chat": {"id": chat_id, "username": username}},
    }


# --- parse_command --------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("/start", ("start", "")),
    ("  /Start  ", ("start", "")),
    ("/setkeywords a, b", ("setkeywords", "a, b")),
    ("/setkeywords@CheckFeedBot a, b", ("setkeywords", "a, b")),
    ("/latest 3", ("latest", "3")),
    ("ciao", (None, "")),
    ("", (None, "")),
    (None, (None, "")),
    ("/", (None, "")),
])
def test_parse_command(text, expected):
    assert tc.parse_command(text) == expected


# --- handle_update dispatch ----------------------------------------------

def test_handle_update_ignores_non_messages_and_plain_text(sent_messages):
    assert tc.handle_update({"update_id": 1, "edited_message": {"text": "/start"}}) is None
    assert tc.handle_update(update("ciao bot")) is None
    assert tc.handle_update({"update_id": 1, "message": {"text": "/start"}}) is None  # senza chat
    assert sent_messages == []


def test_unknown_command_replies(sent_messages):
    assert tc.handle_update(update("/startfoo")) == "startfoo"
    assert "non riconosciuto" in sent_messages[0]["text"]
    assert "/startfoo" in sent_messages[0]["text"]


# --- /start /stop ---------------------------------------------------------

def test_start_registers_user_and_sends_help(sent_messages):
    tc.handle_update(update("/start"))
    user = get_user(1)
    assert user and user["active"] and user["username"] == "alice"
    assert len(sent_messages) == 2
    assert "Benvenuto" in sent_messages[0]["text"]
    help_text = sent_messages[1]["text"]
    assert sent_messages[1]["parse_mode"] == "HTML"
    assert "• Feed Uno" in help_text and "• Feed Due" in help_text
    assert "Fetch ogni 15 minuti" in help_text
    assert "Report giornaliero alle 18:00" in help_text
    assert "Retention notizie e log: 3 giorni" in help_text


def test_stop_then_start_reactivates(sent_messages):
    tc.handle_update(update("/start"))
    tc.handle_update(update("/stop"))
    assert get_user(1)["active"] is False
    assert "disattivato" in sent_messages[-1]["text"]
    tc.handle_update(update("/start"))
    assert get_user(1)["active"] is True
    assert "Bentornato" in sent_messages[-2]["text"]


# --- keywords -------------------------------------------------------------

def test_setkeywords_adds_and_dedupes_case_insensitively(sent_messages):
    add_user(1)
    tc.handle_update(update("/setkeywords scuola, Docenti, GRADUATORIA FINALE"))
    assert get_user(1)["keywords"] == ["scuola", "Docenti", "GRADUATORIA FINALE"]
    assert "✅ Keyword aggiunte: scuola, Docenti, GRADUATORIA FINALE" in sent_messages[-1]["text"]
    assert "Totale keyword: 3" in sent_messages[-1]["text"]

    tc.handle_update(update("/setkeywords SCUOLA, prova"))
    assert get_user(1)["keywords"] == ["scuola", "Docenti", "GRADUATORIA FINALE", "prova"]
    assert "Già presenti: SCUOLA" in sent_messages[-1]["text"]

    tc.handle_update(update("/setkeywords scuola"))
    assert "già presenti" in sent_messages[-1]["text"]
    assert get_user(1)["keywords"] == ["scuola", "Docenti", "GRADUATORIA FINALE", "prova"]


def test_setkeywords_without_args_shows_usage(sent_messages):
    add_user(1)
    tc.handle_update(update("/setkeywords"))
    tc.handle_update(update("/setkeywords , ,"))
    assert all("Usa: /setkeywords" in m["text"] for m in sent_messages)
    assert get_user(1)["keywords"] == []


def test_setkeywords_registers_unknown_user_on_the_fly(sent_messages):
    tc.handle_update(update("/setkeywords scuola", chat_id=77))
    assert get_user(77)["keywords"] == ["scuola"]


def test_removekeywords(sent_messages):
    add_user(1)
    update_keywords(1, ["scuola", "Docenti", "prova"])

    tc.handle_update(update("/removekeywords DOCENTI, inesistente"))
    assert get_user(1)["keywords"] == ["scuola", "prova"]
    assert "Keyword rimosse: Docenti" in sent_messages[-1]["text"]
    assert "Non trovate: inesistente" in sent_messages[-1]["text"]
    assert "Keyword rimanenti: scuola, prova" in sent_messages[-1]["text"]

    tc.handle_update(update("/removekeywords nulla"))
    assert "Nessuna delle keyword" in sent_messages[-1]["text"]

    tc.handle_update(update("/removekeywords scuola, prova"))
    assert get_user(1)["keywords"] == []
    assert "Non hai più keyword" in sent_messages[-1]["text"]

    tc.handle_update(update("/removekeywords scuola"))
    assert "Non hai keyword impostate" in sent_messages[-1]["text"]

    tc.handle_update(update("/removekeywords"))
    assert "Usa: /removekeywords" in sent_messages[-1]["text"]


def test_keywords_command_lists_or_reports_none(sent_messages):
    """Regressione: con keywords vuote rispondeva 'Le tue keyword attive (0)'."""
    add_user(1)
    tc.handle_update(update("/keywords"))
    assert "Non hai keyword impostate" in sent_messages[-1]["text"]

    update_keywords(1, ["scuola", "A & B"])
    tc.handle_update(update("/keywords"))
    text = sent_messages[-1]["text"]
    assert "Le tue keyword attive (2)" in text
    assert "• scuola" in text and "• A &amp; B" in text
    assert sent_messages[-1]["parse_mode"] == "HTML"


def test_keywords_command_not_confused_with_setkeywords(sent_messages):
    add_user(1)
    update_keywords(1, ["x"])
    assert tc.handle_update(update("/keywords")) == "keywords"
    assert tc.handle_update(update("/setkeywords y")) == "setkeywords"
    assert get_user(1)["keywords"] == ["x", "y"]


# --- /commands /fetch /report /latest ------------------------------------

def test_commands_message(sent_messages):
    tc.handle_update(update("/commands"))
    assert "/setkeywords" in sent_messages[0]["text"]
    assert sent_messages[0]["parse_mode"] == "HTML"
    tc.handle_update(update("/help"))
    assert sent_messages[1]["text"] == sent_messages[0]["text"]


def test_fetch_command_reports_count(sent_messages, monkeypatch):
    monkeypatch.setattr(tc, "fetch_news", lambda: 3)
    tc.handle_update(update("/fetch"))
    assert "3 nuove" in sent_messages[-1]["text"]


def test_report_command_targets_requesting_chat(sent_messages, monkeypatch):
    called = []
    monkeypatch.setattr(tc, "generate_report", lambda target_chat_id=None: called.append(target_chat_id))
    tc.handle_update(update("/report", chat_id=5))
    assert called == [5]


def insert_news(n):
    conn = db.get_conn()
    for i in range(n):
        conn.execute(
            "INSERT INTO news (title, link, source, published_at, content) VALUES (?, ?, ?, ?, ?)",
            (f"News {i} & co", f"https://x/{i}", "Src", f"2025-10-{(i % 28) + 1:02d} 10:00:00", "<p>c</p>"),
        )
    conn.commit()
    conn.close()


def test_latest_default_and_bounds(sent_messages):
    tc.handle_update(update("/latest"))
    assert "Nessuna notizia" in sent_messages[-1]["text"]

    insert_news(8)
    tc.handle_update(update("/latest"))
    assert "Ultime 5 notizie" in sent_messages[-1]["text"]

    tc.handle_update(update("/latest 2"))
    assert "Ultime 2 notizie" in sent_messages[-1]["text"]

    tc.handle_update(update("/latest 0"))
    assert "Ultime 1 notizie" in sent_messages[-1]["text"]

    tc.handle_update(update("/latest 9999"))
    assert "Ultime 8 notizie" in sent_messages[-1]["text"]

    tc.handle_update(update("/latest abc"))
    assert "Ultime 5 notizie" in sent_messages[-1]["text"]


def test_latest_escapes_html(sent_messages):
    insert_news(1)
    tc.handle_update(update("/latest 1"))
    text = sent_messages[-1]["text"]
    assert "<b>News 0 &amp; co</b>" in text
    assert '<a href="https://x/0">Src</a>' in text
    assert "<i>c</i>" in text


# --- handle_commands polling loop ----------------------------------------

def test_handle_commands_polls_with_timeout_and_advances_offset(monkeypatch):
    calls = []
    handled = []

    class Stop(Exception):
        pass

    responses = iter([
        {"ok": True, "result": [update("/commands", update_id=10), update("/commands", update_id=11)]},
        {"ok": False, "error_code": 409, "description": "Conflict"},
    ])

    def fake_get(url, params=None, timeout=None, **kw):
        calls.append({"params": dict(params), "timeout": timeout})
        try:
            payload = next(responses)
        except StopIteration:
            raise Stop()
        from tests.conftest import FakeResponse
        return FakeResponse(payload)

    slept = []

    def fake_sleep(s):
        slept.append(s)
        if len(slept) >= 2:
            raise Stop()

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tc, "handle_update", lambda u: handled.append(u["update_id"]))
    monkeypatch.setattr(tc.time, "sleep", fake_sleep)

    with pytest.raises(Stop):
        tc.handle_commands()

    assert handled == [10, 11]
    assert calls[0]["params"]["offset"] is None
    assert calls[1]["params"]["offset"] == 12
    assert all(c["timeout"] > c["params"]["timeout"] for c in calls)
    assert slept and slept[0] == 5  # ok=False -> pausa, niente busy loop
