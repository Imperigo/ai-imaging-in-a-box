"""Oberflächenstile aus der IFC kommen in die glb — und nur sie (F6, 08.10.2026).

**Der Anlass:** ``auf-20261007-259`` zählte im Demohaus null ``IfcSurfaceStyle``; was
ifcopenshell als Material lieferte, waren **seine eigenen** Grautöne je Bauteilart. F6 wurde
darum zurückgestellt. Seit dem 07.10.2026 schreibt der Kernel-Export von KosmoOrbit Stile je
Materialschlüssel (ROADMAP 1725/1732) — damit gibt es etwas zu übernehmen.

Was hier festgehalten wird:

* Nur ein Material mit Kennung in der Datei kommt hinein; die Vorgaben von ifcopenshell
  nicht (gemessen an ``make_test_ifc.py --stile``: Kennung 0, Name = Bauteilart).
* Die Geometrie bleibt dieselbe: gleich viele Knoten, Ecken und Dreiecke. Ohne Stile ist die
  glb dieselbe wie vor F6 — gemessen byte-gleich, und am Multipass die Tiefenkarte
  bitgleich (EXR-Pixel und PNG), 08.10.2026.
* Immer deckend: Durchsicht aus der Datei steht im Bericht, nicht in der glb, damit die
  Soll-Tiefe Fenster weiter als Fläche sieht.
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
    """Den Runner als Datei laden — nicht als Modul (Prozessgrenze, siehe
    ``tests/test_ifc_glb_filter.py``)."""
    spez = importlib.util.spec_from_file_location("ifc_stile_pruefling", RUNNER)
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
    """Den JSON-Block einer glb lesen — ohne trimesh, nur mit der Standardbibliothek."""
    daten = pfad.read_bytes()
    laenge, art = struct.unpack_from("<II", daten, 12)
    assert art == 0x4E4F534A, "erster Block der glb ist kein JSON"
    return json.loads(daten[20:20 + laenge])


def _geometrie(js: dict) -> tuple[int, int, int]:
    """(Knoten mit Mesh, Ecken, Indizes) — die Zahlen, an denen die Tiefe hängt."""
    ecken = indizes = 0
    for mesh in js.get("meshes", []):
        for teil in mesh["primitives"]:
            ecken += js["accessors"][teil["attributes"]["POSITION"]]["count"]
            indizes += js["accessors"][teil["indices"]]["count"]
    knoten = sum(1 for k in js.get("nodes", []) if "mesh" in k)
    return knoten, ecken, indizes


# ======================================================================================
# 1 · Ohne ifcopenshell: die Regeln
# ======================================================================================

def test_nur_eine_kennung_aus_der_datei_zaehlt_als_stil():
    ist = _runner().ist_stil_aus_der_datei
    assert ist(14) is True
    for keine in (0, None, "", "x", -3):
        assert ist(keine) is False


def test_srgb_wird_nach_linear_umgerechnet():
    lin = _runner().srgb_zu_linear
    assert lin(0.0) == 0.0
    assert lin(1.0) == pytest.approx(1.0)
    assert lin(0.5) == pytest.approx(0.2140, abs=1e-4)
    # Werte ausserhalb 0–1 werden geklemmt, nicht durchgereicht.
    assert lin(1.7) == pytest.approx(1.0)
    assert lin(-0.2) == 0.0


def test_der_erzeuger_schreibt_ohne_schalter_keinen_stil(tmp_path):
    text = _erzeuge(tmp_path / "t.ifc").read_text(encoding="utf-8")
    assert "IFCSURFACESTYLE" not in text and "IFCSTYLEDITEM" not in text


def test_der_erzeuger_schreibt_mit_schalter_zwei_stile_fuenf_mal(tmp_path):
    text = _erzeuge(tmp_path / "t.ifc", "--stile", "--gelaende").read_text(encoding="utf-8")
    assert text.count("IFCSURFACESTYLE(") == 2
    assert text.count("IFCSTYLEDITEM(") == 5                 # vier Wände, eine Platte
    assert "'Sichtbeton'" in text and "'Unterlagsboden'" in text


def test_ifc2x3_bekommt_die_zuweisung_dazwischen(tmp_path):
    text = _erzeuge(tmp_path / "t.ifc", "IFC2X3", "--stile").read_text(encoding="utf-8")
    assert text.count("IFCPRESENTATIONSTYLEASSIGNMENT(") == 2


def test_hochbau_mit_stilen_wird_abgewiesen(tmp_path):
    lauf = subprocess.run([sys.executable, str(ERZEUGER), str(tmp_path / "t.ifc"),
                           "--hochbau", "--stile"], capture_output=True, text=True,
                          cwd=WURZEL)
    assert lauf.returncode != 0
    assert "mit_stilen" in lauf.stderr


# ======================================================================================
# 2 · Mit .venv-ifc: die Umwandlung
# ======================================================================================

@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_die_stile_der_datei_stehen_in_der_glb(tmp_path):
    from aiimaging.seams import ifc_zu_glb
    ifc = _erzeuge(tmp_path / "t.ifc", "--stile", "--gelaende")
    bericht = ifc_zu_glb(ifc, tmp_path / "t.glb")
    assert bericht["status"] == "ok", bericht.get("error")
    namen = {m["name"]: m for m in bericht["materialien"]}
    assert set(namen) == {"Sichtbeton", "Unterlagsboden"}
    assert namen["Sichtbeton"]["n_bauteile"] == 4
    assert namen["Unterlagsboden"]["n_bauteile"] == 1
    assert namen["Sichtbeton"]["farbe_srgb"] == [0.62, 0.6, 0.56]
    assert bericht["n_bauteile_mit_stil"] == 5
    assert bericht["n_bauteile_ohne_stil"] == 1                # das Gelände

    js = _glb_json(tmp_path / "t.glb")
    in_der_glb = {m["name"]: m for m in js["materials"]}
    assert set(in_der_glb) == {"Sichtbeton", "Unterlagsboden"}
    farbe = in_der_glb["Sichtbeton"]["pbrMetallicRoughness"]["baseColorFactor"]
    assert farbe[3] == 1.0                                     # deckend
    # trimesh legt die Farbe in 8 Bit ab — auf 1/255 genau, nicht feiner.
    assert farbe[0] == pytest.approx(_runner().srgb_zu_linear(0.62), abs=1 / 255)


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_die_vorgaben_von_ifcopenshell_kommen_nicht_hinein(tmp_path):
    """Die Gegenprobe: Ohne Stil in der Datei steht kein Material in der glb — obwohl
    ifcopenshell für jedes Bauteil eines liefert."""
    from aiimaging.seams import ifc_zu_glb
    ifc = _erzeuge(tmp_path / "t.ifc", "--gelaende")
    bericht = ifc_zu_glb(ifc, tmp_path / "t.glb")
    assert bericht["materialien"] == []
    assert bericht["n_bauteile_mit_stil"] == 0
    assert bericht["n_bauteile_ohne_stil"] == bericht["n_elements"]
    assert "materials" not in _glb_json(tmp_path / "t.glb")


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_die_geometrie_bleibt_mit_und_ohne_stile_dieselbe(tmp_path):
    from aiimaging.seams import ifc_zu_glb
    ohne = ifc_zu_glb(_erzeuge(tmp_path / "a.ifc", "--gelaende"), tmp_path / "a.glb")
    mit = ifc_zu_glb(_erzeuge(tmp_path / "b.ifc", "--stile", "--gelaende"),
                     tmp_path / "b.glb")
    assert (ohne["n_elements"], ohne["n_triangles"]) == (mit["n_elements"],
                                                         mit["n_triangles"])
    assert ohne["bbox"] == mit["bbox"] and ohne["bbox_bauwerk"] == mit["bbox_bauwerk"]
    assert _geometrie(_glb_json(tmp_path / "a.glb")) == _geometrie(
        _glb_json(tmp_path / "b.glb"))
    # Dieselben Knotennamen: An ihnen hängt die Geländeregel drüben in Blender.
    namen = lambda p: sorted(k["name"] for k in _glb_json(p)["nodes"] if "mesh" in k)  # noqa: E731
    assert namen(tmp_path / "a.glb") == namen(tmp_path / "b.glb")


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_ifc2x3_liefert_dieselben_stile(tmp_path):
    from aiimaging.seams import ifc_zu_glb
    bericht = ifc_zu_glb(_erzeuge(tmp_path / "t.ifc", "IFC2X3", "--stile"),
                         tmp_path / "t.glb")
    assert {m["name"] for m in bericht["materialien"]} == {"Sichtbeton", "Unterlagsboden"}


def _blender_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_blender()).exists()
    except Exception:                                  # noqa: BLE001
        return True


@pytest.mark.skipif(_ifc_fehlt() or _blender_fehlt(), reason=".venv-ifc oder Blender fehlt")
def test_mit_stilen_und_ohne_gelaende_bleibt_die_bauwerksmaske_dieselbe(tmp_path):
    """**Der Befund nach F6 (08.10.2026), hier nachgestellt.** Ein Haus, dessen Bauteile
    alle einen Stil tragen und das kein Gelände mitbringt — der Fall des Demohauses
    (``auf-20261008-264``: 47 von 47 mit Stil). Der Material-ID-Durchgang führte danach
    Materialnamen statt Bauteilnamen, die Geländeregel fand nichts, an dem sie greifen
    konnte, und die Maske fiel weg: ``gemessen`` False, vorher True. Damit fehlte das Mass,
    das die Abwesenheit eines Bauwerks fängt.

    Seither bleibt die Kennung eines IFC-Bauteils objektweise; die Maske ist mit und ohne
    Stile Pixel für Pixel dieselbe."""
    import numpy as np
    from aiimaging import maske
    from aiimaging.seams import glb_zu_multipass, ifc_zu_glb

    masken = {}
    for name, schalter in (("ohne", ()), ("mit", ("--stile",))):
        ifc = _erzeuge(tmp_path / f"{name}.ifc", *schalter)
        assert ifc_zu_glb(ifc, tmp_path / f"{name}.glb")["status"] == "ok"
        bericht = glb_zu_multipass(tmp_path / f"{name}.glb", tmp_path / f"mp_{name}",
                                   up_axis="Y", aufloesung=128, samples=4, kamera="s")
        befund = maske.maske_aus_bericht(bericht, gelaende_erwartet=True)
        assert befund["gemessen"] is True, befund.get("grund")
        assert all(e["quelle"] == "objekt" for e in bericht["material_id_tabelle"])
        masken[name] = np.asarray(befund["maske"])
    assert np.array_equal(masken["ohne"], masken["mit"])
