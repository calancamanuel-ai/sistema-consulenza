"""Parti comuni alle chiamate HTTP verso le API (Google e Meta)."""

TIMEOUT = 30  # secondi


class ErroreApi(Exception):
    """Errore restituito da un'API, con il messaggio del servizio (mai la chiave o il token)."""

    def __init__(self, servizio, stato_http, messaggio, codice=None, sottocodice=None):
        super().__init__(f"{servizio}: errore {stato_http} - {messaggio}")
        self.servizio = servizio
        self.stato_http = stato_http
        self.messaggio = messaggio
        self.codice = codice
        self.sottocodice = sottocodice


def controlla(risposta, servizio: str) -> dict:
    """Restituisce il JSON della risposta, o solleva ErroreApi se la risposta è un errore."""
    if risposta.ok:
        return risposta.json()
    try:
        errore = risposta.json().get("error", {})
    except ValueError:
        errore = {}
    if not isinstance(errore, dict):
        errore = {"message": str(errore)}
    raise ErroreApi(
        servizio,
        risposta.status_code,
        errore.get("message") or risposta.text[:300],
        errore.get("code"),
        errore.get("error_subcode"),
    )
