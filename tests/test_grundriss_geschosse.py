"""A0322 «Grundriss ohne Doppelfläche»: ein Netz mit Geschossen, überlappenden Flügeln oder einer Auskragung ergibt
den richtigen Grundriss (die Vereinigung seiner Dachflächen, mit Hof und Winkel).

Herkunft: das dritte Gegenlesen von A0301 (Kopf 9f812589b). ``aiimaging.grundriss.aus_dreiecken`` nahm an, dass sich
die nach oben schauenden Dreiecke eines Netzes nicht überlappen. Mit Geschossen als eigene Körper war die Flächensumme
zu gross, und das Zusammenlegen legte Hof oder Winkel zu (U mit 4 Geschossen 2400 statt 1400 m², L mit 3 Geschossen
1150 statt 700 m², drei Flügel mit Eckenüberlappung 1600 statt 1400 m² aus Stücken, die sich überlappen). Auf einer
Bodenplatte verschmolz dann ein Nachbarhaus im Hof mit dem Bau, ohne Vermerk; die Basis 1781a25a8 trennte.

Die Proben fahren den echten Aufrufweg (glb schreiben, ``lies_glb_umfeld``, ``plane``) und vergleichen mit der Basis.
Die Fläche jedes Grundrisses wird unabhängig vom Produkt nachgerechnet (eigener Schnitt konvexer Vielecke).
"""
from __future__ import annotations

import itertools
import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiimaging import grundriss, umfeld  # noqa: E402
from fluegel_basis import basis_cluster  # noqa: E402
from fluegel_glb import _prisma, schreibe, ueber_den_aufrufweg  # noqa: E402
from fluegel_satz import beurteile, faelle, gemeldet, schlechter, zufallsfall_geschosse  # noqa: E402

GESCHOSSE = [f for f in faelle() if f["herkunft"] == "gegenlesen3"]


def _flaeche(p) -> float:
    return abs(sum(p[k - 1][0] * p[k][1] - p[k][0] * p[k - 1][1] for k in range(len(p)))) / 2.0


def _schnitt(p, q) -> list:
    """Sutherland-Hodgman: ``p`` geschnitten mit dem konvexen ``q`` (beide gegen den Uhrzeigersinn)."""
    aus = list(p)
    for k in range(len(q)):
        a, b = q[k - 1], q[k]
        ein, aus = aus, []
        if not ein:
            break

        def innen(c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) >= -1e-12
        for m in range(len(ein)):
            c, d = ein[m - 1], ein[m]
            if innen(d):
                if not innen(c):
                    aus.append(_kreuzung(c, d, a, b))
                aus.append(d)
            elif innen(c):
                aus.append(_kreuzung(c, d, a, b))
    return aus


def _kreuzung(c, d, a, b):
    x1, y1, x2, y2, x3, y3, x4, y4 = *c, *d, *a, *b
    n = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / n
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _ccw(p):
    s = sum(p[k - 1][0] * p[k][1] - p[k][0] * p[k - 1][1] for k in range(len(p)))
    return list(p) if s >= 0 else list(p)[::-1]


def _ueberlappung(stuecke) -> float:
    return sum(_flaeche(_schnitt(_ccw(p), _ccw(q))) if len(_schnitt(_ccw(p), _ccw(q))) >= 3 else 0.0
               for p, q in itertools.combinations(stuecke, 2))


def _netz(koerper):
    """Dreiecke in der Welt (Z oben) aus ``[(stueck, z0, z1), …]``, alle in EINEM Netz."""
    ecken, dreiecke = [], []
    for st, z0, z1 in koerper:
        e, d = _prisma(st, z0, z1, len(ecken))
        ecken += e
        dreiecke += d
    welt = [(x, -z, y) for x, y, z in ecken]
    return [tuple(welt[i] for i in d) for d in dreiecke]


