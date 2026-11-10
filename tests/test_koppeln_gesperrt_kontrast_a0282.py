"""A0282: Gesperrte Zeilen im Kopplungsblatt sind lesbar (mindestens 3:1) und für Hilfsmittel gesperrt.

Geräteprobe 0.3.75 und Bau-Meldung A0270: ``Koppeln.swift`` zeichnete eine gesperrte Kandidatenzeile
mit ``.opacity(0.6)``, Schrift und Rand verblassten gemeinsam auf den Grund. Jetzt gilt derselbe Weg
wie bei der Rechnerwahl (``tests/test_rechnerwahl_kontrast_a0270.py``): deckende Farben aus der Tafel
``Startfarbe``, und eine gesperrte Zeile ist kein Knopf, sondern eine Beschriftung. Die Probe liest die
Farbwerte aus dem Quelltext und rechnet das Verhältnis nach der WCAG-Formel, hell und dunkel
(3:1 für Bedienelemente, WCAG 1.4.11). SwiftUI läuft hier nicht: gerechnet wird aus den Farbzahlen.
"""
from __future__ import annotations

import re
from pathlib import Path

from test_rechnerwahl_kontrast_a0270 import MAC, MINDESTENS, _farben, verhaeltnis

KOPPELN = MAC / "Koppeln.swift"


def _code() -> str:
    quelle = KOPPELN.read_text(encoding="utf-8")
    return "\n".join(z.split("//", 1)[0] for z in quelle.splitlines())


def _zeilen() -> str:
    """Von der Kandidatenzeile bis zum Ende ihres Inhalts (vor `weiter()`)."""
    code = _code()
    return "func kandidatenzeile(" + code.split("func kandidatenzeile(", 1)[1].split("private func weiter()", 1)[0]


def _gesperrt() -> str:
    teil = _zeilen()
    assert "if k.waehlbar {" in teil and "} else {" in teil, "Zeile unterscheidet wählbar und gesperrt"
    return teil.split("} else {", 1)[1].split("private func zeileninhalt", 1)[0]


def test_kein_gesperrtes_feld_im_kopplungsblatt_wird_ueber_deckkraft_gedimmt():
    code = _code()
    assert ".opacity(" not in code, "Deckkraft lässt Schrift und Rand gemeinsam verblassen"
    assert ".disabled(!k.waehlbar)" not in code, "Systemdimmung ohne genannten Faktor (siehe A0270)"


def test_eine_gesperrte_zeile_ist_fuer_hilfsmittel_gesperrt():
    teil = _zeilen()
    gesperrt = _gesperrt()
    # Der Knopf gehört nur in den wählbaren Zweig.
    assert teil.count("Button {") == 1
    assert teil.index("Button {") < teil.index("} else {"), "Button nur im wählbaren Zweig"
    assert "Button(" not in gesperrt and "Button {" not in gesperrt
    assert ".accessibilityRemoveTraits(.isButton)" in gesperrt
    assert ".accessibilityAddTraits(.isStaticText)" in gesperrt
    assert ".accessibilityRespondsToUserInteraction(false)" in gesperrt
    assert ".accessibilityElement(children: .combine)" in gesperrt
    # Wählbar bleibt unverändert: dieselbe Auswahl.
    assert "auswahl = k.id" in teil.split("} else {", 1)[0]


def test_eine_gesperrte_zeile_nimmt_ihre_farben_aus_der_tafel():
    code = _code()
    inhalt = code.split("private func zeileninhalt", 1)[1].split("@MainActor", 1)[0]
    assert "k.waehlbar ? Startfarbe.gruen : Startfarbe.leise" in inhalt, "Punkt gesperrt: leise"
    assert "k.waehlbar ? Color.primary : Startfarbe.leise" in inhalt, "Name gesperrt: leise Schrift"
    assert ".foregroundStyle(Startfarbe.leise)" in inhalt, "Satz: leise Schrift"
    assert "(k.waehlbar ? Startfarbe.karte : Startfarbe.flaeche)" in inhalt, "Grund gesperrt: die Fläche"
    assert "(k.waehlbar ? Startfarbe.linie : Startfarbe.leise)" in inhalt, "Rand gesperrt: leise"
    assert "dash: k.waehlbar ? [] : [4, 3]" in inhalt, "Rand gesperrt: gestrichelt"


def test_gesperrt_erreicht_hell_und_dunkel_drei_zu_eins():
    farben = _farben()
    for modus in ("hell", "dunkel"):
        # Schrift, Rand und Punkt sind dieselbe Farbe (leise) auf der Fläche, dem Grund der gesperrten Zeile.
        v = verhaeltnis(farben["leise"][modus], farben["flaeche"][modus])
        assert v >= MINDESTENS, f"leise auf Fläche ({modus}): {v:.2f}:1"
        # Die Liste liegt auf dem Blatt: auch gegen die übrigen Gründe.
        for grund in ("grund", "karte"):
            v = verhaeltnis(farben["leise"][modus], farben[grund][modus])
            assert v >= MINDESTENS, f"leise auf {grund} ({modus}): {v:.2f}:1"


def test_der_alte_zustand_haette_die_probe_nicht_bestanden():
    """Belegt, dass die Rechnung den Befund fasst: Satz-Schrift zu 60 % auf Karte im hellen Modus.

    Im dunklen Modus lag die Schrift allein mit rund 3,2:1 knapp darüber; der Rand (`linie`, gedimmt)
    und der Punkt lagen in beiden Modi weit darunter. Der Befund der Geräteprobe war hell.
    """
    farben = _farben()
    grund = farben["karte"]["hell"]
    schrift = farben["leise"]["hell"]
    gemischt = sum(round(0.6 * ((schrift >> s) & 255) + 0.4 * ((grund >> s) & 255)) << s for s in (16, 8, 0))
    assert verhaeltnis(gemischt, grund) < MINDESTENS
    for modus in ("hell", "dunkel"):
        rand = farben["linie"][modus]
        assert verhaeltnis(rand, farben["karte"][modus]) < MINDESTENS, f"alter Rand {modus}"
