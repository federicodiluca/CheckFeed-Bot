from threading import Thread
from email.utils import parsedate_to_datetime
from bot.telegram import TELEGRAM_TOKEN, CHAT_ID, send_message
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.data_manager import load_news
from bot.logger import log
from bot.utils import cleanHTMLPreview
import requests
import time

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def handle_commands():
    """Gestisce i comandi Telegram ricevuti via polling."""
    offset = None
    while True:
        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={"timeout": 10, "offset": offset})
            data = resp.json()

            for result in data.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                text = message.get("text", "").strip()

                if not text:
                    continue

                if text.startswith("/fetch"):
                    fetch_news()
                    send_message("✅ Notizie aggiornate manualmente.")

                elif text.startswith("/report"):
                    generate_report()
                    send_message("✅ Report generato manualmente.")

                elif text.startswith("/latest"):
                    handle_latest_command(text)

        except Exception as e:
            send_message(f"❌ Errore comandi: {e}")
            log(f"❌ Errore comandi Telegram: {e}")
            time.sleep(5)


def handle_latest_command(text):
    parts = text.split()
    n = 5
    if len(parts) > 1 and parts[1].isdigit():
        n = int(parts[1])

    news = load_news()
    if not news:
        send_message("⚠️ Nessuna notizia disponibile.")
        return

    # Ordina per data pubblicazione (decrescente)
    def parse_date(n):
        pub_str = n.get("published", "")
        try:
            return parsedate_to_datetime(pub_str)
        except Exception:
            return datetime.min  # se non riesce, mettiamo la news in fondo

    news_sorted = sorted(news, key=parse_date, reverse=True)
    latest = news_sorted[:n]

    # Composizione messaggio
    message_lines = [f"📰 <b>Ultime {len(latest)} notizie</b>:\n"]
    for item in latest:
        title = str(item.get("title", "Senza titolo"))
        source = str(item.get("source", "Sconosciuto"))
        pub_dt = parse_date(item)
        published = pub_dt.strftime("%Y-%m-%d %H:%M")
        link = str(item.get("link", ""))
        content = str(item.get("content") or item.get("description") or "")
        preview = cleanHTMLPreview(content)

        message_lines.append(
            f"📰 <a href='{link}'>{source}</a>, {published}\n<b>{title}</b>\n<i>{preview}</i>"
        )

    send_message("\n\n".join(message_lines), parse_mode="HTML")
    log(f"📤 Inviate le ultime {len(latest)} notizie via Telegram.")


def start_telegram_listener():
    """Avvia il listener dei comandi in un thread separato."""
    Thread(target=handle_commands, daemon=True).start()
