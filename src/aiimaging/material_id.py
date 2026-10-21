"""Der Plan des Material-ID-Passes — welche Fläche welche Kennung bekommt. Ohne Blender.

Warum dieser Plan aus dem Runner herausgezogen ist
--------------------------------------------------
Bis zum 21.10.2026 entschied ``blender_depth_stage._material_id_zuweisen`` die Kennungen
**während** es die Materialien schon austauschte, Objekt für Objekt. Das ging gut, solange
jedes Objekt sein eigenes Mesh hatte. Die Probedatei von KosmoDraw (19 600 Backsteine als
Instanzen eines einzigen Meshes; der glTF-Import rollt sie zu 19 600 Objekten aus, die sich
dieses Mesh teilen) hat gezeigt, was dann geschieht (HomeStation, ``auf-20261021-316``, B2):

* Das zweite Objekt las am geteilten Mesh nicht mehr ``backstein``, sondern das eben
  vergebene ``MATID_000_backstein`` — einen neuen Namen, also eine neue Kennung, und deren
  Name ``MATID_001_MATID_000_backstein``. Nach 19 600 Objekten: 19 605 Einträge, Namen bis
  zur 255-Zeichen-Grenze verkettet und abgeschnitten, nur 25 trugen noch «backstein».
* Mit 19 605 Einträgen reicht der Farbkreis nicht mehr: Bei fester Sättigung und
  Helligkeit gibt es nur gut tausend verschiedene 8-Bit-Farben, also wiederholten sich
  Kennfarben (Warnung «Zwei Einträge tragen dieselbe Kennfarbe»).

Die Ursache ist eine Reihenfolge, kein Rechenfehler: Gelesen wurde am Zustand, der gerade
umgeschrieben wird. Darum steht der Plan jetzt **vor** jedem Eingriff, an den ursprünglichen
Namen, und als reine Funktion — prüfbar ohne Blender (``tests/test_material_id_plan.py``).

Die drei Regeln
---------------
1. **Eine Kennung je Material, nicht je Objekt.** Wer ``backstein`` trägt, bekommt
   ``MATID_000_backstein`` — gleich ob ein Objekt oder 19 600 es tragen. Namen werden nie
   aus einem schon vergebenen Kennungsnamen gebildet.
2. **Ohne Material: eine Kennung je Mesh, nicht je Objekt** — sobald sich mehrere Objekte
   ein Mesh teilen. Ein geteiltes Mesh kann an seinen Slots nur *ein* Material tragen; eine
   Kennung je Objekt wäre dort ohnehin nur die des letzten. Ausnahme ist ein Bauteil aus
   unserer IFC-Umwandlung: Es behält seine Kennung je Objekt (die Geländeregel liest dort
   Knotennamen), und der Runner hängt sie dafür an das Objekt statt an das Mesh.
3. **Jede Kennfarbe einmal.** Eine Farbe, die in 8 Bit schon vergeben ist, wird
   übersprungen. Die ersten Farben bleiben damit genau die bisherigen.

Reine Standardbibliothek. Kein ``bpy``, kein Oberflächen-Import (Regeln 2 und 4).
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

#: Wie oft die Farbfolge höchstens weitergedreht wird, um eine freie 8-Bit-Farbe zu finden.
#: Bei fester Sättigung und Helligkeit gibt es rund 1300 verschiedene Farben; mehr Einträge
#: lassen sich nicht eindeutig färben, und das wird laut gemeldet statt still verdoppelt.
FARBSUCHE_HOECHSTENS = 64

#: Der Name einer Kennung — eine Stelle, damit Runner und Plan nie auseinanderlaufen.
def kennungsname(index: int, name: str) -> str:
    """``MATID_<index>_<name>``; ``name`` ist immer der ursprüngliche Name."""
    return f"MATID_{index:03d}_{name}"


class MaterialIdError(ValueError):
    """Der Plan lässt sich nicht eindeutig färben."""


def _acht_bit(farbe) -> tuple[int, int, int]:
    return tuple(int(round(float(k) * 255.0)) for k in farbe[:3])


def plane_material_ids(objekte: Sequence[dict], farbe_fuer: Callable[[int], Sequence[float]],
                       ) -> dict:
    """Kennungen planen, bevor ein Material angefasst wird.

    Args:
        objekte: je Mesh-Objekt ``{"name", "mesh", "slots", "ifc"}`` — ``mesh`` ist der Name
            des Mesh-Datenblocks (geteilt heisst: gleicher Name), ``slots`` die
            **ursprünglichen** Materialnamen je Slot (``None`` für einen leeren Slot),
            ``ifc`` ob das Objekt aus unserer IFC-Umwandlung stammt. Die Reihenfolge ist
            gleichgültig; geplant wird nach Objektnamen sortiert, damit zwei Läufe dieselben
            Indizes und damit dieselben Farben vergeben.
        farbe_fuer: die Palette des Runners, Folgeindex → sRGB 0..1. Der Plan dreht sie
            weiter, wenn eine Farbe in 8 Bit schon vergeben ist.

    Returns:
        ``{"tabelle": [...], "zuweisung": {objektname: {...}}}``. Ein Tabelleneintrag trägt
        ``index, name, quelle, farbe_srgb, farbe_srgb_8bit, n_objekte`` (``quelle``
        ``"material"`` oder ``"objekt"``, wie bisher). Die Zuweisung je Objekt ist entweder
        ``{"art": "objekt", "index", "am_objekt"}`` — ein Slot, ``am_objekt`` wahr, wenn die
        Kennung am Objekt statt am geteilten Mesh hängen muss — oder
        ``{"art": "slots", "indizes": [index oder None je Slot]}``.

    Raises:
        MaterialIdError: wenn für einen Eintrag keine freie Kennfarbe zu finden ist.
    """
    tabelle: list[dict] = []
    belegt: set[tuple[int, int, int]] = set()
    folge = [0]                     # nächster Index in der Palette des Runners

    def eintragen(name: str, quelle: str) -> int:
        for _ in range(FARBSUCHE_HOECHSTENS):
            farbe = tuple(float(k) for k in farbe_fuer(folge[0]))[:3]
            folge[0] += 1
            acht = _acht_bit(farbe)
            if acht not in belegt:
                break
        else:
            raise MaterialIdError(
                f"Keine freie Kennfarbe mehr für '{name}' (Eintrag {len(tabelle)}): Die Palette "
                f"wiederholt sich in 8 Bit. So viele Kennungen lassen sich nicht eindeutig "
                f"färben — teilen sich die Objekte kein Material?")
        belegt.add(acht)
        index = len(tabelle)
        tabelle.append({
            "index": index,
            "name": name,
            "quelle": quelle,
            "farbe_srgb": [round(k, 6) for k in farbe],
            "farbe_srgb_8bit": list(acht),
            "n_objekte": 0,
        })
        return index

    geordnet = sorted(objekte, key=lambda o: str(o["name"]))
    nutzer_je_mesh: dict[str, int] = {}
    for obj in geordnet:
        nutzer_je_mesh[str(obj["mesh"])] = nutzer_je_mesh.get(str(obj["mesh"]), 0) + 1

    nach_material: dict[str, int] = {}
    nach_mesh: dict[str, int] = {}
    zuweisung: dict[str, dict] = {}
    for obj in geordnet:
        name, mesh = str(obj["name"]), str(obj["mesh"])
        slots = list(obj.get("slots") or [])
        belegte = [s for s in slots if s not in (None, "")]
        geteilt = nutzer_je_mesh[mesh] > 1
        if not belegte or obj.get("ifc"):
            # Ein IFC-Bauteil behält seine Kennung je Objekt (siehe Modul-Docstring, Regel 2);
            # ein materialloses Objekt mit eigenem Mesh ebenso, wie bisher.
            if obj.get("ifc") or not geteilt:
                index = eintragen(name, "objekt")
                zuweisung[name] = {"art": "objekt", "index": index, "am_objekt": geteilt}
            else:
                if mesh not in nach_mesh:
                    nach_mesh[mesh] = eintragen(name, "objekt")
                index = nach_mesh[mesh]
                zuweisung[name] = {"art": "objekt", "index": index, "am_objekt": False}
            tabelle[index]["n_objekte"] += 1
            continue
        indizes: list[int | None] = []
        for slot in slots:
            if slot in (None, ""):
                indizes.append(None)
                continue
            slot = str(slot)
            if slot not in nach_material:
                nach_material[slot] = eintragen(slot, "material")
            indizes.append(nach_material[slot])
        for index in sorted({i for i in indizes if i is not None}):
            tabelle[index]["n_objekte"] += 1
        zuweisung[name] = {"art": "slots", "indizes": indizes}

    return {"tabelle": tabelle, "zuweisung": zuweisung}


__all__ = ["FARBSUCHE_HOECHSTENS", "MaterialIdError", "kennungsname", "plane_material_ids"]
