"""Dispatcher delle notifiche: decide su quali canali raggiungere un utente e
delega l'invio al modulo del canale. Il core (fetch/match/report) parla solo
con questo modulo, mai direttamente con Telegram o altri canali."""
from bot.channels import telegram_channel
from bot.logger import log

# Registro dei canali disponibili: nome -> modulo con send_alert / send_digest.
CHANNELS = {telegram_channel.NAME: telegram_channel}


def user_label(user):
    return user.get("telegram_id") or user.get("email") or user.get("id") or "?"


def channels_for(user):
    """Canali su cui l'utente vuole essere raggiunto. Per ora: Telegram se ha un telegram_id."""
    names = []
    if user.get("telegram_id"):
        names.append(telegram_channel.NAME)
    return names


def _dispatch(kind, user, *args):
    sent = 0
    for name in channels_for(user):
        try:
            getattr(CHANNELS[name], kind)(user, *args)
            sent += 1
        except Exception as e:
            log(f"❌ Errore {kind} via {name} a {user_label(user)}: {e}")
    return sent


def send_alert(user, news, matched_keywords):
    """Notifica immediata a un utente su tutti i suoi canali. Ritorna il numero di invii riusciti."""
    return _dispatch("send_alert", user, news, matched_keywords)


def send_digest(user, news_list):
    """Report/riepilogo a un utente su tutti i suoi canali. Ritorna il numero di invii riusciti."""
    return _dispatch("send_digest", user, news_list)
