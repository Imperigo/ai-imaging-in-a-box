#!/usr/bin/env python3
"""Erzeugt eine synthetische **COLMAP-Aufnahme** (``sparse/0``) passend zu ``make_test_splat.py``.

Warum dieses Skript existiert
-----------------------------
13.10.2026, nach ``auf-20261013-275``: Die Splat-Brücke nimmt ihre Blickwinkel aus den Kameras
der Aufnahme, mit der der Splat trainiert wurde. Eine echte Aufnahme ist ein echter Ort —
Regel 3 verbietet sie im Repo. Gebraucht wird darum eine, die **im Repo erzeugbar** ist, in
derselben Form wie die der HomeStation: COLMAP 4.x **mit Rig** — vier Kameras (vorn, rechts,
hinten, links), die zusammen einen Weg abgehen; je Augenblick ein Bild jeder Kamera, Modell
PINHOLE, quadratisch.

Reine stdlib, keine Abhängigkeit (wie ``make_test_splat.py``). Das Format ist dasselbe, das
COLMAP 4 schreibt (an pycolmap 4.2.1 nachgeprüft, 13.10.2026): ``cameras``, ``images`` (mit der
fertigen Pose je Bild), ``frames``, ``rigs``, ``points3D`` — binär oder als Text.

Was darin steht (Welt des synthetischen Splats: Meter, Y oben)
---------------------------------------------------------------
* **Weg:** zur Form ``platz`` ein Kreis vom Halbmesser ``radius`` um den Ursprung, zur Form
  ``strasse`` die Mittellinie der Strasse über 80 % ihrer Länge (wie ``make_test_splat.py
  --form``); auf Augenhöhe. Die vordere Kamera blickt in Gehrichtung, die anderen sind um je
  90° gedreht (ein starres Rig).
* **Punkte:** Stichproben derselben Flächen wie im Splat — Boden, Wand, Quaderdach —, mit
  leichtem Rauschen, je mit einer Spur aus zwei Beobachtungen.
* ``versatz`` verschiebt die ganze Aufnahme (Kameras und Punkte): die Gegenprobe für die
  Gleichheitsprüfung.

Die Person und ihre Masken (13.10.2026, nach ``auf-20261013-276``)
-----------------------------------------------------------------
Am echten Splat stand **die gefilmte Person samt Arm als Wolke nah vor den Kameras**, und die
TSDF machte daraus Fetzen. :func:`person_wolke` beschreibt eine solche Person: eine kleine,
dichte Wolke aus Körper und Arm, die mit dem Rig mitgeht — **in jedem Augenblick an anderer
Stelle** um das Rig, 0,7 bis 1,0 m vom Rig entfernt. ``make_test_splat.py --person N`` legt
diese Wolken in den Splat (alle Augenblicke zugleich, wie ein Training sie hinterlässt);
``--masken <ordner>`` schreibt dazu je Bild eine Maske, die **nur die Person dieses
Augenblicks** ausschneidet — wie eine Personenmaske am echten Foto: Schwarz (0) = Person,
Weiss (255) = behalten, PNG in Graustufen, Name = Bildname + ``.png``, dazu eine
``maske.json`` (Auskunft der HomeStation, 13.10.2026). ``--ansichtsordner`` benennt die Bilder
wie dort, ``front/0000.jpg`` statt ``bild_0000_k1.png``.

Aufruf:
    python3 tools/make_test_colmap.py <ordner> [--augenblicke 80] [--text] [--versatz x,y,z]
        [--form platz|strasse] [--person 12] [--masken <ordner>] [--ansichtsordner]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import struct
import sys
import zlib
from pathlib import Path

#: Wie in ``make_test_splat.py``: Wandhöhe und Quaderkante in Metern.
WAND_HOEHE = 8.0
QUADER_KANTE = 3.0

#: COLMAP-Modellnummer von PINHOLE und Sensortyp «Kamera».
PINHOLE = 1
SENSOR_KAMERA = 0

#: Die vier Kameras des Rigs, als Ansichtsordner benannt (``--ansichtsordner``).
ANSICHTEN = {1: "front", 2: "right", 3: "back", 4: "left"}

#: Die Person (Modulkopf): Abstand ihrer Mitte vom Rig (Meter), Grösse, Streuung der
#: Gaussians (σ, Meter). Der Goldene Winkel verteilt ihre Richtung über die Augenblicke, ohne
#: dass sich ein Muster wiederholt.
PERSON_ABSTAND = (0.7, 1.0)
PERSON_GROESSE = 1.75
PERSON_SIGMA = 0.08
PERSON_ARM_ANTEIL = 0.3
GOLDENER_WINKEL = 137.50776405003785

#: Um so viel wird ein Gaussian der Person in der Maske grösser gezeichnet, in σ — eine
#: Personenmaske schneidet grosszügig aus.
MASKE_SIGMA = 2.5


def _mal(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mal_v(a, v):
    return [sum(a[i][k] * v[k] for k in range(3)) for i in range(3)]


def quaternion_aus_matrix(r) -> tuple[float, float, float, float]:
    """3×3-Drehung → Quaternion ``(w, x, y, z)`` mit ``w ≥ 0`` (Shepperd)."""
    spur = r[0][0] + r[1][1] + r[2][2]
    if spur > 0:
        s = math.sqrt(spur + 1.0) * 2
        q = (0.25 * s, (r[2][1] - r[1][2]) / s, (r[0][2] - r[2][0]) / s, (r[1][0] - r[0][1]) / s)
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        s = math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = ((r[2][1] - r[1][2]) / s, 0.25 * s, (r[0][1] + r[1][0]) / s, (r[0][2] + r[2][0]) / s)
    elif r[1][1] > r[2][2]:
        s = math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = ((r[0][2] - r[2][0]) / s, (r[0][1] + r[1][0]) / s, 0.25 * s, (r[1][2] + r[2][1]) / s)
    else:
        s = math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = ((r[1][0] - r[0][1]) / s, (r[0][2] + r[2][0]) / s, (r[1][2] + r[2][1]) / s, 0.25 * s)
    return q if q[0] >= 0 else tuple(-k for k in q)


def _blick(auge, vorn, oben=(0.0, 1.0, 0.0)):
    """Welt → Kamera (OpenCV: x rechts, y unten, z Blick) als ``(R, t)``."""
    def einheit(v):
        n = math.sqrt(sum(k * k for k in v))
        return [k / n for k in v]

    def kreuz(a, b):
        return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

    z = einheit(vorn)
    x = einheit(kreuz(z, oben))
    y = kreuz(z, x)
    r = [x, y, z]
    return r, [-k for k in _mal_v(r, auge)]


def _dreh_y(grad: float):
    """Drehung um die Kamera-y-Achse — vom Rig zur seitlichen Kamera."""
    a = math.radians(grad)
    return [[math.cos(a), 0.0, -math.sin(a)], [0.0, 1.0, 0.0], [math.sin(a), 0.0, math.cos(a)]]


def rig_weg(augenblicke: int, *, form: str = "platz", radius: float = 7.0,
            augenhoehe: float = 1.6, groesse: float = 30.0, versatz=(0.0, 0.0, 0.0)):
    """Der Weg des Rigs: je Augenblick ``(auge, vorn)`` in der Welt (nach dem Versatz).

    Eigene Funktion seit 13.10.2026, damit ``make_test_splat.py --person`` die Person an
    dieselben Stellen legt, an denen die Aufnahme steht.
    """
    v = [float(k) for k in versatz]
    laenge = 0.8 * 2.5 * float(groesse)                  # 80 % der Strasse
    weg = []
    for a in range(augenblicke):
        if form == "strasse":
            z = -laenge / 2 + laenge * a / max(1, augenblicke - 1)
            weg.append(([v[0], augenhoehe + v[1], z + v[2]], (0.0, 0.0, 1.0)))
        else:
            w = 2.0 * math.pi * a / augenblicke
            weg.append(([radius * math.cos(w) + v[0], augenhoehe + v[1],
                         radius * math.sin(w) + v[2]], (-math.sin(w), 0.0, math.cos(w))))
    return weg


def person_wolke(a: int, auge, vorn, n: int, *, augenhoehe: float = 1.6,
                 startwert: int = 11) -> list[tuple[float, float, float, float]]:
    """Die Person im Augenblick ``a``: ``n`` Gaussians ``(x, y, z, σ)`` in der Welt.

    Körper (ein stehender Zylinder vom Boden bis :data:`PERSON_GROESSE`) und Arm (von der
    Schulter bis kurz vor das Rig — wer filmt, hält die Kamera). Die Richtung zum Rig
    wandert je Augenblick um den Goldenen Winkel, der Abstand zwischen den Grenzen von
    :data:`PERSON_ABSTAND`: Die Person steht jedes Mal woanders, wie die Wolke im echten
    Splat.
    """
    zufall = random.Random(startwert * 100003 + a)
    phi = math.radians(GOLDENER_WINKEL * a)
    lo, hi = PERSON_ABSTAND
    d = lo + (hi - lo) * ((a * 0.6180339887) % 1.0)
    vx, vz = vorn[0], vorn[2]
    n_v = math.hypot(vx, vz) or 1.0
    vx, vz = vx / n_v, vz / n_v
    # Richtung in der Waagrechten: vorn um phi gedreht.
    rx = vx * math.cos(phi) - vz * math.sin(phi)
    rz = vx * math.sin(phi) + vz * math.cos(phi)
    boden = auge[1] - augenhoehe
    mx, mz = auge[0] + d * rx, auge[2] + d * rz
    aus = []
    n_arm = int(round(n * PERSON_ARM_ANTEIL))
    for _ in range(n - n_arm):
        w, r = zufall.uniform(0, 2 * math.pi), 0.18 * math.sqrt(zufall.random())
        aus.append((mx + r * math.cos(w), boden + zufall.uniform(0.1, PERSON_GROESSE - 0.1),
                    mz + r * math.sin(w), PERSON_SIGMA))
    schulter = (mx, boden + 0.8 * PERSON_GROESSE, mz)
    for k in range(n_arm):
        t = (k + 0.5) / max(1, n_arm) * 0.85             # bis kurz vor das Rig
        aus.append(tuple(schulter[i] + t * (auge[i] - schulter[i]) for i in range(3))
                   + (0.6 * PERSON_SIGMA,))
    return aus


def schreibe_png_grau(pfad: Path, breite: int, hoehe: int, zeilen: bytearray) -> None:
    """Ein 8-Bit-Graustufen-PNG, nur mit der Standardbibliothek (zlib, struct)."""
    def stueck(art: bytes, daten: bytes) -> bytes:
        return (struct.pack(">I", len(daten)) + art + daten
                + struct.pack(">I", zlib.crc32(art + daten) & 0xFFFFFFFF))

    roh = b"".join(b"\x00" + bytes(zeilen[y * breite:(y + 1) * breite]) for y in range(hoehe))
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + stueck(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 0, 0, 0, 0))
                     + stueck(b"IDAT", zlib.compress(roh, 6)) + stueck(b"IEND", b""))


def _maske(r, t, f, breite: int, hoehe: int, wolke) -> tuple[bytearray, int]:
    """Die Maske eines Bildes: Weiss, die Person (Scheiben um ihre Gaussians) schwarz."""
    pixel = bytearray(b"\xff" * (breite * hoehe))
    for x, y, z, sigma in wolke:
        p = _mal_v(r, [x, y, z])
        p = [p[i] + t[i] for i in range(3)]
        if p[2] <= 0.05:
            continue
        u, v = f * p[0] / p[2] + breite / 2.0, f * p[1] / p[2] + hoehe / 2.0
        rad = f * MASKE_SIGMA * sigma / p[2]
        for zeile in range(max(0, int(v - rad)), min(hoehe, int(v + rad) + 1)):
            dy = zeile + 0.5 - v
            halb = rad * rad - dy * dy
            if halb <= 0:
                continue
            w = math.sqrt(halb)
            x0, x1 = max(0, int(u - w)), min(breite, int(u + w) + 1)
            if x1 > x0:
                pixel[zeile * breite + x0:zeile * breite + x1] = bytes(x1 - x0)
    return pixel, pixel.count(0)


def _flaechenpunkte(zufall: random.Random, n: int, groesse: float, form: str = "platz"):
    """Punkte auf Boden, Wand und Quaderdach — dieselben Flächen wie ``make_test_splat``."""
    L = float(groesse)
    aus = []
    if form == "strasse":
        b, s = 0.4 * L, 2.5 * L
        for i in range(n):
            teil = i % 10
            if teil < 6:                                    # Boden
                aus.append((zufall.uniform(-b / 2, b / 2), zufall.gauss(0.0, 0.01),
                            zufall.uniform(-s / 2, s / 2)))
            else:                                           # Wände
                aus.append(((b / 2 if teil % 2 else -b / 2) + zufall.gauss(0.0, 0.01),
                            zufall.uniform(0.0, WAND_HOEHE), zufall.uniform(-s / 2, s / 2)))
        return aus
    for i in range(n):
        teil = i % 10
        rausch = lambda: zufall.gauss(0.0, 0.01)          # noqa: E731
        if teil < 6:                                        # Boden
            aus.append((zufall.uniform(-L / 2, L / 2), rausch(), zufall.uniform(-L / 2, L / 2)))
        elif teil < 9:                                      # Wand
            aus.append((zufall.uniform(-0.3 * L, 0.3 * L), zufall.uniform(0.0, WAND_HOEHE),
                        -0.4 * L + rausch()))
        else:                                               # Quaderdach
            h = QUADER_KANTE / 2
            aus.append((0.3 * L + zufall.uniform(-h, h), QUADER_KANTE + rausch(),
                        -0.2 * L + zufall.uniform(-h, h)))
    return aus


def schreibe_aufnahme(ordner, *, augenblicke: int = 80, radius: float = 7.0,
                      augenhoehe: float = 1.6, versatz=(0.0, 0.0, 0.0), groesse: float = 30.0,
                      punkte: int = 3000, startwert: int = 7, text: bool = False,
                      mit_frames: bool = True, breite: int = 1086, hoehe: int = 1086,
                      sichtfeld_grad: float = 90.0, form: str = "platz", person: int = 0,
                      masken=None, ansichtsordner: bool = False) -> dict:
    """Die Aufnahme schreiben und sagen, was darin steht.

    ``person`` und ``masken`` (13.10.2026): Mit ``masken`` wird je Bild eine Maske geschrieben,
    die die Person dieses Augenblicks (:func:`person_wolke`, ``person`` Gaussians) ausschneidet.

    Returns:
        ``{ordner, bilder, augenblicke, kameras, zentren, punkte, masken}`` — ``zentren`` sind
        die Kamerazentren in der Welt (nach dem Versatz), ``masken`` die Zahl der Masken und
        der Anteil ausgeschnittener Bildpunkte.
    """
    o = Path(ordner)
    o.mkdir(parents=True, exist_ok=True)
    zufall = random.Random(startwert)
    v = [float(k) for k in versatz]
    f = (breite / 2.0) / math.tan(math.radians(sichtfeld_grad) / 2.0)
    kameras = {k: (PINHOLE, breite, hoehe, (f, f, breite / 2.0, hoehe / 2.0)) for k in (1, 2, 3, 4)}
    sensor = {k: _dreh_y(90.0 * (k - 1)) for k in kameras}  # vorn, rechts, hinten, links
    rahmen, bilder, zentren = [], [], []
    nr = 1
    n_masken = schwarz = 0
    weg = rig_weg(augenblicke, form=form, radius=radius, augenhoehe=augenhoehe,
                  groesse=groesse, versatz=v)
    for a, (auge, vorn) in enumerate(weg):
        r_rig, t_rig = _blick(auge, vorn)
        wolke = (person_wolke(a, auge, vorn, person, augenhoehe=augenhoehe)
                 if person and masken is not None else [])
        daten = []
        for k in kameras:
            r = _mal(sensor[k], r_rig)
            t = _mal_v(sensor[k], t_rig)
            name = (f"{ANSICHTEN[k]}/{a:04d}.jpg" if ansichtsordner
                    else f"bild_{a:04d}_k{k}.png")
            bilder.append((nr, quaternion_aus_matrix(r), t, k, name))
            if masken is not None:
                pixel, n_schwarz = _maske(r, t, f, breite, hoehe, wolke)
                schreibe_png_grau(Path(masken) / (name + ".png"), breite, hoehe, pixel)
                n_masken += 1
                schwarz += n_schwarz
            daten.append((k, nr))
            nr += 1
        rahmen.append((a + 1, quaternion_aus_matrix(r_rig), t_rig, daten))
        zentren.append(tuple(auge))
    pkt = [(p[0] + v[0], p[1] + v[1], p[2] + v[2])
           for p in _flaechenpunkte(zufall, punkte, groesse, form)]
    # Spuren, die zueinander passen (COLMAP prüft beim Lesen beide Richtungen): Punkt i wird
    # in zwei aufeinanderfolgenden Bildern beobachtet. Wo — gleichgültig für die Blickwinkel.
    beob: dict[int, list[int]] = {b[0]: [] for b in bilder}
    spuren = []
    for i in range(1, len(pkt) + 1):
        spur = []
        for bild in ((i - 1) % len(bilder) + 1, i % len(bilder) + 1):
            spur.append((bild, len(beob[bild])))
            beob[bild].append(i)
        spuren.append(spur)

    if text:
        _schreibe_text(o, kameras, sensor, bilder, rahmen, pkt, spuren, beob, mit_frames)
    else:
        _schreibe_binaer(o, kameras, sensor, bilder, rahmen, pkt, spuren, beob, mit_frames)
    if masken is not None:
        (Path(masken) / "maske.json").write_text(json.dumps(
            {"schema": "kosmoprepare.splat-maske/0.2", "verfahren": "person",
             "erzeugt_von": "tools/make_test_colmap.py (synthetisch, Regel 3)",
             "polaritaet": "weiss=behalten", "masken": n_masken}, indent=1), encoding="utf-8")
    return {"ordner": str(o), "bilder": len(bilder), "augenblicke": augenblicke,
            "kameras": len(kameras), "zentren": zentren, "punkte": len(pkt),
            "masken": {"anzahl": n_masken,
                       "ausgeschnitten": round(schwarz / max(1, n_masken * breite * hoehe), 4)}}


def _schreibe_binaer(o: Path, kameras, sensor, bilder, rahmen, pkt, spuren, beob,
                     mit_frames) -> None:
    with open(o / "cameras.bin", "wb") as d:
        d.write(struct.pack("<Q", len(kameras)))
        for k, (modell, b, h, params) in kameras.items():
            d.write(struct.pack("<IiQQ", k, modell, b, h) + struct.pack("<4d", *params))
    with open(o / "images.bin", "wb") as d:
        d.write(struct.pack("<Q", len(bilder)))
        for nr, q, t, k, name in bilder:
            d.write(struct.pack("<I4d3dI", nr, *q, *t, k) + name.encode() + b"\x00")
            # Die 2D-Punkte mit — damit der Leser das Überspringen beweisen muss.
            d.write(struct.pack("<Q", len(beob[nr])) + b"".join(
                struct.pack("<ddQ", 10.0 + j, 20.0 + j, p) for j, p in enumerate(beob[nr])))
    with open(o / "points3D.bin", "wb") as d:
        d.write(struct.pack("<Q", len(pkt)))
        for i, (p, spur) in enumerate(zip(pkt, spuren), start=1):
            d.write(struct.pack("<Q3d3BdQ", i, *p, 128, 128, 128, 0.5, len(spur))
                    + b"".join(struct.pack("<II", bild, j) for bild, j in spur))
    if not mit_frames:
        return
    with open(o / "rigs.bin", "wb") as d:
        d.write(struct.pack("<QIIiI", 1, 1, len(kameras), SENSOR_KAMERA, 1))
        for k in list(kameras)[1:]:
            q = quaternion_aus_matrix(sensor[k])
            d.write(struct.pack("<iIB", SENSOR_KAMERA, k, 1) + struct.pack("<4d3d", *q, 0, 0, 0))
    with open(o / "frames.bin", "wb") as d:
        d.write(struct.pack("<Q", len(rahmen)))
        for nr, q, t, daten in rahmen:
            d.write(struct.pack("<II4d3dI", nr, 1, *q, *t, len(daten)))
            for k, bild in daten:
                d.write(struct.pack("<iIQ", SENSOR_KAMERA, k, bild))


def _schreibe_text(o: Path, kameras, sensor, bilder, rahmen, pkt, spuren, beob,
                   mit_frames) -> None:
    def zahlen(*w):
        return " ".join(repr(float(x)) for x in w)

    (o / "cameras.txt").write_text("# Camera list\n" + "".join(
        f"{k} PINHOLE {b} {h} {zahlen(*params)}\n" for k, (_m, b, h, params) in kameras.items()),
        encoding="utf-8")
    (o / "images.txt").write_text("# Image list\n" + "".join(
        f"{nr} {zahlen(*q, *t)} {k} {name}\n"
        + " ".join(f"{10.0 + j} {20.0 + j} {p}" for j, p in enumerate(beob[nr])) + "\n"
        for nr, q, t, k, name in bilder),
        encoding="utf-8")
    (o / "points3D.txt").write_text("# 3D point list\n" + "".join(
        f"{i} {zahlen(*p)} 128 128 128 0.5 " + " ".join(f"{b} {j}" for b, j in spur) + "\n"
        for i, (p, spur) in enumerate(zip(pkt, spuren), start=1)),
        encoding="utf-8")
    if not mit_frames:
        return
    andere = " ".join(f"CAMERA {k} 1 {zahlen(*quaternion_aus_matrix(sensor[k]), 0, 0, 0)}"
                      for k in list(kameras)[1:])
    (o / "rigs.txt").write_text(f"# Rig list\n1 {len(kameras)} CAMERA 1 {andere}\n",
                                encoding="utf-8")
    (o / "frames.txt").write_text("# Frame list\n" + "".join(
        f"{nr} 1 {zahlen(*q, *t)} {len(daten)} "
        + " ".join(f"CAMERA {k} {bild}" for k, bild in daten) + "\n"
        for nr, q, t, daten in rahmen), encoding="utf-8")


def _drei(text: str) -> tuple[float, float, float]:
    teile = [t.strip() for t in text.split(",")]
    if len(teile) != 3:
        raise argparse.ArgumentTypeError(f"drei Zahlen 'x,y,z' erwartet, war {text!r}")
    return tuple(float(t) for t in teile)  # type: ignore[return-value]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ordner")
    ap.add_argument("--augenblicke", type=int, default=80)
    ap.add_argument("--radius", type=float, default=7.0)
    ap.add_argument("--versatz", type=_drei, default=(0.0, 0.0, 0.0))
    ap.add_argument("--text", action="store_true", help="als Text statt binär")
    ap.add_argument("--form", choices=("platz", "strasse"), default="platz")
    ap.add_argument("--person", type=int, default=12,
                    help="Gaussians der Person je Augenblick (fuer die Masken)")
    ap.add_argument("--masken", default=None,
                    help="Ordner, in den je Bild eine Personenmaske geschrieben wird")
    ap.add_argument("--ansichtsordner", action="store_true",
                    help="Bilder als front/0000.jpg usw. benennen")
    a = ap.parse_args(argv)
    befund = schreibe_aufnahme(a.ordner, augenblicke=a.augenblicke, radius=a.radius,
                               versatz=a.versatz, text=a.text, form=a.form,
                               person=a.person if a.masken else 0, masken=a.masken,
                               ansichtsordner=a.ansichtsordner)
    print(f"{befund['ordner']}  ({befund['bilder']} Bilder aus {befund['kameras']} Kameras, "
          f"{befund['punkte']} Punkte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
