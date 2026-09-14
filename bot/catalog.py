"""Catalogo delle fonti italiane (USR regionali, USP provinciali, MIM).

I dati stanno in bot/catalog/<nome>.json: una lista di voci
    {"name", "url", "type": "rss"|"html", "kind": "usr"|"usp"|"mim"|"other",
     "region": ..., "province": ..., "default_follow": bool (opzionale)}
Il catalogo viene unito alle fonti di config.json quando quest'ultimo contiene
"catalog": "italy" (le voci di config vincono sulle omonime del catalogo).
"""
import json
import os

CATALOG_DIR = os.path.join(os.path.dirname(__file__), "catalog")

REGIONS = [
    "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio", "Liguria",
    "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana",
    "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto",
]


def load_catalog(name="italy"):
    """Lista delle voci del catalogo (già normalizzate come le 'sites' di config)."""
    path = os.path.join(CATALOG_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"catalogo fonti non trovato: {path}")
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)
    out = []
    for e in entries:
        out.append({
            "name": e["name"].strip(),
            "url": e["url"].strip(),
            "type": (e.get("type") or "rss").lower(),
            "kind": (e.get("kind") or "other").lower(),
            "region": e.get("region") or None,
            "province": e.get("province") or None,
            # USR/USP sono opt-in (l'utente sceglie regione/provincia); MIM e nazionali seguiti da tutti
            "default_follow": bool(e.get("default_follow", e.get("kind") in ("mim", "other"))),
        })
    return out


def merge_sites(config_sites, catalog_entries):
    """Unisce config e catalogo per URL: le voci di config hanno la precedenza e vengono prima."""
    config_urls = {s["url"] for s in config_sites}
    return list(config_sites) + [e for e in catalog_entries if e["url"] not in config_urls]
