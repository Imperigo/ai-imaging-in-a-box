"""Dach, Fenster, Glas und Gelände kommen aus der IFC mit ihrer Art in die glb (22.10.2026).

**Der Anlass** (Mac-Demolauf 22.10.2026, ``auf-20261022-331``): Die glb der Mappe hatte kein
Dach, kein Fenster, kein Material und keinen Boden. Die Ursache lag **nicht** in der
Umwandlung, sondern in der Datei — ein Export, der Dächer, Fenster und Stile nicht schrieb
(dieselben Zahlen wie ``auf-20261007-259``: 32 Wände, 2 Decken, 1 Möbel, 39 leere
Ausschnitte, kein Stil). Die Umwandlung hat das aber **nicht gesagt**, und drei Lücken der
Umwandlung selbst kamen dabei ans Licht:

* Eine Dachplatte (``IfcSlab`` unter einem ``IfcRoof``) hiess nach dem Export ``IfcSlab_…``
  und wurde in Blender zu «boden»;
* eine Scheibe mit Durchsicht kam als deckende hellgraue Platte an;
* ein Gelände, das die ``IfcSite`` selbst trägt, fand ``gelaende_in_glb`` nicht.

Geprüft wird zuerst **ohne ifcopenshell** (die Regeln als reine Funktionen), dann mit dem
``.venv-ifc`` an der synthetischen Datei ``make_test_ifc.py --dach-fenster --site-gelaende``.
"""
from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
RUNNER = WURZEL / "src" / "aiimaging" / "runners" / "ifc_to_glb_runner.py"
ERZEUGER = WURZEL / "tools" / "make_test_ifc.py"


