# Ricerca e analisi delle attività (Fase 2)

Istruzioni per la sessione di Claude che riempie la scheda Attività del foglio.
Comandi: `python scripts/attivita.py --help`. Punti dei segnali in `config/punteggio.yaml`.

## Regole

- Nomi e recapiti di persone (titolari, collaboratori) non vanno né nel repository né nella scheda
  Attività: se servono, vanno nella scheda Contatti, dalla Fase 3.
- Instagram (regole in `CLAUDE.md`): gli account business si leggono solo con
  `attivita.py instagram` (API ufficiale); Apify (connettore, o `APIFY_TOKEN`) solo per trovare il
  nome utente e per i post pubblici dell'account non business dell'attività; mai account
  personali di persone.
- Il foglio accetta circa 60 scritture al minuto: ogni `nota` e ogni `analizza` riscrive la scheda,
  quindi tra un comando e l'altro serve qualche secondo di pausa.
- Places costa a richiesta: una ricerca restituisce fino a 20 attività. Non ripetere ricerche già
  fatte (il foglio salta comunque i doppioni) e non chiedere più risultati del necessario.

## Passi

1. **Ricerca.** Per ogni settore scelto e zona:

   ```bash
   python scripts/attivita.py cerca "parrucchieri e barbieri" --ricerca parrucchiere --zona "San Giovanni in Persiceto" --massimo 10
   ```

   Termini di ricerca: `parrucchiere` (parrucchieri e barbieri), `centro estetico`
   (centri estetici), `officina meccanica` (officine meccaniche).
2. **Sito.** Se c'è, leggilo (solo in https: la rete dell'ambiente non apre gli indirizzi http): è aggiornato, si legge bene dal telefono, c'è la prenotazione
   online, c'è un contatto rapido (WhatsApp, modulo)? Cerca anche il link a Instagram.
   Se il sito non si apre da qui (anche solo http o protetto da controlli anti-bot), leggilo con
   lo strumento `apify--web-fetch` del connettore Apify; se non si apre nemmeno così, scrivilo
   nelle note. Le osservazioni si salvano subito con
   `python scripts/attivita.py nota PLACE_ID "testo"`, che si aggiunge alla nota esistente.
3. **Instagram.** Trovato il nome utente: `python scripts/attivita.py instagram NOME`.
   Se l'account non è professionale, l'API non lo legge: annotalo nelle note.
   Se la ricerca web non trova il nome utente, cercalo con l'attore Apify
   `apify/instagram-search-scraper` (`searchType` "user", nome dell'attività e città) oppure prova
   i nomi più probabili (senza spazi, con punti o trattini bassi, con la città). Accetta un
   account solo se nome, bio o sito corrispondono all'attività.
   Se l'account dell'attività non è professionale, leggi i post pubblici con Apify
   (`apify/instagram-scraper`, `resultsType` "posts") e scrivi nelle note i numeri che servono
   (post negli ultimi 90 giorni, ultimo post); `instagram_attivo` resta riservato agli account
   letti con l'API ufficiale, come vuole il codice.
   Per giudicare se foto e video sono curati, guarda le immagini dei post (`file` e `copertina`
   dell'API ufficiale) o usa la skill `guarda-reel` su un Reel recente.
4. **Scheda Google.** Places non dice se la scheda è stata rivendicata: per tutte le attività della
   zona insieme, chiama con il connettore Apify l'attore `compass/crawler-google-places` con
   `placeIds` (gli place_id del foglio), `language` "it", `scrapePlaceDetailPage` true,
   `maxReviews` 10, `reviewsSort` "newest", `scrapeReviewsPersonalData` false e
   `callOptions.maxTotalChargeUsd` 1. Dai risultati leggi `claimThisBusiness` (true: scheda
   non rivendicata), `ownerUpdates`, `responseFromOwnerText` delle recensioni e `bookingLinks`;
   annota nelle note quello che serve. Nomi e testi delle recensioni non vanno né nel foglio né
   nel repository.
5. **Segnali** (solo quelli veri):

   | Segnale | Quando |
   | --- | --- |
   | `instagram_attivo` | Account professionale, almeno 3 post negli ultimi 90 giorni, foto o video dei propri lavori fatti con cura |
   | `nessun_sito` | Nessun sito proprio: Maps senza sito, oppure solo Facebook, Instagram, una pagina di directory o di una piattaforma di prenotazione. Conta solo con `instagram_attivo` |
   | `sito_debole` | Sito vecchio, scomodo dal telefono, oppure senza prenotazione e senza contatto rapido |
   | `indipendente` | Attività del titolare, senza insegna di catena |
   | `catena` | Franchising, catena o rete con sito e prenotazioni gestiti dalla sede centrale |
   | `prenotazione_moderna` | Prenotazione online completa (Treatwell, Fresha, sistema proprio con agenda), anche senza sito proprio. Le schede Fresha con "Call to book" non sono affiliate e non contano |
   | `nessuna_presenza` | Nessun sito e nessun social attivo |
   | `scheda_non_reclamata` | Su Maps la scheda non è stata rivendicata (`claimThisBusiness` true) |
   | `scheda_trascurata` | Scheda rivendicata, ma il titolare non ha risposto a nessuna delle ultime 10 recensioni e non pubblica aggiornamenti |

   `molte_recensioni` non si indica: lo aggiunge il codice da 100 recensioni su Maps in su.
6. **Motivazione e automazioni.** Una frase su cosa si è notato, legata ai segnali. Poi da 1 a 3
   automazioni concrete per quell'attività, per esempio:
   - parrucchieri ed estetiste: promemoria degli appuntamenti su WhatsApp, richiamo dei clienti
     che non tornano da tempo, prenotazione online sul sito, risposte automatiche ai messaggi;
   - officine: promemoria di tagliando e revisione, avviso "auto pronta", preventivi più rapidi,
     prenotazione online;
   - per tutti: sito vetrina se manca, richiesta di recensioni dopo il servizio, rivendicazione e
     configurazione della scheda Google, risposte alle recensioni.
7. **Scrittura.**

   ```bash
   python scripts/attivita.py analizza PLACE_ID --instagram NOME --segnali instagram_attivo,nessun_sito,indipendente --motivazione "..." --automazione "..." --automazione "..."
   ```

   Il comando calcola il punteggio, aggiorna la riga e riordina il foglio dal punteggio più alto.
   Le colonne scritte a mano (per esempio `note`) restano; le formule nel foglio diventano valori.
