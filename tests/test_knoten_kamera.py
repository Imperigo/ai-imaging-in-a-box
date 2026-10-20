"""Knoten «Kamera», Heim-PC-Teil (H2, 20.10.2026): ``cameras_auto`` und ``CameraSpec.perspektive``.

Vertrag mit dem Integrator: ``cameras_auto {richtungen 1..8, augenhoehe_m?, brennweite_mm?
24|35|50, abstand? {art:'auto', fuellt?} | {art:'fest', meter}, perspektive?}`` — nur mit
``cameras === 'auto'``, nicht mit ``skizze``/``interior``. Vorgaben des Heim-PC: 1,70 m,
35 mm, «Haus füllt» 0,70 (Entscheid 113), senkrecht (Entscheid 109 C). Bis heute galten
Richtungen und Kamerawerte nur je Abholer, nicht je Auftrag.

Regel 3: Geometrie synthetisch (``tools/make_test_glb.py`` über ``test_knotenweg._glb``).
"""
from __future__ import annotations

import json
import math

import pytest

from aiimaging import abholer, arbeitsgang, bruecke, kameras, knotenweg, kosmo_szene

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_knotenweg import _glb

BOX = [[-6.0, -4.5, 0.0], [6.0, 4.5, 15.0]]


def _szene(**mehr):
    s = {"geometry": {"path": "/x/model.glb", "format": "glb"},
         "render": {}, "style": {"prompt": "a house"}, "vis": {}}
    s.update(mehr)
    return s


# ====================================================================== kameras.kamerasatz

def test_der_feste_abstand_gilt_und_wird_nicht_nachgeschoben():
    satz = kameras.kamerasatz(BOX, kuerzel=["s", "sSE"], abstand_fest_m=60.0)
    for k in satz["kameras"]:
        waagrecht = math.hypot(k["auge"][0] - 0.0, k["auge"][1] - 0.0)
        assert k["massgebend"] == "fest" and k["durchlaeufe"] == 0
        # Frontal steht die Kamera um FRONTAL_VERSATZ seitlich — der Abstand entlang der
        # Achse ist der bestellte.
        assert waagrecht == pytest.approx(60.0, rel=0.02), k["kuerzel"]
        assert k["vollstaendig"] is True
    assert satz["abstand_fest_m"] == 60.0


def test_zu_nah_wird_nur_gemeldet():
    satz = kameras.kamerasatz(BOX, kuerzel=["s"], abstand_fest_m=8.0)
    k = satz["kameras"][0]
    assert k["vollstaendig"] is False and satz["unvollstaendig"] == ["s"]
    assert "nicht nachgeschoben" in k["begruendung"]
    assert math.hypot(*k["auge"][:2]) == pytest.approx(8.0, rel=0.1)


def test_ohne_festen_abstand_wie_bisher():
    alt = kameras.kamerasatz(BOX, kuerzel=["s"])
    assert alt["abstand_fest_m"] is None and alt["kameras"][0]["massgebend"] != "fest"


@pytest.mark.parametrize("falsch", [0, -3, float("nan"), True])
def test_ein_unsinniger_abstand_wird_abgewiesen(falsch):
    with pytest.raises(ValueError):
        kameras.kamerasatz(BOX, kuerzel=["s"], abstand_fest_m=falsch)


# ====================================================================== lies_szene

def test_cameras_auto_mit_vorgaben():
    s = kosmo_szene.lies_szene(_szene(cameras="auto", cameras_auto={"richtungen": ["s", "nNW"]}))
    assert s["maengel"] == ()
    assert s["kameras_auto"] == {
        "richtungen": ["s", "nNW"], "augenhoehe_m": 1.70, "brennweite_mm": 35.0,
        "abstand": {"art": "auto", "fuellt": 0.70}, "perspektive": "senkrecht",
        "vorgaben": ["augenhoehe_m", "brennweite_mm", "abstand", "perspektive"]}


def test_cameras_auto_ohne_cameras_gilt_als_auto():
    s = kosmo_szene.lies_szene(_szene(cameras_auto={
        "richtungen": ["e"], "brennweite_mm": 50, "augenhoehe_m": 12,
        "abstand": {"art": "fest", "meter": 80}, "perspektive": "frei"}))
    assert s["maengel"] == ()
    assert s["kameras_auto"]["abstand"] == {"art": "fest", "meter": 80.0}
    assert s["kameras_auto"]["vorgaben"] == []


