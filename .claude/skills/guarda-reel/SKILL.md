---
name: guarda-reel
description: Guarda e analizza un video di Instagram (reel o post video) da un link, da un link diretto al video o da un file. Scarica il video, estrae i fotogrammi e la trascrizione, poi Claude guarda i fotogrammi e scrive un'analisi in JSON (hook, cosa si vede, cosa si dice, testi a schermo, call to action, qualità) con un riassunto in italiano. Usala quando l'utente chiede di guardare, analizzare o valutare un reel o un video di Instagram.
---

# Guarda reel

Lo script `scripts/guarda_reel.py` (in questa cartella) fa le parti meccaniche. L'analisi la fai tu
guardando i fotogrammi. Scrivi sempre in italiano.

## 1. Dipendenze

```bash
python -c "import imageio_ffmpeg, faster_whisper" || pip install imageio-ffmpeg faster-whisper
```

Al primo uso faster-whisper scarica il modello `base` (circa 150 MB) da huggingface.co.

## 2. Preparazione

```bash
python .claude/skills/guarda-reel/scripts/guarda_reel.py prepara SORGENTE [--modalita rapida|completa]
```

- `SORGENTE`: link Instagram (`/reel/`, `/p/`, `/tv/`), link diretto al video o file video.
- Con un link Instagram il video si scarica con Apify (attore `apify/instagram-scraper`): serve la
  variabile d'ambiente `APIFY_TOKEN`. Non stampare mai il token e non metterlo in URL o file.
- Se hai già il link diretto al video (per esempio `media_url` dell'API di Meta), passalo con
  `--video-url URL` insieme al link Instagram, oppure con `--codice CODICE`: Apify si salta.
  L'API di Meta spesso non dà `media_url` per i reel con musica protetta: allora serve Apify.
- `--modalita rapida` (predefinita): 6 fotogrammi a 512 px (0, 1, 2, 3 s, metà, fine).
  `--modalita completa`: fitti nei primi 3 secondi, poi uno ogni 2 secondi, al massimo 20, a 768 px.
  Usa la completa quando l'utente chiede un'analisi dettagliata o quando la rapida non basta.
- `--uscita` (predefinita `analisi`): cartella che contiene le analisi.

Il risultato è `analisi/CODICE/` con:
- `video.mp4`, salvato subito perché i link dei CDN di Instagram scadono (non c'è se la sorgente è un file);
- `frames/`, fotogrammi con il secondo nel nome (`03_t001.00s.jpg`);
- `griglia.jpg`, tutti i fotogrammi piccoli in un'immagine;
- `trascrizione.txt`, con i secondi di ogni frase, oppure "Nessun parlato rilevato." o "Nessuna traccia audio nel video.";
- `meta.json`, con durata, risoluzione, fps, lingua, elenco dei fotogrammi e, se il video viene da Apify, i dati
  del post (account, data, didascalia, like, commenti, visualizzazioni).

Se lo script si ferma con `ERRORE:`, riferisci il messaggio e non inventare il contenuto del video.

## 3. Guardare

1. Leggi `meta.json` e `trascrizione.txt`.
2. Guarda `griglia.jpg` per farti un'idea dell'insieme.
3. Guarda a grandezza piena i fotogrammi dei primi 3 secondi e tutti quelli con testo a schermo,
   persone che parlano o prodotti: dalla griglia i testi non si leggono bene.
4. Whisper può scrivere frasi inventate quando c'è solo musica: se la trascrizione non c'entra con
   quello che si vede, dillo nelle note invece di usarla.

## 4. Analisi

Scrivi `analisi/CODICE/analisi.json` con esattamente questi campi:

```json
{
  "codice": "CODICE",
  "hook": "cosa aggancia nei primi 3 secondi (immagine, testo, frase)",
  "cosa_si_vede": "scene, persone, luoghi, prodotti, montaggio",
  "cosa_si_dice": "sintesi del parlato, con i secondi dei passaggi importanti",
  "testi_a_schermo": ["ogni testo sovrimpresso, parola per parola"],
  "call_to_action": "cosa chiede di fare allo spettatore e dove (video, testo, didascalia)",
  "qualita_video": {"voto": 4, "motivo": "luce, fuoco, stabilità, inquadratura, montaggio"},
  "note": "altro di utile, anche vuoto",
  "riassunto": "3-5 frasi in italiano: di cosa parla, cosa funziona, cosa manca"
}
```

- Se un dato manca, scrivi `"manca: "` e il motivo (per esempio `"manca: nessun parlato"`); non
  dedurre e non inventare. `testi_a_schermo` è un elenco vuoto se non ci sono testi.
- `qualita_video.voto` va da 1 (inguardabile) a 5 (livello professionale); `null` solo se dai
  fotogrammi non si può giudicare, e il motivo lo spiega.
- Descrivi le persone per ruolo (cliente, operatrice, titolare), senza nomi propri anche se compaiono.

Poi controlla i campi:

```bash
python .claude/skills/guarda-reel/scripts/guarda_reel.py verifica analisi/CODICE/analisi.json
```

Correggi finché non risponde "Analisi valida", poi riporta all'utente il riassunto e il voto.

## Regole

- La cartella `analisi/` contiene video e trascrizioni di altri: se il repository non la esclude
  già, aggiungi `analisi/` al `.gitignore` e non fare commit dei suoi file.
- Se il repository ha regole sui dati personali o su Instagram (per esempio nel `CLAUDE.md`),
  quelle valgono anche qui.

## Test

```bash
python -m pytest -q .claude/skills/guarda-reel/tests
```

Non usano la rete, ffmpeg né Whisper.
