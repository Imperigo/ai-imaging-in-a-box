#!/usr/bin/env python3
"""Erzeugt eine synthetische **glb** — benannte Quader, sonst nichts.

Warum dieses Skript existiert
-----------------------------
Regel 3 verbietet echte Projektdaten im Repo und verlangt, dass Testdaten **im Repo
erzeugbar** sind. :mod:`aiimaging.glbbox` liest glb-Dateien; ohne einen Erzeuger liesse
sich das nur an einer echten Bauherrschafts-Datei prüfen, und genau das ist verboten.

Der Umweg über ``tools/make_test_ifc.py`` + ``.venv-ifc`` täte es auch — aber er braucht
ein GPL-behaftetes Environment für eine Datei aus vier Quadern. Dieses Skript kommt mit
**reiner stdlib** aus, wie sein IFC-Geschwister und aus demselben Grund.

Was es bewusst NICHT tut
------------------------
Es erzeugt keine Normalen, keine Texturen und keine Hierarchie. Die Frage, für die es
gebaut ist, lautet: *Welche Knoten heissen wie, und wo liegen sie?* Alles andere wäre
Ballast, den eine Prüfung mitschleppen müsste.

**Zwei Ausnahmen, seit dem 02.09.2026** — beide für :mod:`aiimaging.modellstand`, beide
abschaltbar und aus, solange niemand sie bestellt:

* ``materialien`` — ein ``materials``-Block und ein Verweis darauf je Primitiv. Ohne ihn
  gäbe es keine Gegenprobe zu «eine glb ohne Materialblock liegt zurück»: Eine Regel, die
  nur den Mangelfall kennt, beanstandet alles.
* ``vermerk`` — der Herkunftsvermerk in ``asset.extras.kosmo_modellstand``, mit dem
  KosmoDraw seit demselben Tag sagt, was es geschrieben hat. Er wird hier **frei
  übergeben** und nicht nachgebaut: Der Prüfling ist der Leser, nicht der Schreiber, und
  ein Erzeuger, der immer einen gültigen Vermerk baute, könnte den ungültigen Fall gar
  nicht stellen.

Die Koordinaten sind **glTF-Koordinaten** (Y oben), nicht Weltkoordinaten. Das ist
Absicht: Die Umrechnung zwischen beiden ist der Gegenstand, den
``tests/test_glbbox.py`` prüft — sie darf nicht schon im Erzeuger stecken, sonst prüfte
der Test die Umrechnung gegen sich selbst.

Aufruf:
    python3 tools/make_test_glb.py ziel.glb
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

#: Die zwölf Dreiecke eines Quaders, als Eckenindizes auf die acht Ecken unten.
_FLAECHEN = (
    (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5),
    (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
    (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
)


def _ecken(lo, hi):
    """Die acht Ecken eines achsparallelen Quaders, in fester Reihenfolge."""
    return [(lo[0] if not (i & 1) else hi[0],
             lo[1] if not (i & 2) else hi[1],
             lo[2] if not (i & 4) else hi[2]) for i in range(8)]


def baue_glb(koerper, *, materialien=None, vermerk=None, erzeuger=None) -> bytes:
    """Benannte Quader → glb-Bytes.

    Args:
        koerper: Folge von ``(name, lo, hi)`` — ``lo``/``hi`` in **glTF-Koordinaten**
            (Y oben), je drei Zahlen.
        materialien: Materialnamen. ``None`` (Vorgabe) heisst **kein materials-Block** —
            genau der Zustand, den ``aiimaging.modellstand`` beanstandet. Mit Namen
            bekommt jedes Primitiv reihum eines davon.
        vermerk: Inhalt für ``asset.extras.kosmo_modellstand``. Wird **unverändert**
            eingesetzt, auch wenn er unsinnig ist — der ungültige Fall muss stellbar sein.
        erzeuger: ``asset.generator``. Vorgabe bleibt ``make_test_glb.py``.

    Returns:
        Die vollständige glb-Datei als ``bytes``.
    """
    bin_teile: list[bytes] = []
    versatz = 0
    accessors: list[dict] = []
    views: list[dict] = []
    meshes: list[dict] = []
    nodes: list[dict] = []

    for name, lo, hi in koerper:
        lo = [float(v) for v in lo]
        hi = [float(v) for v in hi]
        ecken = _ecken(lo, hi)

        roh = b"".join(struct.pack("<fff", *e) for e in ecken)
        views.append({"buffer": 0, "byteOffset": versatz, "byteLength": len(roh)})
        bin_teile.append(roh)
        versatz += len(roh)
        # min/max ist im glTF-2.0-Vertrag für POSITION **Pflicht** — und genau der
        # Grund, warum `aiimaging.glbbox` ohne Geometriebibliothek auskommt.
        accessors.append({"bufferView": len(views) - 1, "componentType": 5126,
                          "count": 8, "type": "VEC3", "min": lo, "max": hi})
        pos = len(accessors) - 1

        idx = b"".join(struct.pack("<HHH", *f) for f in _FLAECHEN)
        idx += b"\x00" * (-len(idx) % 4)                  # 4-Byte-Ausrichtung
        views.append({"buffer": 0, "byteOffset": versatz, "byteLength": len(idx)})
        bin_teile.append(idx)
        versatz += len(idx)
        accessors.append({"bufferView": len(views) - 1, "componentType": 5123,
                          "count": len(_FLAECHEN) * 3, "type": "SCALAR"})

        prim = {"attributes": {"POSITION": pos}, "indices": len(accessors) - 1}
        if materialien:
            prim["material"] = len(meshes) % len(materialien)
        meshes.append({"primitives": [prim]})
        nodes.append({"name": str(name), "mesh": len(meshes) - 1})

    roh_bin = b"".join(bin_teile)
    asset = {"version": "2.0", "generator": erzeuger or "make_test_glb.py"}
    if vermerk is not None:
        asset["extras"] = {"kosmo_modellstand": vermerk}
    js = {
        "asset": asset,
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(roh_bin)}],
    }
    if materialien:
        js["materials"] = [{"name": str(n)} for n in materialien]
    roh_js = json.dumps(js, separators=(",", ":")).encode("utf-8")
    roh_js += b" " * (-len(roh_js) % 4)                   # JSON mit Leerzeichen auffüllen
    roh_bin += b"\x00" * (-len(roh_bin) % 4)              # BIN mit Nullen

    kopf = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(roh_js) + 8 + len(roh_bin))
    return (kopf
            + struct.pack("<II", len(roh_js), 0x4E4F534A) + roh_js
            + struct.pack("<II", len(roh_bin), 0x004E4942) + roh_bin)


#: Ein Bauwerk auf einer Geländeplatte — die Lage, für die die Bauwerksbox gebaut ist.
#:
#: Bewusst **asymmetrisch** (dx ≠ dy ≠ dz und die Platte nicht mittig), damit eine
#: verdrehte Achse in einem Test *auffällt* statt zufällig gleich auszusehen. Dieselbe
#: Überlegung wie bei ``make_test_ifc.py``.
#:
#: In glTF-Koordinaten, Y oben. Weltmasse (Z oben): Bauwerk 12 × 9 × 15 m auf einer
#: Platte von 40 × 30 m.
VORGABE_SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ziel = Path(argv[0] if argv else "test.glb")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(baue_glb(VORGABE_SZENE))
    print(f"{ziel} — {len(VORGABE_SZENE)} Knoten, {ziel.stat().st_size} Byte")
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
