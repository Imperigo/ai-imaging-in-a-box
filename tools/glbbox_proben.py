"""Die gemeinsame Probendatei der Geländeregel: Python und Swift prüfen dieselbe Box.

A0267. Die Geländeregel für die Hüllbox einer glb steht am Heim-PC in ``aiimaging.glbbox``
(``maske.ist_gelaende``); der Mac rechnet sie in ``Glbauskunft`` (Swift) für das nach, was
aus den Namen im JSON-Kopf lesbar ist. Zwei Rechnungen laufen auseinander, sobald niemand sie
nebeneinanderlegt. Darum gibt es EINE Datei (``tests/daten/glbbox_gelaenderegel.json``):

* jeder Fall trägt den JSON-Kopf einer synthetischen glb (im Repo erzeugt, keine echten Daten);
* ``erwartet`` ist, was ``glbbox.bauwerksbox`` daraus macht (Python-Probe: stimmt es noch?);
* die Swift-Probe (``GlbauskunftGelaendeTests``) liest dieselbe Datei und verlangt dieselbe Box.

**Die Formfälle (A0289, «Gelände an der Form», Runde 2).** Unter ``formfaelle`` stehen Modelle
OHNE erkennbaren Geländenamen, jeder Körper mit seinen Dreiecken. Dort entscheidet am Heim-PC die
Zweitmeinung (``aiimaging.gelaendeform``, über ``glbbox.bauwerksbox``): Die Hüllbox macht einen
Körper zum Kandidaten, Gelände wird er nur mit dem Beweis an seiner Oberseite. Der Mac bildet das in
``Kern/Gelaendeform.swift`` ab und muss in JEDEM Fall dasselbe liefern wie ``erwartet``. Die Gruppen:
``gegenfall`` (alles ist gebaut, nichts darf abgetrennt werden), ``gelaende`` (echtes Gelände;
``eben`` markiert ebene, waagrechte Flächen, die auch ein Bauteil sein könnten), ``schwelle`` (Reihen
quer über jede Schwelle der Regel), ``namen`` (Namensregel und Form zusammen). ``wahrheit`` nennt
die Körper, die wirklich Gelände sind.

Neu erzeugen: ``python tools/glbbox_proben.py --schreiben``. Ohne Schalter wird nur geprüft, ob die
Datei zum Stand des Kerns passt (Ausgang 1, wenn nicht).
"""
from __future__ import annotations

import base64
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
    """Ein glTF-Kopf aus Körpern MIT Dreiecken, für die Formfälle (A0289, Runde 2).

    Jeder Körper trägt seine Ecken und Dreiecke in einem ``data:``-Puffer im Kopf: Die Formregel
    entscheidet seit Runde 2 an der Oberseite, und die steht nur in den Dreiecken. ``gelaende``
    merkt sich, welche Knoten in Wahrheit Gelände sind (die Wahrheit des Falls, nicht das Urteil).
    """

    def __init__(self):
        self.knoten, self.netze, self.zugriffe, self.sichten = [], [], [], []
        self.roh = bytearray()
        self.gelaende: set[int] = set()

    # ------------------------------------------------------------ Rohdaten
    def _sicht(self, daten: bytes, schritt=None) -> int:
        self.roh += b"\0" * (-len(self.roh) % 4)
        sicht = {"buffer": 0, "byteOffset": len(self.roh), "byteLength": len(daten)}
        if schritt:
            sicht["byteStride"] = schritt
        self.roh += daten
        self.sichten.append(sicht)
        return len(self.sichten) - 1

    def _primitiv(self, ecken, dreiecke, index="H", schritt=None, ohne_ecken=False) -> dict:
        """Ein Primitiv; ``ecken`` werden auf 32 Bit gerundet, ``min``/``max`` aus den gerundeten."""
        rund = [struct.unpack("<fff", struct.pack("<fff", *e)) for e in ecken]
        lo = [min(e[i] for e in rund) for i in range(3)]
        hi = [max(e[i] for e in rund) for i in range(3)]
        zugriff = {"componentType": 5126, "count": len(rund), "type": "VEC3", "min": lo, "max": hi}
        prim = {"attributes": {"POSITION": len(self.zugriffe)}}
        if ohne_ecken:
            self.zugriffe.append(zugriff)
            return prim
        folge = [i for d in dreiecke for i in d]
        if index is None:
            # Ohne Indexliste: die Ecken stehen dreiecksweise hintereinander.
            rund = [rund[i] for i in folge]
            zugriff["count"] = len(rund)
        if schritt:
            daten = b"".join(struct.pack("<fff", *e) + b"\0" * (schritt - 12) for e in rund)
        else:
            daten = b"".join(struct.pack("<fff", *e) for e in rund)
        zugriff["bufferView"] = self._sicht(daten, schritt)
        self.zugriffe.append(zugriff)
        if index is not None:
            art = {"B": 5121, "H": 5123, "I": 5125}[index]
            sicht = self._sicht(struct.pack("<" + index * len(folge), *folge))
            self.zugriffe.append({"componentType": art, "count": len(folge), "type": "SCALAR",
                                  "bufferView": sicht})
            prim["indices"] = len(self.zugriffe) - 1
        return prim

    def netz(self, name, ecken, dreiecke, *, gelaende=False, index="H", schritt=None,
             ohne_ecken=False, **extra) -> int:
        """Ein Mesh-Knoten aus Ecken und Dreiecken (Umlaufsinn gegen den Uhrzeiger von aussen)."""
        self.netze.append({"primitives": [self._primitiv(ecken, dreiecke, index, schritt, ohne_ecken)]})
        k = {"mesh": len(self.netze) - 1, **extra}
        if name is not None:
            k = {"name": name, **k}
        self.knoten.append(k)
        if gelaende:
            self.gelaende.add(len(self.knoten) - 1)
        return len(self.knoten) - 1

    # ------------------------------------------------------------ Bauteile
    @staticmethod
    def _quader_netz(lo, hi):
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        e = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
             (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
        d = [(4, 7, 6), (4, 6, 5),            # oben (+Y)
             (0, 1, 2), (0, 2, 3),            # unten
             (0, 4, 5), (0, 5, 1),            # -Z
             (3, 2, 6), (3, 6, 7),            # +Z
             (0, 3, 7), (0, 7, 4),            # -X
             (1, 5, 6), (1, 6, 2)]            # +X
        return e, d

    def quader(self, name, lo, hi, **extra) -> int:
        """Ein Quader ``lo``..``hi`` (glTF, Y oben) mit zwölf Dreiecken; liefert den Knotenindex."""
        e, d = self._quader_netz(lo, hi)
        return self.netz(name, e, d, **extra)

    def zwei_teile(self, name, teil_a, teil_b, **extra) -> int:
        """Ein Mesh-Knoten mit ZWEI Primitiven: die Box ist die Hülle über beide."""
        prims = [self._primitiv(*self._quader_netz(lo, hi)) for lo, hi in (teil_a, teil_b)]
        self.netze.append({"primitives": prims})
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

    def geschosse(self, x, z, breite, tiefe, anzahl, y=0.0, hoehe=3.0, stamm="Geschoss", namen=True):
        """``anzahl`` Geschosse übereinander, je ein Quader."""
        return [self.quader(f"{stamm}_{i + 1}" if namen else None,
                            (x, y + i * hoehe, z), (x + breite, y + (i + 1) * hoehe, z + tiefe))
                for i in range(anzahl)]

    def satteldach(self, name, x0, z0, x1, z1, traufe, first, boden=None, **extra) -> int:
        """Ein Satteldach als Körper (First längs X). ``boden``: Unterkante eines Hauses aus einem
        Stück (Wände bis zur Traufe); ohne ``boden`` nur der Dachkörper ab der Traufe."""
        zm = (z0 + z1) / 2
        yb = traufe if boden is None else boden
        e = [(x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1),
             (x0, traufe, z0), (x1, traufe, z0), (x1, traufe, z1), (x0, traufe, z1),
             (x0, first, zm), (x1, first, zm)]
        d = [(4, 8, 9), (4, 9, 5),            # Dachfläche -Z
             (7, 6, 9), (7, 9, 8),            # Dachfläche +Z
             (4, 7, 8), (5, 9, 6),            # Giebel
             (0, 1, 2), (0, 2, 3)]            # unten
        if boden is not None:
            d += [(0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2)]
        return self.netz(name, e, d, **extra)

    def platte_schraeg(self, name, x0, z0, x1, z1, y_a, y_b, dicke, **extra) -> int:
        """Eine ebene Platte, längs X von ``y_a`` nach ``y_b`` geneigt: Rampe, Pultdach, ebener Hang."""
        e = [(x0, y_a - dicke, z0), (x1, y_b - dicke, z0), (x1, y_b - dicke, z1), (x0, y_a - dicke, z1),
             (x0, y_a, z0), (x1, y_b, z0), (x1, y_b, z1), (x0, y_a, z1)]
        return self.netz(name, e, self._quader_netz((0, 0, 0), (1, 1, 1))[1], **extra)

    # ------------------------------------------------------------ Gelände
    def flaeche(self, name, x0, z0, x1, z1, nx, nz, hoehe, *, boden=None, loch=None,
                gelaende=True, zs=None, **extra) -> int:
        """Eine Fläche als Höhenfeld ``hoehe(x, z)`` über einem Raster ``nx`` x ``nz``.

        ``boden``: Höhe einer ebenen Unterseite; dann ist es ein geschlossener Körper mit Rand.
        ``loch(i, j)``: wahr für Rasterfelder, die fehlen (ohne ``boden``).
        ``zs``: eigene Rasterlinien längs Z (für eine Stufe in einem schmalen Feld).
        """
        xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
        if zs is None:
            zs = [z0 + (z1 - z0) * j / nz for j in range(nz + 1)]
        nz = len(zs) - 1
        e = [(x, hoehe(x, z), z) for z in zs for x in xs]
        nr = lambda i, j: j * (nx + 1) + i      # noqa: E731
        d = []
        for j in range(nz):
            for i in range(nx):
                if loch is not None and loch(i, j):
                    continue
                d += [(nr(i, j), nr(i, j + 1), nr(i + 1, j + 1)), (nr(i, j), nr(i + 1, j + 1), nr(i + 1, j))]
        if boden is not None:
            n0 = len(e)
            e += [(x, boden, z) for z in zs for x in xs]
            u = lambda i, j: n0 + nr(i, j)      # noqa: E731
            d += [(u(0, 0), u(nx, nz), u(0, nz)), (u(0, 0), u(nx, 0), u(nx, nz))]
            for i in range(nx):                 # Ränder bei z0 und z1
                d += [(u(i, 0), nr(i, 0), nr(i + 1, 0)), (u(i, 0), nr(i + 1, 0), u(i + 1, 0))]
                d += [(u(i, nz), nr(i + 1, nz), nr(i, nz)), (u(i, nz), u(i + 1, nz), nr(i + 1, nz))]
            for j in range(nz):                 # Ränder bei x0 und x1
                d += [(u(0, j), nr(0, j + 1), nr(0, j)), (u(0, j), u(0, j + 1), nr(0, j + 1))]
                d += [(u(nx, j), nr(nx, j), nr(nx, j + 1)), (u(nx, j), nr(nx, j + 1), u(nx, j + 1))]
        if len(e) > 65535 and extra.get("index", "H") == "H":
            extra["index"] = "I"
        return self.netz(name, e, d, gelaende=gelaende, **extra)

    def kopf(self, wurzeln=None, **zusatz) -> dict:
        kinder = {k for n in self.knoten for k in n.get("children", [])}
        if wurzeln is None:
            wurzeln = [i for i in range(len(self.knoten)) if i not in kinder]
        js = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": list(wurzeln)}],
              "nodes": self.knoten, "meshes": self.netze, "accessors": self.zugriffe}
        if self.roh:
            js["bufferViews"] = self.sichten
            js["buffers"] = [{"byteLength": len(self.roh),
                              "uri": "data:application/octet-stream;base64,"
                                     + base64.b64encode(bytes(self.roh)).decode("ascii")}]
        js.update(zusatz)
        return js


