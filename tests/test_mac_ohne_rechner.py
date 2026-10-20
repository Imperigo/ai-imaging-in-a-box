"""Ohne Rechner bleibt die Mac-App bedienbar; die Rechner-Wahl ist sichtbar und gespeichert.

«Visbox eigenständig», Schritt 2 (Entscheid 103b: der Vorführmodus entfällt) und Schritt 6
(Rechner-Wahl je Arbeit), 20.10.2026, nach Blatt 28 der Entwurfsfläche (Felder 1 und 2).

Die Regeln selbst prüft ``swift test`` im Kern (``LeitungsschalterTests``, ``RechnerwahlTests``).
Die Mac-App übersetzt nur die Prüfstrecke am Mac; bewacht wird hier darum die **Verdrahtung**:
dass kein Teil mehr das Fenster ersetzt, dass Band, Sperre und Wahl dort ankommen, wo das Blatt
sie zeigt — und die Naht zur Knotenansicht (der Satz der App kommt am Render-Knoten an).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad"
KERN = IPAD / "Visbox.swiftpm" / "Kern"
MAC = IPAD / "VisboxMac" / "Sources" / "VisboxMac"
START = MAC / "Start"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"


def _code(pfad: Path) -> str:
    """Der Quelltext ohne Zeilenkommentare — bewacht wird, was übersetzt wird."""
    return "\n".join(z for z in pfad.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith("//"))


# ------------------------------------------------------------- Schritt 2: kein Vorführmodus

def test_kein_teil_der_mac_app_ersetzt_mehr_das_fenster():
    assert not (MAC / "Vorfuehrung").exists(), "der Ordner des Vorführmodus ist weg"
    for datei in MAC.rglob("*.swift"):
        code = _code(datei)
        for alt in ("Vorfuehrbereich", "Vorfuehransicht", "Vorfuehrsteuerung", "Vorfuehrsaetze",
                    "Vorfuehrfarbe", "Vorfuehrschalter", ".vorfuehrung"):
            assert alt not in code, f"{datei.name} nennt noch {alt}"
    kern = _code(KERN / "Leitungsschalter.swift")
    assert "case vorfuehrung" not in kern
    assert re.search(r"public enum Fensterinhalt[^{]*\{\s*(///[^\n]*\s*)*case start\s*"
                     r"(///[^\n]*\s*)*case arbeit\s*\}", kern), "nur noch Start und Arbeit"


def test_das_band_steht_oben_ueber_start_und_arbeit():
    fenster = _code(START / "Hauptfenster.swift")
    assert "leitungstakt.schalter.band(eingerichtet: eingerichtet)" in fenster
    assert "Leitungsband(band: band," in fenster
    assert "erneutVerbinden: { leitungstakt.erneutVerbinden() }" in fenster
    assert "einrichten: { einrichtenOffen = true }" in fenster
    # DAS WEICHE BAND BLEIBT (3 Fehlversuche und 30 s, im Kern), schwebend und ohne Knopf.
    assert "KurzWegBand(zeigen: band?.weich == true)" in fenster
    band = _code(START / "Leitungsband.swift")
    assert "Leitungssaetze.kurzWeg" in band and "Rechnerband.grund" in band
    # OHNE RECHNER IN DIE ARBEIT, statt sie zu ersetzen; eine Absage holt nicht mehr hinaus.
    assert "oeffnetDieArbeit(eingerichtet: !leitung.braucheEinrichten)" in fenster
    assert "arbeitet = false\n            leitung.pruefeJetzt()" not in fenster


def test_schon_anfangen_und_die_sperre_kommen_vom_kern():
    fenster = _code(START / "Hauptfenster.swift")
    assert "sperre: schalter.sperre(eingerichtet: eingerichtet)" in fenster
    assert "anfangenMoeglich: schalter.anfangenMoeglich(" in fenster
    start = _code(START / "Startansicht.swift")
    assert ".disabled(!anfangenMoeglich)" in start and "Text(anfangenSatz)" in start
    assert "leitung.bild.schonAnfangen" not in start, "der Knopf fragt den Kern, nicht nur die Leitung"


def test_die_assistent_leiste_ist_ohne_rechner_gesperrt_mit_satz():
    arbeit = _code(START / "Arbeitsansicht.swift")
    assert "gesperrt: sperre.satz)" in arbeit
    leiste = _code(MAC / "Assistent" / "Assistentenleiste.swift")
    assert "Eingabe(modell: modell, gesperrt: gesperrt)" in leiste
    # KEIN FELD, DAS NUR EINEN FEHLER BRAECHTE: mit Sperre steht der Satz, nicht das Feld.
    eingabe = leiste[leiste.index("private struct Eingabe"):]
    assert eingabe.index("if let satz = gesperrt") < eingabe.index("TextField(")
    assert "gesperrt: modell.gespraech.wartet || gesperrt != nil" in leiste


def test_die_saetze_des_bands_sind_die_des_blatts():
    kern = (KERN / "Leitungsschalter.swift").read_text(encoding="utf-8")
    for satz in ("Heim-PC nicht erreichbar", "Rechnen und Assistent gesperrt — alles andere geht.",
                 "Erneut verbinden", "Braucht einen Rechner — Heim-PC nicht erreichbar.",
                 "Heim-PC kurz nicht erreichbar — verbinde neu …"):
        assert f'"{satz}"' in kern, satz


# ------------------------------------------- die Naht zur Knotenansicht (Render-Knoten)

def test_der_satz_der_app_kommt_am_render_knoten_an():
    """Ohne Heim-PC antwortet die App auf die Render-Wege mit 503/502 und ``{"fehler": satz}``;
    der Wirt der Knotenansicht macht daraus einen Fehler mit diesem Satz, damit am Knoten nicht
    «Bridge antwortet mit: 503» steht. Beide Seiten müssen dieselben Zahlen und dieselbe Form
    meinen."""
    wege = (KERN / "Knotenwege.swift").read_text(encoding="utf-8")
    zahlen = {int(z) for z in re.findall(r"case (?:heimNichtErreicht|ohneHeim) = (\d+)", wege)}
    assert zahlen == {502, 503}, zahlen
    assert 'withJSONObject: ["fehler": satz]' in wege
    mappe = (WIRT / "mappe.ts").read_text(encoding="utf-8")
    m = re.search(r"BRUECKE_SATZ_STATUS: readonly number\[\] = \[([^\]]+)\]", mappe)
    assert m and {int(z) for z in m.group(1).split(",")} == zahlen
    assert "BRUECKE_SATZ_PFAD = '/bruecke/jobs'" in mappe
    haupt = (WIRT / "main.tsx").read_text(encoding="utf-8")
    assert "window.fetch = brueckeSagtDenSatz(koerperAlsBytes(window.fetch.bind(window)));" in haupt


def test_der_wirt_ist_visbox_eigen_und_die_kopie_bleibt_unberuehrt():
    herkunft = json.loads((WURZEL / "kosmovis" / "HERKUNFT.json").read_text(encoding="utf-8"))
    for pfad in herkunft["woertlich"]:
        assert not pfad.startswith("apps/visbox-knoten/"), pfad


# ------------------------------------------------------------- Schritt 6: Rechner-Wahl

def test_einrichten_hat_wer_rechnet():
    koppeln = _code(START / "Koppeln.swift")
    assert "Rechnerwahlansicht(leitung: leitung, leitungstakt: leitungstakt," in koppeln
    assert koppeln.count('Button(Rechnerwahl.titel + " …") { rechner = true }') == 2, \
        "erreichbar beim Suchen und nach dem Verbinden"
    fenster = _code(START / "Hauptfenster.swift")
    assert "Koppeln(leitung: leitung, leitungstakt: leitungstakt," in fenster


def test_die_wahl_liegt_in_den_app_einstellungen_und_fragt_nur_nach_blender():
    ansicht = _code(START / "Rechnerwahlansicht.swift")
    assert "ablage.data(forKey: Rechnerwahl.schluessel)" in ansicht
    assert "ablage.set(wahl.alsDaten(), forKey: Rechnerwahl.schluessel)" in ansicht
    assert "FileManager.default.fileExists(atPath: Rechnerwahl.blenderOrt)" in ansicht
    assert "ProcessInfo.processInfo.physicalMemory" in ansicht
    # BLENDER WIRD NICHT GESTARTET (Regel 2) — die App sieht nur nach, ob es da ist.
    for verboten in ("Process(", "NSWorkspace", "launchApplication", "openApplication"):
        assert verboten not in ansicht, verboten
    # DIE WAHL AENDERT HEUTE NICHTS AM WEG: keine andere Datei der App liest sie.
    for datei in MAC.rglob("*.swift"):
        if datei.name != "Rechnerwahlansicht.swift":
            assert "Rechnerwahlspeicher" not in _code(datei), datei.name
    kern = (KERN / "Rechnerwahl.swift").read_text(encoding="utf-8")
    assert 'blenderOrt = "/Applications/Blender.app"' in kern
    assert '"Claude über MCP steuert " + Marke.name + " immer — unabhängig "' in kern
