"""Calcola i punteggi dei settori e riscrive data/settori.csv in ordine di classifica.

Voti e prove li scrive Claude seguendo prompts/punteggio-settori.md; lo script li controlla,
calcola punteggio base e punteggio con i pesi di config/punteggio.yaml e stampa la classifica.
Se trova un errore non modifica il file.

Uso:
  python scripts/classifica_settori.py [percorso del CSV]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from consulenza.settori import carica_regole, classifica, leggi, scrivi  # noqa: E402

PREDEFINITO = Path(__file__).resolve().parents[1] / "data" / "settori.csv"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Classifica dei settori.")
    parser.add_argument("percorso", nargs="?", default=str(PREDEFINITO))
    percorso = Path(parser.parse_args(argv).percorso)
    try:
        righe = classifica(leggi(percorso), *carica_regole())
    except ValueError as errore:
        print(f"ERRORE: {errore}")
        return 1
    scrivi(percorso, righe)
    print(f"{'pos':>3}  {'punteggio':>9}  {'base':>5}  settore")
    for posizione, r in enumerate(righe, 1):
        print(f"{posizione:>3}  {r['punteggio']:>9}  {r['punteggio_base']:>5}  {r['settore']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
