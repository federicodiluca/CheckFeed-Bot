import requests
from bot.config_loader import get_config

CONFIG = get_config()
TELEGRAM_TOKEN = CONFIG["telegram_token"]
CHAT_ID = CONFIG["chat_id"]

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        from bot.logger import log
        log(f"❌ Errore invio Telegram: {e}")
