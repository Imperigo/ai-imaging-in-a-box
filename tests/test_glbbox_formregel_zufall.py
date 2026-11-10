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
    # Runde 3 (Steuerung 10.11.2026 13:06 UTC): Die Abtrennrate ist kein Zielwert mehr. Die Regel trennt
    # nur noch offene, im Ganzen geneigte Flächen ab; in diesem Baukasten sind das wenige. Die Zahl
    # stand in Runde 2 bei 200 und hält hier nur fest, dass die Probe nicht leer ist.
    assert zaehler["mit_gelaende"] >= 2000 and zaehler["form"] >= 50 and zaehler["unklar"] >= 2000


def test_die_zufallsnamen_tragen_kein_gelaendewort():
    assert not any(maske.ist_gelaende(n or "") for n in NAMEN)


# ---------------------------------------------------------------- Runde 3: die Klasse, an der Runde 2 scheiterte

KLASSEN = ("kuppel", "schuessel", "wellendach", "podium", "skatepark", "gruendach", "rampe", "tribuene", "erdhaus",
           "zelt", "tonne")


def wuerfle_klasse(w, r: random.Random):
    """Ein gebauter Körper mit gewölbter, gewellter oder geneigter Oberseite, bis nahe an den Boden,
    AUF dem etwas Höheres aufsetzt; in vier von zehn Modellen daneben ein echter Hang mit Haus.
    Liefert ``(_Bau, art)``; ``bau.gelaende`` trägt die Wahrheit (nur der Hang)."""
    b = w._Bau()
    art = r.choice(KLASSEN)
    R = r.uniform(10, 35)
    h = r.uniform(1.5, 10)
    zu = r.random() < 0.5
    unten = r.choice((0.0, 0.0, r.uniform(0, 1.4)))
    n = r.choice((6, 8, 10, 12))
    if art == "kuppel":
        f = w.kuppel(b, None, 0, 0, R, h, zu, y0=unten, n=n)
    elif art == "schuessel":
        f = w.schuessel(b, "S", 0, 0, R, R * r.uniform(0.6, 1), h, zu, n=n)
    elif art in ("wellendach", "podium"):
        f = w.wellenflaeche(b, "W", -R, -R * 0.8, R, R * 0.8, r.uniform(0.3, 2.0), unten, zu, wellen=r.choice((0.5, 1.5, 2.5, 3.0)), n=n)
    elif art == "skatepark":
        f = lambda x, z: 0.9 * (1 + math.sin(x / 4.0) * math.cos(z / 5.0)) + 0.6 * math.sin(x / 9.0)     # noqa: E731
        b.flaeche("K", -R, -R * 0.7, R, R * 0.7, n, n, f, boden=-0.25 if zu else None, gelaende=False)
    elif art in ("gruendach", "erdhaus"):
        hoch = r.uniform(3, 9)
        if art == "erdhaus" and zu:
            f = lambda x, z, hh=hoch, R=R: max(0.25, hh * (R - x) / (2 * R) + 0.5 * math.sin(z / 3))     # noqa: E731
            b.flaeche("E", -R, -R, R, R, n, n, f, boden=0.0, gelaende=False)
        else:
            f = w.schraegflaeche(b, "G", -R, -R, R, R, 3.5 + r.uniform(0, 1), 3.5 + hoch, False, n=n)
            darunter = r.choice(("geschoss", "waende", "stuetzen", "platte"))
            if darunter == "geschoss":
                b.quader("U", (-R, 0, -R), (R, 3.25, R))
            elif darunter == "waende":
                for lo, hi in (((-R, 0, -R), (R, 3.25, -R + 0.25)), ((-R, 0, R - 0.25), (R, 3.25, R)),
                               ((-R, 0, -R), (-R + 0.25, 3.25, R)), ((R - 0.25, 0, -R), (R, 3.25, R))):
                    b.quader("U", lo, hi)
            elif darunter == "stuetzen":
                for x, z in ((-R + 1, -R + 1), (R - 1.5, -R + 1), (-R + 1, R - 1.5), (R - 1.5, R - 1.5)):
                    b.quader("U", (x, 0, z), (x + 0.5, 3.25, z + 0.5))
            else:
                b.quader("U", (-R, -0.25, -R), (R, 0, R))
    elif art == "rampe":
        f = w.schraegflaeche(b, "R", -R, -8, R, 8, 0.25, 0.25 + 2 * R * r.uniform(0.05, 0.18), True, n=n, uneben=0.1)
    elif art == "tribuene":
        s = r.uniform(0.42, 0.75)
        f = lambda x, z, s=s: 0.5 + s * (z + 12) + 0.2 * math.sin(x / 6.0) * math.sin(z / 3.0)     # noqa: E731
        b.flaeche("T", -R, -12, R, 12, n, 8, f, boden=0.0 if zu else None, gelaende=False)
    elif art == "zelt":
        k = r.choice((6, 8, 12))
        e = [(0, h, 0)] + [(R * math.cos(2 * math.pi * s / k), 0, R * math.sin(2 * math.pi * s / k)) for s in range(k)]
        b.netz("Z", e, [(0, 1 + (s + 1) % k, 1 + s) for s in range(k)])
        f = lambda x, z, h=h, R=R: max(0.0, h * (1 - math.hypot(x, z) / R))     # noqa: E731
    else:
        f = lambda x, z, h=h, R=R, u=unten: u + h * math.cos(math.pi * z / (2 * R))     # noqa: E731
        b.flaeche("H", -R, -R, R, R, 2, 14, f, boden=0.0, gelaende=False)
    # Ein bis zwei Aufbauten, die AUF der Fläche aufsetzen, 1,5 bis 8 m breit.
    for _ in range(r.randint(1, 2)):
        breite = r.uniform(1.5, 8)
        x, z = r.uniform(-R * 0.6, R * 0.6 - breite), r.uniform(-6, 6 - min(breite, 5))
        w.aufbau(b, r.choice(NAMEN), f, x, z, breite, min(breite, 5), r.uniform(3, 60))
    if r.random() < 0.4:
        s = r.choice((0.06, 0.1, 0.15))
        hang = lambda x, z, s=s: s * z + w._wellen(0.3)(x, z)     # noqa: E731
        x0 = R + r.uniform(1, 20)
        b.flaeche(r.choice(NAMEN), x0, -25, x0 + 60, 25, 12, 10, hang)
        b.haus(x0 + 24, -5, 12, 10, 12, y=min(hang(0, z) for z in (-5, 5)))
    return b, art


