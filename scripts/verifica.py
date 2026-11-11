"""Verifica della Fase 0 con le credenziali reali.

Controlla le variabili d'ambiente, poi:
  1. foglio Google: crea schede e intestazioni se mancano, legge Attività e Contatti,
     scrive una riga di prova nella scheda Verifica;
  2. Places: cerca attività di un settore in una zona e legge i dettagli della prima;
  3. Instagram: chiama Business Discovery sul nome utente indicato.

Uso:
  python scripts/verifica.py NOME_UTENTE_INSTAGRAM [--settore officina] [--zona "San Giovanni in Persiceto"]
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import requests  # noqa: E402

from consulenza import instagram, places, sheets  # noqa: E402
from consulenza.api import ErroreApi  # noqa: E402
from consulenza.config import carica_zone  # noqa: E402

VARIABILI = (
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "SHEET_ID",
    "PLACES_API_KEY",
    "IG_ACCESS_TOKEN",
    "IG_USER_ID",
)
SCHEDA_PROVA = "Verifica"


def controlla_variabili(ambiente) -> None:
    print("Variabili d'ambiente (i valori non vengono mostrati):")
    for nome in VARIABILI:
        presente = bool(ambiente.get(nome, "").strip())
        print(f"  {nome}: {'presente' if presente else 'MANCANTE'}")


def verifica_foglio(ambiente) -> str:
    schede = {**sheets.SCHEDE, SCHEDA_PROVA: ["data", "esito"]}
    foglio = sheets.da_ambiente(ambiente, schede)
    foglio.prepara()
    attivita = foglio.leggi("Attività")
    contatti = foglio.leggi("Contatti")
    adesso = datetime.now().isoformat(timespec="seconds")
    foglio.aggiungi(SCHEDA_PROVA, [{"data": adesso, "esito": "riga di prova di scripts/verifica.py"}])
    if not any(r.get("data") == adesso for r in foglio.leggi(SCHEDA_PROVA)):
        raise RuntimeError("la riga di prova non risulta scritta")
    return (
        f"schede pronte; Attività: {len(attivita)} righe, Contatti: {len(contatti)} righe; "
        f"riga di prova scritta nella scheda {SCHEDA_PROVA}"
    )


def verifica_places(ambiente, settore: str, nome_zona: str) -> str:
    zona = next((z for z in carica_zone() if z.nome == nome_zona), None)
    if zona is None:
        raise ValueError(f"la zona {nome_zona!r} non è in config/zone.yaml")
    client = places.da_ambiente(ambiente)
    trovate = client.cerca(settore, zona, massimo=5)
    if not trovate:
        raise RuntimeError(f"nessuna attività trovata per {settore!r} a {zona.nome}")
    for a in trovate:
        print(f"    - {a.nome} | {a.indirizzo} | sito: {a.sito or 'nessuno'} | recensioni: {a.recensioni}")
    dettagli = client.dettagli(trovate[0].place_id)
    return f"{len(trovate)} attività trovate per {settore!r} a {zona.nome}; dettagli letti per {dettagli.nome}"


def verifica_instagram(ambiente, username: str) -> str:
    profilo = instagram.da_ambiente(ambiente).profilo(username)
    if profilo is None:
        raise RuntimeError(f"{username}: account inesistente o non professionale; prova con un account aziendale")
    ultimo = profilo.post[0].data.date().isoformat() if profilo.post else "nessuno"
    con_visualizzazioni = sum(p.visualizzazioni is not None for p in profilo.post)
    return (
        f"@{profilo.username}: {profilo.follower} follower, {profilo.numero_post} post; "
        f"letti {len(profilo.post)} post recenti (ultimo: {ultimo}, con visualizzazioni: {con_visualizzazioni})"
    )


def suggerimento(passo: str, errore: Exception) -> str:
    if isinstance(errore, requests.ConnectionError):
        return " -> controlla i domini autorizzati nell'ambiente cloud (docs/SETUP.md, passo 5)"
    if isinstance(errore, ErroreApi):
        if passo == "Foglio Google" and errore.stato_http in (403, 404):
            return " -> controlla SHEET_ID e che il foglio sia condiviso come Editor con l'account di servizio"
        if passo == "Instagram" and errore.codice == 190:
            return " -> token scaduto o non valido: copia quello aggiornato (docs/SETUP.md, passo 4)"
    return ""


def main(argv=None, ambiente=None) -> int:
    parser = argparse.ArgumentParser(description="Verifica di foglio, Places e Instagram.")
    parser.add_argument("username", help="nome utente di un account Instagram professionale")
    parser.add_argument("--settore", default="officina")
    parser.add_argument("--zona", default="San Giovanni in Persiceto")
    argomenti = parser.parse_args(argv)
    ambiente = os.environ if ambiente is None else ambiente

    controlla_variabili(ambiente)
    passi = (
        ("Foglio Google", lambda: verifica_foglio(ambiente)),
        ("Places", lambda: verifica_places(ambiente, argomenti.settore, argomenti.zona)),
        ("Instagram", lambda: verifica_instagram(ambiente, argomenti.username)),
    )
    riusciti = 0
    for nome, passo in passi:
        print(f"\n{nome}...")
        try:
            print(f"OK {nome}: {passo()}")
            riusciti += 1
        except Exception as errore:  # si riporta ogni passo, anche se uno fallisce
            print(f"ERRORE {nome}: {type(errore).__name__}: {errore}{suggerimento(nome, errore)}")
    print(f"\nPassi riusciti: {riusciti} su {len(passi)}")
    return 0 if riusciti == len(passi) else 1


if __name__ == "__main__":
    raise SystemExit(main())
