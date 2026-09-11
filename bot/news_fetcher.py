import feedparser
from datetime import datetime, timezone
from bot.config_loader import get_config
from bot.db_news import add_news
from bot.logger import log
from bot.telegram import send_message
from bot.db_user import get_users
from bot.utils import cleanHTMLPreview, escape_html, find_matching_keywords, strip_html

CONFIG = get_config()
SITES = CONFIG["sites"]


def extract_entry(entry):
    """Estrae (title, link, published, text_content) da una entry feedparser.
    Ritorna None se manca il link (non è possibile deduplicare)."""
    link = (entry.get("link") or "").strip()
    if not link:
        return None
    title = (entry.get("title") or "").strip() or "(senza titolo)"
    published = entry.get("published") or entry.get("updated") or datetime.now(timezone.utc).isoformat()

    content_list = entry.get("content") or []
    content_val = content_list[0].get("value", "") if content_list else ""
    text_content = content_val or entry.get("description", "") or entry.get("summary", "") or ""
    return title, link, published, text_content


def notify_users(users, title, link, source, text_content):
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
            f"🚨 <a href=\"{escape_html(link)}\">{escape_html(source)}</a>\n<b>{escape_html(title)}</b>\n<i>{preview}</i>",
            parse_mode="HTML",
            chat_id=user["telegram_id"],
        )
        notified += 1
    return notified


def fetch_news():
    """Scarica tutti i feed, salva le news nuove e notifica gli utenti. Ritorna il numero di news nuove."""
    new_entries = []
    users = get_users()

    for site in SITES:
        source = site.get("name") or site.get("url")
        try:
            parsed = feedparser.parse(site["url"])
        except Exception as e:
            log(f"❌ Errore lettura feed {source}: {e}")
            continue

        if getattr(parsed, "bozo", False) and not parsed.entries:
            log(f"⚠️ Feed non valido o irraggiungibile: {source} ({getattr(parsed, 'bozo_exception', '')})")
            continue

        for entry in parsed.entries:
            extracted = extract_entry(entry)
            if extracted is None:
                log(f"⚠️ Entry senza link ignorata su {source}")
                continue
            title, link, published, text_content = extracted

            # Salva tutto nel DB e controlla se è nuova
            is_new = add_news(title, link, source, published, text_content)
            if not is_new:
                continue  # news già presente → niente notifica

            new_entries.append(link)

            try:
                notify_users(users, title, link, source, text_content)
            except Exception as e:
                log(f"❌ Errore notifica per '{title}': {e}")

    if new_entries:
        log(f"➕ Aggiunte {len(new_entries)} nuove notizie da {len(SITES)} feed.")
    return len(new_entries)
