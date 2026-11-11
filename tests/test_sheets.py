import json
from urllib.parse import quote

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google.auth.transport.requests import AuthorizedSession

from consulenza.ambiente import VariabileMancante
from consulenza.api import ErroreApi
from consulenza.sheets import (
    COLONNE_ATTIVITA,
    COLONNE_CONTATTI,
    SCHEDE,
    SCOPE,
    Foglio,
    da_ambiente,
    id_foglio,
)
from finti import FintaRisposta, FintoHttp

URL = "https://sheets.googleapis.com/v4/spreadsheets/id-foglio"
SCHEDE_PROVA = {"Attività": ["place_id", "nome", "punteggio"], "Contatti": ["place_id", "stato"]}


def url_valori(intervallo):
    return f"{URL}/values/{quote(intervallo, safe='')}"


def foglio(*risposte):
    http = FintoHttp(*risposte)
    return Foglio(http, "id-foglio", SCHEDE_PROVA), http


def meta(*titoli):
    return {"sheets": [{"properties": {"title": t}} for t in titoli]}


def test_schede_e_colonne_minime():
    assert SCHEDE == {"Attività": COLONNE_ATTIVITA, "Contatti": COLONNE_CONTATTI}
    for colonne in SCHEDE.values():
        assert len(colonne) == len(set(colonne))
        assert colonne[0] == "place_id"
    assert {"nome", "settore", "zona", "sito", "instagram", "segnali", "punteggio",
            "motivazione", "automazioni"} <= set(COLONNE_ATTIVITA)
    assert {"referente", "canale", "stato", "prossimo_passo", "data_prossimo_passo",
            "materiale"} <= set(COLONNE_CONTATTI)


def test_intervallo_con_nome_della_scheda_tra_apici_e_codificato():
    assert url_valori("'Attività'!1:1") == f"{URL}/values/%27Attivit%C3%A0%27%211%3A1"


def test_prepara_un_foglio_nuovo_crea_schede_e_intestazioni():
    lavoro, http = foglio(meta("Foglio1"), {"replies": [{}, {}]}, {}, {}, {}, {})

    lavoro.prepara()

    leggi_meta, crea, leggi_a, scrivi_a, leggi_c, scrivi_c = http.richieste
    assert (leggi_meta["metodo"], leggi_meta["url"]) == ("GET", URL)
    assert leggi_meta["params"] == {"fields": "sheets.properties.title"}
    assert (crea["metodo"], crea["url"]) == ("POST", f"{URL}:batchUpdate")
    assert crea["json"] == {
        "requests": [
            {"addSheet": {"properties": {"title": "Attività"}}},
            {"addSheet": {"properties": {"title": "Contatti"}}},
        ]
    }
    assert (leggi_a["metodo"], leggi_a["url"]) == ("GET", url_valori("'Attività'!1:1"))
    assert (scrivi_a["metodo"], scrivi_a["url"]) == ("PUT", url_valori("'Attività'!A1"))
    assert scrivi_a["params"] == {"valueInputOption": "RAW"}
    assert scrivi_a["json"] == {"values": [["place_id", "nome", "punteggio"]]}
    assert leggi_c["url"] == url_valori("'Contatti'!1:1")
    assert scrivi_c["json"] == {"values": [["place_id", "stato"]]}


def test_prepara_un_foglio_gia_pronto_non_scrive_niente():
    lavoro, http = foglio(
        meta("Attività", "Contatti"),
        {"values": [["place_id", "nome", "punteggio"]]},
        {"values": [["place_id", "stato", "colonna_di_manuel"]]},
    )

    lavoro.prepara()

    assert [r["metodo"] for r in http.richieste] == ["GET", "GET", "GET"]


def test_prepara_aggiunge_in_fondo_le_colonne_mancanti():
    lavoro, http = foglio(
        meta("Attività", "Contatti"),
        {"values": [["nome", "place_id", "colonna_di_manuel"]]},
        {},
        {"values": [["place_id", "stato"]]},
    )

    lavoro.prepara()

    scrivi = http.richieste[2]
    assert (scrivi["metodo"], scrivi["url"]) == ("PUT", url_valori("'Attività'!A1"))
    assert scrivi["json"] == {"values": [["nome", "place_id", "colonna_di_manuel", "punteggio"]]}


def test_leggi_restituisce_una_riga_per_attivita():
    lavoro, http = foglio(
        {
            "values": [
                ["place_id", "nome", "punteggio"],
                ["p1", "Officina Meccanica Esempio", 4],
                ["p2"],
                [],
                ["", "", ""],
                ["p3", "Gommista Demo", -1],
            ]
        }
    )

    righe = lavoro.leggi("Attività")

    assert righe == [
        {"place_id": "p1", "nome": "Officina Meccanica Esempio", "punteggio": 4},
        {"place_id": "p2", "nome": "", "punteggio": ""},
        {"place_id": "p3", "nome": "Gommista Demo", "punteggio": -1},
    ]
    [richiesta] = http.richieste
    assert (richiesta["metodo"], richiesta["url"]) == ("GET", url_valori("'Attività'"))
    assert richiesta["params"] == {
        "valueRenderOption": "UNFORMATTED_VALUE",
        "dateTimeRenderOption": "FORMATTED_STRING",
    }