@pytest.mark.parametrize("auto, wort", [
    ({"richtungen": []}, "richtungen"),
    ({"richtungen": ["s"] * 2}, "richtungen"),
    ({"richtungen": ["sued"]}, "richtungen"),
    ({"richtungen": list(kameras.RICHTUNGSFOLGE[:9])}, "richtungen"),
    ({"richtungen": ["s"], "brennweite_mm": 28}, "brennweite_mm"),
    ({"richtungen": ["s"], "augenhoehe_m": 0.2}, "augenhoehe_m"),
    ({"richtungen": ["s"], "abstand": {"art": "auto", "fuellt": 0.1}}, "fuellt"),
    ({"richtungen": ["s"], "abstand": {"art": "fest"}}, "meter"),
    ({"richtungen": ["s"], "abstand": {"art": "fest", "meter": 1}}, "meter"),
    ({"richtungen": ["s"], "abstand": {"art": "irgendwie"}}, "abstand"),
    ({"richtungen": ["s"], "perspektive": "schraeg"}, "perspektive"),
    ({"richtungen": ["s"], "zoom": 2}, "cameras_auto.zoom"),
])
def test_falsche_auto_kameras_sind_maengel(auto, wort):
    s = kosmo_szene.lies_szene(_szene(cameras_auto=auto))
    assert any(wort in m for m in s["maengel"]), s["maengel"]


@pytest.mark.parametrize("mehr, wort", [
    ({"cameras": [{"name": "a", "position": [0, -9, 2], "target": [0, 0, 2], "up_axis": "z"}]},
     "cameras: 'auto'"),
    ({"skizze": {"quelle": "mappe", "name": "s.png"}}, "skizze"),
    ({"interior": {"rooms": "auto"}}, "interior"),
])
def test_unvertraegliches_endet_mit_satz(mehr, wort):
    s = kosmo_szene.lies_szene(_szene(cameras_auto={"richtungen": ["s"]}, **mehr))
    assert any("cameras_auto" in m and wort in m for m in s["maengel_endgueltig"])


def test_die_perspektive_der_mitgesandten_kamera():
    s = kosmo_szene.lies_szene(_szene(cameras=[
        {"name": "a", "position": [0, -9, 2], "target": [0, 0, 5], "up_axis": "z",
         "perspektive": "senkrecht"},
        {"name": "b", "position": [0, -9, 2], "target": [0, 0, 5], "up_axis": "z"}]))
    assert s["maengel"] == ()
    assert [k["perspektive"] for k in s["kameras"]] == ["senkrecht", None]
    with pytest.raises(kosmo_szene.SzenenError, match="perspektive"):
        kosmo_szene.spec_zu_kamera({"name": "c", "position": [0, 0, 0], "target": [1, 0, 0],
                                    "up_axis": "z", "perspektive": "kippen"})


# ====================================================================== der Abholer

def _bestellung(tmp_path, **mehr):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene.update(mehr)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def test_der_auftrag_bestimmt_richtungen_und_werte(tmp_path):
    ordner = _bestellung(tmp_path, cameras_auto={
        "richtungen": ["s", "nNW"], "brennweite_mm": 50, "perspektive": "senkrecht"})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen, auto_richtungen=("e",), augenhoehe=3.0)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert [kw["kamera"] for kw in protokoll["multipass"]] == ["s", "nNW"]
    for kw in protokoll["multipass"]:
        assert kw["brennweite"] == 50.0 and kw["kamera_modus"] == kameras.MODUS_SHIFT
        assert kw["deckungsgrad"] == 0.70 and kw["augenhoehe"] == 1.70, \
            "der Auftrag schlaegt die Einstellung des Abholers"
        assert "abstand_fest_m" not in kw
    angewandt = antwort["ergebnis"]["angewandt"]["cameras_auto"]
    assert angewandt["richtungen"] == ["s", "nNW"] and angewandt["perspektive"] == "senkrecht"
    assert "augenhoehe_m" in angewandt["vorgaben"]


def test_frei_und_fest(tmp_path):
    ordner = _bestellung(tmp_path, cameras_auto={
        "richtungen": ["sSE"], "perspektive": "frei", "abstand": {"art": "fest", "meter": 45}})
    protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kw = protokoll["multipass"][0]
    assert kw["kamera_modus"] == kameras.MODUS_GEKIPPT
    assert kw["abstand_fest_m"] == 45.0 and kw["deckungsgrad"] is None


