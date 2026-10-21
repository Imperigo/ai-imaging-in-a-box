"""Die Steine-Probe (auf-20261021-316) — Materialkennungen, Boden, Form. Ohne Blender.

Der Befund der HomeStation an der synthetischen Probedatei von KosmoDraw (19 600 Backsteine
als Instanzen eines Meshes, ausgerollt zu 19 600 Objekten mit geteiltem Mesh):

* B2 — je Objekt eine Kennung, Namen rekursiv verkettet («MATID_030_MATID_029_…»), bei 255
  Zeichen abgeschnitten, Kennfarben doppelt. Die Planung steht jetzt in
  ``aiimaging.material_id`` und wird hier an genau dieser Lage geprüft.
* B3 — der Boden («boden») zählte als Bauwerk. Zwei Wege heraus: die Rolle am Knoten
  (``extras.role = "ground"``, ``kosmo_szene.gelaende_in_glb``) und die Form, deren
  Objektnamen der Runner jetzt um die Materiale ergänzt, die nur dort hängen.
"""
from __future__ import annotations

import colorsys
import json
import struct
import time
from pathlib import Path

import pytest

from aiimaging import abholer, gelaendeform, kosmo_szene, maske, material_id, seams

RUNNER_QUELLE = seams.BLENDER_RUNNER.read_text(encoding="utf-8")


def _palette(index: int):
    """Die Palette des Runners (Goldener Winkel, S 0,85, V 1,0) — hier nur als Prüfstück."""
    return colorsys.hsv_to_rgb((index * 0.618033988749895) % 1.0, 0.85, 1.0)


def _steine_szene(n_steine: int = 19600) -> list[dict]:
    objekte = [{"name": "boden", "mesh": "boden", "slots": ["boden"], "ifc": False}]
    for seite in ("nord", "ost", "sued", "west"):
        objekte.append({"name": f"fuge_{seite}", "mesh": "moertelplatte", "slots": ["moertel"],
                        "ifc": False})
    for i in range(n_steine):
        name = "steine_nord" if i == 0 else f"steine_nord.{i:03d}"
        objekte.append({"name": name, "mesh": "stein", "slots": ["backstein"], "ifc": False})
    return objekte


# ── B2: eine Kennung je Material ──────────────────────────────────────────────────────

def test_steine_bekommen_drei_kennungen_statt_19605():
    plan = material_id.plane_material_ids(_steine_szene(), _palette)
    tabelle = plan["tabelle"]
    assert [e["name"] for e in tabelle] == ["boden", "moertel", "backstein"]
    assert [e["quelle"] for e in tabelle] == ["material"] * 3
    assert [e["n_objekte"] for e in tabelle] == [1, 4, 19600]
    assert all("MATID" not in e["name"] for e in tabelle), "Namen nie aus Kennungen bilden"
    assert len({tuple(e["farbe_srgb_8bit"]) for e in tabelle}) == 3
    assert plan["zuweisung"]["steine_nord.123"] == {"art": "slots", "indizes": [2]}


def test_kennungsname_verkettet_nie():
    assert material_id.kennungsname(2, "backstein") == "MATID_002_backstein"


def test_erste_farben_bleiben_die_bisherigen():
    """Wer keine geteilten Meshes hat, sieht dieselben Indizes und Farben wie vor dem Fix."""
    objekte = [{"name": f"Wand_{i}", "mesh": f"m{i}", "slots": [f"Stoff_{i}"], "ifc": False}
               for i in range(12)]
    tabelle = material_id.plane_material_ids(objekte, _palette)["tabelle"]
    for e in tabelle:
        assert e["farbe_srgb_8bit"] == [int(round(k * 255.0)) for k in _palette(e["index"])]


def test_kennfarben_bleiben_eindeutig_auch_bei_vielen_eintraegen():
    objekte = [{"name": f"Teil_{i:05d}", "mesh": f"m{i}", "slots": [f"Stoff_{i}"], "ifc": False}
               for i in range(1000)]
    tabelle = material_id.plane_material_ids(objekte, _palette)["tabelle"]
    farben = [tuple(e["farbe_srgb_8bit"]) for e in tabelle]
    assert len(farben) == 1000 and len(set(farben)) == 1000


def test_zu_viele_kennungen_scheitern_laut():
    with pytest.raises(material_id.MaterialIdError):
        material_id.plane_material_ids(
            [{"name": f"T{i}", "mesh": f"m{i}", "slots": [f"S{i}"]} for i in range(3)],
            lambda i: (1.0, 0.15, 0.15))


