"""Ricerca di attività con Places API (New) di Google Maps.

Il prezzo di ogni richiesta dipende dai campi chiesti: sito, telefono, valutazione e
numero di recensioni sono campi "Enterprise" (vedi docs/SETUP.md).
"""
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import quote

import requests

from consulenza.ambiente import richiedi
from consulenza.api import TIMEOUT, controlla
from consulenza.config import Zona

URL_RICERCA = "https://places.googleapis.com/v1/places:searchText"
URL_DETTAGLI = "https://places.googleapis.com/v1/places/"
CAMPI = (
    "id",
    "displayName",
    "formattedAddress",
    "websiteUri",
    "nationalPhoneNumber",
    "rating",
    "userRatingCount",
    "businessStatus",
    "primaryType",
    "googleMapsUri",
)
MAX_PER_PAGINA = 20  # limite dell'API; in tutto restituisce al massimo 60 risultati
LINGUA = {"languageCode": "it", "regionCode": "IT"}


@dataclass(frozen=True)
class Attivita:
    place_id: str
    nome: str
    indirizzo: str
    sito: str | None
    telefono: str | None
    valutazione: float | None
    recensioni: int
    stato: str | None  # OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY
    tipo: str | None  # tipo principale di Google, per esempio car_repair
    link_maps: str | None


def _attivita(dati: dict) -> Attivita:
    return Attivita(
        place_id=dati["id"],
        nome=dati.get("displayName", {}).get("text", ""),
        indirizzo=dati.get("formattedAddress", ""),
        sito=dati.get("websiteUri"),
        telefono=dati.get("nationalPhoneNumber"),
        valutazione=dati.get("rating"),
        recensioni=dati.get("userRatingCount", 0),
        stato=dati.get("businessStatus"),
        tipo=dati.get("primaryType"),
        link_maps=dati.get("googleMapsUri"),
    )


class ClientPlaces:
    def __init__(self, chiave: str, http=None):
        self._http = http or requests.Session()
        self._chiave = chiave

    def _intestazioni(self, campi: str) -> dict:
        # La chiave va nell'intestazione, così non compare negli URL né nei messaggi di errore.
        return {"X-Goog-Api-Key": self._chiave, "X-Goog-FieldMask": campi}

    def cerca(self, settore: str, zona: Zona, massimo: int = 20) -> list[Attivita]:
        """Attività del settore nella zona, seguendo le pagine fino a `massimo` risultati."""
        campi = ",".join(f"places.{c}" for c in CAMPI) + ",nextPageToken"
        corpo = {
            "textQuery": f"{settore} a {zona.nome}",
            **LINGUA,
            "locationBias": {
                "circle": {
                    "center": {"latitude": zona.lat, "longitude": zona.lng},
                    "radius": float(zona.raggio_m),
                }
            },
        }
        risultati: list[Attivita] = []
        pagina: dict = {}
        while len(risultati) < massimo:
            pagina["pageSize"] = min(MAX_PER_PAGINA, massimo - len(risultati))
            risposta = self._http.post(
                URL_RICERCA,
                json={**corpo, **pagina},
                headers=self._intestazioni(campi),
                timeout=TIMEOUT,
            )
            dati = controlla(risposta, "Places")
            risultati += [_attivita(p) for p in dati.get("places", [])]
            if not dati.get("nextPageToken"):
                break
            pagina["pageToken"] = dati["nextPageToken"]
        return risultati[:massimo]

    def dettagli(self, place_id: str) -> Attivita:
        risposta = self._http.get(
            URL_DETTAGLI + quote(place_id, safe=""),
            params=dict(LINGUA),
            headers=self._intestazioni(",".join(CAMPI)),
            timeout=TIMEOUT,
        )
        return _attivita(controlla(risposta, "Places"))


def da_ambiente(ambiente: Mapping[str, str] | None = None) -> ClientPlaces:
    return ClientPlaces(richiedi("PLACES_API_KEY", ambiente))
