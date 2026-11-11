# Sistema consulenza PMI

Trova le attività con più bisogno e più possibilità di diventare clienti e prepara il materiale
per il primo contatto. Il sistema non invia niente: il contatto lo fa Manuel.

- Piano: [docs/piano-consulenza-pmi.md](docs/piano-consulenza-pmi.md)
- Configurazione delle credenziali: [docs/SETUP.md](docs/SETUP.md)

## Struttura

| Cartella | Contenuto |
| --- | --- |
| `src/consulenza/` | Moduli: `places` (Google Maps), `instagram` (Business Discovery), `opportunita` (punteggio), `sheets` (foglio Google) |
| `config/` | `zone.yaml` (zone di ricerca), `punteggio.yaml` (pesi dei settori e punti dei segnali) |
| `data/` | `settori.csv`, classifica dei settori (nessun dato personale) |
| `prompts/` | Istruzioni per le sessioni di Claude |
| `scripts/` | `verifica.py`, controllo delle credenziali reali |
| `tests/` | Test con risposte simulate, nessuna chiamata reale |

## Comandi

```bash
pip install -r requirements.txt
```

```bash
python -m pytest
```

```bash
python scripts/verifica.py nome_utente_instagram
```