def _ecken_und_dreiecke(bau: "_Bau"):
    """Ecken und Dreiecke des ersten Netzes eines Hilfsbaus (16-Bit-Indexliste), zum Anhängen."""
    js = bau.kopf()
    roh = base64.b64decode(js["buffers"][0]["uri"].split(";base64,", 1)[1])
    prim = js["meshes"][0]["primitives"][0]
    ze, zi = js["accessors"][prim["attributes"]["POSITION"]], js["accessors"][prim["indices"]]
    se, si = js["bufferViews"][ze["bufferView"]], js["bufferViews"][zi["bufferView"]]
    ecken = [struct.unpack_from("<fff", roh, se["byteOffset"] + 12 * i) for i in range(ze["count"])]
    folge = struct.unpack_from("<" + "H" * zi["count"], roh, si["byteOffset"])
    return ecken, [tuple(folge[i:i + 3]) for i in range(0, len(folge), 3)]


def _viertel(winkel_grad: float) -> list[float]:
    """Quaternion (x, y, z, w) einer Drehung um die glTF-Z-Achse: ein geneigter Hang."""
    halb = math.radians(winkel_grad) / 2.0
    return [0.0, 0.0, round(math.sin(halb), 9), round(math.cos(halb), 9)]


def _wellen(amplitude, wx=7.0, wz=9.0):
    """Ein unebener Boden: überlagerte Wellen, damit kein Rasterfeld dem anderen gleicht."""
    return lambda x, z: amplitude * (math.sin(x / wx) + math.cos(z / wz) + 0.5 * math.sin((x + z) / 5.0))


def _hang(steigung, laengs="z", uneben=0.3, sockel=0.0):
    """Ein Hang mit ``steigung`` (Höhe je Länge) und leichter Unebenheit."""
    welle = _wellen(uneben)
    if laengs == "z":
        return lambda x, z: sockel + steigung * z + welle(x, z)
    return lambda x, z: sockel + steigung * x + welle(x, z)


