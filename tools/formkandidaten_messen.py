#!/usr/bin/env python3
"""Die Formkandidaten für ein Bild rechnen — eigene und fremde Soll-Karten (Sitzung 73 §17).

Für die HomeStation gebaut: Sie hat die Bilder und die Blender-Berichte, wir haben die
Kandidaten (:mod:`aiimaging.formkandidaten`). Ein Aufruf je Bild; ``--fremd`` rechnet dasselbe
Bild zusätzlich gegen Soll-Karten **anderer** Fälle — die Kreuzpaare, die kein Auge brauchen.

Aufruf::

    python3 tools/formkandidaten_messen.py --bild B.png --bericht eigen/blender-report.json \\
        [--fremd a/blender-report.json] [--fremd-koerper c/blender-report.json] [--bild-id B14]

``--fremd`` ist eine Soll-Karte **desselben Körpers aus einem anderen Blick** (``fremd_art``
``nachbarblick``), ``--fremd-koerper`` die **eines anderen Körpers** (``anderer_koerper``). Die
beiden werden getrennt ausgewertet: Nach dem Bauwerk gerahmt gleichen sich Nachbarblicke stark
(Befund 194), ein anderer Körper nicht.

Ausgabe: eine JSON-Zeile je Soll-Karte, ``{"bild": ..., "eigen": true|false, "soll_von": ...,
<kandidaten>}`` — sie gehören so in die Liste ``kreuzpaare`` der Ergebnisdatei; die Zeile mit
``eigen: true`` zusätzlich in ``bilder``. Keine Pfade in der Ausgabe (Regel 3): ``soll_von``
ist der Name des Ordners, in dem der Bericht liegt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import formkandidaten  # noqa: E402


def messen(bild, bericht_pfad, *, eigen: bool, bild_id: str,
           fremd_art: str | None = None) -> dict:
    bericht = json.loads(Path(bericht_pfad).read_text(encoding="utf-8"))
    werte = formkandidaten.alle_aus_bericht(bild, bericht)
    zeile = {"bild": bild_id, "eigen": eigen,
             "soll_von": Path(bericht_pfad).resolve().parent.name}
    if fremd_art:
        zeile["fremd_art"] = fremd_art
    return {**zeile, **werte}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bild", required=True)
    ap.add_argument("--bericht", required=True, help="blender-report.json derselben Kamera")
    ap.add_argument("--fremd", action="append", default=[],
                    help="blender-report.json desselben Körpers, anderer Blick (mehrfach)")
    ap.add_argument("--fremd-koerper", action="append", default=[],
                    help="blender-report.json eines anderen Körpers (mehrfach)")
    ap.add_argument("--bild-id", default=None, help="Deckname, sonst der Dateiname")
    a = ap.parse_args(argv)
    bild_id = a.bild_id or Path(a.bild).stem
    print(json.dumps(messen(a.bild, a.bericht, eigen=True, bild_id=bild_id), ensure_ascii=False))
    for art, liste in (("nachbarblick", a.fremd), ("anderer_koerper", a.fremd_koerper)):
        for f in liste:
            print(json.dumps(messen(a.bild, f, eigen=False, bild_id=bild_id, fremd_art=art),
                             ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
