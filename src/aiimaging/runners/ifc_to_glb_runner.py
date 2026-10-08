#!/usr/bin/env python3
"""RUNNER — IFC (IFC4 oder IFC2X3) → glb. Läuft im `.venv-ifc`, nie im Produkt-Environment.

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


#: IFC-Produkttypen, die **keine gebaute Substanz** sind und darum nicht in die glb gehören.
#:
#: Am Gerät gefunden (`auf-20260822-32`, 21.08.2026), als Befund *neben* dem eigentlichen
#: Auftrag: Die aus `make_test_ifc.py --raeume` erzeugte glb trägt sieben Meshes — ein
#: `IfcSlab`, vier `IfcWall` und **zwei `IfcSpace`**. Ein `IfcSpace` ist ein Luftvolumen,
#: und als Mesh ist es ein **massiver Quader**. Eine Innenaufnahme steht mitten darin:
#: Die Tiefenkarte sähe eine graue Fläche unmittelbar vor dem Objektiv, und zwar in jedem
#: Raum, in dem je gerendert wird.
#:
#: Jeder Eintrag mit seinem eigenen Grund, denn eine Sammelbegründung lädt zum
#: Weiterwachsen ein:
#:
#: * ``IfcSpace`` — Luft. Die Zone, in der sich jemand aufhält; kein Bauteil.
#: * ``IfcOpeningElement`` — der **Ausschnitt**, nicht das Bauteil. Er wird von der Wand
#:   abgezogen; wer ihn wieder hinzufügt, füllt jedes Fenster und jede Tür mit einem
#:   Block. Bei unserer Testgeometrie kommt er nicht vor, in jeder echten IFC schon.
#: * ``IfcVirtualElement`` — laut Norm ausdrücklich eine nicht-körperliche Grenze.
#: * ``IfcAnnotation``, ``IfcGrid`` — Zeichnungshilfen. Achsen und Beschriftungen sind
#:   nichts, was ein Bildmodell abbilden soll.
#:
#: **Weggelassen wird nichts stillschweigend:** Der Report zählt, was übersprungen wurde,
#: je Typ. Eine Konversion, die Geometrie verschluckt und schweigt, ist genau der Fehler,
#: gegen den dieses Projekt antritt.
NICHT_GEBAUTE_SUBSTANZ = (
    "IfcSpace",
    "IfcOpeningElement",
    "IfcVirtualElement",
    "IfcAnnotation",
    "IfcGrid",
)


#: IFC-Typen, die **Gelände** sind und nicht Bauwerk.
#:
#: **Warum diese Liste hier steht und nicht importiert wird.** Der Runner läuft im
#: ``.venv-ifc`` und darf sich nicht darauf verlassen, das Produkt-Paket zu erreichen —
#: das ist die Prozessgrenze aus Regel 2. Eine Liste an zwei Stellen ist an einer davon
#: bereits falsch; darum prüft ``tests/test_bauwerksbox.py``, dass sie mit
#: ``aiimaging.maske.GELAENDE_MUSTER`` zusammenpasst. **Der Test ersetzt den Import, den
#: es nicht geben darf.**
GELAENDE_TYPEN = ("IfcSite",)


def ist_gelaende_typ(typname: str) -> bool:
    """Ist dieser IFC-Typ Gelände? — dieselbe Frage wie die Maskenregel, eine Ebene früher."""
    return str(typname) in GELAENDE_TYPEN


def ist_gebaute_substanz(typname: str) -> bool:
    """Gehört ein IFC-Typ in die glb? — dieselbe Frage ohne ``ifcopenshell``.

    Die Konversion selbst fragt mit ``produkt.is_a(...)``, weil das die Vererbung kennt.
    Diese Funktion beantwortet dieselbe Frage für einen blossen Typnamen — und ist damit
    **ohne die Bibliothek prüfbar**, also auch dort, wo es kein `.venv-ifc` gibt.
    """
    return str(typname) not in NICHT_GEBAUTE_SUBSTANZ


#: Wieviel vom IFC-Namen in den Knotennamen darf.
#:
#: **Blender kuerzt Objektnamen bei 63 Byte.** Steht der Name hinten, faellt er dort weg —
#: und mit ihm die einzige Auskunft, die den glb-Export ueberlebt. Er steht darum VOR der
#: GlobalId, und was ueberlaeuft, ist die GlobalId und nicht der Name.
NAME_HOECHSTENS = 24


def _knotenname(produkt) -> str:
    """``IfcSlab_Gelaende_2eYuY4S8…`` — Typ, **Name**, GlobalId.

    Warum der Name mit muss
    -----------------------
    **Gemessen am 26.08.2026.** Der Knotenname war bis dahin ``f"{typ}_{guid}"``, und
    damit ging der IFC-Name beim Export verloren. Auf der Blender-Seite entscheidet aber
    genau er darueber, was Gelaende ist: ``aiimaging.maske.ist_gelaende`` liest den
    **Objektnamen**, weil nach dem glb-Export kein IFC-Typ mehr dasteht.

    Die Folge war an der Testgeometrie mit Gelaende zu sehen: Die Gelaendeplatte ist ein
    ``IfcSlab`` mit dem Namen ``Gelaende`` — der Typfilter dieses Runners
    (``GELAENDE_TYPEN = ("IfcSite",)``) fasst sie nicht, weil die ``IfcSite`` selbst gar
    keine Geometrie traegt, und die Namensregel drueben konnte sie nicht fassen, weil der
    Name nicht mehr dastand. **Beide Filter waren blind, jeder aus einem anderen Grund.**

    Ergebnis: ``bbox_bauwerk`` war gleich der Szenenbox (20 x 20 m statt 8 x 5 m), und der
    Rahmungsriegel des Abholers sah einen Breitenanteil von 1.0, wo 0.4 richtig gewesen
    waere. *Er war damit auf genau dem Fall wirkungslos, fuer den er gebaut wurde.*

    Ein fehlender oder leerer Name ergibt dieselbe Form wie frueher — dann ist nichts zu
    ueberliefern.
    """
    typ = produkt.is_a()
    guid = getattr(produkt, "GlobalId", "") or ""
    roh = (getattr(produkt, "Name", None) or "").strip()
    if not roh:
        return f"{typ}_{guid}"
    # Leerzeichen zu Unterstrichen: `ist_gelaende` zerlegt ohnehin an beidem, aber ein
    # Objektname mit Leerzeichen ist in Blender unhandlich. Sonst bleibt der Name, wie er
    # ist — wer ihn beschneidet, entscheidet ueber eine Regel, die anderswo steht.
    name = "_".join(roh.split())[:NAME_HOECHSTENS]
    return f"{typ}_{name}_{guid}"


#: Woher ein Material der glb stammt. Nur diese eine Quelle kommt hinein.
QUELLE_STIL = "ifc_surface_style"


def ist_stil_aus_der_datei(instance_id) -> bool:
    """Stammt ein Material, das ifcopenshell liefert, aus der Datei — oder von ihm selbst?

    **Gemessen am 08.10.2026** an ``make_test_ifc.py --stile`` (ifcopenshell 0.8.5): Ein
    Bauteil mit ``IfcStyledItem`` bekommt ein Material, dessen ``instance_id`` auf den
    ``IfcSurfaceStyle`` der Datei zeigt (Name «Sichtbeton», Farbe aus der Datei). Ein
    Bauteil **ohne** Stil bekommt trotzdem eines — ``instance_id`` 0, als Name nur die
    Bauteilart («IfcWall», «IfcSlab»), als Farbe ein Grau, das ifcopenshell je Art
    vorgibt (``auf-20261007-259``: Wand 0,9, Decke 0,4, sonst 0,7).

    Diese Vorgaben gehören **nicht** in die glb: Sie sähen nach Modellinformation aus und
    wären keine. Darum entscheidet allein die Kennung.
    """
    try:
        return int(instance_id) > 0
    except (TypeError, ValueError):
        return False


def srgb_zu_linear(k: float) -> float:
    """Eine Farbkomponente von sRGB nach linear — glTF ``baseColorFactor`` ist linear.

    **Angenommen, nicht gemessen:** IFC legt den Farbraum von ``IfcColourRGB`` nicht fest;
    die verbreiteten Erzeuger schreiben die Werte, die man am Bildschirm sieht, also sRGB.
    Ohne Umrechnung käme jede Farbe in Blender zu hell an.
    """
    k = min(max(float(k), 0.0), 1.0)
    return k / 12.92 if k <= 0.04045 else ((k + 0.055) / 1.055) ** 2.4


def _aufrufen(wert):
    """ifcopenshell 0.8 liefert manche Angaben als Methode, ältere als Wert."""
    return wert() if callable(wert) else wert


def _stil_des_materials(modell, material) -> dict | None:
    """Name und Farbe eines Materials — **nur**, wenn es aus der Datei stammt."""
    kennung = _aufrufen(getattr(material, "instance_id", 0))
    if not ist_stil_aus_der_datei(kennung):
        return None
    name = None
    try:
        entitaet = modell.by_id(int(kennung))
        name = getattr(entitaet, "Name", None)
    except Exception:                                 # noqa: BLE001 — Name ist Beiwerk
        pass
    farbe = _aufrufen(getattr(material, "diffuse", None))
    try:
        rgb = [float(_aufrufen(getattr(farbe, k))) for k in ("r", "g", "b")]
    except Exception:                                 # noqa: BLE001
        try:
            rgb = [float(k) for k in _aufrufen(getattr(farbe, "components"))][:3]
        except Exception:                             # noqa: BLE001
            return None                               # ein Stil ohne lesbare Farbe
    durchsicht = _aufrufen(getattr(material, "transparency", None))
    try:
        durchsicht = float(durchsicht)
        durchsicht = None if durchsicht != durchsicht or durchsicht <= 0.0 else durchsicht
    except (TypeError, ValueError):
        durchsicht = None
    return {"kennung": int(kennung),
            "name": (name or _aufrufen(getattr(material, "name", "")) or f"Stil-{kennung}"),
            "farbe_srgb": [round(k, 4) for k in rgb],
            "durchsicht": durchsicht}


def _glb_material(stil: dict):
    """Das glTF-Material zu einem Stil — **deckend**, auch wenn die Datei Durchsicht nennt.

    Warum deckend: Blender liest im Tiefendurchgang nur Flächen, deren Deckkraft über der
    Alpha-Schwelle liegt. Ein Fenster mit Durchsicht 0,8 verschwände dann aus der
    Soll-Tiefe, und die Prüfung gegen die Geometrie urteilte gegen ein Haus ohne Fenster.
    Was die Datei an Durchsicht nennt, steht im Bericht und nicht in der glb.
    """
    import trimesh                                    # noqa: PLC0415 — nur in diesem Prozess
    farbe = [srgb_zu_linear(k) for k in stil["farbe_srgb"]] + [1.0]
    return trimesh.visual.material.PBRMaterial(
        name=stil["name"], baseColorFactor=farbe, metallicFactor=0.0,
        roughnessFactor=1.0)


def ifc_to_glb(ifc_path: str, glb_path: str) -> dict:
    """Konvertiert IFC (IFC4 oder IFC2X3) → glb (Y-up) und liefert einen Report.

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
    # Die ZWEITE Huellbox: nur gebaute Substanz, ohne Gelaende. Siehe unten.
    n_bauwerk = 0
    bau_min = bau_max = None
    uebersprungen: dict[str, int] = {}
    stile_gesehen: dict[str, dict] = {}
    n_mit_stil = n_ohne_stil = 0
    for produkt in modell.by_type("IfcProduct"):
        if not getattr(produkt, "Representation", None):
            continue
        # `is_a(name)` und nicht `is_a() in ...`: Es kennt die Vererbung, und ein
        # Untertyp von IfcSpace ist genauso wenig gebaute Substanz wie IfcSpace selbst.
        nicht_substanz = next(
            (t for t in NICHT_GEBAUTE_SUBSTANZ if produkt.is_a(t)), None)
        if nicht_substanz is not None:
            uebersprungen[produkt.is_a()] = uebersprungen.get(produkt.is_a(), 0) + 1
            continue
        try:
            form = ifcopenshell.geom.create_shape(einst, produkt)
        except Exception:
            continue                                  # nicht-geometrische Produkte
        ecken = np.asarray(form.geometry.verts, dtype="float64").reshape(-1, 3)
        flaechen = np.asarray(form.geometry.faces, dtype="int64").reshape(-1, 3)
        if len(ecken) == 0 or len(flaechen) == 0:
            continue
        # DIE STILE DER DATEI, UND NUR SIE (F6, 08.10.2026). Je Flaeche sagt
        # `material_ids`, welches Material sie traegt. Ein Bauteil mit nur einem Material
        # bleibt EIN Mesh mit denselben Ecken wie zuvor; erst ein Bauteil mit mehreren
        # wird je Material geteilt — die Geometrie bleibt dabei dieselbe, nur aufgeteilt.
        stile = [_stil_des_materials(modell, mat) for mat in form.geometry.materials]
        zuordnung = np.asarray(form.geometry.material_ids, dtype="int64").reshape(-1)
        if len(zuordnung) != len(flaechen):
            zuordnung = np.full(len(flaechen), -1, dtype="int64")
        gruppen = sorted(set(zuordnung.tolist()))
        name = _knotenname(produkt)
        netz = trimesh.Trimesh(vertices=ecken, faces=flaechen, process=False)
        stilnamen: set[str] = set()
        for teil, gruppe in enumerate(gruppen):
            stil = stile[gruppe] if 0 <= gruppe < len(stile) else None
            stueck = (netz if len(gruppen) == 1
                      else netz.submesh([np.nonzero(zuordnung == gruppe)[0]],
                                        append=True))
            if stil is not None:
                stueck.visual = trimesh.visual.TextureVisuals(material=_glb_material(stil))
                stile_gesehen.setdefault(stil["name"], {
                    "name": stil["name"], "farbe_srgb": stil["farbe_srgb"],
                    "durchsicht_in_der_datei": stil["durchsicht"], "n_bauteile": 0})
                stilnamen.add(stil["name"])
            szene.add_geometry(stueck, node_name=name if teil == 0 else f"{name}_{teil}")
        for stilname in stilnamen:
            stile_gesehen[stilname]["n_bauteile"] += 1
        if stilnamen:
            n_mit_stil += 1
        else:
            n_ohne_stil += 1
        n_elemente += 1
        n_dreiecke += len(flaechen)
        # Der groesste gemessene Fehler dieser Woche: Die Kamera rahmt die Huellbox der
        # GANZEN SZENE, die Maske deckt nur das Bauwerk. Auf einer Platte mit zehnfacher
        # Grundflaeche fuellt das Bauwerk dann 1.9 % des Bildes, und das Geometrie-Tor
        # kann rechnerisch nicht bestehen (auf-13/auf-35). Ohne diese zweite Box ist der
        # Bruch nicht einmal FESTSTELLBAR, geschweige denn behebbar.
        if not ist_gelaende_typ(produkt.is_a()):
            n_bauwerk += 1
            unten = ecken.min(axis=0)
            oben = ecken.max(axis=0)
            bau_min = unten if bau_min is None else np.minimum(bau_min, unten)
            bau_max = oben if bau_max is None else np.maximum(bau_max, oben)

    if n_elemente == 0:
        return {
            "status": "error",
            "error": (
                "keine Geometrie im IFC"
                + (f" — {sum(uebersprungen.values())} Produkte waren zwar da, sind aber "
                   f"keine gebaute Substanz ({', '.join(sorted(uebersprungen))}) und "
                   f"wurden übersprungen. Eine Datei, die nur Räume oder nur Achsen "
                   f"enthält, ergibt kein Bauwerk."
                   if uebersprungen else ".")
            ),
            "glb_path": None,
            "n_uebersprungen": sum(uebersprungen.values()),
            "uebersprungen": dict(sorted(uebersprungen.items())),
        }

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
        # Die Huellbox der gebauten Substanz allein — ``None``, wenn ausser Gelaende
        # nichts da war. NICHT die Szenenbox als Ersatz: Das waere genau die
        # Verwechslung, gegen die dieses Feld gebaut ist.
        "bbox_bauwerk": (None if bau_min is None
                         else [bau_min.tolist(), bau_max.tolist()]),
        "n_bauwerk": n_bauwerk,
        "bbox_bauwerk_note": (
            "Nur gebaute Substanz, ohne " + ", ".join(GELAENDE_TYPEN) + "; in nativen "
            "IFC-Metern (Z oben) wie 'bbox'. Die Kamera soll DIESE Box rahmen, gemessen "
            "wird ohnehin nur das Bauwerk."),
        "n_elements": n_elemente,
        "n_triangles": n_dreiecke,
        # Was NICHT in der glb steht, und warum. Ohne diese beiden Felder wäre der
        # Ausschluss unsichtbar — und ein unsichtbarer Ausschluss ist ein Datenverlust,
        # auch wenn er richtig ist.
        "n_uebersprungen": sum(uebersprungen.values()),
        "uebersprungen": dict(sorted(uebersprungen.items())),
        "uebersprungen_grund": (
            "Kein Bauteil, sondern Luft, Ausschnitt oder Zeichnungshilfe — siehe "
            "NICHT_GEBAUTE_SUBSTANZ. Ein IfcSpace als Mesh ist ein massiver Quader; "
            "eine Innenaufnahme stünde mitten darin."
        ),
        # WAS AN MATERIAL IN DER GLB STEHT, und woher (F6, 08.10.2026). Leer heisst: Die
        # Datei traegt keine Oberflaechenstile — NICHT, dass sie verloren gingen.
        "materialien": sorted(stile_gesehen.values(), key=lambda e: e["name"]),
        "materialien_quelle": QUELLE_STIL,
        "n_bauteile_mit_stil": n_mit_stil,
        "n_bauteile_ohne_stil": n_ohne_stil,
        "materialien_note": (
            "Nur IfcSurfaceStyle aus der Datei, Farbe von sRGB nach linear umgerechnet "
            "(angenommen), immer deckend. Bauteile ohne Stil bleiben ohne Material — die "
            "Grautoene, die ifcopenshell sonst je Bauteilart einsetzt, stammen nicht aus dem "
            "Modell und stehen nicht in der glb. Durchsicht aus der Datei steht nur hier."),
        "bbox_note": "bbox in nativen IFC-Metern (Z oben); die glb selbst ist Y-up",
        "error": None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IFC → glb (Y-up). Läuft im .venv-ifc.")
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
