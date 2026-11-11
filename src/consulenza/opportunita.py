"""Punteggio di opportunità della singola attività, dai segnali trovati.

I segnali li stabilisce Claude nella sessione (lettura del sito, qualità di Instagram);
qui si fa solo il conto, con i punti di config/punteggio.yaml.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from consulenza.config import CARTELLA, carica_punteggio

# Nell'ordine del piano: è anche l'ordine con cui i segnali finiscono nel foglio.
SEGNALI = (
    "instagram_attivo",
    "nessun_sito",
    "sito_debole",
    "molte_recensioni",
    "indipendente",
    "catena",
    "prenotazione_moderna",
    "nessuna_presenza",
)

# Coppie che non possono essere vere insieme: indicano un errore nell'analisi.
INCOMPATIBILI = (
    ("indipendente", "catena"),
    ("nessun_sito", "sito_debole"),
    ("nessun_sito", "prenotazione_moderna"),
    ("nessuna_presenza", "instagram_attivo"),
    ("nessuna_presenza", "sito_debole"),
    ("nessuna_presenza", "prenotazione_moderna"),
)


@dataclass(frozen=True)
class Punteggio:
    totale: int
    segnali: tuple[str, ...]  # solo quelli che hanno contato


def carica_punti(percorso: Path = CARTELLA / "punteggio.yaml") -> dict[str, int]:
    punti = carica_punteggio(percorso)["opportunita"]["punti"]
    mancanti = [s for s in SEGNALI if s not in punti]
    extra = [s for s in punti if s not in SEGNALI]
    if mancanti or extra:
        raise ValueError(f"Segnali in {percorso}: mancano {mancanti}, sconosciuti {extra}")
    return {s: int(punti[s]) for s in SEGNALI}


def calcola(segnali: Iterable[str], punti: Mapping[str, int]) -> Punteggio:
    presenti = set(segnali)
    sconosciuti = sorted(presenti - set(SEGNALI))
    if sconosciuti:
        raise ValueError(f"Segnali sconosciuti: {sconosciuti}. Validi: {list(SEGNALI)}")
    for a, b in INCOMPATIBILI:
        if a in presenti and b in presenti:
            raise ValueError(f"Segnali incompatibili: {a} e {b}")
    # "Nessun sito" indica un bisogno chiaro solo se l'attività investe già su Instagram.
    if "instagram_attivo" not in presenti:
        presenti.discard("nessun_sito")
    contati = tuple(s for s in SEGNALI if s in presenti)
    return Punteggio(sum(punti[s] for s in contati), contati)
