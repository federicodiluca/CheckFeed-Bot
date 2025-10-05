import requests
from bot.config_loader import get_config
from bot.db_user import get_users
from bot.logger import log

CONFIG = get_config()
TELEGRAM_TOKEN = CONFIG["telegram_token"]
DISABLE_WEB_PAGE_PREVIEW = CONFIG.get("disable_web_page_preview", True)

def send_message(text, parse_mode=None, chat_id=None):
    """Invia un messaggio Telegram (a uno o più utenti)."""    

    # Se non è specificato un chat_id, invia a tutti gli utenti attivi
    if not chat_id:
        users = get_users()
        for user in users:
            send_message(text, parse_mode=parse_mode, chat_id=user["chat_id"])
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": DISABLE_WEB_PAGE_PREVIEW
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        requests.post(url, data=payload)
    except Exception as e:
        log(f"❌ Errore invio Telegram: {e}")
