from bot.config_loader import get_config
from bot.db import init_db
from bot.db_news import cleanup_old_news
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log, cleanup_logs
from bot.telegram_commands import start_telegram_listener, build_help_message
from bot.telegram import send_message
from bot.utils import escape_html
import schedule
import time
import traceback

# === Configurazione iniziale ===
init_db()
CONFIG = get_config()
MACHINE_NAME = CONFIG["machine_name"]
DAILY_REPORT_TIME = CONFIG["daily_report_time"]
CLEANUP_DAYS = CONFIG["data_retention_days"]
POLLING_MINUTES = CONFIG["polling_minutes"]

log(f"🔄 Servizio avviato su {MACHINE_NAME}.")

# === Scheduler ===
schedule.every(POLLING_MINUTES).minutes.do(fetch_news)
schedule.every().day.at(DAILY_REPORT_TIME).do(generate_report)
schedule.every().day.at("20:00").do(lambda: cleanup_logs(CLEANUP_DAYS))
schedule.every().day.at("20:30").do(lambda: cleanup_old_news(CLEANUP_DAYS))  # N.B. si fa riferimento alla data di fetch

# === Listener Telegram ===
start_telegram_listener()

# Recap di avvio agli utenti attivi (comandi + feed monitorati)
send_message(f"🔄 Servizio avviato su <b>{escape_html(MACHINE_NAME)}</b>.\n\n{build_help_message()}", parse_mode="HTML")

# Primo fetch subito all'avvio, senza attendere il primo intervallo
try:
    fetch_news()
except Exception as e:
    log(f"❌ Errore nel fetch iniziale: {e}\n{traceback.format_exc()}")

while True:
    try:
        schedule.run_pending()
        time.sleep(60)  # Controlla ogni minuto
    except Exception as e:
        err = traceback.format_exc()
        log(f"❌ Errore nel loop principale: {e}\n{err}")
        send_message(f"❌ Errore nel loop principale:\n<pre>{escape_html(e)}</pre>", parse_mode="HTML")
        time.sleep(10)
