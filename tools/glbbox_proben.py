"""Die gemeinsame Probendatei der Geländeregel: Python und Swift prüfen dieselbe Box.

A0267. Die Geländeregel für die Hüllbox einer glb steht am Heim-PC in ``aiimaging.glbbox``
(``maske.ist_gelaende``); der Mac rechnet sie in ``Glbauskunft`` (Swift) für das nach, was
aus den Namen im JSON-Kopf lesbar ist. Zwei Rechnungen laufen auseinander, sobald niemand sie
nebeneinanderlegt. Darum gibt es EINE Datei (``tests/daten/glbbox_gelaenderegel.json``):

* jeder Fall trägt den JSON-Kopf einer synthetischen glb (im Repo erzeugt, keine echten Daten);
* ``erwartet`` ist, was ``glbbox.bauwerksbox`` daraus macht (Python-Probe: stimmt es noch?);
* die Swift-Probe (``GlbauskunftGelaendeTests``) liest dieselbe Datei und verlangt dieselbe Box.

**Die Formfälle (A0289, «Gelände an der Form»).** Unter ``formfaelle`` stehen Modelle, deren
Gelände KEINEN erkennbaren Namen trägt. Dort entscheidet am Heim-PC die Zweitmeinung
(``aiimaging.gelaendeform``, über ``glbbox.bauwerksbox``); der Mac bildet sie in
``Kern/Gelaendeform.swift`` ab. Je Fall steht die Python-Entscheidung (``erwartet``) und, was der
Mac liefern muss (``mac``): dasselbe, ausser in den einzeln benannten Fällen, in denen er nur
«nicht entscheidbar» sagen darf (Szenenhülle mit Vermerk), nie umgekehrt. Die Gruppen:
``form`` (Gelände ohne Namen), ``gegenfall`` (kein Gelände oder eine Tiefgaragendecke: nichts darf
vom Grundriss verloren gehen), ``befund`` (die Formregel trifft hier einen Hausteil; gemeldet,
nicht verändert).

Neu erzeugen: ``python tools/glbbox_proben.py --schreiben``. Ohne Schalter wird nur geprüft, ob die
Datei zum Stand des Kerns passt (Ausgang 1, wenn nicht).
"""
from __future__ import annotations

import json
import math
import struct
import sys
import tempfile
from pathlib import Path

ZIEL = Path(__file__).resolve().parents[1] / "tests" / "daten" / "glbbox_gelaenderegel.json"


def _quader(name, lo, hi, **knoten):
    """Ein Mesh-Knoten (glTF, Y oben) mit Box ``lo``..``hi``; liefert ``(knoten, netz, zugriff)``."""
    k = {"name": name, **knoten}
    netz = {"primitives": [{"attributes": {"POSITION": None}}]}
    zugriff = {"componentType": 5126, "count": 8, "type": "VEC3",
               "min": list(lo), "max": list(hi)}
    return k, netz, zugriff


def _glb_kopf(teile, szene=None, eltern=None):
    """JSON-Kopf aus Quadern. ``eltern``: ``{index: {"name":…, "translation":…}}`` vor die Kinder."""
    knoten, netze, zugriffe = [], [], []
    for i, (name, lo, hi, extra) in enumerate(teile):
        k, n, z = _quader(name, lo, hi, **extra)
        k["mesh"] = i
        n["primitives"][0]["attributes"]["POSITION"] = i
        knoten.append(k)
        netze.append(n)
        zugriffe.append(z)
    return knoten, netze, zugriffe


