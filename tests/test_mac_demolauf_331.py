"""Drei Funde aus dem Mac-Demolauf (Visbox 0.3.33, Mappe «Demohaus Test», 22.10.2026, Protokoll 74 §240).

1. **Falsche Wartemeldung** — direkt nach der Freigabe «nicht abgeholt (Grund unbekannt)», obwohl der
   Abholer im 10-s-Takt läuft. Die Knotenansicht (Kopie des Vis-Werkzeugs) sagt jetzt drei Takte lang
   «wartet auf den Heim-PC …». Die Logik prüft ``vitest`` (drüben ``wartet-heimpc-takt.test.ts``);
   hier wird bewacht, dass der Takt der Anzeige der Takt des Heim-PC ist.
2. **Kein Boden** — ein Modell ohne Gelände bekommt in Blender keinen Boden; erkannt wird Gelände nur
   über ``extras.role`` oder die Namen «Gelaende»/«terrain». Befund, nicht gebaut (Empfehlung).
3. **Glas** — die Materialwahl «fenster» meint die Rahmen; die Scheibe bleibt jetzt Glas.

Regel 2: der Runner läuft mit einer Attrappe für ``bpy``. Regel 3: die glb ist synthetisch.
"""
from __future__ import annotations

import importlib.util
import json
import re
import struct
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from aiimaging import kosmo_szene, maske, materialwahl, modellstand

WURZEL = Path(__file__).resolve().parents[1]
RUNNER = WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py"
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


# ================================================================ 1 · Wartemeldung

def test_der_takt_der_anzeige_ist_der_takt_des_heim_pc():
    timer = (WURZEL / "betrieb" / "kosmo-abholer.timer").read_text(encoding="utf-8")
    sekunden = int(re.search(r"^OnUnitInactiveSec=(\d+)s$", timer, re.M).group(1))
    laufzeit = (VIS / "vis-runtime.ts").read_text(encoding="utf-8")
    takt_ms = int(re.search(r"export const ABHOLER_TAKT_MS = ([\d_]+);", laufzeit)
                  .group(1).replace("_", ""))
    assert takt_ms == sekunden * 1000, "Takt der Anzeige und Takt des Abholers laufen auseinander"
    assert "export const ABHOLER_GEDULD_MS = 3 * ABHOLER_TAKT_MS;" in laufzeit


def test_die_knotenansicht_fragt_die_geduld_ab_bevor_sie_nicht_abgeholt_sagt():
    canvas = (VIS / "NodeCanvas.tsx").read_text(encoding="utf-8")
    assert "wartetAbholerLabel(lauf?.wartetGrund, wartetNochImTakt(lauf?.wartetSeit, Date.now()))" in canvas
    warteort = (VIS / "render-warteort.ts").read_text(encoding="utf-8")
    assert "wartetAbholerText(lauf.gestartetUm, jetzt, lauf.wartetGrund, lauf.wartetSeit)" in warteort


# ================================================================ synthetische glb

def _glb(js: dict) -> bytes:
    roh = json.dumps(js).encode("utf-8")
    roh += b" " * (-len(roh) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(roh))
            + struct.pack("<II", len(roh), 0x4E4F534A) + roh)


def _demohaus_ohne_gelaende() -> dict:
    """Wie die KosmoOrbit-Ausfuhr: Wand, Fenster mit Scheibe (OPAQUE + Durchlass, K3), kein Gelände."""
    return {
        "asset": {"version": "2.0"},
        "extensionsUsed": ["KHR_materials_transmission"],
        "materials": [
            {"name": "Beton", "pbrMetallicRoughness": {"baseColorFactor": [0.6, 0.6, 0.6, 1]},
             "alphaMode": "OPAQUE"},
            {"name": "Glas", "pbrMetallicRoughness": {"baseColorFactor": [0.73, 0.83, 0.86, 1],
                                                      "roughnessFactor": 0.05},
             "alphaMode": "OPAQUE",
             "extensions": {"KHR_materials_transmission": {"transmissionFactor": 1}}},
        ],
        "meshes": [{"primitives": [{"material": 0}]}, {"primitives": [{"material": 1}]}],
        "nodes": [{"name": "Wand [w1]", "mesh": 0, "extras": {"entityId": "w1", "kind": "wall"}},
                  {"name": "Oeffnung Glas [o1]", "mesh": 1,
                   "extras": {"entityId": "o1", "kind": "opening"}}],
    }


# ================================================================ 2 · Boden

def test_ohne_gelaende_weist_die_glb_keinen_boden_aus(tmp_path):
    pfad = tmp_path / "demohaus.glb"
    pfad.write_bytes(_glb(_demohaus_ohne_gelaende()))
    assert kosmo_szene.gelaende_in_glb(pfad) is None


