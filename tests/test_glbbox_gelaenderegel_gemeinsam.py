"""A0267: Die Geländeregel der Hüllbox ist am Heim-PC (Python) und am Mac (Swift) dieselbe.

Beide Seiten lesen dieselbe Probendatei (``tests/daten/glbbox_gelaenderegel.json``, erzeugt von
``tools/glbbox_proben.py``). Diese Datei prüft die Python-Seite und, dass die Swift-Seite ihre
Wortlisten nicht stillschweigend von ``maske`` entfernt; die Swift-Seite prüft
``GlbauskunftGelaendeTests``.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from aiimaging import glbbox, maske

WURZEL = Path(__file__).resolve().parents[1]
DATEI = WURZEL / "tests" / "daten" / "glbbox_gelaenderegel.json"
SWIFT = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Modelltausch.swift"


def _werkzeug():
    spez = importlib.util.spec_from_file_location("glbbox_proben", WURZEL / "tools" / "glbbox_proben.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


DATEN = json.loads(DATEI.read_text(encoding="utf-8"))
FAELLE = DATEN["faelle"]


def test_die_probendatei_passt_zum_kern():
    """Ändert sich die Regel, muss die Datei neu erzeugt werden, sonst prüft Swift Altes."""
    assert json.loads(json.dumps(_werkzeug().erzeuge())) == DATEN, (
        "tests/daten/glbbox_gelaenderegel.json ist veraltet: python tools/glbbox_proben.py --schreiben")


def test_die_fallnamen_decken_die_drei_auftragsfaelle():
    namen = {f["fall"] for f in FAELLE}
    assert {"haus-am-hang", "ohne-gelaende", "alles-gelaende"} <= namen


@pytest.mark.parametrize("fall", FAELLE, ids=[f["fall"] for f in FAELLE])
def test_jeder_fall_ist_eine_namensentscheidung(fall, tmp_path):
    """Die Form (``gelaendeform``) liest der Mac nicht; kein Fall darf von ihr abhängen."""
    p = tmp_path / "probe.glb"
    _werkzeug().schreibe_glb(fall["glb"], p)
    aus = glbbox.bauwerksbox(p)
    assert aus["entschieden_durch"] in ("name", "keine"), fall["fall"]
    soll = fall["erwartet"]
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    for ist_e, soll_e in zip(box, soll["huellbox"]):
        assert ist_e == pytest.approx(soll_e, abs=DATEN["toleranz_m"])
    assert aus["n_gelaende"] == soll["gelaendeKnoten"]
    assert aus["n_knoten"] == soll["bauteile"]


def test_haus_am_hang_ist_nicht_mehr_60_mal_50():
    f = next(f for f in FAELLE if f["fall"] == "haus-am-hang")["erwartet"]
    (x0, y0, _), (x1, y1, z1) = f["huellbox"]
    assert (x1 - x0, y1 - y0) == pytest.approx((30.5, 27.7))
    assert z1 == pytest.approx(9.1)
    (sx0, sy0, _), (sx1, sy1, _) = f["szenenbox"]
    assert (sx1 - sx0, sy1 - sy0) == pytest.approx((60.0, 50.0))


def test_der_mac_fuehrt_dieselben_woerter_und_muster_wie_maske():
    """Die Swift-Listen sind ein Abbild; sie stehen hier gegen ``maske`` fest."""
    text = SWIFT.read_text(encoding="utf-8")

    def liste(name):
        m = re.search(name + r"[^=]*=\s*\[(.*?)\]", text, re.S)
        assert m, name
        return re.findall(r'"([^"]*)"', m.group(1))

    assert tuple(liste("gelaendeMuster")) == maske.GELAENDE_MUSTER
    assert set(liste("gelaendeWoerter")) == set(maske.GELAENDE_WOERTER)
    assert maske._WORTTRENNER.pattern == r"[\s_\-.,;:/\\()\[\]]+", (
        "der Worttrenner in maske hat sich geändert: Swift (wortTrenner) nachziehen")
