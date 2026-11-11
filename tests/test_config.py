import csv
from pathlib import Path

import pytest

from consulenza.config import Zona, carica_punteggio, carica_zone

RADICE = Path(__file__).resolve().parents[1]


def test_le_zone_partono_da_san_giovanni_bologna_e_modena():
    zone = carica_zone()

    assert [z.nome for z in zone] == ["San Giovanni in Persiceto", "Bologna", "Modena"]
    assert all(isinstance(z, Zona) for z in zone)
    assert all(0 < z.raggio_m <= 50000 for z in zone)


def test_zona_letta_da_file(tmp_path):
    percorso = tmp_path / "zone.yaml"
    percorso.write_text(
        "zone:\n  - nome: Carpi\n    lat: 44.78\n    lng: 10.88\n    raggio_m: 5000\n",
        encoding="utf-8",
    )

    assert carica_zone(percorso) == [Zona("Carpi", 44.78, 10.88, 5000)]


def test_pesi_dei_settori_come_nel_piano():
    pesi = carica_punteggio()["settori"]["pesi"]

    assert pesi == {
        "lavoro_ripetitivo": 25,
        "capacita_spesa": 15,
        "dimensione_mercato": 15,
        "potenziale_ricorrente": 10,
        "voucher_incentivi": 10,
        "facilita_contatto": 10,
        "maturita_digitale": 10,
        "concorrenza": 5,
    }
    assert sum(pesi.values()) == 100


def test_moltiplicatori_di_rischio_come_nel_piano():
    assert carica_punteggio()["settori"]["moltiplicatore_rischio"] == {
        "normale": 1.0,
        "dati_sensibili": 0.8,
    }


def test_punti_dei_segnali_come_nel_piano():
    assert carica_punteggio()["opportunita"]["punti"] == {
        "instagram_attivo": 2,
        "nessun_sito": 2,
        "sito_debole": 2,
        "molte_recensioni": 1,
        "indipendente": 1,
        "catena": -3,
        "prenotazione_moderna": -1,
        "nessuna_presenza": -1,
    }


def test_settori_csv_vuoto_con_una_colonna_per_criterio():
    with open(RADICE / "data" / "settori.csv", encoding="utf-8", newline="") as f:
        righe = list(csv.reader(f))

    assert len(righe) == 1, "settori.csv deve contenere solo le intestazioni"
    intestazioni = righe[0]
    criteri = list(carica_punteggio()["settori"]["pesi"])
    assert intestazioni[0] == "settore"
    assert intestazioni[1 : 1 + len(criteri)] == criteri
    assert intestazioni[1 + len(criteri) :] == [
        "moltiplicatore_rischio",
        "punteggio_base",
        "punteggio",
        "prove",
    ]


def test_file_di_configurazione_mancante(tmp_path):
    with pytest.raises(FileNotFoundError):
        carica_zone(tmp_path / "manca.yaml")
