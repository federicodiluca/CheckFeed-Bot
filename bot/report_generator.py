from datetime import datetime
from bot.db_news import get_today_news
from bot.db_user import get_users
from bot.logger import log
from bot.telegram import send_message
from bot.utils import cleanHTMLPreview

def generate_report(target_chat_id=None):
    """
    Genera il report giornaliero.
    Se target_chat_id è None → invia a tutti gli utenti attivi.
    Se target_chat_id è specificato → invia solo a quell'utente.
    """
    today_news = get_today_news()

    if not today_news:
        msg = "🗓️ Nessuna notizia per oggi."
        if target_chat_id:
            send_message(msg, chat_id=target_chat_id)
        else:
            users = get_users()
            for user in users:
                send_message(msg, chat_id=user["telegram_id"])
        log("🗓️ Nessuna notizia per oggi.")
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

    # invio
    if target_chat_id:
        send_message(text, parse_mode="HTML", chat_id=target_chat_id)
        log(f"📄 Report inviato manualmente a {target_chat_id}.")
    else:
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