def test_ohne_material_eine_kennung_je_geteiltem_mesh():
    objekte = [{"name": f"Stein.{i:03d}", "mesh": "stein", "slots": [], "ifc": False}
               for i in range(50)]
    objekte.append({"name": "Einzeln", "mesh": "eigen", "slots": [None], "ifc": False})
    plan = material_id.plane_material_ids(objekte, _palette)
    assert [(e["name"], e["quelle"], e["n_objekte"]) for e in plan["tabelle"]] == [
        ("Einzeln", "objekt", 1), ("Stein.000", "objekt", 50)]
    assert plan["zuweisung"]["Stein.049"] == {"art": "objekt", "index": 1, "am_objekt": False}


def test_ifc_bauteil_am_geteilten_mesh_behaelt_seine_kennung_je_objekt():
    objekte = [{"name": f"IfcWall_Wand_{i}", "mesh": "wand", "slots": ["Beton"], "ifc": True}
               for i in range(3)]
    plan = material_id.plane_material_ids(objekte, _palette)
    assert [e["name"] for e in plan["tabelle"]] == [f"IfcWall_Wand_{i}" for i in range(3)]
    assert all(z["am_objekt"] for z in plan["zuweisung"].values())


def test_runner_plant_vor_dem_tausch():
    """Der Runner nutzt den Plan und bildet keine Kennungsnamen mehr selbst."""
    assert "plane_material_ids" in RUNNER_QUELLE
    assert 'f"MATID_{' not in RUNNER_QUELLE
    assert "bbox_bauwerk_gelaende_materialien" in RUNNER_QUELLE


# ── B3: der Boden ─────────────────────────────────────────────────────────────────────

def _glb(pfad: Path, js: dict) -> Path:
    roh = json.dumps(js).encode()
    roh += b" " * (-len(roh) % 4)
    pfad.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(roh))
                     + struct.pack("<II", len(roh), 0x4E4F534A) + roh)
    return pfad


def _steine_glb(pfad: Path, *, rolle: bool, boden_material: int = 2) -> Path:
    boden = {"name": "boden", "mesh": 2}
    if rolle:
        boden["extras"] = {"role": "ground"}
    return _glb(pfad, {
        "asset": {"version": "2.0"},
        "nodes": [{"name": "steine_nord", "mesh": 0}, {"name": "fuge_nord", "mesh": 1}, boden],
        "meshes": [{"name": "stein", "primitives": [{"material": 0}]},
                   {"name": "moertelplatte", "primitives": [{"material": 1}]},
                   {"name": "boden", "primitives": [{"material": boden_material}]}],
        "materials": [{"name": "backstein"}, {"name": "moertel"}, {"name": "boden"}]})


def test_rolle_ground_wird_gelesen(tmp_path):
    b = kosmo_szene.gelaende_in_glb(_steine_glb(tmp_path / "a.glb", rolle=True))
    assert b["knoten"] == ["boden"] and b["materialien"] == ["boden"] and b["geteilt"] == []
    assert b["namen"] == ["boden"]


def test_ohne_rolle_kein_befund(tmp_path):
    assert kosmo_szene.gelaende_in_glb(_steine_glb(tmp_path / "a.glb", rolle=False)) is None
    assert kosmo_szene.gelaende_in_glb(tmp_path / "fehlt.glb") is None


def test_geteiltes_material_wird_nicht_uebertragen(tmp_path):
    """Teilt der Boden sein Material mit dem Mörtel, darf er es nicht mitnehmen."""
    b = kosmo_szene.gelaende_in_glb(_steine_glb(tmp_path / "a.glb", rolle=True, boden_material=1))
    assert b["materialien"] == [] and b["geteilt"] == ["moertel"] and b["namen"] == ["boden"]


ROT, GRAU, BRAUN = (255, 38, 38), (38, 255, 38), (38, 38, 255)
TABELLE = [{"index": 0, "name": "boden", "quelle": "material", "farbe_srgb_8bit": list(BRAUN)},
           {"index": 1, "name": "moertel", "quelle": "material", "farbe_srgb_8bit": list(GRAU)},
           {"index": 2, "name": "backstein", "quelle": "material", "farbe_srgb_8bit": list(ROT)}]
FARBEN = [ROT, ROT, GRAU, BRAUN, BRAUN, BRAUN, (0, 0, 0), (0, 0, 0)]


