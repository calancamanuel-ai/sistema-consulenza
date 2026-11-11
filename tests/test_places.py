import pytest

from consulenza.ambiente import VariabileMancante
from consulenza.api import ErroreApi
from consulenza.config import Zona
from consulenza.places import Attivita, ClientPlaces, da_ambiente
from finti import FintaRisposta, FintoHttp, da_file

ZONA = Zona("San Giovanni in Persiceto", 44.6403, 11.1844, 8000)


def test_ricerca_per_settore_e_zona():
    http = FintoHttp(da_file("places_ricerca_pagina2.json"))

    ClientPlaces("chiave-finta", http).cerca("officina", ZONA, massimo=10)

    [richiesta] = http.richieste
    assert richiesta["metodo"] == "POST"
    assert richiesta["url"] == "https://places.googleapis.com/v1/places:searchText"
    assert richiesta["json"] == {
        "textQuery": "officina a San Giovanni in Persiceto",
        "languageCode": "it",
        "regionCode": "IT",
        "locationBias": {
            "circle": {"center": {"latitude": 44.6403, "longitude": 11.1844}, "radius": 8000.0}
        },
        "pageSize": 10,
    }
    assert richiesta["timeout"] > 0


def test_la_chiave_va_solo_nell_intestazione():
    http = FintoHttp(da_file("places_ricerca_pagina2.json"))

    ClientPlaces("chiave-finta", http).cerca("officina", ZONA)

    [richiesta] = http.richieste
    assert richiesta["headers"]["X-Goog-Api-Key"] == "chiave-finta"
    assert "chiave-finta" not in richiesta["url"]
    assert "params" not in richiesta


def test_maschera_dei_campi_della_ricerca():
    http = FintoHttp(da_file("places_ricerca_pagina2.json"))

    ClientPlaces("chiave-finta", http).cerca("officina", ZONA)

    campi = http.richieste[0]["headers"]["X-Goog-FieldMask"].split(",")
    assert campi == [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.websiteUri",
        "places.nationalPhoneNumber",
        "places.rating",
        "places.userRatingCount",
        "places.businessStatus",
        "places.primaryType",
        "places.googleMapsUri",
        "nextPageToken",
    ]


def test_converte_i_risultati_in_attivita():
    http = FintoHttp(da_file("places_ricerca_pagina1.json"))

    completa, senza_dati = ClientPlaces("chiave-finta", http).cerca("officina", ZONA, massimo=2)

    assert completa == Attivita(
        place_id="ChIJesempio0000001",
        nome="Officina Meccanica Esempio",
        indirizzo="Via dell'Esempio, 1, 40017 San Giovanni in Persiceto BO, Italia",
        sito="https://www.officina-esempio.example/",
        telefono="051 000 0001",
        valutazione=4.7,
        recensioni=132,
        stato="OPERATIONAL",
        tipo="car_repair",
        link_maps="https://maps.google.com/?cid=1000000000000000001",
    )
    assert senza_dati.sito is None
    assert senza_dati.telefono is None
    assert senza_dati.valutazione is None
    assert senza_dati.recensioni == 0
    assert senza_dati.stato == "CLOSED_TEMPORARILY"


def test_segue_le_pagine_fino_al_massimo():
    http = FintoHttp(da_file("places_ricerca_pagina1.json"), da_file("places_ricerca_pagina2.json"))

    attivita = ClientPlaces("chiave-finta", http).cerca("officina", ZONA, massimo=5)

    assert [a.place_id for a in attivita] == [
        "ChIJesempio0000001",
        "ChIJesempio0000002",
        "ChIJesempio0000003",
    ]
    prima, seconda = http.richieste
    assert "pageToken" not in prima["json"]
    assert seconda["json"]["pageToken"] == "token-pagina-2"
    assert seconda["json"]["pageSize"] == 3
    assert seconda["json"]["textQuery"] == prima["json"]["textQuery"]


def test_non_chiede_altre_pagine_oltre_il_massimo():
    http = FintoHttp(da_file("places_ricerca_pagina1.json"))

    attivita = ClientPlaces("chiave-finta", http).cerca("officina", ZONA, massimo=2)

    assert len(attivita) == 2
    assert len(http.richieste) == 1


def test_pagine_da_venti_risultati_al_massimo():
    http = FintoHttp(da_file("places_ricerca_pagina2.json"))

    ClientPlaces("chiave-finta", http).cerca("officina", ZONA, massimo=60)

    assert http.richieste[0]["json"]["pageSize"] == 20


def test_nessun_risultato():
    assert ClientPlaces("chiave-finta", FintoHttp({})).cerca("officina", ZONA) == []


def test_dettagli_di_un_attivita():
    http = FintoHttp(da_file("places_dettagli.json"))

    attivita = ClientPlaces("chiave-finta", http).dettagli("ChIJesempio0000001")

    [richiesta] = http.richieste
    assert richiesta["metodo"] == "GET"
    assert richiesta["url"] == "https://places.googleapis.com/v1/places/ChIJesempio0000001"
    assert richiesta["params"] == {"languageCode": "it", "regionCode": "IT"}
    assert richiesta["headers"]["X-Goog-Api-Key"] == "chiave-finta"
    assert richiesta["headers"]["X-Goog-FieldMask"].split(",")[:2] == ["id", "displayName"]
    assert "places." not in richiesta["headers"]["X-Goog-FieldMask"]
    assert attivita.nome == "Officina Meccanica Esempio"
    assert attivita.recensioni == 132


def test_errore_dell_api():
    http = FintoHttp(FintaRisposta(da_file("places_errore_chiave.json"), stato=403))

    with pytest.raises(ErroreApi, match="403.*Places API \\(New\\) has not been used") as errore:
        ClientPlaces("chiave-finta", http).cerca("officina", ZONA)

    assert errore.value.stato_http == 403
    assert "chiave-finta" not in str(errore.value)


def test_da_ambiente_senza_chiave():
    with pytest.raises(VariabileMancante, match="PLACES_API_KEY"):
        da_ambiente({})


def test_da_ambiente_con_chiave():
    assert isinstance(da_ambiente({"PLACES_API_KEY": "chiave-finta"}), ClientPlaces)
