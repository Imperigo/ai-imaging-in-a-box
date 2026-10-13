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

**Form «strasse»** (``--form strasse``, 13.10.2026): ein Strassenraum wie die echte Aufnahme
hinter ``auf-20261013-275`` — lang und schmal statt quadratisch. Boden 0,4 L × 2,5 L (entlang z),
zwei Wände bei x = ±0,2 L über die ganze Länge, zwei Quader auf der Strasse
(x = −0,1 L, z = −0,625 L und x = +0,1 L, z = +0,5 L), Schwebeteile dazwischen. Gleiche Anteile.
Dort sieht ein Ring in der Mitte die Wände nur streifend und hinter den Quadern nichts — die
Probe für die Blickwinkel aus der Aufnahme (``tools/make_test_colmap.py --weg linie``).

**Die Person** (``--person N``, 13.10.2026, nach ``auf-20261013-276``): Am echten Splat stand
die gefilmte Person samt Arm als Wolke nah vor den Kameras, und die TSDF machte daraus
Fetzen. Mit ``--person N`` kommt je Augenblick des Rig-Wegs (``--person-augenblicke``,
derselbe Weg wie ``make_test_colmap.py``) eine kleine, dichte Wolke aus ``N`` Gaussians dazu,
gelb, an jedem Augenblick woanders (``make_test_colmap.person_wolke``) — **alle zugleich**, wie
ein Training sie hinterlässt. Sie zählen zu den dichten Punkten.

**Die Schwebeteile sind die Probe für das Verwerfen.** Ihre Deckkraft liegt bei
``sigmoid(−6) ≈ 0,0025`` — weit unter der Schwelle des Runners. Sie stehen absichtlich
auch **vor** dem Bauwerk: Würden sie nicht verworfen, verdeckten sie es, und die
Bauwerksmaske mit Splat wiche von der ohne ab.

Aufruf:
    python3 tools/make_test_splat.py ziel.ply [--punkte 20000] [--startwert 7]
        [--ursprung x,y,z] [--groesse 30] [--mit-f-rest] [--form platz|strasse]
        [--person 12] [--person-augenblicke 80]
