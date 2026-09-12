# TODO — evoluzione web + email (branch `webapp`)

Posizionamento: **aggiornamenti generali dal mondo scuola** (USR, USP, MIM, normativa, graduatorie,
trasferimenti, classi di concorso) filtrati per parole chiave e fonti scelte dall'utente.
Differenziatori: **doppio canale** (Telegram + email) e **scelta della frequenza** (digest giornaliero
di default, alert immediato opzionale).

## Step MVP

- [x] 1. Refactor core/adapter: `matching` + `notifier` + `channels/telegram_channel` (`7b9bb95`)
- [x] 2. Modello dati multi-canale/multi-frequenza + migrazioni versionate + `deliveries` (`6ef66c4`)
- [ ] 3. Canale email — backend intercambiabile: **API Resend** oppure **server SMTP** (env, mai segreti nel repo)
- [ ] 4. Digest giornaliero (batch, orario per utente) + alert istantaneo dopo ogni ciclo di fetch, dedup su `deliveries`
- [ ] 5. Isolamento fallimenti per fonte + watchdog (fonte muta da troppe ore / job fermo → avviso all'admin)
- [ ] 6. Web minimale (Flask, server-side rendering): registrazione, login, preferenze (fonti, keyword, canale, frequenza), collegamento Telegram

## Requisiti trasversali (richiesti esplicitamente)

- [ ] **SEO** — priorità altissima: SSR, `<title>`/meta description/OpenGraph, canonical, `sitemap.xml`, `robots.txt`, URL parlanti, HTML semantico, pagine pubbliche indicizzabili
- [ ] **GDPR — nessun rischio**: privacy policy e termini, consenso esplicito con timestamp e versione, **revoca dei consensi** dall'area utente, export ed eliminazione dell'account (diritto all'oblio), minimizzazione dati, registro trattamenti, provider email/hosting in UE dove possibile, niente tracker di terze parti senza consenso
- [ ] **Login Google** (OAuth 2.0 / OpenID Connect) oltre a email+password
- [ ] **Server SMTP** come alternativa all'API Resend per l'invio email
- [ ] **Tema chiaro/scuro** (rispetta `prefers-color-scheme`, toggle manuale)
- [ ] **Icona app e favicon** (set completo: favicon, apple-touch-icon, manifest)

## Dopo l'MVP

- [ ] Catalogo completo fonti italiane: tutti gli USR regionali e gli USP provinciali
- [ ] Verifica email (double opt-in) prima di attivare il canale email
- [ ] Pubblicità in pagina (solo quando ci sarà trazione)
- [ ] Deploy (Hetzner + Coolify valutato; oppure free tier Google)
- [x] Rename del repo → `school-feed-monitor` (fatto)
- [ ] Rename degli identificatori interni (`CHECKFEED_*`, `data/checkfeed.db`, container Docker, package `bot/`) — con migrazione/compatibilità per `.env` e deploy esistenti

## Fuori scope (deciso)

- Feature "interpelli" / bandi di supplenza (terreno dei competitor)
- Billing / pagamenti