def test_ohne_cameras_auto_wie_bisher(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    protokoll, attrappen = _kette(tmp_path)
    _lauf(tmp_path, ordner, attrappen)
    assert [kw["kamera"] for kw in protokoll["multipass"]] == list(abholer.AUTO_RICHTUNGEN)
    assert all("abstand_fest_m" not in kw for kw in protokoll["multipass"])


def test_senkrecht_von_hand_stellt_waagrecht_mit_shift():
    aufgabe = {"kuerzel": "a", "auge": [0.0, -20.0, 1.7], "blick_auf": [0.0, 0.0, 5.7],
               "brennweite_mm": 35.0, "perspektive": "senkrecht"}
    gestellt = abholer.senkrecht_gestellt(aufgabe)
    assert gestellt["blick_auf"][2] == 1.7, "waagrechte Achse"
    assert gestellt["shift_y"] == pytest.approx(35.0 * 4.0 / 20.0 / 36.0)
    assert abholer.senkrecht_gestellt(dict(aufgabe, perspektive="frei")) == \
        dict(aufgabe, perspektive="frei")
    assert abholer.senkrecht_gestellt(dict(aufgabe, perspektive=None))["blick_auf"][2] == 5.7


def test_senkrecht_von_hand_erreicht_den_runner(tmp_path):
    ordner = _bestellung(tmp_path, cameras=[
        {"name": "hand", "position": [0, -20, 1.7], "target": [0, 0, 5.7], "fov": 54.4,
         "up_axis": "z", "perspektive": "senkrecht"}])
    protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kw = protokoll["multipass"][0]
    assert kw["blick_auf"][2] == pytest.approx(kw["auge"][2])
    assert kw["shift_y"] > 0
    assert antwort["ergebnis"]["angewandt"]["cameras_senkrecht"] == ["hand"]


def test_die_auto_kamera_gehoert_zur_grundlage():
    assert "kameras_auto" in abholer.GRUNDLAGE_MUSS_PASSEN


# ====================================================================== die Standpunkte

def test_die_standpunkte_mit_den_parametern_des_knotens(tmp_path):
    glb = _glb(tmp_path)
    vorschau = knotenweg.heim_standpunkte(glb, "Y", kameras_auto={
        "richtungen": ["n", "e"], "augenhoehe_m": 1.7, "brennweite_mm": 24.0,
        "abstand": {"art": "fest", "meter": 50.0}, "perspektive": "senkrecht"})
    assert [s["kuerzel"] for s in vorschau["standpunkte"]] == ["n", "e"]
    assert [s["name"] for s in vorschau["standpunkte"]] == ["Nord", "Ost"]
    assert all(s["brennweite_mm"] == 24.0 for s in vorschau["standpunkte"])
    assert all(s["blick_auf"][2] == s["auge"][2] for s in vorschau["standpunkte"])


def test_alle_zwoelf_richtungen_haben_einen_namen():
    assert set(knotenweg.RICHTUNGSNAMEN) == set(kameras.RICHTUNGEN)


def test_die_abfrage_der_knotenansicht(tmp_path):
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _glb(tmp_path), name="Testbau")
    antwort = knotenweg.standpunkte_abfrage(mappe, {
        "richtungen": ["s,sSE"], "augenhoehe": ["1.6"], "brennweite": ["50"],
        "fuellt": ["0.6"], "perspektive": ["frei"]})
    assert [s["kuerzel"] for s in antwort["standpunkte"]] == ["s", "sSE"]
    assert antwort["kameras_auto"]["abstand"] == {"art": "auto", "fuellt": 0.6}
    assert antwort["kameras_auto"]["brennweite_mm"] == 50.0
    ohne = knotenweg.standpunkte_abfrage(mappe, {})
    assert [s["kuerzel"] for s in ohne["standpunkte"]] == list(abholer.AUTO_RICHTUNGEN)


@pytest.mark.parametrize("frage", [
    {"richtungen": ["s,sued"]}, {"brennweite": ["28"]}, {"fuellt": ["x"]},
    {"fuellt": ["0.7"], "abstand": ["40"]}, {"perspektive": ["schief"]},
])
def test_falsche_abfragen_sind_400(tmp_path, frage):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.standpunkte_abfrage(tmp_path / "keine", frage)
    assert fehler.value.code == 400


def test_der_weg_steht_im_server_und_in_der_app():
    from pathlib import Path
    import re
    wurzel = Path(__file__).resolve().parents[1]
    server = (wurzel / "oberflaeche" / "server.py").read_text(encoding="utf-8")
    assert 'WEG_KNOTEN_STANDPUNKTE = "/knoten/standpunkte"' in server
    swift = (wurzel / "ipad" / "Visbox.swiftpm" / "Kern" / "Knotenwege.swift").read_text(
        encoding="utf-8")
    assert re.search(r'"/knoten/standpunkte"', swift)
