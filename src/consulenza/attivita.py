"""Righe della scheda Attività (Fase 2): nuove attività da Places, analisi e ordine.

I segnali qualitativi (Instagram attivo, sito debole, catena...) li decide Claude nella sessione
(prompts/analisi-attivita.md); qui si fanno le parti meccaniche.
"""
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from pathlib import Path

from consulenza.config import CARTELLA, carica_punteggio
from consulenza.instagram import ProfiloInstagram
from consulenza.opportunita import calcola
from consulenza.places import Attivita

CHIUSA = "CLOSED_PERMANENTLY"
MAX_AUTOMAZIONI = 3


def carica_soglia_recensioni(percorso: Path = CARTELLA / "punteggio.yaml") -> int:
    return int(carica_punteggio(percorso)["opportunita"]["soglia_molte_recensioni"])


def nuove_righe(trovate: Iterable[Attivita], esistenti: set[str], settore: str, zona: str) -> list[dict]:
    """Righe per il foglio, senza le attività già presenti e quelle chiuse definitivamente."""
    righe, visti = [], set(esistenti)
    for a in trovate:
        if a.place_id in visti or a.stato == CHIUSA:
            continue
        visti.add(a.place_id)
        righe.append({
            "place_id": a.place_id,
            "nome": a.nome,
            "settore": settore,
            "zona": zona,
            "indirizzo": a.indirizzo,
            "telefono": a.telefono or "",
            "sito": a.sito or "",
            "link_maps": a.link_maps or "",
            "valutazione": a.valutazione if a.valutazione is not None else "",
            "recensioni": a.recensioni,
            "stato_maps": a.stato or "",
            "tipo_maps": a.tipo or "",
        })
    return righe


def riassunto_instagram(profilo: ProfiloInstagram, oggi: date) -> dict:
    """I numeri che servono a Claude per giudicare se l'account è attivo."""
    limite = oggi - timedelta(days=90)
    return {
        "follower": profilo.follower,
        "numero_post": profilo.numero_post,
        "ultimo_post": profilo.post[0].data.date().isoformat() if profilo.post else "",
        "post_ultimi_90_giorni": sum(p.data.date() >= limite for p in profilo.post),
    }


def analizza(
    riga: Mapping,
    segnali: Iterable[str],
    motivazione: str,
    automazioni: list[str],
    punti: Mapping[str, int],
    soglia_recensioni: int,
    oggi: date,
    profilo: ProfiloInstagram | None = None,
) -> dict:
    """Riga aggiornata con segnali, punteggio, motivazione e automazioni; le altre colonne restano."""
    if not motivazione.strip():
        raise ValueError("Manca la motivazione")
    automazioni = [a.strip() for a in automazioni]
    if not 1 <= len(automazioni) <= MAX_AUTOMAZIONI or not all(automazioni):
        raise ValueError(f"Servono da 1 a {MAX_AUTOMAZIONI} automazioni, non vuote")
    nuova = dict(riga)
    if profilo is not None:
        nuova.update(instagram=profilo.username, follower=profilo.follower,
                     ultimo_post=riassunto_instagram(profilo, oggi)["ultimo_post"])
    segnali = set(segnali)
    if "instagram_attivo" in segnali and not nuova.get("instagram"):
        raise ValueError("instagram_attivo richiede il profilo Instagram letto con Business Discovery")
    # "Molte recensioni" si decide con i dati di Maps, non a giudizio.
    segnali.discard("molte_recensioni")
    if int(nuova.get("recensioni") or 0) >= soglia_recensioni:
        segnali.add("molte_recensioni")
    punteggio = calcola(segnali, punti)
    nuova.update(
        segnali=", ".join(punteggio.segnali),
        punteggio=punteggio.totale,
        motivazione=motivazione.strip(),
        automazioni="; ".join(automazioni),
        data_analisi=oggi.isoformat(),
    )
    return nuova


def ordina(righe: Iterable[Mapping]) -> list[dict]:
    """Prima le attività analizzate, dal punteggio più alto; a parità, più recensioni prima."""
    def chiave(r):
        analizzata = r.get("punteggio") not in ("", None)
        return (not analizzata, -float(r["punteggio"]) if analizzata else 0, -int(r.get("recensioni") or 0))
    return [dict(r) for r in sorted(righe, key=chiave)]
