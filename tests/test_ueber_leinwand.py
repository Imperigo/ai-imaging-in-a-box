"""Feste Bedienflächen nie hinter der Arbeitsfläche — bei keinem Zoom (Owner-Regel 24.10.2026).

Anlass: In Visbox 0.3.54 verschwand beim Zoomen in der Knotenansicht die Porttyp-Legende unten links
«hinter den Nodes». Gemessen (Protokoll 74): Die Legende lag im selben Stapel wie das Beiblatt am
Render-Knoten, eine Stufe darunter; das Beiblatt wandert mit dem Knoten. Behoben mit einer eigenen
Ebene über der Leinwand (``.vis-ueber-leinwand``), wortgleich mit KosmoVis.

Drei Teile:

* die **Trefferprobe** am eingecheckten Bau (``tools/ueber_leinwand_probe.py``): Chromium, Zoom 0,25 /
  0,5 / 1 / 2 / höchste, Knoten und Beiblatt unter jeder festen Fläche, ``elementFromPoint``;
* der **Bau** in der Kopie: Ebene, Stufe, Tafeleintrag;
* das **iPad**: dort zoomt nur die Zeichenleinwand, in ihrem Rahmen abgeschnitten — Leiste, Seitenfeld
  und Knöpfe liegen ausserhalb oder darüber. Der Wächter hält die Bauweise fest, die das sichert.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
KOPIE = WURZEL / "kosmovis"
CSS = KOPIE / "apps" / "kosmo-orbit" / "src" / "modules" / "vis" / "vis-visual.css"
LEINWAND = KOPIE / "apps" / "kosmo-orbit" / "src" / "modules" / "vis" / "NodeCanvas.tsx"
TAFEL = KOPIE / "packages" / "kosmo-ui" / "src" / "tokens.ts"
IPAD = WURZEL / "ipad" / "Visbox.swiftpm"


def _probe():
    spec = importlib.util.spec_from_file_location("ueber_leinwand_probe", WURZEL / "tools" / "ueber_leinwand_probe.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _chromium_fehlt() -> bool:
    try:
        _probe().chromium()
    except SystemExit:
        return True
    return False


def _block(text: str, selektor: str) -> str:
    m = re.search(r"(^|\n)" + re.escape(selektor) + r"\s*\{", text)
    assert m, f"Regel {selektor} fehlt"
    anfang = text.index("{", m.start())
    return text[anfang:text.index("}", anfang) + 1]


# ------------------------------------------------------------------ die Trefferprobe


@pytest.mark.skipif(_chromium_fehlt(), reason="Chromium fehlt")
def test_feste_flaechen_bleiben_bei_jedem_zoom_vorn():
    """Am eingecheckten Bau: an jeder festen Fläche trifft der Zeiger die Fläche, nicht den Knoten
    oder das Beiblatt darunter — bei 0,25 / 0,5 / 1 / 2 / höchster Stufe. Vor dem Fix: fünf Funde
    (die Legende hinter dem Beiblatt, bei jeder Stufe)."""
    ergebnis = _probe().pruefe()
    assert ergebnis["fehler"] == []
    assert "Porttyp-Legende" in ergebnis["flaechen"] and "Kuratier-Knopf" in ergebnis["flaechen"]
    assert len(ergebnis["stufen"]) == 5 and ergebnis["stufen"][0] < 0.3 and ergebnis["stufen"][-1] > 2
    # Je Stufe jede Fläche mit dem Knoten, dazu die Legende mit dem Beiblatt.
    assert ergebnis["geprueft"] >= 5 * (len(ergebnis["flaechen"]) + 1)


@pytest.mark.skipif(_chromium_fehlt(), reason="Chromium fehlt")
def test_die_probe_als_befehl_mit_eigenem_bau(capsys):
    """Die Schalter ``--bau`` und ``--json``: derselbe Lauf über die Befehlszeile, Ende 0, ganzes Ergebnis."""
    probe = _probe()
    assert probe.main(["--bau", str(probe.BAU), "--json"]) == 0
    ausgabe = capsys.readouterr().out
    assert '"fehler": []' in ausgabe and '"geprueft"' in ausgabe


def test_die_probe_kennt_die_verlangten_stufen_und_flaechen():
    probe = _probe()
    assert probe.ZOOMSTUFEN == (0.25, 0.5, 1, 2, "max")
    namen = {f["name"] for f in probe.FLAECHEN}
    for pflicht in ("Porttyp-Legende", "Kuratier-Knopf", "GRAPH-Insel", "SONNE-Insel", "Erzählzeile",
                    "Karte des Assistenten", "Lot (Assistent)"):
        assert pflicht in namen
    seite = probe.pruefseite()
    assert "elementFromPoint" in seite and "ctrlKey: true" in seite


# ------------------------------------------------------------------ der Bau in der Kopie


def test_die_flaechen_liegen_in_der_ebene_ueber_der_leinwand():
    quelle = LEINWAND.read_text(encoding="utf-8")
    anfang = quelle.index('<div className="vis-ueber-leinwand" data-testid="vis-ueber-leinwand">')
    welt = quelle.index('className="vis-knoten-welt"')
    assert welt < anfang, "die Ebene muss nach der Knotenebene stehen"
    ebene = quelle[anfang:quelle.index("<DockFlaeche", anfang) if "<DockFlaeche" in quelle[anfang:] else None]
    for teil in ('className="vis-chrome-topright"', "<KuratierFlaeche", 'data-testid="vis-island-legende"'):
        assert teil in ebene, teil
    assert "vis-island-legende" not in quelle[welt:quelle.index("P16 · DIE BEIBLAETTER")]


def test_ebene_mit_eigenem_stapel_ueber_dem_beiblatt_und_unter_den_inseln():
    css = CSS.read_text(encoding="utf-8")
    ebene = _block(css, ".vis-ueber-leinwand")
    assert "isolation: isolate" in ebene and "pointer-events: none" in ebene
    stufe = int(re.search(r"z-index: calc\(var\(--k-ebene-grund\) \+ (\d+)\)", ebene).group(1))
    beiblatt = int(re.search(r"const BEIBLATT_Z = (\d+);", LEINWAND.read_text(encoding="utf-8")).group(1))
    assert beiblatt < stufe < 40
    assert "z-index: var(--k-ebene-grund)" in _block(css, ".vis-knoten-ebene")
    tafel = TAFEL.read_text(encoding="utf-8")
    assert "name: 'VIS_UEBER_LEINWAND'" in tafel and f"wert: {stufe}," in tafel


# ------------------------------------------------------------------ das iPad


def test_ipad_zoomt_nur_in_der_abgeschnittenen_zeichenleinwand():
    """Die einzige zoomende Fläche des iPads ist die Zeichenleinwand (Rollfläche mit ``zoomScale``). Sie
    liegt in einem Stapel, der an seinem Rand abschneidet — was sie zeigt, kann nie über Leiste,
    Seitenfeld oder Knöpfe wachsen."""
    leinwand = (IPAD / "Zeichnen" / "Zeichenleinwand.swift").read_text(encoding="utf-8")
    stapel = leinwand[leinwand.index("final class Leinwandstapel"):]
    assert "clipsToBounds = true" in stapel[:stapel.index("required init?")]
    zoomend = [p.relative_to(IPAD).as_posix() for p in IPAD.rglob("*.swift")
               if "zoomScale" in p.read_text(encoding="utf-8")]
    assert zoomend == ["Zeichnen/Zeichenleinwand.swift"]


def test_ipad_vergroessert_keine_flaeche_mit_inhalt_und_ordnet_nicht_per_zindex():
    """Kein ``scaleEffect`` auf einem Behälter (einzig die Übergabe-Marke pulst beim Ablegen) und kein
    ``zIndex``: Was oben liegt, entscheidet die Reihenfolge im Stapel — und die ist geprüft."""
    funde = []
    for datei in IPAD.rglob("*.swift"):
        text = datei.read_text(encoding="utf-8")
        rel = datei.relative_to(IPAD).as_posix()
        if ".zIndex(" in text:
            funde.append(f"{rel}: zIndex")
        if ".scaleEffect(" in text and rel != "Verbindung/Uebergabe.swift":
            funde.append(f"{rel}: scaleEffect")
    assert funde == []


def test_ipad_hinweis_und_ausgang_liegen_ueber_der_leinwand():
    flaeche = (IPAD / "Zeichnen" / "Zeichenflaeche.swift").read_text(encoding="utf-8")
    stapel = flaeche[flaeche.index("ZStack {"):]
    assert stapel.index("Zeichenleinwand(") < stapel.index("ausgeblendetHinweis"), \
        "der Hinweis muss im Stapel nach (über) der Leinwand stehen"
    platz = (IPAD / "Leiste" / "Arbeitsplatz.swift").read_text(encoding="utf-8")
    mitte = platz[platz.index("                mitte\n"):platz.index("                seitenfeld\n")]
    assert ".overlay(" in mitte and "ausgang" in mitte, "der Vollbild-Ausgang liegt als Auflage über der Mitte"
