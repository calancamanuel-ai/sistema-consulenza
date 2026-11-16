import importlib.util
from pathlib import Path

from consulenza.settori import CRITERI, COLONNE, leggi

PERCORSO = Path(__file__).resolve().parents[1] / "scripts" / "classifica_settori.py"
spec = importlib.util.spec_from_file_location("classifica_settori", PERCORSO)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)

PROVE = " | ".join(f"{c}: motivo https://esempio.it" for c in CRITERI)


def scrivi_voti(percorso, righe):
    """Righe come le scrive Claude: voti e prove, punteggi ancora vuoti."""
    testa = ",".join(COLONNE)
    corpo = [
        ",".join([nome, *[str(voto)] * len(CRITERI), rischio, "", "", f'"{PROVE}"'])
        for nome, voto, rischio in righe
    ]
    percorso.write_text("\n".join([testa, *corpo]) + "\n", encoding="utf-8")


def test_calcola_ordina_e_riscrive_il_file(tmp_path, capsys):
    percorso = tmp_path / "settori.csv"
    scrivi_voti(percorso, [("bar", 2, "normale"), ("officine", 4, "normale")])

    assert script.main([str(percorso)]) == 0

    righe = leggi(percorso)
    assert [(r["settore"], r["punteggio"]) for r in righe] == [("officine", "80.0"), ("bar", "40.0")]
    uscita = capsys.readouterr().out
    assert uscita.index("officine") < uscita.index("bar")


def test_errore_nei_voti_non_tocca_il_file(tmp_path, capsys):
    percorso = tmp_path / "settori.csv"
    scrivi_voti(percorso, [("bar", 7, "normale")])
    prima = percorso.read_text(encoding="utf-8")

    assert script.main([str(percorso)]) == 1

    assert percorso.read_text(encoding="utf-8") == prima
    assert "ERRORE" in capsys.readouterr().out
