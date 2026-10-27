"""Marke «freies Bild» ganz sichtbar — Befund Int 1, Geräteprobe R70 (Protokoll 74 §292).

Die Marke war abgeschnitten: am Knoten «Aufs Blatt» ragte sie hinter Knopf, «Vorschau» und Modus-Marke aus dem
38-px-Körper, auf der Kuratier-Karte lag sie ausserhalb der Karte, im Vergleich lagen die drei Marken
übereinander (gemessen in KosmoOrbit, E2E ``kv-freies-bild-marke-ganz``). Grundlage: «nichts abgeschnitten, nichts
verdeckt» und Entscheid 149 (ein freies Bild trägt seine Marke ganz).

Zwei Teile: die **Messprobe** am eingecheckten Stil (``tools/freies_bild_marke_probe.py``, Chromium, normale und
grosse Schrift; am alten Stil 4 Funde auf der Karte) und der **Aufbau** in der Kopie.

Seit 27.10.2026 auch der 96 × 60-Daumen des Varianten-Knotens (KosmoOrbit 112f3b495, Befund Geräteprobe R73): dort
brach «Grundlagenbild» mitten im Wort. Die Modus-Marke steht am Daumen als Symbol (Wortlaut im aria-label), die
Markenleiste bricht nur an Wortgrenzen; die Probe misst je Wort und prüft, dass sich keine Marken überlappen. Am
alten Bau mit Textform: «Wort «Grundlagenbild» ist zerbrochen» und abgeschnittene Marken.
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
def test_marke_ganz_auf_blatt_karte_vergleich_und_daumen():
    ergebnis = _probe().pruefe()
    assert ergebnis["stil"], "der Stil des Baus wurde nicht geladen"
    # Sechs Flächen (Blatt, Karte, Vergleich, Daumen, seit 373 S12 Raster und grosse Ansicht) × zwei Schriftgrössen.
    assert len(ergebnis["gesehen"]) == 12, ergebnis
    assert ergebnis["fehler"] == []
    # Offen bei KosmoOrbit (wörtlich übernommen, E115): das Symbol am Daumen liegt in der zeigerdurchlässigen
    # Markenleiste und nimmt den Zeiger nicht — seine eigene Kurzhilfe erreicht die Maus nicht (die des Daumens
    # nennt den Wortlaut). Die Probe meldet es als Hinweis; sobald KosmoOrbit es löst, fällt die Liste leer.
    assert all("daumen-modus" in z for z in ergebnis["zeiger"]), ergebnis["zeiger"]


def test_daumen_modus_als_symbol_in_der_kopie():
    daumen = (VIS / "VariantenDaumen.tsx").read_text(encoding="utf-8")
    assert '<ModusMarke lauf={zelle} testid="varianten-daumen-modus" form="symbol" />' in daumen
    assert _probe().daumen_modus_form() == "symbol"
    marke = (VIS / "ModusMarke.tsx").read_text(encoding="utf-8")
    assert "form?: 'bild' | 'abzeichen' | 'zeile' | 'symbol';" in marke
    assert 'role="img" aria-label={MODUS_MARKE_TEXT[art]}' in marke
    css = (VIS / "vis-visual.css").read_text(encoding="utf-8")
    leiste = css[css.index(".vis-marken-leiste .vis-modus-marke {"):]
    leiste = leiste[:leiste.index("}")]
    assert "overflow-wrap: normal;" in leiste and "hyphens: none;" in leiste
    assert "overflow-wrap: anywhere" not in leiste


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


def test_s12_marke_im_bildvergleich_und_vor_dem_bild():
    """Generalprobe 373 (S12): im Bildvergleich (Raster) fehlte die Marke, in der grossen Ansicht lag sie halb hinter
    der Fusszeile. Jetzt steht sie über dem Raster und in den grossen Ansichten VOR dem Bild."""
    raster = (VIS / "VariantenRaster.tsx").read_text(encoding="utf-8")
    assert '<FreiesBildMarke lauf={{ freiesBild: true }} testid="varianten-raster-freies-bild" form="abzeichen" />' in raster
    assert raster.index('testid="varianten-raster-gross-freies-bild"') < raster.index('<BridgeBild jobId={gross.jobId}')
    daumen = (VIS / "VariantenDaumen.tsx").read_text(encoding="utf-8")
    assert daumen.index('testid="varianten-daumen-gross-freies-bild"') < daumen.index('className="vis-gross-bild-hoch vis-gross-bild-block"')
    css = (VIS / "vis-visual.css").read_text(encoding="utf-8")
    assert ".vis-raster-oben {" in css and ".vis-gross-marken-oben {" in css
