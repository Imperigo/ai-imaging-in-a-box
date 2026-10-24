"""Die Neutralisierung einer IFC (Auftrag 354) — Texte schwärzen, Namen tilgen, Lage entfernen.

Drei Gruppen:

A · ohne ifcopenshell — Wortregeln, Prüfung auf neutrale Werte, Bericht, Aufruf des
    Werkzeugs, Aufbau des Subprozesses. Laufen immer.
B · mit ``.venv-ifc`` — der echte Runner an der Probe ``make_test_ifc.py --beschriftung``
    (alle Werte erfunden: «Muster AG», «Musterstrasse 1»), in IFC4 und IFC2X3. Ohne venv
    übersprungen, wie die übrigen IFC-Proben.
C · mit ``.venv-ifc`` — die Kopie geht weiter durch ``seams.ifc_zu_glb``, mit derselben
    Zahl Bauteile (abzüglich des Signets) und derselben Hüllbox.

Testdaten nur synthetisch (Regel 3) — es gibt hier keine echte Datei, und es darf keine geben.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import REPO, RUNNER_DIR

RUNNER = RUNNER_DIR / "ifc_neutral_runner.py"
ERZEUGER = REPO / "tools" / "make_test_ifc.py"
WERKZEUG = REPO / "tools" / "ifc_neutralisieren.py"


def _als_datei(pfad: Path, name: str):
    """Ein Skript als Datei laden — nicht als Modul des Pakets (Prozessgrenze)."""
    spez = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def r():
    return _als_datei(RUNNER, "ifc_neutral_pruefling")


@pytest.fixture(scope="module")
def werkzeug():
    return _als_datei(WERKZEUG, "ifc_neutral_werkzeug")


def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


def _erzeuge(ziel: Path, *argumente: str) -> Path:
    subprocess.run([sys.executable, str(ERZEUGER), str(ziel), *argumente], check=True,
                   capture_output=True, cwd=REPO)
    return ziel


# ======================================================================================
# A · ohne ifcopenshell
# ======================================================================================

def test_runner_laedt_ohne_ifcopenshell(r):
    """Die Regeln stehen oben im Runner und brauchen die Bibliothek nicht."""
    assert "ifcopenshell" not in sys.modules
    assert callable(r.ist_neutral)


def test_behaltene_woerter_gibt_nur_listenwoerter_aus(r):
    """Aus «Musterwand» wird «wand» — nie ein Wort des Originals."""
    assert r.behaltene_woerter("Musterwand Muster AG") == ["wand"]
    assert r.behaltene_woerter("Aussenwand Sichtbeton") == ["wand", "sichtbeton"]
    assert r.behaltene_woerter("Muster AG") == []
    assert r.behaltene_woerter("Satteldach Nord") == ["dach"]
    assert r.behaltene_woerter("Dachfenster") == ["dachfenster"]


def test_gelaende_nur_als_ganzes_wort(r):
    """«Gelaender» (Handlauf) ist kein Gelände; «Gelände_Hang» schon."""
    assert "gelaende" not in r.behaltene_woerter("Gelaender Balkon")
    assert r.behaltene_woerter("Gelände_Hang")[0] == "gelaende"
    assert r.behaltene_woerter("Composite Wall") == ["wall"]   # kein «site»


def test_bauteilname_rolle_vorn(r):
    """Das Rollenwort steht vorn — der glb-Knotenname kürzt nach 24 Zeichen."""
    assert r.bauteilname("IfcSlab", 3, "Gelaende Muster", None) == "gelaende IfcSlab 3"
    assert r.bauteilname("IfcWall", 17, "Muster AG", "") == "IfcWall 17"
    assert r.bauteilname("IfcWall", 2, "Aussenwand Beton", None) == "wand beton IfcWall 2"


def test_materialname(r):
    assert r.materialname("Sichtbeton Muster AG", 1) == "Sichtbeton"
    assert r.materialname("Muster-Spezial", 2) == "Material 2"
    assert r.materialname(None, 3) == "Material 3"


def test_material_n_gilt_im_kern_als_unbenannt(r):
    """Ein getilgter Materialname soll keine Wahl auslösen, die ein Stoffname auslöst."""
    from aiimaging import materialwahl
    assert not materialwahl.ist_benanntes_material(r.materialname("Muster", 4))
    assert materialwahl.ist_benanntes_material(r.materialname("Beton Muster", 4))


def test_materialwoerter_decken_die_bibliothek(r):
    """Die Stofffamilien der Bibliothek stehen in der Liste — Kopie statt Import."""
    from aiimaging import materialwahl
    for familie in set(materialwahl.FAMILIE.values()):
        assert familie in r.MATERIALWOERTER, familie


def test_rollenwoerter_decken_die_namensregeln(r):
    """Was ``materialwahl`` und die Geländeregel am Namen lesen, überlebt die Neutralisierung."""
    from aiimaging import maske, materialwahl
    erlaubt = set(r.ROLLENWOERTER) | set(r.GELAENDE_GANZWORT)
    for _art, woerter in materialwahl.NAME_ZU_ART:
        for w in woerter:
            assert r.normalwort(w) in erlaubt, w
    for w in materialwahl.NAME_OEFFNUNG + materialwahl.NAME_TUER:
        assert r.normalwort(w) in erlaubt, w
    for w in maske.GELAENDE_WOERTER:
        if w != "site":                                 # mit Absicht nicht, siehe Runner
            assert r.normalwort(w) in erlaubt, w


@pytest.mark.parametrize("name, erwartet", [
    ("Signet Muster AG", True), ("Logo", True), ("Text_Nord", True),
    ("Beschriftungstafel", True), ("Plan-Nr 12", True), ("Schriftzug Muster", True),
    ("Wand", False), ("Textilfassade", False), ("Design Muster", False), (None, False),
])
def test_beschriftung_erkannt(r, name, erwartet):
    assert r.ist_beschriftung(name) is erwartet


@pytest.mark.parametrize("klasse, attribut, wert", [
    ("IfcWall", "Name", "IfcWall 17"),
    ("IfcSlab", "Name", "gelaende IfcSlab 3"),
    ("IfcBuilding", "Name", "Gebäude 1"),
    ("IfcBuildingStorey", "Name", "Geschoss 0"),
    ("IfcProject", "Name", "Projekt"),
    ("IfcMaterial", "Name", "Sichtbeton"),
    ("IfcSurfaceStyle", "Name", "Beton Grau"),
    ("IfcShapeRepresentation", "RepresentationType", "SweptSolid"),
    ("IfcGeometricRepresentationContext", "ContextType", "Model"),
    ("IfcPropertySet", "Name", "Pset_WallCommon"),
    ("IfcElementQuantity", "Name", "Qto_WallBaseQuantities"),
    ("IfcConversionBasedUnit", "Name", "DEGREE"),
    ("HEADER", "description", "ViewDefinition [ReferenceView_V1.2]"),
    ("IfcPerson", "FamilyName", "Visbox"),
])
def test_neutral(r, klasse, attribut, wert):
    assert r.ist_neutral(klasse, attribut, wert)


@pytest.mark.parametrize("klasse, attribut, wert", [
    ("IfcWall", "Name", "Muster AG"),
    ("IfcWall", "Name", "muster IfcWall 3"),          # Rolle nicht in der Liste
    ("IfcPropertySet", "Name", "Pset_MusterAG"),       # Firmensatz, kein Normsatz
    ("IfcPropertySingleValue", "Name", "Verfasser"),
    ("IfcShapeRepresentation", "RepresentationType", "Muster"),
    ("IfcPostalAddress", "Town", "Musterstadt"),
    ("HEADER", "author", "Max Muster"),
    ("IfcSite", "LandTitleNumber", "GB-1234"),
])
def test_nicht_neutral(r, klasse, attribut, wert):
    assert not r.ist_neutral(klasse, attribut, wert)


def test_normeigenschaft_nur_im_normsatz(r):
    assert r.ist_neutral("IfcPropertySingleValue", "Name", "IsExternal", normsatz=True)
    assert not r.ist_neutral("IfcPropertySingleValue", "Name", "IsExternal")


def test_georef_satz(r):
    assert r.ist_georef_satz("ePset_MapConversion")
    assert r.ist_georef_satz("ePSet_ProjectedCRS")
    assert not r.ist_georef_satz("Pset_WallCommon")


def test_resttexte_nennen_nur_klasse_und_attribut(r):
    rest = r.resttexte_zusammenfassen([("IfcWall", "Name"), ("IfcWall", "Name"),
                                       ("HEADER", "author")])
    assert rest == {"anzahl": 3, "stellen": [
        {"klasse": "HEADER", "attribut": "author", "anzahl": 1},
        {"klasse": "IfcWall", "attribut": "Name", "anzahl": 2}]}
    assert r.resttexte_zusammenfassen([]) == {"anzahl": 0, "stellen": []}


def test_urteil(werkzeug):
    ok = {"resttexte": {"anzahl": 0, "stellen": []}, "n_entfernt_summe": 5,
          "n_umbenannt": 3, "n_bauteile": {"vorher": 7, "nachher": 6},
          "georeferenz_entfernt": True}
    code, satz = werkzeug.urteil(ok)
    assert code == werkzeug.OK and satz.startswith("0 Resttexte")
    rest = dict(ok, resttexte={"anzahl": 2, "stellen": [
        {"klasse": "IfcWall", "attribut": "Name", "anzahl": 2}]})
    code, satz = werkzeug.urteil(rest)
    assert code == werkzeug.RESTTEXTE and "IfcWall.Name" in satz and "NICHT" in satz
    assert werkzeug.urteil({})[0] == werkzeug.GESCHEITERT


def test_werkzeug_weist_gleiche_datei_ab(werkzeug, tmp_path):
    ein = tmp_path / "a.ifc"
    ein.write_text("ISO-10303-21;", encoding="utf-8")
    assert werkzeug.main([str(ein), str(ein)]) == werkzeug.AUFRUF_FALSCH
    assert werkzeug.main([str(ein), str(tmp_path / "b.glb")]) == werkzeug.AUFRUF_FALSCH
    (tmp_path / "b.ifc").write_text("x", encoding="utf-8")
    assert werkzeug.main([str(ein), str(tmp_path / "b.ifc")]) == werkzeug.AUFRUF_FALSCH
    assert ein.read_text(encoding="utf-8") == "ISO-10303-21;"


def test_werkzeug_bericht_und_rueckgabe(werkzeug, tmp_path, monkeypatch, capsys):
    """Resttexte > 0 → Rückgabe 3; der Bericht geht als Datei und auf stdout."""
    ein = tmp_path / "a.ifc"
    ein.write_text("ISO-10303-21;", encoding="utf-8")
    bericht = {"status": "ok", "resttexte": {"anzahl": 1, "stellen": [
        {"klasse": "IfcWall", "attribut": "Name", "anzahl": 1}]}}
    monkeypatch.setattr(werkzeug.seams, "ifc_neutralisieren",
                        lambda *a, **k: bericht)
    datei = tmp_path / "b.json"
    code = werkzeug.main([str(ein), str(tmp_path / "b.ifc"), "--bericht", str(datei)])
    assert code == werkzeug.RESTTEXTE
    assert json.loads(datei.read_text(encoding="utf-8")) == bericht
    assert json.loads(capsys.readouterr().out) == bericht


def test_werkzeug_ueberschreibt_nur_ausdruecklich(werkzeug, tmp_path, monkeypatch):
    ein, aus = tmp_path / "a.ifc", tmp_path / "b.ifc"
    ein.write_text("x", encoding="utf-8")
    aus.write_text("alt", encoding="utf-8")
    gesehen = {}

    def neutral(e, a, **k):
        gesehen.update(k)
        return {"status": "ok", "resttexte": {"anzahl": 0, "stellen": []}}

    monkeypatch.setattr(werkzeug.seams, "ifc_neutralisieren", neutral)
    assert werkzeug.main([str(ein), str(aus)]) == werkzeug.AUFRUF_FALSCH
    assert werkzeug.main([str(ein), str(aus), "--ueberschreiben"]) == werkzeug.OK
    assert gesehen == {"ueberschreiben": True}


def _fake(stdout: str, code: int = 0):
    return SimpleNamespace(returncode=code, stdout=stdout, stderr="Traceback /pfad/geheim")


def test_naht_baut_den_aufruf(tmp_path, monkeypatch):
    from aiimaging import seams
    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/venv-ifc/bin/python")
    ein = tmp_path / "a.ifc"
    ein.write_text("ISO-10303-21;", encoding="utf-8")
    gesehen = {}

    def starte(cmd, frist):
        gesehen["cmd"], gesehen["frist"] = cmd, frist
        return _fake(json.dumps({"status": "ok", "resttexte": {"anzahl": 0}}))

    bericht = seams.ifc_neutralisieren(ein, tmp_path / "b.ifc", _starte=starte)
    assert bericht["status"] == "ok"
    assert gesehen["cmd"] == ["/venv-ifc/bin/python", str(seams.IFC_NEUTRAL_RUNNER),
                              str(ein), str(tmp_path / "b.ifc")]
    assert gesehen["frist"] >= seams.GESAMTFRIST_IFC_S


def test_naht_nennt_keinen_pfad_im_fehler(tmp_path, monkeypatch):
    """Ein Pfad kann einen Projektnamen tragen (Regel 3) — die Meldung wiederholt ihn nicht."""
    from aiimaging import seams
    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/venv-ifc/bin/python")
    ein = tmp_path / "Projekt-Muster" / "a.ifc"
    with pytest.raises(seams.SeamError) as fehler:
        seams.ifc_neutralisieren(ein, tmp_path / "b.ifc", _starte=lambda c, f: _fake("{}"))
    assert "Muster" not in str(fehler.value)
    ein.parent.mkdir()
    ein.write_text("x", encoding="utf-8")
    with pytest.raises(seams.SeamError) as fehler:
        seams.ifc_neutralisieren(
            ein, tmp_path / "b.ifc",
            _starte=lambda c, f: _fake(json.dumps({"status": "error",
                                                   "error": "OSError beim Neutralisieren"}), 1))
    assert "Muster" not in str(fehler.value) and "geheim" not in str(fehler.value)


def test_naht_schuetzt_die_eingabe(tmp_path, monkeypatch):
    from aiimaging import seams
    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/venv-ifc/bin/python")
    ein = tmp_path / "a.ifc"
    ein.write_text("x", encoding="utf-8")
    nie = lambda c, f: pytest.fail("darf nicht starten")       # noqa: E731
    with pytest.raises(seams.SeamError, match="dieselbe Datei"):
        seams.ifc_neutralisieren(ein, ein, _starte=nie)
    (tmp_path / "b.ifc").write_text("y", encoding="utf-8")
    with pytest.raises(seams.SeamError, match="gibt es schon"):
        seams.ifc_neutralisieren(ein, tmp_path / "b.ifc", _starte=nie)


def test_erzeuger_ohne_schalter_unveraendert(tmp_path):
    """``--beschriftung`` ist additiv: ohne den Schalter dieselbe Datei wie zuvor."""
    a = _erzeuge(tmp_path / "t.ifc").read_text(encoding="utf-8")
    assert "Muster" not in a and "IFCANNOTATION" not in a


def test_erzeuger_beschriftung_traegt_die_falschen_namen(tmp_path):
    text = _erzeuge(tmp_path / "t.ifc", "--beschriftung").read_text(encoding="utf-8")
    for teil in ("Muster AG", "Musterstrasse 1", "IFCANNOTATION", "IFCTEXTLITERALWITHEXTENT",
                 "IFCMAPCONVERSION", "(47,22,0,0)", "Signet Muster AG", "Pset_MusterAG",
                 "IFCCLASSIFICATIONREFERENCE"):
        assert teil in text, teil
    text2 = _erzeuge(tmp_path / "t2.ifc", "IFC2X3", "--beschriftung").read_text(
        encoding="utf-8")
    assert "ePset_MapConversion" in text2 and "IFCMAPCONVERSION" not in text2


# ======================================================================================
# B · der echte Runner
# ======================================================================================

_ohne_venv = pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")

#: Jedes erfundene Wort der Probe — keines davon darf in der Kopie stehen.
ERFUNDEN = ("muster", "testfixture", "max@", "+00 000", "gb-", "epsg", "2600000",
            "1200000", "47,22", "8,32", "architekt", "planverfasser", "signet", "musterland")


def _neutral(tmp_path, *argumente):
    from aiimaging import seams
    ein = _erzeuge(tmp_path / "ein.ifc", *argumente, "--beschriftung")
    vor = hashlib.sha256(ein.read_bytes()).hexdigest()
    bericht = seams.ifc_neutralisieren(ein, tmp_path / "aus.ifc")
    assert hashlib.sha256(ein.read_bytes()).hexdigest() == vor, "Eingabe verändert"
    return ein, tmp_path / "aus.ifc", bericht


@_ohne_venv
@pytest.mark.parametrize("argumente", [("IFC4", "--stile", "--gelaende"), ("IFC2X3", "MILLI")])
def test_kopie_ohne_jeden_namen(tmp_path, argumente):
    _ein, aus, bericht = _neutral(tmp_path, *argumente)
    assert bericht["status"] == "ok"
    assert bericht["resttexte"] == {"anzahl": 0, "stellen": []}
    text = aus.read_text(encoding="utf-8").lower()
    for wort in ERFUNDEN:
        assert wort not in text, wort
    assert bericht["georeferenz_entfernt"] is True
    assert bericht["landeskoordinaten"] is False
    assert bericht["beschriftung_entfernt"] == ["IfcBuildingElementProxy 1"]
    assert bericht["n_bauteile"]["nachher"] == bericht["n_bauteile"]["vorher"] - 1
    for klasse in ("IfcAnnotation", "IfcTextLiteralWithExtent", "IfcTextStyle",
                   "IfcPostalAddress", "IfcTelecomAddress", "IfcClassificationReference"):
        assert bericht["n_entfernt"].get(klasse) == 1, klasse


@_ohne_venv
def test_bericht_nennt_keinen_wert(tmp_path):
    _ein, _aus, bericht = _neutral(tmp_path, "IFC4")
    text = json.dumps(bericht, ensure_ascii=False).lower()
    for wort in ERFUNDEN:
        assert wort not in text, wort


@_ohne_venv
def test_kopie_behaelt_was_das_bild_traegt(tmp_path):
    """Klasse, PredefinedType, Stoffwort, Farbe, Rollenwort — und neue GlobalIds."""
    ein, aus, _ = _neutral(tmp_path, "IFC4", "--stile", "--gelaende", "--dach-fenster")
    alt, neu = ein.read_text(encoding="utf-8"), aus.read_text(encoding="utf-8")
    assert "IFCMATERIAL('Sichtbeton'" in neu
    assert re.search(r"IFCSLAB\('[^']+',#\d+,'gelaende IfcSlab \d+'", neu)
    assert ".BASESLAB." in neu and ".FLOOR." in neu
    assert alt.count("IFCOPENINGELEMENT") == neu.count("IFCOPENINGELEMENT") > 0
    assert alt.count("IFCCOLOURRGB") == neu.count("IFCCOLOURRGB")
    assert "IFCMAPCONVERSION" in neu and "0.,0.,0.," in neu
    guids_alt = set(re.findall(r"IFC[A-Z]+\('([0-9A-Za-z_$]{22})'", alt))
    guids_neu = set(re.findall(r"IFC[A-Z]+\('([0-9A-Za-z_$]{22})'", neu))
    assert guids_neu and not guids_alt & guids_neu


@_ohne_venv
def test_landeskoordinaten_werden_gewarnt_nicht_verschoben(tmp_path):
    """Die Lage in der Geometrie selbst lässt sich nicht tilgen, ohne sie zu verschieben —
    das tut die Neutralisierung nicht; sie sagt es (ohne Zahl)."""
    from aiimaging import seams
    ein = _erzeuge(tmp_path / "ein.ifc")
    text = ein.read_text(encoding="utf-8").replace(
        "IFCCARTESIANPOINT((0.000000,0.000000,0.000000))",
        "IFCCARTESIANPOINT((2600000.,1200000.,400.))", 1)
    ein.write_text(text, encoding="utf-8")
    bericht = seams.ifc_neutralisieren(ein, tmp_path / "aus.ifc")
    assert bericht["landeskoordinaten"] is True
    assert any("Landeskoordinaten" in w for w in bericht["warnungen"])
    assert "2600000" not in json.dumps(bericht)
    assert "2600000." in (tmp_path / "aus.ifc").read_text(encoding="utf-8")


@_ohne_venv
def test_kopie_ist_gueltig(tmp_path):
    from aiimaging import seams
    _ein, aus, _ = _neutral(tmp_path, "IFC4", "--stile")
    erg = subprocess.run([seams.finde_ifc_python(), "-m", "ifcopenshell.validate", str(aus)],
                         capture_output=True, text=True, timeout=300)
    assert "No validation issues found" in erg.stdout + erg.stderr, erg.stdout[-800:]


# ======================================================================================
# C · die Kopie läuft weiter
# ======================================================================================

@_ohne_venv
@pytest.mark.parametrize("argumente", [("IFC4", "--stile", "--gelaende"), ("IFC2X3", "MILLI")])
def test_kopie_wird_zur_glb(tmp_path, argumente):
    from aiimaging import seams
    ein, aus, bericht = _neutral(tmp_path, *argumente)
    vor = seams.ifc_zu_glb(ein, tmp_path / "ein.glb")
    nach = seams.ifc_zu_glb(aus, tmp_path / "aus.glb")
    assert nach["status"] == "ok"
    assert nach["n_elements"] == vor["n_elements"] - len(bericht["beschriftung_entfernt"])
    assert sum(nach["bbox"], []) == pytest.approx(sum(vor["bbox"], []))
    if "--gelaende" in argumente:
        from aiimaging import maske
        daten = (tmp_path / "aus.glb").read_bytes()
        laenge = int.from_bytes(daten[12:16], "little")
        namen = [k.get("name", "") for k in json.loads(daten[20:20 + laenge])["nodes"]]
        assert any(maske.ist_gelaende(n) for n in namen), "Gelände am Namen verloren"
