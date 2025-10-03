import json
import os
from datetime import datetime, timedelta

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
        # file malformato
        return []

def save_news(news):
    """Salva le news nel file JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

def cleanup_news(retention_days: int):
    """Rimuove le notizie più vecchie di retention_days."""
    news = load_news()
    cutoff = datetime.now() - timedelta(days=retention_days)
    filtered_news = []

    for n in news:
        pub_date_str = n.get("published")
        try:
            pub_date = datetime.fromisoformat(pub_date_str)
        except Exception:
            # se il formato non è valido, consideriamo la news vecchia e la scartiamo
            continue

        if pub_date >= cutoff:
            filtered_news.append(n)

    if len(filtered_news) != len(news):
        save_news(filtered_news)