def formdefinitionen() -> list[dict]:
    """Die Formfälle von A0289, Runde 2: Modelle OHNE erkennbaren Geländenamen.

    Vier Gruppen:

    * ``gegenfall``: alles ist gebaut. NICHTS darf abgetrennt werden, die Hülle ist die Szene.
      Familien: Tiefgarage, Sockel, Halle, Bodenplatte, Namen (namenlos und gleichnamig), dazu
      eigene gemeine Fälle (Dach, Vordach, Rampe, Haus aus einem Stück).
    * ``gelaende``: echtes Gelände ohne Namen. ``eben`` markiert die ebenen, waagrechten Flächen,
      die auch ein Bauteil sein könnten: dort ist «nicht entscheidbar» die richtige Antwort.
    * ``schwelle``: Reihen in kleinen Schritten quer über jede Schwelle der Regel.
    * ``namen``: Namensregel und Form zusammen.

    ``wahrheit`` nennt je Fall die Stellen (in der Reihenfolge von ``glbbox.knotenboxen``), die in
    Wahrheit Gelände sind. Zahlen sind, wo es geht, exakt in 32 Bit darstellbar.
    """
    faelle: list[dict] = []

    def fall(name, gruppe, familie, sagt, b, **mehr):
        js = b.kopf(**mehr.pop("kopf", {}))
        eintrag = {"fall": name, "gruppe": gruppe, "familie": familie, "sagt": sagt}
        eintrag.update(mehr)
        eintrag["wahrheit_knoten"] = sorted(b.gelaende)
        eintrag["glb"] = js
        faelle.append(eintrag)

    # ================================================================ GEGENFÄLLE
    # ---------------------------------------------------------------- G1 Tiefgarage
    for geschosse in range(1, 11):
        for ug in (1, 2):
            b = _Bau()
            breite, tiefe = 40 + 2 * geschosse, 30 + 2 * geschosse
            tief = -3.0 * ug
            if geschosse % 2:
                b.quader("Waende_UG", (-breite / 2, tief, -tiefe / 2), (breite / 2, 0.0, tiefe / 2))
            else:
                # Die Aussenwände als vier einzelne Körper: ein Ring, keine Fläche.
                w = 0.25
                b.quader("Wand_UG_N", (-breite / 2, tief, -tiefe / 2), (breite / 2, 0.0, -tiefe / 2 + w))
                b.quader("Wand_UG_S", (-breite / 2, tief, tiefe / 2 - w), (breite / 2, 0.0, tiefe / 2))
                b.quader("Wand_UG_W", (-breite / 2, tief, -tiefe / 2), (-breite / 2 + w, 0.0, tiefe / 2))
                b.quader("Wand_UG_O", (breite / 2 - w, tief, -tiefe / 2), (breite / 2, 0.0, tiefe / 2))
            if ug == 2:
                b.quader("Decke_UG2", (-breite / 2, -3.25, -tiefe / 2), (breite / 2, -3.0, tiefe / 2))
            b.quader("Bodenplatte_UG", (-breite / 2, tief - 0.5, -tiefe / 2), (breite / 2, tief, tiefe / 2))
            b.quader("Decke_ueber_UG", (-breite / 2, 0.0, -tiefe / 2), (breite / 2, 0.5, tiefe / 2))
            b.geschosse(-6, -5, 12, 10, geschosse, y=0.5)
            fall(f"gegen-tiefgarage-{geschosse:02d}-geschosse-{ug}-ug", "gegenfall", "tiefgarage",
                 f"Tiefgarage {breite} x {tiefe} m mit {ug} Untergeschoss(en), darauf ein Haus 12 x 10 m "
                 f"mit {geschosse} Geschoss(en). Wände, Decke und Bodenplatte der Garage sind gebaut.", b)

    # ---------------------------------------------------------------- G2 Sockel
    for sockel in (1, 2, 3):
        for art, (hx, hz, hb, ht) in (("turm", (-6, -5, 12, 10)), ("zeile", (-20, -5, 40, 10))):
            for nr, hoch in enumerate((5, 8, 16) if art == "turm" else (3, 5, 7)):
                b = _Bau()
                if nr == 1:
                    b.geschosse(-25, -20, 50, 40, sockel, hoehe=4.0, stamm="Sockelgeschoss")
                else:
                    b.quader("Sockel", (-25 - 5 * nr, 0, -20), (25 + 5 * nr, 4.0 * sockel, 20))
                b.geschosse(hx, hz, hb, ht, hoch, y=4.0 * sockel)
                fall(f"gegen-sockel-{sockel}-geschosse-{art}-{hoch:02d}", "gegenfall", "sockel",
                     f"Sockel mit {sockel} Geschoss(en) unter {'einem Turm' if art == 'turm' else 'einer Zeile'} "
                     f"mit {hoch} Geschossen.", b)

    # ---------------------------------------------------------------- G5 Halle
    for hoehe in (4, 6, 8, 10, 12):
        b = _Bau()
        b.quader("Halle", (-30, 0, -25), (30, hoehe, 25))
        b.quader("Kamin", (10, 0, 10), (12, 25, 12))
        fall(f"gegen-halle-{hoehe:02d}-m-kamin", "gegenfall", "halle",
             f"Flache Halle 60 x 50 x {hoehe} m mit Kamin 2 x 2 x 25 m, kein Gelände.", b)

        b = _Bau()
        b.quader("Halle", (-30, 0, -25), (30, hoehe, 25))
        b.quader("Silo", (34, 0, -3), (40, 30, 3))
        fall(f"gegen-halle-{hoehe:02d}-m-silo", "gegenfall", "halle",
             f"Flache Halle 60 x 50 x {hoehe} m, daneben ein Silo 6 x 6 x 30 m.", b)

        b = _Bau()
        b.quader("Halle", (-30, 0, -25), (30, hoehe, 25))
        b.quader("Dachaufbau", (-4, hoehe, -4), (4, hoehe + 3, 4))
        b.quader("Antenne", (0, hoehe + 3, 0), (0.5, hoehe + 30, 0.5))
        fall(f"gegen-halle-{hoehe:02d}-m-dachaufbau", "gegenfall", "halle",
             f"Flache Halle {hoehe} m mit Dachaufbau und Antenne.", b)

        b = _Bau()
        b.satteldach("Halle", -30, -25, 30, 25, traufe=hoehe, first=hoehe + 2.5, boden=0.0)
        b.quader("Kamin", (10, 0, 10), (12, 30, 12))
        fall(f"gegen-halle-{hoehe:02d}-m-aus-einem-stueck-satteldach", "gegenfall", "halle",
             f"Halle aus EINEM Stück mit Satteldach (Traufe {hoehe} m) und Kamin: die Oberseite ist "
             f"geneigt, aber sie beginnt an der Traufe.", b)

        b = _Bau()
        b.quader("Waende", (-30, 0, -25), (30, hoehe, 25))
        b.satteldach("Dach", -31, -26, 31, 26, traufe=hoehe, first=hoehe + 2.0)
        b.quader("Kamin", (10, 0, 10), (12, 40, 12))
        fall(f"gegen-halle-{hoehe:02d}-m-dach-als-eigener-koerper", "gegenfall", "halle",
             f"Halle {hoehe} m, das Satteldach ist ein eigener Körper über den Wänden.", b)

    # ---------------------------------------------------------------- G10 Bodenplatte
    for nr, ueber in enumerate((0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)):
        for hb, ht, hh in ((12, 10, 9), (24, 14, 18)):
            b = _Bau()
            b.quader("Bodenplatte_EG", (-hb / 2 - ueber, -0.25, -ht / 2 - ueber),
                     (hb / 2 + ueber, 0.0, ht / 2 + ueber))
            b.haus(-hb / 2, -ht / 2, hb, ht, hh)
            if nr % 3 == 2:
                b.quader("Vordach", (-hb / 2, 3.0, ht / 2), (hb / 2, 3.25, ht / 2 + 2))
            fall(f"gegen-bodenplatte-ueberstand-{int(ueber * 10):02d}-dm-haus-{hb}", "gegenfall", "bodenplatte",
                 f"Haus {hb} x {ht} m ohne Gelände auf einer Bodenplatte mit {ueber} m Überstand.", b)
    for gefaelle in (0.01, 0.02, 0.03):
        b = _Bau()
        b.platte_schraeg("Bodenplatte_im_Gefaelle", -16, -14, 16, 14, 0.0, 32 * gefaelle, 0.25)
        b.haus(-6, -5, 12, 10, 12, y=32 * gefaelle)
        fall(f"gegen-bodenplatte-im-gefaelle-{int(gefaelle * 100)}-prozent", "gegenfall", "bodenplatte",
             f"Bodenplatte mit 10 m Überstand und {gefaelle:.0%} Gefälle: gebaut, nicht gewachsen.", b)

    # ---------------------------------------------------------------- Befund 1: namenlos, gleichnamig
    for name, kurz in ((None, "namenlos"), ("Mesh", "gleichnamig"), ("", "leerer-name")):
        b = _Bau()
        b.quader(name, (-30, -0.5, -25), (30, 0.0, 25))
        for lo, hi in (((-6, 0, -5), (6, 3, 5)), ((-6, 3, -5), (6, 6, 5)), ((-6, 6, -5), (6, 9, 5))):
            b.quader(name, lo, hi)
        fall(f"gegen-{kurz}-platte-unter-haus", "gegenfall", "namen",
             f"Alle Körper {kurz}: eine ebene Platte 60 x 50 m unter einem Haus. Eben und waagrecht: "
             f"nicht entscheidbar, die Hülle bleibt die Szene und ist endlich.", b, eben=True)

        b = _Bau()
        b.quader(name, (-25, 0, -20), (25, 4, 20))
        b.quader(name, (-6, 4, -5), (6, 28, 5))
        fall(f"gegen-{kurz}-sockel-unter-turm", "gegenfall", "namen",
             f"Alle Körper {kurz}: Sockelgeschoss unter einem Turm.", b)

        b = _Bau()
        b.quader(name, (-30, 0, -25), (30, 6, 25))
        b.quader(name, (10, 0, 10), (12, 25, 12))
        fall(f"gegen-{kurz}-halle-mit-kamin", "gegenfall", "namen",
             f"Alle Körper {kurz}: Halle mit Kamin.", b)

    # ---------------------------------------------------------------- eigene gemeine Gegenfälle
    b = _Bau()
    b.haus(-6, -5, 12, 10, 9)
    b.quader("Anbau", (6, 0, -5), (10, 3, 0))
    fall("gegen-haus-ohne-gelaende", "gegenfall", "gemein",
         "Ein Haus mit Anbau, kein Gelände, keine Bodenplatte als eigener Knoten.", b)

    b = _Bau()
    b.haus(-6, -5, 12, 10, 9)
    b.quader("Flachdach", (-8, 9.0, -7), (8, 9.25, 7))
    fall("gegen-flachdach-mit-ueberstand", "gegenfall", "gemein",
         "Ein Flachdach mit Überstand: gross und flach, aber ganz oben.", b)

    b = _Bau()
    b.quader("Halle", (-20, 0, -10), (20, 6, 10))
    fall("gegen-ein-einziger-koerper", "gegenfall", "gemein", "Ein einziger Körper: nichts zu trennen.", b)

    b = _Bau()
    b.netz("Scheibe_A", [(-10, 0, 0), (10, 0, 0), (10, 0, 8), (-10, 0, 8)], [(0, 3, 2), (0, 2, 1)])
    b.netz("Scheibe_B", [(-10, 0, 8), (10, 0, 8), (10, 0, 16), (-10, 0, 16)], [(0, 3, 2), (0, 2, 1)])
    fall("gegen-szene-ohne-hoehe", "gegenfall", "gemein",
         "Eine Szene ohne Höhe (zwei flache Scheiben): die Form sagt über sie nichts.", b)

    b = _Bau()
    b.quader("Zwischendecke", (-10, 4.0, -8), (10, 4.25, 8))
    b.quader("Stuetzen", (-10, 0.0, -8), (10, 4.0, 8))
    b.quader("Obergeschoss", (-10, 4.25, -8), (10, 9.0, 8))
    fall("gegen-zwischendecke-auf-halber-hoehe", "gegenfall", "gemein",
         "Eine Geschossdecke über den ganzen Grundriss auf 47 % der Höhe.", b)

    for neigung in (0.08, 0.15, 0.3):
        b = _Bau()
        for i, (x, z) in enumerate(((-29, -24), (28, -24), (-29, 23), (28, 23))):
            b.quader(f"Stuetze_{i + 1}", (x, 0, z), (x + 1, 4, z + 1))
        b.platte_schraeg("Vordach", -30, -25, 30, 25, 4.25, 4.25 + 60 * neigung, 0.25)
        b.quader("Turm", (34, 0, -5), (44, 90, 5))
        fall(f"gegen-vordach-auf-stuetzen-{int(neigung * 100):02d}-prozent", "gegenfall", "gemein",
             f"Ein grosses Pultdach ({neigung:.0%}) auf vier Stützen neben einem Turm: geneigt, dünn, tief "
             f"im Höhenbereich der Szene, aber von den Stützen unterspannt und eine einzige Ebene.", b)

    for neigung in (0.08, 0.12, 0.2):
        b = _Bau()
        b.platte_schraeg("Rampe", -30, -10, 10, 10, 0.25, 0.25 + 40 * neigung, 0.25)
        b.quader("Parkhaus", (10, 0, -10), (30, 40, 10))
        fall(f"gegen-rampe-{int(neigung * 100):02d}-prozent", "gegenfall", "gemein",
             f"Eine Rampe 40 x 20 m ({neigung:.0%}) vor einem Parkhaus: eine geneigte Ebene, gebaut.", b)

    for traufe in (0.5, 2.5):
        b = _Bau()
        b.quader("Waende", (-30, 0, -25), (30, 3, 25))
        b.quader("Bodenplatte", (-30, -0.25, -25), (30, 0, 25))
        e, d = [], []
        # Ein Tonnendach in zwölf Streifen: viele Richtungen, aber über Wänden und Bodenplatte.
        n = 12
        for i in range(n + 1):
            z = -25 + 50 * i / n
            y = 3 + traufe + 4 * math.sin(math.pi * i / n)
            e += [(-30, y, z), (30, y, z)]
        for i in range(n):
            a = 2 * i
            d += [(a, a + 2, a + 3), (a, a + 3, a + 1)]
        b.netz("Tonnendach", e, d)
        b.quader("Turm", (40, 0, -5), (50, 60, 5))
        fall(f"gegen-tonnendach-traufe-{int(traufe * 10):02d}-dm", "gegenfall", "gemein",
             "Ein Tonnendach als offene Schale über einer Halle, daneben ein Turm: uneben und geneigt, "
             "aber unterbaut.", b)

    b = _Bau()
    b.quader("Zaun_und_Mauer", (-30, 0, -25), (30, 1.5, 25), ohne_ecken=True)
    b.haus(-6, -5, 12, 10, 9)
    fall("gegen-koerper-ohne-lesbare-dreiecke", "gegenfall", "gemein",
         "Ein grosser flacher Körper, dessen Dreiecke nicht in der Datei lesbar sind: nicht geraten.", b)

    b = _Bau()
    w = 0.25
    ring_e, ring_d = [], []
    for lo, hi in (((-30, 0, -25), (30, 2, -25 + w)), ((-30, 0, 25 - w), (30, 2, 25)),
                   ((-30, 0, -25), (-30 + w, 2, 25)), ((30 - w, 0, -25), (30, 2, 25))):
        e, d = _Bau._quader_netz(lo, hi)
        ring_d += [tuple(i + len(ring_e) for i in dd) for dd in d]
        ring_e += e
    b.netz("Umfassungsmauer", ring_e, ring_d)
    b.haus(-6, -5, 12, 10, 9)
    fall("gegen-mauerring-um-das-haus", "gegenfall", "gemein",
         "Eine Umfassungsmauer als EIN Körper: grosse Box, fast keine Oberseite.", b)

    for nr, (bx, bz) in enumerate(((60, 50), (100, 100), (200, 150))):
        b = _Bau()
        gel = _Bau()
        h = _hang(0.06, "z")
        gel.flaeche("x", -bx / 2, -bz / 2, bx / 2, bz / 2, 12, 10, h)
        e, d = _ecken_und_dreiecke(gel)
        he, hd = _Bau._quader_netz((-6, h(0, 0) - 0.5, -5), (6, h(0, 0) + 9, 5))
        b.netz("Mesh", e + he, d + [tuple(i + len(e) for i in dd) for dd in hd])
        b.quader("Nebenbau", (bx / 2 - 10, h(0, bz / 2 - 8), bz / 2 - 8), (bx / 2 - 2, h(0, bz / 2 - 8) + 3, bz / 2 - 2))
        b.quader("Mast", (-bx / 2, 0, -bz / 2), (-bx / 2 + 0.5, 60, -bz / 2 + 0.5))
        fall(f"gegen-gelaende-und-haus-in-einem-netz-{bx}-x-{bz}", "gegenfall", "gemein",
             f"EIN Netz trägt das Gelände {bx} x {bz} m UND das Haus; daneben ein Nebenbau. Wer das Netz "
             f"abtrennt, entfernt das Haus mit: die Hauswände im Inneren verraten es.", b)

    # ================================================================ ECHTES GELÄNDE
    def mit_haus(b, y=0.0, x=-6, z=-5):
        b.haus(x, z, 12, 10, 12, y=y)

    # ---------------------------------------------------------------- Hang
    for steigung in (0.06, 0.1, 0.15, 0.2, 0.3):
        for laengs in ("z", "x"):
            for koerper in (False, True):
                b = _Bau()
                h = _hang(steigung, laengs)
                # Streuung über die Grundstücksgrösse: längs Z ein Grundstück 40 x 30 m, längs X 60 x 50 m.
                bx, bz = (20, 15) if laengs == "z" else (30, 25)
                tief = min(h(x, z) for x in (-bx, bx) for z in (-bz, bz)) - 1.0
                b.flaeche("Flaeche" if koerper else "Mesh.001", -bx, -bz, bx, bz, 12, 10, h,
                          boden=tief if koerper else None)
                mit_haus(b, y=h(0, 0) - 0.5)
                fall(f"gelaende-hang-{int(steigung * 100):02d}-prozent-laengs-{laengs}-"
                     f"{'koerper' if koerper else 'flaeche'}", "gelaende", "hang",
                     f"Hang mit {steigung:.0%} längs {laengs.upper()} auf {2 * bx} x {2 * bz} m, leicht uneben, als "
                     f"{'geschlossener Körper mit ebenem Boden und Rand' if koerper else 'offene Fläche'}; "
                     f"das Haus steht im Hang.", b)

    # ---------------------------------------------------------------- Mulde
    for tiefe in (2.0, 3.0, 4.0):
        for koerper in (False, True):
            b = _Bau()
            h = lambda x, z, t=tiefe: -t * math.exp(-(x * x + z * z) / 900.0) + _wellen(0.25)(x, z)  # noqa: E731
            b.flaeche("Objekt_3", -40, -40, 40, 40, 14, 14, h, boden=-tiefe - 1.25 if koerper else None)
            mit_haus(b, y=h(0, 0) - 0.25)
            fall(f"gelaende-mulde-{int(tiefe)}-m-{'koerper' if koerper else 'flaeche'}", "gelaende", "mulde",
                 f"Mulde 80 x 80 m, {tiefe} m tief, das Haus steht darin.", b)

    # ---------------------------------------------------------------- Terrassen
    for stufen in (2, 3, 4):
        b = _Bau()
        def h(x, z, n=stufen):      # noqa: E306
            lage = (z + 30) / 60 * n
            stufe = min(int(lage), n - 1)
            rest = lage - stufe
            return 1.5 * stufe + 1.5 * min(rest / 0.6, 1.0) + 0.1 * math.sin(x / 7.0) * (1 + stufe)
        b.flaeche("Aussenraum", -25, -30, 25, 30, 10, 12 * stufen, h)
        mit_haus(b, y=h(0, 0) - 0.25)
        fall(f"gelaende-terrassen-{stufen}-stufen-ein-netz", "gelaende", "terrasse",
             f"Geländeterrassen in {stufen} Stufen mit Böschungen dazwischen, ein Netz.", b)
    for stufen in (2, 3):
        b = _Bau()
        for i in range(stufen):
            z0 = -30 + 60 * i / stufen
            nr = b.quader(f"Stufe_{i + 1}", (-25, 0, z0), (25, 0.5 + 1.0 * i, z0 + 60 / stufen))
            b.gelaende.add(nr)
        mit_haus(b, y=0.5 + 1.0 * (stufen - 1), z=10)
        fall(f"gelaende-terrassen-{stufen}-ebene-platten", "gelaende", "terrasse",
             f"{stufen} Geländestufen als ebene, waagrechte Platten: an der Form Gelände oder Bauteil, "
             f"nicht entscheidbar.", b, eben=True)

    # ---------------------------------------------------------------- uneben, grösser als das Haus
    for nr, (bx, bz, amp) in enumerate(((60, 50, 0.6), (100, 100, 1.0), (200, 150, 2.0), (40, 36, 0.5),
                                        (120, 60, 1.5), (80, 80, 0.8))):
        b = _Bau()
        h = _wellen(amp, wx=bx / 9.0, wz=bz / 8.0)
        b.flaeche("Object", -bx / 2, -bz / 2, bx / 2, bz / 2, 12, 12, h)
        mit_haus(b, y=h(0, 0) - 0.5)
        if nr % 2:
            b.haus(-bx / 2 + 4, -bz / 2 + 4, 10, 8, 9, y=h(-bx / 2 + 9, -bz / 2 + 8) - 0.5, stamm="Nebenbau")
        fall(f"gelaende-uneben-{bx}-x-{bz}", "gelaende", "uneben",
             f"Unebenes Gelände {bx} x {bz} m, viel grösser als das Haus"
             f"{' und ein Nebenbau' if nr % 2 else ''}.", b)

    # ---------------------------------------------------------------- unter dem Haus, mit Keller
    for keller in (3.0, 6.0, 9.0):
        b = _Bau()
        h = _hang(0.1, "x")
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h)
        b.quader("Keller", (-6, h(-6, 0) - keller, -5), (6, h(0, 0) - 0.5, 5))
        mit_haus(b, y=h(0, 0) - 0.5)
        fall(f"gelaende-unter-dem-haus-keller-{int(keller)}-m", "gelaende", "unter-dem-haus",
             f"Hang unter dem Haus, der Keller reicht {keller} m tiefer als das Gelände: ein Keller unter "
             f"einem Haus unterspannt nur dessen Grundriss.", b)

    # ---------------------------------------------------------------- neben dem Haus
    for abstand in (0, 4):
        b = _Bau()
        h = _hang(0.1, "z")
        b.flaeche("Objekt_7", -40, -20, 0, 20, 10, 10, h)
        b.haus(abstand, -5, 12, 10, 16, y=h(0, 0))
        fall(f"gelaende-neben-dem-haus-abstand-{abstand}", "gelaende", "neben-dem-haus",
             "Das Gelände liegt NEBEN dem Haus (Vorplatz am Hang 40 x 40 m).", b)

    # ---------------------------------------------------------------- Kacheln
    b = _Bau()
    h = _hang(0.12, "z")
    for i, (x, z) in enumerate([(-30, -30), (0, -30), (-30, 0), (0, 0)]):
        b.flaeche(f"Feld_{i + 1}", x, z, x + 30, z + 30, 6, 6, h)
    mit_haus(b, y=h(0, 0) - 0.5)
    fall("gelaende-vier-kacheln", "gelaende", "kacheln",
         "Gelände in vier Kacheln, jede 25 % des Grundrisses: alle vier werden abgetrennt.", b)

    b = _Bau()
    for i in range(9):
        x, z = -30 + 20 * (i % 3), -30 + 20 * (i // 3)
        b.flaeche(f"Feld_{i + 1}", x, z, x + 20, z + 20, 4, 4, h)
    mit_haus(b, y=h(0, 0) - 0.5)
    fall("gelaende-neun-kacheln-zu-klein", "gelaende", "kacheln",
         "Gelände in neun Kacheln, jede 11 % des Grundrisses: je Knoten zu klein, die Form trennt nichts "
         "(Korngrösse).", b)

    # ---------------------------------------------------------------- eben und waagrecht
    for nr, (lo, hi, sagt) in enumerate((
            ((-30, -0.5, -25), (30, 0.0, 25), "Ebene Platte 60 x 50 m unter dem Haus"),
            ((-40, -0.5, -20), (0, 0.0, 20), "Ebene Platte 40 x 40 m neben dem Haus"),
            ((-100, -1.0, -100), (100, 0.0, 100), "Ebene Platte 200 x 200 m unter dem Haus"),
            ((-7, -0.25, -6), (7, 0.0, 6), "Sehr kleines ebenes Gelände 14 x 12 m unter dem Haus"),
            ((-30, -10.0, -25), (30, -9.5, 25), "Ebene Platte tief unter der Nulllinie, ein Keller darauf"))):
        b = _Bau()
        b.gelaende.add(b.quader("Mesh.001", lo, hi))
        if nr == 4:
            b.quader("Keller", (-5, -9.5, -5), (5, 0.0, 5))
        b.haus(2 if nr == 1 else -6, -5, 12, 10, 9)
        fall(f"gelaende-eben-waagrecht-{nr + 1}", "gelaende", "eben",
             sagt + ": an der Form Gelände oder Bodenplatte, nicht entscheidbar.", b, eben=True)

    # ---------------------------------------------------------------- namenlos und gleichnamig
    for name, kurz in ((None, "namenlos"), ("Mesh", "gleichnamig"), ("", "leerer-name")):
        b = _Bau()
        h = _hang(0.1, "z")
        b.flaeche(name, -30, -25, 30, 25, 12, 10, h)
        for i in range(3):
            b.quader(name, (-6, h(0, 0) - 0.5 + 3 * i, -5), (6, h(0, 0) + 2.5 + 3 * i, 5))
        fall(f"gelaende-{kurz}-hang-und-haus", "gelaende", "namen",
             f"Alle Körper {kurz}, das Gelände ist ein Hang: abgetrennt wird nach der Stelle, das Haus "
             f"bleibt ganz.", b)
    b = _Bau()
    h = _hang(0.15, "z")
    b.flaeche("Platte", -30, -25, 0, 25, 6, 10, h)
    b.flaeche("Platte", 0, -25, 30, 25, 6, 10, h)
    mit_haus(b, y=h(0, 0) - 0.5)
    fall("gelaende-zwei-haelften-gleicher-name", "gelaende", "namen",
         "Zwei Geländehälften tragen denselben Namen: beide werden abgetrennt.", b)

    # ---------------------------------------------------------------- Knotenbaum
    b = _Bau()
    h = _hang(0.1, "z")
    b.flaeche("Flaeche", -0.5, -0.5, 0.5, 0.5, 12, 10, lambda x, z: h(60 * x, 50 * z) / 2.0,
              translation=[0.0, -0.25, 0.0], scale=[60.0, 2.0, 50.0])
    teile = b.haus(0, 0, 12, 10, 12)
    b.gruppe("Gebaeude", teile, translation=[-6.0, 0.0, -5.0])
    fall("gelaende-skalierter-knoten", "gelaende", "knotenbaum",
         "Das Gelände ist ein Einheitsnetz mit Skalierung am Knoten, das Haus hängt an einem "
         "verschobenen Elternknoten.", b)

    b = _Bau()
    m = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 100, 2, -50, 1]
    b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h, matrix=m)
    teile = b.haus(-6, -5, 12, 10, 12)
    b.gruppe("Gebaeude", teile, matrix=m)
    fall("gelaende-matrix-am-knoten", "gelaende", "knotenbaum",
         "Gelände und Haus tragen eine Matrix (spaltenweise gespeichert) mit Verschiebung.", b)

    b = _Bau()
    platte = b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h)
    innen = b.gruppe("Umgebung_innen", [platte], translation=[10.0, 0.0, 0.0])
    b.gruppe("Umgebung", [innen], translation=[0.0, -1.0, 5.0])
    teile = b.haus(-6, -5, 12, 10, 12)
    b.gruppe("Gebaeude", teile, rotation=[0.0, 0.70710678, 0.0, 0.70710678])
    fall("gelaende-verschachtelt-und-gedreht", "gelaende", "knotenbaum",
         "Das Gelände hängt zwei Ebenen tief, das Haus ist am Elternknoten um 90 Grad gedreht.", b)

    b = _Bau()
    b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h, scale=[-1.0, 1.0, 1.0])
    mit_haus(b, y=h(0, 0) - 0.5)
    fall("gelaende-gespiegelter-knoten", "gelaende", "knotenbaum",
         "Das Gelände hängt an einem gespiegelten Knoten (Skalierung -1): der Umlaufsinn dreht sich, "
         "die Oberseite bleibt oben.", b)

    b = _Bau()
    b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, lambda x, z: 0.3 * _wellen(1.0)(x, z),
              rotation=_viertel(6.0))
    mit_haus(b, y=0.5)
    fall("gelaende-am-knoten-geneigt", "gelaende", "knotenbaum",
         "Ein unebenes Netz, am Knoten um 6 Grad geneigt: die Ecken werden einzeln gedreht.", b)

    b = _Bau()
    fremd = b.quader("Nachbarblock", (-500, 0, -500), (500, 80, 500))
    platte = b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h)
    teile = b.haus(-6, -5, 12, 10, 12)
    fall("gelaende-zweite-szene-aktiv", "gelaende", "knotenbaum",
         "Zwei Szenen, die zweite ist aktiv: der Block der ersten zählt nicht mit.", b,
         kopf={"scenes": [{"nodes": [fremd]}, {"nodes": [platte, *teile]}], "scene": 1})

    # ---------------------------------------------------------------- Speicherformen
    for kurz, zusatz, sagt in (
            ("index-32-bit", {"index": "I"}, "Indexliste in 32 Bit"),
            ("ohne-indexliste", {"index": None}, "ohne Indexliste, die Ecken stehen dreiecksweise"),
            ("ecken-mit-schrittweite", {"schritt": 16}, "Ecken mit Schrittweite 16 Byte")):
        b = _Bau()
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h, **zusatz)
        mit_haus(b, y=h(0, 0) - 0.5)
        fall(f"gelaende-speicher-{kurz}", "gelaende", "speicher", f"Das Gelände ist gespeichert {sagt}.", b)
    b = _Bau()
    b.flaeche("Flaeche", -3, -2.5, 3, 2.5, 6, 5, lambda x, z: 0.15 * z + 0.05 * math.sin(3 * x) * (1 + 0.3 * z), index="B")
    b.quader("Modellhaus", (-0.6, 0, -0.5), (0.6, 1.2, 0.5))
    fall("gelaende-speicher-index-8-bit", "gelaende", "speicher",
         "Ein kleines Modell (6 x 5 m), Indexliste in 8 Bit.", b)
    for nr in (1, 2):
        b = _Bau()
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, _hang(0.05 * nr, "z"))
        mit_haus(b, y=-0.5)
        fall(f"gelaende-speicher-binaerblock-{nr}", "gelaende", "speicher",
             "Die Dreiecke stehen im Binärblock der glb statt im Kopf, wie in jeder echten Datei.", b,
             binaerblock=True)

    # ================================================================ SCHWELLEN
    def reihe(schwelle, werte, bauen, sagt):
        for w in werte:
            b = _Bau()
            bauen(b, w)
            fall(f"schwelle-{schwelle}-{w:g}".replace(".", "_"), "schwelle", schwelle, sagt.format(w=w), b)

    hang10 = _hang(0.1, "z")

    def grundriss(b, w):
        # Gelände 20 x 25 m (500 m2), die Szene wird über einen fernen Pfosten gestreckt.
        b.flaeche("Flaeche", 0, 0, 20, 25, 8, 10, _hang(0.1, "z", uneben=0.2))
        b.haus(4, 5, 12, 10, 12, y=0.5)
        breite = 500.0 / w / 25.0
        b.quader("Pfosten", (breite - 0.25, 0, 0), (breite, 3, 0.25))
    reihe("grundrissanteil", (0.2, 0.23, 0.245, 0.25, 0.255, 0.27, 0.3), grundriss,
          "Gelände mit {w} des Grundrisses der Szene; die Schwelle gilt ab 0,25.")

    def flachheit(b, w):
        # Die höchste Ecke liegt genau bei 40 w (x = 20, z = 20), die tiefste Kante bei 0.
        b.flaeche("Flaeche", -20, -20, 20, 20, 10, 10,
                  lambda x, z: 40 * w * (z + 20) / 40 * (1 - 0.05 * (1 - math.cos((x - 20) / 3.0)) / 2))
        b.haus(-5, -5, 10, 10, 100, y=20 * w)
    reihe("flachheit", (0.15, 0.2, 0.26, 0.28, 0.29, 0.295, 0.3, 0.305, 0.31, 0.32, 0.36), flachheit,
          "Hang 40 x 40 m mit Höhe {w} der Kante: Kandidat bis 0,30.")

    def tieflage(b, w):
        # Oberkante des Geländes bei 4 m, die Szene ist 4 / w hoch.
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10,
                  lambda x, z: 4.0 * (z + 25) / 50 * (1 - 0.3 * (1 - math.cos((x - 30) / 5)) / 2))
        b.haus(-6, -5, 12, 10, 4.0 / w - 2.0, y=2.0)
    reihe("tieflage", (0.3, 0.4, 0.5, 0.55, 0.58, 0.59, 0.595, 0.605, 0.61, 0.62, 0.7), tieflage,
          "Die Oberkante des Hangs sitzt bei {w} der Szenenhöhe: Gelände bis 0,60, darüber «zu hoch».")

    def neigung(b, w):
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10,
                  lambda x, z: w * z + 0.06 * math.sin(x / 3.0) + 0.03 * math.sin(z / 2.0))
        b.haus(-6, -5, 12, 10, 30, y=0.0)
    reihe("neigung", (0.01, 0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.07), neigung,
          "Gelände mit etwa {w} Gefälle: unter 4 % kann es eine Platte im Gefälle sein.")

    def geneigt_anteil(b, w):
        # Ein Anteil w der Fläche ist Hang, der Rest ein ebenes Plateau.
        grenze = -25 + 50 * w
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 50,
                  lambda x, z: (0.2 * (z - grenze) * (1 + 0.1 * math.sin(x / 3.0))) if z < grenze - 1e-9 else 0.0)
        b.haus(-6, 12, 12, 10, 30, y=0.0)
    reihe("geneigt-anteil", (0.3, 0.4, 0.46, 0.48, 0.5, 0.52, 0.54, 0.6, 0.7), geneigt_anteil,
          "{w} der Oberseite sind Hang, der Rest ein ebenes Plateau: verlangt ist die Hälfte.")

    def deckung(b, w):
        # Von 40 Reihen fehlen w auf drei Vierteln der Breite (ein L): die Oberseite deckt
        # 1 - 0,75 w / 40 des Grundrisses ihrer Hüllbox.
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 40, _hang(0.1, "x"),
                  loch=lambda i, j: i >= 3 and j < w)
        b.haus(-27, 15, 12, 8, 30, y=-2.0)
    reihe("deckung", (20, 24, 25, 26, 27, 28, 30, 32), deckung,
          "Von 40 Reihen fehlen {w} auf drei Vierteln der Breite; die Oberseite deckt 1 - 0,75 x {w} / 40 "
          "des Grundrisses ihrer Hüllbox, verlangt ist die Hälfte (27 Reihen sind knapp zu viel).")

    def sockel(b, w):
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10,
                  lambda x, z: 0.1 * (z + 25) + 0.5 * abs(math.sin(x / 6.0)) * (z + 25) / 50
                  + 0.2 * math.sin(z / 3.0) ** 2 * (z + 25) / 50, boden=-w)
        b.haus(-6, -5, 12, 10, 40, y=2.0)
    reihe("sockel", (0.5, 1.0, 1.25, 1.45, 1.5, 1.55, 1.75, 2.0, 3.0), sockel,
          "Geländekörper mit {w} m Sockel unter der tiefsten Stelle der Oberseite: bis 1,5 m.")

    def lagen(b, w):
        # Über dem Gelände liegt ein zweites, kleineres Höhenfeld im selben Körper: zusammen
        # decken beide den Grundriss w mal.
        h = _hang(0.1, "z")
        nr = b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, h)
        breite = 60.0 * (w - 1.0)
        if breite > 0:
            zwei = _Bau()
            zwei.flaeche("x", -30, -25, -30 + breite, 25, 6, 10, lambda x, z: h(x, z) + 0.5)
            b.netze[b.knoten[nr]["mesh"]]["primitives"].append(
                b._primitiv(*_ecken_und_dreiecke(zwei)))
        b.haus(-6, -5, 12, 10, 40, y=0.0)
    reihe("lagen", (1.0, 1.1, 1.2, 1.24, 1.26, 1.3, 1.5, 2.0), lagen,
          "Die Oberseite deckt den Grundriss {w} mal: bis 1,25 mal ist es ein Höhenfeld.")

    def wand(b, w):
        # Eine Stützmauer mitten im Gelände: in einem 5 cm breiten Feld springt die Höhe um w.
        zs = [-25, -20, -15, -10, -5, 0, 0.0625, 5, 10, 15, 20, 25]
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 0, zs=zs,
                  hoehe=lambda x, z: 0.0625 * (z + 25) * (1 + 0.1 * math.sin(x / 4.0)) + (w if z > 0.03 else 0.0))
        b.haus(-6, 6, 12, 10, 40, y=3.0)
    reihe("wand", (0.5, 1.0, 1.5, 1.75, 1.875, 2.0, 2.125, 2.25, 2.5, 3.0), wand,
          "Eine Stützmauer von etwa {w} m mitten im Geländenetz: über 2 m kann es eine Hauswand sein.")

    def unterbaut(b, w):
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, hang10)
        tief = hang10(0, -25) - 3.0
        # Zwei Schächte reichen tiefer; ihre Hülle spannt den Anteil w des Grundrisses auf.
        breite = 60.0 * w
        b.quader("Schacht_A", (-30, tief, -25), (-29, tief + 2, 25))
        b.quader("Schacht_B", (-30 + breite - 1, tief, -25), (-30 + breite, tief + 2, 25))
        b.haus(-6, -5, 12, 10, 30, y=0.0)
    reihe("unterbaut", (0.15, 0.2, 0.24, 0.245, 0.25, 0.255, 0.26, 0.3, 0.5), unterbaut,
          "Tiefer reichende Körper unterspannen {w} des Grundrisses: bis 25 %.")

    def unterbaut_tiefe(b, w):
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10,
                  lambda x, z: (0.1 + 0.02 * math.sin(x / 5.0) + 0.02 * math.cos(z / 4.0)) * (z + 25))
        b.quader("Fundament", (-30, -w, -25), (30, 0.0, 25))
        b.haus(-6, -5, 12, 10, 30, y=0.0)
    reihe("unterbaut-tiefe", (0.0, 0.05, 0.09, 0.125, 0.15, 0.25, 1.0), unterbaut_tiefe,
          "Ein Körper unter dem ganzen Gelände reicht {w} m tiefer: ab mehr als 0,1 m zählt er.")

    def richtungen(b, w):
        # Streifen längs X, jeder eine Ebene mit eigenem Quergefälle: genau w Richtungen.
        n = int(w)
        e, d = [], []
        for i in range(n):
            z0, z1 = -25 + 50 * i / n, -25 + 50 * (i + 1) / n
            quer = 0.012 * i
            k = len(e)
            e += [(-30, 0.1 * z0, z0), (30, 0.1 * z0 + 60 * quer, z0),
                  (30, 0.1 * z1 + 60 * quer, z1), (-30, 0.1 * z1, z1)]
            d += [(k, k + 3, k + 2), (k, k + 2, k + 1)]
        b.netz("Flaeche", e, d, gelaende=True)
        b.haus(-6, -5, 12, 10, 60, y=0.0)
    reihe("richtungen", (1, 2, 3, 4, 5, 6, 7, 9, 12), richtungen,
          "Die Oberseite besteht aus {w} Ebene(n): verlangt sind sechs Richtungen.")

    def richtungen_eng(b, w):
        # Sechs Ebenen, deren Quergefälle sich um w unterscheidet: unter 1 % fallen zwei in ein Feld.
        e, d = [], []
        for i in range(6):
            z0, z1 = -25 + 50 * i / 6, -25 + 50 * (i + 1) / 6
            k = len(e)
            e += [(-30, 0.1 * z0, z0), (30, 0.1 * z0 + 60 * w * i, z0),
                  (30, 0.1 * z1 + 60 * w * i, z1), (-30, 0.1 * z1, z1)]
            d += [(k, k + 3, k + 2), (k, k + 2, k + 1)]
        b.netz("Flaeche", e, d, gelaende=True)
        b.haus(-6, -5, 12, 10, 60, y=0.0)
    reihe("richtungen-abstand", (0.004, 0.006, 0.008, 0.009, 0.011, 0.012, 0.016), richtungen_eng,
          "Sechs Ebenen im Abstand von {w} Quergefälle: gezählt wird in Feldern von 1 %.")

    def steil(b, w):
        # Böschungen mit Neigung w auf 60 % der Fläche.
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 20,
                  lambda x, z: (w * ((z + 25) % 5.0) if (z + 25) % 10.0 < 5.0 else w * (10.0 - (z + 25) % 10.0))
                  * (1 + 0.03 * math.sin(x / 4.0)) * 0.2)
        b.haus(-6, -5, 12, 10, 60, y=0.0)
    reihe("steil", (2.0, 4.0, 4.6, 4.8, 5.2, 5.4, 6.0, 8.0), steil,
          "Wälle mit Kennzahl {w} (Neigung ein Fünftel davon): über 100 % Neigung ist es Wand.")

    # ================================================================ NAMEN UND FORM
    b = _Bau()
    b.flaeche("Terrain_Rest", 29, -25, 30, 25, 1, 10, hang10)
    b.flaeche("Flaeche", -30, -25, 29, 25, 12, 10, hang10)
    mit_haus(b, y=hang10(0, 0) - 0.5)
    fall("namen-fanden-zu-wenig", "namen", "namen",
         "Die Namensregel findet einen Randstreifen, das grosse Gelände ohne Namen bleibt. Die Form "
         "ergänzt die Namen nicht: es bleibt bei der Namensentscheidung.", b)

    b = _Bau()
    b.flaeche("Terrain_Aussen", -60, -50, 60, 50, 12, 10, hang10)
    b.flaeche("Flaeche", -12, -10, 12, 10, 6, 5, hang10)
    mit_haus(b, y=hang10(0, 0) - 0.5)
    fall("namen-fanden-genug", "namen", "namen",
         "Die Namensregel trennt das grosse Gelände, die Rahmung wird deutlich enger: die Form wird "
         "nicht gefragt.", b)

    for anteil in (0.03, 0.042, 0.048, 0.052, 0.058, 0.08):
        b = _Bau()
        # Ein Geländestreifen MIT Namen am Rand: ohne ihn wird die Diagonale um `anteil` kürzer.
        b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, hang10)
        diagonale = math.sqrt(60.0 * 60.0 + 50.0 * 50.0) / (1 - anteil)
        mehr = math.sqrt(diagonale * diagonale - 2500.0) - 60.0
        b.flaeche("Terrain_Streifen", 30, -25, 30 + mehr, 25, 2, 10, hang10)
        mit_haus(b, y=hang10(0, 0) - 0.5)
        fall(f"namen-schrumpfung-{int(anteil * 1000):03d}-promille", "namen", "schrumpfung",
             f"Die Namensregel macht die Rahmung um {anteil:.1%} enger: unter 5 % wird die Form gefragt "
             "(und ergänzt nicht), darüber nicht.", b)

    return faelle


