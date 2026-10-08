#!/usr/bin/env python3
"""Erzeugt einen synthetischen **Splat** — eine 3D-Gaussian-Splatting-Datei (``.ply``).

Warum dieses Skript existiert
-----------------------------
Owner-Entscheid 76 (08.10.2026): Der Splat soll als **Umgebung** ins Bild. Ein echter
Splat ist eine Aufnahme eines echten Ortes — und genau das verbietet Regel 3 im Repo.
Gebraucht wird darum ein Splat, der **im Repo erzeugbar** ist, mit derselben Dateiform wie
ein echter: binäres PLY, je Punkt ``x y z nx ny nz f_dc_0..2 [f_rest_0..44] opacity
scale_0..2 rot_0..3`` — so, wie die verbreiteten Trainingsprogramme sie schreiben.

Reine stdlib, keine Abhängigkeit — dieselbe Wahl wie ``make_test_ifc.py``.

**In der glTF-Welt, nicht in der Blender-Welt.** Die Lage des Splats wird im Vertrag
(``RenderScene.context.transform``, Integrator 08.10.2026) in derselben Welt angegeben wie
das ``model.glb``: **Meter, Y oben**. Dieser Erzeuger schreibt darum in Y-oben-Koordinaten.
Im Bild landet der Splat nach der Drehung, die Blenders glTF-Import auch dem Modell gibt
(siehe ``blender_depth_stage._kontext_laden``). Wer hier in Z-oben schriebe, bekäme eine
Wand, die flach auf dem Boden liegt — und eine Massprobe sähe es nicht.

Was in der Datei steht (Lage relativ zu ``--ursprung``, Kantenlänge ``L = --groesse``)
-----------------------------------------------------------------------------------------
=============  ==========================================================  ==========
Teil           Lage (glTF: x rechts, y oben, −z hinten = Norden im Bild)    Anteil
=============  ==========================================================  ==========
Boden          L × L, y = 0, flache Gaussians, grün                        55 %
Wand           x ∈ ±0,3 L, y ∈ [0, 8], z = −0,4 L, rotbraun               25 %
Quader         Kante 3 m bei x = +0,3 L, z = −0,2 L, blau (ohne Unterseite) 12 %
Schwebeteile   x, z ∈ ±L/4, y ∈ [0,5, 3], Deckkraft fast null              Rest
=============  ==========================================================  ==========

**Die Schwebeteile sind die Probe für das Verwerfen.** Ihre Deckkraft liegt bei
``sigmoid(−6) ≈ 0,0025`` — weit unter der Schwelle des Runners. Sie stehen absichtlich
auch **vor** dem Bauwerk: Würden sie nicht verworfen, verdeckten sie es, und die
Bauwerksmaske mit Splat wiche von der ohne ab.

Aufruf:
    python3 tools/make_test_splat.py ziel.ply [--punkte 20000] [--startwert 7]
        [--ursprung x,y,z] [--groesse 30] [--mit-f-rest]
"""
from __future__ import annotations

import argparse
import math
import random
import struct
import sys
from pathlib import Path

#: Der Koeffizient der Kugelflächenfunktion nullten Grades, ``1 / (2·√π)``. Mit ihm wird
#: aus einer Farbe der Wert ``f_dc`` — der Runner rechnet ``0,5 + C0 · f_dc`` zurück.
SH_C0 = 0.28209479177387814

#: Anteile der Teile an der Punktzahl. Der Rest sind Schwebeteile.
ANTEIL_BODEN, ANTEIL_WAND, ANTEIL_QUADER = 0.55, 0.25, 0.12

#: Grundfarben (0..1). Deutlich verschieden, damit ein Bild zeigt, welcher Teil wo landet.
FARBE_BODEN = (0.35, 0.55, 0.25)
FARBE_WAND = (0.60, 0.30, 0.22)
FARBE_QUADER = (0.20, 0.35, 0.75)
FARBE_SCHWEBE = (1.00, 1.00, 1.00)

