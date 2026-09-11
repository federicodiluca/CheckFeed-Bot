from bot.db_news import add_news
from bot.db_sources import get_followers_map, get_sources
from bot.db_user import get_users
from bot.logger import log
from bot.source_parser import SourceError, read_source
from bot.telegram import send_message
from bot.utils import cleanHTMLPreview, escape_html, find_matching_keywords, strip_html


def notify_users(users, title, link, source_name, text_content):
    """Invia la notifica agli utenti le cui keyword compaiono nel titolo o nel contenuto.
    Ritorna il numero di utenti notificati."""
    full_text = f"{title} {strip_html(text_content)}"
    notified = 0
    for user in users:
        matched_keywords = find_matching_keywords(full_text, user["keywords"])
        if not matched_keywords:
            continue
        preview = cleanHTMLPreview(text_content)
        log(f"📨 Notifica inviata a {user['telegram_id']} per keyword: {', '.join(matched_keywords)} | Titolo: {title}")
        send_message(
            f"🚨 <a href=\"{escape_html(link)}\">{escape_html(source_name)}</a>\n<b>{escape_html(title)}</b>\n<i>{preview}</i>",
            parse_mode="HTML",
            chat_id=user["telegram_id"],
        )
        notified += 1
    return notified


def fetch_source(source, followers=None, notify=True):
    """Legge una fonte, salva le news nuove e (se notify) avvisa i follower.
    Ritorna il numero di news nuove."""
    followers = followers or []
    try:
        items = read_source(source)
    except SourceError as e:
        log(f"⚠️ Fonte non leggibile: {source['name']} ({e})")
        return 0
    except Exception as e:
        log(f"❌ Errore lettura fonte {source['name']}: {e}")
        return 0

    new_count = 0
    for item in items:
        is_new = add_news(item["title"], item["link"], source["name"], item["published"], item["content"],
                          source_id=source["id"])
        if not is_new:
            continue  # news già presente → niente notifica
        new_count += 1

        if notify and followers:
            try:
                notify_users(followers, item["title"], item["link"], source["name"], item["content"])
            except Exception as e:
                log(f"❌ Errore notifica per '{item['title']}': {e}")
    return new_count


def fetch_news():
    """Scarica tutte le fonti attive, salva le news nuove e notifica gli utenti
    che seguono ciascuna fonte. Ritorna il numero di news nuove."""
    sources = get_sources()
    followers_map = get_followers_map(get_users())

    total = 0
    for source in sources:
        total += fetch_source(source, followers=followers_map.get(source["id"], []))

    if total:
        log(f"➕ Aggiunte {total} nuove notizie da {len(sources)} fonti.")
    return total
