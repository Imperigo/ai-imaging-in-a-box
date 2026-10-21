#!/usr/bin/env python3
"""Einen nachgewiesenen Fehleintrag im Gerätebuch zurücknehmen (Befund auf-20261021-311 B1).

    python3 tools/geraetebuch_bereinigen.py <geraete.json> --zuletzt-um <unix-s> [--art ipad] [--weg mac]

Nur bei **gestopptem Dienst** laufen lassen — der Dienst hält das Buch im Arbeitsspeicher und
schriebe den alten Stand sonst zurück. Ohne ``--ja`` wird nur gezeigt, was geschähe.
``--zuletzt-um`` ist der Wert, der jetzt in der Datei steht (auf die Sekunde); passt er nicht,
ändert das Werkzeug nichts (:func:`aiimaging.geraetebuch.bereinige_fehleintrag`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import geraetebuch  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("datei")
    ap.add_argument("--zuletzt-um", type=float, required=True)
    ap.add_argument("--art", default="ipad")
    ap.add_argument("--weg", default="mac")
    ap.add_argument("--ja", action="store_true", help="wirklich schreiben")
    a = ap.parse_args(argv)
    buch = geraetebuch.lies(a.datei)
    befund = geraetebuch.bereinige_fehleintrag(buch, a.art, zuletzt_um=a.zuletzt_um, weg=a.weg)
    befund["geschrieben"] = bool(befund["bereinigt"] and a.ja)
    if befund["geschrieben"]:
        geraetebuch.schreibe(a.datei, geraetebuch.zum_schreiben(buch))
    print(json.dumps(befund, ensure_ascii=False, indent=1, sort_keys=True))
    return 0 if befund["bereinigt"] else 1


if __name__ == "__main__":
    sys.exit(main())
