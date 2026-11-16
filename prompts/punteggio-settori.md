# Punteggio dei settori (Fase 1)

Istruzioni per la sessione di Claude che vota i settori e aggiorna `data/settori.csv`.
I pesi stanno in `config/punteggio.yaml`; il conto lo fa `scripts/classifica_settori.py`.

## Cosa fare

1. Scegli i settori candidati: attività locali indipendenti con molti clienti privati, dove sito,
   prenotazioni e automazioni hanno senso. Un settore per riga, con un nome che serva anche come
   parola di ricerca su Maps nella Fase 2 (per esempio "officine meccaniche", non "automotive").
2. Per ogni settore dai un voto intero da 1 a 5 a ciascun criterio, con la scala qui sotto.
3. Scrivi le prove nella colonna `prove`: una voce per criterio, nel formato
   `criterio: motivo in poche parole con il dato https://fonte | criterio: ...`.
   Ogni voce deve avere almeno un link. Lo stesso link può servire a più settori.
4. `moltiplicatore_rischio`: `normale`, oppure `dati_sensibili` per settori con dati sanitari
   o altri dati delicati (studi dentistici, fisioterapia).
5. Lascia vuoti `punteggio_base` e `punteggio`, poi esegui:

   ```bash
   python scripts/classifica_settori.py
   ```

   Lo script controlla voti e prove, calcola i punteggi e riordina il file. Se trova un errore
   non tocca il file e dice cosa correggere.

## Scala dei voti

| Criterio | 5 | 3 | 1 |
| --- | --- | --- | --- |
| `lavoro_ripetitivo` | Appuntamenti, promemoria, preventivi o risposte ogni giorno | Qualche attività ripetitiva | Lavoro quasi tutto su misura |
| `capacita_spesa` | Buoni margini, scontrino o valore del cliente alto | Margini nella media delle microimprese | Margini molto bassi, settore in crisi |
| `dimensione_mercato` | Almeno 50.000 attività in Italia | 10.000-20.000 (4: 20.000-50.000; 2: 5.000-10.000) | Meno di 5.000 |
| `potenziale_ricorrente` | Strumenti usati ogni giorno, da mantenere | Uso settimanale o stagionale | Lavoro una tantum |
| `voucher_incentivi` | Imprese iscritte al Registro delle imprese, spese tipiche ammesse senza difficoltà | Ammesse in parte (per esempio solo le forme imprenditoriali) | Escluse |
| `facilita_contatto` | Titolare presente in sede, associazioni di categoria attive | Titolare raggiungibile ma spesso fuori sede o occupato | Decisioni prese altrove (catene, sedi centrali) |
| `maturita_digitale` | Social attivi, poco altro | Strumenti di base già diffusi | Nessun interesse per il digitale, oppure già tutto automatizzato |
| `concorrenza` | Pochi fornitori che servono il settore | Qualche gestionale o piattaforma di settore | Gestionali di settore completi e molto diffusi |

## Fonti utili

- Numero di imprese artigiane per mestiere: Unioncamere-InfoCamere (Movimprese).
- Voucher: bando in corso della Camera di Commercio della zona (requisiti e spese ammesse).
  Le Camere richiedono di solito l'iscrizione al Registro delle imprese: i liberi professionisti
  senza società ne restano fuori.
- Pubblici esercizi: rapporto annuale FIPE. Studi dentistici: ANDI. Fisioterapisti: FNOFI.
- Strumenti già diffusi: pagine dei principali gestionali e piattaforme di prenotazione del settore.

Preferisci fonti ufficiali o associazioni di categoria; i blog di fornitori solo per capire quali
strumenti esistono. Se un dato manca, vota con prudenza e scrivilo nella prova.
