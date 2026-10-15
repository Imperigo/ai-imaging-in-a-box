"""Skizzen der Mappe für den Knoten «Skizze vom iPad» (Owner-Entscheide 95/95a, 14.10.2026, Blatt 25).

Die Knotenansicht ist die Arbeitsfläche zum Rendern (Entscheid 94); die Skizzen vom iPad standen
nur auf der Seite. Der Heim-PC nennt sie jetzt in ``/knoten/mappe`` — die neueste zuerst — und
liefert ihr Bild über ``/knoten/skizze?name=`` aus der Mappe der Knotenansicht.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import arbeitsgang, knotenweg, projekt

from test_modell_laden import _Server, _glb, server  # noqa: F401 — Probe-Wirt und Fixture

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
       b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84"
       b"\x00\x00\x00\x00IEND\xaeB`\x82")


def _mappe(tmp_path) -> Path:
    quelle = tmp_path / "Bau.glb"
    quelle.write_bytes(_glb())
    mappe = tmp_path / "mappen" / "Bau"
    arbeitsgang.lege_an(mappe, quelle)
    return mappe


def _skizze(mappe, name, erzeugt, stand=projekt.SKIZZE_OFFEN):
    (mappe / name).write_bytes(PNG)
    p = projekt.oeffne(mappe)["projekt"]
    projekt.vermerke_skizze(p, skizze=name, stand=stand)
    p["skizzen"][-1]["erzeugt"] = erzeugt
    projekt.speichere(p, mappe)


def test_die_neueste_zuerst_ohne_verworfene_und_jede_einmal(tmp_path):
    mappe = _mappe(tmp_path)
    _skizze(mappe, "skizze-a.png", "2026-10-14T08:00:00Z")
    _skizze(mappe, "skizze-b.png", "2026-10-14T10:00:00Z")
    _skizze(mappe, "skizze-c.png", "2026-10-14T09:00:00Z", stand=projekt.SKIZZE_VERWORFEN)
    # Dieselbe Zeichnung ein zweites Mal vermerkt (Zustandswechsel): es gilt der letzte Eintrag.
    _skizze(mappe, "skizze-a.png", "2026-10-14T11:00:00Z", stand=projekt.SKIZZE_GERECHNET)
    namen = [s["name"] for s in knotenweg.mappe_fuer_knoten(mappe)["skizzen"]]
    assert namen == ["skizze-a.png", "skizze-b.png"]
    liste = knotenweg.skizzen_der_mappe(projekt.oeffne(mappe)["projekt"], hoechstens=1)
    assert [s["name"] for s in liste] == ["skizze-a.png"]
    # kein Pfad; seit 15.10.2026 dazu Bemerkung (96a) und woher der Standpunkt kommt (96b)
    assert set(liste[0]) == {"name", "titel", "erzeugt", "ueber", "stand", "bemerkung",
                             "standpunkt"}


def test_ohne_skizzen_eine_leere_liste(tmp_path):
    assert knotenweg.mappe_fuer_knoten(_mappe(tmp_path))["skizzen"] == []


def test_der_weg_liefert_das_bild_aus_der_mappe_der_knoten(server, tmp_path):  # noqa: F811
    mappe = _mappe(tmp_path)
    _skizze(mappe, "skizze-a.png", "2026-10-14T08:00:00Z")
    s = _Server(server, mappe)
    code, roh = s.get(server.WEG_KNOTEN_SKIZZE + "?name=skizze-a.png")
    assert code == 200 and roh == PNG
    code, _ = s.get(server.WEG_KNOTEN_SKIZZE + "?name=../../etc/passwd")
    assert code == 404
    code, sicht = s.get(server.WEG_KNOTEN_MAPPE)
    assert code == 200 and sicht["skizzen"][0]["name"] == "skizze-a.png"
