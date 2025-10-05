from threading import Thread
from bot.telegram import TELEGRAM_TOKEN, send_message
from bot.db_user import activate_user, add_user, deactivate_user, update_keywords
from bot.db_news import get_recent_news
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log
from bot.config_loader import get_config
from bot.utils import cleanHTMLPreview
import requests
import time

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def build_help_message():
    cfg = get_config()
    sites = cfg.get("sites", [])
    polling = cfg.get("polling_minutes", 10)
    report_time = cfg.get("daily_report_time", "18:00")
    retention = cfg.get("data_retention_days", 7)
    feed_list = "\n".join([f"• {s['name']}" for s in sites]) if sites else "⚠️ Nessun feed configurato."
    return f"""
🤖 <b>CheckFeed Bot</b> — servizio attivo.

<b>Comandi disponibili:</b>
/start — registra l'utente e mostra questo messaggio
/stop — sospende le notifiche per questo utente
/setkeywords parola1 parola2 — imposta le parole chiave
/fetch — aggiorna manualmente le notizie
/report — genera e invia il report giornaliero
/latest [n] — mostra le ultime n notizie (default 5)

<b>Scheduler:</b>
• Fetch ogni {polling} minuti
• Report giornaliero alle {report_time}
• Retention notizie e log: {retention} giorni

<b>Feed monitorati:</b>
{feed_list}
"""

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
                if not text:
                    continue
                text = text.strip()
                telegram_id = message["chat"]["id"]
                username = message["chat"].get("username", "")

                if text.startswith("/start"):
                    added = add_user(telegram_id, username)
                    if added:
                        send_message("👋 Benvenuto! Imposta le tue parole chiave con /setkeywords parola1 parola2", chat_id=telegram_id)
                    else:
                        activate_user(telegram_id)
                        send_message("👋 Bentornato! Le notifiche sono attive. Usa /setkeywords per aggiornare.", chat_id=telegram_id)

                    # invia il messaggio di help completo
                    help_msg = build_help_message()
                    send_message(help_msg.strip(), parse_mode="HTML", chat_id=telegram_id)

                elif text.startswith("/stop"):
                    deactivate_user(telegram_id)
                    send_message("✅ Hai disattivato le notifiche. Usa /start per riattivarle.", chat_id=telegram_id)

                elif text.startswith("/setkeywords"):
                    parts = text.split()[1:]
                    if not parts:
                        send_message("❗ Usa: /setkeywords parola1 parola2 ...", chat_id=telegram_id)
                        continue
                    update_keywords(telegram_id, parts)
                    send_message(f"✅ Parole chiave aggiornate: {', '.join(parts)}", chat_id=telegram_id)

                elif text.startswith("/fetch"):
                    fetch_news()
                    send_message("✅ Notizie aggiornate manualmente.", chat_id=telegram_id)

                elif text.startswith("/report"):
                    generate_report()
                    send_message("✅ Report generato manualmente.", chat_id=telegram_id)

                elif text.startswith("/latest"):
                    handle_latest_command(telegram_id, text)

        except Exception as e:
            log(f"❌ Errore comandi Telegram: {e}")
            time.sleep(5)


def handle_latest_command(telegram_id, text):
    parts = text.split()
    n = 5
    if len(parts) > 1 and parts[1].isdigit():
        n = int(parts[1])

    rows = get_recent_news(limit=n)
    if not rows:
        send_message("⚠️ Nessuna notizia disponibile.", chat_id=telegram_id)
        return

    lines = [f"📰 <b>Ultime {len(rows)} notizie</b>:\n"]
    for r in rows:
        title = r["title"]
        source = r["source"] or "Sorgente"
        link = r["link"]
        published = r["published_at"] or ""
        preview = cleanHTMLPreview(r.get("content", "") or "")
        lines.append(f"<a href='{link}'>{source}</a> – {published[:16]}\n<b>{title}</b>\n<i>{preview}</i>\n")

    send_message("\n\n".join(lines), parse_mode="HTML", chat_id=telegram_id)


def start_telegram_listener():
    Thread(target=handle_commands, daemon=True).start()
