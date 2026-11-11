"""Sostituti delle chiamate HTTP: nessuna richiesta reale parte dai test."""
import json
from pathlib import Path

RISPOSTE = Path(__file__).parent / "risposte"


def da_file(nome):
    """Legge una risposta simulata da tests/risposte/."""
    return json.loads((RISPOSTE / nome).read_text(encoding="utf-8"))


class FintaRisposta:
    def __init__(self, dati, stato=200):
        self.status_code = stato
        self._dati = dati

    @property
    def ok(self):
        return self.status_code < 400

    @property
    def text(self):
        return json.dumps(self._dati)

    def json(self):
        return self._dati


class FintoHttp:
    """Al posto di requests.Session: registra le richieste e dà le risposte preparate, in ordine."""

    def __init__(self, *risposte):
        self.risposte = [r if isinstance(r, FintaRisposta) else FintaRisposta(r) for r in risposte]
        self.richieste = []

    def _rispondi(self, metodo, url, **opzioni):
        self.richieste.append({"metodo": metodo, "url": url, **opzioni})
        if not self.risposte:
            raise AssertionError(f"Richiesta non prevista: {metodo} {url}")
        return self.risposte.pop(0)

    def get(self, url, **opzioni):
        return self._rispondi("GET", url, **opzioni)

    def post(self, url, **opzioni):
        return self._rispondi("POST", url, **opzioni)

    def put(self, url, **opzioni):
        return self._rispondi("PUT", url, **opzioni)
