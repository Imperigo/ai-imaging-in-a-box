"""A0270 Satz 2: Deaktivierte Felder der Rechnerwahl sind im hellen Modus lesbar (mindestens 3:1).

Geräteprobe 0.3.75, Befund A0156: «Dieses Gerät» war sehr blass. Ursache: das ganze Feld wurde mit
``.opacity(0.45)`` halb durchsichtig gezeichnet, Schrift und Rand verblassten gemeinsam auf den Grund.
Jetzt zeichnet ein gesperrtes Feld mit deckenden Farben aus der Tafel ``Startfarbe``; diese Probe
liest die Farbwerte aus dem Quelltext und rechnet das Kontrastverhältnis nach der Formel der WCAG
(relative Helligkeit), im hellen wie im dunklen Modus.

Das Mass: 3:1 für Bedienelemente und deren Zustände (WCAG 1.4.11). Die Rechnerwahl ist Teil von
``VisboxMac`` (kein XCTest-Ziel, SwiftUI läuft hier nicht): gerechnet wird aus den Farbzahlen.
"""
from __future__ import annotations

import re
from pathlib import Path

MAC = Path(__file__).resolve().parents[1] / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start"
MINDESTENS = 3.0


def _lin(k: int) -> float:
    c = k / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hell(rgb: int) -> float:
    r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def verhaeltnis(a: int, b: int) -> float:
    la, lb = _hell(a), _hell(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _farben() -> dict[str, dict[str, int]]:
    quelle = (MAC / "Startfarben.swift").read_text(encoding="utf-8")
    return {n: {"dunkel": int(d, 16), "hell": int(h, 16)}
            for n, d, h in re.findall(r"static let (\w+) = Color\(startHex: 0x([0-9A-Fa-f]{6}), hell: 0x([0-9A-Fa-f]{6})\)", quelle)}


def _feld() -> str:
    quelle = (MAC / "Rechnerwahlansicht.swift").read_text(encoding="utf-8")
    code = "\n".join(z.split("//", 1)[0] for z in quelle.splitlines())
    return code.split("private struct Rechnerfeld", 1)[1].split("\n}\n", 1)[0]


def test_die_formel_kennt_ihre_enden():
    assert abs(verhaeltnis(0xFFFFFF, 0x000000) - 21.0) < 0.01
    assert abs(verhaeltnis(0x777777, 0x777777) - 1.0) < 0.01


def test_das_feld_wird_nicht_mehr_halb_durchsichtig_gezeichnet():
    feld = _feld()
    assert ".opacity(" not in feld, "Deckkraft über das ganze Feld lässt Schrift und Rand verblassen"
    # Das System dimmt ein `.disabled` zusätzlich zu den eigenen Farben: gesperrt wird in der Aktion geprüft.
    assert ".disabled(" not in feld
    assert "Button(action: { if waehlbar { waehle() } })" in feld


def test_ein_gesperrtes_feld_nimmt_seine_farben_aus_der_tafel():
    feld = _feld()
    assert "waehlbar ? Color.primary : Startfarbe.leise" in feld, "Titel gesperrt: leise Schrift"
    assert "Text(zeile)" in feld and ".foregroundStyle(Startfarbe.leise)" in feld, "Zeile: leise Schrift"
    assert "waehlbar ? Color.clear : Startfarbe.flaeche" in feld, "Grund gesperrt: die Fläche"
    assert "(waehlbar ? Startfarbe.ring : Startfarbe.leise)" in feld, "Rand gesperrt: leise, gestrichelt"
    assert "dash: waehlbar ? [] : [4, 3]" in feld


def test_gesperrt_erreicht_im_hellen_modus_drei_zu_eins():
    farben = _farben()
    schrift = farben["leise"]["hell"]
    for grund in ("flaeche", "grund", "karte"):
        v = verhaeltnis(schrift, farben[grund]["hell"])
        assert v >= MINDESTENS, f"leise Schrift auf {grund} (hell): {v:.2f}:1"
    # Der Rand ist dieselbe Farbe, also gegen dieselben Gründe.
    v = verhaeltnis(farben["leise"]["hell"], farben["flaeche"]["hell"])
    assert v >= MINDESTENS, f"Rand auf Fläche (hell): {v:.2f}:1"


def test_gesperrt_erreicht_auch_im_dunklen_modus_drei_zu_eins():
    farben = _farben()
    for grund in ("flaeche", "grund", "karte"):
        v = verhaeltnis(farben["leise"]["dunkel"], farben[grund]["dunkel"])
        assert v >= MINDESTENS, f"leise Schrift auf {grund} (dunkel): {v:.2f}:1"


def test_der_alte_zustand_haette_die_probe_nicht_bestanden():
    """Belegt, dass die Rechnung den Befund fasst: Schrift 0x5C6573 zu 45 % auf Fläche (hell)."""
    farben = _farben()
    grund = farben["grund"]["hell"]
    schrift = farben["leise"]["hell"]
    gemischt = sum(round(0.45 * ((schrift >> s) & 255) + 0.55 * ((grund >> s) & 255)) << s for s in (16, 8, 0))
    assert verhaeltnis(gemischt, grund) < MINDESTENS
