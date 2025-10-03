import json
import os

CONFIG_FILE = "config.json"

def get_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"❌ Configurazione mancante: {CONFIG_FILE}.\n"
            f"Copia 'config.example.json' in '{CONFIG_FILE}' e personalizzalo."
        )
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
