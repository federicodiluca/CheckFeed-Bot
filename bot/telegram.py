# bot/telegram.py
import requests
import time
from bot.config_loader import get_config
from bot.db_user import get_users
from bot.logger import log

CONFIG = get_config()
TELEGRAM_TOKEN = CONFIG["telegram_token"]
DISABLE_WEB_PAGE_PREVIEW = CONFIG.get("disable_web_page_preview", True)
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Parametri
MAX_MSG_LEN = 4000         # Telegram ~4096, resto conservativo
SLEEP_BETWEEN_MSGS = 0.35  # evita di colpire rate limits
REQUEST_TIMEOUT = 15


def send_message(text, parse_mode=None, chat_id=None, disable_web_page_preview=None):
    """Invia un messaggio Telegram. Con chat_id=None lo invia a tutti gli utenti attivi."""
    if chat_id is None:
        results = []
        for user in get_users():
            uid = user.get("telegram_id")
            if uid:
                results.append(_send_single_message(
                    text, parse_mode=parse_mode, chat_id=uid,
                    disable_web_page_preview=disable_web_page_preview,
                ))
        return results

    return _send_single_message(text, parse_mode=parse_mode, chat_id=chat_id, disable_web_page_preview=disable_web_page_preview)


def _send_single_message(text, parse_mode=None, chat_id=None, disable_web_page_preview=None):
    """Funzione privata: invia un singolo messaggio a Telegram."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": DISABLE_WEB_PAGE_PREVIEW if disable_web_page_preview is None else disable_web_page_preview
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        # JSON: i booleani arrivano a Telegram come veri booleani, non come stringhe
        resp = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=REQUEST_TIMEOUT)
        try:
            data = resp.json()
        except ValueError:
            data = {"ok": False, "status_code": resp.status_code, "text": resp.text}

        if not resp.ok or not data.get("ok"):
            log(f"❌ Telegram error {resp.status_code} - chat_id={chat_id} - resp={data}")
            return {"ok": False, "status_code": resp.status_code, "data": data}

        return {"ok": True, "result": data.get("result")}

    except Exception as e:
        log(f"❌ Errore invio Telegram: {e}")
        return {"ok": False, "exception": str(e)}


def split_long_message(text, max_len=MAX_MSG_LEN):
    """Spezza un testo in parti <= max_len, tagliando preferibilmente su
    doppia newline > newline > spazio."""
    if not text:
        return []

    parts = []
    remaining = text.strip()

    while remaining:
        if len(remaining) <= max_len:
            parts.append(remaining)
            break

        # cerca taglio intelligente: doppia newline > newline > space
        cut = remaining.rfind("\n\n", 0, max_len)
        if cut == -1:
            cut = remaining.rfind("\n", 0, max_len)
        if cut == -1:
            cut = remaining.rfind(" ", 0, max_len)
        if cut == -1 or cut < int(max_len * 0.6):
            cut = max_len

        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    return [p for p in parts if p]


def send_long_message(text, chat_id, parse_mode="HTML"):
    """
    Spezza e invia un testo lungo in più messaggi rispettando il limite.
    Ritorna lista di esiti.
    """
    parts = split_long_message(text)
    results = []
    for i, p in enumerate(parts):
        res = send_message(p, parse_mode=parse_mode, chat_id=chat_id)
        results.append(res)
        if i < len(parts) - 1:
            time.sleep(SLEEP_BETWEEN_MSGS)
    return results