def schreibe_glb(js: dict, pfad: Path, binaerblock: bool = False) -> None:
    """Eine glb aus dem JSON-Kopf. Die Dreiecke stehen als ``data:``-Puffer im Kopf; mit
    ``binaerblock`` wandert Puffer 0 stattdessen in den Binärblock der glb (wie in echten Dateien)."""
    anhang = b""
    if binaerblock:
        js = json.loads(json.dumps(js))
        roh = base64.b64decode(js["buffers"][0].pop("uri").split(";base64,", 1)[1])
        roh += b"\0" * (-len(roh) % 4)
        anhang = struct.pack("<II", len(roh), 0x004E4942) + roh
    block = json.dumps(js, separators=(",", ":")).encode("utf-8")
    block += b" " * (-len(block) % 4)
    pfad.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(block) + len(anhang))
                     + struct.pack("<II", len(block), 0x4E4F534A) + block + anhang)


def _bauwerksbox(js: dict, binaerblock: bool = False) -> dict:
    from aiimaging import glbbox
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "probe.glb"
        schreibe_glb(js, p, binaerblock)
        return glbbox.bauwerksbox(p)


def rechne(js: dict, aus: dict | None = None) -> dict:
    """Was der Kern (``glbbox.bauwerksbox``) aus diesem Kopf macht, als ``erwartet``."""
    aus = _bauwerksbox(js) if aus is None else aus
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    return {"huellbox": [[round(v, 6) for v in e] for e in box],
            "szenenbox": [[round(v, 6) for v in e] for e in aus["bbox_szene"]],
            "bauteile": aus["n_knoten"],
            "gelaendeKnoten": aus["n_gelaende"],
            "abgetrennt": aus["bbox_bauwerk"] is not None and aus["n_gelaende"] > 0,
            "entschieden_durch": aus["entschieden_durch"]}


