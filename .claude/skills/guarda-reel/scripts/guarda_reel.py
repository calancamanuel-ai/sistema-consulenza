"""Prepara un video di Instagram per l'analisi: video, fotogrammi, trascrizione e metadati.

Uso:
  python guarda_reel.py prepara SORGENTE [--modalita rapida|completa] [--video-url URL]
                                [--post FILE] [--codice CODICE] [--uscita analisi]
  python guarda_reel.py verifica analisi/CODICE/analisi.json

SORGENTE può essere un link Instagram (reel, post, tv), un file video o un link diretto al video
(per esempio media_url dell'API di Meta). Con un link Instagram serve APIFY_TOKEN, a meno che non
si passi --video-url (link diretto) o --post (post già letto con il connettore Apify): in quei
casi lo script non chiama Apify.

Crea USCITA/CODICE/ con video.mp4, frames/, griglia.jpg, trascrizione.txt e meta.json.
Dipendenze: imageio-ffmpeg, faster-whisper (pip install imageio-ffmpeg faster-whisper).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

URL_APIFY = "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"
TIMEOUT_APIFY = 300  # secondi: l'attore parte, legge il post e restituisce il risultato
TIMEOUT_DOWNLOAD = 120
MODALITA = {"rapida": 512, "completa": 768}  # larghezza dei fotogrammi in pixel
MAX_FOTOGRAMMI = 20
MODELLO_WHISPER = "base"
CAMPI_TESTO = ("hook", "cosa_si_vede", "cosa_si_dice", "call_to_action", "riassunto")
CAMPI_ANALISI = ("codice", *CAMPI_TESTO, "testi_a_schermo", "qualita_video", "note")
_LINK_INSTAGRAM = re.compile(r"instagram\.com/(?:[A-Za-z0-9._]+/)?(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)")


class ErroreSkill(Exception):
    """Errore da mostrare così com'è, senza traccia dello stack."""


@dataclass(frozen=True)
class Sorgente:
    tipo: str  # instagram, video_url, file
    codice: str  # nome della cartella di uscita
    valore: str  # link Instagram, link al video o percorso del file
    link: str | None = None  # link Instagram, se noto


# --- Sorgente -----------------------------------------------------------------

def _link_instagram(testo: str) -> str | None:
    trovato = _LINK_INSTAGRAM.search(testo)
    return trovato.group(1) if trovato else None


def riconosci_sorgente(testo: str, video_url: str | None = None, codice: str | None = None) -> Sorgente:
    testo = testo.strip()
    shortcode = _link_instagram(testo)
    link = f"https://www.instagram.com/reel/{shortcode}/" if shortcode else None
    if video_url:
        if not (shortcode or codice):
            raise ValueError("Con --video-url serve un link Instagram oppure --codice")
        return Sorgente("video_url", codice or shortcode, video_url, link)
    if shortcode:
        return Sorgente("instagram", codice or shortcode, link, link)
    if re.match(r"https?://(www\.)?instagram\.com/", testo):
        raise ValueError(f"Il link non porta a un post o a un reel: {testo!r}")
    if re.match(r"https?://", testo):
        senza_parametri = testo.split("?")[0]
        automatico = "video-" + hashlib.sha1(senza_parametri.encode()).hexdigest()[:10]
        return Sorgente("video_url", codice or automatico, testo)
    percorso = Path(testo)
    if testo and percorso.is_file():
        automatico = re.sub(r"[^A-Za-z0-9_-]+", "-", percorso.stem).strip("-") or "video"
        return Sorgente("file", codice or automatico, str(percorso))
    raise ValueError(f"Sorgente non riconosciuta: {testo!r} (serve un link Instagram a un post, "
                     "un link diretto al video o un file esistente)")


# --- Apify --------------------------------------------------------------------

def token_apify(ambiente=os.environ) -> str:
    token = ambiente.get("APIFY_TOKEN", "").strip()
    if not token:
        raise ErroreSkill("Manca la variabile d'ambiente APIFY_TOKEN (chiave API di Apify). "
                          "In alternativa passa --video-url con un link diretto al video.")
    return token


def _post_http(url: str, corpo: bytes, intestazioni: dict, timeout: int):
    richiesta = urllib.request.Request(url, data=corpo, headers=intestazioni, method="POST")
    try:
        with urllib.request.urlopen(richiesta, timeout=timeout) as risposta:
            return json.loads(risposta.read())
    except urllib.error.HTTPError as errore:
        dettaglio = errore.read().decode("utf-8", "replace")[:300]
        raise ErroreSkill(f"Apify ha risposto {errore.code}: {dettaglio}") from None
    except urllib.error.URLError as errore:
        raise ErroreSkill(f"Apify non raggiungibile: {errore.reason}") from None