def _runner():
    """Den Runner als Datei laden — nicht als Modul (Prozessgrenze)."""
    spez = importlib.util.spec_from_file_location("ifc_merkmale_pruefling", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


def _erzeuge(ziel: Path, *argumente: str) -> Path:
    subprocess.run([sys.executable, str(ERZEUGER), str(ziel), *argumente], check=True,
                   capture_output=True, cwd=WURZEL)
    return ziel


def _glb_json(pfad: Path) -> dict:
    daten = pfad.read_bytes()
    laenge, art = struct.unpack_from("<II", daten, 12)
    assert art == 0x4E4F534A
    return json.loads(daten[20:20 + laenge])


def _kleine_glb(pfad: Path, js: dict, binaer: bytes = b"\x01\x02\x03\x04") -> Path:
    """Eine glb aus JSON und Binärblock — Standardbibliothek allein."""
    roh = json.dumps(js).encode("utf-8")
    roh += b" " * (-len(roh) % 4)
    binaer += b"\x00" * (-len(binaer) % 4)
    gesamt = 12 + 8 + len(roh) + 8 + len(binaer)
    pfad.write_bytes(b"glTF" + struct.pack("<II", 2, gesamt)
                     + struct.pack("<II", len(roh), 0x4E4F534A) + roh
                     + struct.pack("<II", len(binaer), 0x004E4942) + binaer)
    return pfad


# ======================================================================================
# 1 · Ohne ifcopenshell: die Regeln
# ======================================================================================

def test_dachplatte_unter_einem_dach_wird_dach_und_nicht_boden():
    from aiimaging.materialwahl import art_von
    m = _runner().knoten_merkmale("IfcSlab", "NOTDEFINED", "IfcRoof")
    assert m == {"ifc_type": "IfcSlab", "kind": "roof", "teil_von": "IfcRoof"}
    assert art_von("IfcSlab_Dachplatte_x", kind=m["kind"]) == "dach"
    # Die Gegenprobe: ohne Merkmal bleibt dieselbe Platte, was sie vorher war.
    assert art_von("IfcSlab_Dachplatte_x") == "boden"


def test_platte_mit_typ_roof_wird_dach_auch_ohne_ganzes():
    m = _runner().knoten_merkmale("IfcSlab", "roof")
    assert m["kind"] == "roof" and m["PredefinedType"] == "ROOF"
    assert "teil_von" not in m


def test_fenster_und_tuer_tragen_opening_mit_ihrer_art():
    from aiimaging.materialwahl import art_von
    k = _runner().knoten_merkmale
    fenster, tuer = k("IfcWindow"), k("IfcDoor", "DOOR")
    assert (fenster["kind"], fenster["openingType"]) == ("opening", "fenster")
    assert (tuer["kind"], tuer["openingType"]) == ("opening", "tuer")
    assert art_von("IfcWindow_F_x", kind="opening", opening_type="fenster") == "fenster"
    # Türen bleiben «uebrige» (Entscheid 113) — wie vorher über das Präfix.
    assert art_von("IfcDoor_T_x", kind="opening", opening_type="tuer") == "uebrige"
    # Ein Teil eines Fensters (Rahmenprofil als IfcMember) wird Fenster, nicht «uebrige».
    assert k("IfcMember", None, "IfcWindow")["openingType"] == "fenster"


def test_gelaende_typ_bekommt_die_rolle_ground():
    m = _runner().knoten_merkmale("IfcSite")
    assert m["role"] == "ground"
    assert "role" not in _runner().knoten_merkmale("IfcSlab", "BASESLAB")


def test_nichtssagende_vordefinierte_typen_bleiben_draussen():
    k = _runner().knoten_merkmale
    assert "PredefinedType" not in k("IfcWall", "NOTDEFINED")
    assert "PredefinedType" not in k("IfcWall", "USERDEFINED")
    assert k("IfcWall", None) == {"ifc_type": "IfcWall"}


def test_dachtypen_gleich_wie_in_der_materialwahl():
    """Zwei Listen, eine Regel — der Test ersetzt den Import über die Prozessgrenze."""
    from aiimaging import materialwahl
    assert tuple(_runner().DACH_TYPEN) == tuple(materialwahl.DACH_TYPEN)


def test_jede_art_aus_den_merkmalen_stimmt_mit_der_materialwahl():
    """``kind`` muss in ``KIND_ZU_ART`` stehen — sonst fällt ``art_von`` stumm auf den
    Namen zurück, und das Merkmal wäre wirkungslos."""
    from aiimaging.materialwahl import KIND_ZU_ART
    for _, merkmal in _runner().GANZES_ZU_MERKMAL:
        assert merkmal["kind"] in KIND_ZU_ART


def test_nachtragen_schreibt_extras_und_durchlass_und_laesst_die_geometrie(tmp_path):
    from aiimaging import kosmo_szene
    js = {"asset": {"version": "2.0"},
          "nodes": [{"name": "IfcSite_G_1", "mesh": 0}, {"name": "IfcWindow_F_2", "mesh": 1},
                    {"name": "IfcWall_W_3", "mesh": 2, "extras": {"alt": 1}}],
          "meshes": [{"primitives": [{"attributes": {}, "material": 0}]},
                     {"primitives": [{"attributes": {}, "material": 1}]},
                     {"primitives": [{"attributes": {}, "material": 0}]}],
          "materials": [{"name": "Beton"}, {"name": "Glas"}],
          "buffers": [{"byteLength": 4}]}
    glb = _kleine_glb(tmp_path / "a.glb", js)
    vorher_bin = glb.read_bytes()[-12:]
    r = _runner()
    gesagt = r.glb_nachtragen(glb, {"IfcSite_G_1": {"role": "ground"},
                                    "IfcWindow_F_2": {"kind": "opening"},
                                    "IfcWall_W_3": {"ifc_type": "IfcWall"}},
                              {"Glas": 0.7})
    assert gesagt == {"knoten": 3, "materialien": 1}
    daten = glb.read_bytes()
    assert daten[-12:] == vorher_bin                       # Binärblock unverändert
    assert struct.unpack_from("<I", daten, 8)[0] == len(daten)
    assert struct.unpack_from("<I", daten, 12)[0] % 4 == 0
    neu = _glb_json(glb)
    assert neu["nodes"][2]["extras"] == {"alt": 1, "ifc_type": "IfcWall"}
    glas = neu["materials"][1]
    assert glas["extensions"]["KHR_materials_transmission"]["transmissionFactor"] == 0.7
    assert glas["alphaMode"] == "OPAQUE"                   # deckend: die Tiefe sieht sie
    assert "extensions" not in neu["materials"][0]
    assert neu["extensionsUsed"] == ["KHR_materials_transmission"]
    # Der Leser drüben findet den Boden jetzt an der Rolle.
    assert kosmo_szene.gelaende_in_glb(glb)["knoten"] == ["IfcSite_G_1"]


def test_ohne_durchlass_kein_extensions_used(tmp_path):
    js = {"asset": {"version": "2.0"}, "nodes": [{"name": "a"}],
          "materials": [{"name": "Beton"}]}
    glb = _kleine_glb(tmp_path / "b.glb", js)
    _runner().glb_nachtragen(glb, {"a": {"ifc_type": "IfcWall"}}, {})
    assert "extensionsUsed" not in _glb_json(glb)


def test_der_demohaus_export_ohne_dach_fenster_und_farben_wird_gemeldet():
    """Die Zahlen der Datei aus ``auf-20261007-259`` — derselbe Bestand wie die glb des
    Mac-Demolaufs (``auf-20261022-331``: 32 IfcWall, 2 IfcSlab, 1 Möbel, 0 Materialien)."""
    saetze = _runner().warnungen_aus_bestand(
        {"IfcWall": 32, "IfcSlab": 2, "IfcRoof": 0, "IfcOpeningElement": 39,
         "IfcWindow": 0, "IfcDoor": 0, "dachplatten": 0, "fuellungen": 0}, n_stile=0)
    text = " ".join(saetze)
    assert len(saetze) == 3
    assert "KEIN DACH" in text and "FENSTER NUR ALS LÖCHER" in text and "39" in text
    assert "KEINE FARBEN" in text


def test_der_heutige_demohaus_export_meldet_nichts():
    """Die Gegenprobe mit den Zahlen aus ``auf-20261008-264`` (Export mit Dächern,
    Fenstern und sieben Stilen) — eine Warnung, die immer kommt, liest niemand."""
    assert _runner().warnungen_aus_bestand(
        {"IfcWall": 32, "IfcSlab": 2, "IfcRoof": 2, "IfcOpeningElement": 39,
         "IfcWindow": 8, "IfcDoor": 31, "dachplatten": 0, "fuellungen": 39},
        n_stile=7) == []


def test_der_erzeuger_schreibt_dach_fenster_und_tuer_nur_mit_schalter(tmp_path):
    ohne = _erzeuge(tmp_path / "a.ifc").read_text(encoding="utf-8")
    for wort in ("IFCROOF(", "IFCWINDOW(", "IFCDOOR(", "IFCOPENINGELEMENT("):
        assert wort not in ohne
    mit = _erzeuge(tmp_path / "b.ifc", "--dach-fenster").read_text(encoding="utf-8")
    assert mit.count("IFCROOF(") == 1 and mit.count("IFCWINDOW(") == 1
    assert mit.count("IFCDOOR(") == 1 and mit.count("IFCOPENINGELEMENT(") == 2
    assert mit.count("IFCRELVOIDSELEMENT(") == 2 and mit.count("IFCRELFILLSELEMENT(") == 2
    assert "'Glas'" in mit and "IFCSURFACESTYLERENDERING(" in mit


def test_der_erzeuger_gibt_der_site_nur_mit_schalter_geometrie(tmp_path):
    def site(*a):
        text = _erzeuge(tmp_path / "s.ifc", *a).read_text(encoding="utf-8")
        return next(z for z in text.splitlines() if "IFCSITE(" in z)
    assert ",$,$,.ELEMENT." in site()
    assert ",$,$,.ELEMENT." not in site("--site-gelaende")


def test_ohne_neue_schalter_bleibt_die_datei_dieselbe(tmp_path):
    """Jede bestehende Messreihe hängt an der Vorgabedatei — sie bleibt Zeichen für Zeichen."""
    a = _erzeuge(tmp_path / "a.ifc", "--stile", "--gelaende").read_bytes()
    sys.path.insert(0, str(WURZEL / "tools"))
    try:
        import make_test_ifc
    finally:
        sys.path.pop(0)
    b = make_test_ifc.erzeuge_ifc(tmp_path / "a2.ifc", mit_stilen=True, mit_gelaende=True,
                                  dach_fenster=False, site_gelaende=False)
    assert b.read_bytes().replace(b"a2.ifc", b"a.ifc") == a


def test_hochbau_mit_dach_fenster_wird_abgewiesen(tmp_path):
    lauf = subprocess.run([sys.executable, str(ERZEUGER), str(tmp_path / "t.ifc"),
                           "--hochbau", "--dach-fenster"], capture_output=True, text=True,
                          cwd=WURZEL)
    assert lauf.returncode != 0 and "dach_fenster" in lauf.stderr


def test_der_importeur_reicht_die_warnungen_der_umwandlung_weiter(tmp_path, monkeypatch):
    from aiimaging import importeur, seams
    ifc = _erzeuge(tmp_path / "t.ifc")

    def falsch(quelle, ziel, **_):
        Path(ziel).write_bytes(b"glTF")
        return {"status": "ok", "glb_path": str(ziel), "up_axis": "Y",
                "warnungen": ["KEIN DACH IN DER DATEI: …"]}
    monkeypatch.setattr(seams, "ifc_zu_glb", falsch)
    bericht = importeur.importiere(ifc, tmp_path / "t.glb")
    assert "KEIN DACH IN DER DATEI: …" in bericht["hinweise"]


# ======================================================================================
# 2 · Mit .venv-ifc: die Umwandlung
# ======================================================================================

@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_dach_fenster_glas_und_gelaende_kommen_mit_ihrer_art_an(tmp_path, schema):
    from aiimaging import kosmo_szene
    from aiimaging.materialwahl import art_von
    from aiimaging.seams import ifc_zu_glb
    ifc = _erzeuge(tmp_path / "t.ifc", schema, "--dach-fenster", "--site-gelaende",
                   "--stile")
    bericht = ifc_zu_glb(ifc, tmp_path / "t.glb")
    assert bericht["status"] == "ok", bericht.get("error")
    # Site, Bodenplatte, vier Wände, Dachplatte, Fenster, Tür.
    assert bericht["n_elements"] == 9
    assert bericht["uebersprungen"] == {"IfcOpeningElement": 2}
    assert bericht["geometrie_fehler"] == {} and bericht["ohne_geometrie"] == {}
    assert (bericht["n_dach_knoten"], bericht["n_oeffnungs_knoten"],
            bericht["n_gelaende_knoten"]) == (1, 2, 1)
    assert bericht["warnungen"] == []
    assert bericht["materialien_mit_durchlass"] == 1

    js = _glb_json(tmp_path / "t.glb")
    arten = {}
    for k in js["nodes"]:
        if "mesh" not in k:
            continue
        e = k.get("extras") or {}
        assert e.get("ifc_type"), k["name"]
        arten[k["name"].split("_")[0] + "_" + k["name"].split("_")[1]] = art_von(
            k["name"], kind=e.get("kind"), predefined=e.get("PredefinedType"),
            opening_type=e.get("openingType"), ist_gelaende=e.get("role") == "ground")
    assert arten["IfcSlab_Dachplatte"] == "dach"
    assert arten["IfcSlab_Bodenplatte"] == "boden"
    assert arten["IfcWindow_Fenster-Sued"] == "fenster"
    assert arten["IfcDoor_Tuer-Nord"] == "uebrige"
    assert arten["IfcSite_Gelaende"] == "gelaende"
    glas = next(m for m in js["materials"] if m["name"] == "Glas")
    assert glas["extensions"]["KHR_materials_transmission"]["transmissionFactor"] == \
        pytest.approx(0.7)
    assert glas.get("alphaMode", "OPAQUE") == "OPAQUE"
    assert glas["pbrMetallicRoughness"]["baseColorFactor"][3] == 1.0
    assert kosmo_szene.gelaende_in_glb(tmp_path / "t.glb")["n_gelaende"] == 1
    # Das Dach schliesst das Haus oben: Hüllbox bis 3,0 + 0,2 m.
    assert bericht["bbox_bauwerk"][1][2] == pytest.approx(3.2, abs=1e-6)


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_der_quader_ohne_dach_und_stil_wird_gemeldet(tmp_path):
    from aiimaging.seams import ifc_zu_glb
    bericht = ifc_zu_glb(_erzeuge(tmp_path / "t.ifc"), tmp_path / "t.glb")
    text = " ".join(bericht["warnungen"])
    assert "KEIN DACH" in text and "KEINE FARBEN" in text
    assert "LÖCHER" not in text                         # er hat keine Ausschnitte
