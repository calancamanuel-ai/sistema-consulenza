import pytest

from consulenza.ambiente import VariabileMancante
from consulenza.api import ErroreApi
from consulenza.pagespeed import ClientPageSpeed, ControlloSito, da_ambiente
from finti import FintaRisposta, FintoHttp, da_file


def test_richiesta_a_pagespeed():
    http = FintoHttp(da_file("pagespeed_sito.json"))

    ClientPageSpeed("chiave-finta", http).controlla("salone-esempio.example")

    [richiesta] = http.richieste
    assert richiesta["metodo"] == "GET"
    assert richiesta["url"] == "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
    assert richiesta["params"] == [
        ("url", "https://salone-esempio.example"),
        ("strategy", "mobile"),
        ("locale", "it"),
        ("category", "performance"),
        ("category", "seo"),
        ("category", "best-practices"),
    ]
    # L'analisi di Lighthouse dura anche un minuto.
    assert richiesta["timeout"] >= 90


def test_la_chiave_va_solo_nell_intestazione():
    http = FintoHttp(da_file("pagespeed_sito.json"))

    ClientPageSpeed("chiave-finta", http).controlla("https://salone-esempio.example/")

    [richiesta] = http.richieste
    assert richiesta["headers"] == {"X-Goog-Api-Key": "chiave-finta"}
    assert "chiave-finta" not in richiesta["url"] + str(richiesta["params"])


def test_indirizzo_http_resta_http():
    http = FintoHttp(da_file("pagespeed_sito.json"))

    ClientPageSpeed("k", http).controlla("http://salone-esempio.example/")

    assert ("url", "http://salone-esempio.example/") in http.richieste[0]["params"]


def test_riassunto_del_controllo():
    controllo = ClientPageSpeed("k", FintoHttp(da_file("pagespeed_sito.json"))).controlla("salone-esempio.example")

    assert controllo == ControlloSito(
        url_finale="https://www.salone-esempio.example/",
        tutto_https=True,
        prestazioni=42,
        seo=83,
        buone_pratiche=74,
        adatto_al_telefono=True,
        titolo=True,
        descrizione=False,
        cookie_terze_parti=2,
    )


def test_audit_mancanti_restano_sconosciuti():
    dati = {"lighthouseResult": {"finalDisplayedUrl": "https://x.example/", "categories": {}, "audits": {}}}

    controllo = ClientPageSpeed("k", FintoHttp(dati)).controlla("x.example")

    assert controllo.prestazioni is None
    assert controllo.tutto_https is None
    assert controllo.cookie_terze_parti is None


def test_viewport_delle_versioni_precedenti_di_lighthouse():
    dati = {"lighthouseResult": {"audits": {"viewport": {"score": 0}}}}

    assert ClientPageSpeed("k", FintoHttp(dati)).controlla("x.example").adatto_al_telefono is False


def test_sito_che_non_si_carica():
    client = ClientPageSpeed("chiave-finta", FintoHttp(FintaRisposta(da_file("pagespeed_errore.json"), stato=400)))

    with pytest.raises(ErroreApi, match="FAILED_DOCUMENT_REQUEST") as errore:
        client.controlla("salone-esempio.example")

    assert "chiave-finta" not in str(errore.value)


def test_indirizzo_vuoto():
    with pytest.raises(ValueError):
        ClientPageSpeed("k", FintoHttp()).controlla(" ")


def test_chiave_dall_ambiente():
    assert isinstance(da_ambiente({"PLACES_API_KEY": "chiave"}), ClientPageSpeed)
    with pytest.raises(VariabileMancante):
        da_ambiente({})
