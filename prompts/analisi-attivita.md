# Ricerca e analisi delle attività (Fase 2)

Istruzioni per la sessione di Claude che riempie la scheda Attività del foglio.
Comandi: `python scripts/attivita.py --help`. Punti dei segnali in `config/punteggio.yaml`.

## Regole

- Nomi e recapiti di persone (titolari, collaboratori) non vanno né nel repository né nella scheda
  Attività: se servono, vanno nella scheda Contatti, dalla Fase 3.
- Instagram: i dati del profilo si leggono solo con `attivita.py instagram` (API ufficiale).
  Il nome utente si trova sul sito dell'attività, nella scheda Maps o con una ricerca web;
  non si leggono pagine di instagram.com.
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
   Se il sito non si apre, scrivilo nelle note. Le osservazioni si salvano subito con
   `python scripts/attivita.py nota PLACE_ID "testo"`, che si aggiunge alla nota esistente.
3. **Instagram.** Trovato il nome utente: `python scripts/attivita.py instagram NOME`.
   Se l'account non è professionale, l'API non lo legge: annotalo nelle note.
   Se la ricerca web non trova il nome utente, prova i nomi più probabili (nome dell'attività
   senza spazi, con punti o trattini bassi, con la città) e accetta un account solo se nome,
   bio o sito corrispondono all'attività.
4. **Segnali** (solo quelli veri):

   | Segnale | Quando |
   | --- | --- |
   | `instagram_attivo` | Account professionale, almeno 3 post negli ultimi 90 giorni, foto o video dei propri lavori fatti con cura |
   | `nessun_sito` | Nessun sito proprio: Maps senza sito, oppure solo Facebook, Instagram, una pagina di directory o di una piattaforma di prenotazione. Conta solo con `instagram_attivo` |
   | `sito_debole` | Sito vecchio, scomodo dal telefono, oppure senza prenotazione e senza contatto rapido |
   | `indipendente` | Attività del titolare, senza insegna di catena |
   | `catena` | Franchising, catena o rete con sito e prenotazioni gestiti dalla sede centrale |
   | `prenotazione_moderna` | Prenotazione online completa (Treatwell, Fresha, sistema proprio con agenda) |
   | `nessuna_presenza` | Nessun sito e nessun social attivo |

   `molte_recensioni` non si indica: lo aggiunge il codice da 100 recensioni su Maps in su.
5. **Motivazione e automazioni.** Una frase su cosa si è notato, legata ai segnali. Poi da 1 a 3
   automazioni concrete per quell'attività, per esempio:
   - parrucchieri ed estetiste: promemoria degli appuntamenti su WhatsApp, richiamo dei clienti
     che non tornano da tempo, prenotazione online sul sito, risposte automatiche ai messaggi;
   - officine: promemoria di tagliando e revisione, avviso "auto pronta", preventivi più rapidi,
     prenotazione online;
   - per tutti: sito vetrina se manca, richiesta di recensioni dopo il servizio.
6. **Scrittura.**

   ```bash
   python scripts/attivita.py analizza PLACE_ID --instagram NOME --segnali instagram_attivo,nessun_sito,indipendente --motivazione "..." --automazione "..." --automazione "..."
   ```

   Il comando calcola il punteggio, aggiorna la riga e riordina il foglio dal punteggio più alto.
   Le colonne scritte a mano (per esempio `note`) restano; le formule nel foglio diventano valori.
