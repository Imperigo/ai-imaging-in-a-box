#!/usr/bin/env python3
"""RUNNER — glb → Cycles-Multipass. Läuft INNERHALB von Blender, nie im Produkt.

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

Die vier Ausgaben
-----------------
1. **Beauty** (`beauty_.png`) — das gewöhnliche gerenderte Bild. Beleuchtet von einer
   Sonne plus gleichmässigem Umgebungslicht. Bewusst schlicht und fest verdrahtet: Die
   Lichtstimmung ist nicht Gegenstand dieser Phase, die Reproduzierbarkeit schon.
2. **Material-ID** (`material_id.png`) — pro Material eine flache, unbeleuchtete
   Farbfläche. Dient später als Segmentierungsmaske für die Geometrie-QA.
3. **Tiefe roh** (`tiefe_0001.exr`) — 32-Bit-EXR über den Compositor, mit **echten
   Meterwerten**. Das ist die Grundlage der Geometrie-QA.
4. **Tiefe normalisiert** (`tiefe_norm.png`) — 16-Bit-Graustufen, Konvention
   **nah = hell**. Das ist die ControlNet-Konvention und der Pass, den das Bildmodell
   später als Konditionierung bekommt.

Zwei Renderdurchgänge, kein Kompromiss
--------------------------------------
Beauty und Tiefe entstehen im **selben** Durchgang (die Tiefe ist ein View-Layer-Pass,
sie kostet keinen zweiten Strahl). Die Material-ID braucht dagegen einen **eigenen**
Durchgang: Sie ersetzt jedes Material durch einen Emissions-Shader, und dieser Eingriff
würde das Beauty-Bild in dieselbe flache Farbfläche verwandeln.

Warum die Farben unbeleuchtet sein müssen
-----------------------------------------
Eine Material-ID-Farbe ist eine *Kennung*, kein Aussehen. Sähe sie Licht, wären zwei
Wände desselben Materials in Sonne und Schatten zwei verschiedene Farben — die Maske
wäre unbrauchbar. Emissions-Shader (mit schwarzer Welt und einem einzigen Sample)
liefern den Farbwert exakt so, wie er gesetzt wurde.

Aufruf (immer über `aiimaging.seams`, nicht von Hand):
    blender --background --python blender_depth_stage.py -- \
        --glb <in.glb> --out <verzeichnis> [--aufloesung 512] [--samples 16] \
        [--rotiere-z-up] [--ohne-beauty] [--ohne-material-id]
"""
from __future__ import annotations

import colorsys
import json
import math
import sys
import time
from pathlib import Path

import bpy  # noqa: E402  — nur innerhalb von Blender vorhanden; siehe Modul-Docstring

#: Goldener Winkel als Anteil eines Vollkreises (1/φ²). Die Farbtöne der Material-IDs
#: werden damit über den HSV-Farbkreis verteilt: h = (i * GOLDENER_WINKEL) % 1.0.
#: Der Grund ist eine Eigenschaft der Zahl selbst — weil sie irrational ist, liegen auch
#: aufeinanderfolgende Indizes weit auseinander, und die Folge häuft sich nie. Eine
#: gleichmässige Teilung (h = i/n) bräuchte dagegen die Gesamtzahl im Voraus und änderte
#: bei jedem neuen Material sämtliche bisherigen Farben.
GOLDENER_WINKEL = 0.618033988749895

#: Sättigung und Helligkeit der ID-Farben. Fest, damit sich die Farben allein im Farbton
#: unterscheiden — das ist die Achse, auf der der Goldene Winkel den Abstand garantiert.
ID_SAETTIGUNG = 0.85
ID_HELLIGKEIT = 1.00

#: Ab diesem Wert gilt ein Tiefenpixel als Hintergrund. Cycles schreibt für Strahlen ins
#: Leere keinen Fehlwert, sondern eine sehr grosse Zahl (Grössenordnung 1e10). Ohne diese
#: Schranke risse ein einziges Hintergrundpixel die Normalisierung auseinander und das
#: ganze Gebäude wäre schwarz.
HINTERGRUND_AB_M = 1.0e7


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
    ap.add_argument("--ohne-beauty", action="store_true",
                    help="Beauty-Bild nicht schreiben (der Durchgang läuft trotzdem — die "
                         "Tiefe hängt an ihm)")
    ap.add_argument("--ohne-material-id", action="store_true",
                    help="zweiten Renderdurchgang auslassen; spart etwa die halbe Rechenzeit")
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