def _r(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


U = [_r(0, 0, 40, 10), _r(0, 10, 10, 60), _r(30, 10, 40, 60)]
L = [_r(0, 0, 40, 10), _r(0, 10, 10, 40)]
U_UEBERLAPPEND = [_r(0, 0, 40, 10), _r(0, 0, 10, 60), _r(30, 0, 40, 60)]


@pytest.mark.parametrize("name, koerper, soll, frei", [
    ("U mit 4 Geschossen", [(s, 3.0 * k, 3.0 * k + 3.0) for k in range(4) for s in U], 1400.0, (20.0, 35.0)),
    ("L mit 3 Geschossen", [(s, 3.0 * k, 3.0 * k + 3.0) for k in range(3) for s in L], 700.0, (25.0, 25.0)),
    ("drei Flügel mit Eckenüberlappung", [(s, 0.0, 12.0) for s in U_UEBERLAPPEND], 1400.0, (20.0, 35.0)),
    ("drei Flügel, 3 Geschosse", [(s, 4.0 * k, 4.0 * k + 4.0) for k in range(3) for s in U_UEBERLAPPEND], 1400.0,
     (20.0, 35.0)),
    ("Auskragung", [(_r(0, 0, 20, 20), 2.0, 8.0), (_r(10, 10, 30, 30), 8.0, 14.0)], 700.0, (25.0, 5.0)),
    ("Stapel gleicher Geschosse", [(_r(0, 0, 20, 12), 3.0 * k, 3.0 * k + 3.0) for k in range(5)], 240.0, None),
])
def test_die_handfaelle_des_gegenlesens(name, koerper, soll, frei):
    """Die Handfälle mit Zahlen zum Nachrechnen: Fläche der Vereinigung (unter 1 % daneben), keine Stücke, die sich
    überlappen, der Hof oder Winkel bleibt frei. Am Kopf 9f812589b: 2400, 1150, 1600 (überlappend), Hülle 800."""
    stuecke = grundriss.aus_dreiecken(_netz(koerper))
    assert stuecke is not None, name
    assert sum(_flaeche(s) for s in stuecke) == pytest.approx(soll, rel=0.01), name
    assert _ueberlappung(stuecke) < 1e-6 * soll, name
    if frei is not None:
        assert not any(grundriss._im_konvexen(*frei, s) for s in stuecke), name


def test_gedreht_und_fein_vernetzt_bleibt_die_vereinigung():
    """Dieselben Handfälle gedreht und mit feinen Dächern (jedes Rechteck in viele Dreiecke geteilt, die Geschosse mit
    verschiedener Teilung): Fläche unter 1 % daneben, keine Überlappung, der Hof frei."""
    grad = 27.0
    c, s = math.cos(math.radians(grad)), math.sin(math.radians(grad))

    def dreh(p):
        return [(x * c - y * s, x * s + y * c) for x, y in p]
    for form, n, soll, frei in ((U, 4, 1400.0, (20.0, 35.0)), (L, 3, 700.0, (25.0, 25.0))):
        dreiecke = []
        for k in range(n):
            teilung = 2 + k
            for st in form:
                (x0, y0), (x1, y1) = st[0], st[2]
                for a in range(teilung):
                    for b in range(teilung):
                        q = _r(x0 + (x1 - x0) * a / teilung, y0 + (y1 - y0) * b / teilung,
                               x0 + (x1 - x0) * (a + 1) / teilung, y0 + (y1 - y0) * (b + 1) / teilung)
                        dreiecke += _netz([(dreh(q), 3.0 * k, 3.0 * k + 3.0)])
        stuecke = grundriss.aus_dreiecken(dreiecke)
        assert stuecke is not None
        assert sum(_flaeche(t) for t in stuecke) == pytest.approx(soll, rel=0.01)
        assert _ueberlappung(stuecke) < 1e-6 * soll
        fx, fy = frei
        assert not any(grundriss._im_konvexen(fx * c - fy * s, fx * s + fy * c, t) for t in stuecke)


def test_ohne_ueberlappung_bleibt_der_grundriss_wie_bisher():
    """Ein Netz ohne Dächer übereinander nimmt den Weg vor A0322: ein Quader ist seine Hülle, ein U als ein Netz die
    Dachdreiecke zusammengelegt (dieselben Stücke wie ``_zusammenlegen`` der Dachdreiecke allein)."""
    quader = grundriss.aus_dreiecken(_netz([(_r(0, 0, 10, 4), 0.0, 5.0)]))
    assert len(quader) == 1 and _flaeche(quader[0]) == pytest.approx(40.0)
    dreiecke = _netz([(s, 0.0, 9.0) for s in U])
    dach = [[(e[0], e[1]) for e in d] for d in dreiecke]
    dach = [p for p in dach if grundriss._umlauf(p) / 2.0 > grundriss.FLAECHE_MIN_M2]
    assert grundriss.aus_dreiecken(dreiecke) == grundriss._zusammenlegen(dach)


def test_kreisring_mit_geschossen_raet_nicht():
    """Ein Kreisring aus 64 Segmenten mit 3 Geschossen: die Vereinigung hat einen Hof; entweder kommt sie (Fläche
    stimmt, Hof frei) oder ``None`` (zu viele Stücke). Nie die volle Scheibe (am Kopf 9f812589b: die Scheibe)."""
    koerper = []
    for k in range(64):
        a, b = 2 * math.pi * k / 64, 2 * math.pi * (k + 1) / 64
        st = [(10 * math.cos(a), 10 * math.sin(a)), (20 * math.cos(a), 20 * math.sin(a)),
              (20 * math.cos(b), 20 * math.sin(b)), (10 * math.cos(b), 10 * math.sin(b))]
        koerper += [(st, 3.0 * g, 3.0 * g + 3.0) for g in range(3)]
    stuecke = grundriss.aus_dreiecken(_netz(koerper))
    if stuecke is not None:
        assert not any(grundriss._im_konvexen(0.0, 0.0, t) for t in stuecke)
        assert sum(_flaeche(t) for t in stuecke) == pytest.approx(64 * 0.5 * math.sin(2 * math.pi / 64) * 300, rel=0.01)


def test_zu_viele_randkanten_gibt_keinen_grundriss():
    """Überlappende Dächer mit mehr Randkanten, als sicher prüfbar sind, oder mit zu vielen Kantenschnitten: ``None``
    (die Box gilt), nie geraten, und schnell."""
    import time
    rnd = random.Random(322)

    def wirr(anzahl, groesse):
        koerper = []
        for _ in range(anzahl):
            x, y = rnd.uniform(0, 50), rnd.uniform(0, 50)
            koerper.append(([(x, y), (x + groesse, y + groesse / 6), (x + groesse / 3, y + groesse * 2 / 3)], 0.0, 3.0))
        return _netz(koerper)
    viele = wirr(grundriss.KANTEN_HOECHSTENS // 3 + 1, 3.0)                  # mehr Randkanten als erlaubt
    wirre = wirr(300, 40.0)                                                    # 900 Kanten, sehr viele Schnitte
    for dreiecke in (viele, wirre):
        start = time.perf_counter()
        assert grundriss.aus_dreiecken(dreiecke) is None
        assert time.perf_counter() - start < 5.0


def _faelle_ueber_glb(tmp_path, faelle_liste):
    """Jeden Fall als glb schreiben und durch den Aufrufweg fahren; zurück je Fall (Urteil, Urteil der Basis,
    Ergebnis). Die Basis sieht dieselben Boxen aus derselben Datei."""
    aus = []
    for nummer, fall in enumerate(faelle_liste):
        pfad = tmp_path / f"geschosse{nummer}.glb"
        schreibe(pfad, fall["glb"])
        ergebnis = ueber_den_aufrufweg(pfad)
        bauten = umfeld.grundriss_cluster(ergebnis["boxen"], grundrisse=ergebnis["grundrisse"])
        assert sorted(c["teile"] for c in bauten) == sorted(ergebnis["gruppen"]), fall["name"]
        aus.append((beurteile(fall, bauten), beurteile(fall, basis_cluster(ergebnis["boxen"])), ergebnis, bauten))
    return aus


def test_die_rueckschrittfaelle_ueber_den_aufrufweg(tmp_path):
    """Die Handfälle des dritten Gegenlesens als glb: jeder richtig, ohne Vermerk, keiner schlechter als die Basis;
    jeder Grundriss aus der glb mit der Fläche der wahren Vereinigung (unter 1 %) und ohne Überlappung. Am Kopf
    9f812589b verschmolzen U mit 4 Geschossen, L mit 3 Geschossen und die Auskragung auf der Bodenplatte."""
    assert len(GESCHOSSE) == 20
    for fall, (urteil, vorher, ergebnis, bauten) in zip(GESCHOSSE, _faelle_ueber_glb(tmp_path, GESCHOSSE)):
        assert not schlechter(urteil, vorher), (fall["name"], urteil["grund"])
        assert urteil["richtig"] and not gemeldet(bauten), (fall["name"], urteil["grund"])
        for wahr, g in zip(fall["grundrisse"], ergebnis["grundrisse"]):
            assert g is not None, fall["name"]
            assert sum(_flaeche(s) for s in g) == pytest.approx(sum(_flaeche(s) for s in wahr), rel=0.01), fall["name"]
            assert _ueberlappung(g) < 1e-6 * sum(_flaeche(s) for s in g), fall["name"]


def test_die_basis_trennt_die_handfaelle_auf_der_bodenplatte(tmp_path):
    """Gegenprobe zum Satz: die Handfälle mit Nachbar auf der Bodenplatte trennt schon die Basis. Ein Fehler hier
    wäre ein Rückschritt; ohne diese Gegenprobe könnte die vorige Probe nichts widerlegen."""
    auf_platte = [f for f in GESCHOSSE if f["name"].endswith("-gelaende-glb") and f["gegenfall"]]
    assert len(auf_platte) == 9
    assert all(vorher["richtig"] for _, vorher, _, _ in _faelle_ueber_glb(tmp_path, auf_platte))


def test_die_gezielte_reihe_mit_geschossen_ueber_den_aufrufweg(tmp_path):
    """300 Szenen der gezielten Reihe (ein Netz L, U, T, Z mit 2 bis 4 Geschossen, ein Viertel mit Eckenüberlappung,
    ein Achtel Auskragung, Nachbar im Hof oder Winkel, halb gedreht und davon ein Teil verschachtelt, drei Viertel
    auf der Bodenplatte), über ``lies_glb_umfeld`` und ``plane``: keine schlechter als die Basis, jede richtig, ohne
    Vermerk, jeder Grundriss ohne Überlappung. Gemessen sind 2000 und mehr im Protokoll (§318)."""
    rnd = random.Random(32200)
    reihe = [zufallsfall_geschosse(rnd) for _ in range(300)]
    assert sum(any(len(t) > 6 and t[6] and t[6] > 1 for t in f["glb"]) for f in reihe) > 150
    assert sum(any(len(t) > 7 and t[7] for t in f["glb"]) for f in reihe) > 15
    assert sum(any(len(t) > 8 and t[8] for t in f["glb"]) for f in reihe) > 15
    for nummer, (fall, (urteil, vorher, ergebnis, bauten)) in enumerate(zip(reihe, _faelle_ueber_glb(tmp_path, reihe))):
        assert not schlechter(urteil, vorher), (nummer, fall["name"], urteil["grund"])
        assert urteil["richtig"] and not gemeldet(bauten), (nummer, fall["name"], urteil["grund"])
        for g in ergebnis["grundrisse"]:
            assert g is not None and _ueberlappung(g) < 1e-6 * sum(_flaeche(s) for s in g), (nummer, fall["name"])


def test_verschachtelte_drehung_ergibt_dieselbe_welt(tmp_path):
    """Der Schreiber: dieselbe Drehung ganz im Knoten oder verschachtelt (Teil im Elternknoten) ergibt dieselben Boxen
    und Grundrisse über ``lies_glb_umfeld``."""
    a, b = tmp_path / "flach.glb", tmp_path / "verschachtelt.glb"
    schreibe(a, [("teil_000", U, 0.0, 12.0, 35.0, (20.0, 30.0), 3)])
    schreibe(b, [("teil_000", U, 0.0, 12.0, 35.0, (20.0, 30.0), 3, None, -20.0)])
    ga, gb = umfeld.lies_glb_umfeld(a), umfeld.lies_glb_umfeld(b)
    assert [v for p in ga["bauwerk_boxen"][0] for v in p] == pytest.approx([v for p in gb["bauwerk_boxen"][0] for v in p],
                                                                           abs=1e-3)
    fa = sum(_flaeche(s) for s in ga["bauwerk_grundrisse"][0])
    assert fa == pytest.approx(sum(_flaeche(s) for s in gb["bauwerk_grundrisse"][0]), rel=1e-6)
    assert fa == pytest.approx(1400.0, rel=0.01)


def _lamellen(anzahl, geschosse=2, teile=5, versatz=0.19):
    """Der Lamellenfall des Gegenlesens zu A0322: ``anzahl`` parallele Lamellen 100 x 1 m im Abstand 1 m, jeder
    Lamellenrand in ``teile`` Stücke geteilt (die Teilungspunkte je Lamelle um ``versatz`` m verschoben), in
    ``geschosse`` gleichen Geschossen, alles in EINEM Netz (Dach und Boden je als Streifen aus Dreiecken)."""
    dreiecke = []
    for g in range(geschosse):
        z0, z1 = 3.0 * g, 3.0 * g + 3.0
        for j in range(anzahl):
            y0, y1 = 2.0 * j, 2.0 * j + 1.0
            xs = [0.0] + [100.0 * k / teile + versatz * j for k in range(1, teile)] + [100.0]
            for a, b in zip(xs, xs[1:]):
                dreiecke += [((a, y0, z1), (b, y0, z1), (b, y1, z1)), ((a, y0, z1), (b, y1, z1), (a, y1, z1)),
                             ((a, y0, z0), (b, y1, z0), (b, y0, z0)), ((a, y0, z0), (a, y1, z0), (b, y1, z0))]
    return dreiecke


def _gueltig(stuecke, soll):
    """``None`` (nicht geraten) oder die Vereinigung: Fläche unter 1 % daneben, keine Stücke, die sich überlappen."""
    if stuecke is None:
        return True
    return (sum(_flaeche(s) for s in stuecke) == pytest.approx(soll, rel=0.01)
            and _ueberlappung(stuecke) < 1e-6 * soll)


@pytest.mark.parametrize("anzahl", [40, 60, 100])
def test_lamellen_bleiben_unter_der_rechengrenze(anzahl):
    """A0322 Runde 2, Mangel 1 des Gegenlesens: das Zusammenlegen der Trapeze lief ausserhalb der Rechengrenze und
    wuchs mit dem Quadrat ihrer Zahl (am Kopf 141898de1: J = 40 7,5 s, J = 60 41 s, J = 100 326 s für ein Teil). Jetzt
    unter 1 s, und das Ergebnis ist nie geraten (hier über 64 Stücke: ``None``, die Box gilt)."""
    import time
    dreiecke = _lamellen(anzahl)
    start = time.perf_counter()
    stuecke = grundriss.aus_dreiecken(dreiecke)
    dauer = time.perf_counter() - start
    assert dauer < 1.0, dauer
    assert _gueltig(stuecke, 100.0 * anzahl)


def test_rauschen_in_den_geschossen_bleibt_schnell():
    """Das U mit 4 Geschossen, jede Ecke jedes Dreiecks für sich um 0,1 mm verschoben, nicht geteilt (am Kopf
    141898de1: 2,9 bis 5,1 s, ``None``): jetzt unter 0,2 s (bester von drei Läufen), und das Ergebnis ist ``None``
    oder die Vereinigung."""
    import time
    for saat in range(5):
        rnd = random.Random(3220 + saat)
        dreiecke = [tuple((x + rnd.uniform(-1e-4, 1e-4), y + rnd.uniform(-1e-4, 1e-4), z) for x, y, z in d)
                    for d in _netz([(s, 3.0 * k, 3.0 * k + 3.0) for k in range(4) for s in U])]
        zeiten = []
        for _ in range(3):
            start = time.perf_counter()
            stuecke = grundriss.aus_dreiecken(dreiecke)
            zeiten.append(time.perf_counter() - start)
        assert min(zeiten) < 0.2, (saat, zeiten)
        assert _gueltig(stuecke, 1400.0), saat
