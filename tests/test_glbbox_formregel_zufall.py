"""A0289 «Gelände an der Form», Runde 2: Zufallsvergleich an 5000 Modellen.

Ein eigener Satz, an dem die Lösung alles besteht, belegt wenig, wenn ihre Schwellen in einer Lücke
des Satzes liegen. Darum würfelt diese Probe Modelle aus den Bausteinen, an denen die Formregel in
Runde 1 gescheitert ist (Tiefgarage, Sockel, Halle mit Kamin, Bodenplatte, Dächer, Vordächer,
Rampen), mit und ohne Gelände, mit zufälligen Namen (auch keinen, leere, doppelte), verschoben,
gedreht und skaliert. An JEDEM Modell gilt:

* die Hülle ist endlich und nicht leer;
* kein Körper, der als Bauwerk gekennzeichnet ist, wird als Gelände abgetrennt;
* kein solcher Körper liegt ausserhalb der Hülle.

Die Modelle sind synthetisch und aus dem Startwert wieder erzeugbar (kein echtes Projekt).
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from aiimaging import glbbox, maske

WURZEL = Path(__file__).resolve().parents[1]
STARTWERT = 20261110
ANZAHL = 5000

NAMEN = (None, "", "Mesh", "Mesh", "Object", "Objekt_7", "Koerper", "Platte", "Decke", "IfcSlab_Platte_1",
         "IfcSlab_Platte_1", "Bauteil", "Flaeche", "Haus", "Wand", "Dach", "IfcBuildingElementProxy_0a1b")


def _werkzeug():
    spez = importlib.util.spec_from_file_location("glbbox_proben", WURZEL / "tools" / "glbbox_proben.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _viertelschritt(r, lo, hi):
    """Eine Zahl auf Viertel genau: in 32 Bit exakt, damit die Boxen der Körper sauber aneinanderliegen."""
    return round(r.uniform(lo, hi) * 4) / 4


def wuerfle(w, r: random.Random):
    """Ein Zufallsmodell: ``(_Bau, wurzelzusatz)``. ``bau.gelaende`` trägt die Wahrheit."""
    b = w._Bau()
    name = lambda: r.choice(NAMEN)      # noqa: E731
    x0 = 0.0
    breite_gesamt = 0.0
    hoehe0 = _viertelschritt(r, -2, 2)
    for _ in range(r.randint(1, 3)):
        art = r.choice(("haus", "tiefgarage", "sockel", "halle", "bodenplatte", "satteldachhalle",
                        "halle_mit_dach", "vordach", "rampe", "turm"))
        bx, bz = _viertelschritt(r, 8, 30), _viertelschritt(r, 8, 24)
        if art == "haus":
            b.geschosse(x0, 0, bx, bz, r.randint(1, 10), y=hoehe0, namen=False)
        elif art == "tiefgarage":
            gx, gz = bx + _viertelschritt(r, 4, 40), bz + _viertelschritt(r, 4, 40)
            ug = r.randint(1, 2)
            b.quader(name(), (x0, hoehe0 - 3 * ug - 0.5, 0), (x0 + gx, hoehe0 - 3 * ug, gz))
            b.quader(name(), (x0, hoehe0 - 3 * ug, 0), (x0 + gx, hoehe0, gz))
            b.quader(name(), (x0, hoehe0, 0), (x0 + gx, hoehe0 + 0.5, gz))
            b.geschosse(x0 + 2, 2, bx, bz, r.randint(1, 10), y=hoehe0 + 0.5, namen=False)
            bx = gx
        elif art == "sockel":
            sx, sz = bx + _viertelschritt(r, 6, 40), bz + _viertelschritt(r, 6, 30)
            sh = 4.0 * r.randint(1, 3)
            b.quader(name(), (x0, hoehe0, 0), (x0 + sx, hoehe0 + sh, sz))
            b.geschosse(x0 + 3, 3, bx, bz, r.randint(2, 16), y=hoehe0 + sh, namen=False)
            bx = sx
        elif art == "halle":
            hx, hz, hh = bx * 2, bz * 2, _viertelschritt(r, 4, 12)
            b.quader(name(), (x0, hoehe0, 0), (x0 + hx, hoehe0 + hh, hz))
            b.quader(name(), (x0 + 2, hoehe0, 2), (x0 + 4, hoehe0 + _viertelschritt(r, 15, 40), 4))
            bx = hx
        elif art == "bodenplatte":
            u = _viertelschritt(r, 0, 4)
            b.quader(name(), (x0, hoehe0 - 0.25, 0), (x0 + bx + 2 * u, hoehe0, bz + 2 * u))
            b.geschosse(x0 + u, u, bx, bz, r.randint(1, 6), y=hoehe0, namen=False)
            bx += 2 * u
        elif art == "satteldachhalle":
            hx, hz, tr = bx * 2, bz * 2, _viertelschritt(r, 2, 8)
            b.satteldach(name(), x0, 0, x0 + hx, hz, traufe=hoehe0 + tr, first=hoehe0 + tr + 2.5, boden=hoehe0)
            b.quader(name(), (x0 + 2, hoehe0, 2), (x0 + 4, hoehe0 + 30, 4))
            bx = hx
        elif art == "halle_mit_dach":
            hx, hz, hh = bx * 2, bz * 2, _viertelschritt(r, 3, 8)
            b.quader(name(), (x0, hoehe0, 0), (x0 + hx, hoehe0 + hh, hz))
            b.satteldach(name(), x0 - 1, -1, x0 + hx + 1, hz + 1, traufe=hoehe0 + hh, first=hoehe0 + hh + 2)
            b.quader(name(), (x0 + 2, hoehe0, 2), (x0 + 4, hoehe0 + 40, 4))
            bx = hx
        elif art == "vordach":
            for px, pz in ((0, 0), (bx - 0.5, 0), (0, bz - 0.5), (bx - 0.5, bz - 0.5)):
                b.quader(name(), (x0 + px, hoehe0, pz), (x0 + px + 0.5, hoehe0 + 4, pz + 0.5))
            b.platte_schraeg(name(), x0, 0, x0 + bx, bz, hoehe0 + 4.25, hoehe0 + 4.25 + bx * r.choice((0.0, 0.05, 0.1, 0.2)), 0.25)
            b.quader(name(), (x0 + bx + 1, hoehe0, 0), (x0 + bx + 5, hoehe0 + 60, 4))
            bx += 5
        elif art == "rampe":
            b.platte_schraeg(name(), x0, 0, x0 + bx, bz, hoehe0 + 0.25, hoehe0 + 0.25 + bx * r.choice((0.06, 0.1, 0.15)), 0.25)
            b.quader(name(), (x0 + bx, hoehe0, 0), (x0 + bx + 10, hoehe0 + 30, bz))
            bx += 10
        else:
            b.quader(name(), (x0, hoehe0, 0), (x0 + 4, hoehe0 + _viertelschritt(r, 20, 80), 4))
            bx = 4
        x0 += bx + _viertelschritt(r, 0, 12)
        breite_gesamt = x0
    gebaut = len(b.knoten)
    assert not b.gelaende

    # Gelände: in sechs von zehn Modellen.
    art = r.choice(("keines", "keines", "keines", "keines", "platte", "hang", "hang", "uneben", "kacheln", "ebene"))
    rand = _viertelschritt(r, 0, 30)
    gx0, gx1, gz0, gz1 = -rand, breite_gesamt + rand, -rand, 30 + rand
    steigung = r.choice((0.0, 0.03, 0.06, 0.1, 0.2))
    amp = r.choice((0.0, 0.1, 0.4, 1.0))
    welle = w._wellen(amp)
    h = lambda x, z: hoehe0 + steigung * (z - gz0) * r_fest + welle(x, z)      # noqa: E731
    r_fest = r.choice((1.0, -1.0))
    if art == "platte":
        b.gelaende.add(b.quader(name(), (gx0, hoehe0 - 0.5, gz0), (gx1, hoehe0, gz1)))
    elif art in ("hang", "uneben"):
        boden = None
        if r.random() < 0.4:
            boden = min(h(x, z) for x in (gx0, gx1) for z in (gz0, gz1)) - amp * 3 - _viertelschritt(r, 0.25, 3)
        b.flaeche(name(), gx0, gz0, gx1, gz1, r.randint(1, 8), r.randint(1, 8), h, boden=boden)
    elif art == "kacheln":
        n = r.randint(2, 3)
        for i in range(n):
            for j in range(n):
                b.flaeche(name(), gx0 + (gx1 - gx0) * i / n, gz0 + (gz1 - gz0) * j / n,
                          gx0 + (gx1 - gx0) * (i + 1) / n, gz0 + (gz1 - gz0) * (j + 1) / n, 3, 3, h)
    elif art == "ebene":
        b.gelaende.add(b.platte_schraeg(name(), gx0, gz0, gx1, gz1, hoehe0, hoehe0 + (gx1 - gx0) * steigung, 0.5))

    zusatz = {}
    if r.random() < 0.5:
        # Alles unter einen Wurzelknoten: verschoben, um die Hochachse gedreht, skaliert (auch gespiegelt).
        winkel = r.uniform(0, 2 * math.pi)
        wurzel = b.gruppe(name(), list(range(len(b.knoten))),
                          translation=[r.uniform(-500, 500), r.uniform(-20, 20), r.uniform(-500, 500)],
                          rotation=[0.0, math.sin(winkel / 2), 0.0, math.cos(winkel / 2)],
                          scale=r.choice(([1.0, 1.0, 1.0], [0.5, 0.5, 0.5], [2.0, 2.0, 2.0], [-1.0, 1.0, 1.0],
                                          [1.0, 1.0, -1.0], [0.001, 0.001, 0.001])))
        del wurzel
    return b, zusatz, gebaut


def test_fuenftausend_zufallsmodelle_verlieren_kein_bauwerk(tmp_path):
    w = _werkzeug()
    r = random.Random(STARTWERT)
    pfad = tmp_path / "zufall.glb"
    zaehler = {"modelle": 0, "mit_gelaende": 0, "form": 0, "unklar": 0, "name": 0}
    for nr in range(ANZAHL):
        b, zusatz, _gebaut = wuerfle(w, r)
        js = b.kopf(**zusatz)
        w.schreibe_glb(js, pfad, binaerblock=nr % 2 == 1)
        aus = glbbox.bauwerksbox(pfad)
        gelesen = glbbox.knotenboxen(js)
        wahr = set(w.stellen(js, b.gelaende))
        zaehler["modelle"] += 1
        zaehler["mit_gelaende"] += bool(wahr)
        box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
        assert all(math.isfinite(v) for e in box for v in e), f"Modell {nr}: Hülle nicht endlich"
        assert all(box[1][i] >= box[0][i] for i in range(3)) and box[1][0] > box[0][0], f"Modell {nr}: leere Hülle"
        if aus["entschieden_durch"] == "name":
            # Ein Zufallsname darf kein Geländewort tragen; sonst prüft diese Probe die falsche Regel.
            raise AssertionError(f"Modell {nr}: die Namensregel hat gegriffen: {aus['gelaende_namen']}")
        weg = set(aus["form_befund"]["gelaende_stellen"]) if aus["entschieden_durch"] == "form" else set()
        zaehler["form"] += bool(weg)
        zaehler["unklar"] += bool((aus["form_befund"] or {}).get("unklar_stellen"))
        assert weg <= wahr, f"Modell {nr}: gebaute Körper {sorted(weg - wahr)} als Gelände abgetrennt"
        szene = aus["bbox_szene"]
        toleranz = 1e-6 * max(1.0, max(abs(v) for e in szene for v in e))
        for stelle, (_name, lo, hi) in enumerate(gelesen["knoten"]):
            if stelle in wahr:
                continue
            wlo, whi = glbbox.nach_welt(lo, hi)
            assert all(box[0][i] - toleranz <= wlo[i] and whi[i] <= box[1][i] + toleranz for i in range(3)), (
                f"Modell {nr}: der gebaute Körper an Stelle {stelle} liegt ausserhalb der Hülle")
    print(f"A0289-2 Zufallsvergleich: {zaehler}")
    assert zaehler["modelle"] >= 5000
    # Die Probe ist nicht leer: Gelände kommt vor, wird abgetrennt, und bleibt auch oft unentschieden.
    assert zaehler["mit_gelaende"] >= 2000 and zaehler["form"] >= 300 and zaehler["unklar"] >= 2000


def test_die_zufallsnamen_tragen_kein_gelaendewort():
    assert not any(maske.ist_gelaende(n or "") for n in NAMEN)
