from datetime import datetime
from bot.data_manager import load_news
from bot.logger import log
from bot.telegram import send_message
from bot.utils import cleanHTMLPreview
import os

def generate_report():
    news = load_news()
    today = datetime.now().date()
    from bot.data_manager import parse_date

    today_news = [n for n in news if parse_date(n.get("published")).date() == today]

    if not today_news:
        log("Nessuna notizia per oggi.")
        send_message("🗓️ Nessuna notizia per oggi.")
        return

    lines = [f"📢 <b>Report del {today}</b> ({len(today_news)} notizie)\n\n"]
    for n in today_news:
        preview = cleanHTMLPreview(n['content'] or n['description'])
        lines.append(f"🗞️ <a href='{n['link']}'>{n['source']}</a>\n<b>{n['title']}</b>\n<i>{preview}</i>")

    send_message("\n\n".join(lines), parse_mode="HTML")
    log(f"📄 Report Telegram inviato con {len(today_news)} notizie.")


