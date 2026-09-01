#!/usr/bin/env python3
"""Welcher Schalter ist noch nie gedrückt worden?

**Wozu es dieses Werkzeug gibt** (01.09.2026, nach drei Fehlern desselben Tages): Ein
Kommandozeilenschalter ist ein Versprechen. Wird er nie in einer Probe benutzt, kann er
still nichts tun — und niemand merkt es, weil kein Test rot wird und kein Benutzer eine
Fehlermeldung bekommt.

Gemessen am Tag des Baus: **9 von 33 Schaltern kamen in keiner einzigen Probe vor.** Zwei
davon waren kaputt:

* ``auftragspost.py --auftrag X --nach Y`` kehrte vor der Ablage um und **druckte**. Die
  Datei, die der Adressat lesen sollte, entstand nie — ohne Fehlermeldung.
* ``einbau.py --worker kern`` wurde mit *«invalid choice»* abgewiesen. Die Liste der
  Adressaten stand ein zweites Mal im Skript und war seit dem 28.08. veraltet.

*Ein Bedienelement ohne Wirkung ist schlimmer als keines: Es sagt, etwas sei geschehen.*
Genau diesen Befund geben wir sonst an die Oberfläche weiter.

Was hier NICHT geprüft wird
---------------------------
Ob der Schalter das Richtige **tut**. Gezählt wird nur, ob sein Name irgendwo in einer
Probe vorkommt — das ist eine schwache Bedingung, und sie ist mit Absicht schwach: Eine
starke wäre nicht automatisch zu prüfen, und eine schwache, die läuft, findet mehr als
eine starke, die nicht gebaut wird.

*Ein Treffer ist darum kein Fehler, sondern eine unbeantwortete Frage: Was passiert,
wenn jemand diesen Schalter setzt? Wer sie beantwortet, schreibt die Probe dazu.*

    python tools/schalterprobe.py
    python tools/schalterprobe.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

#: Wie ein Schalter in einem Werkzeug angemeldet wird. Nur lange Namen — kurze
#: Einbuchstaben-Schalter gibt es hier nicht, und eine Suche nach ``-j`` fände zu viel.
_ANMELDUNG = re.compile(r'add_argument\(\s*"(--[a-z0-9-]+)"')

#: Schalter, die absichtlich in keiner Probe stehen — **mit Begründung**.
#: *Eine wachsende Liste hier ist ein Zeichen dafür, dass weggesehen statt geprüft wird.*
ABSICHTLICH: dict[str, str] = {
    "--help": "von argparse erzeugt, nicht von uns",
}


def schalter(werkzeug: Path) -> list[str]:
    """Die langen Schalter, die dieses Werkzeug anmeldet."""
    return _ANMELDUNG.findall(werkzeug.read_text(encoding="utf-8"))


def probentext(testordner: Path) -> str:
    """Alle Proben als ein Text. Gesucht wird darin nach dem blossen Namen."""
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in sorted(testordner.glob("*.py")))


def ungedrueckt(wurzel: Path | None = None) -> dict:
    """Je Werkzeug die Schalter, die in keiner Probe vorkommen."""
    wurzel = Path(wurzel or WURZEL)
    text = probentext(wurzel / "tests")
    je_werkzeug: dict[str, list[str]] = {}
    n_gesamt = 0
    for werkzeug in sorted((wurzel / "tools").glob("*.py")):
        alle = schalter(werkzeug)
        n_gesamt += len(alle)
        offen = [s for s in alle
                 if s not in ABSICHTLICH
                 and f'"{s}"' not in text and f"'{s}'" not in text]
        if offen:
            je_werkzeug[werkzeug.name] = offen
    return {
        "n_gesamt": n_gesamt,
        "n_ungedrueckt": sum(len(v) for v in je_werkzeug.values()),
        "je_werkzeug": je_werkzeug,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--wurzel", default=str(WURZEL), help="Repo-Wurzel")
    p.add_argument("--json", action="store_true", help="maschinenlesbar ausgeben")
    a = p.parse_args(argv)

    befund = ungedrueckt(a.wurzel)
    if a.json:
        print(json.dumps(befund, ensure_ascii=False, indent=1))
        return 0

    for werkzeug, offen in befund["je_werkzeug"].items():
        print(f"{werkzeug:<28} {len(offen):>2} nie in einer Probe: {', '.join(offen)}")
    print(f"\n{befund['n_ungedrueckt']} von {befund['n_gesamt']} Schaltern kommen in "
          f"keiner Probe vor.")
    print("\nEin Treffer ist KEIN Fehler, sondern eine unbeantwortete Frage: Was passiert,")
    print("wenn jemand diesen Schalter setzt? Wer sie beantwortet, schreibt die Probe")
    print("dazu — oder traegt den Schalter mit BEGRUENDUNG in ABSICHTLICH ein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
