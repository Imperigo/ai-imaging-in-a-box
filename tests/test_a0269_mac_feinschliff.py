"""A0269 — zwei Befunde der Geräteprobe 0.3.75 Teil 2 am Mac (08.11.2026).

1. Im Kopplungsblatt standen drei Verweise und drei Knöpfe in EINER Zeile; das Blatt kürzte die
   Knöpfe auf «Neu suc…» und «Abbrech…». Verweise und Knöpfe stehen jetzt in zwei Zeilen.
2. Im Aktualisieren-Blatt folgte auf «Neu ist:» nichts, wenn die Freigabe weder Neuerungen noch
   eine Seite nannte (so beim simulierten Angebot). Jetzt steht dort ein Satz.

Geprüft wird der übersetzte Quelltext (ohne Zeilenkommentare); Swift läuft in der iPad-CI.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad"
KERN = IPAD / "Visbox.swiftpm" / "Kern"
MAC = IPAD / "VisboxMac" / "Sources" / "VisboxMac"


def _code(pfad: Path) -> str:
    return "\n".join(z for z in pfad.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith("//"))


def _hstack_mit(code: str, kennung: str) -> str:
    """Der Rumpf des innersten HStack, der ``kennung`` enthält (Klammern gezählt)."""
    stelle = code.index(kennung)
    anfang = code.rfind("HStack {", 0, stelle)
    assert anfang >= 0, kennung
    tiefe, i = 0, code.index("{", anfang)
    while True:
        if code[i] == "{":
            tiefe += 1
        elif code[i] == "}":
            tiefe -= 1
            if tiefe == 0:
                return code[anfang:i + 1]
        i += 1


def test_im_kopplungsblatt_stehen_verweise_und_knoepfe_in_zwei_zeilen():
    code = _code(MAC / "Start" / "Koppeln.swift")
    knoepfe = _hstack_mit(code, 'Button("Neu suchen")')
    assert 'Button("Abbrechen", action: fertig)' in knoepfe
    assert 'Button("Weiter")' in knoepfe
    for verweis in ('Button("Von Hand eintragen …")', 'Button(Rechnerwahl.titel + " …") { rechner = true }',
                    'Button(Claudeeinrichtung.titel + " …") { claude = true }'):
        assert verweis not in knoepfe, f"{verweis} steht in der Knopfzeile"


def test_nach_neu_ist_steht_immer_etwas():
    blatt = _code(MAC / "Aktualisieren" / "Aktualisierenblatt.swift")
    assert "Aktualisierung.keineNeuerungen" in blatt
    kern = _code(KERN / "Aktualisierung.swift")
    satz = re.search(r'static let keineNeuerungen = "([^"]+)"', kern)
    assert satz and satz.group(1).strip(), "der Satz fehlt im Kern"
