#!/usr/bin/env python3
"""RUNNER — glb → Cycles-Tiefenkarte. Läuft INNERHALB von Blender, nie im Produkt.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
Blender steht unter GPL-2.0-or-later (Binär-Releases GPL-3.0-or-later). Ein `import bpy`
im Produkt-Environment zöge das strengere Linking-Argument nach sich und machte das
Produkt GPL. Regel 2 zieht die Grenze deshalb am **Prozessaufruf**:

    blender --background --python blender_depth_stage.py -- <argumente>

Das ist GPL-rechtlich eine Aggregation. Blender bleibt GPL, der Apache-2.0-Code dieses
Projekts bleibt Apache-2.0.

**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden** — ausserhalb von
Blender existiert `bpy` nicht, und innerhalb wäre der Import die verbotene Verbindung.
`tests/test_prozessgrenze.py` erzwingt das.

Der Tiefen-Pass
---------------
Die Tiefe wird über den Compositor als 32-Bit-EXR geführt, nicht über einen
Emissions-Trick: Nur so stehen echte Meterwerte im Bild. Die Normalisierung auf 16-Bit-
Graustufen folgt der ControlNet-Konvention **nah = hell**.

Aufruf (immer über `aiimaging.blender_seam`, nicht von Hand):
    blender --background --python blender_depth_stage.py -- \
        --glb <in.glb> --out <verzeichnis> [--aufloesung 512] [--rotiere-z-up]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy  # noqa: E402  — nur innerhalb von Blender vorhanden; siehe Modul-Docstring


def _argumente():
    """Argumente hinter dem `--`-Trenner lesen (davor gehört alles Blender)."""
    import argparse

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--aufloesung", type=int, default=512)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--rotiere-z-up", action="store_true",
                    help="Quelle ist Z-up (z.B. kosmodraw_export_glb) → vor dem Rendern drehen")
    return ap.parse_args(argv)


def _szene_leeren() -> None:
    """Blenders Standardszene (Würfel, Licht, Kamera) entfernen — sie verfälscht die Tiefe."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _bbox_aller_meshes():
    """Achsparallele Bounding-Box aller Mesh-Objekte in Weltkoordinaten."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for ecke in obj.bound_box:
            welt = obj.matrix_world @ __import__("mathutils").Vector(ecke)
            for i in range(3):
                lo[i] = min(lo[i], welt[i])
                hi[i] = max(hi[i], welt[i])
    if lo[0] == float("inf"):
        raise RuntimeError("keine Mesh-Geometrie in der Szene")
    return lo, hi


def _kamera_setzen(lo, hi):
    """Eine Kamera aus der Bounding-Box ableiten — diagonal von vorn-oben.

    Bewusst schlicht: Das Skelett soll die Prozessgrenze prüfen, nicht die
    Kamerakomposition. Die zwölf Automatikkameras kommen in Phase 3.
    """
    import mathutils

    mitte = mathutils.Vector([(lo[i] + hi[i]) / 2.0 for i in range(3)])
    spanne = max(hi[i] - lo[i] for i in range(3)) or 1.0

    kam_daten = bpy.data.cameras.new("Kamera")
    kam = bpy.data.objects.new("Kamera", kam_daten)
    bpy.context.scene.collection.objects.link(kam)
    kam.location = mitte + mathutils.Vector((1.6, -2.0, 1.2)) * spanne
    kam.rotation_mode = "QUATERNION"
    kam.rotation_quaternion = (mitte - kam.location).to_track_quat("-Z", "Y")
    bpy.context.scene.camera = kam
    return kam, mitte, spanne


def _compositor_auf_tiefe(out_dir: Path) -> None:
    """View-Layer-Z-Pass über den Compositor als 32-Bit-EXR ausgeben.

    Der Umweg über den Compositor ist der Grund, warum hier volles Blender nötig ist und
    Cycles allein nicht genügt: `use_pass_z` liefert die Tiefe erst über einen
    Node-Graph als Datei mit echten Meterwerten.
    """
    szene = bpy.context.scene
    szene.view_layers[0].use_pass_z = True
    szene.use_nodes = True
    baum = szene.node_tree
    baum.nodes.clear()

    render_layer = baum.nodes.new("CompositorNodeRLayers")
    ausgabe = baum.nodes.new("CompositorNodeOutputFile")
    ausgabe.base_path = str(out_dir)
    ausgabe.format.file_format = "OPEN_EXR"
    ausgabe.format.color_depth = "32"
    # OPEN_EXR kennt nur RGB/RGBA — kein Graustufen-Modus. Die Tiefe steht im R-Kanal;
    # alle drei Kanaele tragen denselben Wert, das kostet Platz, aber keine Genauigkeit.
    ausgabe.format.color_mode = "RGB"
    ausgabe.file_slots.clear()
    ausgabe.file_slots.new("tiefe_")
    baum.links.new(render_layer.outputs["Depth"], ausgabe.inputs["tiefe_"])


def main() -> int:
    a = _argumente()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    _szene_leeren()
    bpy.ops.import_scene.gltf(filepath=a.glb)

    if getattr(a, "rotiere_z_up", False):
        # Quelle war Z-up (glTF verlangt Y-up). Ohne diese Drehung läge der Bau auf der
        # Seite — und Tiefenkarte, Kamera und Geometrie-QA wären still verdreht.
        import math

        import mathutils
        dreh = mathutils.Matrix.Rotation(math.radians(90.0), 4, "X")
        for obj in bpy.data.objects:
            if obj.parent is None:
                obj.matrix_world = dreh @ obj.matrix_world

    lo, hi = _bbox_aller_meshes()
    _kamera_setzen(lo, hi)

    szene = bpy.context.scene
    szene.render.engine = "CYCLES"
    szene.cycles.samples = a.samples
    szene.cycles.device = "CPU"
    szene.render.resolution_x = szene.render.resolution_y = a.aufloesung
    szene.render.resolution_percentage = 100
    szene.render.filepath = str(out_dir / "beauty_")

    _compositor_auf_tiefe(out_dir)
    bpy.ops.render.render(write_still=True)

    exr = sorted(out_dir.glob("tiefe_*.exr"))
    report = {
        "status": "ok" if exr else "error",
        "depth_exr": str(exr[0]) if exr else None,
        "bbox": [lo, hi],
        "bbox_size_m": [hi[i] - lo[i] for i in range(3)],
        "n_meshes": sum(1 for o in bpy.data.objects if o.type == "MESH"),
        "aufloesung": a.aufloesung,
        "rotiert": bool(getattr(a, "rotiere_z_up", False)),
        "blender": bpy.app.version_string,
        "error": None if exr else "Compositor schrieb keine EXR",
    }
    (out_dir / "blender-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("BLENDER_REPORT " + json.dumps(report, ensure_ascii=False))
    return 0 if exr else 1


if __name__ == "__main__":
    sys.exit(main())
