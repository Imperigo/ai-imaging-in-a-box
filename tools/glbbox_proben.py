"""Die gemeinsame Probendatei der Geländeregel: Python und Swift prüfen dieselbe Box.

A0267. Die Geländeregel für die Hüllbox einer glb steht am Heim-PC in ``aiimaging.glbbox``
(``maske.ist_gelaende``); der Mac rechnet sie in ``Glbauskunft`` (Swift) für das nach, was
aus den Namen im JSON-Kopf lesbar ist. Zwei Rechnungen laufen auseinander, sobald niemand sie
nebeneinanderlegt. Darum gibt es EINE Datei (``tests/daten/glbbox_gelaenderegel.json``):

* jeder Fall trägt den JSON-Kopf einer synthetischen glb (im Repo erzeugt, keine echten Daten);
* ``erwartet`` ist, was ``glbbox.bauwerksbox`` daraus macht (Python-Probe: stimmt es noch?);
* die Swift-Probe (``GlbauskunftGelaendeTests``) liest dieselbe Datei und verlangt dieselbe Box.

Neu erzeugen: ``python tools/glbbox_proben.py --schreiben``. Ohne Schalter wird nur geprüft, ob die
Datei zum Stand des Kerns passt (Ausgang 1, wenn nicht).
"""
from __future__ import annotations

import json
import struct
import sys
import tempfile
from pathlib import Path

ZIEL = Path(__file__).resolve().parents[1] / "tests" / "daten" / "glbbox_gelaenderegel.json"


def _quader(name, lo, hi, **knoten):
    """Ein Mesh-Knoten (glTF, Y oben) mit Box ``lo``..``hi``; liefert ``(knoten, netz, zugriff)``."""
    k = {"name": name, **knoten}
    netz = {"primitives": [{"attributes": {"POSITION": None}}]}
    zugriff = {"componentType": 5126, "count": 8, "type": "VEC3",
               "min": list(lo), "max": list(hi)}
    return k, netz, zugriff


def _glb_kopf(teile, szene=None, eltern=None):
    """JSON-Kopf aus Quadern. ``eltern``: ``{index: {"name":…, "translation":…}}`` vor die Kinder."""
    knoten, netze, zugriffe = [], [], []
    for i, (name, lo, hi, extra) in enumerate(teile):
        k, n, z = _quader(name, lo, hi, **extra)
        k["mesh"] = i
        n["primitives"][0]["attributes"]["POSITION"] = i
        knoten.append(k)
        netze.append(n)
        zugriffe.append(z)
    return knoten, netze, zugriffe


def _haus_am_hang():
    # Gelände 60 x 50 m, 0,3 m dick unter der Nulllinie; Haus 30,5 x 27,7 m, 9,1 m hoch, unter einem
    # verschobenen Elternknoten. Welt = (x, -z, y): glTF-Z 25 -> Welt -Y.
    teile = [
        ("Gelaende_Hang", (-30, -0.3, -25), (30, 0.0, 25), {}),
        ("Wand_Nord", (-15.25, 0.0, -13.85), (15.25, 6.0, 13.85), {}),
        ("Dach", (-15.25, 6.0, -13.85), (15.25, 9.1, 13.85), {}),
    ]
    knoten, netze, zugriffe = _glb_kopf(teile)
    # Elternknoten "Haus" (Index 3) trägt Wand und Dach; keine Verschiebung, damit die Box der
    # Beschreibung im Auftrag entspricht, aber mit Skalierung 1 und einer Drehung um 0 als Gegenprobe.
    knoten.append({"name": "Haus", "children": [1, 2], "translation": [0.0, 0.0, 0.0]})
    return {"asset": {"version": "2.0"}, "scene": 0,
            "scenes": [{"nodes": [0, 3]}], "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def _einfach(teile, wurzeln=None):
    knoten, netze, zugriffe = _glb_kopf(teile)
    return {"asset": {"version": "2.0"}, "scene": 0,
            "scenes": [{"nodes": wurzeln if wurzeln is not None else list(range(len(knoten)))}],
            "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def _verschoben():
    # Haus unter einem verschobenen Elternknoten, Gelände daneben: die Elternmatrix muss in die
    # Bauwerksbox eingehen, genau wie in die Szenenbox.
    teile = [
        ("Toposolid_1", (-40, -0.5, -40), (40, 0.0, 40), {}),
        ("Wand", (0.0, 0.0, 0.0), (10.0, 5.0, 8.0), {}),
    ]
    knoten, netze, zugriffe = _glb_kopf(teile)
    knoten.append({"name": "Gebaeude", "children": [1], "translation": [5.0, 1.0, -3.0]})
    return {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0, 2]}],
            "nodes": knoten, "meshes": netze, "accessors": zugriffe}


