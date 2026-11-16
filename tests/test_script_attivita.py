import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path

from consulenza.instagram import Post, ProfiloInstagram
from consulenza.places import Attivita
from consulenza.sheets import COLONNE_ATTIVITA

PERCORSO = Path(__file__).resolve().parents[1] / "scripts" / "attivita.py"
spec = importlib.util.spec_from_file_location("script_attivita", PERCORSO)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)

OGGI = date(2026, 11, 16)


class FintoFoglio:
    def __init__(self, righe=()):
        self.righe = [{c: "" for c in COLONNE_ATTIVITA} | r for r in righe]
        self.preparato = False

    def prepara(self):
        self.preparato = True

    def leggi(self, scheda):
        assert scheda == "Attività"
        return [dict(r) for r in self.righe]

    def aggiungi(self, scheda, righe):
        self.righe += [{c: "" for c in COLONNE_ATTIVITA} | r for r in righe]

    def riscrivi(self, scheda, righe):
        self.righe = [dict(r) for r in righe]


class FintoPlaces:
    def __init__(self, trovate):
        self.trovate = trovate
        self.chiamate = []

    def cerca(self, ricerca, zona, massimo):
        self.chiamate.append((ricerca, zona.nome, massimo))
        return self.trovate


class FintoInstagram:
    def __init__(self, profili):
        self.profili = profili

    def profilo(self, username):
        return self.profili.get(username)


def trovata(place_id, sito=None, recensioni=10):
    return Attivita(place_id, f"Salone {place_id}", "Via Esempio 1", sito, "051 000 0000", 4.6,
                    recensioni, "OPERATIONAL", "hair_care", "https://maps.google.com/?cid=1")


PROFILO = ProfiloInstagram("salone_p2", "Salone", "Taglio e colore", None, 1200, 250,
                           (Post(datetime(2026, 11, 1, tzinfo=timezone.utc), "IMAGE", 30, 1, None, None),))


def test_cerca_aggiunge_solo_le_nuove(capsys):
    foglio = FintoFoglio([{"place_id": "p1", "nome": "Salone p1"}])
    places = FintoPlaces([trovata("p1"), trovata("p2", sito="https://p2.example")])

    esito = script.main(["cerca", "parrucchieri e barbieri", "--ricerca", "parrucchiere",
                         "--zona", "Bologna"], foglio=foglio, client_places=places)

    assert esito == 0
    assert foglio.preparato
    assert places.chiamate == [("parrucchiere", "Bologna", 20)]
    assert [r["place_id"] for r in foglio.righe] == ["p1", "p2"]
    assert foglio.righe[1]["settore"] == "parrucchieri e barbieri"
    uscita = capsys.readouterr().out
    assert "Salone p2" in uscita and "https://p2.example" in uscita
    assert "aggiunte 1" in uscita


def test_cerca_zona_sconosciuta(capsys):
    esito = script.main(["cerca", "x", "--ricerca", "x", "--zona", "Atlantide"],
                        foglio=FintoFoglio(), client_places=FintoPlaces([]))

    assert esito == 1
    assert "Atlantide" in capsys.readouterr().out


def test_instagram_mostra_il_riassunto(capsys):
    esito = script.main(["instagram", "@salone_p2"], client_instagram=FintoInstagram({"salone_p2": PROFILO}), oggi=OGGI)

    assert esito == 0
    uscita = capsys.readouterr().out
    assert "1200 follower" in uscita and "ultimo post 2026-11-01" in uscita and "Taglio e colore" in uscita


def test_instagram_account_non_professionale(capsys):
    assert script.main(["instagram", "privato"], client_instagram=FintoInstagram({}), oggi=OGGI) == 1
    assert "non professionale" in capsys.readouterr().out


def test_analizza_aggiorna_e_riordina(capsys):
    foglio = FintoFoglio([
        {"place_id": "p1", "nome": "Salone p1", "punteggio": 1, "recensioni": 5},
        {"place_id": "p2", "nome": "Salone p2", "recensioni": 40, "note": "visto di persona"},
    ])

    esito = script.main(
        ["analizza", "p2", "--instagram", "salone_p2", "--segnali", "instagram_attivo,nessun_sito",
         "--motivazione", "Instagram curato e nessun sito.", "--automazione", "Sito vetrina",
         "--automazione", "Promemoria degli appuntamenti"],
        foglio=foglio, client_instagram=FintoInstagram({"salone_p2": PROFILO}), oggi=OGGI,
    )

    assert esito == 0
    primo = foglio.righe[0]
    assert primo["place_id"] == "p2"
    assert (primo["punteggio"], primo["segnali"], primo["follower"]) == (4, "instagram_attivo, nessun_sito", 1200)
    assert primo["automazioni"] == "Sito vetrina; Promemoria degli appuntamenti"
    assert primo["note"] == "visto di persona"
    assert "punteggio 4" in capsys.readouterr().out


def test_analizza_errore_non_scrive(capsys):
    foglio = FintoFoglio([{"place_id": "p1", "nome": "Salone p1"}])
    prima = [dict(r) for r in foglio.righe]

    esito = script.main(["analizza", "p1", "--segnali", "instagram_attivo", "--motivazione", "m",
                         "--automazione", "a"], foglio=foglio, oggi=OGGI)

    assert esito == 1
    assert foglio.righe == prima
    assert "ERRORE" in capsys.readouterr().out


def test_analizza_attivita_sconosciuta(capsys):
    esito = script.main(["analizza", "p9", "--motivazione", "m", "--automazione", "a"],
                        foglio=FintoFoglio(), oggi=OGGI)

    assert esito == 1
    assert "p9" in capsys.readouterr().out


def test_elenco(capsys):
    foglio = FintoFoglio([
        {"place_id": "p1", "nome": "Salone p1", "settore": "parrucchieri e barbieri", "recensioni": 5},
        {"place_id": "p2", "nome": "Officina p2", "settore": "officine meccaniche", "punteggio": 3},
    ])

    assert script.main(["elenco", "--settore", "officine meccaniche"], foglio=foglio) == 0

    uscita = capsys.readouterr().out
    assert "Officina p2" in uscita and "Salone p1" not in uscita


class InstagramScaduto:
    def profilo(self, username):
        from consulenza.api import ErroreApi
        raise ErroreApi("Instagram", 401, "Error validating access token", codice=190)


def test_token_scaduto_messaggio_chiaro(capsys):
    esito = script.main(["instagram", "salone"], client_instagram=InstagramScaduto(), oggi=OGGI)

    assert esito == 1
    uscita = capsys.readouterr().out
    assert "token" in uscita and "docs/SETUP.md" in uscita


def test_nota_si_aggiunge_a_quella_esistente(capsys):
    foglio = FintoFoglio([{"place_id": "p1", "nome": "Salone p1", "note": "visto di persona"},
                          {"place_id": "p2", "nome": "Salone p2"}])

    assert script.main(["nota", "p1", "sito in manutenzione"], foglio=foglio) == 0
    assert script.main(["nota", "p2", "nessun sito"], foglio=foglio) == 0

    assert foglio.righe[0]["note"] == "visto di persona | sito in manutenzione"
    assert foglio.righe[1]["note"] == "nessun sito"


def test_nota_attivita_sconosciuta(capsys):
    assert script.main(["nota", "p9", "x"], foglio=FintoFoglio()) == 1
