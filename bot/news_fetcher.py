import feedparser
import re
from datetime import datetime
from bot.config_loader import get_config
from bot.db_news import add_news
from bot.logger import log
from bot.telegram import send_message
from bot.db_user import get_users
from bot.utils import cleanHTMLPreview

CONFIG = get_config()
SITES = CONFIG["sites"]

def fetch_news():
    new_entries = []

    for site in SITES:
        parsed = feedparser.parse(site["url"])
        for entry in parsed.entries:
            link = entry.link
            title = entry.title
            source = site["name"]
            published = entry.get("published", datetime.now().isoformat())
            content_val = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            description = entry.get("description", "")
            text_content = content_val or description or entry.get("summary", "")

            # Salva tutto nel DB e controlla se è nuova
            is_new = add_news(title, link, source, published, text_content)
            if not is_new:
                continue  # news già presente → niente notifica

            new_entries.append(link)

            # Notifiche utenti filtrate per keywords
            full_text = " ".join([title, text_content]).lower()
            for user in get_users():
                kws = [k.strip().lower() for k in user["keywords"] if k.strip()]
                if not kws:
                    continue

                # Ricerca esatta delle parole (word boundaries)
                matched_keywords = []
                for kw in kws:
                    # Utilizza \b per word boundaries - cerca la parola esatta
                    if re.search(r'\b' + re.escape(kw) + r'\b', full_text):
                        matched_keywords.append(kw)
                
                if matched_keywords:
                    preview = cleanHTMLPreview(text_content)
                    log(f"📨 Notifica inviata a {user['telegram_id']} per keyword: {', '.join(matched_keywords)} | Titolo: {title}")
                    send_message(
                        f"🚨 <a href='{link}'>{source}</a>\n<b>{title}</b>\n<i>{preview}</i>",
                        parse_mode="HTML",
                        chat_id=user["telegram_id"]
                    )

    if new_entries:
        log(f"➕ Aggiunte {len(new_entries)} nuove notizie da {len(SITES)} feed.")