def test_gelaende_wird_an_rolle_oder_namen_erkannt_nicht_an_boden(tmp_path):
    js = _demohaus_ohne_gelaende()
    js["nodes"].append({"name": "Platte", "mesh": 0, "extras": {"role": "ground"}})
    pfad = tmp_path / "mit_rolle.glb"
    pfad.write_bytes(_glb(js))
    assert kosmo_szene.gelaende_in_glb(pfad)["knoten"] == ["Platte"]
    # Der Name der KosmoOrbit-Ausfuhr für Gelände («Gelaende», gltf.ts MATERIAL_AUSSEHEN.terrain)
    # trifft die Namensregel; «boden» nie (ein Geschossboden ist kein Gelände).
    assert maske.ist_gelaende("Gelaende") and not maske.ist_gelaende("boden")


def test_die_blender_stufe_legt_keinen_boden_an():
    """Befund, kein Wunsch: Ohne Gelände in der glb gibt es im Grundbild keinen Boden (Fund 2)."""
    quelle = RUNNER.read_text(encoding="utf-8")
    assert "primitive_plane_add" not in quelle and "is_shadow_catcher" not in quelle


# ================================================================ 3 · Glas

def test_die_scheibe_der_ausfuhr_zaehlt_als_durchsichtig(tmp_path):
    pfad = tmp_path / "demohaus.glb"
    pfad.write_bytes(_glb(_demohaus_ohne_gelaende()))
    gemessen = modellstand._messe_glb(pfad)
    assert gemessen["n_materialien_durchlass"] == 1
    assert gemessen["n_materialien_durchsichtig"] == 1


def test_die_scheibe_ist_art_fenster():
    """Darum traf die Fenster-Wahl bisher auch das Glas."""
    assert materialwahl.art_von("Oeffnung Glas [o1]", kind="opening") == "fenster"
    assert materialwahl.ART_IM_SATZ["fenster"] == "frames"


class _Material(dict):
    def __init__(self, name, durchlass=None, **mehr):
        super().__init__(**mehr)
        self.name = name
        knoten = []
        if durchlass is not None:
            eingang = SimpleNamespace(default_value=durchlass)
            knoten.append(SimpleNamespace(type="BSDF_PRINCIPLED",
                                          inputs={"Transmission Weight": eingang}))
        self.node_tree = SimpleNamespace(nodes=knoten)


class _Daten:
    def __init__(self):
        self.materials = []


def _mesh(name, *, materialien=(), **extras):
    obj = SimpleNamespace(name=name, type="MESH", parent=None, data=_Daten(), get=extras.get)
    obj.material_slots = [SimpleNamespace(material=m) for m in materialien]
    return obj


def _runner(monkeypatch, objekte):
    bpy = mock.MagicMock()
    bpy.data.objects = objekte
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_331", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    monkeypatch.setattr(modul, "_material_aus_wahl",
                        lambda art, wahl, ursprung: _Material(f"Materialwahl_{art}"))
    return modul


def test_die_fenster_wahl_ersetzt_den_rahmen_und_laesst_das_glas(tmp_path, monkeypatch):
    rahmen_und_glas = _mesh("Oeffnung [o1]", kind="opening",
                            materialien=[_Material("Fensterrahmen"), _Material("Glas", durchlass=1.0)])
    nur_glas = _mesh("Oeffnung Glas [o2]", kind="opening", materialien=[_Material("Glas")])
    scheibe_ohne_namen = _mesh("Oeffnung [o3]", kind="opening",
                               materialien=[_Material("Material.007", durchlass=1.0)])
    wand = _mesh("Wand [w1]", kind="wall", materialien=[_Material("Beton")])
    modul = _runner(monkeypatch, [rahmen_und_glas, nur_glas, scheibe_ohne_namen, wand])
    wahl = tmp_path / "w.json"
    wahl.write_text(json.dumps({"arten": {"fenster": {"id": "fichte", "karten": {}},
                                          "fassade": {"id": "backstein", "karten": {}}}}),
                    encoding="utf-8")

    befund = modul._materialien_setzen(SimpleNamespace(materialien=str(wahl)))

    assert [s.material.name for s in rahmen_und_glas.material_slots] == ["Materialwahl_fenster", "Glas"]
    assert nur_glas.material_slots[0].material.name == "Glas"
    assert scheibe_ohne_namen.material_slots[0].material.name == "Material.007"
    assert wand.material_slots[0].material.name == "Materialwahl_fassade"
    assert befund["arten"]["fenster"]["objekte"] == 1, "nur der Rahmen zählt als getroffen"


def test_glas_bleibt_nur_bei_der_fenster_wahl_unangetastet(tmp_path, monkeypatch):
    """Eine Fassaden-Wahl auf einem Objekt, das (fälschlich) Glas trägt, ändert sich nicht: nur «fenster»."""
    wand_mit_glas = _mesh("Wand [w2]", kind="wall", materialien=[_Material("Glas")])
    modul = _runner(monkeypatch, [wand_mit_glas])
    wahl = tmp_path / "w.json"
    wahl.write_text(json.dumps({"arten": {"fassade": {"id": "backstein", "karten": {}}}}),
                    encoding="utf-8")
    modul._materialien_setzen(SimpleNamespace(materialien=str(wahl)))
    assert wand_mit_glas.material_slots[0].material.name == "Materialwahl_fassade"
