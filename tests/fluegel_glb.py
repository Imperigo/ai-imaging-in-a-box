"""Fälle des Satzes «Flügel bleiben ein Haus» als echte glb-Dateien (A0301, Runde 3).

**Wozu:** Die Gruppierung bekommt im Produkt ihre Boxen und Grundrisse nicht von Hand, sondern aus
:func:`aiimaging.umfeld.lies_glb_umfeld` (Knoten, Lage, Drehung, Dreiecke) und ruft sie in
:func:`aiimaging.umfeld.plane` auf. Diese Datei schreibt einen Fall als glb, damit die Proben genau diesen Weg
fahren: je Bauteil ein Knoten mit einem geschlossenen Netz (ein Prisma je konvexem Stück seines Grundrisses),
wahlweise mit der Drehung im Knoten statt in den Ecken, dazu ein Gelände.

**Regel 3:** frei erfunden; die Dateien entstehen im Prüflauf und liegen nie im Repo.
"""
from __future__ import annotations

import json
import math
import struct


def _prisma(stueck, z0: float, z1: float, basis: int):
    """Ein konvexes Stück ``[(x, y), …]`` (Welt, gegen den Uhrzeigersinn) als geschlossenes Prisma: Ecken in
    glTF-Koordinaten (Y oben: ``(x, z, -y)``) und Dreiecke, aussen gegen den Uhrzeigersinn gewickelt."""
    n = len(stueck)
    ecken = [(x, z0, -y) for x, y in stueck] + [(x, z1, -y) for x, y in stueck]
    dreiecke = []
    for k in range(1, n - 1):
        dreiecke.append((basis + n, basis + n + k, basis + n + k + 1))          # Dach (nach oben)
        dreiecke.append((basis, basis + k + 1, basis + k))                      # Boden (nach unten)
    for k in range(n):
        a, b = basis + k, basis + (k + 1) % n
        dreiecke += [(a, b, b + n), (a, b + n, a + n)]                           # Wände
    return ecken, dreiecke


def _drehung_y(grad: float):
    """Das Quaternion einer Drehung um die glTF-Hochachse Y; in der Welt (Z oben) dreht es um ``grad`` gegen den
    Uhrzeigersinn (glTF ``(x, y, z)`` → Welt ``(x, -z, y)``)."""
    w = math.radians(grad) / 2
    return [0.0, math.sin(w), 0.0, math.cos(w)]


def schreibe(pfad, teile, *, gelaende=True) -> list[str]:
    """Eine glb aus ``teile = [(name, stuecke, z0, z1, drehung_grad, mitte), …]``: ``stuecke`` sind konvexe
    Vielecke in Weltkoordinaten VOR der Drehung; ``drehung_grad`` (oder 0) steht im Knoten und dreht um ``mitte``
    (die Knotenverschiebung). Mit ``gelaende`` kommt ein flaches Gelände 2 km × 2 km dazu (Knoten «Gelaende»).

    Returns:
        die Namen der Bauteilknoten in der Reihenfolge der Datei.
    """
    knoten, netze, accessoren, sichten = [], [], [], []
    daten = bytearray()

    def puffer(roh: bytes, ziel=None) -> int:
        while len(daten) % 4:
            daten.append(0)
        start = len(daten)
        daten.extend(roh)
        sicht = {"buffer": 0, "byteOffset": start, "byteLength": len(roh)}
        if ziel:
            sicht["target"] = ziel
        sichten.append(sicht)
        return len(sichten) - 1

    def netz(stuecke, z0, z1, versatz):
        ecken, dreiecke = [], []
        for st in stuecke:
            lokal = [(x - versatz[0], y - versatz[1]) for x, y in st]
            e, d = _prisma(lokal, z0, z1, len(ecken))
            ecken += e
            dreiecke += d
        pos = struct.pack(f"<{3 * len(ecken)}f", *[v for e in ecken for v in e])
        idx = struct.pack(f"<{3 * len(dreiecke)}I", *[i for d in dreiecke for i in d])
        accessoren.append({"bufferView": puffer(pos, 34962), "componentType": 5126, "count": len(ecken), "type": "VEC3",
                           "min": [min(e[k] for e in ecken) for k in range(3)],
                           "max": [max(e[k] for e in ecken) for k in range(3)]})
        accessoren.append({"bufferView": puffer(idx, 34963), "componentType": 5125, "count": 3 * len(dreiecke),
                           "type": "SCALAR"})
        netze.append({"primitives": [{"attributes": {"POSITION": len(accessoren) - 2}, "indices": len(accessoren) - 1}]})
        return len(netze) - 1

    namen = []
    for name, stuecke, z0, z1, grad, mitte in teile:
        mitte = mitte or (0.0, 0.0)
        k = {"name": name, "mesh": netz(stuecke, z0, z1, mitte), "translation": [mitte[0], 0.0, -mitte[1]]}
        if grad:
            k["rotation"] = _drehung_y(grad)
        knoten.append(k)
        namen.append(name)
    if gelaende:
        knoten.append({"name": "Gelaende", "mesh": netz([[(-1000, -1000), (1000, -1000), (1000, 1000), (-1000, 1000)]],
                                                       -1.0, 0.0, (0.0, 0.0))})
    js = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": list(range(len(knoten)))}],
          "nodes": knoten, "meshes": netze, "accessors": accessoren, "bufferViews": sichten,
          "buffers": [{"byteLength": len(daten)}]}
    roh_js = json.dumps(js).encode("utf-8")
    roh_js += b" " * (-len(roh_js) % 4)
    while len(daten) % 4:
        daten.append(0)
    gesamt = 12 + 8 + len(roh_js) + 8 + len(daten)
    with open(pfad, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, gesamt))
        f.write(struct.pack("<II", len(roh_js), 0x4E4F534A) + roh_js)
        f.write(struct.pack("<II", len(daten), 0x004E4942) + bytes(daten))
    return namen


def ueber_den_aufrufweg(pfad, *, mit_grundrissen: bool = True) -> dict:
    """Die Gruppierung so, wie das Produkt sie rechnet: :func:`lies_glb_umfeld`, dann :func:`plane` im
    Situationsmodell. ``mit_grundrissen=False`` gibt dieselben Boxen ohne Grundrisse (der Aufruf bis Runde 2).

    Returns:
        ``{namen, boxen, grundrisse, gruppen, mehrdeutig}``: ``gruppen`` als Listen von Indizes in ``namen``.
    """
    from aiimaging import umfeld
    gelesen = umfeld.lies_glb_umfeld(pfad)
    grundrisse = gelesen["bauwerk_grundrisse"] if mit_grundrissen else None
    plan = umfeld.plane(gelaende=gelesen["gelaende"], bauwerk_boxen=gelesen["bauwerk_boxen"],
                        haupt_box=gelesen["haupt_box"], kameras=(), kategorien=["baeume"], dichte="wenig",
                        situation=True, bauwerk_grundrisse=grundrisse)
    return {"boxen": gelesen["bauwerk_boxen"], "grundrisse": gelesen["bauwerk_grundrisse"],
            "gruppen": plan["bauten"]["gruppen"], "mehrdeutig": plan["bauten"]["mehrdeutig"]}