def _haus_am_hang():
    # Gelände 60 x 50 m, 0,3 m dick unter der Nulllinie; Haus 30,5 x 27,7 m, 9,1 m hoch, unter einem
    # verschobenen Elternknoten. Welt = (x, -z, y): glTF-Z 25 -> Welt -Y.
    teile = [
        ("Gelaende_Hang", (-30, -0.3, -25), (30, 0.0, 25), {}),
        ("Wand_Nord", (-15.25, 0.0, -13.85), (15.25, 6.0, 13.85), {}),
        ("Dach", (-15.25, 6.0, -13.85), (15.25, 9.1, 13.85), {}),
    ]
    knoten, netze, zugriffe = _glb_kopf(teile)
    # Elternknoten "Haus" (Index 3) trägt Wand und Dach; keine Verschiebung, damit die Box der
    # Beschreibung im Auftrag entspricht, aber mit Skalierung 1 und einer Drehung um 0 als Gegenprobe.
    knoten.append({"name": "Haus", "children": [1, 2], "translation": [0.0, 0.0, 0.0]})
    return {"asset": {"version": "2.0"}, "scene": 0,
            "scenes": [{"nodes": [0, 3]}], "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def _einfach(teile, wurzeln=None):
    knoten, netze, zugriffe = _glb_kopf(teile)
    return {"asset": {"version": "2.0"}, "scene": 0,
            "scenes": [{"nodes": wurzeln if wurzeln is not None else list(range(len(knoten)))}],
            "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def _verschoben():
    # Haus unter einem verschobenen Elternknoten, Gelände daneben: die Elternmatrix muss in die
    # Bauwerksbox eingehen, genau wie in die Szenenbox.
    teile = [
        ("Toposolid_1", (-40, -0.5, -40), (40, 0.0, 40), {}),
        ("Wand", (0.0, 0.0, 0.0), (10.0, 5.0, 8.0), {}),
    ]
    knoten, netze, zugriffe = _glb_kopf(teile)
    knoten.append({"name": "Gebaeude", "children": [1], "translation": [5.0, 1.0, -3.0]})
    return {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0, 2]}],
            "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def definitionen() -> list[dict]:
    wuerfel = lambda x: ((x, 0.0, 0.0), (x + 4.0, 3.0, 4.0), {})   # noqa: E731
    return [
        {"fall": "haus-am-hang", "glb": _haus_am_hang(),
         "sagt": "Gelände 60 x 50 m neben dem Haus 30,5 x 27,7 m: die Hausbox, nicht die Szene."},
        {"fall": "elternknoten-verschoben", "glb": _verschoben(),
         "sagt": "Die Matrix des Elternknotens geht in die Bauwerksbox ein."},
        {"fall": "wortgrenzen", "glb": _einfach([
            ("Umgebung - Toposolid", (-50, -0.4, -50), (50, 0.0, 50), {}),
            ("IfcSite_1a2b3c", (-60, -1.0, -60), (60, -0.4, 60), {}),
            ("Waenden_EG", *wuerfel(0)),
            ("Geländer_Balkon", *wuerfel(5)),
            ("Bodenplatte des 2. OG", *wuerfel(10)),
        ]), "sagt": "Wörter an Wortgrenzen und das Muster ifcsite*: Toposolid und IfcSite sind Gelände, "
                    "Geländer und Bodenplatte nicht."},
        {"fall": "grossbuchstaben", "glb": _einfach([
            ("TERRAIN", (-30, -0.5, -30), (30, 0.0, 30), {}),
            ("Haus_A", *wuerfel(0)),
            ("Haus_B", *wuerfel(6)),
        ]), "sagt": "Kleinschreibung vor dem Vergleich."},
        {"fall": "ohne-gelaende", "glb": _einfach([
            ("Haus_A", *wuerfel(0)),
            ("Haus_B", *wuerfel(6)),
            ("Haus_C", *wuerfel(12)),
        ]), "sagt": "Kein Gelände erkennbar: Szenenbox, nicht abgetrennt."},
        {"fall": "alles-gelaende", "glb": _einfach([
            ("Terrain_A", (-20, -0.5, -20), (0, 0.0, 20), {}),
            ("Gelände_B", (0, -0.5, -20), (20, 0.0, 20), {}),
        ]), "sagt": "Alles Gelände: nie eine leere Box, es bleibt die Szenenbox."},
    ]


class _Bau:
    """Ein glTF-Kopf aus Quadern und Gruppenknoten, für die Formfälle (A0289)."""

    def __init__(self):
        self.knoten, self.netze, self.zugriffe = [], [], []

    def quader(self, name, lo, hi, **extra) -> int:
        """Ein Mesh-Knoten mit der lokalen Box ``lo``..``hi`` (glTF, Y oben); liefert den Knotenindex."""
        self.zugriffe.append({"componentType": 5126, "count": 8, "type": "VEC3",
                              "min": list(lo), "max": list(hi)})
        self.netze.append({"primitives": [{"attributes": {"POSITION": len(self.zugriffe) - 1}}]})
        k = {"mesh": len(self.netze) - 1, **extra}
        if name is not None:
            k = {"name": name, **k}
        self.knoten.append(k)
        return len(self.knoten) - 1

    def zwei_teile(self, name, teil_a, teil_b, **extra) -> int:
        """Ein Mesh-Knoten mit ZWEI Primitiven: die Box ist die Hülle über beide."""
        stellen = []
        for lo, hi in (teil_a, teil_b):
            self.zugriffe.append({"componentType": 5126, "count": 8, "type": "VEC3",
                                  "min": list(lo), "max": list(hi)})
            stellen.append(len(self.zugriffe) - 1)
        self.netze.append({"primitives": [{"attributes": {"POSITION": s}} for s in stellen]})
        self.knoten.append({"name": name, "mesh": len(self.netze) - 1, **extra})
        return len(self.knoten) - 1

    def gruppe(self, name, kinder, **extra) -> int:
        self.knoten.append({"name": name, "children": list(kinder), **extra})
        return len(self.knoten) - 1

    def haus(self, x, z, breite, tiefe, hoehe, y=0.0, stamm="Bauteil") -> list[int]:
        """Ein Haus aus drei Körpern ohne Bodenplatte: zwei Geschosse und ein Dachkörper."""
        halb = hoehe * 0.4
        return [
            self.quader(f"{stamm}_EG", (x, y, z), (x + breite, y + halb, z + tiefe)),
            self.quader(f"{stamm}_OG", (x, y + halb, z), (x + breite, y + 2 * halb, z + tiefe)),
            self.quader(f"{stamm}_Dach", (x, y + 2 * halb, z), (x + breite, y + hoehe, z + tiefe)),
        ]

    def kopf(self, wurzeln=None, **zusatz) -> dict:
        kinder = {k for n in self.knoten for k in n.get("children", [])}
        if wurzeln is None:
            wurzeln = [i for i in range(len(self.knoten)) if i not in kinder]
        js = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": list(wurzeln)}],
              "nodes": self.knoten, "meshes": self.netze, "accessors": self.zugriffe}
        js.update(zusatz)
        return js


