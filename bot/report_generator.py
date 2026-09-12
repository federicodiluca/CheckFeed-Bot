from bot import notifier
from bot.channels.telegram_channel import NO_NEWS_MESSAGE, build_report  # noqa: F401 (compatibilità)
from bot.db_news import get_today_news
from bot.db_sources import get_followed_source_ids
from bot.db_user import get_user, get_users
from bot.logger import log


def send_user_report(user):
    """Invia a un utente il report delle news di oggi dalle fonti che segue.
    Ritorna il numero di notizie incluse."""
    news = get_today_news(source_ids=get_followed_source_ids(user.get("id")))
    notifier.send_digest(user, news)
    return len(news)


def generate_report(target_chat_id=None):
    """Report giornaliero: a un singolo utente (target_chat_id) o a tutti gli attivi.
    Ogni utente riceve solo le notizie delle fonti che segue."""
    if target_chat_id:
        user = get_user(target_chat_id) or {"id": None, "telegram_id": target_chat_id, "keywords": []}
        count = send_user_report(user)
        log(f"📄 Report inviato manualmente a {target_chat_id} ({count} notizie).")
        return

    users = get_users()
    if not users:
        log("⚠️ Nessun utente attivo per l'invio del report.")
        return

    sent = 0
    for u in users:
        try:
            send_user_report(u)
            sent += 1
        except Exception as e:
            log(f"⚠️ Errore nell'invio report a {notifier.user_label(u)}: {e}")
    log(f"📄 Report inviato a {sent} utenti.")
