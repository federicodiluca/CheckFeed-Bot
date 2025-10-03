# 📰 Telegram News Bot

Un bot in **Python + Docker** che:

* raccoglie notizie da più siti (RSS/Feed)
* invia **alert immediati** su Telegram se trova keyword configurate
* genera un **report giornaliero** con tutte le notizie del giorno
* gestisce automaticamente i **log con retention configurabile**

---

## 🚀 Funzionalità

* Polling periodico dei feed (es. ogni 60 minuti, configurabile)
* Notifica immediata su Telegram se una notizia contiene una delle keyword specificate
* Report giornaliero inviato a Telegram e salvato in `data/reports/`
* Deduplica automatica delle notizie già viste
* Log persistenti in `data/logs/` con cancellazione automatica dopo *N giorni*

---

## 📂 Struttura progetto

```
├── .gitignore
├── config.example.json
├── docker-compose.yml
├── Dockerfile
├── main.py
├── README.md
├── requirements.txt
├── bot/
|   └── ...
└── data/
    ├── .gitkeep
    ├── news.json
    ├── reports/
    └── logs/
```

---

## ⚙️ Configurazione

### 1. Crea la tua configurazione
Copia `config.example.json` in `config.json`:

```bash
cp config.example.json config.json
```

### 2. Modifica `config.json`

Inserisci i tuoi dati:

```json
{
  "telegram_token": "IL_TUO_TOKEN",
  "chat_id": "IL_TUO_CHAT_ID",
  "machine_name": "Server-01",
  "sites": [
    {
      "name": "USR Emilia Romagna",
      "url": "https://www.istruzioneer.gov.it/tutte-le-notizie/feed/"
    }
  ],
  "keywords": ["supplenze", "graduatorie", "docenti"],
  "daily_report_time": "18:00",
  "polling_minutes": 60,
  "log_retention_days": 10
}
```

* **telegram_token** → token del bot Telegram (da [BotFather](https://core.telegram.org/bots#botfather))
* **chat_id** → ID chat o canale dove inviare i messaggi
* **machine_name** → Nome della macchina che hosta il bot
* **sites** → lista di siti con feed RSS
* **keywords** → elenco di parole chiave da monitorare (alert immediato)
* **daily_report_time** → orario invio report giornaliero (HH:MM)
* **polling_minutes** → frequenza polling feed in minuti
* **log_retention_days** → giorni dopo i quali i log vengono cancellati

---

## 🐳 Esecuzione con Docker

1. Clona il repo

2. Modifica `config.json` con i tuoi parametri

3. Avvia con docker-compose

   ```bash
   docker-compose build --no-cache
   docker-compose up -d --build
   ```

---

## 📊 Output

* **Alert Telegram immediato**:

  ```
  🚨 Nuova notizia con keyword!
  Titolo notizia
  https://link-notizia
  ```
* **Report giornaliero Telegram**:

  ```
  📢 Report del 2025-10-03
  - Titolo 1 (Fonte)
  - Titolo 2 (Fonte)
  ```
* **File report** → salvato in `data/reports/report_YYYY-MM-DD.md`
* **Log giornalieri** → `data/logs/YYYY-MM-DD.log`

---

## 🔧 Manutenzione

* I log più vecchi di `log_retention_days` vengono eliminati automaticamente.
* Le notizie già viste sono salvate in `data/news.json`.
* Per azzerare la cache notizie → cancellare `data/news.json`.

---

## 📜 Licenza

MIT License – libero utilizzo e modifica.