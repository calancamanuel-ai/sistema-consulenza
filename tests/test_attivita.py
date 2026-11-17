from datetime import date, datetime, timezone

import pytest

from consulenza.attivita import analizza, carica_soglia_recensioni, nuove_righe, ordina, riassunto_instagram
from consulenza.instagram import Post, ProfiloInstagram
from consulenza.opportunita import carica_punti, carica_servizi
from consulenza.places import Attivita

PUNTI = carica_punti()
SERVIZI = {"nessun_sito": "sito vetrina", "solo_telefono": "WhatsApp Business", "sito_debole": "sito nuovo"}
OGGI = date(2026, 11, 16)


def trovata(place_id, stato="OPERATIONAL", sito=None, recensioni=10):
    return Attivita(place_id, f"Attività {place_id}", "Via Esempio 1", sito, "051 000 0000", 4.5,
                    recensioni, stato, "hair_care", f"https://maps.google.com/?cid={place_id}")


def post(giorno):
    return Post(datetime(2026, *giorno, 10, tzinfo=timezone.utc), "IMAGE", 20, 2, None, None)


PROFILO = ProfiloInstagram("salone_esempio", "Salone Esempio", "bio", None, 1500, 300,
                           (post((11, 10)), post((10, 1)), post((8, 30)), post((5, 1))))


def riga(**campi):
    base = {"place_id": "p1", "nome": "Salone Esempio", "recensioni": 40, "sito": "", "instagram": "",
            "follower": "", "ultimo_post": "", "segnali": "", "punteggio": "", "motivazione": "",
            "automazioni": "", "servizi": "", "data_analisi": "", "note": "a mano"}
    return base | campi


def test_soglia_delle_recensioni_dal_file_di_configurazione():
    assert carica_soglia_recensioni() == 100


def test_nuove_righe_salta_doppioni_e_chiuse_definitivamente():
    trovate = [trovata("p1", sito="https://salone.example"), trovata("p2"), trovata("p2"),
               trovata("p3", stato="CLOSED_PERMANENTLY"), trovata("p4", stato="CLOSED_TEMPORARILY")]

    righe = nuove_righe(trovate, {"p4"}, "parrucchieri e barbieri", "Bologna")

    assert [r["place_id"] for r in righe] == ["p1", "p2"]
    assert righe[0] == {
        "place_id": "p1", "nome": "Attività p1", "settore": "parrucchieri e barbieri", "zona": "Bologna",
        "indirizzo": "Via Esempio 1", "telefono": "051 000 0000", "sito": "https://salone.example",
        "link_maps": "https://maps.google.com/?cid=p1", "valutazione": 4.5, "recensioni": 10,
        "stato_maps": "OPERATIONAL", "tipo_maps": "hair_care",
    }
    assert righe[1]["sito"] == ""


def test_riassunto_instagram():
    assert riassunto_instagram(PROFILO, OGGI) == {
        "follower": 1500, "numero_post": 300, "ultimo_post": "2026-11-10", "post_ultimi_90_giorni": 3,
    }


def test_riassunto_instagram_senza_post():
    vuoto = ProfiloInstagram("x", None, None, None, 0, 0, ())

    assert riassunto_instagram(vuoto, OGGI)["ultimo_post"] == ""


def test_analizza_con_instagram_attivo_e_senza_sito():
    risultato = analizza(riga(), ["instagram_attivo", "nessun_sito", "indipendente"], "Instagram curato, niente sito.",
                         ["Sito vetrina con prenotazione", "Promemoria WhatsApp"], PUNTI, 100, OGGI, PROFILO)

    assert risultato == riga(
        instagram="salone_esempio", follower=1500, ultimo_post="2026-11-10",
        segnali="instagram_attivo, nessun_sito, indipendente", punteggio=5,
        motivazione="Instagram curato, niente sito.",
        automazioni="Sito vetrina con prenotazione; Promemoria WhatsApp", data_analisi="2026-11-16",
    )


def test_servizi_dai_segnali_che_contano_piu_quelli_extra():
    risultato = analizza(riga(), ["nessun_sito", "solo_telefono", "indipendente"], "m", ["a"], PUNTI, 100, OGGI,
                         servizi=SERVIZI, extra=["buoni regalo online", "WhatsApp Business", " "])

    # nessun_sito non conta senza instagram_attivo, quindi niente sito vetrina; niente doppioni.
    assert risultato["servizi"] == "WhatsApp Business; buoni regalo online"


def test_servizi_vuoti_senza_segnali_che_li_danno():
    assert analizza(riga(), ["indipendente"], "m", ["a"], PUNTI, 100, OGGI, servizi=SERVIZI)["servizi"] == ""


def test_ogni_segnale_dei_servizi_ha_un_servizio():
    servizi = carica_servizi()
    for segnale in ("scheda_incompleta", "lamentele_recensioni", "sito_senza_privacy", "pubblicita_attiva",
                    "solo_telefono", "scheda_non_reclamata", "scheda_trascurata", "nessun_sito", "sito_debole"):
        assert segnale in servizi


def test_molte_recensioni_viene_dai_dati_di_maps():
    con_molte = analizza(riga(recensioni=130), ["sito_debole"], "m", ["a"], PUNTI, 100, OGGI)
    senza = analizza(riga(recensioni=99), ["sito_debole", "molte_recensioni"], "m", ["a"], PUNTI, 100, OGGI)

    assert (con_molte["segnali"], con_molte["punteggio"]) == ("sito_debole, molte_recensioni", 3)
    assert (senza["segnali"], senza["punteggio"]) == ("sito_debole", 2)


def test_instagram_attivo_richiede_il_profilo():
    with pytest.raises(ValueError, match="instagram_attivo"):
        analizza(riga(), ["instagram_attivo"], "m", ["a"], PUNTI, 100, OGGI)


def test_instagram_attivo_vale_anche_con_il_profilo_gia_nel_foglio():
    risultato = analizza(riga(instagram="salone_esempio", follower=900), ["instagram_attivo"], "m", ["a"],
                         PUNTI, 100, OGGI)

    assert (risultato["instagram"], risultato["follower"], risultato["punteggio"]) == ("salone_esempio", 900, 2)


@pytest.mark.parametrize("automazioni", [[], ["a", "b", "c", "d"], ["a", " "]])
def test_da_una_a_tre_automazioni(automazioni):
    with pytest.raises(ValueError, match="automazioni"):
        analizza(riga(), [], "m", automazioni, PUNTI, 100, OGGI)


def test_motivazione_obbligatoria():
    with pytest.raises(ValueError, match="motivazione"):
        analizza(riga(), [], " ", ["a"], PUNTI, 100, OGGI)


def test_ordina_prima_le_analizzate_per_punteggio_poi_per_recensioni():
    righe = [
        riga(place_id="a", punteggio="", recensioni=300),
        riga(place_id="b", punteggio=2, recensioni=10),
        riga(place_id="c", punteggio=4, recensioni=5),
        riga(place_id="d", punteggio=2, recensioni=50),
        riga(place_id="e", punteggio=-1, recensioni=500),
        riga(place_id="f", punteggio="", recensioni=""),
    ]

    assert [r["place_id"] for r in ordina(righe)] == ["c", "d", "b", "e", "a", "f"]
