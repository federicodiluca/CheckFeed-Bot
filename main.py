from bot.config_loader import get_config
from bot.data_manager import cleanup_news
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log, cleanup_logs
from bot.telegram_commands import start_telegram_listener
from bot.telegram import send_message
import schedule
import time
import traceback

CONFIG = get_config()
MACHINE_NAME = CONFIG["machine_name"]
DAILY_REPORT_TIME = CONFIG["daily_report_time"]
CLEANUP_DAYS = CONFIG["data_retention_days"]

log(f"🔄 Servizio avviato su {MACHINE_NAME}.")
send_message(f"🔄 Servizio avviato su <b>{MACHINE_NAME}</b>.", parse_mode="HTML")

# === Scheduler ===
schedule.every(CONFIG.get("polling_minutes", 10)).minutes.do(fetch_news)
schedule.every().day.at(DAILY_REPORT_TIME).do(generate_report)
schedule.every().day.at("20:00").do(lambda: cleanup_logs(CLEANUP_DAYS))
schedule.every().day.at("20:30").do(lambda: cleanup_news(CLEANUP_DAYS))

# === Avvia listener Telegram per comandi manuali ===
start_telegram_listener()

# === Loop principale ===
while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except Exception as e:
        err = traceback.format_exc()
        log(f"❌ Errore nel loop principale: {e}\n{err}")
        send_message(f"❌ Errore nel loop principale:\n<pre>{e}</pre>", parse_mode="HTML")
        time.sleep(10)

