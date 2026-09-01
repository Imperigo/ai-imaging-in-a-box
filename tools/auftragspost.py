#!/usr/bin/env python3
"""AUFTRAGSPOST — einen Auftrag als **einen** Block, den man weiterreichen kann.

Die dünne Schicht über :mod:`aiimaging.auftragspost`.

**Wozu es sie gibt** (27.08.2026): Zwei der drei Worker lesen unser Repo — die HomeStation
und der UI-Worker. **Der Cloud-Worker hat es nicht.** Damit liegt jeder
`worker: "cloud"`-Auftrag an einer Stelle, die sein Adressat nicht lesen kann, und der
einzige Bote ist der Owner. Ihm einen Dateipfad zu nennen, hilft nicht; er braucht einen
Text.

*Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm — er ist
einer bei uns.*

    python tools/auftragspost.py cloud            # alle offenen an den Cloud-Worker
    python tools/auftragspost.py cloud --neueste  # nur den juengsten
    python tools/auftragspost.py --auftrag auf-20260827-63

Rückgabewert **1**, wenn zum gewählten Adressaten nichts offen ist. Das ist kein Fehler,
aber es soll sich von «hier ist dein Block» unterscheiden lassen, ohne den Text zu lesen.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag as _auftrag       # noqa: E402
from aiimaging import auftragspost              # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("worker", nargs="?", choices=sorted(_auftrag.WORKER),
                   help="Adressat. Ohne ihn ist --auftrag noetig — «alle Blocks auf "
                        "einmal» ist beim Weiterreichen fast nie gemeint.")
    p.add_argument("--auftrag", help="genau diese Kennung, egal ob offen oder beantwortet")
    p.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    p.add_argument("--neueste", action="store_true", help="nur den juengsten Auftrag")
    p.add_argument("--nach", type=Path,
                   help="Blocks als <kennung>.md in dieses Verzeichnis schreiben, statt "
                        "sie zu drucken. Der Pfad wird NICHT im Repo festgeschrieben — "
                        "er zeigt auf ein fremdes Repo, und dessen Aufbau gehoert nicht "
                        "in unser oeffentliches.")
    a = p.parse_args(argv)

    if not a.worker and not a.auftrag:
        p.error("Entweder ein Adressat oder --auftrag.")

    if a.auftrag:
        datei = _finde(Path(a.repo), a.auftrag)
        if datei is None:
            print(f"FEHLER: {a.auftrag} liegt weder unter auftraege/offen noch unter "
                  f"auftraege/ergebnisse.", file=sys.stderr)
            return 2
        # `--nach` GILT AUCH HIER, und das war es zuerst nicht: Dieser Zweig kehrte
        # vor der Ablage um und druckte den Block, obwohl ein Zielverzeichnis dastand.
        # Ein Schalter ohne Wirkung ist schlimmer als keiner — er sagt, etwas sei
        # geschehen. Gefunden am 01.09.2026 beim ersten Gebrauch mit --auftrag.
        block = [(a.auftrag, auftragspost.block(
            json.loads(datei.read_text(encoding="utf-8"))))]
        if a.nach:
            for ziel in auftragspost.lege_ab(block, a.nach):
                print(f"geschrieben: {ziel.name}")
            return 0
        print(block[0][1])
        return 0

    blocks = auftragspost.offene_blocks(a.repo, worker=a.worker)
    if not blocks:
        print(f"Nichts offen fuer {a.worker!r}. Es gibt nichts weiterzureichen.")
        return 1
    if a.neueste:
        blocks = blocks[-1:]

    if a.nach:
        for ziel in auftragspost.lege_ab(blocks, a.nach):
            print(f"geschrieben: {ziel.name}")
        return 0

    for i, (kennung, text) in enumerate(blocks):
        if i:
            print("\n")
        print(text)
    return 0


def _finde(wurzel: Path, kennung: str) -> Path | None:
    for ordner in ("offen", "ergebnisse"):
        pfad = wurzel / "auftraege" / ordner / f"{kennung}.json"
        if pfad.exists():
            return pfad
    return None


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
