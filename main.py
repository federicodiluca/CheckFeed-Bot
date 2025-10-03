from bot.config_loader import get_config
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log, cleanup_logs
from bot.telegram_commands import start_telegram_listener
from bot.telegram import send_message
import schedule
import time

CONFIG = get_config()
MACHINE_NAME = CONFIG["machine_name"]
log("🔄 Servizio avviato.")

# Scheduler
schedule.every(10).minutes.do(fetch_news)
schedule.every().day.at("08:00").do(generate_report)
schedule.every().day.at("00:10").do(lambda: cleanup_logs(days=10))

# Avvia listener Telegram per comandi attivi
start_telegram_listener()
send_message(f"🔄 Servizio avviato da {MACHINE_NAME}.")

while True:
    schedule.run_pending()
    time.sleep(60)
