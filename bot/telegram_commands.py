from threading import Thread
from bot.telegram import TELEGRAM_TOKEN, send_long_message, send_message
from bot.db_user import activate_user, add_user, deactivate_user, get_user, update_keywords
from bot.db_news import get_recent_news
from bot.news_fetcher import fetch_news
from bot.report_generator import generate_report
from bot.logger import log
from bot.config_loader import get_config
from bot.utils import cleanHTMLPreview, escape_html, format_local_datetime, parse_keywords
import requests
import time

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

POLL_TIMEOUT = 10                 # long polling lato Telegram (secondi)
REQUEST_TIMEOUT = POLL_TIMEOUT + 10  # timeout HTTP: deve superare il long polling
LATEST_DEFAULT = 5
LATEST_MAX = 50

USAGE_SETKEYWORDS = "❗ Usa: /setkeywords parola1, parola2, PAROLA COMPOSTA, ..."
USAGE_REMOVEKEYWORDS = "❗ Usa: /removekeywords parola1, parola2, PAROLA COMPOSTA, ..."


def build_help_message():
    cfg = get_config()
    sites = cfg.get("sites", [])
    polling = cfg.get("polling_minutes", 10)
    report_time = cfg.get("daily_report_time", "18:00")
    retention = cfg.get("data_retention_days", 7)
    feed_list = "\n".join([f"• {escape_html(s['name'])}" for s in sites]) if sites else "⚠️ Nessun feed configurato."
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
/latest [n] — mostra le ultime n notizie (default {LATEST_DEFAULT}, max {LATEST_MAX})
/commands — elenco rapido comandi

<b>Scheduler:</b>
• Fetch ogni {polling} minuti
• Report giornaliero alle {report_time}
• Retention notizie e log: {retention} giorni

<b>Feed monitorati:</b>
{feed_list}
""".strip()


COMMANDS_MESSAGE = f"""
📋 <b>Elenco comandi disponibili:</b>

/start — registra e mostra informazioni complete
/stop — sospende le notifiche
/setkeywords parola1, parola2, PAROLA COMPOSTA — aggiunge keyword (separate da virgole)
/removekeywords parola1, parola2, PAROLA COMPOSTA — rimuove keyword specifiche
/keywords — mostra le tue keyword attive
/fetch — aggiorna notizie manualmente
/report — genera report giornaliero
/latest [n] — mostra ultime n notizie (default {LATEST_DEFAULT}, max {LATEST_MAX})
/commands — mostra questo elenco

