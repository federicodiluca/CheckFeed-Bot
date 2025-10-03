import feedparser
from datetime import datetime
from bot.data_manager import load_news, save_news
from bot.logger import log
from bot.config_loader import get_config
from bot.telegram import send_message

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
                item = {
                    "source": site["name"],
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", datetime.now().isoformat())
                }
                stored_news.append(item)
                new_entries.append(item)

                if any(kw in entry.title.lower() for kw in KEYWORDS):
                    send_message(f"🚨 Nuova notizia con keyword!\n{entry.title}\n\n{entry.link}")

    if new_entries:
        save_news(stored_news)
        log(f"➕ Aggiunte {len(new_entries)} notizie nuove.")
