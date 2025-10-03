import json
import os

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
