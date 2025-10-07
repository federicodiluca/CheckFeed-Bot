# 📰 Telegram News Bot

Un bot in **Python + Docker** che:

* raccoglie notizie da più siti (RSS/Feed)
* invia **alert immediati su Telegram** se trova keyword personalizzate
* genera un **report giornaliero** con le notizie del giorno
* gestisce automaticamente **log e retention**
* supporta **più utenti Telegram**, ciascuno con la propria configurazione
* memorizza le **news e i contenuti completi** su SQLite

---

## 🚀 Funzionalità principali

✅ Polling periodico dei feed (intervallo configurabile)
✅ Notifiche immediate via Telegram su keyword specifiche
✅ Report giornaliero automatico alle ore configurate
✅ Deduplica automatica delle notizie già viste
✅ Gestione log e news con cancellazione automatica dopo *N giorni*
✅ Supporto **multi–utente con SQLite**
✅ Ogni utente può personalizzare le **parole chiave** e ricevere solo ciò che gli interessa
✅ Contenuto completo delle news memorizzato nel DB

---

## ⚙️ Configurazione iniziale

### 1️⃣ Crea la tua configurazione

Copia il file di esempio:

```bash
cp config.example.json config.json
```

### 2️⃣ Modifica `config.json`

Esempio base:

```json
{
  "telegram_token": "IL_TUO_TOKEN",
  "machine_name": "Server-01",
  "sites": [
    {
      "name": "USR Emilia Romagna",
      "url": "https://www.istruzioneer.gov.it/tutte-le-notizie/feed/"
    }
  ],
  "daily_report_time": "18:00",
  "polling_minutes": 60,
  "data_retention_days": 10,
  "disable_web_page_preview": true
}
```

**Campi principali:**

* `telegram_token` → token del bot (ottenuto da [BotFather](https://core.telegram.org/bots#botfather))
* `machine_name` → nome della macchina o del container
* `sites` → elenco dei feed RSS da monitorare
* `daily_report_time` → orario (HH:MM) del report giornaliero
* `polling_minutes` → intervallo tra i controlli dei feed
* `data_retention_days` → giorni di conservazione di log e news
* `disable_web_page_preview` → nasconde le anteprime dei link (opzionale)

---

## 👥 Multi–utente con SQLite

Il bot ora salva gli utenti in **`data/checkfeed.db`**.

Ogni utente che invia `/start` viene registrato automaticamente e può:

* impostare le **proprie keyword** (`/setkeywords parola1, parola2, ...`)
* ricevere **solo le notizie rilevanti** per sé
* ricevere report e comandi personalizzati

Niente più config manuale: ogni utente Telegram ha il proprio profilo salvato in automatico.

---

## 💬 Comandi disponibili

| Comando                              | Descrizione                                      |
| ------------------------------------ | ------------------------------------------------ |
| `/start`                             | Mostra il messaggio di aiuto e registra l’utente |
| `/stop`                              | Sospende le notifiche per questo utente          |
| `/fetch`                             | Aggiorna manualmente i feed                      |
| `/report`                            | Genera e invia il report giornaliero             |
| `/latest [n]`                        | Mostra le ultime *n* notizie (default: 5)        |
| `/setkeywords parola1, parola2, ...` | Imposta le parole chiave per filtrare le notizie |
| `/help`                              | Mostra il riepilogo dei comandi disponibili      |

All’avvio, il bot invia automaticamente un messaggio di **recap con tutti i comandi e i feed monitorati**.

---

## 🐳 Esecuzione con Docker

1. Clona il repository

2. Modifica `config.json` secondo le tue esigenze

3. Avvia il container:

   ```bash
   docker-compose up -d --build
   ```

I dati persistono in `data/`, inclusi log, news e database utenti.

---

## 📊 Output di esempio

**🔔 Notifica immediata**

```
🚨 Nuova notizia da USR Emilia Romagna
Concorso docenti AM2A – graduatoria aggiornata
https://www.istruzioneer.gov.it/...
```

**🗓️ Report giornaliero**

```
📢 Report del 2025-10-05 (3 notizie)
- Titolo 1 (USR Emilia Romagna)
- Titolo 2 (Miur)
```

**🧹 Log giornalieri**

```
data/logs/2025-10-05.log
```

---

## 🔧 Manutenzione automatica

* 🧹 Pulizia log e notizie vecchie ogni giorno
* 💾 Dati persistenti in `data/`
* 🧩 Deduplica feed per evitare duplicati
* 📁 Database utenti in `data/checkfeed.db`

---

## 📜 Licenza

**MIT License** – libero utilizzo e modifica.
Creato per sviluppatori e scuole che vogliono restare aggiornati automaticamente ✨
