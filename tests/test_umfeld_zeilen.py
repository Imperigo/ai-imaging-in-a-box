"""Knoten «Umfeld»: jede Zeile zeigt Quelle und «CC0» ganz, kein Satz liegt über dem anderen.

Befund von KosmoOrbit Int 1 (24.10.2026, Demo-Stand), gleich in der Visbox-Kopie: Zeilen der Modell-Liste
abgeschnitten (bei Bäumen und Autos fehlte «CC0»), der Lizenzsatz über dem Ladesatz. Grundlage: die
Regel «nichts abgeschnitten, nichts verdeckt» und Owner-Entscheid 147 (die Lizenz steht sichtbar am Knoten).
Protokoll 74 §288, Nachtrag.

Zwei Teile: die **Messprobe** am eingecheckten Bau (``tools/umfeld_zeilen_probe.py``, Chromium, Zoom 1
und 0,5, mit langen Namen) und der **Aufbau** in der Kopie (eigene Stücke für Herkunft und Lizenz).
Die Probe der Kopie selbst (``kv-umfeld.test.tsx``, jsdom) kommt wortgleich aus KosmoVis.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


def _probe():
    spec = importlib.util.spec_from_file_location("umfeld_zeilen_probe", WURZEL / "tools" / "umfeld_zeilen_probe.py")
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
def test_umfeld_zeilen_ganz_bei_zoom_1_und_halb():
    """Am eingecheckten Bau: fünf Zeilen je Stufe und Namenslänge, keine läuft über, «CC0» und Quelle
    ganz sichtbar, Lade- und Lizenzsatz ohne Überlauf und ohne Überdeckung. Vor dem Fix: 42 Funde."""
    ergebnis = _probe().pruefe()
    assert ergebnis["fehler"] == []
    assert len(ergebnis["stufen"]) == 2 and ergebnis["stufen"][1] < 0.55
    assert ergebnis["zeilen"] == 5 * 2 * 2


@pytest.mark.skipif(_chromium_fehlt(), reason="Chromium fehlt")
def test_die_probe_als_befehl(capsys):
    probe = _probe()
    assert probe.main(["--json"]) == 0
    assert '"fehler": []' in capsys.readouterr().out


def test_aufbau_der_kopie_herkunft_und_lizenz_als_eigene_stuecke():
    knoten = (VIS / "UmfeldKnoten.tsx").read_text(encoding="utf-8")
    assert 'data-umfeld="herkunft"' in knoten and 'data-umfeld="modelle"' in knoten
    assert "vis-kn-umfeld-huelle" in knoten
    css = (VIS / "knoten-neu.css").read_text(encoding="utf-8")
    herkunft = css[css.index(".vis-kn-umfeld-herkunft {"):]
    herkunft = herkunft[:herkunft.index("}")]
    assert "flex: none" in herkunft and "text-overflow" not in herkunft and "overflow: hidden" not in herkunft
    satz = css[css.index(".vis-kn-umfeld-satz {"):]
    assert "line-clamp" not in satz[:satz.index("}")]
    probe = _probe()
    assert probe.ZOOMSTUFEN == (1, 0.5)
    seite = probe.pruefseite()
    assert "vis_umfeldSetzen" in seite and "scrollWidth" in seite and "ctrlKey: true" in seite
