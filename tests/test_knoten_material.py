"""Knoten «Material», Heim-PC-Teil (H3, 20.10.2026): ``render.materialien`` je Bauteil-Art.

Vertrag mit dem Integrator: ``render.materialien {fassade?, dach?, fenster?, boden?,
uebrige?}`` mit je einer MaterialWahl ``{id, massstab_m?, drehungGrad?, relief?, toenung?}``;
ein leeres ``{}`` wird abgewiesen. Texturen CC0 (ambientCG) am Heim-PC über
``AIIMAGING_MATERIAL_ORDNER``, Muster ``<id>__<Asset>_<1K|2K>-JPG_<Karte>.jpg``. Fehlt eine,
endet der Auftrag mit Satz, und der Satz steht im Ergebnis (Entscheid 113).

Regel 3: Texturen sind hier erzeugte Mini-JPG in ``tmp_path``. Regel 2: Der Runner läuft mit
einer Attrappe für ``bpy``.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import abholer, bruecke, kosmo_szene, materialwahl, prompts

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")

#: Die Tabelle der HomeStation (20.10.2026) — id → Asset.
ASSETS = {"sichtbeton-sandgestrahlt": "Concrete037", "sichtbeton-schalungsglatt": "Concrete002",
          "fichte": "Wood096", "backstein": "Bricks101", "klinker": "Bricks054",
          "sandstein": "Rock004", "stampflehm": "Ground104",
          "verputz-weiss-glatt": "Plaster002", "verputz-weiss-rau": "Plaster003",
          "holzlattung-fichte": "Planks021", "dreischichtplatte": "Wood090A"}


def _mini_jpg(pfad: Path) -> None:
    from PIL import Image
    Image.new("RGB", (4, 2), (120, 110, 100)).save(pfad, "JPEG")


def _texturen(tmp_path, monkeypatch, *, ids=tuple(ASSETS), groessen=("1K", "2K"),
              karten=materialwahl.KARTEN[:4], asset=None):
    ordner = tmp_path / "texturen"
    ordner.mkdir(exist_ok=True)
    for kennung in ids:
        for g in groessen:
            for k in karten:
                _mini_jpg(ordner / f"{kennung}__{asset or ASSETS[kennung]}_{g}-JPG_{k}.jpg")
    monkeypatch.setenv(materialwahl.MATERIAL_ORDNER_ENV, str(ordner))
    return ordner


def _szene(materialien, **mehr):
    s = {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
         "render": {"materialien": materialien}, "style": {"prompt": "a quiet house"},
         "vis": {}}
    s.update(mehr)
    return s


# ====================================================================== die Bibliothek

def test_elf_materialien_mit_herkunft():
    assert {k: v["asset"] for k, v in materialwahl.BIBLIOTHEK.items()} == ASSETS
    assert materialwahl.HERKUNFT["lizenz"] == "CC0-1.0"
    for kennung, e in materialwahl.BIBLIOTHEK.items():
        assert materialwahl.ID_MUSTER.match(kennung)
        assert e["label"] and e["prompt_de"] and e["prompt_en"]
        for art in materialwahl.ARTEN:
            satz, _ = materialwahl.prompt_satz(art, kennung, "")
            assert not prompts.bauteilwaechter(satz)["gefunden"], (art, kennung, satz)
    assert materialwahl.BIBLIOTHEK["holzlattung-fichte"]["fugen"]["latte_m"] == 0.05


@pytest.mark.parametrize("name, merkmale, art", [
    ("Wand", {"kind": "wall"}, "fassade"),
    ("Dach", {"kind": "roof"}, "dach"),
    ("Platte", {"kind": "slab"}, "boden"),
    ("Platte", {"kind": "slab", "predefined": "ROOF"}, "dach"),
    ("Loch", {"kind": "opening"}, "fenster"),
    ("Loch", {"kind": "opening", "opening_type": "tuer"}, "uebrige"),
    ("Luke", {"kind": "dachfenster"}, "fenster"),
    ("Hang", {"kind": "terrain"}, "gelaende"),
    ("Treppe", {"kind": "stair"}, "uebrige"),
    ("IfcWall_Wand-Sued_0abc", {}, "fassade"),
    ("IfcRoof_Dach_0abc", {}, "dach"),
    ("IfcSlab_Decke_0abc", {}, "boden"),
    ("IfcSlab_Decke_0abc", {"predefined": "ROOF"}, "dach"),
    ("IfcWindow_F1_0abc", {}, "fenster"),
    ("IfcDoor_T1_0abc", {}, "uebrige"),
    ("IfcSite_Grund_0abc", {}, "gelaende"),
    ("IfcWall_W_0abc", {"kind": "freemesh"}, "fassade"),
    ("Mesh.001", {}, "uebrige"),
    ("Mesh.001", {"ist_gelaende": True}, "gelaende"),
])
def test_die_art_eines_bauteils(name, merkmale, art):
    assert materialwahl.art_von(name, **merkmale) == art


def test_die_tabellen_kennen_nur_die_arten():
    erlaubt = set(materialwahl.ARTEN) | {materialwahl.ART_GELAENDE, None}
    assert set(materialwahl.KIND_ZU_ART.values()) <= erlaubt
    assert set(materialwahl.IFC_ZU_ART.values()) <= erlaubt


# ====================================================================== die Texturen

def test_die_karten_werden_nach_dem_muster_gesucht(tmp_path, monkeypatch):
    ordner = _texturen(tmp_path, monkeypatch, ids=("backstein",), asset="AnderesAsset7")
    gefunden = materialwahl.texturen("backstein")
    assert gefunden["satz"] is None and gefunden["asset"] == "AnderesAsset7"
    assert gefunden["groesse"] == "2K"
    assert gefunden["karten"]["Color"] == ordner / "backstein__AnderesAsset7_2K-JPG_Color.jpg"
    assert materialwahl.texturen("backstein", guete="vorschau")["groesse"] == "1K"


def test_eine_fehlende_karte_nennt_ihren_namen(tmp_path, monkeypatch):
    _texturen(tmp_path, monkeypatch, ids=("klinker",), karten=("Color", "Roughness"))
    satz = materialwahl.texturen("klinker")["satz"]
    assert satz == "Textur 'klinker' (2K, Displacement) fehlt am Rechner."


def test_ohne_ordner_ein_satz(monkeypatch):
    monkeypatch.delenv(materialwahl.MATERIAL_ORDNER_ENV, raising=False)
    assert materialwahl.MATERIAL_ORDNER_ENV in materialwahl.texturen("fichte")["satz"]


# ====================================================================== lies_szene

def test_die_wahl_wird_gelesen_mit_vorgaben(tmp_path, monkeypatch):
    _texturen(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene({
        "fassade": {"id": "sichtbeton-sandgestrahlt"},
        "boden": {"id": "stampflehm", "massstab_m": 2, "toenung": {"farbe": "#AA8866",
                                                                    "staerke": 0.3}}}))
    assert s["maengel"] == ()
    assert s["materialien"]["fassade"] == {"id": "sichtbeton-sandgestrahlt", "massstab_m": 1.0,
                                           "drehungGrad": 0.0, "relief": 0.6, "toenung": None}
    assert s["materialien"]["boden"]["toenung"] == {"farbe": "#aa8866", "staerke": 0.3}
    assert s["materialien_vorgaben"]["boden"] == ["drehungGrad", "relief"]
    assert set(s["materialien_dateien"]) == {"fassade", "boden"}
    # Seit Entscheid 126 (material_vorne Vorgabe) steht der Stoff vorne; der Satz hinten
    # faellt weg (auf-20261021-303, B3) und bleibt mit `weggelassen` im Befund.
    assert s["prompt"].startswith("monolithic sandblasted exposed concrete building")
    assert [z.get("weggelassen") for z in s["prompt_zusaetze"]
            if z.get("art") == "material" and z.get("id") == "sichtbeton-sandgestrahlt"] == \
        ["material_vorne"]


@pytest.mark.parametrize("wahl, wort, endgueltig", [
    ({}, "leer", True),
    ({"fassade": {"id": "marmor"}}, "nicht in der Bibliothek", True),
    ({"fassade": {"id": "Marmor!"}}, "fassade.id", False),
    ({"wand": {"id": "backstein"}}, "wand", False),
    ({"dach": {"id": "backstein", "massstab_m": 50}}, "massstab_m", False),
    ({"dach": {"id": "backstein", "relief": 2}}, "relief", False),
    ({"dach": {"id": "backstein", "toenung": {"farbe": "rot", "staerke": 1}}}, "farbe", False),
    ({"dach": {"id": "backstein", "toenung": {"farbe": "#112233"}}}, "staerke", False),
    ({"dach": {"id": "backstein", "glanz": 1}}, "glanz", False),
    ("backstein", "kein Block", False),
])
def test_falsche_wahlen_sind_maengel(tmp_path, monkeypatch, wahl, wort, endgueltig):
    _texturen(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene(wahl))
    assert any(wort in m for m in s["maengel"]), s["maengel"]
    assert any(wort in m for m in s["maengel_endgueltig"]) is endgueltig


def test_eine_fehlende_textur_endet_mit_namen(tmp_path, monkeypatch):
    _texturen(tmp_path, monkeypatch, ids=("backstein",))
    s = kosmo_szene.lies_szene(_szene({"fassade": {"id": "backstein"},
                                       "boden": {"id": "stampflehm"}}))
    satz = "Textur 'stampflehm' (2K, Color, Roughness, Displacement) fehlt am Rechner."
    assert s["fehlende_dateien"] == (satz,)
    assert satz in s["maengel_endgueltig"]


def test_weiss_und_materialien_widersprechen_sich(tmp_path, monkeypatch):
    _texturen(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene({"fassade": {"id": "backstein"}}))
    s2 = _szene({"fassade": {"id": "backstein"}})
    s2["render"]["environment"] = {"preset": "weiss"}
    s2 = kosmo_szene.lies_szene(s2)
    assert not any("Gipsmodell" in m for m in s["maengel"])
    assert any("weiss" in m and "Gipsmodell" in m for m in s2["maengel_endgueltig"])


def test_mit_grundlage_keine_textur_noetig(monkeypatch):
    monkeypatch.delenv(materialwahl.MATERIAL_ORDNER_ENV, raising=False)
    s = kosmo_szene.lies_szene(_szene({"dach": {"id": "klinker"}},
                                      vis={"grundlage": "gl-0123456789abcdef"}))
    assert s["maengel"] == () and s["materialien_dateien"] is None


# ====================================================================== der Abholer

def _bestellung(tmp_path, materialien, **vis):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["render"]["materialien"] = materialien
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def test_der_runner_bekommt_die_wahl_als_json(tmp_path, monkeypatch):
    texturen = _texturen(tmp_path, monkeypatch)
    ordner = _bestellung(tmp_path, {"fassade": {"id": "holzlattung-fichte", "drehungGrad": 90},
                                    "boden": {"id": "stampflehm"}}, guete="vorschau")
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    datei = Path(protokoll["multipass"][0]["materialien_json"])
    assert datei.name == abholer.DATEI_MATERIALWAHL
    wahl = json.loads(datei.read_text(encoding="utf-8"))
    assert wahl["schema"] == abholer.MATERIALWAHL_SCHEMA
    fassade = wahl["arten"]["fassade"]
    assert fassade["drehungGrad"] == 90.0 and fassade["groesse"] == "1K"
    assert fassade["fugen"] == {"latte_m": 0.05, "fuge_m": 0.02, "dunkel": 0.25}
    assert Path(fassade["karten"]["Color"]).parent == texturen
    assert wahl["arten"]["boden"]["fugen"] is None
    angewandt = antwort["ergebnis"]["angewandt"]["materialien"]
    assert angewandt["fassade"]["label"] == "Holzlattung Fichte"
    assert angewandt["boden"]["asset"] == "Ground104"
    assert str(tmp_path) not in json.dumps(antwort["ergebnis"]), "kein Pfad (Regel 3)"


def test_eine_fehlende_textur_ergibt_ergebnis_mit_grund(tmp_path, monkeypatch):
    _texturen(tmp_path, monkeypatch, ids=("backstein",))
    ordner = _bestellung(tmp_path, {"boden": {"id": "stampflehm"}})
    protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_FEHLER and protokoll["multipass"] == []
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["lieferstatus"] == "fehlgeschlagen"
    assert "stampflehm" in ergebnis["lieferstatus_grund"]


def test_die_materialien_gehoeren_zur_grundlage():
    assert "materialien" in abholer.GRUNDLAGE_MUSS_PASSEN


# ====================================================================== der Runner

class _Material(dict):
    def __init__(self, name, **mehr):
        super().__init__(**mehr)
        self.name = name


class _Daten:
    def __init__(self):
        self.materials = []


def _mesh(name, *, materialien=(), **extras):
    obj = SimpleNamespace(name=name, type="MESH", parent=None, data=_Daten(),
                          get=extras.get)
    obj.material_slots = [SimpleNamespace(material=m) for m in materialien]
    return obj


def _runner(monkeypatch, objekte):
    bpy = mock.MagicMock()
    bpy.data.objects = objekte
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_material", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    erzeugt = []

    def material_aus_wahl(art, wahl, ursprung):
        m = _Material(f"Materialwahl_{art}", **{modul.MATERIAL_MARKE: art,
                                                modul.URSPRUNG_MARKE: ursprung})
        erzeugt.append((art, wahl["id"], ursprung))
        return m

    monkeypatch.setattr(modul, "_material_aus_wahl", material_aus_wahl)
    return modul, bpy, erzeugt


def test_die_wahl_trifft_die_richtigen_bauteile(tmp_path, monkeypatch):
    wand = _mesh("IfcWall_Sued_0a", materialien=[_Material("Beton")])
    dach = _mesh("Dach", kind="roof", materialien=[_Material("Ziegel")])
    gelaende = _mesh("Gelaende", materialien=[_Material("Gras")])
    tuer = _mesh("IfcDoor_T1_0b")
    modul, _, erzeugt = _runner(monkeypatch, [wand, dach, gelaende, tuer])
    wahl = tmp_path / "materialwahl.json"
    wahl.write_text(json.dumps({"arten": {
        "fassade": {"id": "backstein", "karten": {"Color": "/x/a.jpg"}},
        "uebrige": {"id": "fichte", "karten": {"Color": "/x/b.jpg"}},
        "dach": {"id": "klinker", "karten": {}}}}), encoding="utf-8")

    befund = modul._materialien_setzen(SimpleNamespace(materialien=str(wahl)), ["Gelaende"])

    assert wand.material_slots[0].material.name == "Materialwahl_fassade"
    assert dach.material_slots[0].material.name == "Materialwahl_dach"
    assert gelaende.material_slots[0].material.name == "Gras", "Gelaende bleibt"
    assert tuer.data.materials[0][modul.URSPRUNG_MARKE] == "", "ein Objekt ohne Material"
    assert ("fassade", "backstein", "Beton") in erzeugt
    assert befund["arten"]["fassade"]["objekte"] == 1
    assert befund["objekte_je_art"]["gelaende"] == 1
    assert befund["arten"]["fassade"]["karten"] == ["a.jpg"], "nur Namen (Regel 3)"


def test_nicht_gewaehlte_arten_behalten_ihr_material(tmp_path, monkeypatch):
    wand = _mesh("Wand", kind="wall", materialien=[_Material("Beton")])
    modul, _, _ = _runner(monkeypatch, [wand])
    wahl = tmp_path / "w.json"
    wahl.write_text(json.dumps({"arten": {"boden": {"id": "stampflehm", "karten": {}}}}),
                    encoding="utf-8")
    befund = modul._materialien_setzen(SimpleNamespace(materialien=str(wahl)))
    assert wand.material_slots[0].material.name == "Beton"
    assert befund["nicht_getroffen"] == ["boden"]


def test_der_shader_baut_box_projektion_bump_und_fugen(monkeypatch):
    modul, bpy, _ = _runner(monkeypatch, [])
    monkeypatch.undo()                         # die echte Funktion, nicht die Attrappe
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_shader", RUNNER)
    echt = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(echt)
    echt._material_aus_wahl("fassade", {
        "id": "holzlattung-fichte", "massstab_m": 2.0, "drehungGrad": 90.0, "relief": 0.6,
        "toenung": {"farbe": "#aa8866", "staerke": 0.3},
        "fugen": {"latte_m": 0.05, "fuge_m": 0.02, "dunkel": 0.25},
        "karten": {"Color": "/x/c.jpg", "Roughness": "/x/r.jpg", "Displacement": "/x/d.jpg"}},
        "Holz")
    baum = bpy.data.materials.new.return_value.node_tree
    arten = [c.args[0] for c in baum.nodes.new.call_args_list]
    for art in ("ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeTexImage",
                "ShaderNodeBsdfPrincipled", "ShaderNodeBump", "ShaderNodeSeparateXYZ"):
        assert art in arten, art
    assert arten.count("ShaderNodeTexImage") == 3
    knoten = baum.nodes.new.return_value
    assert knoten.projection == "BOX" and knoten.projection_blend == 0.2
    quelle = RUNNER.read_text(encoding="utf-8")
    assert 'koord.outputs["Object"]' in quelle and '"Non-Color"' in quelle


def test_die_kennung_bleibt_unter_dem_alten_namen():
    quelle = RUNNER.read_text(encoding="utf-8")
    assert "slot.material.get(URSPRUNG_MARKE) or slot.material.name" in quelle
    assert quelle.index("_materialien_setzen(a, bau_form") < \
        quelle.index("bpy.ops.render.render(write_still=not")


def test_der_runner_kennt_den_schalter(monkeypatch):
    modul, _, _ = _runner(monkeypatch, [])
    monkeypatch.setattr(sys, "argv", ["blender", "--", "--glb", "a.glb", "--out", "aus",
                                      "--materialien", "w.json"])
    assert modul._argumente().materialien == "w.json"
