from datetime import datetime
from bot.db_news import get_today_news
from bot.db_user import get_users
from bot.logger import log
from bot.telegram import send_message
from bot.utils import cleanHTMLPreview

def generate_report():
    """
    Genera il report giornaliero e lo invia a tutti gli utenti attivi.
    Le notizie sono filtrate per data odierna (campo published_at).
    """
    today_news = get_today_news()  # già filtrato lato DB

    if not today_news:
        log("🗓️ Nessuna notizia per oggi.")
        users = get_users()
        for user in users:
            send_message("🗓️ Nessuna notizia per oggi.", chat_id=user["telegram_id"])
        return

    lines = [f"📢 <b>Report del {datetime.now():%d/%m/%Y}</b> — {len(today_news)} notizie trovate\n"]

    for n in today_news:
        title = n.get("title", "Titolo non disponibile").strip()
        source = n.get("source") or "Sorgente sconosciuta"
        link = n.get("link")
        content = n.get("content") or ""
        preview = cleanHTMLPreview(content)
        published = n.get("published_at", "")[:16]

        lines.append(f"🗞️ <a href='{link}'>{source}</a> — {published}\n<b>{title}</b>\n<i>{preview}</i>\n")

    text = "\n".join(lines).strip()

    users = get_users()
    if not users:
        log("⚠️ Nessun utente attivo per l'invio del report.")
        return

    for user in users:
        try:
            send_message(text, parse_mode="HTML", chat_id=user["telegram_id"])
        except Exception as e:
            log(f"⚠️ Errore nell'invio report a {user['telegram_id']}: {e}")

    log(f"📄 Report Telegram inviato a {len(users)} utenti ({len(today_news)} notizie).")
