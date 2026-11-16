"""Punteggio e classifica dei settori (data/settori.csv).

Voti e prove li scrive Claude nella sessione (prompts/punteggio-settori.md);
qui si controllano e si fa il conto, con i pesi di config/punteggio.yaml.
"""
import csv
import re
from collections.abc import Iterable, Mapping
from pathlib import Path

from consulenza.config import CARTELLA, carica_punteggio

# Nell'ordine del piano: è anche l'ordine delle colonne di data/settori.csv.
CRITERI = (
    "lavoro_ripetitivo",
    "capacita_spesa",
    "dimensione_mercato",
    "potenziale_ricorrente",
    "voucher_incentivi",
    "facilita_contatto",
    "maturita_digitale",
    "concorrenza",
)
COLONNE = ("settore", *CRITERI, "moltiplicatore_rischio", "punteggio_base", "punteggio", "prove")
SEPARATORE_PROVE = " | "


def carica_regole(percorso: Path = CARTELLA / "punteggio.yaml") -> tuple[dict[str, int], dict[str, float]]:
    """Pesi dei criteri e moltiplicatori di rischio."""
    regole = carica_punteggio(percorso)["settori"]
    pesi = regole["pesi"]
    if list(pesi) != list(CRITERI):
        raise ValueError(f"Criteri in {percorso}: attesi {list(CRITERI)}, trovati {list(pesi)}")
    return {c: int(pesi[c]) for c in CRITERI}, {k: float(v) for k, v in regole["moltiplicatore_rischio"].items()}


def punteggio_base(voti: Mapping[str, object], pesi: Mapping[str, int]) -> float:
    """Somma di (peso × voto) ÷ 5: da 20 a 100 se i pesi sommano a 100."""
    totale = 0
    for criterio in CRITERI:
        if criterio not in voti:
            raise ValueError(f"Manca il voto per {criterio}")
        voto = voti[criterio]
        if isinstance(voto, str):
            voto = float(voto) if voto.strip() else 0
        if voto != int(voto) or not 1 <= voto <= 5:
            raise ValueError(f"Voto di {criterio} non valido ({voto}): deve essere un intero da 1 a 5")
        totale += pesi[criterio] * int(voto)
    return totale / 5


def _controlla_prove(settore: str, prove: str) -> None:
    """Ogni criterio deve avere la sua voce nelle prove, con almeno un link."""
    voci = {}
    for voce in prove.split(SEPARATORE_PROVE.strip()):
        criterio, _, testo = voce.strip().partition(":")
        voci[criterio.strip()] = testo
    for criterio in CRITERI:
        if not re.search(r"https?://", voci.get(criterio, "")):
            raise ValueError(f"{settore}: manca la prova con link per {criterio}")


def classifica(
    righe: Iterable[Mapping[str, str]], pesi: Mapping[str, int], moltiplicatori: Mapping[str, float]
) -> list[dict[str, str]]:
    """Controlla voti e prove, calcola i punteggi e ordina dal più alto."""
    risultato, visti = [], set()
    for riga in righe:
        nome = riga["settore"].strip()
        if nome in visti:
            raise ValueError(f"Settore duplicato: {nome}")
        visti.add(nome)
        rischio = riga["moltiplicatore_rischio"].strip()
        if rischio not in moltiplicatori:
            raise ValueError(f"{nome}: moltiplicatore {rischio!r} sconosciuto, validi: {list(moltiplicatori)}")
        try:
            base = punteggio_base(riga, pesi)
        except ValueError as errore:
            raise ValueError(f"{nome}: {errore}") from None
        _controlla_prove(nome, riga["prove"])
        nuova = {c: riga[c].strip() if isinstance(riga[c], str) else str(riga[c]) for c in COLONNE[:-3]}
        nuova.update(
            settore=nome,
            punteggio_base=f"{base:.1f}",
            punteggio=f"{base * moltiplicatori[rischio]:.1f}",
            prove=riga["prove"].strip(),
        )
        risultato.append({c: nuova[c] for c in COLONNE})
    return sorted(risultato, key=lambda r: (-float(r["punteggio"]), r["settore"]))


def leggi(percorso: Path) -> list[dict[str, str]]:
    with open(percorso, encoding="utf-8", newline="") as f:
        lettore = csv.DictReader(f)
        if tuple(lettore.fieldnames or ()) != COLONNE:
            raise ValueError(f"{percorso}: colonne attese {list(COLONNE)}")
        return list(lettore)


def scrivi(percorso: Path, righe: Iterable[Mapping[str, str]]) -> None:
    with open(percorso, "w", encoding="utf-8", newline="") as f:
        scrittore = csv.DictWriter(f, fieldnames=COLONNE, lineterminator="\n")
        scrittore.writeheader()
        scrittore.writerows(righe)
