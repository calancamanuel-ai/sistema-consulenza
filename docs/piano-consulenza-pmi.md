# Piano — Sistema per trovare e preparare i clienti della consulenza

Aggiornato: 11 novembre 2026

## Come usare questo piano

- Sistema completamente separato da quello per i creator: repository, foglio, segreti e sessioni propri. Si possono copiare moduli dal sistema creator, ma senza dipendenze condivise.
- Si lavora una fase alla volta. Durante il lavoro non raccontare i passaggi né i problemi che risolvi da solo.
- A fine fase fermati e riporta solo: cosa non sei riuscito a risolvere, cosa deve fare Manuel, cosa deve verificare.
- Le decisioni valgono solo per questo progetto. Quelle segnate **DA DECIDERE** si chiedono a Manuel quando servono.
- Segui il CLAUDE.md: niente funzioni oltre il necessario (YAGNI), test prima del codice, file sotto le 500 righe.

## Obiettivo e criterio di successo

Trovare le attività con più bisogno e più possibilità di diventare clienti, e preparare per ognuna il materiale per il primo contatto. Il contatto lo fa Manuel.

- Classifica dei settori pronta, con 3 settori scelti da Manuel.
- 50-100 attività analizzate, con punteggio di opportunità.
- 20-30 attività contattate con materiale personalizzato.
- Primi 2-3 clienti con analisi gratuita, poi preventivo.

## Impostazione

Stessa impostazione del sistema creator: codice Python con test per le parti meccaniche, Claude nelle sessioni per i ragionamenti, connettori per gli account, attività programmate una volta al giorno con notifica a Manuel.

Differenza principale: **il sistema non invia niente.** Con le PMI italiane le email a freddo in massa sono rischiose per le regole sulla privacy e funzionano poco. Il sistema prepara chi contattare, perché e con cosa; Manuel contatta di persona, al telefono, su LinkedIn o tramite i partner.

Mercato: tutta Italia. Le zone stanno in un file di configurazione. Si parte dalla zona di San Giovanni in Persiceto, Bologna e Modena perché all'inizio il contatto di persona e le prime referenze locali convertono di più; poi si allarga con telefono, LinkedIn e demo a distanza.

## Decisioni

| Decisione | Scelta |
| --- | --- |
| Repository | Nuovo e separato dal sistema creator |
| Esecuzione | Attività programmate di Claude Code in cloud, una volta al giorno |
| Linguaggio | Python |
| Dati con informazioni personali | Foglio Google proprio, schede Attività e Contatti |
| Accesso al foglio dal codice | Account di servizio Google |
| Fonti | Google Maps (API Places), Instagram (API ufficiale, Business Discovery), sito web dell'attività |
| App Meta | La stessa del sistema creator, con nome generico; segreti copiati nell'ambiente di questo repository |
| Account Google | **DA DECIDERE**: proposta un solo Workspace con il dominio della consulenza come principale e il dominio dei creator come secondario; fogli e account di servizio separati per sistema |

## Passaggi del sistema

1. Punteggio dei settori.
2. Ricerca delle attività dei settori scelti, nella zona.
3. Analisi di ogni attività e punteggio di opportunità.
4. Materiale personalizzato per il primo contatto.
5. Contatto da parte di Manuel.
6. Tracciamento, promemoria e prossimi passi.
7. Analisi gratuita, poi preventivo a prezzo fisso.

## Punteggio dei settori

Voti da 1 a 5 con le prove (link). Base = somma di (peso × voto) ÷ 5, da 20 a 100. Pesi di partenza, da ritarare dopo le prime classifiche e dopo i primi contatti.

| Criterio | Peso | Come si misura | Voto 5 | Voto 1 |
| --- | --- | --- | --- | --- |
| Lavoro ripetitivo automatizzabile | 25 | Prenotazioni, promemoria, preventivi, risposte ai clienti, documenti | Molte attività ripetitive ogni giorno | Lavoro quasi tutto su misura |
| Capacità di spesa | 15 | Margini e scontrino tipici del settore | Buoni margini, clienti di valore alto | Margini molto bassi |
| Dimensione del mercato | 15 | Numero di attività indipendenti del settore in Italia, stimato con ricerche Maps su un campione di città | Migliaia di attività | Poche centinaia |
| Potenziale ricorrente | 10 | Bisogno di assistenza mensile, hosting, aggiornamenti | Strumenti usati ogni giorno, da mantenere | Lavoro una tantum |
| Voucher e incentivi | 10 | Il settore rientra nei voucher digitali delle Camere di Commercio | Sì, tipicamente | No |
| Facilità di contatto | 10 | Titolare raggiungibile di persona o al telefono, presenza nelle associazioni di categoria | Titolare presente in sede | Decisioni prese altrove |
| Maturità digitale "giusta" | 10 | Usano già un minimo di strumenti ma senza automazioni | Social attivi, poco altro | Nessun interesse per il digitale, oppure già tutto automatizzato |
| Concorrenza | 5 | Altri fornitori che servono il settore in zona | Pochi | Settore già servito da gestionali di settore completi |

Moltiplicatore di rischio: 1,0 normale; 0,8 per settori con dati sensibili da trattare con cura (per esempio studi sanitari), dove servono più attenzione alla privacy e più tempo.

## Punteggio di opportunità della singola attività

Ogni segnale aggiunge o toglie punti; il totale ordina le attività da contattare. Punti di partenza, da ritarare.

