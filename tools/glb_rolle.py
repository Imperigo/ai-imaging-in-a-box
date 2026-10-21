#!/usr/bin/env python3
"""Einem Knoten einer glb eine Rolle geben (``extras.role``) — als Kopie, die Quelle bleibt.

Die dünne Schicht über :func:`aiimaging.kosmo_szene.glb_mit_rolle`. Anlass: die Steine-Probe
(auf-20261021-316, B3) — ihr Boden heisst «boden» und trägt noch keine Rolle.

    python tools/glb_rolle.py <quelle.glb> <ziel.glb> --knoten boden [--rolle ground]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import kosmo_szene  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("quelle")
    ap.add_argument("ziel")
    ap.add_argument("--knoten", required=True)
    ap.add_argument("--rolle", default=kosmo_szene.GELAENDE_ROLLEN[0])
    a = ap.parse_args(argv)
    if Path(a.quelle).resolve() == Path(a.ziel).resolve():
        print("Ziel und Quelle sind dieselbe Datei — die Quelle bleibt unberuehrt.",
              file=sys.stderr)
        return 2
    print(json.dumps(kosmo_szene.glb_mit_rolle(a.quelle, a.ziel, a.knoten, a.rolle),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