@pytest.mark.parametrize("risposta", [{}, {"values": [["place_id", "nome"]]}])
def test_leggi_una_scheda_senza_righe(risposta):
    lavoro, _ = foglio(risposta)

    assert lavoro.leggi("Attività") == []


def test_aggiungi_segue_l_ordine_delle_colonne_del_foglio():
    lavoro, http = foglio({"values": [["nome", "place_id", "punteggio"]]}, {"updates": {}})

    lavoro.aggiungi(
        "Attività",
        [
            {"place_id": "p1", "nome": "Officina Meccanica Esempio", "punteggio": 4},
            {"place_id": "p2", "nome": "=1+1", "punteggio": None},
        ],
    )

    leggi, scrivi = http.richieste
    assert leggi["url"] == url_valori("'Attività'!1:1")
    assert (scrivi["metodo"], scrivi["url"]) == ("POST", url_valori("'Attività'!A1") + ":append")
    # RAW: il testo resta testo, anche se sembra una formula
    assert scrivi["params"] == {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
    assert scrivi["json"] == {
        "values": [["Officina Meccanica Esempio", "p1", 4], ["=1+1", "p2", ""]]
    }


def test_aggiungi_rifiuta_colonne_sconosciute():
    lavoro, http = foglio({"values": [["place_id", "nome", "punteggio"]]})

    with pytest.raises(ValueError, match="punteggo"):
        lavoro.aggiungi("Attività", [{"place_id": "p1", "punteggo": 4}])

    assert len(http.richieste) == 1


def test_aggiungi_senza_intestazioni():
    lavoro, _ = foglio({})

    with pytest.raises(ValueError, match="prepara"):
        lavoro.aggiungi("Attività", [{"place_id": "p1"}])


def test_aggiungi_niente():
    lavoro, http = foglio()

    lavoro.aggiungi("Attività", [])

    assert http.richieste == []


def test_errore_di_permesso():
    errore = {"error": {"code": 403, "message": "The caller does not have permission",
                        "status": "PERMISSION_DENIED"}}
    lavoro, _ = foglio(FintaRisposta(errore, stato=403))

    with pytest.raises(ErroreApi, match="does not have permission") as eccezione:
        lavoro.leggi("Attività")

    assert eccezione.value.stato_http == 403


@pytest.mark.parametrize(
    "valore",
    [
        "1AbC-_xyz",
        "https://docs.google.com/spreadsheets/d/1AbC-_xyz/edit#gid=0",
        "https://docs.google.com/spreadsheets/d/1AbC-_xyz/edit?usp=sharing",
        "https://docs.google.com/spreadsheets/u/0/d/1AbC-_xyz",
    ],
)
def test_id_del_foglio_anche_dal_link(valore):
    assert id_foglio(valore) == "1AbC-_xyz"


def chiave_finta(**modifiche):
    chiave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = chiave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    return {
        "type": "service_account",
        "project_id": "progetto-di-prova",
        "private_key_id": "0",
        "private_key": pem,
        "client_email": "verifica@progetto-di-prova.iam.gserviceaccount.com",
        "client_id": "0",
        "token_uri": "https://oauth2.googleapis.com/token",
        **modifiche,
    }


def test_da_ambiente_con_account_di_servizio():
    ambiente = {
        "GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps(chiave_finta()),
        "SHEET_ID": "https://docs.google.com/spreadsheets/d/1AbC-_xyz/edit",
    }

    lavoro = da_ambiente(ambiente)

    assert lavoro.sheet_id == "1AbC-_xyz"
    assert isinstance(lavoro.http, AuthorizedSession)
    assert lavoro.http.credentials.scopes == [SCOPE]


def test_da_ambiente_accetta_a_capo_veri_nella_chiave():
    # Se l'ambiente trasforma "\n" in a capo veri, il JSON deve restare leggibile.
    testo = json.dumps(chiave_finta()).replace("\\n", "\n")
    ambiente = {"GOOGLE_SERVICE_ACCOUNT_JSON": testo, "SHEET_ID": "1AbC-_xyz"}

    assert da_ambiente(ambiente).sheet_id == "1AbC-_xyz"


def test_da_ambiente_json_non_valido_non_mostra_il_contenuto():
    ambiente = {"GOOGLE_SERVICE_ACCOUNT_JSON": "contenuto-segreto{", "SHEET_ID": "1AbC-_xyz"}

    with pytest.raises(ValueError, match="GOOGLE_SERVICE_ACCOUNT_JSON") as errore:
        da_ambiente(ambiente)

    assert "contenuto-segreto" not in str(errore.value)


def test_da_ambiente_senza_variabili():
    with pytest.raises(VariabileMancante, match="GOOGLE_SERVICE_ACCOUNT_JSON"):
        da_ambiente({"SHEET_ID": "1AbC-_xyz"})
    with pytest.raises(VariabileMancante, match="SHEET_ID"):
        da_ambiente({"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps(chiave_finta())})
