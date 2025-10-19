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

✅ **Polling periodico** dei feed (intervallo configurabile)  
✅ **Notifiche immediate** via Telegram su keyword specifiche  
✅ **Report giornaliero** automatico alle ore configurate  
✅ **Deduplica automatica** delle notizie già viste  
✅ **Gestione log e news** con cancellazione automatica dopo *N giorni*  
✅ **Supporto multi–utente** con SQLite  
✅ **Ricerca keyword precisa** con word boundaries (parole esatte)  
✅ **Gestione keyword avanzata** (aggiungi/rimuovi selettivamente)  
✅ **Supporto parole composte** con spazi nelle keyword  
✅ **Controllo duplicati intelligente** (case-insensitive)  
✅ **Contenuto completo** delle news memorizzato nel DB  
✅ **Comandi interattivi** con feedback dettagliato

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

| Comando                                     | Descrizione                                           |
| ------------------------------------------- | ----------------------------------------------------- |
| `/start`                                    | Registra l'utente e mostra informazioni complete      |
| `/stop`                                     | Sospende le notifiche per questo utente               |
| `/setkeywords parola1, parola2, COMPOSTA`   | **Aggiunge** parole chiave (separate da virgole)      |
| `/removekeywords parola1, parola2, ...`     | **Rimuove** keyword specifiche dall'elenco            |
| `/keywords`                                 | Mostra le tue keyword attualmente attive              |
| `/fetch`                                    | Aggiorna manualmente i feed                           |
| `/report`                                   | Genera e invia il report giornaliero                  |
| `/latest [n]`                               | Mostra le ultime *n* notizie (default: 5)             |
| `/commands`                                 | Elenco rapido di tutti i comandi disponibili          |

### 🔍 **Ricerca keyword migliorata**
- Le keyword ora usano **ricerca esatta** delle parole
- "Rowe" **non** viene più trovato in "Crowe"  
- "Demir" **non** viene più trovato in "Ademir"
- Supporto per **parole composte** con spazi

### 🎯 **Gestione keyword intelligente**
- `/setkeywords` **aggiunge** alle keyword esistenti (non le sostituisce)
- `/removekeywords` **rimuove** solo quelle specificate  
- **Controllo duplicati** automatico (case-insensitive)
- Feedback dettagliato su operazioni eseguite

All'avvio, il bot invia automaticamente un messaggio di **recap con tutti i comandi e i feed monitorati**.

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

**� Esempi di comandi**

```
/setkeywords scuola, docenti, GRADUATORIA FINALE
✅ Keyword aggiunte: scuola, docenti, GRADUATORIA FINALE
📝 Totale keyword: 3

/removekeywords docenti
✅ Keyword rimosse: docenti  
📝 Keyword rimanenti: scuola, GRADUATORIA FINALE

/keywords
📝 Le tue keyword attive (2):
• scuola
• GRADUATORIA FINALE
```

**�🗓️ Report giornaliero**

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

---

## 💪 Contributors

<a href="https://github.com/federicodiluca/CheckFeed-Bot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=federicodiluca/CheckFeed-Bot" />
</a>