| Segnale | Fonte | Punti |
| --- | --- | --- |
| Instagram attivo, con buon materiale e post regolari (investe nella promozione) | Instagram | +2 |
| Nessun sito, quando Instagram è attivo (bisogno chiaro di sito vetrina) | Maps, sito | +2 |
| Sito vecchio o senza prenotazione o contatto rapido | Sito | +2 |
| Molte recensioni (volume di clienti alto) | Maps | +1 |
| Attività indipendente | Maps, sito | +1 |
| Franchising o catena | Maps, sito | −3 |
| Già un sistema di prenotazione moderno e completo | Sito | −1 |
| Nessuna presenza online e nessuna attività sui social | Maps, Instagram | −1 |

Logica: i segnali sono strutturali, non basati sul tono delle recensioni. Instagram attivo dice che l'attività investe nella promozione; la mancanza del sito, solo se Instagram è attivo, dice che c'è un bisogno chiaro. Insieme fanno +4, il punteggio più alto: è il caso tipico di chi pensa che il sito sia costoso o impegnativo (per esempio un'officina con un Instagram curato e senza sito).

Ogni attività riceve anche una frase di motivazione e 1-3 automazioni proposte, legate ai segnali trovati.

## Fonti e limiti

- **API Places di Google Maps:** nome, indirizzo, sito, telefono, valutazione e numero di recensioni. È a pagamento a consumo; quota gratuita e prezzi da verificare nella fase 0.
- **Instagram (Business Discovery):** solo per account professionali. Restituisce follower, post, like, commenti, visualizzazioni, bio e sito. Le attività con account personale non si leggono.
- **Sito web:** lo legge Claude con i suoi strumenti; alcuni siti possono bloccare la lettura automatica.

## Materiale per il primo contatto

Per ogni attività scelta da Manuel:

- **Scheda di una pagina:** cosa si è notato (dai segnali), 1-3 automazioni proposte, cosa cambierebbe in tempo risparmiato.
- **Demo personalizzata:** versione della demo interattiva di Manuel con nome e settore dell'attività.
- **Cosa dire:** apertura per telefono o visita, in poche frasi, e le risposte alle obiezioni più probabili.
- **Prezzi di lancio**, sempre con la formula: "Da X €. Dopo l'analisi gratuita ricevi un preventivo a prezzo fisso, che non cambia in corso d'opera."
    - analisi iniziale gratuita;
    - primo workflow semplice da 300 €;
    - workflow medio con AI da 1.000 €;
    - sito vetrina da 600 €;
    - sito premium con 3D da 1.500 €;
    - assistenza da 30 € al mese;
    - costi ricorrenti (server, API, WhatsApp) a parte, al costo.

## Fasi

1. **Fase 0 — Preparazione e verifica.** Manuel: foglio e account di servizio, chiave API Places, app Meta e token, segreti e domini nell'ambiente cloud. Claude Code: repository, moduli, `docs/SETUP.md`, script di verifica. Fatto quando: lo script legge e scrive il foglio, una ricerca Places restituisce attività della zona e Business Discovery restituisce i dati di un account.
2. **Fase 1 — Punteggio dei settori.** Istruzioni in `prompts/`, classifica in `data/settori.csv` nel repository (nessun dato personale). Fatto quando: Manuel ha controllato la classifica e scelto 3 settori.
3. **Fase 2 — Ricerca e analisi delle attività.** Ricerca nella zona, dati da Maps, Instagram e sito, punteggio di opportunità, motivazione e automazioni proposte. Fatto quando: 30 attività nel foglio, ordinate, e Manuel ne ha controllate 5 a mano.
4. **Fase 3 — Materiale personalizzato.** Scheda, demo personalizzata e cosa dire, per le attività scelte da Manuel, salvati su Drive. Fatto quando: il materiale per 5 attività è pronto e Manuel lo approva.
5. **Fase 4 — Tracciamento e promemoria.** Stati dei contatti, prossimo passo con data, promemoria e riepilogo giornaliero. Fatto quando: il ciclo funziona su 5 contatti di prova.
6. **STOP — Contatti reali.** 20-30 attività in 3-4 settimane. Si confrontano punteggi e risultati e si ritarano i pesi.

## Modello consigliato per fase

| Fase | Modello | Sforzo |
| --- | --- | --- |
| 0 — Preparazione e verifica | Opus | Alto |
| 1 — Punteggio dei settori | Opus | Alto |
| 2 — Ricerca e analisi | Sonnet | Normale |
| 3 — Materiale personalizzato | Sonnet | Normale |
| 4 — Tracciamento | Sonnet | Normale |
| Attività programmate di ogni giorno | Sonnet | Normale |

## Domini di rete da autorizzare nell'ambiente cloud

| Dominio | A cosa serve | Fase |
| --- | --- | --- |
| places.googleapis.com | API Places di Google Maps | 0 |
| graph.facebook.com | Dati Instagram | 0 |
| oauth2.googleapis.com, sheets.googleapis.com | Foglio | 0 |
| pypi.org, files.pythonhosted.org, github.com | Pacchetti e codice | Tutte |

Siti delle attività, Gmail e Drive passano dagli strumenti e dai connettori di Claude.

## Regole e vincoli

- **Contatti:** il sistema non invia email né messaggi. Prepara il materiale; il contatto lo fa Manuel.
- **Dati personali:** nomi e recapiti di persone solo nel foglio, mai nel repository.
- **Segreti:** chiavi e token solo nei segreti dell'ambiente.
- **Instagram:** solo l'API ufficiale, nessuna raccolta di dati fuori dall'API.