def _viertel(winkel_grad: float) -> list[float]:
    """Quaternion (x, y, z, w) einer Drehung um die glTF-Z-Achse: ein geneigter Hang."""
    halb = math.radians(winkel_grad) / 2.0
    return [0.0, 0.0, round(math.sin(halb), 9), round(math.cos(halb), 9)]


def formdefinitionen() -> list[dict]:
    """Modelle mit Gelände OHNE erkennbaren Namen, samt Gegenfällen (A0289).

    Kein Name dieser Fälle trägt ein Wort aus ``maske.GELAENDE_WOERTER`` oder passt auf
    ``maske.GELAENDE_MUSTER``, ausser dort, wo es im Satz steht (die beiden Fälle «Namen fanden …»).
    Zahlen an den Schwellen sind so gewählt, dass sie in jedem JSON-Leser exakt ankommen (ganze
    Zahlen, Halbe, Viertel).
    """
    faelle: list[dict] = []

    def fall(name, gruppe, sagt, bau_oder_js):
        js = bau_oder_js.kopf() if isinstance(bau_oder_js, _Bau) else bau_oder_js
        faelle.append({"fall": name, "gruppe": gruppe, "sagt": sagt, "glb": js})

    # ---------------------------------------------------------------- Gelände unter dem Haus
    b = _Bau()
    b.quader("Mesh.001", (-30, -0.5, -25), (30, 0.0, 25))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-ebene-unter-dem-haus", "form",
         "Ebene Platte 60 x 50 m unter dem Haus 12 x 10 m, kein Name sagt Gelände.", b)

    b = _Bau()
    b.quader("Objekt_7", (-40, -0.4, -20), (0, 0.0, 20))
    b.haus(2, -5, 12, 10, 8)
    fall("form-ebene-neben-dem-haus", "form",
         "Die Platte liegt NEBEN dem Haus (Vorplatz 40 x 40 m): sie wird abgetrennt, die Hülle ist das Haus.", b)

    b = _Bau()
    b.quader("Koerper", (-30, -10.0, -30), (30, -9.5, 30))
    b.quader("Keller", (-5, -9.5, -5), (5, 0.0, 5))
    b.haus(-5, -5, 10, 10, 9)
    fall("form-platte-tief-unter-null", "form",
         "Die Platte liegt tief unter der Nulllinie, ein Keller steht darauf.", b)

    # ---------------------------------------------------------------- Hang
    b = _Bau()
    b.quader("IfcBuildingElementProxy_Hang_0a1b", (-30, 0, -25), (30, 4, 25))
    b.haus(-6, -5, 12, 10, 12, y=2.0)
    fall("form-hang-flach", "form",
         "Hang als ein Körper, 4 m Höhenunterschied auf 50 m: flach genug und unten.", b)

    b = _Bau()
    b.quader("Hangkoerper", (-30, 0, -25), (30, 6, 25))
    b.haus(-6, -5, 12, 10, 10, y=3.0)
    fall("form-hang-oberkante-zu-hoch", "form",
         "Hang mit 6 m: seine Oberkante sitzt bei 46 % der Szenenhöhe. Nicht entscheidbar, also Szenenhülle.", b)

    b = _Bau()
    b.quader("Hangkoerper", (-30, 0, -25), (30, 10, 25))
    b.haus(-6, -5, 12, 10, 30, y=5.0)
    fall("form-hang-steil", "form",
         "Hang mit 10 m auf 50 m: der Körper ragt auf (Flachheit 0,2). Die Form trennt ihn nicht.", b)

    b = _Bau()
    b.quader("Flaeche", (-30, -0.25, -25), (30, 0.25, 25), rotation=_viertel(3.0))
    b.haus(-6, -5, 12, 10, 14, y=0.5)
    fall("form-hang-gedrehte-platte", "form",
         "Eine dünne Platte, am Knoten um 3 Grad geneigt: die acht Ecken werden einzeln gedreht.", b)

    # ---------------------------------------------------------------- Mulde
    b = _Bau()
    b.quader("Mulde", (-40, -3, -40), (40, 0, 40))
    b.haus(-5, -5, 10, 10, 9, y=-2.5)
    fall("form-mulde", "form",
         "Mulde 80 x 80 m, 3 m tief, das Haus steht darin: gross, flach, unten.", b)

    b = _Bau()
    b.quader("Mulde", (-40, -5, -40), (40, 0, 40))
    b.haus(-5, -5, 10, 10, 7, y=-4.0)
    fall("form-mulde-tief", "form",
         "Tiefe Mulde, niedriges Haus: die Oberkante der Mulde sitzt bei 62,5 % der Szenenhöhe. "
         "Die Form hält sie für eine Decke, es bleibt die Szenenhülle.", b)

    # ---------------------------------------------------------------- Terrasse
    b = _Bau()
    b.quader("Stufe_unten", (-25, 0, -30), (25, 0.5, 0))
    b.quader("Stufe_oben", (-25, 0, 0), (25, 3.5, 30))
    b.haus(-6, 8, 12, 10, 9, y=3.5)
    fall("form-terrasse-zwei-stufen", "form",
         "Zwei Geländestufen, das Haus auf der oberen: beide werden abgetrennt.", b)

    b = _Bau()
    b.quader("Stufe_unten", (-25, 0, -30), (25, 0.5, 0))
    b.quader("Stufe_oben", (-25, 0, 0), (25, 4, 30))
    b.haus(-6, 8, 12, 10, 6, y=4.0)
    fall("form-terrasse-obere-stufe-unklar", "form",
         "Die obere Stufe reicht auf 40 % der Szenenhöhe: nicht entscheidbar, sie bleibt in der Hülle; "
         "die untere wird abgetrennt.", b)

    # ---------------------------------------------------------------- Schwellen, exakt
    b = _Bau()
    for i, (x, z) in enumerate([(-30, -30), (0, -30), (-30, 0), (0, 0)]):
        b.quader(f"Feld_{i + 1}", (x, -0.5, z), (x + 30, 0.0, z + 30))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-vier-viertel-genau-an-der-schwelle", "form",
         "Gelände in vier Feldern, jedes genau 25 % des Grundrisses: die Schwelle gilt ab 25 %.", b)

    b = _Bau()
    for i in range(6):
        b.quader(f"Feld_{i + 1}", (-30 + 10 * i, -0.5, -30), (-20 + 10 * i, 0.0, 30))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-sechs-streifen-zu-klein", "form",
         "Gelände in sechs Streifen, jeder 17 % des Grundrisses: je Knoten zu klein, die Form trennt "
         "nichts (Korngrösse; die Familienprüfung ist am Heim-PC Vorgabe aus).", b)

    b = _Bau()
    b.quader("Platte", (-10, 0, -10), (10, 3, 10))
    b.haus(-5, -5, 10, 10, 17, y=3.0)
    fall("form-flachheit-genau-an-der-schwelle", "form",
         "Platte 20 x 20 m, 3 m dick: Flachheit genau 0,15. Die Schwelle gilt bis 0,15.", b)

    b = _Bau()
    b.quader("Platte", (-20, 0, -20), (20, 6.5, 20))
    b.haus(-5, -5, 10, 10, 13.5, y=6.5)
    fall("form-flachheit-darueber", "form",
         "Eine Platte 40 x 40 m, 6,5 m dick: Flachheit 0,1625, der Körper ragt auf. Es bleibt die Szenenhülle.", b)

    b = _Bau()
    b.quader("Platte", (-25, 5, -25), (25, 7, 25))
    b.quader("Sockel", (-5, 0, -5), (5, 5, 5))
    b.quader("Turm", (-5, 7, -5), (5, 20, 5))
    fall("form-oberkante-genau-35-prozent", "form",
         "Flache Platte 50 x 50 m, Oberkante bei 7 von 20 m: genau 35 %. Die Schwelle gilt bis 35 %.", b)

    b = _Bau()
    b.quader("Platte", (-25, 10, -25), (25, 12, 25))
    b.quader("Sockel", (-5, 0, -5), (5, 10, 5))
    b.quader("Turm", (-5, 12, -5), (5, 20, 5))
    fall("form-oberkante-genau-60-prozent", "form",
         "Oberkante bei 12 von 20 m: genau 60 %, also noch «nicht entscheidbar» und nicht «Decke».", b)

    # ---------------------------------------------------------------- Vorplatz, Strasse
    b = _Bau()
    b.quader("Belag", (-30, -0.3, -10), (-10, 0.0, 10))
    b.haus(-8, -10, 28, 20, 9)
    fall("form-vorplatz-an-der-schmalseite", "form",
         "Vorplatz 20 x 20 m bei einer Szene von 50 x 20 m: 40 %, flach, unten. Er wird abgetrennt.", b)

    b = _Bau()
    b.quader("Belag", (-16, -0.3, -10), (-8, 0.0, 10))
    b.haus(-8, -10, 28, 20, 9)
    fall("form-vorplatz-zu-klein", "form",
         "Vorplatz 8 x 20 m bei einer Szene von 36 x 20 m: 22 % des Grundrisses, zu klein. Er bleibt "
         "in der Hülle.", b)

    b = _Bau()
    b.quader("Belag", (-50, -0.3, -2), (50, 0.0, 2))
    b.haus(-10, 4, 20, 30, 9)
    fall("form-strasse-schmal", "form",
         "Ein Strassenband 100 x 4 m: 11 % des Grundrisses, zu klein. Es bleibt in der Hülle.", b)

    # ---------------------------------------------------------------- Knotenbaum
    b = _Bau()
    b.quader("Einheitsquader", (-0.5, -0.5, -0.5), (0.5, 0.5, 0.5),
             translation=[0.0, -0.25, 0.0], scale=[60.0, 0.5, 50.0])
    teile = b.haus(0, 0, 12, 10, 9)
    b.gruppe("Gebaeude", teile, translation=[-6.0, 0.0, -5.0])
    fall("form-skalierter-knoten", "form",
         "Das Gelände ist ein Einheitsquader mit Skalierung am Knoten, das Haus hängt an einem "
         "verschobenen Elternknoten.", b)

    b = _Bau()
    b.quader("Flaeche", (-30, -0.5, -25), (30, 0.0, 25),
             matrix=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 100, 2, -50, 1])
    teile = b.haus(-6, -5, 12, 10, 9)
    b.gruppe("Gebaeude", teile, matrix=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 100, 2, -50, 1])
    fall("form-matrix-am-knoten", "form",
         "Gelände und Haus tragen eine Matrix (spaltenweise gespeichert) mit Verschiebung.", b)

    b = _Bau()
    platte = b.quader("Flaeche", (-30, -0.5, -25), (30, 0.0, 25))
    innen = b.gruppe("Umgebung_innen", [platte], translation=[10.0, 0.0, 0.0])
    b.gruppe("Umgebung", [innen], translation=[0.0, -1.0, 5.0])
    teile = b.haus(-6, -5, 12, 10, 9)
    b.gruppe("Gebaeude", teile, rotation=[0.0, 0.70710678, 0.0, 0.70710678])
    fall("form-verschachtelt-und-gedreht", "form",
         "Das Gelände hängt zwei Ebenen tief, das Haus ist am Elternknoten um 90 Grad gedreht.", b)

    b = _Bau()
    b.zwei_teile("Flaeche", ((-30, -0.5, -25), (0, 0.0, 25)), ((0, -0.5, -25), (30, 0.0, 25)))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-zwei-primitive", "form",
         "Das Gelände ist EIN Knoten mit zwei Primitiven: seine Box ist die Hülle über beide.", b)

    b = _Bau()
    b.quader("Flaeche", (-30, -0.5, -25), (30, 0.0, 25))
    b.haus(-6, -5, 12, 10, 9)
    js = b.kopf()
    del js["scenes"], js["scene"]
    fall("form-ohne-szenenliste", "form",
         "Die Datei nennt keine Szene: alles, was kein Kind ist, ist Wurzel.", js)

    b = _Bau()
    fremd = b.quader("Nachbarblock", (-500, 0, -500), (500, 80, 500))
    platte = b.quader("Flaeche", (-30, -0.5, -25), (30, 0.0, 25))
    teile = b.haus(-6, -5, 12, 10, 9)
    js = b.kopf()
    js["scenes"] = [{"nodes": [fremd]}, {"nodes": [platte, *teile]}]
    js["scene"] = 1
    fall("form-zweite-szene-aktiv", "form",
         "Zwei Szenen, die zweite ist aktiv: der Block der ersten zählt nicht mit.", js)

    b = _Bau()
    b.quader("Flaeche", (-40, -0.5, -35), (40, 0.0, 35))
    for g in range(3):
        for i in range(4):
            b.quader(f"Wand_{g}_{i}", (-8 + 4 * i, 3.0 * g, -6), (-4 + 4 * i, 3.0 * g + 2.7, 6))
        b.quader(f"Decke_{g}", (-8, 3.0 * g + 2.7, -6), (8, 3.0 * g + 3.0, 6))
    b.quader("Dachaufbau", (-2, 9, -2), (2, 10.5, 2))
    fall("form-haus-aus-vielen-teilen", "form",
         "Ein Haus aus sechzehn Teilen (Wände, Decken, Dachaufbau) auf einer Platte 80 x 70 m: die "
         "Geschossdecken sind klein gegen die Szene und bleiben Bauwerk.", b)

    b = _Bau()
    b.quader("Platte", (-30, -0.5, -25), (0, 0.0, 25))
    b.quader("Platte", (0, -0.5, -25), (30, 0.0, 25))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-zwei-platten-gleicher-name", "form",
         "Zwei Geländeplatten tragen denselben Namen, kein Bauteil teilt ihn: beide werden abgetrennt.", b)

    # ---------------------------------------------------------------- Namen und Form zusammen
    b = _Bau()
    b.quader("Terrain_Rest", (29, -0.5, -25), (30, 0.0, 25))
    b.quader("Flaeche", (-30, -0.5, -25), (29, 0.0, 25))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-namen-fanden-zu-wenig", "form",
         "Die Namensregel findet einen Randstreifen, die grosse Platte ohne Namen bleibt. Die Form "
         "ergänzt die Namen nicht: es bleibt bei der Namensentscheidung.", b)

    b = _Bau()
    b.quader("Terrain_Aussen", (-60, -0.5, -50), (60, 0.0, 50))
    b.quader("Flaeche", (-12, -0.3, -10), (12, 0.0, 10))
    b.haus(-6, -5, 12, 10, 9)
    fall("form-namen-fanden-genug", "form",
         "Die Namensregel trennt das grosse Gelände, die Rahmung wird deutlich enger: die Form wird "
         "nicht gefragt, die namenlose Platte unter dem Haus bleibt.", b)

    # ---------------------------------------------------------------- Namensgleichheit: der Mac darf abweichen
    b = _Bau()
    b.quader(None, (-30, -0.5, -25), (30, 0.0, 25))
    for lo, hi in (((-6, 0, -5), (6, 3, 5)), ((-6, 3, -5), (6, 6, 5)), ((-6, 6, -5), (6, 9, 5))):
        b.quader(None, lo, hi)
    fall("form-kein-knoten-hat-einen-namen", "form",
         "Kein Knoten trägt einen Namen. Der Heim-PC trennt nach Namen der Form-Treffer und verliert "
         "damit ALLE Teile; der Mac sagt «nicht entscheidbar» und behält die Szenenhülle.", b)

    b = _Bau()
    b.quader("Mesh", (-30, -0.5, -25), (30, 0.0, 25))
    b.quader("Mesh", (-6, 0, -5), (6, 6, 5))
    b.quader("Dach", (-6, 6, -5), (6, 9, 5))
    fall("form-gelaende-und-bauteil-gleicher-name", "form",
         "Gelände und ein Geschoss heissen gleich. Der Heim-PC nimmt das Geschoss mit dem Gelände "
         "heraus; der Mac sagt «nicht entscheidbar» und behält die Szenenhülle.", b)

    # ---------------------------------------------------------------- Gegenfälle
    b = _Bau()
    b.haus(-6, -5, 12, 10, 9)
    b.quader("Anbau", (6, 0, -5), (10, 3, 0))
    fall("gegen-haus-ohne-gelaende", "gegenfall",
         "Ein Haus mit Anbau, kein Gelände, keine Bodenplatte als eigener Knoten.", b)

    b = _Bau()
    b.quader("Waende_UG", (-20, -6.0, -15), (20, 0.0, 15))
    b.quader("Decke_ueber_UG", (-20, 0.0, -15), (20, 0.4, 15))
    b.haus(-6, -5, 12, 10, 6, y=0.4)
    fall("gegen-tiefgaragendecke", "gegenfall",
         "Zwei Untergeschosse 40 x 30 m, darüber die Tiefgaragendecke bei 52 % der Szenenhöhe, darauf "
         "das Haus: die Decke ist an der Form nicht entscheidbar und bleibt in der Hülle.", b)

    b = _Bau()
    b.quader("Waende_UG", (-20, -3.0, -15), (20, 0.0, 15))
    b.quader("Decke_ueber_UG", (-20, 0.0, -15), (20, 0.4, 15))
    b.quader("Aufbau", (-6, 0.4, -5), (6, 2.0, 5))
    fall("gegen-tiefgaragendecke-oben", "gegenfall",
         "Eine Tiefgarage mit niedrigem Aufbau: die Decke sitzt bei 68 % der Szenenhöhe und gilt als "
         "Decke (Bauwerk).", b)

    b = _Bau()
    b.haus(-6, -5, 12, 10, 9)
    b.quader("Flachdach", (-8, 9.0, -7), (8, 9.3, 7))
    fall("gegen-flachdach-mit-ueberstand", "gegenfall",
         "Ein Flachdach mit Überstand: gross und flach, aber ganz oben. Es bleibt Bauwerk.", b)

    b = _Bau()
    b.quader("Halle", (-20, 0, -10), (20, 6, 10))
    fall("gegen-ein-einziger-koerper", "gegenfall",
         "Ein einziger Körper: nichts zu trennen.", b)

    b = _Bau()
    b.quader("Scheibe_A", (-10, 0, 0), (10, 0, 8))
    b.quader("Scheibe_B", (-10, 0, 8), (10, 0, 16))
    fall("gegen-szene-ohne-hoehe", "gegenfall",
         "Eine Szene ohne Höhe (zwei flache Scheiben): die Form sagt über sie nichts, es bleibt die Szenenhülle.", b)

    b = _Bau()
    b.quader("Zwischendecke", (-10, 4.0, -8), (10, 4.3, 8))
    b.quader("Stuetzen", (-10, 0.0, -8), (10, 4.0, 8))
    b.quader("Obergeschoss", (-10, 4.3, -8), (10, 9.0, 8))
    fall("gegen-zwischendecke-auf-halber-hoehe", "gegenfall",
         "Eine Geschossdecke über den ganzen Grundriss auf 48 % der Höhe: nicht entscheidbar, bleibt.", b)

    # ---------------------------------------------------------------- Befunde an der Python-Regel
    b = _Bau()
    b.quader("Bodenplatte_EG", (-6, -0.3, -5), (6, 0.0, 5))
    b.haus(-6, -5, 12, 10, 9)
    fall("befund-bodenplatte-ganzer-grundriss", "befund",
         "Haus OHNE Gelände, mit einer Bodenplatte über den ganzen Grundriss: gross, flach, unten. "
         "Die Formregel hält sie für Gelände; der Grundriss der Hülle bleibt, nur die Unterkante steigt "
         "um die Plattendicke.", b)

    b = _Bau()
    b.quader("Fundamentplatte", (-9, -0.4, -8), (9, 0.0, 8))
    b.haus(-6, -5, 12, 10, 9)
    fall("befund-fundament-mit-ueberstand", "befund",
         "Haus OHNE Gelände auf einer Fundamentplatte mit 3 m Überstand: die Formregel trennt sie ab, "
         "die Hülle verliert den Überstand.", b)

    b = _Bau()
    b.quader("Boden_UG2", (-20, -6.4, -15), (20, -6.0, 15))
    b.quader("Waende_UG", (-20, -6.0, -15), (20, 0.0, 15))
    b.quader("Decke_ueber_UG", (-20, 0.0, -15), (20, 0.4, 15))
    b.haus(-6, -5, 12, 10, 6, y=0.4)
    fall("befund-tiefgarage-mit-bodenplatte", "befund",
         "Tiefgarage OHNE Gelände, die unterste Bodenplatte ist ein eigener Knoten: die Formregel hält "
         "sie für Gelände (die Decke darüber bleibt nicht entscheidbar). Der Grundriss der Hülle bleibt.", b)

    return faelle