def stellen(js: dict, knoten) -> list[int]:
    """Knotenindizes → Stellen in der Reihenfolge von ``glbbox.knotenboxen`` (nur die aktive Szene)."""
    from aiimaging import glbbox
    folge = [h[0] for h in glbbox.knotenboxen(js)["herkunft"]]
    return sorted(folge.index(k) for k in knoten if k in folge)


def rechne_form(js: dict, binaerblock: bool = False) -> dict:
    """``erwartet`` für einen Formfall: die Entscheidung des Kerns samt dem, was die Form fand.

    ``form_gefragt``: ``bauwerksbox`` hat die Zweitmeinung gefragt. ``form_gelaende`` und
    ``form_unklar``: wie viele Körper sie für Gelände hielt und wie viele «nicht entscheidbar»
    blieben; ``form_gruende`` nennt je unklarem Körper das Kurzwort des Grundes.
    ``gelaende_stellen``: welche Körper abgetrennt wurden (leer, wenn nichts abgetrennt ist).
    """
    aus = _bauwerksbox(js, binaerblock)
    erwartet = rechne(js, aus)
    befund = aus.get("form_befund")
    erwartet["form_gefragt"] = befund is not None
    erwartet["form_gelaende"] = len((befund or {}).get("gelaende_stellen") or ())
    erwartet["form_unklar"] = len((befund or {}).get("unklar_stellen") or ())
    erwartet["form_gruende"] = list((befund or {}).get("gruende") or ())
    if aus["entschieden_durch"] == "form":
        erwartet["gelaende_stellen"] = list(befund["gelaende_stellen"])
    elif aus["entschieden_durch"] == "name" and erwartet["abgetrennt"]:
        from aiimaging import glbbox, maske
        erwartet["gelaende_stellen"] = [i for i, k in enumerate(glbbox.knotenboxen(js)["knoten"])
                                        if maske.ist_gelaende(k[0])]
    else:
        erwartet["gelaende_stellen"] = []
    return erwartet


