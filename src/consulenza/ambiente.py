"""Lettura dei segreti dalle variabili d'ambiente: mai da file nel repository."""
import os
from collections.abc import Mapping


class VariabileMancante(RuntimeError):
    pass


def richiedi(nome: str, ambiente: Mapping[str, str] | None = None) -> str:
    """Restituisce il valore della variabile, senza spazi ai lati; errore se manca o è vuota."""
    ambiente = os.environ if ambiente is None else ambiente
    valore = ambiente.get(nome, "").strip()
    if not valore:
        raise VariabileMancante(f"Manca la variabile d'ambiente {nome}: vedi docs/SETUP.md.")
    return valore
