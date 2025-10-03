import os
from datetime import datetime, timedelta

LOG_DIR = "data/logs"

os.makedirs(LOG_DIR, exist_ok=True)

def log(message):
    now = datetime.now()
    log_file = os.path.join(LOG_DIR, f"{now.date()}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {message}\n")
    print(message)

def cleanup_logs(days=10):
    cutoff = datetime.now() - timedelta(days=days)
    for file in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, file)
        if os.path.isfile(path):
            file_date = file.replace(".log", "")
            try:
                if datetime.fromisoformat(file_date) < cutoff:
                    os.remove(path)
                    log(f"🗑️ Rimosso log vecchio: {file}")
            except Exception:
                continue