#: Deckkraft als Logit (so steht sie in der Datei). ``sigmoid(4) ≈ 0,982``,
#: ``sigmoid(−6) ≈ 0,0025``.
OPAZITAET_DICHT = 4.0
OPAZITAET_SCHWEBE = -6.0

WAND_HOEHE = 8.0
QUADER_KANTE = 3.0
#: Dicke der flachen Gaussians quer zur Fläche (Meter).
FLACH = 0.01

#: Anzahl der höheren SH-Koeffizienten bei ``--mit-f-rest`` (Grad 3: 3 · 15).
F_REST = 45


def eigenschaften(mit_f_rest: bool) -> list[str]:
    """Die Spaltennamen in der Reihenfolge der Datei."""
    namen = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2"]
    if mit_f_rest:
        namen += [f"f_rest_{i}" for i in range(F_REST)]
    namen += ["opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    return namen


def _f_dc(farbe, zufall: random.Random) -> list[float]:
    """Farbe → ``f_dc`` (SH-Grad 0), mit einem Hauch Streuung je Punkt."""
    return [(min(1.0, max(0.0, k + zufall.uniform(-0.04, 0.04))) - 0.5) / SH_C0
            for k in farbe]


def _anzahlen(punkte: int) -> dict:
    boden = int(punkte * ANTEIL_BODEN)
    wand = int(punkte * ANTEIL_WAND)
    quader = int(punkte * ANTEIL_QUADER)
    return {"boden": boden, "wand": wand, "quader": quader,
            "schwebe": punkte - boden - wand - quader}


def erzeuge_splat(ziel, *, punkte: int = 20000, startwert: int = 7,
                  ursprung=(0.0, 0.0, 0.0), groesse: float = 30.0,
                  mit_f_rest: bool = False) -> dict:
    """Den Splat schreiben und beschreiben, was darin steht.

    Returns:
        ``{pfad, punkte, anzahlen, dicht, schwebe, huellbox_dicht}`` — die Hüllbox der
        **dichten** Punkte (ohne Schwebeteile) in glTF-Koordinaten, nur über die
        Mittelpunkte. Gegen sie prüft die Probe, wo der Runner den Splat hingelegt hat.

    Raises:
        ValueError: zu wenige Punkte für alle vier Teile, oder keine positive Grösse.
    """
    if punkte < 40:
        raise ValueError(f"punkte={punkte}: Unter 40 bleibt ein Teil leer.")
    if not groesse > 0.0:
        raise ValueError(f"groesse={groesse}: Die Kantenlänge muss positiv sein.")
    zufall = random.Random(startwert)
    ox, oy, oz = (float(v) for v in ursprung)
    L = float(groesse)
    n = _anzahlen(punkte)
    zeilen: list[tuple] = []

    def punkt(x, y, z, farbe, skala, opazitaet):
        zeilen.append((x + ox, y + oy, z + oz, _f_dc(farbe, zufall),
                       [math.log(s) for s in skala], opazitaet))

    # Boden — die Gaussians so gross wie der Punktabstand, damit eine Fläche entsteht.
    abstand = L / math.sqrt(n["boden"])
    breit = abstand * 0.6
    for _ in range(n["boden"]):
        punkt(zufall.uniform(-L / 2, L / 2), 0.0, zufall.uniform(-L / 2, L / 2),
              FARBE_BODEN, (breit, FLACH, breit), OPAZITAET_DICHT)

    # Wand hinten (−z), senkrecht.
    wand_b = 0.6 * L
    abstand = math.sqrt(wand_b * WAND_HOEHE / n["wand"])
    breit = abstand * 0.6
    for _ in range(n["wand"]):
        punkt(zufall.uniform(-wand_b / 2, wand_b / 2), zufall.uniform(0.0, WAND_HOEHE),
              -0.4 * L, FARBE_WAND, (breit, breit, FLACH), OPAZITAET_DICHT)

    # Quader: fünf Flächen (ohne Unterseite), nach Fläche gleich verteilt.
    cx, cz, h = 0.3 * L, -0.2 * L, QUADER_KANTE / 2
    abstand = math.sqrt(5 * QUADER_KANTE ** 2 / n["quader"])
    breit = abstand * 0.6
    for _ in range(n["quader"]):
        seite = zufall.randrange(5)
        u, v = zufall.uniform(-h, h), zufall.uniform(-h, h)
        if seite == 0:                                   # oben
            p, s = (cx + u, QUADER_KANTE, cz + v), (breit, FLACH, breit)
        elif seite in (1, 2):                            # ±x
            p = (cx + (h if seite == 1 else -h), h + v, cz + u)
            s = (FLACH, breit, breit)
        else:                                            # ±z
            p = (cx + u, h + v, cz + (h if seite == 3 else -h))
            s = (breit, breit, FLACH)
        punkt(*p, FARBE_QUADER, s, OPAZITAET_DICHT)

    # Schwebeteile — fast durchsichtig, auch vor dem Bauwerk. Siehe Modulkopf.
    for _ in range(n["schwebe"]):
        punkt(zufall.uniform(-L / 4, L / 4), zufall.uniform(0.5, 3.0),
              zufall.uniform(-L / 4, L / 4), FARBE_SCHWEBE, (0.3, 0.3, 0.3),
              OPAZITAET_SCHWEBE)

    namen = eigenschaften(mit_f_rest)
    kopf = ("ply\nformat binary_little_endian 1.0\n"
            "comment synthetischer Splat, tools/make_test_splat.py (Regel 3)\n"
            f"element vertex {len(zeilen)}\n"
            + "".join(f"property float {name}\n" for name in namen)
            + "end_header\n").encode("ascii")
    form = struct.Struct("<" + "f" * len(namen))
    rest = [0.0] * (F_REST if mit_f_rest else 0)
    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "wb") as datei:
        datei.write(kopf)
        for x, y, z, dc, skala, opa in zeilen:
            datei.write(form.pack(x, y, z, 0.0, 0.0, 0.0, *dc, *rest, opa, *skala,
                                  1.0, 0.0, 0.0, 0.0))

    dicht = zeilen[:len(zeilen) - n["schwebe"]]
    lo = [min(z[i] for z in dicht) for i in range(3)]
    hi = [max(z[i] for z in dicht) for i in range(3)]
    return {"pfad": str(ziel), "punkte": len(zeilen), "anzahlen": n,
            "dicht": len(dicht), "schwebe": n["schwebe"], "huellbox_dicht": [lo, hi]}


