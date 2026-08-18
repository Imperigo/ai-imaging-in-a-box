"""Verträge der Bildkette: render-scene und die Up-Achsen-Regel.

Warum dieses Modul zuerst entstand
----------------------------------
Phase 0 hat einen Konflikt zwischen zwei Erzeugern von ``glb_path`` belegt:

  * KosmoDraw ``glb_export_runner.py``  → ``up_axis: "Z"`` (rohe IFC-Koordinaten)
  * KosmoVis  ``ifc_to_glb.py``         → ``up_axis: "Y (glTF-2.0-Standard; …)"``

Beide Felder heissen gleich, beide Werkzeuge sind für ihren eigenen Abnehmer richtig —
aber glTF 2.0 ist definitionsgemäss Y-up und Blender importiert strikt Y-up → Z-up. Eine
rohe Z-up-glb landet in Blender **liegend auf der Seite**, und zwar ohne Fehlermeldung:
Tiefenkarte, Kameraableitung und Geometrie-QA wären still verdreht.

Darum ist ``up_axis`` hier **Pflichtfeld**, nicht Vermutung. Fehlt es, wird abgelehnt.

Abhängigkeiten: keine. Reine stdlib, damit der Vertrag überall prüfbar ist — auch dort,
wo weder Blender noch ifcopenshell existieren.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

SCHEMA_ID = "aiimaging.render-scene/v1"

#: Wie die Nachbar-Lanes ihre Geometrie benennen (belegt in Phase 0, 2026-08-14, aus
#: ``kosmodraw_mcp_server.py:274-300``). Diese Namen sind bindend: KosmoOrbits
#: ``mergeInputs`` zieht Kanten allein über Feldnamen-Gleichheit — ein abweichender Name
#: erzeugt keine Kante und keine Fehlermeldung.
LANE_FIELDS = ("ifc_path", "glb_path", "up_axis", "bbox")


class ContractError(ValueError):
    """Eingabe verletzt den Vertrag. Bewusst laut statt stillschweigend geraten."""


def normalize_up_axis(value) -> str:
    """Beliebige Up-Achsen-Angabe → ``"Y"`` oder ``"Z"``.

    Muss tolerant sein, weil die beiden bekannten Erzeuger unterschiedlich schreiben:
    KosmoDraw liefert das blosse ``"Z"``, KosmoVis einen beschreibenden Satz, der mit
    ``"Y"`` beginnt. Toleranz endet allerdings bei Abwesenheit — ``None`` ist ein Fehler,
    keine Gelegenheit für einen Default.

    Raises:
        ContractError: fehlend, leer oder nicht als Y/Z deutbar.
    """
    if value is None:
        raise ContractError(
            "up_axis fehlt. Pflichtfeld — glTF 2.0 kennt kein Up-Achsen-Feld, und die "
            "Erzeuger im Ökosystem sind sich uneinig (KosmoDraw Z, KosmoVis Y). Ein "
            "Default wäre eine stille Verdrehung."
        )
    text = str(value).strip()
    if not text:
        raise ContractError("up_axis ist leer.")
    first = text[0].upper()
    if first in ("Y", "Z"):
        return first
    raise ContractError(f"up_axis nicht als Y oder Z deutbar: {value!r}")


def needs_rotation(up_axis) -> bool:
    """Muss diese glb vor dem Blender-Import Z-up → Y-up gedreht werden?

    ``True`` bei Z-up (etwa aus ``kosmodraw_export_glb``), ``False`` bei bereits
    glTF-konformem Y-up.
    """
    return normalize_up_axis(up_axis) == "Z"


def validate_render_scene(scene: dict) -> dict:
    """Prüft eine render-scene und gibt sie normalisiert zurück.

    Genau **eine** Geometriequelle ist erlaubt: ``ifc_path`` (eigener Pfad, Regel 4 —
    der Kern liest selbst) oder ``glb_path`` (Einfügen in die Ökosystem-Kette). Beide
    zugleich wäre mehrdeutig, keine von beiden unbrauchbar.

    ``up_axis`` ist nur bei ``glb_path`` Pflicht: Beim eigenen IFC-Pfad kennen wir die
    Orientierung, weil wir sie selbst erzeugen.

    Returns:
        Normalisierte Kopie; bei glb-Eingang zusätzlich ``up_axis`` (``"Y"``/``"Z"``)
        und ``needs_rotation``.

    Raises:
        ContractError: bei jedem Verstoss — nie stillschweigend repariert.
    """
    if not isinstance(scene, dict):
        raise ContractError(f"render-scene muss ein Objekt sein, war {type(scene).__name__}")

    geom = scene.get("geometry")
    if not isinstance(geom, dict):
        raise ContractError("Pflichtfeld 'geometry' fehlt oder ist kein Objekt.")

    ifc_path, glb_path = geom.get("ifc_path"), geom.get("glb_path")
    if ifc_path and glb_path:
        raise ContractError(
            "geometry trägt ifc_path UND glb_path — mehrdeutig. Genau eine Quelle angeben."
        )
    if not ifc_path and not glb_path:
        raise ContractError("geometry braucht ifc_path oder glb_path.")

    # out_dir zuerst prüfen: Fehlen mehrere Pflichtfelder, soll der Aufrufer nicht erst
    # den up_axis-Fehler sehen und nach dessen Behebung den nächsten.
    if not scene.get("out_dir"):
        raise ContractError("Pflichtfeld 'out_dir' fehlt.")

    # `copy.deepcopy` statt eines JSON-Umwegs: Ein `Path` als ifc_path ist beim
    # programmatischen Bauen naheliegend, und `json.dumps` wirft darauf einen TypeError
    # — ein Fehler, der nichts mit dem Vertrag zu tun hat und den Aufrufer in die Irre
    # führt. Pfadartige Werte werden stattdessen zu str normalisiert.
    out = copy.deepcopy(scene)
    out["schema"] = SCHEMA_ID
    g = out["geometry"]
    for feld in ("ifc_path", "glb_path"):
        if isinstance(g.get(feld), os.PathLike):
            g[feld] = os.fspath(g[feld])

    if glb_path:
        # Der Kern des Phase-0-Befunds: hier wird nicht geraten.
        g["up_axis"] = normalize_up_axis(geom.get("up_axis"))
        g["needs_rotation"] = g["up_axis"] == "Z"
    else:
        # Eigener IFC-Pfad → der Runner erzeugt glTF-konformes Y-up. Ein mitgegebenes,
        # abweichendes up_axis wird NICHT stillschweigend überschrieben: Es deutet auf
        # eine falsche Annahme des Aufrufers hin, und diese Linie — nie stillschweigend
        # reparieren — ist der Grund, warum dieses Modul überhaupt existiert.
        angabe = geom.get("up_axis")
        if angabe is not None and normalize_up_axis(angabe) != "Y":
            raise ContractError(
                f"up_axis={angabe!r} widerspricht dem eigenen IFC-Pfad: Der Runner "
                f"erzeugt glTF-konformes Y-up. Entweder up_axis weglassen oder eine "
                f"fertige glb über glb_path übergeben."
            )
        g["up_axis"] = "Y"
        g["needs_rotation"] = False

    return out


def load_render_scene(path) -> dict:
    """render-scene aus einer JSON-Datei laden und prüfen."""
    return validate_render_scene(json.loads(Path(path).read_text(encoding="utf-8")))
