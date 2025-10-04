import feedparser
from datetime import datetime
from bot.data_manager import load_news, save_news
from bot.logger import log
from bot.config_loader import get_config
from bot.telegram import send_message
from bot.utils import cleanHTMLPreview

CONFIG = get_config()
SITES = CONFIG["sites"]
KEYWORDS = [k.lower() for k in CONFIG.get("keywords", [])]

def fetch_news():
    stored_news = load_news()
    existing_links = {item["link"] for item in stored_news}
    new_entries = []

    for site in SITES:
        parsed = feedparser.parse(site["url"])
        for entry in parsed.entries:
            if entry.link not in existing_links:
                content_val = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
                item = {
                    "source": site["name"],
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", datetime.now().isoformat()),
                    "description": entry.get("description", ""),
                    "content": content_val
                }
                stored_news.append(item)
                new_entries.append(item)

                # Controlla keyword su tutti i campi
                full_text = " ".join([
                    entry.title,
                    entry.get("description", ""),
                    entry.get("summary", ""),
                    content_val,
                ]).lower()

                if any(kw in full_text for kw in KEYWORDS):
                    preview = cleanHTMLPreview(content_val or entry.get("description", ""))
                    send_message(
                        f"🚨 <a href='{entry.link}'>{site['name']}</a>\n<b>{entry.title}</b>\n<i>{preview}</i>",
                        parse_mode="HTML"
                    )

    if new_entries:
        save_news(stored_news)
        log(f"➕ Aggiunte {len(new_entries)} notizie nuove.")

