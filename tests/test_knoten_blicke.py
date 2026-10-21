"""Gesicherte Blicke der Mappe für den Knoten «Kamera» (Video-Befund L4-4, 21.10.2026).

Der Knoten «Kamera» bietet gesicherte Blicke als Auswahl an (Reiter «Blick»), ohne 3D-Ansicht. In
Visbox sind das die von Hand gesetzten Standpunkte der Bilder (``herkunft.standpunkt`` mit Auge
und Blickpunkt). ``/knoten/mappe`` nennt sie unter ``blicke``. Alle Namen und Zahlen sind erfunden.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import arbeitsgang, knotenweg, projekt
from aiimaging.kameras import BRENNWEITE_MM

from test_modell_laden import _glb


def _mappe(tmp_path) -> Path:
    quelle = tmp_path / "Bau.glb"
    quelle.write_bytes(_glb())
    mappe = tmp_path / "mappen" / "Bau"
    arbeitsgang.lege_an(mappe, quelle)
    return mappe


def _bild(p, bild, erzeugt, standpunkt, titel=None):
    p.setdefault("bilder", []).append({"bild": bild, "erzeugt": erzeugt, "titel": titel,
                                       "herkunft": {"standpunkt": standpunkt}})


def test_nur_gesetzte_standpunkte_der_neueste_zuerst_und_jeder_einmal():
    p: dict = {}
    _bild(p, "bilder/a.png", "2026-10-15T08:00:00Z", {"auge": [10, -20, 1.6], "blick_auf": [0, 0, 4], "brennweite": 28})
    _bild(p, "bilder/b.png", "2026-10-15T09:00:00Z", {"kamera": "s"})  # aus einer Richtung: kein Blick
    _bild(p, "bilder/c.png", "2026-10-15T10:00:00Z", {"auge": [10, -20, 1.6], "blick_auf": [0, 0, 4], "brennweite": 28},
          titel="Ecke SO/SW")
    _bild(p, "bilder/d.png", "2026-10-15T11:00:00Z", {"auge": [-5, 8, 1.7], "blick_auf": [0, 0, 3]})
    blicke = knotenweg.blicke_der_mappe(p)
    assert [b["name"] for b in blicke] == ["d", "Ecke SO/SW"]
    assert blicke[1] == {"id": "bild:bilder/c.png", "name": "Ecke SO/SW", "bild": "bilder/c.png", "auge": [10.0, -20.0, 1.6],
                         "blick_auf": [0.0, 0.0, 4.0], "brennweite_mm": 28.0, "erzeugt": "2026-10-15T10:00:00Z"}
    # Ohne Brennweite am Bild: die, mit der der Heim-PC gerechnet hat — nicht geraten.
    assert blicke[0]["brennweite_mm"] == BRENNWEITE_MM


def test_die_kennung_bleibt_wenn_der_titel_sich_aendert():
    p: dict = {}
    _bild(p, "bilder/a.png", "2026-10-15T08:00:00Z", {"auge": [1, 2, 1.6], "blick_auf": [0, 0, 1]}, titel="Hof")
    vorher = knotenweg.blicke_der_mappe(p)[0]["id"]
    p["bilder"][0]["titel"] = "Hof von Westen"
    nachher = knotenweg.blicke_der_mappe(p)[0]
    assert nachher["id"] == vorher == "bild:bilder/a.png"
    assert nachher["name"] == "Hof von Westen"


def test_gleiche_namen_bekommen_eine_nummer_und_unlesbares_faellt_weg():
    p: dict = {}
    _bild(p, "bilder/x.png", "2026-10-15T08:00:00Z", {"auge": [1, 2, 1.6], "blick_auf": [0, 0, 1]}, titel="Hof")
    _bild(p, "bilder/y.png", "2026-10-15T09:00:00Z", {"auge": [3, 2, 1.6], "blick_auf": [0, 0, 1]}, titel="Hof")
    _bild(p, "bilder/z.png", "2026-10-15T10:00:00Z", {"auge": [1, "2", 1.6], "blick_auf": [0, 0, 1]})
    p["bilder"].append("kein Eintrag")
    assert [b["name"] for b in knotenweg.blicke_der_mappe(p)] == ["Hof", "Hof (2)"]


def test_die_mappe_nennt_sie_auch_ohne_modell(tmp_path):
    mappe = _mappe(tmp_path)
    assert knotenweg.mappe_fuer_knoten(mappe)["blicke"] == []
    p = projekt.oeffne(mappe)["projekt"]
    _bild(p, "bilder/a.png", "2026-10-15T08:00:00Z", {"auge": [10, -20, 1.6], "blick_auf": [0, 0, 4]}, titel="Gartenblick")
    projekt.speichere(p, mappe)
    assert [b["name"] for b in knotenweg.mappe_fuer_knoten(mappe)["blicke"]] == ["Gartenblick"]
