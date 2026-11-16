from pathlib import Path

import pytest

from consulenza.settori import (
    COLONNE,
    CRITERI,
    carica_regole,
    classifica,
    leggi,
    punteggio_base,
    scrivi,
)

PESI = {
    "lavoro_ripetitivo": 25,
    "capacita_spesa": 15,
    "dimensione_mercato": 15,
    "potenziale_ricorrente": 10,
    "facilita_contatto": 10,
    "maturita_digitale": 10,
    "concorrenza": 5,
}
MOLTIPLICATORI = {"normale": 1.0, "dati_sensibili": 0.8}


def prove_complete(testo="motivo https://esempio.it/fonte"):
    return " | ".join(f"{c}: {testo}" for c in CRITERI)


def riga(nome, voto=3, rischio="normale", **voti):
    r = {c: str(voti.get(c, voto)) for c in CRITERI}
    r.update(settore=nome, moltiplicatore_rischio=rischio, prove=prove_complete())
    return r


def test_i_criteri_sono_quelli_del_file_di_configurazione():
    assert list(CRITERI) == list(PESI)
    assert COLONNE == ("settore", *CRITERI, "moltiplicatore_rischio", "punteggio_base", "punteggio", "prove")


def test_base_minima_e_massima():
    assert punteggio_base({c: 1 for c in CRITERI}, PESI) == 20
    assert punteggio_base({c: 5 for c in CRITERI}, PESI) == 100


def test_base_pesata():
    voti = {c: 1 for c in CRITERI} | {"lavoro_ripetitivo": 5}
    # (25×5 + 65×1) / 90 × 20
    assert punteggio_base(voti, PESI) == pytest.approx(42.22, abs=0.01)


def test_i_pesi_non_devono_sommare_a_100():
    pesi = {c: 1 for c in CRITERI}

    assert punteggio_base({c: 1 for c in CRITERI}, pesi) == 20
    assert punteggio_base({c: 5 for c in CRITERI}, pesi) == 100


@pytest.mark.parametrize("voto", [0, 6, 2.5])
def test_voto_fuori_scala(voto):
    with pytest.raises(ValueError, match="da 1 a 5"):
        punteggio_base({c: 3 for c in CRITERI} | {"concorrenza": voto}, PESI)


def test_voto_mancante():
    voti = {c: 3 for c in CRITERI if c != "concorrenza"}
    with pytest.raises(ValueError, match="concorrenza"):
        punteggio_base(voti, PESI)


def test_classifica_ordina_e_applica_il_rischio():
    righe = [
        riga("bar", voto=2),
        riga("dentisti", voto=4, rischio="dati_sensibili"),
        riga("officine", voto=4),
    ]

    risultato = classifica(righe, PESI, MOLTIPLICATORI)

    assert [(r["settore"], r["punteggio_base"], r["punteggio"]) for r in risultato] == [
        ("officine", "80.0", "80.0"),
        ("dentisti", "80.0", "64.0"),
        ("bar", "40.0", "40.0"),
    ]


def test_a_parita_di_punteggio_ordine_alfabetico():
    risultato = classifica([riga("parrucchieri"), riga("estetiste")], PESI, MOLTIPLICATORI)

    assert [r["settore"] for r in risultato] == ["estetiste", "parrucchieri"]


def test_punteggio_arrotondato_a_un_decimale():
    voti = {c: 1 for c in CRITERI} | {"concorrenza": 2}
    r = riga("fioristi", rischio="dati_sensibili", **voti)

    (risultato,) = classifica([r], PESI, MOLTIPLICATORI)

    # (85×1 + 5×2) / 90 × 20 = 21,11; × 0,8 = 16,89
    assert risultato["punteggio_base"] == "21.1"
    assert risultato["punteggio"] == "16.9"


def test_moltiplicatore_sconosciuto():
    with pytest.raises(ValueError, match="moltiplicatore"):
        classifica([riga("bar", rischio="alto")], PESI, MOLTIPLICATORI)


def test_ogni_criterio_deve_avere_una_prova_con_link():
    r = riga("bar")
    r["prove"] = " | ".join(f"{c}: motivo https://x.it" for c in CRITERI if c != "concorrenza")
    r["prove"] += " | concorrenza: motivo senza link"

    with pytest.raises(ValueError, match="bar.*concorrenza"):
        classifica([r], PESI, MOLTIPLICATORI)


def test_settore_duplicato():
    with pytest.raises(ValueError, match="duplicato"):
        classifica([riga("bar"), riga("bar")], PESI, MOLTIPLICATORI)


def test_scrivi_e_rileggi(tmp_path):
    percorso = tmp_path / "settori.csv"
    righe = classifica([riga("bar"), riga("officine", voto=4)], PESI, MOLTIPLICATORI)

    scrivi(percorso, righe)

    assert leggi(percorso) == righe
    assert percorso.read_text(encoding="utf-8").splitlines()[0] == ",".join(COLONNE)


def test_leggi_rifiuta_colonne_diverse(tmp_path):
    percorso = tmp_path / "settori.csv"
    percorso.write_text("settore,voto\nbar,3\n", encoding="utf-8")

    with pytest.raises(ValueError, match="colonne"):
        leggi(percorso)


def test_la_classifica_nel_repository_e_valida_e_aggiornata():
    """data/settori.csv deve essere già passato da scripts/classifica_settori.py."""
    percorso = Path(__file__).resolve().parents[1] / "data" / "settori.csv"
    righe = leggi(percorso)

    assert classifica(righe, *carica_regole()) == righe


def test_regole_dal_file_di_configurazione():
    assert carica_regole() == (PESI, MOLTIPLICATORI)
