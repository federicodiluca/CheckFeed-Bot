from threading import Thread
from bot.telegram import TELEGRAM_TOKEN, send_long_message, send_message
from bot.db_user import activate_user, add_user, deactivate_user, update_keywords
from bot.db_news import get_recent_news
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log
from bot.config_loader import get_config
from bot.utils import cleanHTMLPreview
import requests
import time

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def build_help_message():
    cfg = get_config()
    sites = cfg.get("sites", [])
    polling = cfg.get("polling_minutes", 10)
    report_time = cfg.get("daily_report_time", "18:00")
    retention = cfg.get("data_retention_days", 7)
    feed_list = "\n".join([f"• {s['name']}" for s in sites]) if sites else "⚠️ Nessun feed configurato."
    return f"""
🤖 <b>CheckFeed Bot</b> — servizio attivo.

<b>Comandi disponibili:</b>
/start — registra l'utente e mostra questo messaggio
/stop — sospende le notifiche per questo utente
/setkeywords parola1, parola2, PAROLA COMPOSTA — aggiunge parole chiave (separate da virgole)
/removekeywords parola1, parola2, PAROLA COMPOSTA — rimuove keyword specifiche
/keywords — mostra le tue keyword attive
/fetch — aggiorna manualmente le notizie
/report — genera e invia il report giornaliero
/latest [n] — mostra le ultime n notizie (default 5)
/commands — elenco rapido comandi

<b>Scheduler:</b>
• Fetch ogni {polling} minuti
• Report giornaliero alle {report_time}
• Retention notizie e log: {retention} giorni

<b>Feed monitorati:</b>
{feed_list}
"""