def post_da_apify(link: str, token: str, http=_post_http) -> tuple[str, dict]:
    """Legge il post con l'attore apify/instagram-scraper; restituisce link al video e dati del post."""
    corpo = json.dumps({"directUrls": [link], "resultsType": "posts", "resultsLimit": 1}).encode()
    # Il token va nell'intestazione, così non finisce negli URL né nei messaggi di errore.
    intestazioni = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return _video_e_dati(http(URL_APIFY, corpo, intestazioni, TIMEOUT_APIFY))


def post_da_file(percorso: Path) -> tuple[str, dict]:
    """Post di apify/instagram-scraper salvato da Claude dopo averlo letto con il connettore Apify."""
    try:
        contenuto = json.loads(Path(percorso).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as errore:
        raise ErroreSkill(f"{percorso}: {errore}") from None
    if isinstance(contenuto, dict) and isinstance(contenuto.get("items"), list):
        contenuto = contenuto["items"]  # risposta intera di get-dataset-items
    return _video_e_dati(contenuto if isinstance(contenuto, list) else [contenuto])


def _video_e_dati(risultati: list) -> tuple[str, dict]:
    if not risultati:
        raise ErroreSkill("Apify non ha restituito nessun risultato (post privato, rimosso o link errato?)")
    post = risultati[0]
    if post.get("error"):
        raise ErroreSkill(f"Apify: {post.get('errorDescription') or post['error']}")
    if not post.get("videoUrl"):
        raise ErroreSkill(f"Il post non è un video (tipo: {post.get('type', 'sconosciuto')})")
    dati = {
        "account": post.get("ownerUsername"),
        "pubblicato": post.get("timestamp"),
        "didascalia": post.get("caption"),
        "hashtag": post.get("hashtags"),
        "like": post.get("likesCount"),
        "commenti": post.get("commentsCount"),
        "visualizzazioni": post.get("videoViewCount"),
        "riproduzioni": post.get("videoPlayCount"),
        "durata_s": post.get("videoDuration"),
        "copertina": post.get("displayUrl"),
    }
    return post["videoUrl"], dati


def scarica(url: str, destinazione: Path) -> None:
    """Scarica subito il video: i link dei CDN di Instagram scadono dopo qualche ora."""
    richiesta = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(richiesta, timeout=TIMEOUT_DOWNLOAD) as risposta:
            destinazione.write_bytes(risposta.read())
    except urllib.error.HTTPError as errore:
        raise ErroreSkill(f"Download del video non riuscito ({errore.code}): il link è scaduto?") from None
    except urllib.error.URLError as errore:
        raise ErroreSkill(f"Download del video non riuscito: {errore.reason}") from None
    if destinazione.stat().st_size == 0:
        raise ErroreSkill("Il video scaricato è vuoto")


# --- Fotogrammi ---------------------------------------------------------------

def _fine(durata: float) -> float:
    return round(max(durata - 0.1, 0.0), 2)


def tempi_fotogrammi(durata: float, modalita: str) -> list[float]:
    """Secondi dei fotogrammi da estrarre, in ordine e senza doppioni."""
    fine = _fine(durata)
    if modalita == "rapida":
        tempi = [0.0, 1.0, 2.0, 3.0, round(durata / 2, 2), fine]
        return sorted({t for t in tempi if t <= fine})
    if modalita != "completa":
        raise ValueError(f"Modalità sconosciuta: {modalita}")
    # Fitti nei primi 3 secondi (l'aggancio), poi uno ogni 2 secondi.
    iniziali = [t / 2 for t in range(7) if t / 2 <= fine]
    centrali, t = [], 5.0
    while t < fine - 1.0:  # niente fotogramma attaccato all'ultimo
        centrali.append(t)
        t += 2.0
    posti = MAX_FOTOGRAMMI - len(iniziali) - 1
    if len(centrali) > posti:
        passo = len(centrali) / posti
        centrali = [centrali[int(i * passo)] for i in range(posti)]
    return sorted(set(iniziali + centrali + [fine]))


def info_video(stderr_ffmpeg: str) -> dict:
    """Durata, risoluzione, fps e presenza dell'audio dall'output di `ffmpeg -i`."""
    durata = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", stderr_ffmpeg)
    video = re.search(r"Stream #.*Video:.*?(\d{2,5})x(\d{2,5})", stderr_ffmpeg)
    fps = re.search(r"Stream #.*Video:.*?([\d.]+) fps", stderr_ffmpeg)
    if not durata or not video:
        raise ErroreSkill("ffmpeg non riconosce il file come video")
    ore, minuti, secondi = durata.groups()
    return {
        "durata_s": round(int(ore) * 3600 + int(minuti) * 60 + float(secondi), 2),
        "larghezza": int(video.group(1)),
        "altezza": int(video.group(2)),
        "fps": float(fps.group(1)) if fps else None,
        "audio": bool(re.search(r"Stream #.*Audio:", stderr_ffmpeg)),
    }


def nome_fotogramma(indice: int, secondi: float) -> str:
    return f"{indice + 1:02d}_t{secondi:06.2f}s.jpg"


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        raise ErroreSkill("Manca imageio-ffmpeg: pip install imageio-ffmpeg") from None
    return imageio_ffmpeg.get_ffmpeg_exe()


def leggi_info(video: Path) -> dict:
    uscita = subprocess.run([_ffmpeg(), "-hide_banner", "-i", str(video)], capture_output=True, text=True)
    return info_video(uscita.stderr)


def estrai_fotogrammi(video: Path, cartella: Path, tempi: list[float], larghezza: int) -> list[dict]:
    cartella.mkdir(parents=True, exist_ok=True)
    estratti = []
    for i, t in enumerate(tempi):
        file = cartella / nome_fotogramma(i, t)
        # Vicino alla fine ffmpeg a volte non trova un fotogramma: si riprova un po' prima.
        for prova in (t, max(t - 0.5, 0.0)):
            subprocess.run(
                [_ffmpeg(), "-v", "error", "-y", "-ss", f"{prova:.2f}", "-i", str(video), "-frames:v", "1",
                 "-vf", f"scale={larghezza}:-2", "-q:v", "3", str(file)],
                capture_output=True,
            )
            if file.exists() and file.stat().st_size > 0:
                estratti.append({"file": f"frames/{file.name}", "secondi": round(prova, 2)})
                break
    if not estratti:
        raise ErroreSkill("Nessun fotogramma estratto")
    return estratti


def colonne_griglia(numero: int) -> tuple[int, int]:
    colonne = min(numero, 6)
    return colonne, -(-numero // colonne)


def crea_griglia(cartella: Path, fotogrammi: list[dict]) -> None:
    """griglia.jpg: tutti i fotogrammi piccoli in un'immagine sola, per una prima occhiata."""
    elenco = cartella / "frames" / "elenco.txt"
    elenco.write_text("ffconcat version 1.0\n" + "".join(
        f"file '{Path(f['file']).name}'\nduration 1\n" for f in fotogrammi), encoding="utf-8")
    colonne, righe = colonne_griglia(len(fotogrammi))
    subprocess.run([_ffmpeg(), "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(elenco),
                    "-vf", f"scale=240:-2,tile={colonne}x{righe}", "-frames:v", "1", "-q:v", "3",
                    str(cartella / "griglia.jpg")], capture_output=True)
    elenco.unlink()


# --- Trascrizione -------------------------------------------------------------

def testo_trascrizione(segmenti, lingua, probabilita) -> str:
    if segmenti is None:
        return "Nessuna traccia audio nel video.\n"
    righe = [f"[{s.start:.1f} s - {s.end:.1f} s] {s.text.strip()}" for s in segmenti if s.text.strip()]
    if not righe:
        return "Nessun parlato rilevato.\n"
    return f"Lingua rilevata: {lingua} (probabilità {probabilita:.2f})\n" + "\n".join(righe) + "\n"


def trascrivi(video: Path, audio: bool) -> tuple[str, dict]:
    if not audio:
        return testo_trascrizione(None, None, None), {"lingua": None, "probabilita_lingua": None}
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ErroreSkill("Manca faster-whisper: pip install faster-whisper") from None
    import numpy as np
    # L'audio si decodifica con lo stesso ffmpeg dei fotogrammi (16 kHz, mono): così non serve PyAV,
    # che in alcune versioni non va d'accordo con faster-whisper.
    pcm = subprocess.run([_ffmpeg(), "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    campioni = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    modello = WhisperModel(MODELLO_WHISPER, device="cpu", compute_type="int8")
    # Il filtro VAD toglie i tratti senza voce, dove Whisper tende a inventare frasi.
    segmenti, info = modello.transcribe(campioni, vad_filter=True)
    segmenti = list(segmenti)
    parlato = any(s.text.strip() for s in segmenti)
    return (testo_trascrizione(segmenti, info.language, info.language_probability),
            {"lingua": info.language if parlato else None,
             "probabilita_lingua": round(info.language_probability, 2) if parlato else None})


# --- Verifica dell'analisi ----------------------------------------------------

def errori_analisi(analisi: dict) -> list[str]:
    """Controlla che analisi.json abbia i campi fissi; restituisce gli errori trovati."""
    errori = [f"manca il campo {c}" for c in CAMPI_ANALISI if c not in analisi]
    errori += [f"campo non previsto: {c}" for c in analisi if c not in CAMPI_ANALISI]
    for campo in CAMPI_TESTO:
        if campo in analisi and not (isinstance(analisi[campo], str) and analisi[campo].strip()):
            errori.append(f"{campo}: serve un testo (se il dato manca, scrivi 'manca' e perché)")
    if "note" in analisi and not isinstance(analisi["note"], str):
        errori.append("note: serve un testo, anche vuoto")
    testi = analisi.get("testi_a_schermo", [])
    if not (isinstance(testi, list) and all(isinstance(t, str) for t in testi)):
        errori.append("testi_a_schermo: serve un elenco di testi (vuoto se non ce ne sono)")
    qualita = analisi.get("qualita_video", {})
    if "qualita_video" in analisi:
        if not isinstance(qualita, dict):
            errori.append("qualita_video: serve un oggetto con voto e motivo")
        else:
            voto = qualita.get("voto")
            if voto is not None and (not isinstance(voto, int) or not 1 <= voto <= 5):
                errori.append("qualita_video.voto: da 1 a 5, oppure null se non giudicabile")
            if not (isinstance(qualita.get("motivo"), str) and qualita["motivo"].strip()):
                errori.append("qualita_video.motivo: serve un testo")
    return errori


# --- Comandi ------------------------------------------------------------------

def prepara(arg) -> int:
    sorgente = riconosci_sorgente(arg.sorgente, arg.video_url, arg.codice)
    cartella = Path(arg.uscita) / sorgente.codice
    cartella.mkdir(parents=True, exist_ok=True)
    video = cartella / "video.mp4"
    post, origine = None, sorgente.tipo
    if arg.post:
        video_url, post = post_da_file(arg.post)
        scarica(video_url, video)
        origine = "apify (connettore)"
    elif sorgente.tipo == "instagram":
        video_url, post = post_da_apify(sorgente.valore, token_apify())
        scarica(video_url, video)
        origine = "apify"
    elif sorgente.tipo == "video_url":
        scarica(sorgente.valore, video)
    else:
        video = Path(sorgente.valore)
    info = leggi_info(video)
    tempi = tempi_fotogrammi(info["durata_s"], arg.modalita)
    frames = cartella / "frames"
    for vecchio in frames.glob("*.jpg"):  # una nuova preparazione sostituisce i fotogrammi
        vecchio.unlink()
    fotogrammi = estrai_fotogrammi(video, frames, tempi, MODALITA[arg.modalita])
    crea_griglia(cartella, fotogrammi)
    trascrizione, lingua = trascrivi(video, info["audio"])
    (cartella / "trascrizione.txt").write_text(trascrizione, encoding="utf-8")
    meta = {
        "codice": sorgente.codice,
        "link_instagram": sorgente.link,
        "origine": origine,  # apify, apify (connettore), video_url o file
        "file_video": str(video if sorgente.tipo == "file" else video.relative_to(cartella)),
        "preparato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modalita": arg.modalita,
        **info,
        **lingua,
        "modello_trascrizione": f"faster-whisper {MODELLO_WHISPER}",
        "fotogrammi": fotogrammi,
        "post": post,  # dati del post da Apify; null se il video non viene da Apify
    }
    (cartella / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Pronto: {cartella}/ ({len(fotogrammi)} fotogrammi, {info['durata_s']} s, "
          f"{trascrizione.splitlines()[0]})")
    return 0


def verifica(arg) -> int:
    try:
        analisi = json.loads(Path(arg.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as errore:
        raise ErroreSkill(f"{arg.file}: {errore}") from None
    if not isinstance(analisi, dict):
        raise ErroreSkill(f"{arg.file}: serve un oggetto JSON")
    errori = errori_analisi(analisi)
    for e in errori:
        print(f"ERRORE: {e}")
    if not errori:
        print("Analisi valida")
    return 1 if errori else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prepara un video di Instagram per l'analisi.")
    comandi = parser.add_subparsers(dest="comando", required=True)
    p = comandi.add_parser("prepara", help="scarica il video, estrae fotogrammi e trascrizione")
    p.add_argument("sorgente", help="link Instagram, link diretto al video o file video")
    p.add_argument("--modalita", choices=MODALITA, default="rapida")
    p.add_argument("--video-url", help="link diretto al video già pronto (salta Apify)")
    p.add_argument("--post", help="file JSON con il post letto dal connettore Apify (salta la chiave)")
    p.add_argument("--codice", help="nome della cartella di uscita")
    p.add_argument("--uscita", default="analisi", help="cartella che contiene le analisi")
    v = comandi.add_parser("verifica", help="controlla i campi di analisi.json")
    v.add_argument("file")
    arg = parser.parse_args(argv)
    try:
        return prepara(arg) if arg.comando == "prepara" else verifica(arg)
    except (ErroreSkill, ValueError) as errore:
        print(f"ERRORE: {errore}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
