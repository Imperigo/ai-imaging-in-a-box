"""Greifen die Stile der Knotenansicht im Bau? (Befund des Owners am Mac, 21.10.2026)

Eine einzige fehlende Klammer in ``vis-visual.css`` legte im Bau fast die Hälfte aller Regeln unter
eine fremde Regel: Inseln als Spalte links unten, doppeltes «Sonnenstunden», Claudes Karte unter dem
Fensterrand, «Senden» ohne Feld. ``tsc``, Vite und Vitest blieben grün. Diese Proben werden rot,
sobald so etwas wieder durchrutscht — die erste ohne Browser, die zweite mit Chrome gegen den Bau.

In ``pruefung.yml`` ist ``AIIMAGING_STILPROBE_PFLICHT=1`` gesetzt: Dort ist ein fehlendes Chrome ein
Fehler, kein Überspringen.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("stil_probe", WURZEL / "tools" / "stil_probe.py")
stil_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stil_probe)


# ── ohne Browser ────────────────────────────────────────────────────────────────────────────

def test_geschlossenes_css_hat_keinen_befund():
    text = """/* { im Kommentar } */
.a { color: red; content: "}{"; }
@media (min-width: 10px) { .b { color: blue; } }
@keyframes k { from { opacity: 0; } to { opacity: 1; } }
@supports (display: grid) { @media print { .c { x: y } } }
"""
    assert stil_probe.css_befunde(text) == []


def test_die_verlorene_klammer_wird_gefunden():
    """Genau der Fall vom 20.10.2026: die Regel bleibt offen, alles danach steckt in ihr."""
    text = ".vis-raster-gross-urteil {\n  color: red;\n\n.isl-leiste { display: flex; }\n"
    befunde = stil_probe.css_befunde(text)
    assert any("isl-leiste" in b and "vis-raster-gross-urteil" in b for b in befunde)
    assert any("nie geschlossen" in b for b in befunde)


def test_ueberzaehlige_klammer_wird_gefunden():
    assert stil_probe.css_befunde(".a { x: y; } }") != []


def test_auch_der_minifizierte_bau_wird_gelesen():
    assert stil_probe.css_befunde(".a{x:y}@media(x){.b{x:y}}") == []
    assert stil_probe.css_befunde(".a{x:y.b{x:y}}") != []


def test_jede_css_der_kopie_und_der_bau_sind_geschlossen():
    dateien = stil_probe.css_dateien()
    assert any("dist" in p.parts for p in dateien), "der Bau fehlt in der Prüfung"
    assert any(p.name == "vis-visual.css" for p in dateien)
    assert stil_probe.pruefe_css() == {}


# ── mit Chrome, gegen den eingecheckten Bau ─────────────────────────────────────────────────

def _chrome() -> str:
    chrome = stil_probe.finde_chrome()
    if chrome is None:
        if os.environ.get("AIIMAGING_STILPROBE_PFLICHT") == "1":
            pytest.fail("Kein Chromium/Chrome — die Sichtprobe ist hier Pflicht")
        pytest.skip("Kein Chromium/Chrome")
    return chrome


@pytest.fixture(scope="module")
def messung() -> dict:
    return stil_probe.miss(stil_probe.BAU, _chrome())


def test_inseln_kugel_claude_karte_und_gespraechsfeld_greifen_im_bau(messung):
    assert stil_probe.befunde_der_messung(messung) == []


def test_der_pillentitel_steht_nicht_doppelt(messung):
    """«Sonnenstunden» doppelt: der Titel der Pille ist in der Leiste nur für Vorleser da
    (``.isl-leiste .isl-werkzeug-titel``, island.css) — ohne die Regel steht er sichtbar daneben."""
    assert messung["titel_sichtbar"] == []


def test_claudes_offene_karte_ist_im_fenster(messung):
    assert messung["claude"]["marke"] and messung["claude"]["offen"] and messung["claude"]["karte"]


def test_die_messung_erkennt_den_kaputten_stand():
    """Gegenprobe: eine Messung wie im Bau vom 21.10.2026 (vor der Klammer) ist rot."""
    kaputt = {"breite": 1440, "hoehe": 900, "wurzel": True, "thema": "orbit",
              "inseln": {n: {"pos": "static", "box": [0, 600 + 30 * i, 36, 31]}
                         for i, n in enumerate(("graph", "ansicht", "stimmung", "austausch", "sonne"))},
              "kugel": {"pos": "static", "box": [0, 746, 72, 67], "sicht": True},
              "titel_sichtbar": ["Sonnenstunden"],
              "claude": {"marke": False, "offen": False, "karte": False, "box": [0, 918, 156, 27]},
              "gespraech": {"feld": False, "senden": True, "feld_box": [0, 159, 157, 44],
                            "senden_box": [157, 184, 66, 32], "panel_pos": "static"}}
    befunde = stil_probe.befunde_der_messung(kaputt)
    assert len(befunde) >= 10
    assert any("doppelt" in b for b in befunde)
    assert any("Claude" in b for b in befunde)
