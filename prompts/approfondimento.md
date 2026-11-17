# Approfondimento e materiale per il primo contatto (Fase 3)

Istruzioni per la sessione di Claude che prepara il materiale per le attività scelte da Manuel.
Si parte dalle righe della scheda Attività del foglio (`python scripts/attivita.py elenco`):
segnali, motivazione, automazioni, servizi e note sono già lì.

## Regole

- Nomi e recapiti di persone (titolari, collaboratori) solo nella scheda Contatti del foglio.
  Nei documenti su Drive e nella demo si scrive "titolare", mai il nome.
- Fonti: WebSearch, connettore Apify (`apify--web-search`, `apify--web-fetch` per i siti che da qui
  non si aprono), dati già nel foglio. Instagram, Facebook e Google Maps con le regole di `CLAUDE.md`.
- Recensioni: contano soprattutto le recenti; se due dicono il contrario, vale la più recente solo
  se tra le due c'è più di un anno, altrimenti valgono entrambe. Niente nomi degli autori.
- Il sistema non contatta nessuno: prepara il materiale, il contatto lo fa Manuel.
- Prima di creare o cambiare file Google si carica la skill `anthropic-skills:google-workspace`.

## Passi, per ogni attività

1. **Ricerca.** Sito (servizi, prezzi, come si prenota), notizie locali, recensioni recenti
   (cosa lodano, di cosa si lamentano), Instagram e altri social, da quanto tempo esiste.
   Per le società di capitali (srl, srls, spa): fatturato, utile e andamento degli ultimi anni dai
   bilanci depositati (companyreports.it, Registro Imprese e simili). Per ditte individuali, snc e
   sas il bilancio non è pubblico: scriverlo. Il bilancio non entra nel punteggio.
2. **Contatti.** Nome e ruolo del titolare o del referente, se pubblici, nella scheda Contatti:
   `place_id`, `attivita`, `referente`, `ruolo`, `telefono` (quello dell'attività),
   `canale` (visita, telefono), `stato` "da contattare", `materiale` (link alla cartella Drive).
3. **Cartella su Drive:** `Consulenza PMI/Fase 3/<nome dell'attività>`, con tre Google Docs.
   - **Approfondimento:** cosa fa e per chi, punti forti, cosa manca, dati utili (bilancio o "non
     pubblico", anni di attività, numero di recensioni e valutazione), fonti con i link.
   - **Scheda di una pagina:** cosa si è notato (dai segnali, in parole semplici), 1-3 automazioni
     con il tempo risparmiato stimato a settimana (dire come è stimato), servizi proponibili (colonna
     `servizi`), prezzi di lancio del piano (`docs/piano-consulenza-pmi.md`, "Materiale per il primo
     contatto"), ognuno come "da X €", e sotto la frase: "I prezzi sono di partenza: dopo l'analisi
     gratuita ricevi un preventivo a prezzo fisso, che non cambia in corso d'opera." (la X non va mai
     lasciata nel testo).
   - **Cosa dire:** apertura per telefono e per visita, in poche frasi, partendo da una cosa vera
     notata sull'attività; risposte brevi alle 4-5 obiezioni più probabili del settore (costo, tempo,
     "ho già Instagram", "i clienti mi chiamano già", "ci penso").
4. **Demo.** Copia di `demo/demo.html` con il blocco `CONFIG` compilato per l'attività: nome,
   settore, servizi e prezzi indicativi presi dal sito o dal listino, automazioni proposte. Nessun
   nome di persona. La scritta "Esempio preparato per <attività>, non è il loro sito" resta visibile.
   Controllo con Playwright (390 px e 1280 px, nessun errore in console), poi il file HTML va nella
   cartella Drive. La demo non si pubblica online: porta nome e marchio di un'attività reale.
5. **Nota nel foglio.** `python scripts/attivita.py nota PLACE_ID "Fase 3: materiale pronto, <link>"`.

La prima attività si mostra a Manuel prima di preparare le altre.
