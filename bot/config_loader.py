import json
import os

# Percorso del file di configurazione: sovrascrivibile con la variabile
# d'ambiente CHECKFEED_CONFIG (utile per test e deploy alternativi).
CONFIG_FILE = os.environ.get("CHECKFEED_CONFIG", "config.json")

REQUIRED_KEYS = ("telegram_token", "sites")

DEFAULTS = {
    "machine_name": "CheckFeed",
    "daily_report_time": "18:00",
    "polling_minutes": 10,
    "data_retention_days": 7,
    "disable_web_page_preview": True,
}

_cache = None


def load_config(path=None):
    """Legge e valida il file di configurazione, applicando i default."""
    path = path or CONFIG_FILE
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"❌ Configurazione mancante: {path}.\n"
            f"Copia 'config.example.json' in '{path}' e personalizzalo."
        )
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    missing = [k for k in REQUIRED_KEYS if not cfg.get(k)]
    if missing:
        raise ValueError(f"❌ Configurazione incompleta: campi mancanti {', '.join(missing)}")
    if not isinstance(cfg["sites"], list):
        raise ValueError("❌ Configurazione non valida: 'sites' deve essere una lista")
    for site in cfg["sites"]:
        if not isinstance(site, dict) or not site.get("url"):
            raise ValueError(f"❌ Configurazione non valida: feed senza 'url' ({site!r})")
        site.setdefault("name", site["url"])

    for key, value in DEFAULTS.items():
        cfg.setdefault(key, value)
    return cfg


def get_config():
    """Restituisce la configurazione (letta una sola volta e messa in cache)."""
    global _cache
    if _cache is None:
        _cache = load_config()
    return _cache