def test_fuenftausend_modelle_der_schwachen_klasse_verlieren_kein_bauwerk(tmp_path):
    """Runde 3, M3: Der Zufallsvergleich enthält jetzt ausdrücklich die Klasse, an der Runde 2
    scheiterte. An jedem Modell: kein gebauter Körper abgetrennt oder ausserhalb, Hülle endlich."""
    w = _werkzeug()
    r = random.Random(STARTWERT + 3)
    pfad = tmp_path / "klasse.glb"
    je_art = {k: 0 for k in KLASSEN}
    haenge = hang_ab = 0
    for nr in range(ANZAHL):
        b, art = wuerfle_klasse(w, r)
        js = b.kopf()
        w.schreibe_glb(js, pfad, binaerblock=nr % 2 == 1)
        aus = glbbox.bauwerksbox(pfad)
        je_art[art] += 1
        wahr = set(w.stellen(js, b.gelaende))
        weg = set(aus["form_befund"]["gelaende_stellen"]) if aus["entschieden_durch"] == "form" else set()
        assert weg <= wahr, f"Modell {nr} ({art}): gebaute Körper {sorted(weg - wahr)} als Gelände abgetrennt"
        box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
        assert all(math.isfinite(v) for e in box for v in e) and box[1][0] > box[0][0], f"Modell {nr}"
        toleranz = 1e-6 * max(1.0, max(abs(v) for e in aus["bbox_szene"] for v in e))
        for stelle, (_name, lo, hi) in enumerate(glbbox.knotenboxen(js)["knoten"]):
            if stelle not in wahr:
                wlo, whi = glbbox.nach_welt(lo, hi)
                assert all(box[0][i] - toleranz <= wlo[i] and whi[i] <= box[1][i] + toleranz for i in range(3)), (
                    f"Modell {nr} ({art}): gebauter Körper {stelle} ausserhalb der Hülle")
        haenge += bool(wahr)
        hang_ab += bool(wahr) and weg == wahr
    print(f"A0289-3 Zufall der schwachen Klasse: {ANZAHL} Modelle, 0 Verluste; je Art {je_art}; "
          f"echter Hang daneben in {haenge} Modellen, davon {hang_ab} abgetrennt")
    assert min(je_art.values()) >= 300 and haenge >= 1500


