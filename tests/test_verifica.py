import importlib.util
from pathlib import Path

PERCORSO = Path(__file__).resolve().parents[1] / "scripts" / "verifica.py"
spec = importlib.util.spec_from_file_location("verifica", PERCORSO)
verifica = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifica)

# Questi test non fanno chiamate reali: ogni passo si ferma prima di usare la rete.


def test_senza_variabili_segnala_cosa_manca(capsys):
    esito = verifica.main(["officina_esempio"], ambiente={})

    uscita = capsys.readouterr().out
    assert esito == 1
    for nome in verifica.VARIABILI:
        assert f"{nome}: MANCANTE" in uscita
    assert "ERRORE Foglio Google" in uscita
    assert "ERRORE Places" in uscita
    assert "ERRORE Instagram" in uscita


def test_non_mostra_mai_i_valori_dei_segreti(capsys):
    ambiente = {
        "GOOGLE_SERVICE_ACCOUNT_JSON": "json-segreto{",
        "SHEET_ID": "id-segreto",
        "IG_ACCESS_TOKEN": "token-segreto",
        "IG_USER_ID": "non-numerico",
    }

    esito = verifica.main(["officina_esempio"], ambiente=ambiente)

    uscita = capsys.readouterr().out
    assert esito == 1
    assert "GOOGLE_SERVICE_ACCOUNT_JSON: presente" in uscita
    assert "PLACES_API_KEY: MANCANTE" in uscita
    for segreto in ambiente.values():
        assert segreto not in uscita


def test_zona_sconosciuta(capsys):
    verifica.main(["officina_esempio", "--zona", "Atlantide"], ambiente={"PLACES_API_KEY": "x"})

    assert "Atlantide" in capsys.readouterr().out
