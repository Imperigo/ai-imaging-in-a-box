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
GLAS = MAC / "Start" / "Fensterglas.swift"
FARBEN = MAC / "Start" / "Startfarben.swift"


def _code(datei: Path) -> str:
    return "\n".join(z.split("//", 1)[0] for z in datei.read_text(encoding="utf-8").splitlines())


def test_der_kopf_nimmt_das_material_und_faellt_auf_deckend_zurueck():
    code = _code(FENSTER)
    assert re.search(r"\\\.accessibilityReduceTransparency", code)
    assert "Kopfgrund.waehle(reduzierteTransparenz:" in code
    assert "for: .windowToolbar" in code
    assert "Startfarbe.flaeche" in _code(GLAS)
    assert ".modifier(Glaskopf())" in code


def test_das_glas_mischt_hinter_dem_fenster():
    """Runde 2: `.toolbarBackground(.ultraThinMaterial)` mischte nur innerhalb des undurchsichtigen
    Fensters (Mac-Abend 07.11.2026, Kopf einfarbig). Das Glas ist eine `NSVisualEffectView`,
    `.behindWindow`, ueber dem Inhalt, und der Balken darunter nimmt nichts weg."""
    code = _code(FENSTER)
    assert ".ultraThinMaterial" not in code
    assert ".toolbarBackground(.hidden, for: .windowToolbar)" in code
    assert "Fensterglas(grund: Kopfgrund.waehle(reduzierteTransparenz: reduziert))" in code
    assert ".overlay(alignment: .top)" in code
    glas = _code(GLAS)
    assert "NSVisualEffectView" in glas
    assert ".blendingMode = .behindWindow" in glas
    assert ".state = .active" in glas
    assert "titlebarAppearsTransparent = true" in glas
    # Deckend bei «Transparenz reduzieren»: keine Mischung, die Flaeche.
    teil = glas[glas.index("case .deckend"):]
    assert "Startfarbe.flaeche" in teil and "Mischung()" not in teil.split("}")[0]


def test_die_visbox_folgt_dem_system_hell_und_dunkel():
    """O-20261107-01: kein fest gesetztes Schema; die Farben tragen beide Faelle."""
    for datei in (FENSTER, MAC / "VisboxMacApp.swift", GLAS):
        assert ".preferredColorScheme" not in _code(datei)
    farben = _code(FARBEN)
    assert "NSAppearance" in farben or ".darkAqua" in farben
    # Jede Farbe der Tafel hat ihre helle Zahl.
    zeilen = [z for z in farben.splitlines() if "static let" in z and "Color(startHex:" in z]
    assert len(zeilen) >= 15
    assert all("hell:" in z for z in zeilen), [z for z in zeilen if "hell:" not in z]


def test_die_fassungsnummer_hat_abstand_zu_einrichten():
    code = _code(FENSTER)
    teil = code[code.index("struct Fassungsanzeige"):]
    assert ".padding(.trailing, Fensterglas.abstandZumNachbarn)" in teil
    m = re.search(r"abstandZumNachbarn: CGFloat = (\d+)", _code(GLAS))
    assert m and int(m.group(1)) >= 10


def test_das_angebot_zur_probe_kommt_nur_aus_der_umgebung():
    """Der Weg fuer die Geraeteprobe: `VISBOX_ANGEBOT_SIMULIERT`; ohne ihn nie ein Angebot."""
    code = _code(WAECHTER)
    assert "Angebotsprobe.freigabe(umgebung:" in code
    assert "ProcessInfo.processInfo.environment" in code
    # Im Normalbetrieb fragt der Waechter weiter GitHub; das simulierte Angebot ersetzt nur die Antwort.
    assert "if let simuliert { antwort = simuliert } else { antwort = await hole() }" in code
    # Der Klick laedt nie etwas aus einem simulierten Angebot.
    assert "guard simuliert == nil else" in code
    assert "UserDefaults" not in code[code.index("Angebotsprobe"):code.index("Angebotsprobe") + 200]


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
