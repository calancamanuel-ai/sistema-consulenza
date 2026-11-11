import pytest

from consulenza.opportunita import SEGNALI, Punteggio, calcola, carica_punti

PUNTI = carica_punti()


def test_i_punti_vengono_dal_file_di_configurazione():
    assert set(PUNTI) == set(SEGNALI)
    assert PUNTI["catena"] == -3


def test_instagram_attivo_e_nessun_sito_fanno_il_massimo():
    assert calcola({"instagram_attivo", "nessun_sito"}, PUNTI) == Punteggio(
        totale=4, segnali=("instagram_attivo", "nessun_sito")
    )


def test_nessun_sito_senza_instagram_attivo_non_conta():
    assert calcola({"nessun_sito"}, PUNTI) == Punteggio(totale=0, segnali=())


def test_nessuna_presenza_online():
    assert calcola({"nessun_sito", "nessuna_presenza"}, PUNTI) == Punteggio(
        totale=-1, segnali=("nessuna_presenza",)
    )


def test_somma_di_piu_segnali_nell_ordine_del_piano():
    risultato = calcola(
        ["molte_recensioni", "indipendente", "sito_debole", "instagram_attivo"], PUNTI
    )

    assert risultato.totale == 6
    assert risultato.segnali == (
        "instagram_attivo",
        "sito_debole",
        "molte_recensioni",
        "indipendente",
    )


def test_catena_con_prenotazione_moderna():
    assert calcola({"catena", "prenotazione_moderna"}, PUNTI).totale == -4


def test_nessun_segnale():
    assert calcola(set(), PUNTI) == Punteggio(totale=0, segnali=())


def test_usa_i_punti_ricevuti():
    punti = dict(PUNTI, instagram_attivo=5, nessun_sito=3)

    assert calcola({"instagram_attivo", "nessun_sito"}, punti).totale == 8


def test_segnale_sconosciuto():
    with pytest.raises(ValueError, match="instagram_ativo"):
        calcola({"instagram_ativo"}, PUNTI)


@pytest.mark.parametrize(
    "segnali",
    [
        {"indipendente", "catena"},
        {"nessun_sito", "sito_debole"},
        {"nessun_sito", "prenotazione_moderna"},
        {"nessuna_presenza", "instagram_attivo"},
        {"nessuna_presenza", "sito_debole"},
    ],
)
def test_segnali_incompatibili(segnali):
    with pytest.raises(ValueError, match="incompatibili"):
        calcola(segnali, PUNTI)


def test_configurazione_con_segnale_mancante(tmp_path):
    percorso = tmp_path / "punteggio.yaml"
    percorso.write_text("opportunita:\n  punti:\n    instagram_attivo: 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="nessun_sito"):
        carica_punti(percorso)
