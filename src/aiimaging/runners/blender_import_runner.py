#!/usr/bin/env python3
"""RUNNER — ein fremdes 3D-Format → glb. Läuft INNERHALB von Blender, nie im Produkt.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
Blender steht unter GPL-2.0-or-later (Binär-Releases GPL-3.0-or-later). Ein ``import
bpy`` im Produkt-Environment zöge das strengere Linking-Argument nach sich und machte das
Produkt GPL. Regel 2 zieht die Grenze deshalb am **Prozessaufruf**:

    blender --background --python blender_import_runner.py -- <argumente>

Das ist GPL-rechtlich eine Aggregation. Blender bleibt GPL, der Apache-2.0-Code dieses
Projekts bleibt Apache-2.0.

**Dieses Modul darf aus ``aiimaging`` heraus niemals importiert werden** — ausserhalb von
Blender existiert ``bpy`` nicht, und innerhalb wäre der Import die verbotene Verbindung.
``tests/test_prozessgrenze.py`` erzwingt das.

Warum es diesen Runner überhaupt gibt
-------------------------------------
Bis zum 21.09.2026 kannte dieses Projekt **drei** Modellformate: ``glb``, ``gltf``,
``ifc``. Alles andere lief in :mod:`aiimaging.einlass` gegen eine höfliche Absage mit
einem Rat: *«Blender liest FBX und schreibt glTF: Datei → Exportieren → glTF 2.0.»*

Der Rat ist richtig und er ist eine Zumutung. Wer eine Software herunterlädt, die aus
einem Gebäudemodell Bilder macht, soll nicht zuerst ein zweites Programm installieren,
das sie selbst bereits aufruft.

    *Ein Werkzeug, das den Weg kennt und ihn dem Benutzer aufträgt, hat die Arbeit nicht
    getan, sondern verteilt.*

Was er tut, und was ausdrücklich nicht
--------------------------------------
Er **öffnet eine leere Szene**, importiert genau eine Datei, misst, und schreibt eine
glb. Er repariert nichts, er skaliert nichts, er dreht nichts zurecht. Was an der Datei
krumm ist, ist danach immer noch krumm — und steht im Bericht.

Der Bericht trägt dieselben Felder wie der IFC-Runner (``bbox``, ``n_elements``,
``n_triangles``), damit :mod:`aiimaging.konversionstreue` **beide** Wege mit demselben
Mass prüfen kann. Ein zweites Berichtsformat wäre eine zweite Wahrheit.

Aufruf (immer über :mod:`aiimaging.importeur`, nicht von Hand):
    blender --background --python blender_import_runner.py -- \
        --quelle <datei> --glb <ziel.glb> [--report <bericht.json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy                                                        # noqa: E402  (nur in Blender)


#: Endung → (Anzeigename, Name des Blender-Operators).
#:
#: **Nur Formate, die Blender von Haus aus liest.** Ein Format, für das ein Add-on
#: nachinstalliert werden müsste, gehört nicht hierher: Es liefe bei uns und bei der
#: Hälfte der Benutzerinnen nicht, und der Unterschied wäre von aussen unsichtbar.
IMPORTEURE: dict[str, tuple[str, str]] = {
    ".obj": ("Wavefront OBJ", "wm.obj_import"),
    ".fbx": ("Autodesk FBX", "import_scene.fbx"),
    ".dae": ("Collada", "wm.collada_import"),
    ".stl": ("STL", "wm.stl_import"),
    ".ply": ("Stanford PLY", "wm.ply_import"),
    ".usd": ("USD", "wm.usd_import"),
    ".usdc": ("USD (binär)", "wm.usd_import"),
    ".usda": ("USD (Text)", "wm.usd_import"),
    ".abc": ("Alembic", "wm.alembic_import"),
    ".x3d": ("X3D", "import_scene.x3d"),
    ".glb": ("glTF (binär)", "import_scene.gltf"),
    ".gltf": ("glTF", "import_scene.gltf"),
}

#: Formate, die **nur Dreiecke** tragen: keine Bauteile, keine Räume, keine Materialien.
#: Sie laufen durch, aber der Bericht sagt es — denn was hier fehlt, fehlt später der
#: Geometrie-QA, und dort sähe es nach einem Messfehler aus statt nach einer Eigenschaft
#: der Datei.
NUR_DREIECKE = (".stl", ".ply")


def _leere_szene() -> None:
    """Alles weg, was Blender beim Start mitbringt — Würfel, Kamera, Lampe.

    **Nicht kosmetisch.** Bliebe der Vorgabewürfel stehen, wanderte er in die glb, in die
    Hüllbox und damit in jede Kameraableitung. Ein zwei Meter grosser Würfel neben einem
    Gebäude verschiebt die Rahmung, und niemand sähe ihm an, woher er kommt.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _operator(name: str):
    """Den Blender-Operator zu ``"wm.obj_import"`` holen, oder ``None``.

    Blender benennt Importeure zwischen Fassungen um (``import_mesh.stl`` hiess der
    STL-Weg bis 4.0, ``wm.stl_import`` heisst er seit 4.1). Ein fehlender Operator ist
    darum **kein Programmfehler**, sondern eine Auskunft über die vorhandene Fassung —
    und sie gehört in den Bericht, nicht in einen Traceback.
    """
    ziel = bpy.ops
    for teil in name.split("."):
        ziel = getattr(ziel, teil, None)
        if ziel is None:
            return None
    return ziel


