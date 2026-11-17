"""Controllo tecnico di un sito con l'API ufficiale PageSpeed Insights (Lighthouse, da telefono).

Usa la stessa chiave Google di Places (`PLACES_API_KEY`): nel progetto Google va attivata anche
"PageSpeed Insights API". Il giudizio sul sito (vecchio, scomodo, senza privacy) resta a Claude:
qui si raccolgono solo i numeri.
"""
from collections.abc import Mapping
from dataclasses import dataclass

import requests

from consulenza.ambiente import richiedi
from consulenza.api import controlla

URL = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
CATEGORIE = ("performance", "seo", "best-practices")
TIMEOUT = 120  # secondi: Lighthouse carica davvero la pagina e può metterci un minuto


@dataclass(frozen=True)
class ControlloSito:
    url_finale: str | None
    tutto_https: bool | None  # falso anche se una sola risorsa della pagina passa in http
    prestazioni: int | None  # da 0 a 100, da telefono
    seo: int | None
    buone_pratiche: int | None
    adatto_al_telefono: bool | None  # meta viewport presente
    titolo: bool | None
    descrizione: bool | None  # meta description presente
    cookie_terze_parti: int | None  # quanti ne usa la pagina


def _indirizzo(testo: str) -> str:
    testo = testo.strip()
    if not testo:
        raise ValueError("Manca l'indirizzo del sito")
    return testo if testo.startswith(("http://", "https://")) else "https://" + testo


def _voto(categorie: Mapping, nome: str) -> int | None:
    punteggio = categorie.get(nome, {}).get("score")
    return None if punteggio is None else round(punteggio * 100)


def _superato(audit: Mapping, nome: str) -> bool | None:
    punteggio = audit.get(nome, {}).get("score")
    return None if punteggio is None else punteggio >= 1


def _controllo(dati: dict) -> ControlloSito:
    risultato = dati.get("lighthouseResult", {})
    categorie = risultato.get("categories", {})
    audit = risultato.get("audits", {})
    cookie = audit.get("third-party-cookies")
    return ControlloSito(
        url_finale=risultato.get("finalDisplayedUrl") or risultato.get("finalUrl"),
        tutto_https=_superato(audit, "is-on-https"),
        prestazioni=_voto(categorie, "performance"),
        seo=_voto(categorie, "seo"),
        buone_pratiche=_voto(categorie, "best-practices"),
        # Da Lighthouse 13 il controllo del viewport si chiama viewport-insight.
        adatto_al_telefono=_superato(audit, "viewport-insight" if "viewport-insight" in audit else "viewport"),
        titolo=_superato(audit, "document-title"),
        descrizione=_superato(audit, "meta-description"),
        cookie_terze_parti=None if cookie is None else len(cookie.get("details", {}).get("items", [])),
    )


class ClientPageSpeed:
    def __init__(self, chiave: str, http=None):
        self._chiave = chiave
        self._http = http or requests.Session()

    def controlla(self, sito: str) -> ControlloSito:
        parametri = [("url", _indirizzo(sito)), ("strategy", "mobile"), ("locale", "it")]
        parametri += [("category", c) for c in CATEGORIE]
        risposta = self._http.get(
            URL,
            params=parametri,
            # La chiave va nell'intestazione, così non compare negli URL né nei messaggi di errore.
            headers={"X-Goog-Api-Key": self._chiave},
            timeout=TIMEOUT,
        )
        return _controllo(controlla(risposta, "PageSpeed"))


def da_ambiente(ambiente: Mapping[str, str] | None = None) -> ClientPageSpeed:
    return ClientPageSpeed(richiedi("PLACES_API_KEY", ambiente))
