from datetime import datetime
from bot.db_news import get_today_news
from bot.db_sources import get_followed_source_ids
from bot.db_user import get_users
from bot.logger import log
from bot.telegram import send_long_message
from bot.utils import cleanHTMLPreview, escape_html, format_local_datetime

NO_NEWS_MESSAGE = "🗓️ Nessuna notizia per oggi dalle fonti che segui."


def build_report(today_news):
    """Costruisce il testo HTML del report giornaliero. Ritorna None se non ci sono notizie."""
    if not today_news:
        return None

    lines = [f"📢 <b>Report del {datetime.now():%d/%m/%Y}</b> — {len(today_news)} notizie trovate\n"]
    for n in today_news:
        title = escape_html((n.get("title") or "Titolo non disponibile").strip())
        source = escape_html(n.get("source") or "Sorgente sconosciuta")
        link = escape_html(n.get("link") or "")
        preview = cleanHTMLPreview(n.get("content") or "")
        published = format_local_datetime(n.get("published_at"))
        lines.append(f"🗞️ <a href=\"{link}\">{source}</a> — {published}\n<b>{title}</b>\n<i>{preview}</i>\n")

    return "\n".join(lines).strip()


def send_user_report(telegram_id):
    """Invia a un utente il report delle news di oggi dalle fonti che segue.
    Ritorna il numero di notizie incluse."""
    news = get_today_news(source_ids=get_followed_source_ids(telegram_id))
    text = build_report(news)
    if text is None:
        send_long_message(NO_NEWS_MESSAGE, chat_id=telegram_id, parse_mode="HTML")
        return 0
    send_long_message(text, chat_id=telegram_id, parse_mode="HTML")
    return len(news)


def generate_report(target_chat_id=None):
    """Report giornaliero: a un singolo utente (target_chat_id) o a tutti gli attivi.
    Ogni utente riceve solo le notizie delle fonti che segue."""
    if target_chat_id:
        count = send_user_report(target_chat_id)
        log(f"📄 Report inviato manualmente a {target_chat_id} ({count} notizie).")
        return

    users = get_users()
    if not users:
        log("⚠️ Nessun utente attivo per l'invio del report.")
        return

    sent = 0
    for u in users:
        try:
            send_user_report(u["telegram_id"])
            sent += 1
        except Exception as e:
            log(f"⚠️ Errore nell'invio report a {u['telegram_id']}: {e}")
    log(f"📄 Report Telegram inviato a {sent} utenti.")