# --------------------------------------------------------------------------------------
# Beleuchtung — schlicht, aber vorhanden
# --------------------------------------------------------------------------------------

def _welt_setzen(farbe, staerke: float) -> None:
    """Gleichmässiges Umgebungslicht als Welt-Hintergrund setzen.

    `read_factory_settings(use_empty=True)` löscht auch die Welt. Ohne sie rendert Cycles
    vor absolutem Schwarz und ohne jede Aufhellung — genau der Zustand, in dem das
    Beauty-Bild des Vorgängerstands unsichtbar blieb.
    """
    welt = bpy.data.worlds.new("Welt")
    hintergrund = _welt_hintergrund(welt)
    hintergrund.inputs["Color"].default_value = (*farbe, 1.0)
    hintergrund.inputs["Strength"].default_value = staerke
    bpy.context.scene.world = welt


def _sonne_setzen(mitte, spanne: float):
    """Eine einzelne Sonne von schräg vorn-oben.

    Eine Sonne (Richtungslicht) statt einer Punktlichtquelle, weil ihre Wirkung nicht vom
    Abstand abhängt: Dieselben Winkel liefern bei einem Reihenhaus dieselbe Helligkeit
    wie bei einem Hochhaus. Damit bleibt das Bild über verschiedene Bauten hinweg
    vergleichbar, ohne dass irgendetwas an der Geometrie nachgeführt werden müsste.
    """
    licht = bpy.data.lights.new("Sonne", type="SUN")
    licht.energy = 2.0
    licht.angle = math.radians(3.0)      # weiche Schattenkanten, nicht rasiermesserscharf
    sonne = bpy.data.objects.new("Sonne", licht)
    bpy.context.scene.collection.objects.link(sonne)
    # Position ist bei einer Sonne bedeutungslos, nur die Drehung zählt. Sie wird trotzdem
    # über der Szene abgelegt, damit ein späterer Blick in die .blend nicht verwirrt.
    sonne.location = (mitte[0], mitte[1], mitte[2] + spanne * 2.0)
    sonne.rotation_euler = (math.radians(50.0), 0.0, math.radians(35.0))
    return sonne


# --------------------------------------------------------------------------------------
# Material-ID — Farbverteilung über den Goldenen Winkel
# --------------------------------------------------------------------------------------

def _id_farbe_srgb(index: int):
    """Anzeigefarbe (sRGB, 0..1) für den Material-Index `index`.

    Der Farbton läuft über den Goldenen Winkel, Sättigung und Helligkeit sind fest.
    """
    h = (index * GOLDENER_WINKEL) % 1.0
    return colorsys.hsv_to_rgb(h, ID_SAETTIGUNG, ID_HELLIGKEIT)


