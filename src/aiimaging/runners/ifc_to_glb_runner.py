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


#: Klassen, die nur dann Gelände sind, wenn die Datei es sagt — mit ``PredefinedType``.
#:
#: **Anlass (Geräteprobe R56, 23.10.2026):** Die Bestellseite liefert ihre Geländefläche ab
#: R57 als ``IfcGeographicElement`` mit ``PredefinedType .TERRAIN.`` (IFC4). Dieselbe Klasse
#: trägt aber auch Bäume — die Klasse allein bleibt darum Umfeld (``maske.UMFELD_KLASSEN``);
#: Gelände ist sie erst mit ``TERRAIN``, oder (IFC2X3 kennt kein ``PredefinedType``, und
#: ``USERDEFINED`` verweist auf ``ObjectType``) mit einem Geländewort in ``ObjectType``
#: oder ``Name`` (:data:`GELAENDE_OBJEKTWOERTER`).
GELAENDE_VORDEFINIERT = {"IfcGeographicElement": ("TERRAIN",)}

#: Geländewörter für ``ObjectType``/``Name`` einer Klasse aus :data:`GELAENDE_VORDEFINIERT`.
#: Eine Teilmenge von ``aiimaging.maske.GELAENDE_WOERTER`` — geprüft in
#: ``tests/test_ifc_terrain_r56.py`` statt importiert (Prozessgrenze). ``site`` fehlt mit
#: Absicht: An einem ``IfcGeographicElement`` sagt es nichts über Boden.
GELAENDE_OBJEKTWOERTER = ("terrain", "gelaende", "gelände", "gelaendeflaeche", "toposolid")

#: Umlaute werden vor dem Vergleich umgeschrieben: «Geländefläche» → ``gelaendeflaeche``. So
#: trifft die Schreibweise mit Umlauten, ohne dass die Wortliste der Maske wächst.
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})