def _masse() -> dict:
    """Hüllbox, Objektzahl und Dreieckszahl der geladenen Szene — in Metern, Z oben.

    Die Hüllbox wird aus den **Welt-Koordinaten** der Eckpunkte gerechnet, nicht aus den
    lokalen: Ein Objekt, das über seine Objekt-Transformation verschoben oder skaliert
    ist, steht sonst an der falschen Stelle in der Box. Genau das ist bei FBX aus
    CAD-Programmen der Regelfall.
    """
    minimum = [float("inf")] * 3
    maximum = [float("-inf")] * 3
    n_objekte = 0
    n_dreiecke = 0

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.data is None:
            continue
        n_objekte += 1
        netz = obj.data
        netz.calc_loop_triangles()
        n_dreiecke += len(netz.loop_triangles)
        for ecke in netz.vertices:
            welt = obj.matrix_world @ ecke.co
            for i in range(3):
                minimum[i] = min(minimum[i], welt[i])
                maximum[i] = max(maximum[i], welt[i])

    if n_objekte == 0 or minimum[0] == float("inf"):
        return {"bbox": None, "n_elements": n_objekte, "n_triangles": n_dreiecke}
    return {"bbox": [minimum, maximum], "n_elements": n_objekte, "n_triangles": n_dreiecke}


def importiere(quelle: str, glb: str) -> dict:
    """Eine Datei importieren und als glb schreiben. Gibt den Bericht zurück."""
    pfad = Path(quelle)
    endung = pfad.suffix.lower()
    if endung not in IMPORTEURE:
        return {"status": "error", "glb_path": None,
                "error": f"Kein Blender-Importeur für die Endung {endung!r}."}

    name, operator_name = IMPORTEURE[endung]
    operator = _operator(operator_name)
    if operator is None:
        return {"status": "error", "glb_path": None,
                "error": (f"Diese Blender-Fassung ({bpy.app.version_string}) kennt den "
                          f"Operator {operator_name!r} nicht. {name} ist damit hier nicht "
                          f"zu lesen.")}

    _leere_szene()
    try:
        operator(filepath=str(pfad))
    except Exception as fehler:                      # Fehler als Bericht, nicht als Traceback
        return {"status": "error", "glb_path": None,
                "error": f"{type(fehler).__name__}: {fehler}"}

    gemessen = _masse()
    if gemessen["n_elements"] == 0:
        return {"status": "error", "glb_path": None, "error": (
            f"{name} gelesen, aber die Szene ist leer — keine einzige Fläche. Die Datei "
            f"trägt vermutlich nur Kurven, Punkte oder Hilfsgeometrie."), **gemessen}

    Path(glb).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB",
                              export_yup=True, use_selection=False)

    warnungen = []
    if endung in NUR_DREIECKE:
        warnungen.append(
            f"{name} trägt nur Dreiecke — keine Bauteile, keine Räume, keine Materialien. "
            f"Die Geometrie-QA misst danach die Form, aber nichts trennt Bauwerk und "
            f"Gelände. Für eine Architektur-Visualisierung ist IFC oder glTF der bessere "
            f"Weg.")

    return {
        "status": "ok",
        "glb_path": str(glb),
        "quelle_format": name,
        "quelle_endung": endung,
        "blender": bpy.app.version_string,
        "up_axis": "Y",
        "bbox_note": ("bbox in den Metern der Quelldatei, Z oben — wie beim IFC-Runner. "
                      "Die glb selbst ist Y-up."),
        "warnungen": warnungen,
        "error": None,
        **gemessen,
    }


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="Fremdes 3D-Format → glb. Läuft in Blender.")
    ap.add_argument("--quelle", required=True)
    ap.add_argument("--glb", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)

    try:
        bericht = importiere(a.quelle, a.glb)
    except Exception as fehler:                      # Fehler als Bericht, nicht als Traceback
        bericht = {"status": "error", "glb_path": None,
                   "error": f"{type(fehler).__name__}: {fehler}"}

    text = json.dumps(bericht, indent=2, ensure_ascii=False)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
    print(text)
    return 0 if bericht["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
