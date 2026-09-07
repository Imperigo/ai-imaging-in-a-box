#!/usr/bin/env python3
"""STUDIE NAMENSDECKUNG — sehen Boxseite und Bildseite dieselben Namen?

Die Frage
---------
Seit dem 07.09.2026 erkennt `aiimaging.gelaendeform` Gelände an der **Gestalt**, wenn der
Name es nicht trägt. Das hilft der **Boxseite** (`glbbox.bauwerksbox`).

Die **Bildseite** (`maske.bauwerksmaske`) benutzt dieselbe Namensregel und hat diesen
Ausweg nicht: Sie bekommt eine flache Bildpunktliste und eine Farbtabelle — keine
Geometrie, keine Bildbreite, keine Positionen. Ein Formmerkmal ist von dort aus nicht
rechenbar.

Übertragen liesse sich aber das **Ergebnis**: die Namen, die die Form als Gelände erkannt
hat. Das trägt genau dann, wenn beide Seiten **dieselben Namen sehen** — und das ist die
Frage dieser Studie.

Was gemessen wird und was nicht
-------------------------------
`blender_depth_stage._material_id_zuweisen` baut die Tabelle auf zwei Wegen, und sein
eigener Docstring nennt beide:

* **``quelle: material``** — der Name kommt aus ``slot.material.name``, also aus dem
  Materialnamen. Bestandsmessung vom 06.09.2026 (`auf-20260826-51`): *Beton, Glas,
  Volumen, mauerwerk*.
* **``quelle: objekt``** — trägt ein Mesh gar kein Material, bekommt es objektweise eine
  ID, und der Name ist ``obj.name``. *«Genau das ist der Normalfall der aktuellen Kette:
  `ifc_to_glb_runner.py` überträgt nur Geometrie, keine IfcMaterial-Zuordnung.»*

**Diese Studie rechnet ohne Blender.** Sie baut die beiden Tabellenformen so nach, wie der
Runner sie laut seinem Quelltext baut, und misst die Deckung gegen die Knotennamen aus
`glbbox.knotenboxen`. *Das ist eine Aussage über die Namensregel, nicht über einen Lauf* —
was Blender wirklich in ``obj.name`` schreibt, kann nur ein Lauf auf der HomeStation sagen,
und genau darum steht der dritte Fall unten drin.

    python tools/studie_namensdeckung.py
    python tools/studie_namensdeckung.py --json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import gelaendeform as gf  # noqa: E402
from aiimaging import glbbox  # noqa: E402


def _make_glb():
    spec = importlib.util.spec_from_file_location("mk_glb", WURZEL / "tools" / "make_test_glb.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


#: Die Szene: eine Geländeplatte, die kein bekanntes Wort trägt, und zwei Baukörper.
#: Nachgebaut nach dem echten Bestand (`auf-20260826-51`).
KOERPER = [
    ("IfcCovering_Sub-Division:1", (-47, -0.5, -47), (47, 0, 47)),
    ("IfcWall_Aussenwand:12", (-20, 0, -20), (20, 30, 20)),
    ("IfcWall_Aussenwand:12", (25, 0, -20), (35, 30, 20)),
]

#: **Der Fall, der am echten Bestand wirklich vorliegt.** Dort bilden **zwanzig** Knoten
#: namens ``IfcCovering_Sub-Division:…`` zusammen die Gelaendeplatte (`auf-20260826-51`).
#: Hier vier davon — genug, damit Blenders Eindeutigkeitsregel zuschlaegt.
KOERPER_GETEILTES_GELAENDE = [
    ("IfcCovering_Sub-Division:1", (-47, -0.5, -47), (0, 0, 0)),
    ("IfcCovering_Sub-Division:1", (0, -0.5, -47), (47, 0, 0)),
    ("IfcCovering_Sub-Division:1", (-47, -0.5, 0), (0, 0, 47)),
    ("IfcCovering_Sub-Division:1", (0, -0.5, 0), (47, 0, 47)),
    ("IfcWall_Aussenwand:12", (-20, 0, -20), (20, 30, 20)),
]

#: Wie der Runner die Tabelle benennt — beide Wege aus seinem Quelltext.
#:
#: ``objekt_mit_dubletten`` ist der dritte Fall und der unbequemste: Blender vergibt
#: Objektnamen **eindeutig** und hängt bei einer Dublette ``.001`` an. Zwei Wände desselben
#: Namens in der glb werden dort also zu ``…:12`` und ``…:12.001`` — und ein Vergleich auf
#: Gleichheit trifft die zweite nicht mehr.
#: Beim Materialfall ist **einer** der vier Namen das Gelände — welcher, weiss von aussen
#: niemand. Das Gelände verschwindet ja nicht, weil die Tabelle Materialnamen trägt; seine
#: Bildpunkte stehen dann unter dem Material, mit dem es gerendert wurde. *Ohne diesen
#: Eintrag zeigte die Studie ``0/0`` und läse sich wie «hier gibt es nichts zu finden» —
#: richtig ist «hier ist etwas, und die Brücke findet es nicht».*
MATERIAL_GELAENDE = "Volumen"

FAELLE = {
    "material": ["Beton", "Glas", "Volumen", "mauerwerk"],
    "objekt": None,                    # aus den Knotennamen, unverändert
    "objekt_mit_dubletten": None,      # aus den Knotennamen, mit Blenders .001-Suffix
}


def _tabelle(fall: str, knoten: list[tuple], gelaende: set[str]) -> list[dict]:
    """Die Tabelle so, wie der Runner sie baut — plus die Wahrheit je Eintrag.

    ``ist_gelaende_wirklich`` ist die **bekannte** Wahrheit der Szene und nicht das Urteil
    einer Regel: Ohne sie liesse sich keine Deckung messen, sondern nur eine Regel gegen
    sich selbst halten.
    """
    knotennamen = [k[0] for k in knoten]
    if FAELLE[fall] is not None:
        eintraege = [(n, n == MATERIAL_GELAENDE) for n in FAELLE[fall]]
        quelle = "material"
    elif fall == "objekt":
        eintraege = [(n, n in gelaende) for n in sorted(set(knotennamen))]
        quelle = "objekt"
    else:
        # BLENDER VERGIBT OBJEKTNAMEN EINDEUTIG und haengt bei einer Dublette `.001` an.
        # Am echten Bestand bilden ZWANZIG Knoten desselben Namens die Gelaendeplatte —
        # aus einem Namen werden dort zwanzig, und neunzehn davon kennt die Formliste
        # nicht.
        eintraege, gesehen = [], {}
        for n in sorted(knotennamen):
            gesehen[n] = gesehen.get(n, 0) + 1
            gezeigt = n if gesehen[n] == 1 else f"{n}.{gesehen[n] - 1:03d}"
            eintraege.append((gezeigt, n in gelaende))
        quelle = "objekt"
    return [{"index": i, "name": n, "quelle": quelle, "ist_gelaende_wirklich": g}
            for i, (n, g) in enumerate(eintraege)]


def messen(ziel: Path, koerper=None) -> dict:
    koerper = KOERPER if koerper is None else koerper
    ziel.write_bytes(_make_glb().baue_glb([(n, lo, hi) for n, lo, hi in koerper]))
    knoten = glbbox.knotenboxen(glbbox.lies_gltf_json(ziel))["knoten"]
    knotennamen = [k[0] for k in knoten]
    gefunden = gf.gelaende_knoten(knoten)["gelaende"]

    aus = {"knotennamen": sorted(set(knotennamen)),
           "form_gelaende": sorted(set(gefunden)), "faelle": {}}
    # GEMESSEN WIRD UEBER DIE TABELLENEINTRAEGE, nicht ueber die Formnamen.
    #
    # Der erste Anlauf am 08.09.2026 zaehlte, wie viele der von der Form erkannten NAMEN
    # in der Tabelle vorkommen. Das ergab beim geteilten Gelaende 100 % — und war
    # trotzdem falsch: Die Maske arbeitet ueber die Tabelle, und dort standen vier
    # Eintraege, von denen die uebergebene Namensliste nur einen traf. *Eine Deckung, die
    # in die falsche Richtung misst, ist eine Zahl ohne Gegenstand.*
    zusatz = set(gefunden)
    for fall in FAELLE:
        tabelle = _tabelle(fall, knoten, zusatz)
        echt = [e for e in tabelle if e["ist_gelaende_wirklich"]]
        getroffen = [e for e in echt if e["name"] in zusatz]
        aus["faelle"][fall] = {
            "quelle": tabelle[0]["quelle"],
            "tabellennamen": sorted(e["name"] for e in tabelle),
            "n_gelaende_eintraege": len(echt),
            "n_getroffen": len(getroffen),
            "verfehlt": sorted(e["name"] for e in echt if e["name"] not in zusatz),
            "deckung": (len(getroffen) / len(echt)) if echt else None,
        }
    return aus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ziel", default="build/namensdeckung.glb")
    a = ap.parse_args(argv)

    ziel = Path(a.ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    szenen = {"ein Gelaendekoerper": messen(ziel, KOERPER),
              "geteiltes Gelaende (4 Knoten)": messen(
                  ziel.with_name("namensdeckung_geteilt.glb"),
                  KOERPER_GETEILTES_GELAENDE)}
    if a.json:
        print(json.dumps(szenen, ensure_ascii=False, indent=1))
        return 0

    for titel, aus in szenen.items():
        print(f"=== {titel}")
        print(f"  Knoten: {aus['knotennamen']}")
        print(f"  Von der FORM als Gelaende erkannt: {aus['form_gelaende']}")
        print(f"  {'Fall':<22} {'quelle':<9} {'Deckung':>8}  Tabellennamen")
        for fall, e in aus["faelle"].items():
            d = "—" if e["deckung"] is None else f"{e['deckung']:.0%}"
            print(f"  {fall:<22} {e['quelle']:<9} {d:>8}  "
                  f"{e['n_getroffen']}/{e['n_gelaende_eintraege']} Gelaende-Eintraege"
                  + (f", verfehlt: {e['verfehlt']}" if e["verfehlt"] else ""))
        print()

    print("BEFUND")
    for titel, aus in szenen.items():
        for fall, e in aus["faelle"].items():
            if not e["deckung"]:
                lage = "traegt NICHT — kein Formbefund kommt in der Tabelle vor"
            elif e["deckung"] < 1.0:
                lage = (f"traegt NUR TEILWEISE ({e['deckung']:.0%}) — der Rest steht "
                        f"unter einem anderen Namen in der Tabelle")
            else:
                lage = "traegt"
            print(f"  {titel} / {fall}: {lage}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
