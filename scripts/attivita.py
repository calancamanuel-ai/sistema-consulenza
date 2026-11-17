"""Fase 2: ricerca e analisi delle attività nella scheda Attività del foglio.

Comandi:
  cerca SETTORE --ricerca TERMINE --zona ZONA [--massimo 20]
      Cerca su Places e aggiunge al foglio le attività nuove (una richiesta ogni 20 risultati).
  instagram NOME_UTENTE
      Mostra i numeri di un account professionale (Business Discovery), senza scrivere niente.
  analizza PLACE_ID --motivazione TESTO --automazione TESTO [--automazione ...]
           [--segnali s1,s2] [--instagram NOME_UTENTE] [--servizio TESTO ...] [--note TESTO]
      Calcola il punteggio e i servizi proponibili, aggiorna la riga e riordina il foglio.
  sito URL
      Controllo tecnico del sito con PageSpeed (da telefono), senza scrivere niente.
  nota PLACE_ID TESTO
      Aggiunge un'osservazione alla colonna note, senza toccare il resto.
  elenco [--settore SETTORE]
      Mostra le attività del foglio, nell'ordine attuale.

Istruzioni per l'analisi: prompts/analisi-attivita.md.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from consulenza import attivita, instagram, pagespeed, places, sheets  # noqa: E402
from consulenza.api import ErroreApi  # noqa: E402
from consulenza.config import carica_zone  # noqa: E402
from consulenza.opportunita import carica_punti, carica_servizi  # noqa: E402

SCHEDA = "Attività"
TOKEN_NON_VALIDO = 190  # codice Meta: token scaduto o non valido


def _argomenti(argv):
    parser = argparse.ArgumentParser(description="Ricerca e analisi delle attività (Fase 2).")
    comandi = parser.add_subparsers(dest="comando", required=True)
    cerca = comandi.add_parser("cerca")
    cerca.add_argument("settore")
    cerca.add_argument("--ricerca", required=True, help="termine per Maps, per esempio parrucchiere")
    cerca.add_argument("--zona", required=True)
    cerca.add_argument("--massimo", type=int, default=20)
    ig = comandi.add_parser("instagram")
    ig.add_argument("username")
    analisi = comandi.add_parser("analizza")
    analisi.add_argument("place_id")
    analisi.add_argument("--segnali", default="")
    analisi.add_argument("--motivazione", required=True)
    analisi.add_argument("--automazione", action="append", default=[])
    analisi.add_argument("--instagram")
    analisi.add_argument("--servizio", action="append", default=[], help="servizio in più, oltre a quelli dei segnali")
    analisi.add_argument("--note")
    sito = comandi.add_parser("sito")
    sito.add_argument("url")
    nota = comandi.add_parser("nota")
    nota.add_argument("place_id")
    nota.add_argument("testo")
    elenco = comandi.add_parser("elenco")
    elenco.add_argument("--settore")
    return parser.parse_args(argv)


def _cerca(arg, foglio, client) -> int:
    zona = next((z for z in carica_zone() if z.nome == arg.zona), None)
    if zona is None:
        print(f"ERRORE: la zona {arg.zona!r} non è in config/zone.yaml")
        return 1
    foglio.prepara()
    esistenti = {r["place_id"] for r in foglio.leggi(SCHEDA)}
    trovate = client.cerca(arg.ricerca, zona, arg.massimo)
    nuove = attivita.nuove_righe(trovate, esistenti, arg.settore, zona.nome)
    foglio.aggiungi(SCHEDA, nuove)
    for r in nuove:
        print(f"  {r['place_id']} | {r['nome']} | {r['indirizzo']} | sito: {r['sito'] or 'nessuno'} "
              f"| recensioni: {r['recensioni']}")
    print(f"Trovate {len(trovate)}, aggiunte {len(nuove)}")
    return 0


def _instagram(arg, client, oggi) -> int:
    profilo = client.profilo(instagram.normalizza_username(arg.username))
    if profilo is None:
        print(f"{arg.username}: account inesistente o non professionale")
        return 1
    r = attivita.riassunto_instagram(profilo, oggi)
    print(f"@{profilo.username}: {r['follower']} follower, {r['numero_post']} post, "
          f"ultimo post {r['ultimo_post'] or 'nessuno'}, {r['post_ultimi_90_giorni']} post negli ultimi 90 giorni")
    print(f"  nome: {profilo.nome or ''} | sito: {profilo.sito or 'nessuno'}")
    print(f"  bio: {(profilo.bio or '').replace(chr(10), ' ')}")
    for p in profilo.post[:5]:
        print(f"  {p.data.date()} {p.tipo} like {p.like} commenti {p.commenti} visualizzazioni {p.visualizzazioni}")
    return 0


def _si_no(valore) -> str:
    return "?" if valore is None else ("sì" if valore else "no")


def _sito(arg, client) -> int:
    c = client.controlla(arg.url)
    voti = ", ".join(f"{nome} {'?' if v is None else v}" for nome, v in
                     (("prestazioni da telefono", c.prestazioni), ("SEO", c.seo), ("buone pratiche", c.buone_pratiche)))
    print(f"{c.url_finale or arg.url}: {voti} (su 100)")
    print(f"  tutto in https: {_si_no(c.tutto_https)} | adatto al telefono: {_si_no(c.adatto_al_telefono)} "
          f"| titolo: {_si_no(c.titolo)} | descrizione: {_si_no(c.descrizione)} "
          f"| cookie di terze parti: {'?' if c.cookie_terze_parti is None else c.cookie_terze_parti}")
    return 0


def _analizza(arg, foglio, client, oggi) -> int:
    foglio.prepara()  # crea le colonne nuove (per esempio servizi) se il foglio non le ha ancora
    righe = foglio.leggi(SCHEDA)
    indice = next((i for i, r in enumerate(righe) if r["place_id"] == arg.place_id), None)
    if indice is None:
        print(f"ERRORE: {arg.place_id} non è nella scheda {SCHEDA}")
        return 1
    profilo = None
    if arg.instagram:
        profilo = client.profilo(instagram.normalizza_username(arg.instagram))
        if profilo is None:
            print(f"ERRORE: {arg.instagram}: account inesistente o non professionale")
            return 1
    segnali = [s.strip() for s in arg.segnali.split(",") if s.strip()]
    try:
        nuova = attivita.analizza(righe[indice], segnali, arg.motivazione, arg.automazione, carica_punti(),
                                  attivita.carica_soglia_recensioni(), oggi, profilo,
                                  servizi=carica_servizi(), extra=arg.servizio)
    except ValueError as errore:
        print(f"ERRORE: {errore}")
        return 1
    if arg.note is not None:
        nuova["note"] = arg.note
    righe[indice] = nuova
    foglio.riscrivi(SCHEDA, attivita.ordina(righe))
    print(f"{nuova['nome']}: punteggio {nuova['punteggio']} ({nuova['segnali'] or 'nessun segnale'})")
    return 0


def _nota(arg, foglio) -> int:
    righe = foglio.leggi(SCHEDA)
    riga = next((r for r in righe if r["place_id"] == arg.place_id), None)
    if riga is None:
        print(f"ERRORE: {arg.place_id} non è nella scheda {SCHEDA}")
        return 1
    riga["note"] = " | ".join(t for t in (str(riga.get("note") or ""), arg.testo.strip()) if t)
    foglio.riscrivi(SCHEDA, righe)
    print(f"{riga['nome']}: nota aggiunta")
    return 0


def _elenco(arg, foglio) -> int:
    for r in foglio.leggi(SCHEDA):
        if arg.settore and r.get("settore") != arg.settore:
            continue
        print(f"{r.get('punteggio', ''):>3} | {r['place_id']} | {r.get('nome', '')} | {r.get('zona', '')} "
              f"| sito: {r.get('sito') or 'nessuno'} | recensioni: {r.get('recensioni', '')} "
              f"| instagram: {r.get('instagram') or '-'}")
    return 0


def main(argv=None, **dipendenze) -> int:
    try:
        return _esegui(_argomenti(argv), **dipendenze)
    except ErroreApi as errore:
        print(f"ERRORE: {errore}")
        if errore.codice == TOKEN_NON_VALIDO:
            print("  -> token Instagram scaduto o non valido: rinnovalo (docs/SETUP.md, passo 4c)")
        return 1


def _esegui(arg, foglio=None, client_places=None, client_instagram=None, client_pagespeed=None, oggi=None) -> int:
    # Foglio e client si creano solo se servono: i test li passano già pronti.
    oggi = oggi or date.today()
    if arg.comando == "instagram":
        return _instagram(arg, client_instagram or instagram.da_ambiente(), oggi)
    if arg.comando == "sito":
        return _sito(arg, client_pagespeed or pagespeed.da_ambiente())
    foglio = foglio or sheets.da_ambiente()
    if arg.comando == "cerca":
        return _cerca(arg, foglio, client_places or places.da_ambiente())
    if arg.comando == "analizza":
        if arg.instagram and client_instagram is None:
            client_instagram = instagram.da_ambiente()
        return _analizza(arg, foglio, client_instagram, oggi)
    if arg.comando == "nota":
        return _nota(arg, foglio)
    return _elenco(arg, foglio)


if __name__ == "__main__":
    sys.exit(main())
