"""Neustart nach dem Aktualisieren, kleine Nummer und Wiederverbinden am iPad (14.10.2026).

Owner-Meldung: Nach «Neu starten» blieb die alte Mac-App offen, ein neues Fenster ging davor
auf, und eine Bestätigung kam nie; am iPad verband sich die App beim Öffnen nicht von selbst.
Bewacht wird der Weg im Quelltext — übersetzt wird Swift nur auf der Prüfstrecke am Mac.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
IPAD = WURZEL / "ipad" / "Visbox.swiftpm"


def _code(datei: Path) -> str:
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.strip().startswith("//"))


def test_der_neustart_beendet_erst_und_oeffnet_dann():
    code = _code(MAC / "Aktualisieren" / "Fassungswaechter.swift")
    teil = code[code.index("func starteNeu()"):]
    assert "Aktualisierung.neustartBefehl(" in teil and "helfer.run()" in teil
    # Die alte App oeffnet die neue nicht mehr selbst.
    assert "openApplication" not in code and "createsNewApplicationInstance" not in code
    assert teil.index("helfer.run()") < teil.index("NSApp.terminate(nil)") < teil.index("exit(0)")
    # Die erwartete Nummer wird VOR dem Beenden gemerkt.
    assert teil.index("Aktualisierung.erwarteteSchluessel") < teil.index("NSApp.terminate(nil)")


def test_auch_der_umzug_beendet_erst():
    code = _code(MAC / "Aktualisieren" / "Umzug.swift")
    assert "openApplication" not in code and "Aktualisierung.neustartBefehl(" in code


def test_der_naechste_start_bestaetigt_die_nummer():
    fenster = _code(MAC / "Start" / "Hauptfenster.swift")
    assert "aktualisierung.pruefeNeustart()" in fenster
    assert "aktualisierung.neustartBefund?.satz" in fenster
    kern = (IPAD / "Kern" / "Aktualisierung.swift").read_text(encoding="utf-8")
    assert "ist installiert." in kern and "kam nicht an" in kern


def test_die_mac_app_hat_ein_fenster_nicht_eine_gruppe():
    app = _code(MAC / "VisboxMacApp.swift")
    assert "Window(Marke.name" in app and "WindowGroup" not in app


def test_die_nummer_steht_klein_neben_dem_namen():
    for datei in ("Arbeitsansicht.swift", "Startansicht.swift"):
        code = _code(MAC / "Start" / datei)
        m = re.search(r"Text\(Marke\.name\)\s*\.font\(Macschriften\.schrift\(\.titel, 25\)\)\s*"
                      r"Text\(Aktualisierung\.kleineNummer\(", code)
        assert m, datei


def test_das_ipad_fragt_beim_oeffnen_sofort_und_kurz():
    stand = _code(IPAD / "Verbindung" / "Verbindungsstand.swift")
    assert "static let pruefFrist: TimeInterval = 5" in stand
    assert "frist: Verbindungsstand.pruefFrist" in stand
    # Beim Start sucht es gleich auch nach dem Namen, nicht erst nach einer gescheiterten Frage.
    init = stand[stand.index("    init() {"):stand.index("static func fachordner()")]
    assert "verlange(.wiederfinden)" in init
    assert "func wiederAktiv()" in stand
    sender = _code(IPAD / "Verbindung" / "Sender.swift")
    assert "if let frist { auftrag.timeoutInterval = frist }" in sender
    start = _code(IPAD / "Startansicht.swift")
    assert "Verbindungsstand.gemeinsam.wiederAktiv()" in start
