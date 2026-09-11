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
✅ **Fonti per utente**: ognuno sceglie quali fonti seguire  
✅ **Fonti custom** aggiunte da Telegram (RSS o pagine HTML senza feed, es. siti MIM)

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
    },
    {
      "name": "USR Marche",
      "url": "https://www.mim.gov.it/web/miur-usr-marche/novit%C3%A0-dall-usr-marche",
      "type": "html"
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
* `sites` → fonti di base, visibili a tutti gli utenti (opzionale, altre fonti si aggiungono da Telegram). Ogni voce:
  * `name` → nome mostrato nelle notifiche e in `/sources`
  * `url` → feed RSS/Atom, oppure pagina HTML "lista notizie" se `type` è `html`
  * `type` → `rss` (default) o `html` (scraping della pagina, per i siti senza feed come quelli MIM/Liferay)
  * `default_follow` → `true` (default) seguita da tutti salvo `/unfollow`; `false` disponibile ma da attivare con `/follow`
* `daily_report_time` → orario (HH:MM) del report giornaliero
* `polling_minutes` → intervallo tra i controlli dei feed
* `data_retention_days` → giorni di conservazione di log e news
* `disable_web_page_preview` → nasconde le anteprime dei link (opzionale)

Solo `telegram_token` e `sites` sono obbligatori; gli altri campi hanno un default.

**Variabili d'ambiente (opzionali):**

* `CHECKFEED_CONFIG` → percorso del file di configurazione (default `config.json`)
* `CHECKFEED_DB_PATH` → percorso del database SQLite (default `data/checkfeed.db`)
* `CHECKFEED_LOG_DIR` → cartella dei log (default `data/logs`)

---

## 👥 Multi–utente con SQLite

Il bot ora salva gli utenti in **`data/checkfeed.db`**.

Ogni utente che invia `/start` viene registrato automaticamente e può:

* impostare le **proprie keyword** (`/setkeywords parola1, parola2, ...`)
* ricevere **solo le notizie rilevanti** per sé
* ricevere report e comandi personalizzati

Niente più config manuale: ogni utente Telegram ha il proprio profilo salvato in automatico.

### 📡 Fonti per utente

Le fonti vivono nel database (tabella `sources`); quelle di `config.json` vengono sincronizzate a ogni avvio.

* Di default ogni utente segue **tutte** le fonti di `config.json`; con `/sources` compare un pulsante per fonte: un tocco la attiva/disattiva (in alternativa `/follow n` e `/unfollow n` con il numero mostrato in elenco).
* Con `/addsource URL [nome]` un utente aggiunge una fonte nuova. Il bot verifica che sia leggibile:
  1. è un **feed RSS/Atom**? → usato direttamente;
  2. è una **pagina HTML che dichiara un feed** (`<link rel="alternate" type="application/rss+xml">`, tipico di WordPress)? → usa quel feed;
  3. altrimenti prova lo **scraping** della pagina come lista di notizie (`<article>` o titoli `h2/h3` con link, data italiana come "11 settembre 2026") — è il caso dei siti MIM/Liferay senza RSS;
  4. se non trova almeno 3 notizie, rifiuta la fonte.
* La fonte custom è seguita subito da chi l'ha aggiunta; gli altri la vedono in `/sources` e possono attivarla con `/follow`.
* Alla prima lettura le notizie già pubblicate vengono salvate **senza notifiche**, per non ricevere una raffica di alert.
* Notifiche, report giornaliero e `/latest` includono solo le fonti che l'utente segue.

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
| `/latest [n]`                               | Mostra le ultime *n* notizie (default: 5, max 50)     |
| `/sources`                                  | Elenco fonti con pulsanti ✅/❌ per attivarle/disattivarle |
| `/follow 1, 3` / `/follow all`              | Segui le fonti indicate                               |
| `/unfollow 2` / `/unfollow all`             | Smetti di seguire le fonti indicate                   |
| `/addsource URL [nome]`                     | Aggiunge una fonte (RSS o pagina notizie) con verifica |
| `/removesource n`                           | Rimuove una fonte aggiunta da te                      |
| `/commands` (o `/help`)                     | Elenco rapido di tutti i comandi disponibili          |

### 📡 **Esempio: aggiungere fonti**

```
/addsource https://fc.istruzioneer.gov.it/tutte-le-notizie/
✅ Fonte aggiunta: Ufficio VII – sede di Forlì-Cesena (n. 4)
📎 Tipo: feed RSS
🔗 https://fc.istruzioneer.gov.it/feed/
📰 Notizie trovate: 10 (salvate 10 nuove, senza notifica)

/addsource https://www.mim.gov.it/web/miur-usr-marche/novit%C3%A0-dall-usr-marche USR Marche
✅ Fonte aggiunta: USR Marche (n. 5)
📎 Tipo: pagina HTML (scraping)

/unfollow 2
✅ Non segui più: USP Rimini
```

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
`config.json` viene montato in sola lettura nel container: dopo una modifica basta `docker-compose restart`, senza rebuild.

---

## 🧪 Test

```bash
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

I test girano su un database e una configurazione temporanei e non effettuano alcuna chiamata di rete.

---

## 📊 Output di esempio

**🔔 Notifica immediata**

```
🚨 Nuova notizia da USR Emilia Romagna
Concorso docenti AM2A – graduatoria aggiornata
https://www.istruzioneer.gov.it/...
```

**💬 Esempi di comandi**

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

**🗓️ Report giornaliero**

```
📢 Report del 05/10/2025 — 3 notizie trovate

🗞️ USR Emilia Romagna — 05/10/2025 10:14
Titolo 1
Anteprima del contenuto...
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