def schreibe_glb(js: dict, pfad: Path) -> None:
    """Eine glb nur aus dem JSON-Kopf (ohne Binärblock): genug für die Hüllbox."""
    block = json.dumps(js, separators=(",", ":")).encode("utf-8")
    block += b" " * (-len(block) % 4)
    pfad.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(block))
                     + struct.pack("<II", len(block), 0x4E4F534A) + block)


def _bauwerksbox(js: dict) -> dict:
    from aiimaging import glbbox
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "probe.glb"
        schreibe_glb(js, p)
        return glbbox.bauwerksbox(p)


def rechne(js: dict, aus: dict | None = None) -> dict:
    """Was der Kern (``glbbox.bauwerksbox``) aus diesem Kopf macht, als ``erwartet``."""
    aus = _bauwerksbox(js) if aus is None else aus
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    if not all(math.isfinite(v) for e in box for v in e):
        # A0289, Befund am Heim-PC: Tragen Form-Gelände und Bauteile denselben Namen, bleibt dort
        # kein Bauteil übrig und die Box ist nicht endlich. In JSON steht dafür `null`.
        box = None
    return _erwartet(aus, box)


def _erwartet(aus: dict, box) -> dict:
    return {"huellbox": None if box is None else [[round(v, 6) for v in e] for e in box],
            "szenenbox": [[round(v, 6) for v in e] for e in aus["bbox_szene"]],
            "bauteile": aus["n_knoten"],
            "gelaendeKnoten": aus["n_gelaende"],
            "abgetrennt": aus["bbox_bauwerk"] is not None and aus["n_gelaende"] > 0,
            "entschieden_durch": aus["entschieden_durch"]}


