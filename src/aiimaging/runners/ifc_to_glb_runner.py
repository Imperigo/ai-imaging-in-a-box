#!/usr/bin/env python3
"""RUNNER — IFC4 → glb. Läuft im `.venv-ifc`, NIEMALS im Produkt-Environment.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
`ifcopenshell` steht unter LGPL-3.0-or-later. Schwerwiegender: Das ausgelieferte
PyPI-Wheel bindet **CGAL statisch** ein, und die genutzten CGAL-Pakete
(`Nef_polyhedron_3`, `Polygon_mesh_processing`) stehen unter **GPL-3.0-or-later**
(verifiziert am Binary, 2026-08-14). Ein `import ifcopenshell` im Produkt-Environment
würde das Produkt GPL machen.

Die Prozessgrenze löst das: Dieses Skript ist ein eigenständiges Programm in einem
eigenen venv. Es wird aufgerufen, nicht importiert; die Verständigung läuft über Dateien.
Es entsteht eine Aggregation, kein abgeleitetes Werk.

**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden.**
`tests/test_prozessgrenze.py` erzwingt das.

Up-Achse
--------
IFC ist Z-up, glTF 2.0 ist definitionsgemäss Y-up und kennt kein Up-Achsen-Feld. Ohne
Rotation importiert Blender (strikt Y-up → Z-up) den Baukörper **liegend**. Dieser
Runner dreht darum −90° um X und meldet `up_axis: "Y"`.

Aufruf:
    .venv-ifc/bin/python ifc_to_glb_runner.py <in.ifc> <out.glb> [--report r.json]
"""
from __future__ import annotations

import argparse
import json
import sys


def ifc_to_glb(ifc_path: str, glb_path: str) -> dict:
    """Konvertiert IFC4 → glb (Y-up) und liefert einen Report.

    Der Report meldet auch dann `status`, wenn etwas schiefging — der Aufrufer soll
    entscheiden, nicht raten müssen.
    """
    import ifcopenshell            # noqa: PLC0415 — bewusst lokal: nur in diesem Prozess
    import ifcopenshell.geom
    import numpy as np
    import trimesh

    modell = ifcopenshell.open(ifc_path)
    einst = ifcopenshell.geom.settings()
    einst.set("use-world-coords", True)

    szene = trimesh.Scene()
    n_elemente = n_dreiecke = 0
    for produkt in modell.by_type("IfcProduct"):
        if not getattr(produkt, "Representation", None):
            continue
        try:
            form = ifcopenshell.geom.create_shape(einst, produkt)
        except Exception:
            continue                                  # nicht-geometrische Produkte
        ecken = np.asarray(form.geometry.verts, dtype="float64").reshape(-1, 3)
        flaechen = np.asarray(form.geometry.faces, dtype="int64").reshape(-1, 3)
        if len(ecken) == 0 or len(flaechen) == 0:
            continue
        szene.add_geometry(trimesh.Trimesh(vertices=ecken, faces=flaechen, process=False),
                           node_name=f"{produkt.is_a()}_{produkt.GlobalId}")
        n_elemente += 1
        n_dreiecke += len(flaechen)

    if n_elemente == 0:
        return {"status": "error", "error": "keine Geometrie im IFC", "glb_path": None}

    bbox_zup = szene.bounds.tolist()                  # noch in nativen IFC-Metern (Z oben)

    # Z-up → Y-up: −90° um X. glTF 2.0 ist Y-up; ohne das liegt der Bau in Blender.
    dreh = trimesh.transformations.rotation_matrix(-np.pi / 2.0, [1, 0, 0])
    szene.apply_transform(dreh)
    szene.export(glb_path)

    return {
        "status": "ok",
        "glb_path": glb_path,
        "up_axis": "Y",
        "bbox": bbox_zup,
        "n_elements": n_elemente,
        "n_triangles": n_dreiecke,
        "bbox_note": "bbox in nativen IFC-Metern (Z oben); die glb selbst ist Y-up",
        "error": None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IFC4 → glb (Y-up). Läuft im .venv-ifc.")
    ap.add_argument("ifc")
    ap.add_argument("glb")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)

    try:
        rep = ifc_to_glb(a.ifc, a.glb)
    except Exception as e:                            # Fehler als Report, nicht als Traceback
        rep = {"status": "error", "error": f"{type(e).__name__}: {e}", "glb_path": None}

    text = json.dumps(rep, indent=2, ensure_ascii=False)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
