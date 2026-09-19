#!/usr/bin/env python3
"""RUECKSTAU ÜBER BEIDE ABLAGEN — was hier offen ist, und was davon drüben beantwortet.

Die dünne Schicht über :mod:`aiimaging.rueckstau`. Sie rechnet nichts; sie zeigt.

**Wozu es sie gibt** (eigener Fehler vom 19.09.2026): Ein Auftrag galt hier als
unbeantwortet, weil in diesem Baum keine Antwort lag. Sie lag im anderen Repo. Daraus
wurde ein Vorwurf, und der Vorwurf war falsch. Gemessen am selben Tag: **neun von 33**
hier offenen Aufträgen tragen drüben eine Antwort.

    python tools/rueckstau.py                      # Standardpfad daneben
    python tools/rueckstau.py --fremd ../anderes   # anderer Ort
    python tools/rueckstau.py --json               # für ein Werkzeug

**Rückgabewert immer 0.** Das hier ist ein Melder, kein Torwächter: Ein Rückstand ist
kein Fehler, sondern ein verteilter Auftrag. Rot würde hier nur bedeuten «es gibt noch
Arbeit», und das ist der Normalfall.

**Findet es den zweiten Baum nicht, sagt es das** — in der ersten Zeile, nicht in einer
Fussnote. Der `cloud`-Worker hat ihn nicht, und eine Zahl ohne diesen Vorbehalt wäre
dort wieder die halbe Auskunft, die den Vorwurf erzeugt hat.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag, rueckstau  # noqa: E402

#: Wo der zweite Baum üblicherweise liegt: neben diesem Repo.
FREMD_VORGABE = Path(__file__).resolve().parents[2] / "Architektur-Cosmos"


def _zeilen(bericht: dict, wurzel: Path) -> list[str]:
    aus: list[str] = []
    if not bericht["fremdbaum_gesehen"]:
        aus += ["!! " + bericht["vorbehalt"],
                f"   gesucht unter: {bericht['fremdbaum'] or '(kein Pfad angegeben)'}", ""]
    aus.append(f"OFFEN NACH HAUSREGEL: {len(bericht['offen'])}")
    aus.append(f"DRUEBEN BEANTWORTET : {len(bericht['anderswo_beantwortet'])}")
    for k in sorted(bericht["anderswo_beantwortet"]):
        aus.append(f"      {k}")
    aus.append(f"WIRKLICH OFFEN      : {len(bericht['wirklich_offen'])}")

    saetze = {a["auftrag_id"]: a for a in auftrag.offene_auftraege(wurzel)}
    nach_worker: dict[str, int] = {}
    for k in bericht["wirklich_offen"]:
        w = str(saetze.get(k, {}).get("worker") or "ohne Adressat")
        nach_worker[w] = nach_worker.get(w, 0) + 1
    for w, n in sorted(nach_worker.items(), key=lambda x: -x[1]):
        aus.append(f"      {n:3}  {w}")
    return aus


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--fremd", default=str(FREMD_VORGABE),
                   help="Wurzel des zweiten Ablagebaums (Vorgabe: Nachbarverzeichnis)")
    p.add_argument("--wurzel", default=".", help="Dieses Repo")
    p.add_argument("--json", action="store_true", help="Bericht als JSON")
    a = p.parse_args(argv)

    wurzel = Path(a.wurzel)
    bericht = rueckstau.rueckstau(wurzel, a.fremd)
    if a.json:
        print(json.dumps(bericht, indent=2, ensure_ascii=False))
    else:
        print("\n".join(_zeilen(bericht, wurzel)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
