"""Setup condiviso dei test.

I moduli `bot.*` leggono config, DB e cartella log a import-time, quindi
impostiamo le variabili d'ambiente PRIMA di importarli.
"""
import json
import os
import tempfile

import pytest

_SESSION_DIR = tempfile.mkdtemp(prefix="checkfeed-tests-")
_CONFIG_PATH = os.path.join(_SESSION_DIR, "config.json")

TEST_CONFIG = {
    "telegram_token": "123456:TEST-TOKEN",
    "machine_name": "Test-Machine",
    "sites": [
        {"name": "Feed Uno", "url": "https://example.org/uno/feed/"},
        {"name": "Feed Due", "url": "https://example.org/due/feed/"},
    ],
    "daily_report_time": "18:00",
    "polling_minutes": 15,
    "data_retention_days": 3,
    "disable_web_page_preview": True,
}

with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump(TEST_CONFIG, f)

os.environ["CHECKFEED_CONFIG"] = _CONFIG_PATH
os.environ["CHECKFEED_DB_PATH"] = os.path.join(_SESSION_DIR, "test.db")
os.environ["CHECKFEED_LOG_DIR"] = os.path.join(_SESSION_DIR, "logs")

# Solo ora è sicuro importare i moduli del bot
import bot.db as db  # noqa: E402
import bot.telegram as telegram  # noqa: E402
import bot.telegram_commands as telegram_commands  # noqa: E402
import bot.news_fetcher as news_fetcher  # noqa: E402


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Nessun test deve raggiungere la rete: requests.* e feedparser.parse falliscono di default."""
    def _blocked(*args, **kwargs):
        raise AssertionError(f"Accesso di rete non previsto: {args} {kwargs}")

    monkeypatch.setattr("requests.post", _blocked)
    monkeypatch.setattr("requests.get", _blocked)
    monkeypatch.setattr(news_fetcher.feedparser, "parse", _blocked)
    yield


@pytest.fixture(autouse=True)
def fresh_db():
    """Database SQLite vuoto per ogni test."""
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    yield
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)


@pytest.fixture
def sent_messages(monkeypatch):
    """Cattura i messaggi che il bot invierebbe su Telegram, ovunque venga usato send_message."""
    messages = []

    def fake_send(text, parse_mode=None, chat_id=None, disable_web_page_preview=None):
        messages.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})
        return {"ok": True, "result": {}}

    # send_long_message di bot.telegram chiama send_message dello stesso modulo
    monkeypatch.setattr(telegram, "send_message", fake_send)
    monkeypatch.setattr(telegram_commands, "send_message", fake_send)
    monkeypatch.setattr(news_fetcher, "send_message", fake_send)
    monkeypatch.setattr(telegram, "SLEEP_BETWEEN_MSGS", 0)
    return messages