"""
from __future__ import annotations

import argparse
import importlib.util
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
FARBE_PERSON = (0.95, 0.85, 0.20)

#: Deckkraft als Logit (so steht sie in der Datei). ``sigmoid(4) ≈ 0,982``,
#: ``sigmoid(−6) ≈ 0,0025``.
OPAZITAET_DICHT = 4.0
OPAZITAET_SCHWEBE = -6.0

#: Deckkraft der Person als Logit: ``sigmoid(0,4) ≈ 0,60``. Halb durchsichtig, weil ein
#: Training eine Person, die sich mit der Kamera bewegt, nie scharf lernt — jeder Augenblick
#: widerspricht dem vorigen, und es bleibt eine **Wolke** (``auf-20261013-276``: «die Person
#: samt Arm steht als Wolke nah vor den Kameras»). Über ``DECKKRAFT_DICHT`` und
#: ``DECKKRAFT_LEER`` des Runners: Sie zählt als dicht, und der Ersatzrenderer zeichnet sie.
#: Wo sich zwei Wölkchen überlagern, springt die Tiefe — das Sprenkeln aus 276.
OPAZITAET_PERSON = 0.4

WAND_HOEHE = 8.0
QUADER_KANTE = 3.0
#: Dicke der flachen Gaussians quer zur Fläche (Meter).
FLACH = 0.01

#: Anzahl der höheren SH-Koeffizienten bei ``--mit-f-rest`` (Grad 3: 3 · 15).
F_REST = 45

#: Die Formen der Szene (Modulkopf).
FORMEN = ("platz", "strasse")


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


def _colmap_erzeuger():
    """``make_test_colmap.py`` daneben, über den Pfad — dort steht der Weg des Rigs und die
    Person, damit Splat und Aufnahme dieselben Stellen meinen."""
    pfad = Path(__file__).resolve().with_name("make_test_colmap.py")
    spez = importlib.util.spec_from_file_location("make_test_colmap_person", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _personen(n: int, augenblicke: int, form: str, groesse: float) -> list[tuple]:
    """Alle Personenwolken des Rig-Wegs, ``(x, y, z, σ)`` je Gaussian (Modulkopf)."""
    if n <= 0:
        return []
    c = _colmap_erzeuger()
    aus = []
    for a, (auge, vorn) in enumerate(c.rig_weg(augenblicke, form=form, groesse=groesse)):
        aus.extend(c.person_wolke(a, auge, vorn, n))
    return aus


def erzeuge_splat(ziel, *, punkte: int = 20000, startwert: int = 7,
                  ursprung=(0.0, 0.0, 0.0), groesse: float = 30.0,
                  mit_f_rest: bool = False, form: str = "platz", person: int = 0,
                  person_augenblicke: int = 80) -> dict:
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
    if form not in FORMEN:
        raise ValueError(f"form={form!r}: bekannt sind {FORMEN}.")
    zufall = random.Random(startwert)
    ox, oy, oz = (float(v) for v in ursprung)
    L = float(groesse)
    n = _anzahlen(punkte)
    zeilen: list[tuple] = []

    def punkt(x, y, z, farbe, skala, opazitaet):
        zeilen.append((x + ox, y + oy, z + oz, _f_dc(farbe, zufall),
                       [math.log(s) for s in skala], opazitaet))

    personen = _personen(person, person_augenblicke, form, L)
    n["person"] = len(personen)

    def personen_schreiben():
        for x, y, z, sigma in personen:
            punkt(x, y, z, FARBE_PERSON, (sigma, sigma, sigma), OPAZITAET_PERSON)

    if form == "strasse":
        _strasse(punkt, n, L, zufall, personen_schreiben)
        return _schreiben(ziel, zeilen, n, mit_f_rest)

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
    personen_schreiben()

    # Schwebeteile — fast durchsichtig, auch vor dem Bauwerk. Siehe Modulkopf.
    for _ in range(n["schwebe"]):
        punkt(zufall.uniform(-L / 4, L / 4), zufall.uniform(0.5, 3.0),
              zufall.uniform(-L / 4, L / 4), FARBE_SCHWEBE, (0.3, 0.3, 0.3),
              OPAZITAET_SCHWEBE)
    return _schreiben(ziel, zeilen, n, mit_f_rest)


def _quader(punkt, anzahl: int, cx: float, cz: float, zufall: random.Random) -> None:
    """Ein Quader der Kante ``QUADER_KANTE``: fünf Flächen (ohne Unterseite), gleich verteilt."""
    h = QUADER_KANTE / 2
    abstand = math.sqrt(5 * QUADER_KANTE ** 2 / max(1, anzahl))
    breit = abstand * 0.6
    for _ in range(anzahl):
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


def _strasse(punkt, n: dict, L: float, zufall: random.Random, personen_schreiben) -> None:
    """Die Form «strasse» (Modulkopf): Boden, zwei Wände, zwei Quader, Schwebeteile."""
    b, s = 0.4 * L, 2.5 * L                              # Breite (x) und Länge (z)
    abstand = math.sqrt(b * s / n["boden"])
    breit = abstand * 0.6
    for _ in range(n["boden"]):
        punkt(zufall.uniform(-b / 2, b / 2), 0.0, zufall.uniform(-s / 2, s / 2),
              FARBE_BODEN, (breit, FLACH, breit), OPAZITAET_DICHT)
    abstand = math.sqrt(2 * s * WAND_HOEHE / n["wand"])
    breit = abstand * 0.6
    for i in range(n["wand"]):
        punkt(b / 2 if i % 2 else -b / 2, zufall.uniform(0.0, WAND_HOEHE),
              zufall.uniform(-s / 2, s / 2), FARBE_WAND, (FLACH, breit, breit), OPAZITAET_DICHT)
    halb = n["quader"] // 2
    _quader(punkt, halb, -0.25 * b, -0.25 * s, zufall)
    _quader(punkt, n["quader"] - halb, 0.25 * b, 0.2 * s, zufall)
    personen_schreiben()                                 # vor den Schwebeteilen: dicht
    for _ in range(n["schwebe"]):
        punkt(zufall.uniform(-0.4 * b, 0.4 * b), zufall.uniform(0.5, 3.0),
              zufall.uniform(-s / 4, s / 4), FARBE_SCHWEBE, (0.3, 0.3, 0.3),
              OPAZITAET_SCHWEBE)


def _schreiben(ziel, zeilen: list, n: dict, mit_f_rest: bool) -> dict:
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
            "dicht": len(dicht), "schwebe": n["schwebe"], "person": n.get("person", 0),
            "huellbox_dicht": [lo, hi]}


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
    ap.add_argument("--form", choices=FORMEN, default="platz",
                    help="platz (quadratisch, Vorgabe) oder strasse (lang und schmal)")
    ap.add_argument("--person", type=int, default=0,
                    help="Gaussians der gefilmten Person je Augenblick (0 = keine Person)")
    ap.add_argument("--person-augenblicke", type=int, default=80,
                    help="Augenblicke des Rig-Wegs, wie make_test_colmap.py --augenblicke")
    a = ap.parse_args(argv)
    try:
        befund = erzeuge_splat(a.ziel, punkte=a.punkte, startwert=a.startwert,
                               ursprung=a.ursprung, groesse=a.groesse,
                               mit_f_rest=a.mit_f_rest, form=a.form, person=a.person,
                               person_augenblicke=a.person_augenblicke)
    except ValueError as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2
    print(f"{befund['pfad']}  ({befund['punkte']} Punkte, davon {befund['schwebe']} "
          f"fast durchsichtig)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
