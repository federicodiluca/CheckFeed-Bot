import json
import os
from datetime import datetime, timedelta, timezone
from bot.utils import parse_date
from bot.logger import log  # utile per tracciare cleanup o errori

DATA_FILE = "data/news.json"
os.makedirs("data", exist_ok=True)


def load_news():
    """Carica le news dal file JSON. Se il file non esiste o è malformato, ritorna una lista vuota."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # file vuoto
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        log("⚠️ File news.json malformato — ricreato da zero.")
        return []
    except Exception as e:
        log(f"❌ Errore nel caricamento delle news: {e}")
        return []


def save_news(news):
    """Salva le news nel file JSON."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(news, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"❌ Errore nel salvataggio delle news: {e}")


def cleanup_news(retention_days: int):
    """Rimuove le notizie più vecchie di retention_days"""
    news = load_news()
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    filtered_news = []

    for n in news:
        pub_date_str = n.get("published")
        pub_date = parse_date(pub_date_str)

        if pub_date >= cutoff:
            filtered_news.append(n)

    if len(filtered_news) != len(news):
        removed = len(news) - len(filtered_news)
        save_news(filtered_news)
        log(f"🧹 Rimosse {removed} notizie più vecchie di {retention_days} giorni.")