#: Der Grund, aus dem der Mac in einem Formfall nur «nicht entscheidbar» sagt (A0289, Fertig-Satz 3).
GRUND_NAMENSGLEICH = (
    "Ein Bauteil trägt denselben Namen wie ein Körper, den die Form für Gelände hält. Der Heim-PC "
    "trennt nach diesen Namen und nähme das Bauteil mit heraus; der Mac behält die Szenenhülle.")


def namensgleich(js: dict) -> bool:
    """Trägt ein Körper, den die Form NICHT für Gelände hält, den Namen eines Form-Geländes?

    Unabhängig von ``bauwerksbox`` nachgerechnet, unmittelbar an ``gelaendeform``.
    """
    from aiimaging import gelaendeform, glbbox
    alle = glbbox.knotenboxen(js)["knoten"]
    try:
        befund = gelaendeform.gelaende_knoten(alle, hoch=1)
    except gelaendeform.GelaendeformError:
        return False
    namen = {u["name"] for u in befund["urteile"] if u["urteil"] == gelaendeform.GELAENDE}
    andere = {u["name"] for u in befund["urteile"] if u["urteil"] != gelaendeform.GELAENDE}
    return bool(namen & andere)


def rechne_form(js: dict) -> dict:
    """``erwartet`` (Heim-PC) und ``mac`` (was der Mac liefern muss) für einen Formfall.

    ``form_gefragt``, ``form_gelaende`` und ``form_unklar`` sagen, ob ``bauwerksbox`` die
    Zweitmeinung gefragt hat und was sie fand (``form_befund``).
    """
    aus = _bauwerksbox(js)
    erwartet = rechne(js, aus)
    befund = aus.get("form_befund")
    erwartet["form_gefragt"] = befund is not None
    erwartet["form_gelaende"] = len((befund or {}).get("gelaende") or ())
    erwartet["form_unklar"] = len((befund or {}).get("unklar") or ())
    if erwartet["entschieden_durch"] == "form" and namensgleich(js):
        mac = {"gleich": False, "urteil": "nicht entscheidbar", "grund": GRUND_NAMENSGLEICH,
               "huellbox": erwartet["szenenbox"], "abgetrennt": False, "gelaendeKnoten": 0,
               "entschieden_durch": "keine"}
    else:
        mac = {"gleich": True, "huellbox": erwartet["huellbox"], "abgetrennt": erwartet["abgetrennt"],
               "gelaendeKnoten": erwartet["gelaendeKnoten"],
               "entschieden_durch": erwartet["entschieden_durch"]}
    return {"erwartet": erwartet, "mac": mac}


