from types import SimpleNamespace

import bot.news_fetcher as news_fetcher
from bot.db_news import get_recent_news
from bot.db_user import add_user, deactivate_user, update_keywords


def make_feed(entries, bozo=False, bozo_exception=None):
    return SimpleNamespace(entries=entries, bozo=bozo, bozo_exception=bozo_exception)


def entry(**kw):
    """Entry stile feedparser (dict con accesso .get)."""
    return dict(kw)


def install_feeds(monkeypatch, by_url):
    """Sostituisce feedparser.parse con una mappa url -> feed."""
    calls = []

    def fake_parse(url):
        calls.append(url)
        result = by_url.get(url, make_feed([]))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(news_fetcher.feedparser, "parse", fake_parse)
    return calls


# --- extract_entry --------------------------------------------------------

def test_extract_entry_prefers_content_then_description_then_summary():
    e = entry(link="https://x/1", title="T", published="Mon, 29 Sep 2025 10:05:28 +0000",
              content=[{"value": "<p>full</p>"}], description="desc", summary="sum")
    assert news_fetcher.extract_entry(e) == ("T", "https://x/1", "Mon, 29 Sep 2025 10:05:28 +0000", "<p>full</p>")

    e = entry(link="https://x/1", title="T", description="desc", summary="sum")
    assert news_fetcher.extract_entry(e)[3] == "desc"

    e = entry(link="https://x/1", title="T", summary="sum")
    assert news_fetcher.extract_entry(e)[3] == "sum"


def test_extract_entry_without_link_returns_none_and_missing_title_gets_placeholder():
    assert news_fetcher.extract_entry(entry(title="T")) is None
    assert news_fetcher.extract_entry(entry(link="  ")) is None
    title, _, published, text = news_fetcher.extract_entry(entry(link="https://x/1"))
    assert title == "(senza titolo)"
    assert published  # fallback a now
    assert text == ""


def test_extract_entry_uses_updated_when_published_missing():
    e = entry(link="https://x/1", title="T", updated="2025-10-05T10:00:00Z")
    assert news_fetcher.extract_entry(e)[2] == "2025-10-05T10:00:00Z"


# --- fetch_news -----------------------------------------------------------

def test_fetch_news_stores_new_entries_and_dedupes(monkeypatch, sent_messages):
    feed = make_feed([
        entry(link="https://x/1", title="Uno", published="Mon, 29 Sep 2025 10:05:28 +0000", summary="s1"),
        entry(link="https://x/2", title="Due", published="Mon, 29 Sep 2025 11:05:28 +0000", summary="s2"),
    ])
    calls = install_feeds(monkeypatch, {"https://example.org/uno/feed/": feed})

    assert news_fetcher.fetch_news() == 2
    assert sorted(calls) == ["https://example.org/due/feed/", "https://example.org/uno/feed/"]
    assert {r["link"] for r in get_recent_news()} == {"https://x/1", "https://x/2"}
    assert {r["source"] for r in get_recent_news()} == {"Feed Uno"}

    # secondo giro: niente di nuovo, niente notifiche
    assert news_fetcher.fetch_news() == 0
    assert sent_messages == []


def test_fetch_news_notifies_only_matching_active_users(monkeypatch, sent_messages):
    add_user(10); update_keywords(10, ["docenti"])
    add_user(20); update_keywords(20, ["graduatoria finale"])
    add_user(30); update_keywords(30, ["docenti"]); deactivate_user(30)
    add_user(40)  # nessuna keyword

    feed = make_feed([
        entry(link="https://x/1", title="Concorso docenti & ATA", summary="<p>Testo <b>breve</b></p>"),
        entry(link="https://x/2", title="Altro", content=[{"value": "pubblicata la GRADUATORIA FINALE"}]),
        entry(link="https://x/3", title="Nulla", summary="<div class='docenti'>senza match nel testo</div>"),
    ])
    install_feeds(monkeypatch, {"https://example.org/uno/feed/": feed})

    news_fetcher.fetch_news()

    by_chat = {}
    for m in sent_messages:
        by_chat.setdefault(m["chat_id"], []).append(m)
    assert set(by_chat) == {10, 20}
    assert len(by_chat[10]) == 1 and len(by_chat[20]) == 1

    msg = by_chat[10][0]
    assert msg["parse_mode"] == "HTML"
    # titolo escapato: '&' -> '&amp;' e nessun tag grezzo dal contenuto
    assert "<b>Concorso docenti &amp; ATA</b>" in msg["text"]
    assert "<i>Testo breve</i>" in msg["text"]
    assert '<a href="https://x/1">Feed Uno</a>' in msg["text"]


def test_fetch_news_skips_broken_feed_and_continues(monkeypatch, sent_messages):
    good = make_feed([entry(link="https://x/ok", title="ok")])
    broken = make_feed([], bozo=True, bozo_exception=Exception("URLError"))
    install_feeds(monkeypatch, {
        "https://example.org/uno/feed/": broken,
        "https://example.org/due/feed/": good,
    })
    assert news_fetcher.fetch_news() == 1
    assert get_recent_news()[0]["source"] == "Feed Due"


def test_fetch_news_survives_parse_exception(monkeypatch, sent_messages):
    install_feeds(monkeypatch, {
        "https://example.org/uno/feed/": RuntimeError("boom"),
        "https://example.org/due/feed/": make_feed([entry(link="https://x/ok", title="ok")]),
    })
    assert news_fetcher.fetch_news() == 1


def test_fetch_news_ignores_entries_without_link(monkeypatch, sent_messages):
    feed = make_feed([entry(title="senza link"), entry(link="https://x/1", title="con link")])
    install_feeds(monkeypatch, {"https://example.org/uno/feed/": feed})
    assert news_fetcher.fetch_news() == 1


def test_notification_error_does_not_abort_fetch(monkeypatch):
    add_user(10); update_keywords(10, ["ok"])

    def failing_send(*a, **k):
        raise RuntimeError("telegram down")

    monkeypatch.setattr(news_fetcher, "send_message", failing_send)
    feed = make_feed([entry(link="https://x/1", title="ok 1"), entry(link="https://x/2", title="ok 2")])
    install_feeds(monkeypatch, {"https://example.org/uno/feed/": feed})

    assert news_fetcher.fetch_news() == 2
    assert len(get_recent_news()) == 2