def handle_commands():
    offset = None
    while True:
        try:
            resp = requests.get(f"{API_URL}/getUpdates", params={"timeout": 10, "offset": offset})
            data = resp.json()

            for result in data.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                text = message.get("text", "")
                if not text:
                    continue
                text = text.strip()
                telegram_id = message["chat"]["id"]
                username = message["chat"].get("username", "")

                if text.startswith("/start"):
                    added = add_user(telegram_id, username)
                    if added:
                        send_message("👋 Benvenuto! Imposta le tue parole chiave con /setkeywords parola1, parola2, PAROLA COMPOSTA", chat_id=telegram_id)
                    else:
                        activate_user(telegram_id)
                        send_message("👋 Bentornato! Le notifiche sono attive. Usa /setkeywords per aggiornare.", chat_id=telegram_id)

                    # invia il messaggio di help completo
                    help_msg = build_help_message()
                    send_message(help_msg.strip(), parse_mode="HTML", chat_id=telegram_id)

                elif text.startswith("/stop"):
                    deactivate_user(telegram_id)
                    send_message("✅ Hai disattivato le notifiche. Usa /start per riattivarle.", chat_id=telegram_id)

                elif text.startswith("/setkeywords"):
                    # Estrai tutto dopo "/setkeywords "
                    keywords_text = text[len("/setkeywords"):].strip()
                    if not keywords_text:
                        send_message("❗ Usa: /setkeywords parola1, parola2, PAROLA COMPOSTA, ...", chat_id=telegram_id)
                        continue
                    
                    # Dividi per virgole e pulisci spazi extra
                    new_keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
                    if not new_keywords:
                        send_message("❗ Usa: /setkeywords parola1, parola2, PAROLA COMPOSTA, ...", chat_id=telegram_id)
                        continue
                    
                    # Ottieni le keyword attuali dell'utente
                    from bot.db_user import get_users
                    current_user = None
                    for user in get_users():
                        if user["telegram_id"] == telegram_id:
                            current_user = user
                            break
                    
                    # Combina keyword esistenti con quelle nuove
                    existing_keywords = []
                    if current_user and current_user["keywords"]:
                        existing_keywords = [kw.strip() for kw in current_user["keywords"] if kw.strip()]
                    
                    # Crea una mappa case-insensitive per evitare duplicati
                    keyword_map = {kw.lower(): kw for kw in existing_keywords}
                    
                    # Aggiungi le nuove keyword evitando duplicati (case-insensitive)
                    added_keywords = []
                    skipped_keywords = []
                    
                    for new_kw in new_keywords:
                        if new_kw.lower() not in keyword_map:
                            keyword_map[new_kw.lower()] = new_kw
                            added_keywords.append(new_kw)
                        else:
                            skipped_keywords.append(new_kw)
                    
                    # Lista finale delle keyword (mantenendo l'ordine: esistenti + nuove)
                    final_keywords = existing_keywords + added_keywords
                    
                    if not added_keywords:
                        send_message(f"❌ Tutte le keyword specificate sono già presenti.\n📝 Keyword attuali: {', '.join(existing_keywords)}", chat_id=telegram_id)
                        continue
                    
                    update_keywords(telegram_id, final_keywords)
                    
                    message = f"✅ Keyword aggiunte: {', '.join(added_keywords)}"
                    if skipped_keywords:
                        message += f"\n⚠️ Già presenti: {', '.join(skipped_keywords)}"
                    message += f"\n📝 Totale keyword: {len(final_keywords)}"
                    
                    send_message(message, chat_id=telegram_id)

                elif text.startswith("/removekeywords"):
                    # Estrai tutto dopo "/removekeywords "
                    keywords_text = text[len("/removekeywords"):].strip()
                    if not keywords_text:
                        send_message("❗ Usa: /removekeywords parola1, parola2, PAROLA COMPOSTA, ...", chat_id=telegram_id)
                        continue
                    
                    # Dividi per virgole e pulisci spazi extra
                    keywords_to_remove = [kw.strip().lower() for kw in keywords_text.split(",") if kw.strip()]
                    if not keywords_to_remove:
                        send_message("❗ Usa: /removekeywords parola1, parola2, PAROLA COMPOSTA, ...", chat_id=telegram_id)
                        continue
                    
                    # Ottieni le keyword attuali dell'utente
                    from bot.db_user import get_users
                    current_user = None
                    for user in get_users():
                        if user["telegram_id"] == telegram_id:
                            current_user = user
                            break
                    
                    if not current_user or not current_user["keywords"]:
                        send_message("❌ Non hai keyword impostate. Usa /setkeywords per aggiungerne.", chat_id=telegram_id)
                        continue
                    
                    # Ottieni le keyword originali (mantenendo il case)
                    original_keywords = [kw.strip() for kw in current_user["keywords"] if kw.strip()]
                    
                    # Crea una mappa case-insensitive per trovare le corrispondenze
                    keyword_map = {kw.lower(): kw for kw in original_keywords}
                    
                    # Trova le keyword da rimuovere (corrispondenze case-insensitive)
                    keywords_to_remove_original = []
                    keywords_not_found = []
                    
                    for remove_kw in keywords_to_remove:
                        if remove_kw in keyword_map:
                            keywords_to_remove_original.append(keyword_map[remove_kw])
                        else:
                            keywords_not_found.append(remove_kw)
                    
                    if not keywords_to_remove_original:
                        current_display = [keyword_map[k] for k in keyword_map.keys()]
                        send_message(f"❌ Nessuna delle keyword specificate è stata trovata.\n📝 Keyword attuali: {', '.join(current_display)}", chat_id=telegram_id)
                        continue
                    
                    # Rimuovi solo le keyword specificate
                    final_keywords = [kw for kw in original_keywords if kw not in keywords_to_remove_original]
                    
                    update_keywords(telegram_id, final_keywords)
                    
                    if final_keywords:
                        send_message(f"✅ Keyword rimosse: {', '.join(keywords_to_remove_original)}\n📝 Keyword rimanenti: {', '.join(final_keywords)}", chat_id=telegram_id)
                    else:
                        send_message(f"✅ Keyword rimosse: {', '.join(keywords_to_remove_original)}\n📝 Non hai più keyword impostate.", chat_id=telegram_id)

                elif text.startswith("/keywords"):
                    # Ottieni le keyword attuali dell'utente
                    from bot.db_user import get_users
                    current_user = None
                    for user in get_users():
                        if user["telegram_id"] == telegram_id:
                            current_user = user
                            break
                    
                    if not current_user or not current_user["keywords"]:
                        send_message("❌ Non hai keyword impostate.\n💡 Usa /setkeywords per aggiungerne alcune!", chat_id=telegram_id)
                    else:
                        keywords_list = [kw.strip() for kw in current_user["keywords"] if kw.strip()]
                        keywords_count = len(keywords_list)
                        keywords_text = "\n".join([f"• {kw}" for kw in keywords_list])
                        
                        message = f"📝 <b>Le tue keyword attive ({keywords_count}):</b>\n\n{keywords_text}\n\n💡 Usa /setkeywords per modificare o /removekeywords per rimuovere."
                        send_message(message, parse_mode="HTML", chat_id=telegram_id)

                elif text.startswith("/commands"):
                    commands_list = f"""
📋 <b>Elenco comandi disponibili:</b>

/start — registra e mostra informazioni complete
/stop — sospende le notifiche
/setkeywords parola1, parola2, PAROLA COMPOSTA — aggiunge keyword (separate da virgole)  
/removekeywords parola1, parola2, PAROLA COMPOSTA — rimuove keyword specifiche
/keywords — mostra le tue keyword attive
/fetch — aggiorna notizie manualmente
/report — genera report giornaliero
/latest [n] — mostra ultime n notizie (default 5)
/commands — mostra questo elenco

💡 <i>Usa /start per informazioni complete su feed e scheduler.</i>
"""
                    send_message(commands_list.strip(), parse_mode="HTML", chat_id=telegram_id)

                elif text.startswith("/fetch"):
                    fetch_news()
                    send_message("✅ Notizie aggiornate manualmente.", chat_id=telegram_id)

                elif text.startswith("/report"):
                    generate_report(target_chat_id=telegram_id)
                    send_message("✅ Report generato manualmente.", chat_id=telegram_id)


                elif text.startswith("/latest"):
                    handle_latest_command(telegram_id, text)

        except Exception as e:
            log(f"❌ Errore comandi Telegram: {e}")
            time.sleep(5)


def handle_latest_command(telegram_id, text):
    parts = text.split()
    n = 5
    if len(parts) > 1 and parts[1].isdigit():
        n = int(parts[1])

    rows = get_recent_news(limit=n)
    if not rows:
        send_message("⚠️ Nessuna notizia disponibile.", chat_id=telegram_id)
        return

    lines = [f"📰 <b>Ultime {len(rows)} notizie</b>:\n"]
    for r in rows:
        title = r["title"]
        source = r["source"] or "Sorgente"
        link = r["link"]
        published = r["published_at"] or ""
        preview = cleanHTMLPreview(r.get("content", "") or "")
        lines.append(f"<a href='{link}'>{source}</a> – {published[:16]}\n<b>{title}</b>\n<i>{preview}</i>\n")

    send_long_message("\n\n".join(lines), chat_id=telegram_id, parse_mode="HTML")


def start_telegram_listener():
    Thread(target=handle_commands, daemon=True).start()

def normalize_text(text):
    """Normalizza il testo sostituendo diversi tipi di apostrofi"""
    return text.replace("'", "'").replace("'", "'")
