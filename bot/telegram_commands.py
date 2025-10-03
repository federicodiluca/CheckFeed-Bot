from threading import Thread
from bot.telegram import TELEGRAM_TOKEN, CHAT_ID, send_message
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
import requests
import time

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def handle_commands():
    offset = None
    while True:
        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={"timeout": 10, "offset": offset})
            data = resp.json()
            for result in data.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                text = message.get("text", "")
                if text.startswith("/fetch"):
                    fetch_news()
                    send_message("✅ Notizie aggiornate manualmente.")
                elif text.startswith("/report"):
                    generate_report()
                    send_message("✅ Report generato manualmente.")
        except Exception as e:
            send_message(f"❌ Errore comandi: {e}")
            time.sleep(5)

def start_telegram_listener():
    Thread(target=handle_commands, daemon=True).start()