def test_boden_mit_rolle_faellt_aus_der_bauwerksmaske():
    ohne = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_erwartet=False)
    assert ohne["n_bauwerk"] == 6, "so war es in 316: der Boden zaehlte mit"
    mit = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_erwartet=False,
                              gelaende_rolle=("boden",))
    assert mit["n_bauwerk"] == 3 and mit["n_gelaende"] == 3
    # auf-20261021-318 B2: angeglichen an «name+form» — die Namensregel steht immer vorn.
    assert mit["gelaende_quelle"] == "name+rolle"
    assert mit["gelaende_nach_rolle"] == ("boden",)
    assert mit["bauwerk_namen"] == ["backstein", "moertel"]
    assert not any("Eine der beiden Angaben stimmt nicht" in w for w in mit["warnungen"])
    # Mit erwartetem Gelaende traegt die Rolle die Maske, statt sie auf None zu setzen.
    erwartet = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_rolle=("boden",))
    assert erwartet["maske"] == [True, True, True, False, False, False, False, False]


def test_wort_boden_bleibt_ausserhalb_der_namensregel():
    """Die Rolle ersetzt das Wort nicht: «boden» als Name allein bleibt Bauwerk."""
    assert "boden" in maske.WOERTER_AUSDRUECKLICH_NICHT
    assert not maske.ist_gelaende("boden")


def test_formbruecke_traegt_die_eigenen_materiale():
    bericht = {"bbox_bauwerk_entschieden_durch": "form",
               "bbox_bauwerk_gelaende_namen": ["Bodenkoerper"],
               "bbox_bauwerk_gelaende_materialien": ["boden"]}
    assert abholer._formgelaende_aus_bericht(bericht) == ("Bodenkoerper", "boden")


def test_form_rechnet_auch_ausgerollte_instanzen_schnell():
    """19 600 Steine plus Boden: vorher quadratisch (Szenenbox je Knoten), jetzt linear."""
    alle = [("boden", (-11.0, -0.2, -7.0), (11.0, 0.0, 7.0))]
    for i in range(19600):
        x = -10.0 + (i % 140) * 0.143
        y = (i // 140) * 0.043
        alle.append((f"stein.{i}", (x, y, -6.0), (x + 0.24, y + 0.07, -5.885)))
    beginn = time.monotonic()
    befund = gelaendeform.gelaende_knoten(alle, hoch=1)
    assert time.monotonic() - beginn < 10.0
    assert befund["gelaende"] == ("boden",)


def test_glb_mit_rolle_aendert_nur_den_knoten(tmp_path):
    quelle = _steine_glb(tmp_path / "q.glb", rolle=False)
    vorher = quelle.read_bytes()
    kosmo_szene.glb_mit_rolle(quelle, tmp_path / "z.glb", "boden")
    assert quelle.read_bytes() == vorher, "die Quelle bleibt unberuehrt"
    assert kosmo_szene.gelaende_in_glb(tmp_path / "z.glb")["knoten"] == ["boden"]
    with pytest.raises(ValueError):
        kosmo_szene.glb_mit_rolle(quelle, tmp_path / "x.glb", "gibt_es_nicht")


def test_werkzeug_glb_rolle_drueckt_seine_schalter(tmp_path):
    import importlib.util
    pfad = Path(__file__).resolve().parents[1] / "tools" / "glb_rolle.py"
    spec = importlib.util.spec_from_file_location("werkzeug_glb_rolle", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    quelle = _steine_glb(tmp_path / "q.glb", rolle=False)
    assert modul.main([str(quelle), str(tmp_path / "z.glb"), "--knoten", "boden",
                       "--rolle", "terrain"]) == 0
    assert kosmo_szene.gelaende_in_glb(tmp_path / "z.glb")["knoten"] == ["boden"]
    assert modul.main([str(quelle), str(quelle), "--knoten", "boden"]) == 2


def test_quelle_wie_in_318_ohne_und_mit_rolle_gleich_gebaut():
    """auf-20261021-318: ohne Rolle «name+form», mit Rolle bis dahin «rolle» — jetzt «name+rolle»."""
    ohne = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_zusatz=("boden",))
    mit = maske.bauwerksmaske(FARBEN, TABELLE, gelaende_zusatz=("boden",), gelaende_rolle=("boden",))
    assert ohne["gelaende_quelle"] == "name+form" and ohne["gelaende_von_aussen"] == ("boden",)
    assert mit["gelaende_quelle"] == "name+rolle" and mit["gelaende_von_aussen"] == ()
    assert mit["maske"] == ohne["maske"]          # bildpunktgleich, wie 318 gemessen
