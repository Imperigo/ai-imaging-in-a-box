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

#: Wo die Beweisskripte ihre Bilder ablegen.
BEWEISE = "build/beweis"


def aufloesen(kennung: str, wurzel=WURZEL):
    """Aus ``<ordner>/<index>`` die eine Datei, die dahinter steht — oder ``None``.

    **Warum die Karte keine Dateinamen mehr führt** (gemessen am 16.09.2026). Die
    Beweisskripte schreiben ihre **Messwerte in den Dateinamen** — das ist Absicht und
    gut so::

        03_regel3_waechter_dateien-542_treffer-0.png     (09.09.2026)
        03_regel3_waechter_dateien-626_treffer-0.png     (16.09.2026)

    Dasselbe Bild, andere Zahl: Das Repo ist gewachsen. Ebenso bei den Laufzeiten der
    Kette und den Augenpunkten der Innenräume. Eine Karte auf **vollen Dateinamen** hält
    das keinen Nachbau lang — nach dem Verlust von ``build/`` fanden fünf von 23
    Einträgen ihre Datei nicht mehr, **obwohl das Bild neu erzeugt dastand.**

    Die stabile Kennung ist ``<Ordner>/<Index>``; der Rest des Namens ist Messwert.

    Raises:
        SystemExit: mehr als eine Datei unter derselben Kennung. Dann ist nicht
            entscheidbar, welche gemeint war — und eine beliebige zu nehmen hiesse, die
            Auswahl dem Zufall der Sortierung zu überlassen.
    """
    ordner, _, index = str(kennung).partition("/")   # index ist ein Muster, kein Name
    ziel = Path(wurzel) / BEWEISE / ordner
    if not ziel.is_dir():
        return None
    treffer = sorted(ziel.glob(f"{index}.png"))
    if len(treffer) > 1:
        raise SystemExit(
            f"{kennung}: {len(treffer)} Dateien tragen diesen Index — "
            + ", ".join(t.name for t in treffer)
            + ". Welche gemeint ist, sagt die Karte nicht, und eine beliebige zu nehmen "
              "hiesse, die Auswahl der Sortierung zu ueberlassen.")
    return treffer[0] if treffer else None


def fehlende(karte: dict, wurzel=WURZEL) -> list[tuple[str, str]]:
    """``(Zielname, Kennung)`` für alles, was nicht dasteht."""
    return [(ziel, kennung) for ziel, kennung in sorted(karte.items())
            if aufloesen(kennung, wurzel) is None]


def hole(karte: dict, nach: Path, wurzel=WURZEL) -> list[str]:
    """Kopiert, was da ist. Gibt die kopierten Zielnamen zurück."""
    nach.mkdir(parents=True, exist_ok=True)
    kopiert = []
    for ziel, kennung in sorted(karte.items()):
        q = aufloesen(kennung, wurzel)
        if q is not None:
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
        beweise = sorted({k.split("/")[0] for _, k in luecken if "/" in k})
        for ziel, kennung in luecken:
            print(f"  {ziel:<22} {BEWEISE}/{kennung}.png", file=sys.stderr)
        print(f"\nZu fahren: {', '.join('tools/beweis/' + b + '.py' for b in beweise)}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
