"""Dati pubblici di un account Instagram professionale con Business Discovery (API ufficiale).

Gli account personali non si leggono: per loro `profilo` restituisce None.
"""
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

import requests

from consulenza.ambiente import richiedi
from consulenza.api import TIMEOUT, ErroreApi, controlla

VERSIONE_API = "v26.0"  # Graph API di luglio 2026
URL_BASE = f"https://graph.facebook.com/{VERSIONE_API}/"
CAMPI_PROFILO = ("username", "name", "biography", "website", "followers_count", "media_count")
# view_count esiste solo per i Reel; like_count manca se il titolare nasconde i like.
CAMPI_POST = ("timestamp", "media_type", "like_count", "comments_count", "view_count", "permalink")
ACCOUNT_NON_TROVATO = 2207013  # sottocodice: account inesistente o non professionale
_USERNAME = re.compile(r"[A-Za-z0-9._]{1,30}")


@dataclass(frozen=True)
class Post:
    data: datetime
    tipo: str  # IMAGE, VIDEO, CAROUSEL_ALBUM
    like: int | None
    commenti: int | None
    visualizzazioni: int | None
    link: str | None


@dataclass(frozen=True)
class ProfiloInstagram:
    username: str
    nome: str | None
    bio: str | None
    sito: str | None
    follower: int
    numero_post: int
    post: tuple[Post, ...]  # i più recenti per primi


def normalizza_username(testo: str) -> str:
    """Accetta "nome", "@nome" o il link al profilo; restituisce il nome utente."""
    testo = testo.strip()
    trovato = re.search(r"instagram\.com/([^/?#]+)", testo)
    if trovato:
        testo = trovato.group(1)
    testo = testo.removeprefix("@")
    if not _USERNAME.fullmatch(testo):
        raise ValueError(f"Nome utente Instagram non valido: {testo!r}")
    return testo


def _post(dati: dict) -> Post:
    return Post(
        data=datetime.strptime(dati["timestamp"], "%Y-%m-%dT%H:%M:%S%z"),
        tipo=dati.get("media_type", ""),
        like=dati.get("like_count"),
        commenti=dati.get("comments_count"),
        visualizzazioni=dati.get("view_count"),
        link=dati.get("permalink"),
    )


def _profilo(dati: dict) -> ProfiloInstagram:
    return ProfiloInstagram(
        username=dati["username"],
        nome=dati.get("name"),
        bio=dati.get("biography"),
        sito=dati.get("website"),
        follower=dati.get("followers_count", 0),
        numero_post=dati.get("media_count", 0),
        post=tuple(_post(p) for p in dati.get("media", {}).get("data", [])),
    )


class ClientInstagram:
    def __init__(self, token: str, ig_user_id: str, http=None):
        if not ig_user_id.isdigit():
            raise ValueError("IG_USER_ID deve essere l'ID numerico dell'account Instagram")
        self._token = token
        self._url = URL_BASE + ig_user_id
        self._http = http or requests.Session()

    def profilo(self, username: str, numero_post: int = 12) -> ProfiloInstagram | None:
        nome = normalizza_username(username)
        campi = (
            f"business_discovery.username({nome})"
            f"{{{','.join(CAMPI_PROFILO)},"
            f"media.limit({int(numero_post)}){{{','.join(CAMPI_POST)}}}}}"
        )
        risposta = self._http.get(
            self._url,
            params={"fields": campi},
            # Il token va nell'intestazione, così non compare negli URL né nei messaggi di errore.
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=TIMEOUT,
        )
        try:
            dati = controlla(risposta, "Instagram")
        except ErroreApi as errore:
            if errore.sottocodice == ACCOUNT_NON_TROVATO:
                return None
            raise
        return _profilo(dati["business_discovery"])


def da_ambiente(ambiente: Mapping[str, str] | None = None) -> ClientInstagram:
    return ClientInstagram(richiedi("IG_ACCESS_TOKEN", ambiente), richiedi("IG_USER_ID", ambiente))
