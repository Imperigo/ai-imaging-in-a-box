"""Der Fensterkopf der Mac-App (A0156, E132 A): Glas, Fassungsnummer, grüner Punkt.

SwiftUI lässt sich hier nicht übersetzen. Die Regeln prüft der Kern
(``AktualisierungTests``), diese Probe nur, dass das Fenster sie auch benutzt.
"""
from __future__ import annotations

import re
from pathlib import Path

MAC = Path(__file__).resolve().parents[1] / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
FENSTER = MAC / "Start" / "Hauptfenster.swift"
WAECHTER = MAC / "Aktualisieren" / "Fassungswaechter.swift"


def _code(datei: Path) -> str:
    return "\n".join(z.split("//", 1)[0] for z in datei.read_text(encoding="utf-8").splitlines())


def test_der_kopf_nimmt_das_material_und_faellt_auf_deckend_zurueck():
    code = _code(FENSTER)
    assert re.search(r"\\\.accessibilityReduceTransparency", code)
    assert "Kopfgrund.waehle(reduzierteTransparenz:" in code
    assert "for: .windowToolbar" in code and ".ultraThinMaterial" in code
    assert "Startfarbe.flaeche" in code
    assert ".modifier(Glaskopf())" in code


def test_die_ampel_bleibt():
    """Kein versteckter Fensterkopf: Die Ampel-Knöpfe bleiben Sache des Systems."""
    for datei in (FENSTER, MAC / "VisboxMacApp.swift"):
        code = _code(datei)
        assert ".windowStyle(.hiddenTitleBar)" not in code
        assert "standardWindowButton" not in code


def test_der_punkt_kommt_vom_kern_und_oeffnet_aktualisieren():
    assert "Kopfnummer(stand: stand)" in _code(WAECHTER)
    code = _code(FENSTER)
    teil = code[code.index("struct Fassungsanzeige"):]
    assert "nummer.punkt" in teil and "Startfarbe.gruen" in teil
    assert "aktualisierung.kopfnummer" in code
    assert "Fassungsanzeige(nummer: aktualisierung.kopfnummer)" in code
