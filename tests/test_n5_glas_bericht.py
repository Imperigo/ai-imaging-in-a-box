"""N5, Glas und der Bericht der Materialwahl (Mac-Demolauf und Ergebnis 332, 22.10.2026).

* **N5** — eine glb aus einem anderen Programm trägt weder ``extras.kind`` noch ``Ifc*``-Namen:
  alles war «uebrige», und die Wahl für «uebrige» (im Lauf die Holzlattung) lag auch auf Beton,
  Bäumen und Terrasse. Jetzt: zuerst ein Wort im Objektnamen (``materialwahl.NAME_ZU_ART``);
  ein Bauteil ohne jede Angabe behält sein **benanntes** Material aus der Datei.
* **Glas** — der IFC-Stil brachte Rauheit 1,0, die Scheibe sah aus wie mattes Milchglas.
  Materialien mit Durchlass bekommen höchstens 0,05 — in der glb der IFC-Umwandlung und in
  Blender für jede Datei.
* **Bericht** — «nicht_getroffen: fenster» las sich wie ein Fehler, war aber gewollt (das
  Fenster war nur Glas). Jetzt nach Grund getrennt: ``ohne_bauteil`` / ``nur_behalten``.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import materialwahl

from test_ifc_merkmale import _glb_json, _kleine_glb

WURZEL = Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
RUNNER = WURZEL / "blender_depth_stage.py"
IFC_RUNNER = WURZEL / "ifc_to_glb_runner.py"


class _Material(dict):
    def __init__(self, name, **mehr):
        super().__init__(**mehr)
        self.name = name


class _Daten:
    def __init__(self):
        self.materials = []


def _mesh(name, *, materialien=(), parent=None, **extras):
    obj = SimpleNamespace(name=name, type="MESH", parent=parent, data=_Daten(),
                          get=extras.get)
    obj.material_slots = [SimpleNamespace(material=m) for m in materialien]
    return obj


def _runner(monkeypatch, objekte, materialien=()):
    bpy = mock.MagicMock()
    bpy.data.objects = objekte
    bpy.data.materials = list(materialien)
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_n5", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)

    def material_aus_wahl(art, wahl, ursprung):
        return _Material(f"Materialwahl_{art}", **{modul.MATERIAL_MARKE: art,
                                                   modul.URSPRUNG_MARKE: ursprung})

    monkeypatch.setattr(modul, "_material_aus_wahl", material_aus_wahl)
    return modul


def _wahl(tmp_path, **arten):
    pfad = tmp_path / "wahl.json"
    pfad.write_text(json.dumps({"arten": {a: {"id": i, "karten": {}} for a, i in arten.items()}}),
                    encoding="utf-8")
    return SimpleNamespace(materialien=str(pfad))


# ====================================================================== N5: die Art aus dem Namen

@pytest.mark.parametrize("name, art", [
    ("Aussenwand_Nord", "fassade"), ("Facade.002", "fassade"), ("Wall_01", "fassade"),
    ("Satteldach", "dach"), ("Roof", "dach"),
    ("Fenster_Sued", "fenster"), ("Dachfenster 2", "fenster"), ("Window.004", "fenster"),
    ("Bodenplatte", "boden"), ("Geschossdecke OG", "boden"),
])
def test_ein_wort_im_namen_gibt_die_art(name, art):
    assert materialwahl.art_und_herkunft(name) == (art, materialwahl.HERKUNFT_NAME)


@pytest.mark.parametrize("name", ["Baum_03", "Terrasse", "Mesh.012", "Haus", "Stuhl"])
def test_ohne_wort_bleibt_es_unbestimmt(name):
    assert materialwahl.art_und_herkunft(name) == ("uebrige", materialwahl.HERKUNFT_UNBESTIMMT)


def test_kind_und_ifc_gehen_dem_namen_vor():
    """Die KosmoOrbit-glb und unsere IFC-Umwandlung rechnen wie bisher."""
    assert materialwahl.art_und_herkunft("Wand Dach", kind="stair") == ("uebrige", "kind")
    assert materialwahl.art_und_herkunft("IfcDoor_Wand_x") == ("uebrige", "ifc")
    assert materialwahl.art_und_herkunft("Wand", kind="freemesh") == ("uebrige", "kind")
    assert materialwahl.art_und_herkunft("Wand", ist_gelaende=True) == ("gelaende", "gelaende")
    # art_von sagt dasselbe wie vorher, wo kind oder Praefix da sind.
    assert materialwahl.art_von("IfcSlab_Dachplatte_x") == "boden"
    assert materialwahl.art_von("Oeffnung Glas [o1]", kind="opening") == "fenster"


def test_die_namensregel_sieht_die_eltern():
    assert materialwahl.art_und_herkunft("Mesh.3", namen=["Mesh.3", "Dach_Nord"]) == \
        ("dach", materialwahl.HERKUNFT_NAME)


@pytest.mark.parametrize("name, benannt", [
    ("Beton", True), ("Baum_Rinde", True), ("Terrasse Holz", True), ("Glas", True),
    ("", False), ("Material", False), ("Material.001", False), ("Default", False),
    ("DefaultMaterial", False), ("lambert1", False), ("Material #25", False),
])
def test_was_ein_benanntes_material_ist(name, benannt):
    assert materialwahl.ist_benanntes_material(name) is benannt


# ====================================================================== N5 im Runner

def test_eine_glb_ohne_arten_behaelt_ihre_benannten_materialien(tmp_path, monkeypatch):
    """Der Lauf vom 22.10.: Holzlattung fuer «uebrige» lag auf Beton, Baum und Terrasse."""
    beton = _mesh("Mesh.001", materialien=[_Material("Beton")])
    baum = _mesh("Baum_03", materialien=[_Material("Baum_Rinde"), _Material("Laub")])
    terrasse = _mesh("Terrasse", materialien=[_Material("Terrasse_Holz")])
    namenlos = _mesh("Mesh.002", materialien=[_Material("Material.001")])
    aussenwand = _mesh("Aussenwand_Sued", materialien=[_Material("Beton")])
    modul = _runner(monkeypatch, [beton, baum, terrasse, namenlos, aussenwand])

    befund = modul._materialien_setzen(_wahl(tmp_path, fassade="holzlattung-fichte",
                                             uebrige="holzlattung-fichte"))

    assert beton.material_slots[0].material.name == "Beton"
    assert [s.material.name for s in baum.material_slots] == ["Baum_Rinde", "Laub"]
    assert terrasse.material_slots[0].material.name == "Terrasse_Holz"
    assert namenlos.material_slots[0].material.name == "Materialwahl_uebrige", \
        "ohne Namen gilt die Wahl"
    assert aussenwand.material_slots[0].material.name == "Materialwahl_fassade", \
        "die Fassadentextur liegt auf der Wand"
    assert befund["objekte_je_art"]["fassade"] == 1
    assert befund["objekte_ohne_art"] == 4
    assert befund["arten"]["uebrige"]["datei_material_behalten"] == 4
    assert befund["arten"]["uebrige"]["objekte"] == 1


def test_mit_kind_gilt_die_wahl_wie_bisher(tmp_path, monkeypatch):
    """Eine Treppe der KosmoOrbit-glb (kind stair) ist «uebrige» aus der Datei — die Wahl gilt."""
    treppe = _mesh("Treppe · EG", kind="stair", materialien=[_Material("Beton")])
    modul = _runner(monkeypatch, [treppe])
    befund = modul._materialien_setzen(_wahl(tmp_path, uebrige="stampflehm"))
    assert treppe.material_slots[0].material.name == "Materialwahl_uebrige"
    assert befund["objekte_ohne_art"] == 0


# ====================================================================== Punkt 4: der Bericht

def test_der_bericht_trennt_ohne_bauteil_und_nur_behalten(tmp_path, monkeypatch):
    """Ergebnis 332: Das Fenster war nur Glas — gewollt, kein Fehlschlag."""
    fenster = _mesh("IfcWindow_F_1", kind="opening", openingType="fenster",
                    materialien=[_Material("Glas")])
    wand = _mesh("IfcWall_W_2", materialien=[_Material("Beton")])
    modul = _runner(monkeypatch, [fenster, wand])

    befund = modul._materialien_setzen(_wahl(tmp_path, fassade="sichtbeton-schalungsglatt",
                                             fenster="holzlattung-fichte",
                                             dach="klinker"))

    assert fenster.material_slots[0].material.name == "Glas"
    assert befund["nur_behalten"] == ["fenster"]
    assert befund["ohne_bauteil"] == ["dach"]
    assert befund["arten"]["fenster"]["scheiben_behalten"] == 1
    assert befund["nicht_getroffen"] == ["dach", "fenster"], "das alte Feld bleibt"
    assert "kein Fehler" in befund["lesart"]


# ====================================================================== Glas

def _principled(durchlass, rauheit, *, verbunden=False):
    eingaenge = {"Transmission Weight": SimpleNamespace(default_value=durchlass),
                 "Roughness": SimpleNamespace(default_value=rauheit, is_linked=verbunden)}
    return SimpleNamespace(type="BSDF_PRINCIPLED", inputs=eingaenge)


def _mat(*knoten):
    return SimpleNamespace(name="m", node_tree=SimpleNamespace(nodes=list(knoten)))


def test_glas_mit_durchlass_wird_glatt(monkeypatch):
    glas = _principled(0.7, 1.0)
    milch = _principled(0.7, 0.03)
    beton = _principled(0.0, 0.9)
    karte = _principled(1.0, 0.8, verbunden=True)
    modul = _runner(monkeypatch, [], [_mat(glas), _mat(milch), _mat(beton), _mat(karte)])

    befund = modul._glas_klar()

    assert glas.inputs["Roughness"].default_value == modul.GLAS_RAUHEIT_HOECHSTENS == 0.05
    assert milch.inputs["Roughness"].default_value == 0.03, "glatter bleibt glatter"
    assert beton.inputs["Roughness"].default_value == 0.9, "ohne Durchlass unberuehrt"
    assert karte.inputs["Roughness"].default_value == 0.8, "eine Karte meint die Datei"
    assert befund == {"materialien": 1, "rauheit": 0.05}


def test_die_ifc_umwandlung_schreibt_glattes_glas(tmp_path):
    spez = importlib.util.spec_from_file_location("ifc_n5_pruefling", IFC_RUNNER)
    r = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(r)
    js = {"asset": {"version": "2.0"}, "nodes": [{"name": "a"}],
          "materials": [{"name": "Beton", "pbrMetallicRoughness": {"roughnessFactor": 1.0}},
                        {"name": "Glas", "pbrMetallicRoughness": {"roughnessFactor": 1.0}}]}
    glb = _kleine_glb(tmp_path / "g.glb", js)

    r.glb_nachtragen(glb, {}, {"Glas": 0.7})

    neu = _glb_json(glb)
    assert neu["materials"][1]["pbrMetallicRoughness"]["roughnessFactor"] == 0.05
    assert neu["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"] == 1.0
    assert r.GLAS_RAUHEIT_HOECHSTENS == 0.05


def test_beide_runner_nennen_dieselbe_rauheit(monkeypatch):
    modul = _runner(monkeypatch, [])
    spez = importlib.util.spec_from_file_location("ifc_n5_pruefling2", IFC_RUNNER)
    r = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(r)
    assert modul.GLAS_RAUHEIT_HOECHSTENS == r.GLAS_RAUHEIT_HOECHSTENS
