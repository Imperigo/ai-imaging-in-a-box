"""A0289 «Gelände an der Form»: Heim-PC (Python) und Mac (Swift) entscheiden Gelände ohne Namen gleich.

Der Massstab ist ``aiimaging.gelaendeform`` in ihrem Einsatz in ``glbbox.bauwerksbox`` (die
Zweitmeinung: sie spricht nur, wenn die Namensregel schweigt, und kennt «nicht entscheidbar»). Der
Mac bildet sie in ``ipad/Visbox.swiftpm/Kern/Gelaendeform.swift`` ab.

Beide Seiten lesen dieselbe Probendatei (``tests/daten/glbbox_gelaenderegel.json``, Schlüssel
``formfaelle``, erzeugt von ``tools/glbbox_proben.py``):

* ``erwartet`` ist die Entscheidung des Heim-PC; diese Datei prüft, dass sie noch stimmt, und dass
  eine Regeländerung ohne neu erzeugte Datei rot wird;
* ``mac`` ist, was der Mac liefern muss; die Swift-Probe ``GelaendeformTests`` prüft es in der CI.

**Die Zielfunktion:** Anteil der Formfälle (Gruppe ``form``, mindestens 20), in denen der Mac
dieselbe Entscheidung und dieselbe Hülle liefert wie der Heim-PC: mindestens 90 %; Gegenfälle 100 %;
nie eine leere Hülle. Abweichen darf der Mac nur zu «nicht entscheidbar», nie umgekehrt.
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path

import pytest

from aiimaging import gelaendeform, glbbox, maske

WURZEL = Path(__file__).resolve().parents[1]
DATEI = WURZEL / "tests" / "daten" / "glbbox_gelaenderegel.json"
SWIFT_FORM = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Gelaendeform.swift"
SWIFT_BOX = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Modelltausch.swift"
SWIFT_PROBE = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests" / "GelaendeformTests.swift"

#: Die Fälle, in denen der Mac vom Heim-PC abweichen darf (Fertig-Satz 3), einzeln benannt. Der Grund
#: ist in beiden derselbe und steht in der Probendatei (``mac.grund``): Namensgleichheit.
MAC_DARF_ABWEICHEN = {
    "form-kein-knoten-hat-einen-namen",
    "form-gelaende-und-bauteil-gleicher-name",
}


def _werkzeug():
    spez = importlib.util.spec_from_file_location("glbbox_proben", WURZEL / "tools" / "glbbox_proben.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


DATEN = json.loads(DATEI.read_text(encoding="utf-8"))
FORMFAELLE = DATEN["formfaelle"]
NACH_NAME = {f["fall"]: f for f in FORMFAELLE}
IDS = [f["fall"] for f in FORMFAELLE]


def _bauwerksbox(fall, tmp_path):
    p = tmp_path / "probe.glb"
    _werkzeug().schreibe_glb(fall["glb"], p)
    return glbbox.bauwerksbox(p)


def _grundriss(box):
    return [box[0][0], box[0][1], box[1][0], box[1][1]]


# ---------------------------------------------------------------- Fertig-Satz 1: die Probendatei


def test_die_probendatei_traegt_genug_formfaelle():
    gruppen = [f["gruppe"] for f in FORMFAELLE]
    assert set(gruppen) == {"form", "gegenfall", "befund"}
    assert gruppen.count("form") >= 20, "der Auftrag verlangt mindestens 20 Fälle"
    assert gruppen.count("gegenfall") >= 5
    assert len(IDS) == len(set(IDS)), "Fallnamen doppelt"
    # Die Fallarten des Auftrags: Hang, Mulde, Terrasse, unter und neben dem Haus, Tiefgaragendecke,
    # Haus ohne Gelände.
    for stichwort in ("hang", "mulde", "terrasse", "unter-dem-haus", "neben-dem-haus",
                      "tiefgaragendecke", "haus-ohne-gelaende"):
        assert any(stichwort in name for name in IDS), stichwort


def test_kein_formfall_traegt_einen_gelaendenamen():
    """«Ohne erkennbaren Namen»: nur die zwei Fälle, die Namen und Form zusammen prüfen, tragen einen."""
    mit_namen = {f["fall"] for f in FORMFAELLE
                 if any(maske.ist_gelaende(k.get("name", "")) for k in f["glb"]["nodes"])}
    assert mit_namen == {"form-namen-fanden-zu-wenig", "form-namen-fanden-genug"}


@pytest.mark.parametrize("fall", FORMFAELLE, ids=IDS)
def test_der_heim_pc_entscheidet_wie_in_der_probendatei(fall, tmp_path):
    aus = _bauwerksbox(fall, tmp_path)
    soll = fall["erwartet"]
    assert aus["entschieden_durch"] == soll["entschieden_durch"]
    assert aus["n_gelaende"] == soll["gelaendeKnoten"]
    assert aus["n_knoten"] == soll["bauteile"]
    assert (aus["bbox_bauwerk"] is not None and aus["n_gelaende"] > 0) == soll["abgetrennt"]
    for ist_e, soll_e in zip(aus["bbox_szene"], soll["szenenbox"]):
        assert ist_e == pytest.approx(soll_e, abs=DATEN["toleranz_m"])
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    if soll["huellbox"] is None:
        assert not all(math.isfinite(v) for e in box for v in e)
    else:
        for ist_e, soll_e in zip(box, soll["huellbox"]):
            assert ist_e == pytest.approx(soll_e, abs=DATEN["toleranz_m"])
    assert (aus["form_befund"] is not None) == soll["form_gefragt"]
    befund = aus["form_befund"] or {}
    assert len(befund.get("gelaende") or ()) == soll["form_gelaende"]
    assert len(befund.get("unklar") or ()) == soll["form_unklar"]


@pytest.mark.parametrize("modul, name, wert", [
    (gelaendeform, "GRUNDRISSANTEIL_MIN", 0.26), (gelaendeform, "GRUNDRISSANTEIL_MIN", 0.20),
    (gelaendeform, "FLACHHEIT_MAX", 0.14), (gelaendeform, "FLACHHEIT_MAX", 0.17),
    (gelaendeform, "TIEFLAGE_MAX", 0.34), (gelaendeform, "TIEFLAGE_MAX", 0.42),
    (gelaendeform, "TIEFLAGE_UNKLAR_MAX", 0.59), (gelaendeform, "TIEFLAGE_UNKLAR_MAX", 0.65),
    (glbbox, "GERINGE_SCHRUMPFUNG", 0.0), (glbbox, "GERINGE_SCHRUMPFUNG", 0.9),
])
def test_eine_regelaenderung_ohne_neue_datei_wird_rot(modul, name, wert, monkeypatch):
    """Fertig-Satz 1: Wer eine Schwelle der Regel verschiebt, ohne die Datei neu zu erzeugen, fällt auf.

    Jede Schwelle wird in beide Richtungen verschoben; die Probendatei muss danach vom frisch
    gerechneten Stand abweichen (dieselbe Prüfung wie ``test_die_probendatei_passt_zum_kern``).
    """
    assert json.loads(json.dumps(_werkzeug().erzeuge())) == DATEN, "vor der Änderung muss die Datei passen"
    monkeypatch.setattr(modul, name, wert)
    assert json.loads(json.dumps(_werkzeug().erzeuge())) != DATEN, (
        f"{name} = {wert} ändert keinen einzigen Fall: die Probendatei bewacht diese Schwelle nicht")


def test_die_zweitmeinung_ohne_die_form_waere_ueberall_die_szenenhuelle(monkeypatch):
    """Rot vor grün, auf der Python-Seite nachgestellt: Sagt die Form immer «nicht entscheidbar»,
    trennt sie kein einziges Gelände ab; so stand der Mac vor A0289."""
    def immer_unklar(knoten, alle, **_):
        return {"name": str(knoten[0]), "urteil": gelaendeform.NICHT_ENTSCHEIDBAR, "grund": "", "merkmale": {}}
    monkeypatch.setattr(gelaendeform, "urteil", immer_unklar)
    neu = _werkzeug().erzeuge()["formfaelle"]
    assert not any(f["erwartet"]["entschieden_durch"] == "form" for f in neu)
    anders = [f["fall"] for f, alt in zip(neu, FORMFAELLE)
              if f["erwartet"]["huellbox"] != alt["erwartet"]["huellbox"]]
    assert len(anders) >= 20, anders


# ---------------------------------------------------------------- Fertig-Satz 3: die Zielfunktion


def test_zielfunktion_gleichstand_laut_probendatei():
    """Mindestens 90 % der Formfälle verlangen vom Mac genau die Python-Entscheidung; Gegenfälle 100 %."""
    form = [f for f in FORMFAELLE if f["gruppe"] == "form"]
    gleich = [f for f in form if f["mac"]["gleich"]]
    assert len(gleich) / len(form) >= 0.9, f"{len(gleich)} von {len(form)}"
    assert {f["fall"] for f in FORMFAELLE if not f["mac"]["gleich"]} == MAC_DARF_ABWEICHEN
    assert all(f["mac"]["gleich"] for f in FORMFAELLE if f["gruppe"] != "form")


@pytest.mark.parametrize("fall", FORMFAELLE, ids=IDS)
def test_was_der_mac_liefern_muss(fall):
    """Gleichstand heisst: dieselben vier Angaben. Abweichung heisst: Szenenhülle, nichts abgetrennt."""
    soll, mac = fall["erwartet"], fall["mac"]
    box = mac["huellbox"]
    assert box is not None and all(math.isfinite(v) for e in box for v in e), "nie eine leere Hülle"
    assert all(box[1][i] >= box[0][i] for i in range(3))
    if mac["gleich"]:
        assert {k: mac[k] for k in ("huellbox", "abgetrennt", "gelaendeKnoten", "entschieden_durch")} == \
               {k: soll[k] for k in ("huellbox", "abgetrennt", "gelaendeKnoten", "entschieden_durch")}
    else:
        # NUR «NICHT ENTSCHEIDBAR» STATT EINER ENTSCHEIDUNG, NIE UMGEKEHRT.
        assert soll["entschieden_durch"] == "form"
        assert mac["urteil"] == "nicht entscheidbar" and mac["grund"]
        assert mac["huellbox"] == soll["szenenbox"]
        assert mac["abgetrennt"] is False and mac["gelaendeKnoten"] == 0
        assert mac["entschieden_durch"] == "keine"


@pytest.mark.parametrize("fall", [f for f in FORMFAELLE if f["gruppe"] == "gegenfall"],
                         ids=[f["fall"] for f in FORMFAELLE if f["gruppe"] == "gegenfall"])
def test_gegenfaelle_verlieren_nichts_vom_grundriss(fall):
    """Kein Gelände, eine Tiefgaragendecke, ein Flachdach: kein Haus wird als Gelände entfernt."""
    soll = fall["erwartet"]
    assert soll["abgetrennt"] is False and soll["gelaendeKnoten"] == 0
    assert soll["entschieden_durch"] == "keine"
    assert soll["huellbox"] == soll["szenenbox"]


def test_die_form_trennt_in_den_formfaellen_wirklich_gelaende_ab():
    """Die Probe ist nicht leer: In der Mehrzahl der Formfälle entscheidet am Heim-PC die Form, und
    die Hülle wird im Grundriss enger als die Szene."""
    form = [f for f in FORMFAELLE if f["gruppe"] == "form" and f["mac"]["gleich"]]
    durch_form = [f for f in form if f["erwartet"]["entschieden_durch"] == "form"]
    assert len(durch_form) >= 15
    for f in durch_form:
        e = f["erwartet"]
        assert _grundriss(e["huellbox"]) != _grundriss(e["szenenbox"]), f["fall"]
    unter = NACH_NAME["form-ebene-unter-dem-haus"]["erwartet"]
    (x0, y0, _), (x1, y1, z1) = unter["huellbox"]
    assert (x1 - x0, y1 - y0, z1) == pytest.approx((12.0, 10.0, 9.0))


# ---------------------------------------------------------------- die Swift-Seite, soweit hier lesbar


def test_der_mac_fuehrt_dieselben_schwellen_wie_der_heim_pc():
    """Die Schwellen in ``Gelaendeform.swift`` sind ein Abbild; sie stehen hier gegen Python fest."""
    text = SWIFT_FORM.read_text(encoding="utf-8")

    def zahl(name):
        m = re.search(r"static let " + name + r"\s*=\s*([0-9.]+)", text)
        assert m, name
        return float(m.group(1))

    assert zahl("grundrissanteilMin") == gelaendeform.GRUNDRISSANTEIL_MIN
    assert zahl("flachheitMax") == gelaendeform.FLACHHEIT_MAX
    assert zahl("tieflageMax") == gelaendeform.TIEFLAGE_MAX
    assert zahl("tieflageUnklarMax") == gelaendeform.TIEFLAGE_UNKLAR_MAX
    assert zahl("geringeSchrumpfung") == glbbox.GERINGE_SCHRUMPFUNG
    assert f'nichtEntscheidbar = "{gelaendeform.NICHT_ENTSCHEIDBAR}"' in text


def test_der_mac_fragt_die_form_und_die_swift_probe_liest_die_formfaelle():
    assert "Gelaendeform.zweitmeinung(" in SWIFT_BOX.read_text(encoding="utf-8")
    probe = SWIFT_PROBE.read_text(encoding="utf-8")
    assert '"formfaelle"' in probe and "glbbox_gelaenderegel.json" in probe
    for name in MAC_DARF_ABWEICHEN:
        assert name in NACH_NAME


def test_die_familienpruefung_ist_am_heim_pc_vorgabe_aus():
    """Der Mac bildet sie nicht ab, weil ``bauwerksbox`` sie nicht einschaltet. Ändert sich das,
    muss der Mac nachziehen: dann wird diese Probe rot."""
    import inspect
    assert inspect.signature(gelaendeform.gelaende_knoten).parameters["als_familie"].default is False
    assert "als_familie" not in inspect.getsource(glbbox._zweitmeinung)


# ---------------------------------------------------------------- Befunde am Heim-PC (gemeldet, nicht verändert)


def test_befund_namensgleichheit_der_heim_pc_trennt_nach_namen(tmp_path):
    """A0289, Befund 1 (gemeldet): ``bauwerksbox`` trennt die Form-Treffer nach ihrem NAMEN ab.

    Tragen Gelände und Bauteile denselben Namen, geht das Bauteil mit hinaus; trägt kein Knoten einen
    Namen, bleibt kein Bauteil und die Box ist nicht endlich. Der Mac sagt in beiden Fällen «nicht
    entscheidbar». Wird der Heim-PC hier berichtigt, wird diese Probe rot: dann die Probendatei neu
    erzeugen, und die Abweichung des Mac fällt weg.
    """
    ohne = _bauwerksbox(NACH_NAME["form-kein-knoten-hat-einen-namen"], tmp_path)
    assert ohne["entschieden_durch"] == "form" and ohne["n_bauwerk"] == 0
    assert not all(math.isfinite(v) for e in ohne["bbox_bauwerk"] for v in e)
    gleich = _bauwerksbox(NACH_NAME["form-gelaende-und-bauteil-gleicher-name"], tmp_path)
    assert gleich["n_gelaende"] == 2 and len(gleich["form_befund"]["gelaende"]) == 1
    (_, _, z0), (_, _, z1) = gleich["bbox_bauwerk"]
    assert (z0, z1) == pytest.approx((6.0, 9.0)), "nur das Dach bleibt, das Geschoss ging mit dem Gelände"


def test_befund_die_form_haelt_eine_bodenplatte_fuer_gelaende():
    """A0289, Befund 2 (gemeldet): Eine Bodenplatte über den ganzen Grundriss ist gross, flach und
    unten; die Formregel kann sie von Gelände nicht unterscheiden. Beide Seiten entscheiden gleich."""
    for name in ("befund-bodenplatte-ganzer-grundriss", "befund-fundament-mit-ueberstand",
                 "befund-tiefgarage-mit-bodenplatte"):
        f = NACH_NAME[name]
        assert f["gruppe"] == "befund" and f["mac"]["gleich"]
        assert f["erwartet"]["entschieden_durch"] == "form" and f["erwartet"]["form_gelaende"] == 1
    platte = NACH_NAME["befund-bodenplatte-ganzer-grundriss"]["erwartet"]
    assert _grundriss(platte["huellbox"]) == _grundriss(platte["szenenbox"])
    assert platte["huellbox"][0][2] - platte["szenenbox"][0][2] == pytest.approx(0.3)
