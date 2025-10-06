from datetime import datetime
from bot.db_news import get_today_news
from bot.db_user import get_users
from bot.logger import log
from bot.telegram import send_long_message
from bot.utils import cleanHTMLPreview
import html

def generate_report(target_chat_id=None):
    today_news = get_today_news()

    if not today_news:
        msg = "🗓️ Nessuna notizia per oggi."
        if target_chat_id:
            send_long_message(msg, chat_id=target_chat_id, parse_mode="HTML")
        else:
            users = get_users()
            for u in users:
                send_long_message(msg, chat_id=u["telegram_id"], parse_mode="HTML")
        log("🗓️ Nessuna notizia per oggi.")
        return

    lines = [f"📢 <b>Report del {datetime.now():%d/%m/%Y}</b> — {len(today_news)} notizie trovate\n"]
    for n in today_news:
        title = cleanHTMLPreview((n.get("title") or "Titolo non disponibile").strip())
        source = cleanHTMLPreview(n.get("source") or "Sorgente sconosciuta")
        link = cleanHTMLPreview(n.get("link") or "")
        content = n.get("content") or ""
        preview = cleanHTMLPreview(content)
        published = n.get("published_at", "")[:16]
        lines.append(f"🗞️ <a href=\"{link}\">{source}</a> — {published}\n<b>{title}</b>\n<i>{preview}</i>\n")

    text = "\n".join(lines).strip()

    # log diagnostico prima dell'invio
    log(f"🔎 Report length: {len(text)} chars; preview: {text[:200]!r}")

    if target_chat_id:
        send_long_message(text, chat_id=target_chat_id, parse_mode="HTML")
        log(f"📄 Report inviato manualmente a {target_chat_id}.")
    else:
        users = get_users()
        if not users:
            log("⚠️ Nessun utente attivo per l'invio del report.")
            return
        sent = 0
        for u in users:
            try:
                send_long_message(text, chat_id=u["telegram_id"], parse_mode="HTML")
                sent += 1
            except Exception as e:
                log(f"⚠️ Errore nell'invio report a {u['telegram_id']}: {e}")
        log(f"📄 Report Telegram inviato a {sent} utenti ({len(today_news)} notizie).")
