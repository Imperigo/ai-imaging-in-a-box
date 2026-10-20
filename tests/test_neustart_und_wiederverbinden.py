"""Neustart nach dem Aktualisieren, kleine Nummer und Wiederverbinden am iPad (14.10.2026).

Owner-Meldung: Nach «Neu starten» blieb die alte Mac-App offen, ein neues Fenster ging davor
auf, und eine Bestätigung kam nie; am iPad verband sich die App beim Öffnen nicht von selbst.
Bewacht wird der Weg im Quelltext — übersetzt wird Swift nur auf der Prüfstrecke am Mac.
"""
from __future__ import annotations

import re

import pytest
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"
IPAD = WURZEL / "ipad" / "Visbox.swiftpm"
KERN = IPAD / "Kern"


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
    assert "Neustartmeldung(waechter: aktualisierung)" in fenster and "waechter.neustartBefund?.satz" in fenster
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


# ------------------------------------------------------------------ 0.2.10 (20.10.2026)
# Owner-Befund beim Aktualisieren von 0.2.8 auf 0.2.9: nach dem Herunterladen eine zweite
# Visbox neben der alten, nach «Neu starten» eine dritte.

def test_nach_dem_herunterladen_startet_nichts_von_selbst():
    code = _code(MAC / "Aktualisieren" / "Fassungswaechter.swift")
    teil = code[code.index("func ladeUndErsetze()"):code.index("private func melde(")]
    assert "starteNeu()" not in teil, "erst der Klick auf «Neu starten» beendet die alte App"
    blatt = _code(MAC / "Aktualisieren" / "Aktualisierenblatt.swift")
    assert "waechter.starteNeu()" in blatt


def test_ein_zweiter_klick_startet_keinen_zweiten_helfer():
    code = _code(MAC / "Aktualisieren" / "Fassungswaechter.swift")
    teil = code[code.index("func starteNeu()"):]
    assert "!neustartLaeuft" in teil[:300]


def test_ein_zweiter_start_holt_die_laufende_nach_vorn():
    app = _code(MAC / "VisboxMacApp.swift")
    assert "Einzelstart.pruefe()" in app
    einzel = _code(MAC / "Aktualisieren" / "Einzelstart.swift")
    assert "Aktualisierung.startentscheid(" in einzel
    assert "activate(" in einzel and "forceTerminate()" in einzel


def _helfer(tmp_path, pid):
    """Der Helfer aus dem Kern, mit `echo` statt `open` — gelesen aus dem Swift-Text."""
    import re
    text = (KERN / "Aktualisierung.swift").read_text(encoding="utf-8")
    teil = text[text.index("public static func neustartBefehl"):]
    zahlen = {n: int(re.search(rf"static let {n} = (\d+)", text).group(1))
              for n in ("neustartBittenNach", "neustartZwingenNach", "neustartAufgebenNach")}
    roh = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', teil[:teil.index('"neustart", String(pid)')]))
    roh = roh.replace('\\"', '"')
    for n, z in zahlen.items():
        roh = roh.replace(f"\\({n})", str(z))
    return roh.replace("/bin/sh-c", "", 1).replace("exec /usr/bin/open", "exec echo GEOEFFNET")


def test_der_helfer_zwingt_eine_haengende_alte_app_und_oeffnet_erst_dann(tmp_path):
    import subprocess
    import time
    if not Path("/bin/sh").exists():
        pytest.skip("kein /bin/sh")
    # Eine «alte App», die das hoefliche Ende ignoriert — so hing sie am Mac des Owners.
    alt = subprocess.Popen(["/bin/sh", "-c", "trap '' TERM; while :; do sleep 0.1; done"])
    # ABGEHOLT WIE AM MAC: Dort raeumt launchd die beendete App sofort weg. Hier ist der
    # Test ihr Elternteil — ohne dieses Abholen bliebe sie als Zombie, und `kill -0` saehe
    # sie weiter «laufen».
    import threading
    threading.Thread(target=alt.wait, daemon=True).start()
    try:
        beginn = time.monotonic()
        lauf = subprocess.run(["/bin/sh", "-c", _helfer(tmp_path, alt.pid), "neustart",
                               str(alt.pid), "/Applications/Visbox.app"],
                              capture_output=True, text=True, timeout=30)
        dauer = time.monotonic() - beginn
    finally:
        alt.kill()
    assert alt.wait(timeout=5) is not None
    assert lauf.stdout.strip() == "GEOEFFNET /Applications/Visbox.app"
    assert 9 <= dauer <= 14, dauer   # nach 10 s gezwungen, dann geoeffnet

