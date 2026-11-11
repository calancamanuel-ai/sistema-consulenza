"""Lettura e scrittura del foglio Google (schede Attività e Contatti) con un account di servizio.

Nomi e recapiti delle persone stanno solo nel foglio, mai nel repository.
"""
import json
import re
from collections.abc import Mapping
from urllib.parse import quote

from consulenza.ambiente import richiedi
from consulenza.api import TIMEOUT, controlla

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
URL = "https://sheets.googleapis.com/v4/spreadsheets/"

# Una riga per attività analizzata (Fase 2).
COLONNE_ATTIVITA = [
    "place_id",  # identificativo Google Maps, evita i doppioni
    "nome",
    "settore",
    "zona",
    "indirizzo",
    "telefono",  # numero dell'attività da Maps
    "sito",
    "link_maps",
    "valutazione",
    "recensioni",
    "stato_maps",  # OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY
    "tipo_maps",
    "instagram",  # nome utente
    "follower",
    "ultimo_post",  # data dell'ultimo post
    "segnali",  # segnali che hanno contato, separati da virgola
    "punteggio",
    "motivazione",  # una frase
    "automazioni",  # 1-3 automazioni proposte
    "data_analisi",
    "note",
]

# Una riga per persona da contattare (Fasi 3 e 4).
COLONNE_CONTATTI = [
    "place_id",  # collega il contatto all'attività
    "attivita",
    "referente",
    "ruolo",
    "telefono",
    "email",
    "linkedin",
    "canale",  # visita, telefono, LinkedIn, partner
    "stato",
    "ultimo_contatto",
    "prossimo_passo",
    "data_prossimo_passo",
    "materiale",  # link alla cartella Drive
    "note",
]

SCHEDE = {"Attività": COLONNE_ATTIVITA, "Contatti": COLONNE_CONTATTI}


def id_foglio(valore: str) -> str:
    """Accetta l'ID del foglio o il suo link completo."""
    trovato = re.search(r"/d/([A-Za-z0-9_-]+)", valore)
    return trovato.group(1) if trovato else valore.strip()


def _intervallo(scheda: str, celle: str = "") -> str:
    nome = "'" + scheda.replace("'", "''") + "'"
    return f"{nome}!{celle}" if celle else nome


class Foglio:
    def __init__(self, http, sheet_id: str, schede: Mapping[str, list[str]] = SCHEDE):
        self.http = http
        self.sheet_id = sheet_id
        self._schede = schede

    def _url_valori(self, scheda: str, celle: str = "") -> str:
        return f"{URL}{self.sheet_id}/values/{quote(_intervallo(scheda, celle), safe='')}"

    def _intestazione(self, scheda: str) -> list[str]:
        risposta = self.http.get(self._url_valori(scheda, "1:1"), timeout=TIMEOUT)
        valori = controlla(risposta, "Sheets").get("values", [])
        return [str(c) for c in valori[0]] if valori else []

    def prepara(self) -> None:
        """Crea le schede e le colonne che mancano; non tocca quelle che ci sono già."""
        risposta = self.http.get(
            URL + self.sheet_id, params={"fields": "sheets.properties.title"}, timeout=TIMEOUT
        )
        esistenti = {s["properties"]["title"] for s in controlla(risposta, "Sheets").get("sheets", [])}
        nuove = [{"addSheet": {"properties": {"title": n}}} for n in self._schede if n not in esistenti]
        if nuove:
            risposta = self.http.post(
                f"{URL}{self.sheet_id}:batchUpdate", json={"requests": nuove}, timeout=TIMEOUT
            )
            controlla(risposta, "Sheets")
        for scheda, colonne in self._schede.items():
            attuale = self._intestazione(scheda)
            mancanti = [c for c in colonne if c not in attuale]
            if mancanti:
                risposta = self.http.put(
                    self._url_valori(scheda, "A1"),
                    params={"valueInputOption": "RAW"},
                    json={"values": [attuale + mancanti]},
                    timeout=TIMEOUT,
                )
                controlla(risposta, "Sheets")

    def leggi(self, scheda: str) -> list[dict]:
        """Righe della scheda come dizionari con i nomi delle colonne; salta le righe vuote."""
        risposta = self.http.get(
            self._url_valori(scheda),
            params={"valueRenderOption": "UNFORMATTED_VALUE", "dateTimeRenderOption": "FORMATTED_STRING"},
            timeout=TIMEOUT,
        )
        valori = controlla(risposta, "Sheets").get("values", [])
        if not valori:
            return []
        intestazione = [str(c) for c in valori[0]]
        return [
            dict(zip(intestazione, riga + [""] * (len(intestazione) - len(riga))))
            for riga in valori[1:]
            if any(c != "" for c in riga)
        ]

    def aggiungi(self, scheda: str, righe: list[dict]) -> None:
        """Aggiunge righe in fondo, nell'ordine delle colonne del foglio."""
        if not righe:
            return
        intestazione = self._intestazione(scheda)
        if not intestazione:
            raise ValueError(f"La scheda {scheda} non ha intestazioni: esegui prima prepara()")
        for riga in righe:
            sconosciute = [c for c in riga if c not in intestazione]
            if sconosciute:
                raise ValueError(f"Colonne sconosciute nella scheda {scheda}: {sconosciute}")
        valori = [["" if r.get(c) is None else r[c] for c in intestazione] for r in righe]
        risposta = self.http.post(
            self._url_valori(scheda, "A1") + ":append",
            # RAW: i valori restano come sono, anche un testo che sembra una formula.
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": valori},
            timeout=TIMEOUT,
        )
        controlla(risposta, "Sheets")


def da_ambiente(
    ambiente: Mapping[str, str] | None = None, schede: Mapping[str, list[str]] = SCHEDE
) -> Foglio:
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    testo = richiedi("GOOGLE_SERVICE_ACCOUNT_JSON", ambiente)
    try:
        # strict=False: accetta anche gli a capo veri dentro la chiave privata.
        info = json.loads(testo, strict=False)
    except json.JSONDecodeError:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON non contiene un JSON valido: incolla tutto il file della chiave"
        ) from None
    credenziali = service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])
    return Foglio(AuthorizedSession(credenziali), id_foglio(richiedi("SHEET_ID", ambiente)), schede)