def _srgb_zu_linear(c: float) -> float:
    """sRGB-Anzeigewert → linearer Renderwert (die Umkehrung dessen, was das PNG tut).

    Cycles rechnet linear, PNG speichert sRGB-kodiert. Würde die Anzeigefarbe direkt als
    Emissionsfarbe gesetzt, käme im PNG die zweimal kodierte Farbe an. Über diesen Schritt
    steht am Ende **exakt** die Palette in der Datei, die `_id_farbe_srgb` beschreibt — die
    QA kann später Bildfarbe und Report-Tabelle Byte für Byte vergleichen.
    """
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _emissions_material(name: str, farbe_srgb) -> "bpy.types.Material":
    """Ein Material, das genau eine Farbe abstrahlt und kein Licht empfängt."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    baum = mat.node_tree
    baum.nodes.clear()
    emission = baum.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*(_srgb_zu_linear(k) for k in farbe_srgb), 1.0)
    emission.inputs["Strength"].default_value = 1.0
    ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
    baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])
    return mat


def _material_id_zuweisen() -> tuple[list[dict], int]:
    """Jedem Material eine ID-Farbe geben und die Szene darauf umstellen.

    Returns:
        (Tabelle, Anzahl echter Materialien). Die Tabelle trägt pro ID-Eintrag Index,
        Name, Herkunft und Farbe — ohne sie liesse sich aus dem Bild nicht zurücklesen,
        welche Fläche welches Material war.

    Warum **nicht** `view_layer.material_override`
    ----------------------------------------------
    Der View-Layer-Override kennt genau *ein* Material für die ganze Ebene. Er kann das
    Beleuchtungsmodell austauschen, aber nicht pro Material unterscheiden — mit ihm wäre
    das Bild einfarbig und als Maske wertlos. Dieselbe Wirkung (nichts vom Original
    bleibt sichtbar, alles emittiert) entsteht hier stattdessen slotweise. Das ist
    strenger als ein Override: Ein Objekt mit mehreren Material-Slots behält seine
    Aufteilung, jede Teilfläche bekommt ihre eigene Farbe.

    Rückfall ohne Materialien
    -------------------------
    Trägt ein Mesh gar kein Material, bekommt es **objektweise** eine eigene ID. Sonst
    verschmölze eine materiallose Szene zu einer einzigen Fläche. Genau das ist der
    Normalfall der aktuellen Kette: `ifc_to_glb_runner.py` überträgt nur Geometrie, keine
    IfcMaterial-Zuordnung — die glb kommt ohne Materialien in Blender an. Die Herkunft
    steht deshalb in jedem Eintrag (`quelle`), damit niemand eine Objekt-Maske für eine
    Material-Maske hält.
    """
    tabelle: list[dict] = []
    nach_material: dict[str, int] = {}
    n_echte_materialien = len(bpy.data.materials)

    def eintragen(name: str, quelle: str) -> "bpy.types.Material":
        index = len(tabelle)
        farbe = _id_farbe_srgb(index)
        mat = _emissions_material(f"MATID_{index:03d}_{name}", farbe)
        tabelle.append({
            "index": index,
            "name": name,
            "quelle": quelle,
            "farbe_srgb": [round(k, 6) for k in farbe],
            "farbe_srgb_8bit": [int(round(k * 255.0)) for k in farbe],
        })
        return mat

    # Nach Namen sortiert, damit zwei Läufe dieselben Indizes und damit dieselben Farben
    # vergeben. Ohne feste Reihenfolge wäre die Maske nicht reproduzierbar.
    meshes = sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name)
    for obj in meshes:
        belegt = [s for s in obj.material_slots if s.material is not None]
        if not belegt:
            obj.data.materials.clear()
            obj.data.materials.append(eintragen(obj.name, "objekt"))
            continue
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            name = slot.material.name
            if name not in nach_material:
                nach_material[name] = len(tabelle)
                slot.material = eintragen(name, "material")
            else:
                slot.material = bpy.data.materials[
                    f"MATID_{nach_material[name]:03d}_{name}"
                ]

    return tabelle, n_echte_materialien


# --------------------------------------------------------------------------------------
# Tiefe
# --------------------------------------------------------------------------------------

def _kompositor_baum(szene):
    """Den Kompositor-Knotenbaum holen — versionsfest über Blender 4.x und 5.x.

    **Belegt auf echter Hardware (2026-08-18, HomeStation, Auftrag `auf-20260818-01`):**
    Blender 5.0 hat `Scene.node_tree` entfernt. Der Kompositor ist dort ein eigener
    Datenblock und hängt unter `Scene.compositing_node_group`; `use_nodes` ist abgekündigt.
    Auf 4.2 LTS — wogegen dieser Runner ursprünglich gebaut und geprüft wurde — gilt
    weiterhin der alte Weg.

    Die Weiche prüft die **Fähigkeit**, nicht die Versionsnummer: `hasattr` bleibt richtig,
    auch wenn Blender die Umstellung in einer anderen Fassung nachzieht als angenommen.
    """
    if hasattr(szene, "compositing_node_group"):          # Blender 5.x
        baum = szene.compositing_node_group
        if baum is None:
            baum = bpy.data.node_groups.new("Kompositor", "CompositorNodeTree")
            szene.compositing_node_group = baum
        return baum
    szene.use_nodes = True                                # Blender <= 4.x
    return szene.node_tree


def _kompositor_abschalten(szene) -> None:
    """Den Kompositor für den Material-ID-Durchgang stilllegen — ebenfalls versionsfest."""
    if hasattr(szene, "compositing_node_group"):
        szene.compositing_node_group = None
    else:
        szene.use_nodes = False


def _welt_hintergrund(welt):
    """Den Hintergrund-Knoten einer Welt holen. `World.use_nodes` ist ab 5.0 abgekündigt."""
    if not getattr(welt, "use_nodes", False) and hasattr(welt, "use_nodes"):
        try:
            welt.use_nodes = True
        except Exception:                                 # ab Blender 6.0 entfernt
            pass
    return welt.node_tree.nodes["Background"]



def _exr_kanalnamen(pfad) -> list[str]:
    """Die Kanalnamen einer EXR aus ihrem Kopf lesen — ohne Fremdbibliothek.

    Reine Diagnose fuer den Report: `aiimaging.bildlesen` sucht den Tiefenkanal nach
    Namen, und Multilayer-EXR benennt ihn anders als eine einkanalige Datei. Die Namen
    gehoeren darum in den Report — sonst kostet jede Formataenderung einen weiteren
    Rundlauf zur HomeStation.
    """
    try:
        roh = Path(pfad).read_bytes()
        i = roh.index(b"chlist", roh.index(b"channels")) + len(b"chlist") + 1 + 4
        namen = []
        while i < len(roh) and roh[i] != 0 and len(namen) < 64:
            ende = roh.index(b"\x00", i)
            namen.append(roh[i:ende].decode("utf-8", "replace"))
            i = ende + 1 + 16
        return namen
    except Exception as e:                                # noqa: BLE001 — reine Diagnose
        return [f"<nicht lesbar: {type(e).__name__}>"]


def _api_befund(knoten) -> str:
    """Die tatsaechlich vorhandene API eines Knotens als Text.

    Wird nur im Fehlerfall gerufen. Der Grund: Ein Rundlauf zur HomeStation kostet den
    Owner einen Handgriff, also soll ein Fehlschlag mehr zurueckbringen als einen
    Traceback. Blender 5.x hat den File-Output-Knoten mehrfach umgebaut
    (`base_path` -> `directory`/`file_name`, `file_slots` -> `file_output_items`), und
    Raten hat hier schon zwei Rundlaeufe gekostet.
    """
    felder = sorted(a for a in dir(knoten) if not a.startswith("_"))
    zeilen = [f"API-Befund fuer {type(knoten).__name__}:", f"  Attribute: {', '.join(felder)}"]
    for name in ("file_slots", "file_output_items", "layer_slots"):
        s = getattr(knoten, name, None)
        if s is not None:
            zeilen.append(f"  {name}: {type(s).__name__}, "
                          f"Methoden {sorted(m for m in dir(s) if not m.startswith('_'))}")
    try:
        zeilen.append(f"  Eingaenge: {[e.name for e in knoten.inputs]}")
    except Exception:
        pass
    zeilen.append(f"  Blender: {bpy.app.version_string}")
    return "\n".join(zeilen)


def _compositor_auf_tiefe(out_dir: Path) -> str:
    """View-Layer-Z-Pass über den Compositor als 32-Bit-EXR ausgeben.

    Der Umweg über den Compositor ist der Grund, warum hier volles Blender nötig ist und
    Cycles allein nicht genügt: `use_pass_z` liefert die Tiefe erst über einen
    Node-Graph als Datei mit echten Meterwerten.
    """
    szene = bpy.context.scene
    szene.view_layers[0].use_pass_z = True
    baum = _kompositor_baum(szene)
    baum.nodes.clear()

    render_layer = baum.nodes.new("CompositorNodeRLayers")
    ausgabe = baum.nodes.new("CompositorNodeOutputFile")

    # Ausgabeort — Blender 5.0 hat `base_path` in `directory` + `file_name` getrennt.
    # Belegt auf der HomeStation (auf-20260818-02): AttributeError auf `base_path`.
    if hasattr(ausgabe, "base_path"):                     # <= 4.x
        ausgabe.base_path = str(out_dir)
    else:                                                 # 5.x
        ausgabe.directory = str(out_dir)
        ausgabe.file_name = "tiefe_"

    # Dateiformat — Blender 5.2 laesst am File-Output-Knoten NUR noch OPEN_EXR_MULTILAYER
    # zu; das einfache OPEN_EXR ist dort aus der Auswahl verschwunden. Belegt durch den
    # API-Befund aus auf-20260818-03: enum "OPEN_EXR" not found in ('OPEN_EXR_MULTILAYER').
    # Die Auswahl wird darum nicht geraten, sondern am Knoten selbst erfragt.
    erlaubte = {e.identifier for e in
                ausgabe.format.bl_rna.properties["file_format"].enum_items}
    ausgabe.format.file_format = ("OPEN_EXR" if "OPEN_EXR" in erlaubte
                                  else "OPEN_EXR_MULTILAYER")
    ausgabe.format.color_depth = "32"
    # OPEN_EXR kennt in dieser Einstellung nur RGB/RGBA. Blender schreibt die Tiefe aber
    # als EINEN Kanal namens "V" in die Datei — nachgemessen 2026-08-18 am erzeugten
    # Header. Der frühere Kommentar behauptete hier drei Kanaele und einen "R"-Kanal; das
    # war falsch und stand seit Phase 1 so da. Wer die EXR von aussen liest, muss nach "V"
    # suchen, nicht nach "R" (siehe `aiimaging.bildlesen`, das eine Vorrangliste benutzt).
    ausgabe.format.color_mode = "RGB"

    # Eingangsslot — `file_slots` heisst ab 5.0 `file_output_items`, und der Name eines
    # Eintrags steht dort unter `.name` statt unter `.path`. Weil die genaue Signatur von
    # `new()` sich zwischen den Fassungen unterscheidet, wird sie NICHT geraten: Es werden
    # mehrere bekannte Aufrufformen versucht, und schlaegt alles fehl, meldet der Runner
    # die tatsaechlich vorhandene API zurueck (siehe `_api_befund`) — ein Fehlschlag soll
    # Fakten liefern, nicht nur einen Traceback.
    slot_name = "tiefe_"
    sammlung = getattr(ausgabe, "file_slots", None)
    if sammlung is None:
        sammlung = getattr(ausgabe, "file_output_items", None)
    if sammlung is None:
        raise RuntimeError("Weder file_slots noch file_output_items: " + _api_befund(ausgabe))

    try:
        sammlung.clear()
    except Exception:                                     # manche Fassungen kennen kein clear()
        pass

    letzter = None
    for versuch in (lambda: sammlung.new(slot_name),
                    lambda: sammlung.new(name=slot_name),
                    lambda: sammlung.new("COLOR", slot_name),
                    lambda: sammlung.new()):
        try:
            versuch()
            letzter = None
            break
        except Exception as e:                            # noqa: BLE001 — naechste Form probieren
            letzter = e
    if letzter is not None:
        raise RuntimeError(f"Eingangsslot nicht anlegbar ({letzter}). {_api_befund(ausgabe)}")

    # Der Eingang heisst je nach Fassung wie der Slot oder schlicht "Image".
    ziel = ausgabe.inputs.get(slot_name) or (ausgabe.inputs[0] if len(ausgabe.inputs) else None)
    if ziel is None:
        raise RuntimeError("Kein Eingang am File-Output-Knoten. " + _api_befund(ausgabe))
    baum.links.new(render_layer.outputs["Depth"], ziel)
    return ausgabe.format.file_format


def _tiefe_normalisieren(exr: Path, ziel_png: Path) -> dict:
    """32-Bit-Meter-EXR → 16-Bit-Graustufen-PNG, nah = hell.

    Warum nicht der `Normalize`-Node im Compositor
    ----------------------------------------------
    Er würde über *alle* Pixel normalisieren, also auch über den Hintergrund mit seinen
    ~1e10 Metern. Das Gebäude landete dann in den untersten Promille des Wertebereichs
    und wäre gleichmässig schwarz. Deshalb wird hier ausserhalb des Renderns gerechnet,
    mit einer ausdrücklichen Hintergrundschranke.

    Warum 16 Bit
    ------------
    8 Bit teilen die Bautiefe in 256 Stufen. Bei einem 30 m tiefen Bild ist eine Stufe
    12 cm — sichtbare Terrassen auf jeder schrägen Fläche. 16 Bit liefern 65 536 Stufen.

    Returns:
        Die Normalisierung als Dictionary: Ohne `min_m`/`max_m` ist das PNG nicht mehr in
        Meter zurückzurechnen, und genau das braucht die Geometrie-QA.
    """
    import numpy as np

    quelle = bpy.data.images.load(str(exr))
    # Non-Color: Die Zahlen im EXR sind Meter, keine Farben. Ohne diesen Schalter dürfte
    # die Farbverwaltung sie unterwegs umrechnen.
    quelle.colorspace_settings.name = "Non-Color"
    breite, hoehe = quelle.size

    roh = np.empty(breite * hoehe * 4, dtype=np.float32)
    quelle.pixels.foreach_get(roh)
    # `img.pixels` liefert IMMER RGBA, unabhaengig davon, wieviele Kanaele in der Datei
    # stehen: Blender vervielfacht den einen "V"-Kanal auf R=G=B. Darum ist jeder vierte
    # Wert ab 0 richtig — nicht weil die Datei einen R-Kanal haette.
    tiefe = roh[0::4]

    gueltig = np.isfinite(tiefe) & (tiefe > 0.0) & (tiefe < HINTERGRUND_AB_M)
    if not gueltig.any():
        raise RuntimeError("Tiefenbild enthält keinen einzigen Geometriepixel")

    min_m = float(tiefe[gueltig].min())
    max_m = float(tiefe[gueltig].max())
    spanne = (max_m - min_m) or 1.0                     # eine ebene Fläche frontal: Spanne 0

    grau = np.zeros_like(tiefe)
    # nah = hell (ControlNet-Konvention). Der Hintergrund bleibt 0.0 — unendlich fern ist
    # der Grenzfall von "dunkel", nicht ein eigener Sonderfall.
    grau[gueltig] = 1.0 - (tiefe[gueltig] - min_m) / spanne

    ziel_puffer = np.empty(breite * hoehe * 4, dtype=np.float32)
    ziel_puffer[0::4] = ziel_puffer[1::4] = ziel_puffer[2::4] = grau
    ziel_puffer[3::4] = 1.0

    bild = bpy.data.images.new("tiefe_norm", width=breite, height=hoehe, float_buffer=True)
    bild.colorspace_settings.name = "Non-Color"          # sonst schriebe Blender sRGB-kodiert
    bild.pixels.foreach_set(ziel_puffer)

    szene = bpy.context.scene
    einst = szene.render.image_settings
    einst.file_format = "PNG"
    einst.color_mode = "BW"
    einst.color_depth = "16"
    bild.save_render(str(ziel_png), scene=szene)

    return {
        "min_m": min_m,
        "max_m": max_m,
        "konvention": ("nah = hell (ControlNet); Hintergrund = 0. Das entfernteste "
                       "Geometriepixel liegt ebenfalls bei 0 und ist im PNG nicht vom "
                       "Hintergrund zu unterscheiden — wer die Silhouette exakt braucht, "
                       "nimmt die EXR."),
        "hintergrund_grauwert": 0.0,
        "rueckrechnung": "meter = max_m - grau * (max_m - min_m), grau in 0..1",
        "n_geometriepixel": int(gueltig.sum()),
    }


# --------------------------------------------------------------------------------------
# Ablauf
# --------------------------------------------------------------------------------------

def _renderparameter_setzen(a) -> None:
    """Engine, Sampling und Farbverwaltung — für beide Durchgänge gemeinsam."""
    szene = bpy.context.scene
    szene.render.engine = "CYCLES"
    szene.cycles.samples = a.samples
    szene.cycles.device = "CPU"                          # in dieser Umgebung gibt es keine GPU
    szene.render.resolution_x = szene.render.resolution_y = a.aufloesung
    szene.render.resolution_percentage = 100
    # Standard statt AgX: AgX ist ein Filmlook mit weicher Kompression der Lichter. Für ein
    # Bild, das gleich wieder maschinell ausgewertet wird, ist eine nachvollziehbare
    # Zuordnung von Renderwert zu Bildwert wichtiger als ein schönes Rollover.
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"


def _frisch(pfad: Path, seit: float) -> bool:
    """Wurde diese Datei in DIESEM Lauf geschrieben?

    Blosse Existenz genügt nicht: `out_dir` wird üblicherweise wiederverwendet, und eine
    liegengebliebene Datei aus einem früheren Lauf sähe genauso aus wie ein Erfolg. Die
    Erfolgsmeldung hinge dann an fremden Bytes.
    """
    return pfad.exists() and pfad.stat().st_mtime >= seit


def main() -> int:
    a = _argumente()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    beginn = time.time() - 1.0                           # 1 s Luft für grobe mtime-Auflösung

    _szene_leeren()
    bpy.ops.import_scene.gltf(filepath=a.glb)

    if getattr(a, "rotiere_z_up", False):
        # Quelle war Z-up (glTF verlangt Y-up). Ohne diese Drehung läge der Bau auf der
        # Seite — und Tiefenkarte, Kamera und Geometrie-QA wären still verdreht.
        import mathutils
        dreh = mathutils.Matrix.Rotation(math.radians(90.0), 4, "X")
        for obj in bpy.data.objects:
            if obj.parent is None:
                obj.matrix_world = dreh @ obj.matrix_world

    lo, hi = _bbox_aller_meshes()
    _kamera_setzen(lo, hi)
    mitte = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    spanne = max(hi[i] - lo[i] for i in range(3)) or 1.0

    _renderparameter_setzen(a)
    szene = bpy.context.scene

    # ── Durchgang 1: Beauty + Tiefe ────────────────────────────────────────────────────
    # Umgebungsstärke 0.25 zu Sonnenstärke 2.0: gemessen, nicht geschätzt. Mit 1.0/3.0
    # lag das Bild im Mittel bei 0.83 von 1.0 — durchgehend ausgebrannt, die Fassaden
    # ohne Zeichnung. Die Schattenseite soll dunkel bleiben, ohne zuzulaufen.
    _welt_setzen((0.55, 0.60, 0.68), 0.25)               # kühles, gleichmässiges Umgebungslicht
    _sonne_setzen(mitte, spanne)
    szene.cycles.use_denoising = True                    # 8 Samples auf CPU rauschen sichtbar
    szene.render.image_settings.file_format = "PNG"
    szene.render.image_settings.color_mode = "RGBA"
    szene.render.image_settings.color_depth = "8"
    beauty_png = out_dir / "beauty_.png"
    szene.render.filepath = str(out_dir / "beauty_")

    exr_format = "unbekannt"
    try:
        exr_format = _compositor_auf_tiefe(out_dir)
    except Exception as e:
        # Jeder Fehler im Kompositor-Aufbau soll die tatsaechliche API mitliefern.
        # Blender 5.x hat diesen Bereich mehrfach umgebaut, und jeder Rundlauf zur
        # HomeStation kostet den Owner einen Handgriff — ein Fehlschlag muss darum mehr
        # zurueckbringen als die blosse Meldung, dass etwas fehlt.
        befund = ""
        try:
            szene = bpy.context.scene
            baum = _kompositor_baum(szene)
            knoten = baum.nodes.new("CompositorNodeOutputFile")
            befund = "\n" + _api_befund(knoten)
        except Exception as e2:
            befund = f"\n(API-Befund nicht erhebbar: {e2})"
        raise RuntimeError(f"Kompositor-Aufbau gescheitert: {e}{befund}") from e
    bpy.ops.render.render(write_still=not a.ohne_beauty)

    exr_kandidaten = [p for p in sorted(out_dir.glob("tiefe_*.exr")) if _frisch(p, beginn)]
    exr = exr_kandidaten[0] if exr_kandidaten else None

    # ── Durchgang 2: Material-ID ──────────────────────────────────────────────────────
    tabelle: list[dict] = []
    n_materialien = len(bpy.data.materials)
    material_id_png = out_dir / "material_id.png"
    if not a.ohne_material_id:
        tabelle, n_materialien = _material_id_zuweisen()
        # Der Compositor darf hier nicht mitlaufen: Er schriebe die (unveränderte) Tiefe
        # ein zweites Mal über dieselbe Datei.
        _kompositor_abschalten(szene)
        _welt_setzen((0.0, 0.0, 0.0), 0.0)               # schwarzer Grund, Farbwert 0 = "nichts"
        # Ein Sample, kein Denoiser, keine Bounces: Jedes Pixel trägt genau die gesetzte
        # Farbe. Mehr Samples würden Kanten mischen und neue, falsche IDs erfinden.
        szene.cycles.samples = 1
        szene.cycles.use_denoising = False
        szene.cycles.max_bounces = 0
        szene.cycles.transparent_max_bounces = 0
        # Rekonstruktionsfilter aus: Bei Breite 1.5 darf ein Sample in ein Nachbarpixel
        # fallen und trägt dort eine fremde ID ein. Bei 0.0 bleibt jedes Sample in seinem
        # Pixel, die Kanten sitzen hart.
        szene.render.filter_size = 0.0
        # Dithering aus. Es streut vor der 8-Bit-Quantisierung Rauschen ein — für ein
        # Foto richtig (es verhindert Banding), für eine Kennung falsch: Gemessen wurden
        # damit 19 statt 5 Farben, weil jede ID um ±1 zerfaserte und selbst der schwarze
        # Grund zwischen 0 und 1 sprang.
        szene.render.dither_intensity = 0.0
        szene.render.filepath = str(out_dir / "material_id")
        bpy.ops.render.render(write_still=True)

    # ── Normalisierte Tiefenkarte ─────────────────────────────────────────────────────
    depth_png = out_dir / "tiefe_norm.png"
    normalisierung = None
    fehler = None
    if exr is not None:
        try:
            normalisierung = _tiefe_normalisieren(exr, depth_png)
        except Exception as e:                           # Fehler als Report, nicht als Traceback
            fehler = f"Tiefen-Normalisierung fehlgeschlagen: {type(e).__name__}: {e}"
    else:
        fehler = "Compositor schrieb keine EXR"

    erwartet = {
        "depth_exr": exr if exr is not None else None,
        "depth_png": depth_png if normalisierung is not None else None,
        "beauty_png": beauty_png if not a.ohne_beauty else None,
        "material_id_png": material_id_png if not a.ohne_material_id else None,
    }
    fehlend = [name for name, pfad in erwartet.items()
               if pfad is not None and not _frisch(Path(pfad), beginn)]
    if fehlend and fehler is None:
        fehler = "nicht geschrieben: " + ", ".join(sorted(fehlend))

    report = {
        # Bestandsfelder — Bedeutung unverändert, damit seams.py und die Tests tragen.
        "status": "ok" if fehler is None else "error",
        "depth_exr": str(exr) if exr is not None else None,
        "bbox": [lo, hi],
        "bbox_size_m": [hi[i] - lo[i] for i in range(3)],
        "n_meshes": sum(1 for o in bpy.data.objects if o.type == "MESH"),
        "aufloesung": a.aufloesung,
        "rotiert": bool(getattr(a, "rotiere_z_up", False)),
        "blender": bpy.app.version_string,
        "error": fehler,
        # Neu mit dem Multipass.
        "beauty_png": str(beauty_png) if _frisch(beauty_png, beginn) else None,
        "material_id_png": str(material_id_png) if _frisch(material_id_png, beginn) else None,
        "depth_png": str(depth_png) if _frisch(depth_png, beginn) else None,
        "n_materialien": n_materialien,
        "material_id_tabelle": tabelle,
        "material_id_quelle": sorted({e["quelle"] for e in tabelle}) or None,
        "depth_normalisierung": normalisierung,
        "samples": a.samples,
        # Diagnose fuer den externen Leser: Multilayer-EXR benennt Kanaele anders als eine
        # einkanalige Datei ("tiefe_.V" statt "V"), und `aiimaging.bildlesen` sucht nach
        # Namen. Ohne diese Angabe kostete jede Formataenderung einen weiteren Rundlauf.
        "depth_exr_kanaele": _exr_kanalnamen(exr) if exr is not None else [],
        "depth_exr_format": exr_format,
    }
    (out_dir / "blender-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("BLENDER_REPORT " + json.dumps(report, ensure_ascii=False))
    return 0 if fehler is None else 1


if __name__ == "__main__":
    sys.exit(main())
