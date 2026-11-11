# Regole del progetto

- Piano in `docs/piano-consulenza-pmi.md`. Si lavora una fase alla volta; a fine fase si riporta solo:
  cosa non si è riusciti a risolvere, cosa deve fare Manuel, cosa deve verificare.
- Sistema separato da quello per i creator: nessuna dipendenza condivisa.
- Niente funzioni oltre il necessario (YAGNI). Test prima del codice. File sotto le 500 righe.
- Test con risposte simulate (`tests/finti.py`, `tests/risposte/`): nessuna chiamata reale nei test.
- Il codice fa le parti meccaniche; letture dei siti e valutazioni qualitative le fa Claude nella sessione.
- Il sistema non invia email né messaggi: prepara il materiale, il contatto lo fa Manuel.
- Nomi e recapiti di persone solo nel foglio Google, mai nel repository (neanche nei test).
- Segreti solo da variabili d'ambiente (`GOOGLE_SERVICE_ACCOUNT_JSON`, `SHEET_ID`, `PLACES_API_KEY`,
  `IG_ACCESS_TOKEN`, `IG_USER_ID`); mai stamparli, mai metterli in URL o file.
- Instagram solo con l'API ufficiale (Business Discovery), nessuna raccolta di dati fuori dall'API.
- Testi, nomi e commenti in italiano.