def test_zweitausend_zufaellig_beschaedigte_dateien_werfen_nur_glberror(tmp_path):
    """Runde 3, M2, am Kern: Zahlen im Kopf durch beliebige ersetzt, Dateien abgeschnitten, Bytes
    verdreht. Erlaubt ist eine Auskunft mit endlicher Hülle oder die gewollte Weigerung ``GlbError``."""
    import json as _json
    import struct as _struct
    w = _werkzeug()
    b = w._Bau()
    hang = w._hang(0.1, "z")
    b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, hang)
    b.haus(-6, -5, 12, 10, 12, y=hang(0, 0) - 0.5)
    basis = tmp_path / "basis.glb"
    w.schreibe_glb(b.kopf(), basis, binaerblock=True)
    roh = basis.read_bytes()
    laenge = _struct.unpack_from("<I", roh, 12)[0]
    kopf, rest = _json.loads(roh[20:20 + laenge]), roh[20 + laenge:]
    werte = [0, -1, 1, 3, 255, 65536, 2 ** 31 - 1, 2 ** 31, 2 ** 32, 2 ** 63 - 1, -2 ** 63, 9 * 10 ** 18, 1e300, 1.5, None,
             "x", [], {}, True, 5126, 5123, 2 ** 62, 2 ** 70, float("nan"), float("inf")]
    felder = ["byteOffset", "byteLength", "byteStride", "count", "bufferView", "buffer", "componentType", "indices",
              "POSITION", "mode", "mesh", "scene", "min", "max", "nodes", "primitives", "attributes"]
    r = random.Random(STARTWERT + 5)
    ziel = tmp_path / "kaputt.glb"
    zaehler = {"auskunft": 0, "glberror": 0}

    def orte(knoten, gefunden):
        if isinstance(knoten, dict):
            for k, v in knoten.items():
                if k in felder:
                    gefunden.append((knoten, k))
                orte(v, gefunden)
        elif isinstance(knoten, list):
            for v in knoten:
                orte(v, gefunden)
        return gefunden

    for nr in range(2000):
        if nr % 4 == 3:
            daten = bytearray(roh)
            if r.random() < 0.5:
                daten = daten[:r.randrange(len(daten))]
            else:
                for _ in range(r.randint(1, 5)):
                    daten[r.randrange(len(daten))] = r.randrange(256)
            ziel.write_bytes(bytes(daten))
        else:
            js = _json.loads(_json.dumps(kopf))
            for _ in range(r.randint(1, 4)):
                knoten, feld = r.choice(orte(js, []))
                knoten[feld] = r.choice(werte)
            block = _json.dumps(js, separators=(",", ":")).encode("utf-8")
            block += b" " * (-len(block) % 4)
            ziel.write_bytes(_struct.pack("<III", 0x46546C67, 2, 20 + len(block) + len(rest))
                             + _struct.pack("<II", len(block), 0x4E4F534A) + block + rest)
        try:
            aus = glbbox.bauwerksbox(ziel)
        except glbbox.GlbError:
            zaehler["glberror"] += 1
            continue
        zaehler["auskunft"] += 1
        box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
        if box is not None:
            assert all(math.isfinite(v) for e in box for v in e), f"Datei {nr}: {box}"
    print(f"A0289-3 beschädigte Dateien am Kern: 2000 gelesen, {zaehler}")
    assert zaehler["auskunft"] >= 200 and zaehler["glberror"] >= 200