💡 <i>Usa /start per informazioni complete su feed e scheduler.</i>
""".strip()


def parse_command(text):
    """Estrae (comando, argomenti) da un messaggio.
    '/SetKeywords@MyBot a, b' -> ('setkeywords', 'a, b'). Ritorna (None, '') se non è un comando."""
    if not text:
        return None, ""
    text = text.strip()
    if not text.startswith("/"):
        return None, ""
    head, _, args = text.partition(" ")
    command = head[1:].split("@", 1)[0].lower()
    if not command:
        return None, ""
    return command, args.strip()


# === Handler dei singoli comandi ===

def cmd_start(telegram_id, args, username=None):
    added = add_user(telegram_id, username)
    if added:
        send_message("👋 Benvenuto! Imposta le tue parole chiave con /setkeywords parola1, parola2, PAROLA COMPOSTA", chat_id=telegram_id)
    else:
        activate_user(telegram_id)
        send_message("👋 Bentornato! Le notifiche sono attive. Usa /setkeywords per aggiornare.", chat_id=telegram_id)
    send_message(build_help_message(), parse_mode="HTML", chat_id=telegram_id)


def cmd_stop(telegram_id, args):
    deactivate_user(telegram_id)
    send_message("✅ Hai disattivato le notifiche. Usa /start per riattivarle.", chat_id=telegram_id)


def cmd_setkeywords(telegram_id, args):
    new_keywords = parse_keywords(args)
    if not new_keywords:
        send_message(USAGE_SETKEYWORDS, chat_id=telegram_id)
        return

    user = get_user(telegram_id)
    if user is None:
        # utente che scrive senza /start: lo registriamo al volo
        add_user(telegram_id)
        user = get_user(telegram_id)
    existing_keywords = user["keywords"]

    # Mappa case-insensitive per evitare duplicati
    keyword_map = {kw.lower(): kw for kw in existing_keywords}
    added_keywords, skipped_keywords = [], []
    for new_kw in new_keywords:
        if new_kw.lower() not in keyword_map:
            keyword_map[new_kw.lower()] = new_kw
            added_keywords.append(new_kw)
        else:
            skipped_keywords.append(new_kw)

    if not added_keywords:
        send_message(f"❌ Tutte le keyword specificate sono già presenti.\n📝 Keyword attuali: {', '.join(existing_keywords)}", chat_id=telegram_id)
        return

    final_keywords = existing_keywords + added_keywords
    update_keywords(telegram_id, final_keywords)

    message = f"✅ Keyword aggiunte: {', '.join(added_keywords)}"
    if skipped_keywords:
        message += f"\n⚠️ Già presenti: {', '.join(skipped_keywords)}"
    message += f"\n📝 Totale keyword: {len(final_keywords)}"
    send_message(message, chat_id=telegram_id)


def cmd_removekeywords(telegram_id, args):
    keywords_to_remove = [kw.lower() for kw in parse_keywords(args)]
    if not keywords_to_remove:
        send_message(USAGE_REMOVEKEYWORDS, chat_id=telegram_id)
        return

    user = get_user(telegram_id)
    if not user or not user["keywords"]:
        send_message("❌ Non hai keyword impostate. Usa /setkeywords per aggiungerne.", chat_id=telegram_id)
        return

    original_keywords = user["keywords"]
    keyword_map = {kw.lower(): kw for kw in original_keywords}

    removed, not_found = [], []
    for remove_kw in keywords_to_remove:
        if remove_kw in keyword_map:
            removed.append(keyword_map[remove_kw])
        else:
            not_found.append(remove_kw)

    if not removed:
        send_message(f"❌ Nessuna delle keyword specificate è stata trovata.\n📝 Keyword attuali: {', '.join(original_keywords)}", chat_id=telegram_id)
        return

    final_keywords = [kw for kw in original_keywords if kw not in removed]
    update_keywords(telegram_id, final_keywords)

    message = f"✅ Keyword rimosse: {', '.join(removed)}"
    if not_found:
        message += f"\n⚠️ Non trovate: {', '.join(not_found)}"
    if final_keywords:
        message += f"\n📝 Keyword rimanenti: {', '.join(final_keywords)}"
    else:
        message += "\n📝 Non hai più keyword impostate."
    send_message(message, chat_id=telegram_id)


def cmd_keywords(telegram_id, args):
    user = get_user(telegram_id)
    if not user or not user["keywords"]:
        send_message("❌ Non hai keyword impostate.\n💡 Usa /setkeywords per aggiungerne alcune!", chat_id=telegram_id)
        return
    keywords_list = user["keywords"]
    keywords_text = "\n".join([f"• {escape_html(kw)}" for kw in keywords_list])
    message = f"📝 <b>Le tue keyword attive ({len(keywords_list)}):</b>\n\n{keywords_text}\n\n💡 Usa /setkeywords per modificare o /removekeywords per rimuovere."
    send_message(message, parse_mode="HTML", chat_id=telegram_id)


def cmd_commands(telegram_id, args):
    send_message(COMMANDS_MESSAGE, parse_mode="HTML", chat_id=telegram_id)


def cmd_fetch(telegram_id, args):
    new_count = fetch_news()
    send_message(f"✅ Notizie aggiornate manualmente ({new_count} nuove).", chat_id=telegram_id)


def cmd_report(telegram_id, args):
    generate_report(target_chat_id=telegram_id)


def cmd_latest(telegram_id, args):
    n = LATEST_DEFAULT
    first = args.split()[0] if args else ""
    if first.isdigit():
        n = max(1, min(int(first), LATEST_MAX))

    rows = get_recent_news(limit=n)
    if not rows:
        send_message("⚠️ Nessuna notizia disponibile.", chat_id=telegram_id)
        return

    lines = [f"📰 <b>Ultime {len(rows)} notizie</b>:\n"]
    for r in rows:
        title = escape_html(r.get("title") or "Titolo non disponibile")
        source = escape_html(r.get("source") or "Sorgente")
        link = escape_html(r.get("link") or "")
        published = format_local_datetime(r.get("published_at"))
        preview = cleanHTMLPreview(r.get("content") or "")
        lines.append(f"<a href=\"{link}\">{source}</a> – {published}\n<b>{title}</b>\n<i>{preview}</i>\n")

    send_long_message("\n".join(lines), chat_id=telegram_id, parse_mode="HTML")


def cmd_unknown(telegram_id, args, command=None):
    send_message(f"❓ Comando /{command} non riconosciuto. Usa /commands per l'elenco.", chat_id=telegram_id)


HANDLERS = {
    "start": cmd_start,
    "stop": cmd_stop,
    "setkeywords": cmd_setkeywords,
    "removekeywords": cmd_removekeywords,
    "keywords": cmd_keywords,
    "commands": cmd_commands,
    "help": cmd_commands,
    "fetch": cmd_fetch,
    "report": cmd_report,
    "latest": cmd_latest,
}


def handle_update(update):
    """Gestisce un singolo update di Telegram. Ritorna il comando eseguito (o None)."""
    message = update.get("message") or {}
    text = message.get("text", "")
    chat = message.get("chat") or {}
    telegram_id = chat.get("id")
    if not text or telegram_id is None:
        return None

    command, args = parse_command(text)
    if command is None:
        return None

    if command == "start":
        cmd_start(telegram_id, args, username=chat.get("username") or message.get("from", {}).get("username"))
    elif command in HANDLERS:
        HANDLERS[command](telegram_id, args)
    else:
        cmd_unknown(telegram_id, args, command=command)
    return command


def handle_commands():
    offset = None
    while True:
        try:
            resp = requests.get(
                f"{API_URL}/getUpdates",
                params={"timeout": POLL_TIMEOUT, "offset": offset},
                timeout=REQUEST_TIMEOUT,
            )
            data = resp.json()
            if not data.get("ok"):
                # es. 409 se un'altra istanza del bot sta già facendo polling
                log(f"❌ getUpdates fallito: {data}")
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception as e:
                    log(f"❌ Errore gestione update {update.get('update_id')}: {e}")

        except Exception as e:
            log(f"❌ Errore comandi Telegram: {e}")
            time.sleep(5)


def start_telegram_listener():
    thread = Thread(target=handle_commands, daemon=True)
    thread.start()
    return thread