def _punkt(text: str) -> tuple[float, float, float]:
    teile = [t.strip() for t in text.split(",")]
    if len(teile) != 3:
        raise argparse.ArgumentTypeError(f"drei Zahlen 'x,y,z' erwartet, war {text!r}")
    return tuple(float(t) for t in teile)  # type: ignore[return-value]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ziel")
    ap.add_argument("--punkte", type=int, default=20000)
    ap.add_argument("--startwert", type=int, default=7)
    ap.add_argument("--ursprung", type=_punkt, default=(0.0, 0.0, 0.0),
                    help="Verschiebung 'x,y,z' in der glTF-Welt (Meter, Y oben)")
    ap.add_argument("--groesse", type=float, default=30.0, help="Kantenlänge des Bodens (m)")
    ap.add_argument("--mit-f-rest", action="store_true",
                    help="auch die 45 höheren SH-Koeffizienten schreiben (alle null)")
    a = ap.parse_args(argv)
    try:
        befund = erzeuge_splat(a.ziel, punkte=a.punkte, startwert=a.startwert,
                               ursprung=a.ursprung, groesse=a.groesse,
                               mit_f_rest=a.mit_f_rest)
    except ValueError as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2
    print(f"{befund['pfad']}  ({befund['punkte']} Punkte, davon {befund['schwebe']} "
          f"fast durchsichtig)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