def erzeuge() -> dict:
    faelle = []
    for d in definitionen():
        faelle.append({"fall": d["fall"], "sagt": d["sagt"], "glb": d["glb"], "erwartet": rechne(d["glb"])})
    formfaelle = []
    for d in formdefinitionen():
        d = dict(d)
        js = d.pop("glb")
        d["wahrheit"] = {"gelaende_stellen": stellen(js, d.pop("wahrheit_knoten"))}
        d["glb"] = js
        d["erwartet"] = rechne_form(js, bool(d.get("binaerblock")))
        formfaelle.append(d)
    return {"schema": "visbox.glbbox-gelaenderegel/v2",
            "hinweis": "Synthetisch, mit tools/glbbox_proben.py erzeugt. Python (tests/"
                       "test_glbbox_gelaenderegel_gemeinsam.py) und Swift (GlbauskunftGelaendeTests) "
                       "lesen diese Datei und verlangen dieselbe Box.",
            "toleranz_m": 0.01, "faelle": faelle,
            "hinweis_form": "A0289, Runde 2: Modelle ohne erkennbaren Geländenamen, jeder Körper mit "
                            "seinen Dreiecken. `erwartet` ist die Entscheidung des Heim-PC "
                            "(glbbox.bauwerksbox mit der Zweitmeinung gelaendeform); der Mac muss in "
                            "JEDEM Fall dasselbe liefern (GelaendeformTests). `wahrheit` nennt die "
                            "Körper, die wirklich Gelände sind. `binaerblock`: Puffer 0 wandert vor dem "
                            "Lesen aus dem Kopf in den Binärblock der glb.",
            "formfaelle": formfaelle}


def schreibe_text(daten: dict) -> str:
    """Die Probendatei als Text: lesbar eingerückt, aber jeder glb-Kopf auf EINER Zeile (die Köpfe
    tragen die Dreiecke und wären eingerückt Hunderttausende Zeilen)."""
    koepfe = []

    def ersetzt(fall):
        fall = dict(fall)
        koepfe.append(json.dumps(fall["glb"], separators=(",", ":"), ensure_ascii=False))
        fall["glb"] = f"@@GLB{len(koepfe) - 1}@@"
        return fall

    flach = dict(daten, faelle=[ersetzt(f) for f in daten["faelle"]],
                 formfaelle=[ersetzt(f) for f in daten["formfaelle"]])
    text = json.dumps(flach, indent=1, ensure_ascii=False)
    for i, k in enumerate(koepfe):
        text = text.replace(f'"@@GLB{i}@@"', k, 1)
    return text + "\n"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    neu = schreibe_text(erzeuge())
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
