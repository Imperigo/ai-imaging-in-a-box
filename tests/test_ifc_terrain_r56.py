"""Das Gelände einer IFC als ``IfcGeographicElement`` mit ``PredefinedType .TERRAIN.`` (R56/R57).

**Anlass (Geräteprobe R56, 23.10.2026):** Renders mit Innenraum gehen als IFC an den Heim-PC;
im Bild «Eingang» fehlte das Gelände, über den glb-Weg ist es da. Befund: Die IFC-Ausfuhr der
Bestellseite schreibt eine ``IfcSite`` ohne Geometrie und **keine** Geländefläche — es gibt
nichts, was unsere Umwandlung verlieren könnte. Die Bestellseite baut die Fläche für R57 als
``IfcGeographicElement`` mit ``PredefinedType .TERRAIN.`` ein.

Bei uns hätte sie bis 0.3.48 trotzdem nicht als Gelände gegolten:

* die Umwandlung (``ifc_to_glb_runner``) gab nur der ``IfcSite`` ``role: ground`` und zählte
  jedes ``IfcGeographicElement`` in die Bauwerksbox;
* die Bauwerksmaske prüfte die Umfeld-Klasse (Klassenanfang ``IfcGeographicElement``) VOR
  der Rolle und vor dem Namen — die Fläche wäre «Umfeld» gewesen wie ein Baum, und die
  Rolle (``nach_rolle``) war ausdrücklich nur ausserhalb des Umfelds zugelassen.

Seither: ``TERRAIN`` (oder ein Geländewort in ``ObjectType``/``Name``) → ``role: ground`` in
der glb, nicht in der Bauwerksbox; in der Maske gehen Rolle und Geländename vor der
Umfeld-Klasse. Der Klassenanfang allein bleibt Umfeld (ein Baum bleibt ein Baum).

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from aiimaging import maske

from test_ifc_merkmale import ERZEUGER, WURZEL, _glb_json, _ifc_fehlt, _runner


# ====================================================================== die Umwandlung (ohne ifcopenshell)

def test_terrain_bekommt_die_rolle_ground():
    k = _runner().knoten_merkmale
    m = k("IfcGeographicElement", "TERRAIN")
    assert m["role"] == "ground" and m["PredefinedType"] == "TERRAIN"


@pytest.mark.parametrize("objekttyp, name", [("Gelaendeflaeche", None), ("TERRAIN", None),
                                             (None, "Geländefläche"),
                                             (None, "Gelaende gewachsen")])
def test_gelaendewort_in_objekttyp_oder_name_genuegt(objekttyp, name):
    m = _runner().knoten_merkmale("IfcGeographicElement", "USERDEFINED",
                                  objekttyp=objekttyp, name=name)
    assert m.get("role") == "ground"


def test_ein_baum_bleibt_umfeld_und_ohne_rolle():
    k = _runner().knoten_merkmale
    assert "role" not in k("IfcGeographicElement", None, name="Baum")
    assert "role" not in k("IfcGeographicElement", "USERDEFINED", objekttyp="Baum")
    # Nur die Klasse IfcGeographicElement liest das Wort — eine Wand «Gelaende» nicht.
    assert "role" not in k("IfcWall", None, name="Gelaende")


def test_die_woerter_des_runners_kennt_auch_die_maske():
    """Zwei Listen, eine Regel — der Test ersetzt den Import über die Prozessgrenze."""
    assert set(_runner().GELAENDE_OBJEKTWOERTER) <= set(maske.GELAENDE_WOERTER)


# ====================================================================== die Maske

ROT, GRUEN, BLAU = (255, 38, 38), (38, 255, 38), (38, 38, 255)
FARBEN = [ROT, ROT, GRUEN, GRUEN, GRUEN, BLAU, (0, 0, 0), (0, 0, 0)]


def _tabelle(gelaende_name):
    return [{"index": 0, "name": "IfcWall_Wand_1", "quelle": "objekt",
             "farbe_srgb_8bit": list(ROT)},
            {"index": 1, "name": gelaende_name, "quelle": "objekt",
             "farbe_srgb_8bit": list(GRUEN)},
            {"index": 2, "name": "IfcGeographicElement_Baum_3", "quelle": "objekt",
             "farbe_srgb_8bit": list(BLAU)}]


def test_terrain_mit_rolle_ist_gelaende_und_nicht_umfeld():
    flaeche = "IfcGeographicElement_Flaeche_2"
    m = maske.bauwerksmaske(FARBEN, _tabelle(flaeche), gelaende_rolle=(flaeche,))
    assert flaeche in m["gelaende_namen"]
    assert m["gelaende_nach_rolle"] == (flaeche,)
    assert m["umfeld_namen"] == ["IfcGeographicElement_Baum_3"]
    assert m["maske"] == [True, True, False, False, False, False, False, False]


def test_ein_gelaendename_am_geographic_element_ist_gelaende():
    """Die Namensregel als Brücke: auch ohne Rolle (z. B. eine glb ohne extras)."""
    flaeche = "IfcGeographicElement_Gelaendeflaeche_2"
    m = maske.bauwerksmaske(FARBEN, _tabelle(flaeche))
    assert flaeche in m["gelaende_namen"]
    assert flaeche not in m["umfeld_namen"]
    assert not maske.ist_umfeld(flaeche)
    assert maske.ist_umfeld("IfcGeographicElement_Baum_3")


def test_die_kontextmaske_zaehlt_das_terrain_nicht_als_umfeld():
    flaeche = "IfcGeographicElement_Flaeche_2"
    k = maske.kontextmaske(FARBEN, _tabelle(flaeche), gelaende_rolle=(flaeche,))
    assert k["namen"]["umfeld"] == ["IfcGeographicElement_Baum_3"]
    assert k["quellen"]["umfeld"] == 1


# ====================================================================== die synthetische IFC

def _erzeuge(ziel, *argumente):
    subprocess.run([sys.executable, str(ERZEUGER), str(ziel), *argumente], check=True,
                   capture_output=True, cwd=WURZEL)
    return ziel


def test_der_erzeuger_schreibt_das_terrain_nur_mit_schalter(tmp_path):
    ohne = _erzeuge(tmp_path / "a.ifc").read_text(encoding="utf-8")
    assert "IFCGEOGRAPHICELEMENT(" not in ohne
    mit = _erzeuge(tmp_path / "b.ifc", "--terrain").read_text(encoding="utf-8")
    zeile = next(z for z in mit.splitlines() if "IFCGEOGRAPHICELEMENT(" in z)
    assert ".TERRAIN." in zeile and "'Flaeche'" in zeile
    assert "IFCRELCONTAINEDINSPATIALSTRUCTURE(" in mit


def test_terrain_in_ifc2x3_wird_abgewiesen(tmp_path):
    """IFC2X3 kennt ``IfcGeographicElement`` nicht — ifcopenshell liesse es still fallen."""
    lauf = subprocess.run([sys.executable, str(ERZEUGER), str(tmp_path / "t.ifc"), "IFC2X3",
                           "--terrain"], capture_output=True, text=True, cwd=WURZEL)
    assert lauf.returncode != 0 and "IFC4" in lauf.stderr


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_das_terrain_kommt_als_boden_in_die_glb(tmp_path):
    from aiimaging import kosmo_szene
    from aiimaging.seams import ifc_zu_glb
    ifc = _erzeuge(tmp_path / "t.ifc", "--terrain")
    bericht = ifc_zu_glb(ifc, tmp_path / "t.glb")
    assert bericht["status"] == "ok", bericht.get("error")
    assert bericht["n_gelaende_knoten"] == 1
    js = _glb_json(tmp_path / "t.glb")
    terrain = [k for k in js["nodes"] if k.get("name", "").startswith("IfcGeographicElement")]
    assert terrain and all((k.get("extras") or {}).get("role") == "ground" for k in terrain)
    assert kosmo_szene.gelaende_in_glb(tmp_path / "t.glb")["n_gelaende"] == 1
    # Die Fläche reicht weit über das Haus — in der Bauwerksbox steht sie nicht.
    assert bericht["bbox_bauwerk"][1][0] < bericht["bbox"][1][0]
