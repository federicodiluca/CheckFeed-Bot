import requests
from bot.config_loader import get_config
from bot.logger import log

CONFIG = get_config()
TELEGRAM_TOKEN = CONFIG["telegram_token"]
CHAT_ID = CONFIG["chat_id"]
DISABLE_WEB_PAGE_PREVIEW = CONFIG.get("disable_web_page_preview", True)

def send_message(text, parse_mode="HTML"):
    """Invia un messaggio Telegram (supporta HTML opzionale)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": DISABLE_WEB_PAGE_PREVIEW
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        requests.post(url, data=payload)
    except Exception as e:
        log(f"❌ Errore invio Telegram: {e}")