def ist_gelaende_element(typname: str, predefined=None, objekttyp=None, name=None) -> bool:
    """Ist dieses Bauteil Gelände? — der Typ (:data:`GELAENDE_TYPEN`), oder eine Klasse aus
    :data:`GELAENDE_VORDEFINIERT` mit ``TERRAIN`` bzw. einem Geländewort. Ohne ifcopenshell."""
    typ = str(typname)
    if ist_gelaende_typ(typ):
        return True
    vordef = GELAENDE_VORDEFINIERT.get(typ)
    if not vordef:
        return False
    if str(predefined or "").strip().upper() in vordef:
        return True
    import re
    for text in (objekttyp, name):
        woerter = re.split(r"[\s_\-.,;:/\\()\[\]]+", str(text or "").strip().lower())
        if any(w in GELAENDE_OBJEKTWOERTER or w.translate(_UMLAUTE) in GELAENDE_OBJEKTWOERTER
               or w.upper() in vordef for w in woerter if w):
            return True
    return False


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
    Die Durchsicht der Datei kommt seit dem 22.10.2026 als **Durchlass**
    (``KHR_materials_transmission``) hinein, nicht als Alpha — :func:`glb_nachtragen`.
    """
    import trimesh                                    # noqa: PLC0415 — nur in diesem Prozess
    farbe = [srgb_zu_linear(k) for k in stil["farbe_srgb"]] + [1.0]
    return trimesh.visual.material.PBRMaterial(
        name=stil["name"], baseColorFactor=farbe, metallicFactor=0.0,
        roughnessFactor=1.0)


#: Vordefinierte Typen, die ein Bauteil zum Dach machen — dieselben wie
#: ``aiimaging.materialwahl.DACH_TYPEN`` (die Probe in ``tests/test_ifc_merkmale.py`` hält
#: beide Listen gleich; ein Import wäre über die Prozessgrenze, siehe ``GELAENDE_TYPEN``).
DACH_TYPEN = ("ROOF", "ROOFING")

#: ``PredefinedType``-Werte, die nichts sagen und darum nicht in die glb gehen.
NICHTSSAGEND = ("NOTDEFINED", "USERDEFINED")

#: Das Bauteil, zu dem ein Teil gehört (``IfcRelAggregates``), und das Merkmal, das der Teil
#: dadurch trägt. Reihenfolge = Vorrang.
GANZES_ZU_MERKMAL = (
    ("IfcRoof", {"kind": "roof"}),
    ("IfcWindow", {"kind": "opening", "openingType": "fenster"}),
    ("IfcDoor", {"kind": "opening", "openingType": "tuer"}),
)


def knoten_merkmale(typ: str, predefined=None, ganzes: str | None = None, *,
                    objekttyp=None, name=None) -> dict:
    """Die ``extras`` eines Knotens der glb — **ohne ifcopenshell** berechnet.

    **Anlass (Mac-Demolauf 22.10.2026, ``auf-20261022-331``):** Nach dem Export steht von
    einem IFC-Bauteil nur noch der Knotenname da. Blender entscheidet daran die Art
    (``aiimaging.materialwahl.art_von``: Präfix ``IfcSlab`` → «boden»). Eine Dachplatte —
    in ArchiCAD- und Revit-Dateien eine ``IfcSlab`` unter einem ``IfcRoof`` — wurde damit
    zum Boden, ein Fensterteil unter einem ``IfcWindow`` zu «uebrige», und ein Gelände, das
    die ``IfcSite`` selbst trägt, fand ``kosmo_szene.gelaende_in_glb`` nicht, weil es nur
    ``extras.role`` liest.

    Darum trägt jeder Knoten, was die IFC über ihn weiss, in derselben Sprache, die die
    KosmoOrbit-glb schon spricht (``kind``, ``openingType``, ``role``) — gelesen von
    ``art_von`` (``kind`` vor dem Namen) und von ``gelaende_in_glb`` (``role``):

    * ``ifc_type`` — immer; ``PredefinedType`` — wenn er etwas sagt;
    * ``kind: roof`` — für ``IfcRoof``, seine Teile und Platten/Bekleidungen mit
      ``ROOF``/``ROOFING``;
    * ``kind: opening`` mit ``openingType`` ``fenster``/``tuer`` — für ``IfcWindow``,
      ``IfcDoor`` und ihre Teile (Türen bleiben damit «uebrige», Entscheid 113);
    * ``role: ground`` — für Gelände-Typen (:data:`GELAENDE_TYPEN`), und seit R56
      (23.10.2026) für ein ``IfcGeographicElement`` mit ``TERRAIN`` oder Geländewort in
      ``objekttyp``/``name`` (:func:`ist_gelaende_element`).

    Die Geometrie ändert das nicht, nur den JSON-Block der glb.
    """
    typ = str(typ)
    merkmale: dict = {"ifc_type": typ}
    vordef = str(predefined or "").strip().upper()
    if vordef and vordef not in NICHTSSAGEND:
        merkmale["PredefinedType"] = vordef
    ganzes_merkmal = next((m for name, m in GANZES_ZU_MERKMAL
                           if typ == name or ganzes == name), None)
    if ganzes_merkmal is not None:
        merkmale.update(ganzes_merkmal)
    elif typ in ("IfcSlab", "IfcCovering") and vordef in DACH_TYPEN:
        merkmale["kind"] = "roof"
    if ganzes and ganzes != typ:
        merkmale["teil_von"] = ganzes
    if ist_gelaende_element(typ, predefined, objekttyp, name):
        merkmale["role"] = "ground"
    return merkmale


def _ganzes_von(produkt) -> str | None:
    """Der Typ des Bauteils, zu dem ``produkt`` als Teil gehört — nur, wenn es eines aus
    :data:`GANZES_ZU_MERKMAL` ist (``IfcRelAggregates``, eine oder mehrere Stufen)."""
    gesucht = tuple(name for name, _ in GANZES_ZU_MERKMAL)
    gesehen = 0
    teil = produkt
    while teil is not None and gesehen < 8:          # Schutz gegen kaputte Zyklen
        gesehen += 1
        oben = None
        for rel in (getattr(teil, "Decomposes", None) or ()):
            if rel.is_a("IfcRelAggregates"):
                oben = rel.RelatingObject
                break
        if oben is None:
            return None
        treffer = next((name for name in gesucht if oben.is_a(name)), None)
        if treffer is not None:
            return treffer
        teil = oben
    return None


#: Die Erweiterung, mit der glTF Durchlass (Glas) beschreibt.
DURCHLASS_ERWEITERUNG = "KHR_materials_transmission"
#: Die höchste Rauheit eines Materials mit Durchlass (Ergebnis 332) — dieselbe Zahl wie
#: ``blender_depth_stage.GLAS_RAUHEIT_HOECHSTENS`` (die Probe hält beide gleich).
GLAS_RAUHEIT_HOECHSTENS = 0.05


def glb_nachtragen(pfad, merkmale_je_knoten: dict, durchlass_je_material: dict) -> dict:
    """``extras`` an Knoten und Durchlass an Materialien in eine fertige glb schreiben.

    Geändert wird **nur der JSON-Block** (neu auf vier Bytes aufgefüllt); der Binärblock
    mit der Geometrie wandert unverändert mit. Standardbibliothek allein — darum ohne
    ifcopenshell prüfbar.

    **Durchlass, aber deckend** (22.10.2026, Ablösung von «Durchsicht nur im Bericht»): Ein
    Material, dessen Stil in der Datei eine Durchsicht nennt, bekommt
    ``KHR_materials_transmission`` mit diesem Wert und bleibt ``alphaMode OPAQUE``. Das ist
    dieselbe Form, in der die KosmoOrbit-glb ihr Glas liefert: Die Tiefe sieht die Scheibe
    weiter als Fläche (sie ist nicht durchsichtig im Sinn von Alpha), das Bild sieht Glas.
    Ohne das kam eine Scheibe aus der IFC als hellgraue Platte an.

    Returns:
        ``{"knoten": n, "materialien": n}`` — wie viele tatsächlich ergänzt wurden.
    """
    import struct as _struct
    from pathlib import Path as _Path
    pfad = _Path(pfad)
    daten = pfad.read_bytes()
    if len(daten) < 20 or daten[:4] != b"glTF":
        raise ValueError("Keine glb (Kopf 'glTF' fehlt).")
    laenge, art = _struct.unpack_from("<II", daten, 12)
    if art != 0x4E4F534A:
        raise ValueError("Der erste Block der glb ist kein JSON.")
    js = json.loads(daten[20:20 + laenge])
    rest = daten[20 + laenge:]
    n_knoten = n_mat = 0
    for knoten in js.get("nodes") or ():
        zusatz = merkmale_je_knoten.get(knoten.get("name"))
        if zusatz:
            alt = knoten.get("extras") if isinstance(knoten.get("extras"), dict) else {}
            knoten["extras"] = {**alt, **zusatz}
            n_knoten += 1
    for material in js.get("materials") or ():
        wert = durchlass_je_material.get(material.get("name"))
        if wert:
            erw = material.setdefault("extensions", {})
            erw[DURCHLASS_ERWEITERUNG] = {"transmissionFactor": round(float(wert), 4)}
            material["alphaMode"] = "OPAQUE"
            # GLAS IST GLATT (Ergebnis 332): Der Stil bringt Rauheit 1,0 mit (`_glb_material`),
            # und eine Scheibe mit Durchlass sah damit aus wie mattes Milchglas.
            pbr = material.setdefault("pbrMetallicRoughness", {})
            pbr["roughnessFactor"] = min(float(pbr.get("roughnessFactor", 1.0)),
                                         GLAS_RAUHEIT_HOECHSTENS)
            n_mat += 1
    if n_mat:
        benutzt = js.setdefault("extensionsUsed", [])
        if DURCHLASS_ERWEITERUNG not in benutzt:
            benutzt.append(DURCHLASS_ERWEITERUNG)
    roh = json.dumps(js, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    roh += b" " * (-len(roh) % 4)
    gesamt = 12 + 8 + len(roh) + len(rest)
    pfad.write_bytes(daten[:4] + _struct.pack("<II", _struct.unpack_from("<I", daten, 4)[0],
                                              gesamt)
                     + _struct.pack("<II", len(roh), 0x4E4F534A) + roh + rest)
    return {"knoten": n_knoten, "materialien": n_mat}


def warnungen_aus_bestand(bestand: dict, n_stile: int) -> list[str]:
    """Was der Datei fehlt, in Sätzen — **ohne ifcopenshell** aus Zählungen berechnet.

    **Anlass (``auf-20261022-331``):** Die glb des Mac-Demolaufs hatte kein Dach, keine
    Fenster und kein Material, und nichts hat es gesagt: Die Umwandlung lief «ok», weil
    sie alles umwandelte, was die Datei hatte. Dass die Datei selbst unvollständig war
    (ein Export ohne Dächer, Fenster und Stile), sah man erst im Bild. Diese Sätze sagen
    es beim Laden.

    ``bestand`` zählt je IFC-Typ (``IfcWall``, ``IfcRoof``, ``IfcOpeningElement`` …) plus
    ``dachplatten`` (Platten/Bekleidungen mit ``ROOF``/``ROOFING``) und ``fuellungen``
    (``IfcRelFillsElement``).
    """
    n = lambda k: int(bestand.get(k) or 0)              # noqa: E731
    saetze = []
    hat_bau = n("IfcWall") + n("IfcWallStandardCase") + n("IfcSlab") > 0
    if hat_bau and n("IfcRoof") == 0 and n("dachplatten") == 0:
        saetze.append(
            "KEIN DACH IN DER DATEI: Die IFC enthält weder ein IfcRoof noch eine Platte mit "
            "Typ ROOF. Das Bild zeigt das Haus oben offen — Licht fällt ins oberste "
            "Geschoss. Im Autorenprogramm das Dach mit ausgeben.")
    if n("IfcOpeningElement") > 0 and n("fuellungen") == 0:
        saetze.append(
            f"FENSTER NUR ALS LÖCHER: Die IFC hat {n('IfcOpeningElement')} Wandausschnitt(e), "
            "aber kein Fenster und keine Tür füllt sie (kein IfcRelFillsElement). Im Bild "
            "sind die Öffnungen leer — schwarz oder hell, ohne Glas. Im Autorenprogramm "
            "Fenster und Türen mit ausgeben.")
    if hat_bau and n_stile == 0:
        saetze.append(
            "KEINE FARBEN IN DER DATEI: Die IFC trägt keinen Oberflächenstil "
            "(IfcSurfaceStyle); die glb hat darum kein Material. Die Materialwahl am "
            "Render-Knoten wirkt trotzdem; Farben aus dem Modell kommen erst mit einem "
            "Export, der Stile schreibt.")
    return saetze


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
    # WAS STILL WEGFIEL (22.10.2026): Bis dahin stand hier `except: continue` ohne Zahl —
    # ein Bauteil, dessen Geometrie ifcopenshell nicht bilden konnte, verschwand spurlos.
    geometrie_fehler: dict[str, int] = {}
    ohne_geometrie: dict[str, int] = {}
    merkmale_je_knoten: dict[str, dict] = {}
    durchlass_je_material: dict[str, float] = {}
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
            # Nicht-geometrische Produkte und echte Fehler landen hier — gezählt, je Typ.
            geometrie_fehler[produkt.is_a()] = geometrie_fehler.get(produkt.is_a(), 0) + 1
            continue
        ecken = np.asarray(form.geometry.verts, dtype="float64").reshape(-1, 3)
        flaechen = np.asarray(form.geometry.faces, dtype="int64").reshape(-1, 3)
        if len(ecken) == 0 or len(flaechen) == 0:
            ohne_geometrie[produkt.is_a()] = ohne_geometrie.get(produkt.is_a(), 0) + 1
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
        merkmale = knoten_merkmale(produkt.is_a(), getattr(produkt, "PredefinedType", None),
                                   _ganzes_von(produkt),
                                   objekttyp=getattr(produkt, "ObjectType", None),
                                   name=getattr(produkt, "Name", None))
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
                if stil["durchsicht"]:
                    durchlass_je_material[stil["name"]] = stil["durchsicht"]
            knotenname = name if teil == 0 else f"{name}_{teil}"
            merkmale_je_knoten[knotenname] = merkmale
            szene.add_geometry(stueck, node_name=knotenname)
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
        # Gelände ist, was die Rolle traegt — seit R56 auch ein TERRAIN-Element.
        if merkmale.get("role") != "ground":
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
    nachgetragen = glb_nachtragen(glb_path, merkmale_je_knoten, durchlass_je_material)

    # WAS DER DATEI FEHLT — gezählt, nicht vermutet (auf-20261022-331).
    bestand = {t: len(modell.by_type(t)) for t in (
        "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcOpeningElement",
        "IfcWindow", "IfcDoor")}
    bestand["dachplatten"] = sum(
        1 for t in ("IfcSlab", "IfcCovering") for e in modell.by_type(t)
        if str(getattr(e, "PredefinedType", "") or "").upper() in DACH_TYPEN)
    bestand["fuellungen"] = len(modell.by_type("IfcRelFillsElement"))
    warnungen = warnungen_aus_bestand(bestand, len(modell.by_type("IfcSurfaceStyle")))

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
            "Modell und stehen nicht in der glb. Durchsicht aus der Datei steht seit dem "
            "22.10.2026 auch in der glb: als KHR_materials_transmission, weiter deckend."),
        "bbox_note": "bbox in nativen IFC-Metern (Z oben); die glb selbst ist Y-up",
        # Was die Umwandlung nicht bilden konnte — je Typ, statt still verworfen.
        "geometrie_fehler": dict(sorted(geometrie_fehler.items())),
        "ohne_geometrie": dict(sorted(ohne_geometrie.items())),
        # Merkmale an den Knoten (kind, openingType, role, ifc_type, PredefinedType) und
        # Durchlass an Glas-Materialien — siehe knoten_merkmale / glb_nachtragen.
        "knoten_mit_merkmalen": nachgetragen["knoten"],
        "materialien_mit_durchlass": nachgetragen["materialien"],
        "n_dach_knoten": sum(1 for m in merkmale_je_knoten.values()
                             if m.get("kind") == "roof"),
        "n_oeffnungs_knoten": sum(1 for m in merkmale_je_knoten.values()
                                  if m.get("kind") == "opening"),
        "n_gelaende_knoten": sum(1 for m in merkmale_je_knoten.values()
                                 if m.get("role") == "ground"),
        "bestand": bestand,
        # Was der DATEI fehlt (kein Dach, Fenster nur als Löcher, keine Farben) — in
        # Sätzen; der Importeur reicht sie als Hinweise weiter.
        "warnungen": warnungen,
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
