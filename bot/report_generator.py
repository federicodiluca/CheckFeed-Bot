from datetime import datetime
from bot.data_manager import load_news
from bot.logger import log
from bot.telegram import send_message
import os

def generate_report():
    news = load_news()
    today = datetime.now().date()
    today_news = [n for n in news if today.isoformat() in n.get("published", "")]

    if not today_news:
        log("Nessuna notizia per oggi.")
        send_message("🗓️ Nessuna notizia per oggi.")
        return

    # Componi messaggio Telegram
    message_lines = [f"📢 Report del {today} ({len(today_news)} notizie):\n"]
    for n in today_news:
        message_lines.append(f"- {n['title']} ({n['source']})\n  {n['link']}")
    message_text = "\n\n".join(message_lines)

    # Invio Telegram
    send_message(message_text)
    log(f"📄 Report Telegram inviato con {len(today_news)} notizie.")