def definitionen() -> list[dict]:
    wuerfel = lambda x: ((x, 0.0, 0.0), (x + 4.0, 3.0, 4.0), {})   # noqa: E731
    return [
        {"fall": "haus-am-hang", "glb": _haus_am_hang(),
         "sagt": "Gelände 60 x 50 m neben dem Haus 30,5 x 27,7 m: die Hausbox, nicht die Szene."},
        {"fall": "elternknoten-verschoben", "glb": _verschoben(),
         "sagt": "Die Matrix des Elternknotens geht in die Bauwerksbox ein."},
        {"fall": "wortgrenzen", "glb": _einfach([
            ("Umgebung - Toposolid", (-50, -0.4, -50), (50, 0.0, 50), {}),
            ("IfcSite_1a2b3c", (-60, -1.0, -60), (60, -0.4, 60), {}),
            ("Waenden_EG", *wuerfel(0)),
            ("Geländer_Balkon", *wuerfel(5)),
            ("Bodenplatte des 2. OG", *wuerfel(10)),
        ]), "sagt": "Wörter an Wortgrenzen und das Muster ifcsite*: Toposolid und IfcSite sind Gelände, "
                    "Geländer und Bodenplatte nicht."},
        {"fall": "grossbuchstaben", "glb": _einfach([
            ("TERRAIN", (-30, -0.5, -30), (30, 0.0, 30), {}),
            ("Haus_A", *wuerfel(0)),
            ("Haus_B", *wuerfel(6)),
        ]), "sagt": "Kleinschreibung vor dem Vergleich."},
        {"fall": "ohne-gelaende", "glb": _einfach([
            ("Haus_A", *wuerfel(0)),
            ("Haus_B", *wuerfel(6)),
            ("Haus_C", *wuerfel(12)),
        ]), "sagt": "Kein Gelände erkennbar: Szenenbox, nicht abgetrennt."},
        {"fall": "alles-gelaende", "glb": _einfach([
            ("Terrain_A", (-20, -0.5, -20), (0, 0.0, 20), {}),
            ("Gelände_B", (0, -0.5, -20), (20, 0.0, 20), {}),
        ]), "sagt": "Alles Gelände: nie eine leere Box, es bleibt die Szenenbox."},
    ]


def schreibe_glb(js: dict, pfad: Path) -> None:
    """Eine glb nur aus dem JSON-Kopf (ohne Binärblock): genug für die Hüllbox."""
    block = json.dumps(js, separators=(",", ":")).encode("utf-8")
    block += b" " * (-len(block) % 4)
    pfad.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(block))
                     + struct.pack("<II", len(block), 0x4E4F534A) + block)


def rechne(js: dict) -> dict:
    """Was der Kern (``glbbox.bauwerksbox``) aus diesem Kopf macht, als ``erwartet``."""
    from aiimaging import glbbox
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "probe.glb"
        schreibe_glb(js, p)
        aus = glbbox.bauwerksbox(p)
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    return {"huellbox": [[round(v, 6) for v in e] for e in box],
            "szenenbox": [[round(v, 6) for v in e] for e in aus["bbox_szene"]],
            "bauteile": aus["n_knoten"],
            "gelaendeKnoten": aus["n_gelaende"],
            "abgetrennt": aus["bbox_bauwerk"] is not None and aus["n_gelaende"] > 0,
            "entschieden_durch": aus["entschieden_durch"]}


def erzeuge() -> dict:
    faelle = []
    for d in definitionen():
        faelle.append({"fall": d["fall"], "sagt": d["sagt"], "glb": d["glb"], "erwartet": rechne(d["glb"])})
    return {"schema": "visbox.glbbox-gelaenderegel/v1",
            "hinweis": "Synthetisch, mit tools/glbbox_proben.py erzeugt. Python (tests/"
                       "test_glbbox_gelaenderegel_gemeinsam.py) und Swift (GlbauskunftGelaendeTests) "
                       "lesen diese Datei und verlangen dieselbe Box.",
            "toleranz_m": 0.01, "faelle": faelle}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    neu = json.dumps(erzeuge(), indent=1, ensure_ascii=False) + "\n"
    if "--schreiben" in argv:
        ZIEL.parent.mkdir(parents=True, exist_ok=True)
        ZIEL.write_text(neu, encoding="utf-8")
        print(f"geschrieben: {ZIEL}")
        return 0
    if not ZIEL.exists() or ZIEL.read_text(encoding="utf-8") != neu:
        print("Die Probendatei passt nicht zum Kern: python tools/glbbox_proben.py --schreiben")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