def erzeuge() -> dict:
    faelle = []
    for d in definitionen():
        faelle.append({"fall": d["fall"], "sagt": d["sagt"], "glb": d["glb"], "erwartet": rechne(d["glb"])})
    formfaelle = []
    for d in formdefinitionen():
        formfaelle.append({"fall": d["fall"], "gruppe": d["gruppe"], "sagt": d["sagt"], "glb": d["glb"],
                           **rechne_form(d["glb"])})
    return {"schema": "visbox.glbbox-gelaenderegel/v1",
            "hinweis": "Synthetisch, mit tools/glbbox_proben.py erzeugt. Python (tests/"
                       "test_glbbox_gelaenderegel_gemeinsam.py) und Swift (GlbauskunftGelaendeTests) "
                       "lesen diese Datei und verlangen dieselbe Box.",
            "toleranz_m": 0.01, "faelle": faelle,
            "hinweis_form": "A0289: Gelände ohne erkennbaren Namen. `erwartet` ist die Entscheidung des "
                            "Heim-PC (glbbox.bauwerksbox mit der Zweitmeinung gelaendeform), `mac` das, "
                            "was der Mac liefern muss (tests/test_glbbox_formregel_gemeinsam.py, "
                            "GelaendeformTests).",
            "formfaelle": formfaelle}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    neu = json.dumps(erzeuge(), indent=1, ensure_ascii=False) + "\n"
    if "--schreiben" in argv:
        ZIEL.parent.mkdir(parents=True, exist_ok=True)
        ZIEL.write_text(neu, encoding="utf-8")
        print(f"geschrieben: {ZIEL}")
        return 0
    if not ZIEL.exists() or ZIEL.read_text(encoding="utf-8") != neu:
        print("Die Probendatei passt nicht zum Kern: python tools/glbbox_proben.py --schreiben")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
