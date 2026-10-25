"""Marke «freies Bild» ganz sichtbar — Befund Int 1, Geräteprobe R70 (Protokoll 74 §292).

Die Marke war abgeschnitten: am Knoten «Aufs Blatt» ragte sie hinter Knopf, «Vorschau» und Modus-Marke aus dem
38-px-Körper, auf der Kuratier-Karte lag sie ausserhalb der Karte, im Vergleich lagen die drei Marken
übereinander (gemessen in KosmoOrbit, E2E ``kv-freies-bild-marke-ganz``). Grundlage: «nichts abgeschnitten, nichts
verdeckt» und Entscheid 149 (ein freies Bild trägt seine Marke ganz).

Zwei Teile: die **Messprobe** am eingecheckten Stil (``tools/freies_bild_marke_probe.py``, Chromium, normale und
grosse Schrift; am alten Stil 4 Funde auf der Karte) und der **Aufbau** in der Kopie.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


def _probe():
    spec = importlib.util.spec_from_file_location("freies_bild_marke_probe",
                                                  WURZEL / "tools" / "freies_bild_marke_probe.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _chromium_fehlt() -> bool:
    try:
        _probe().chromium()
    except SystemExit:
        return True
    return False


@pytest.mark.skipif(_chromium_fehlt(), reason="Chromium fehlt")
def test_marke_ganz_auf_blatt_karte_und_vergleich():
    ergebnis = _probe().pruefe()
    assert ergebnis["stil"], "der Stil des Baus wurde nicht geladen"
    assert len(ergebnis["gesehen"]) == 6, ergebnis
    assert ergebnis["fehler"] == []


def test_aufbau_in_der_kopie():
    canvas = (VIS / "NodeCanvas.tsx").read_text(encoding="utf-8")
    blatt = canvas[canvas.index("case 'blatt': {"):canvas.index("case 'referenz': {")]
    marken = blatt[blatt.index('className="vis-node-blatt-marken"'):]
    assert '<FreiesBildMarke lauf={quelle} testid="blatt-freies-bild-marke" form="abzeichen" />' in marken
    zeile = blatt[blatt.index('className="vis-node-blatt-zeile"'):blatt.index('className="vis-node-blatt-marken"')]
    assert "FreiesBildMarke" not in zeile and "GueteMarke" not in zeile          # nicht mehr in der Knopfzeile
    assert re.search(r"blatt: 38 \+ BLATT_MARKEN_H,", canvas)
    assert int(re.search(r"export const BLATT_MARKEN_H = (\d+);", canvas).group(1)) >= 3 * 17
    kur = (VIS / "KuratierFlaeche.tsx").read_text(encoding="utf-8")
    leiste = kur[kur.index('<div className="vis-marken-leiste">'):]
    assert leiste.index("vis-kuratier-vergleich-freies-bild-marke") < leiste.index("</div>")
    css = (VIS / "vis-visual.css").read_text(encoding="utf-8")
    rechts = css[css.index(".vis-raster-karte-embleme-rechts {"):]
    rechts = rechts[:rechts.index("}")]
    assert "flex-wrap: wrap;" in rechts and "justify-content: flex-end;" in rechts
    assert ".vis-node-blatt-marken {" in css
