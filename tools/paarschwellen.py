#!/usr/bin/env python3
"""TRENNKURVE — was eine Kandidatenschwelle an beiden Fehlern kostet.

Die dünne Schicht über :mod:`aiimaging.paarschwellen`. Sie misst nichts; sie rechnet aus
Fällen, die anderswo gemessen wurden.

**Wozu es sie gibt** (`auf-20260827-61`, Owner-Entscheid 26.08.2026): ``PAAR_RHO_SCHWELLE``
und ``PAAR_KANTENANTEIL_SCHWELLE`` sind abgelesen und nicht kalibriert; bis sie es sind,
darf das Paarurteil nichts sperren. Die Kalibrierung braucht eine Tabelle mit **beiden**
Fehlerzahlen je Kandidatenschwelle — und eine von Hand gerechnete Tabelle ist der Weg,
auf dem aus einer Kalibrierung wieder eine abgelesene Schwelle wird.

    python tools/paarschwellen.py faelle.json
    python tools/paarschwellen.py faelle.json --groesse kantenanteil
    python tools/paarschwellen.py faelle.json --json

Die Eingabedatei ist eine Liste von Sätzen — oder ein Satz mit dem Schlüssel ``faelle``:

    [{"fall_id": "h1-sSE", "gut": false, "wert": -0.018,
      "szene": "gelaende-4x", "kamera": "sSE"}, ...]

``wert`` darf ``null`` sein. Das heisst *nicht messbar*, und der Fall wird dann benannt
mitgeführt statt stillschweigend verworfen.

Rückgabewert **1**, wenn die Kurve **nicht als Kalibrierung genügt** — leere Gruppe, zu
geringer Umfang, zu wenig Streuung oder nicht messbare Fälle. Die Tabelle wird trotzdem
gedruckt: Sie ist dann eine Zwischenauskunft, keine Grundlage für einen Entscheid.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import paarschwellen  # noqa: E402

REIHEN = {
    "rho": (paarschwellen.KANDIDATEN_RHO, "rho_maske_gerichtet"),
    "kantenanteil": (paarschwellen.KANDIDATEN_KANTENANTEIL, "kantenanteil"),
}


def _lies_faelle(pfad: Path) -> list[dict]:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    if isinstance(daten, dict):
        daten = daten.get("faelle")
    if not isinstance(daten, list):
        raise SystemExit(
            f"{pfad}: erwartet wird eine Liste von Faellen oder ein Satz mit dem "
            f"Schluessel 'faelle'.")
    return daten


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("faelle", type=Path, help="JSON-Datei mit den gemessenen Faellen")
    p.add_argument("--groesse", choices=sorted(REIHEN), default="rho",
                   help="welche Messgroesse — bestimmt die Kandidatenreihe")
    p.add_argument("--json", action="store_true", help="der ganze Satz als JSON")
    args = p.parse_args(argv)

    kandidaten, name = REIHEN[args.groesse]
    try:
        kurve = paarschwellen.trennkurve(_lies_faelle(args.faelle), kandidaten,
                                         groesse=name)
    except paarschwellen.PaarschwellenError as fehler:
        print(f"FEHLER: {fehler}", file=sys.stderr)
        return 2

    print(json.dumps(kurve, indent=2, ensure_ascii=False) if args.json
          else paarschwellen.bericht(kurve))
    return 0 if kurve["genuegt_als_kalibrierung"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
