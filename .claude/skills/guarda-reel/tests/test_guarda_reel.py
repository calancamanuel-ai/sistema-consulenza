"""Test della skill guarda-reel: niente rete, niente ffmpeg, niente Whisper."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import guarda_reel as gr  # noqa: E402


# --- Sorgente -----------------------------------------------------------------

@pytest.mark.parametrize("testo, codice", [
    ("https://www.instagram.com/reel/DfzCerJhXOx/", "DfzCerJhXOx"),
    ("https://instagram.com/reel/DfzCerJhXOx/?igsh=abc", "DfzCerJhXOx"),
    ("https://www.instagram.com/p/DfrUGHskZUx/", "DfrUGHskZUx"),
    ("https://www.instagram.com/tv/Abc_-123/", "Abc_-123"),
    ("https://www.instagram.com/officina/reel/DfzCerJhXOx/", "DfzCerJhXOx"),
])
def test_link_instagram(testo, codice):
    s = gr.riconosci_sorgente(testo)
    assert (s.tipo, s.codice) == ("instagram", codice)
    assert s.valore == f"https://www.instagram.com/reel/{codice}/"


def test_file_locale(tmp_path):
    video = tmp_path / "Il mio reel.mp4"
    video.write_bytes(b"x")
    s = gr.riconosci_sorgente(str(video))
    assert (s.tipo, s.codice, s.valore) == ("file", "Il-mio-reel", str(video))


def test_video_url_diretto():
    s = gr.riconosci_sorgente("https://scontent.cdninstagram.com/o1/v/t16/f2/m86/abc.mp4?efg=1")
    assert s.tipo == "video_url"
    assert s.codice.startswith("video-") and len(s.codice) == len("video-") + 10


def test_video_url_con_codice_dato():
    s = gr.riconosci_sorgente("https://cdn.example.invalid/a.mp4", codice="DfzCerJhXOx")
    assert (s.tipo, s.codice) == ("video_url", "DfzCerJhXOx")


def test_link_instagram_con_video_url_salta_apify():
    s = gr.riconosci_sorgente("https://www.instagram.com/reel/DfzCerJhXOx/",
                              video_url="https://cdn.example.invalid/a.mp4")
    assert (s.tipo, s.codice, s.valore) == ("video_url", "DfzCerJhXOx", "https://cdn.example.invalid/a.mp4")
    assert s.link == "https://www.instagram.com/reel/DfzCerJhXOx/"


@pytest.mark.parametrize("testo", ["", "ciao", "https://www.instagram.com/officina/", "/non/esiste.mp4"])
def test_sorgente_non_valida(testo):
    with pytest.raises(ValueError):
        gr.riconosci_sorgente(testo)


# --- Apify --------------------------------------------------------------------

class FintoHttp:
    def __init__(self, risposta):
        self.risposta = risposta
        self.richieste = []

    def __call__(self, url, corpo, intestazioni, timeout):
        self.richieste.append({"url": url, "corpo": corpo, "intestazioni": intestazioni, "timeout": timeout})
        return self.risposta


POST_APIFY = {
    "type": "Video",
    "shortCode": "DfzCerJhXOx",
    "url": "https://www.instagram.com/p/DfzCerJhXOx/",
    "caption": "Prima e dopo #nails",
    "hashtags": ["nails"],
    "ownerUsername": "studio_esempio",
    "timestamp": "2026-11-16T10:00:00.000Z",
    "likesCount": 32,
    "commentsCount": 0,
    "videoViewCount": 4280,
    "videoPlayCount": 9000,
    "videoDuration": 14.2,
    "videoUrl": "https://cdn.example.invalid/v.mp4",
    "displayUrl": "https://cdn.example.invalid/c.jpg",
}


def test_richiesta_apify():
    http = FintoHttp([POST_APIFY])
    gr.post_da_apify("https://www.instagram.com/reel/DfzCerJhXOx/", "token-finto", http)
    [r] = http.richieste
    assert r["url"] == ("https://api.apify.com/v2/acts/apify~instagram-scraper/"
                        "run-sync-get-dataset-items")
    assert json.loads(r["corpo"]) == {
        "directUrls": ["https://www.instagram.com/reel/DfzCerJhXOx/"],
        "resultsType": "posts",
        "resultsLimit": 1,
    }
    assert r["intestazioni"]["Authorization"] == "Bearer token-finto"
    assert "token-finto" not in r["url"]


def test_post_apify_restituisce_video_e_dati():
    video_url, dati = gr.post_da_apify("https://www.instagram.com/reel/X/", "t", FintoHttp([POST_APIFY]))
    assert video_url == "https://cdn.example.invalid/v.mp4"
    assert dati == {
        "account": "studio_esempio",
        "pubblicato": "2026-11-16T10:00:00.000Z",
        "didascalia": "Prima e dopo #nails",
        "hashtag": ["nails"],
        "like": 32,
        "commenti": 0,
        "visualizzazioni": 4280,
        "riproduzioni": 9000,
        "durata_s": 14.2,
        "copertina": "https://cdn.example.invalid/c.jpg",
    }


@pytest.mark.parametrize("risposta, errore", [
    ([], "nessun risultato"),
    ([{"error": "not_found", "errorDescription": "Post non trovato"}], "Post non trovato"),
    ([{"type": "Image", "displayUrl": "x"}], "non è un video"),
])
def test_errori_apify(risposta, errore):
    with pytest.raises(gr.ErroreSkill, match=errore):
        gr.post_da_apify("https://www.instagram.com/reel/X/", "t", FintoHttp(risposta))


def test_token_mancante():
    with pytest.raises(gr.ErroreSkill, match="APIFY_TOKEN"):
        gr.token_apify({})


# --- Fotogrammi ---------------------------------------------------------------

def test_tempi_rapida():
    assert gr.tempi_fotogrammi(30.0, "rapida") == [0.0, 1.0, 2.0, 3.0, 15.0, 29.9]


def test_tempi_rapida_video_corto():
    assert gr.tempi_fotogrammi(2.5, "rapida") == [0.0, 1.0, 1.25, 2.0, 2.4]


def test_tempi_completa():
    tempi = gr.tempi_fotogrammi(15.0, "completa")
    assert tempi == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 14.9]


def test_tempi_completa_senza_doppione_finale():
    assert gr.tempi_fotogrammi(11.24, "completa")[-3:] == [7.0, 9.0, 11.14]


def test_tempi_completa_massimo_venti():
    tempi = gr.tempi_fotogrammi(90.0, "completa")
    assert len(tempi) == 20
    assert tempi[:7] == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    assert tempi[-1] == 89.9
    assert tempi == sorted(set(tempi))


def test_dimensione_per_modalita():
    assert gr.MODALITA == {"rapida": 512, "completa": 768}


def test_info_ffmpeg():
    stderr = (
        "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':\n"
        "  Duration: 00:00:14.23, start: 0.000000, bitrate: 1520 kb/s\n"
        "  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, bt709, progressive),"
        " 720x1280 [SAR 1:1 DAR 9:16], 1386 kb/s, 30 fps, 30 tbr, 15360 tbn (default)\n"
        "  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 128 kb/s\n"
    )
    assert gr.info_video(stderr) == {"durata_s": 14.23, "larghezza": 720, "altezza": 1280,
                                     "fps": 30.0, "audio": True}


def test_info_ffmpeg_senza_audio():
    stderr = ("  Duration: 00:01:02.50, start: 0.0\n"
              "  Stream #0:0: Video: h264, yuv420p, 1080x1920, 25 fps\n")
    assert gr.info_video(stderr) == {"durata_s": 62.5, "larghezza": 1080, "altezza": 1920,
                                     "fps": 25.0, "audio": False}


@pytest.mark.parametrize("numero, attese", [(6, (6, 1)), (12, (6, 2)), (13, (6, 3)), (20, (6, 4)), (3, (3, 1))])
def test_colonne_griglia(numero, attese):
    assert gr.colonne_griglia(numero) == attese


def test_nome_fotogramma():
    assert gr.nome_fotogramma(3, 2.5) == "04_t002.50s.jpg"


# --- Trascrizione -------------------------------------------------------------

class Segmento:
    def __init__(self, start, end, text):
        self.start, self.end, self.text = start, end, text


def test_testo_trascrizione():
    testo = gr.testo_trascrizione([Segmento(0.0, 2.44, " Ciao a tutti"), Segmento(2.5, 5.0, "oggi ")],
                                  "it", 0.987)
    assert testo == ("Lingua rilevata: it (probabilità 0.99)\n"
                     "[0.0 s - 2.4 s] Ciao a tutti\n"
                     "[2.5 s - 5.0 s] oggi\n")


def test_trascrizione_senza_parlato():
    assert gr.testo_trascrizione([Segmento(0, 1, "  ")], "en", 0.4) == "Nessun parlato rilevato.\n"


def test_trascrizione_senza_audio():
    assert gr.testo_trascrizione(None, None, None) == "Nessuna traccia audio nel video.\n"


# --- Verifica dell'analisi ----------------------------------------------------

ANALISI = {
    "codice": "DfzCerJhXOx",
    "hook": "Prima e dopo delle unghie nei primi 2 secondi",
    "cosa_si_vede": "Mani in primo piano, luce buona",
    "cosa_si_dice": "manca: nessun parlato",
    "testi_a_schermo": ["Prima", "Dopo"],
    "call_to_action": "manca",
    "qualita_video": {"voto": 4, "motivo": "Luce e fuoco buoni"},
    "note": "",
    "riassunto": "Reel prima/dopo curato, senza invito all'azione.",
}


def test_analisi_valida():
    assert gr.errori_analisi(ANALISI) == []


def test_analisi_voto_nullo_se_non_giudicabile():
    assert gr.errori_analisi({**ANALISI, "qualita_video": {"voto": None, "motivo": "manca: video illeggibile"}}) == []


@pytest.mark.parametrize("modifica, errore", [
    ({"hook": None}, "hook"),
    ({"riassunto": ""}, "riassunto"),
    ({"testi_a_schermo": "Prima"}, "testi_a_schermo"),
    ({"qualita_video": {"voto": 6, "motivo": "x"}}, "voto"),
    ({"qualita_video": {"voto": 3}}, "motivo"),
    ({"extra": 1}, "extra"),
])
def test_analisi_non_valida(modifica, errore):
    analisi = {**ANALISI, **modifica}
    if modifica.get("hook", 0) is None:
        del analisi["hook"]
    assert any(errore in e for e in gr.errori_analisi(analisi))
