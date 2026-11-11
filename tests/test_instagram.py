from datetime import datetime, timezone

import pytest

from consulenza.ambiente import VariabileMancante
from consulenza.api import ErroreApi
from consulenza.instagram import (
    ClientInstagram,
    Post,
    ProfiloInstagram,
    da_ambiente,
    normalizza_username,
)
from finti import FintaRisposta, FintoHttp, da_file

ID_UTENTE = "17841400000000000"


def client(*risposte):
    http = FintoHttp(*risposte)
    return ClientInstagram("token-finto", ID_UTENTE, http), http


def test_richiesta_business_discovery():
    instagram, http = client(da_file("instagram_profilo.json"))

    instagram.profilo("officina_esempio")

    [richiesta] = http.richieste
    assert richiesta["metodo"] == "GET"
    assert richiesta["url"] == f"https://graph.facebook.com/v26.0/{ID_UTENTE}"
    assert richiesta["params"] == {
        "fields": "business_discovery.username(officina_esempio)"
        "{username,name,biography,website,followers_count,media_count,"
        "media.limit(12){timestamp,media_type,like_count,comments_count,view_count,permalink}}"
    }
    assert richiesta["timeout"] > 0


def test_il_token_va_solo_nell_intestazione():
    instagram, http = client(da_file("instagram_profilo.json"))

    instagram.profilo("officina_esempio")

    [richiesta] = http.richieste
    assert richiesta["headers"] == {"Authorization": "Bearer token-finto"}
    assert "token-finto" not in richiesta["url"] + str(richiesta["params"])


def test_numero_di_post_richiesti():
    instagram, http = client(da_file("instagram_profilo.json"))

    instagram.profilo("officina_esempio", numero_post=30)

    assert "media.limit(30)" in http.richieste[0]["params"]["fields"]


def test_dati_del_profilo():
    instagram, _ = client(da_file("instagram_profilo.json"))

    profilo = instagram.profilo("officina_esempio")

    assert isinstance(profilo, ProfiloInstagram)
    assert profilo.username == "officina_esempio"
    assert profilo.nome == "Officina Esempio"
    assert profilo.bio == "Riparazioni e tagliandi. Scrivici in DM per un appuntamento."
    assert profilo.sito == "https://www.officina-esempio.example/"
    assert profilo.follower == 1840
    assert profilo.numero_post == 212
    assert len(profilo.post) == 3


def test_dati_dei_post_recenti():
    instagram, _ = client(da_file("instagram_profilo.json"))

    reel, foto, carosello = instagram.profilo("officina_esempio").post

    assert reel == Post(
        data=datetime(2026, 11, 8, 17, 2, 11, tzinfo=timezone.utc),
        tipo="VIDEO",
        like=85,
        commenti=6,
        visualizzazioni=2310,
        link="https://www.instagram.com/reel/ESEMPIO1/",
    )
    assert foto.visualizzazioni is None  # view_count esiste solo per i Reel
    assert carosello.like is None  # like nascosti dal titolare
    assert carosello.commenti == 0


def test_profilo_senza_post_ne_bio():
    instagram, _ = client(
        {"business_discovery": {"username": "nuovo", "followers_count": 3, "media_count": 0}}
    )

    profilo = instagram.profilo("nuovo")

    assert profilo.post == ()
    assert profilo.bio is None
    assert profilo.sito is None
    assert profilo.nome is None


def test_account_inesistente_o_non_professionale():
    instagram, _ = client(FintaRisposta(da_file("instagram_non_trovato.json"), stato=400))

    assert instagram.profilo("account_inesistente") is None


def test_token_scaduto():
    instagram, _ = client(FintaRisposta(da_file("instagram_token_scaduto.json"), stato=400))

    with pytest.raises(ErroreApi, match="Session has expired") as errore:
        instagram.profilo("officina_esempio")

    assert errore.value.codice == 190
    assert "token-finto" not in str(errore.value)


@pytest.mark.parametrize(
    "testo",
    [
        "officina_esempio",
        "@officina_esempio",
        " officina_esempio ",
        "https://www.instagram.com/officina_esempio/",
        "instagram.com/officina_esempio?igsh=abc123",
    ],
)
def test_normalizza_username(testo):
    assert normalizza_username(testo) == "officina_esempio"


@pytest.mark.parametrize("testo", ["", "officina esempio", "a){id}", "x" * 31])
def test_username_non_valido(testo):
    with pytest.raises(ValueError):
        normalizza_username(testo)


def test_username_non_valido_non_fa_richieste():
    instagram, http = client()

    with pytest.raises(ValueError):
        instagram.profilo("a){id}")

    assert http.richieste == []


def test_id_utente_deve_essere_numerico():
    with pytest.raises(ValueError, match="IG_USER_ID"):
        ClientInstagram("token-finto", "officina_esempio", FintoHttp())


def test_da_ambiente_senza_variabili():
    with pytest.raises(VariabileMancante, match="IG_ACCESS_TOKEN"):
        da_ambiente({"IG_USER_ID": ID_UTENTE})
    with pytest.raises(VariabileMancante, match="IG_USER_ID"):
        da_ambiente({"IG_ACCESS_TOKEN": "token-finto"})


def test_da_ambiente_con_variabili():
    client_ig = da_ambiente({"IG_ACCESS_TOKEN": "token-finto", "IG_USER_ID": ID_UTENTE})

    assert isinstance(client_ig, ClientInstagram)
