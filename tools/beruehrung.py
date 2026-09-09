#!/usr/bin/env python3
"""BERÜHRUNG — welche veröffentlichten Zahlen eine Änderung im Kern angeht.

Die dünne Schicht über :mod:`aiimaging.beruehrung` (Regel 4: die Fähigkeit liegt in der
Bibliothek, hier steht nur die Bedienung).

    python tools/beruehrung.py                 # alle Dokumente mit Codestand-Zeile
    python tools/beruehrung.py --nur-beruehrt  # nur, was man ansehen muss
    python tools/beruehrung.py --bis HEAD~5    # gegen einen anderen Endstand

Rückgabewert **1**, sobald ein Dokument berührt ist. Damit lässt sich der Lauf in eine
Kette hängen, ohne den Text zu lesen. *Ein unklares Dokument ist kein Fehler — es ist eine
Frage an seinen Verfasser, und die stellt kein Rückgabewert.*
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import beruehrung as ber      # noqa: E402

ZEICHEN = {ber.BERUEHRT: "ANSEHEN", ber.UNKLAR: "UNKLAR ", ber.UNBERUEHRT: "ruhig  "}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--docs", default="docs", help="Ordner der Dokumente (Vorgabe: docs)")
    p.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    p.add_argument("--bis", default="HEAD", help="Endstand des Vergleichs")
    p.add_argument("--nur-beruehrt", action="store_true",
                   help="nur Dokumente, deren Grundlage sich bewegt hat")
    a = p.parse_args(argv)

    reihe = ber.durchsicht(Path(a.repo) / a.docs, bis=a.bis, repo=a.repo)
    if a.nur_beruehrt:
        reihe = [s for s in reihe if s["zustand"] == ber.BERUEHRT]

    if not reihe:
        print("Kein Dokument zu melden.")
    for satz in reihe:
        print(f"{ZEICHEN[satz['zustand']]}  {satz['datei']}")
        print(f"          {satz['grund']}")

    fehlend = ber.ohne_grundlage(Path(a.repo) / a.docs)
    if fehlend:
        print(f"\nOHNE GRUNDLAGENZEILE ab {ber.STICHTAG_GRUNDLAGE.isoformat()}: "
              f"{', '.join(fehlend)}")
        print(f"          Eine Zeile «{ber.MARKE_GRUNDLAGE} <Module>» nachtragen — oder "
              f"«{ber.MARKE_GRUNDLAGE} keine», wenn das Dokument nichts an unserem Code "
              f"misst.")

    return 1 if any(s["zustand"] == ber.BERUEHRT for s in reihe) else 0


if __name__ == "__main__":
    raise SystemExit(main())
