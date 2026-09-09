#!/usr/bin/env python3
"""Die Bilder der Schlusspräsentation aus dem Beweisgang holen.

**Warum es dieses Skript gibt.** Die 36 Bilder liegen unter `build/` — erzeugt, nicht
versioniert (Regel 3, und sie sind zusammen 1,5 MB). Die **Auswahl** dagegen ist eine
Entscheidung und muss den Container überleben: welches der 205 Beweisbilder auf welche
Folie kommt, steht in `bilder.json`.

*Ohne diese Datei wäre die Präsentation nach jedem Neustart von Hand neu zusammenzusuchen —
und was man von Hand zusammensucht, sucht man irgendwann nicht mehr zusammen.*

    python praesentation/hole_bilder.py            # nach praesentation/bilder/
    python praesentation/hole_bilder.py --pruefen  # nur sagen, was fehlt

**Was fehlt, wird gemeldet und nicht übergangen.** Ein fehlendes Bild ergibt eine Folie
mit einem leeren Kasten, und die sieht aus wie eine Gestaltungsentscheidung. Rückgabewert
**1**, sobald etwas fehlt; die fehlenden Beweise werden mit dem Skript genannt, das sie
erzeugt.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KARTE = Path(__file__).resolve().parent / "bilder.json"


def fehlende(karte: dict, wurzel=WURZEL) -> list[tuple[str, str]]:
    """``(Zielname, Quellpfad)`` für alles, was nicht dasteht."""
    return [(ziel, quelle) for ziel, quelle in sorted(karte.items())
            if not (Path(wurzel) / quelle).is_file()]


def hole(karte: dict, nach: Path, wurzel=WURZEL) -> list[str]:
    """Kopiert, was da ist. Gibt die kopierten Zielnamen zurück."""
    nach.mkdir(parents=True, exist_ok=True)
    kopiert = []
    for ziel, quelle in sorted(karte.items()):
        q = Path(wurzel) / quelle
        if q.is_file():
            shutil.copy2(q, nach / ziel)
            kopiert.append(ziel)
    return kopiert


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--nach", type=Path, default=Path(__file__).resolve().parent / "bilder",
                   help="Zielordner (Vorgabe: praesentation/bilder)")
    p.add_argument("--pruefen", action="store_true",
                   help="nichts kopieren, nur melden, was fehlt")
    a = p.parse_args(argv)

    karte = json.loads(KARTE.read_text(encoding="utf-8"))
    luecken = fehlende(karte)

    if not a.pruefen:
        kopiert = hole(karte, a.nach)
        print(f"{len(kopiert)} von {len(karte)} Bildern nach {a.nach.name}/ kopiert.")

    if luecken:
        print(f"\nES FEHLEN {len(luecken)} von {len(karte)}:", file=sys.stderr)
        beweise = sorted({q.split("/")[2] for _, q in luecken if q.count("/") > 2})
        for ziel, quelle in luecken:
            print(f"  {ziel:<22} {quelle}", file=sys.stderr)
        print(f"\nZu fahren: {', '.join('tools/beweis/' + b + '.py' for b in beweise)}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
