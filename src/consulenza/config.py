"""Lettura dei file in config/."""
from dataclasses import dataclass
from pathlib import Path

import yaml

CARTELLA = Path(__file__).resolve().parents[2] / "config"


@dataclass(frozen=True)
class Zona:
    nome: str
    lat: float
    lng: float
    raggio_m: int


def _leggi(percorso: Path) -> dict:
    with open(percorso, encoding="utf-8") as f:
        return yaml.safe_load(f)


def carica_zone(percorso: Path = CARTELLA / "zone.yaml") -> list[Zona]:
    return [
        Zona(z["nome"], float(z["lat"]), float(z["lng"]), int(z["raggio_m"]))
        for z in _leggi(percorso)["zone"]
    ]


def carica_punteggio(percorso: Path = CARTELLA / "punteggio.yaml") -> dict:
    return _leggi(percorso)
