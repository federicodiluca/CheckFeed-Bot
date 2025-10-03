from datetime import datetime
from bot.data_manager import load_news
from bot.logger import log
from bot.telegram import send_message
import os

REPORT_DIR = "data/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def generate_report():
    news = load_news()
    today = datetime.now().date()
    today_news = [n for n in news if today.isoformat() in n.get("published", "")]

    if not today_news:
        log("Nessuna notizia per oggi.")
        return

    report_file = os.path.join(REPORT_DIR, f"report_{today}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Report del {today}\n\n")
        for n in today_news:
            f.write(f"- **{n['title']}** ({n['source']})\n")
            f.write(f"  Link: {n['link']}\n\n")

    send_message(f"📢 Report del {today} generato con {len(today_news)} notizie.")
    log(f"📄 Report creato: {report_file}")
