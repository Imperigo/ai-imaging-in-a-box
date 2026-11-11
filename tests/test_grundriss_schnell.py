"""A0327 «Grundriss schnell und ohne Wegwurf»: die Gruppierung bleibt im dichtesten gedrehten Fall unter einer
Sekunde, und ein brauchbarer Grundriss wird nicht vorzeitig weggeworfen.

Herkunft: der Entscheid der Steuerung zu A0301 (dichtester gedrehter Fall mit 5000 Teilen 1,1 bis 1,39 s, die
Beschleunigung als eigener Auftrag) und Befund B1 des zweiten Gegenlesens von A0322: Der frühe Abbruch in
``_streifen_zusammenlegen`` (über 64 Stücke nach dem Zusammenlegen benachbarter Streifen: ``None``) warf Grundrisse
weg, die das paarweise Zusammenlegen danach auf 64 oder weniger Stücke gebracht hätte.

Die Szenen sind dieselben wie in den Meldungen: 5000 Teile 5 bis 40 m auf einer Geländeplatte, hier lauter gedrehte
Rechtecke auf 700 m Seite (im Mittel 33 überlappende Hüllpaare je Teil).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiimaging import grundriss, umfeld  # noqa: E402
from test_grundriss_geschosse import _flaeche, _lamellen, _ueberlappung  # noqa: E402


def _szene(seite, art, saat=5000):
    """5000 Teile 5 bis 40 m, Höhe 2 bis 20 m, auf einer Platte; ``art`` ``boxen`` (ohne Grundrisse),
    ``achsparallel`` (Grundriss = Box) oder ``gedreht`` (gedrehtes Rechteck, die Box ist seine Hülle)."""
    rnd = random.Random(saat)
    boxen, grund = [], []
    for _ in range(5000):
        x, y = rnd.uniform(0, seite), rnd.uniform(0, seite)
        w, h = rnd.uniform(5, 40), rnd.uniform(5, 40)
        z0, z1 = 2.0, 2.0 + rnd.uniform(2, 20)
        if art == "gedreht":
            a = rnd.uniform(0, math.pi)
            c, s = math.cos(a), math.sin(a)
            p = [(x + c * u - s * v, y + s * u + c * v) for u, v in ((-w / 2, -h / 2), (w / 2, -h / 2),
                                                                      (w / 2, h / 2), (-w / 2, h / 2))]
        else:
            p = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        boxen.append(((min(xs), min(ys), z0), (max(xs), max(ys), z1)))
        grund.append(p)
    boxen.append(((-50.0, -50.0, 0.0), (seite + 100.0, seite + 100.0, 2.0)))
    grund.append(None)
    return boxen, (None if art == "boxen" else grund)


def _fingerabdruck(ergebnis) -> str:
    return hashlib.sha1(json.dumps(ergebnis, sort_keys=True).encode()).hexdigest()[:16]


def test_der_dichteste_gedrehte_fall_bleibt_unter_einer_sekunde():
    """5000 lauter gedrehte Teile auf 700 m Seite: Median aus 5 unter 1 s (am Kopf f220e2e38 1,03 bis 1,39 s)."""
    boxen, grund = _szene(700, "gedreht")
    zeiten = []
    for _ in range(5):
        start = time.perf_counter()
        umfeld.grundriss_cluster(boxen, grundrisse=grund)
        zeiten.append(time.perf_counter() - start)
    assert statistics.median(zeiten) < 1.0, zeiten


#: Die Gruppierung dieser Szenen am Kopf f220e2e38 (vor der Beschleunigung), als Fingerabdruck des ganzen Ergebnisses
#: (Boxen, Höhen, Flächen, Art, Teile, Vermerk, andere Lesart). Die Beschleunigung darf kein Ergebnis verschieben.
GRUPPEN_VORHER = {
    "boxen/2000": "da4add72c0bfd2d2",
    "achsparallel/1000": "e09c3ab48ffae574",
    "gedreht/3000": "47e79720e7b8f23c",
    "gedreht/1000": "c17390050cd16877",
    "gedreht/700": "2451fa61d409b589",
}


@pytest.mark.parametrize("art, seite", [("boxen", 2000), ("achsparallel", 1000), ("gedreht", 3000),
                                        ("gedreht", 1000), ("gedreht", 700)])
def test_die_beschleunigung_verschiebt_keine_gruppe(art, seite):
    """Dieselben Szenen gruppieren wörtlich wie vor der Beschleunigung (Fingerabdruck am Kopf f220e2e38)."""
    boxen, grund = _szene(seite, art)
    assert _fingerabdruck(umfeld.grundriss_cluster(boxen, grundrisse=grund)) == GRUPPEN_VORHER[f"{art}/{seite}"]


def _dreh45(dreiecke, mx, my):
    c = s = math.sqrt(0.5)
    return [tuple((mx + c * (x - mx) - s * (y - my), my + s * (x - mx) + c * (y - my), z) for x, y, z in d)
            for d in dreiecke]


@pytest.mark.parametrize("mitte", [(0.0, 0.0), (50.0, 20.5)], ids=["um-den-ursprung", "um-die-mitte"])
def test_der_fruehe_abbruch_wirft_keinen_grundriss_weg(mitte):
    """Befund B1 aus dem Gegenlesen von A0322 Runde 2: 21 Lamellen 100 x 1 m in 2 Geschossen, um 45 Grad gedreht.
    Nach dem Zusammenlegen benachbarter Streifen sind es über 64 Stücke, das paarweise Zusammenlegen bringt sie auf
    64 bzw. 63. Am Kopf f220e2e38 brach die Rechnung vorher ab: ``None``. Jetzt der Grundriss, genau die Lamellen."""
    dreiecke = _dreh45(_lamellen(21), *mitte)
    stuecke = grundriss.aus_dreiecken(dreiecke)
    assert stuecke is not None
    assert len(stuecke) <= grundriss.STUECKE_HOECHSTENS
    assert sum(_flaeche(s) for s in stuecke) == pytest.approx(2100.0, rel=1e-6)
    assert _ueberlappung(stuecke) < 1e-6 * 2100.0
    rnd = random.Random(327)                               # Stichpunkte: in einem Stück genau dann, wenn in einer Lamelle
    c = math.sqrt(0.5)
    for _ in range(4000):
        u, v = rnd.uniform(-1.0, 101.0), rnd.uniform(-1.0, 42.0)
        if min(abs(u), abs(u - 100.0)) < 1e-3 or abs(v - round(v)) < 1e-3:
            continue                                       # auf einem Rand: nicht entscheidbar
        x, y = mitte[0] + c * (u - mitte[0]) - c * (v - mitte[1]), mitte[1] + c * (u - mitte[0]) + c * (v - mitte[1])
        soll = 0.0 < u < 100.0 and 0.0 < v < 42.0 and int(math.floor(v)) % 2 == 0
        ist = any(_im(x, y, s) for s in stuecke)
        assert ist == soll, (u, v)


def _im(x, y, p) -> bool:
    return all((p[k][0] - p[k - 1][0]) * (y - p[k - 1][1]) - (p[k][1] - p[k - 1][1]) * (x - p[k - 1][0]) >= -1e-9
               for k in range(len(p)))
