"""Eine Variante mit einem TEIL der Kameras ihrer Grundlage — Geräteprobe R56 (23.10.2026).

Am Heim-PC bestellte die Knotenansicht eine Variante mit 2 von 3 Kameras auf einer Grundlage
mit drei Kameras, gleiche Stimmung. Bis 0.3.48 verglich der Heim-PC das Feld ``kameras`` (und
``kameras_auto``) als Ganzes: Zwei Kameras sind nicht drei — 409 beim Anlegen
(``knotenweg.grundlage_passt_nicht``) bzw. «passt nicht» beim Rechnen
(``abholer.lies_grundlage``). Die Grundbilder je Kamera lagen aber längst da.

Seither passt eine **Teilmenge**: jede bestellte Kamera steht in der Grundlage mit derselben
Kennung und derselben Pose (bei ``cameras_auto``: dieselben Werte, Richtungen eine Teilmenge).
Eine neue oder verschobene Kamera bleibt, was sie war: 409 bzw. «passt nicht».

Regel 3: alle Kameras und Modelle synthetisch.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, bruecke, knotenweg

from test_grundlage_varianten import _mit_schoenbild, _ordner, _vertrag
from test_kettenlauf_26august import _kette, _lauf


DREI = [{"name": "a", "position": [0, -30, 1.7], "target": [0, 0, 5.5], "fov": 50,
         "up_axis": "z"},
        {"name": "b", "position": [30, 0, 1.7], "target": [0, 0, 5.5], "fov": 50,
         "up_axis": "z"},
        {"name": "c", "position": [0, 30, 1.7], "target": [0, 0, 5.5], "fov": 50,
         "up_axis": "z"}]


def _mit_kameras(ordner, cameras=None, cameras_auto=None):
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    if cameras is not None:
        szene["cameras"] = cameras
    if cameras_auto is not None:
        szene["cameras"] = "auto"
        szene["cameras_auto"] = cameras_auto
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def _grundlage(tmp_path, attrappen, **kameras):
    ordner = _mit_kameras(_ordner(tmp_path, "erster", skip=True), **kameras)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return _vertrag(ordner)["grundlage"]["id"]


# ====================================================================== beim Rechnen

def test_zwei_von_drei_mitgesandten_kameras_nehmen_die_grundbilder(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage(tmp_path, attrappen, cameras=DREI)
    blender_vorher = len(protokoll["multipass"])
    assert blender_vorher == 3

    ordner = _mit_kameras(_ordner(tmp_path, "teil", vis={"grundlage": kennung, "seed": 5}),
                          cameras=[DREI[2], DREI[0]])
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert len(protokoll["render"]) == 2, "je bestellte Kamera ein KI-Lauf"
    assert _vertrag(ordner)["grundlage"] == {"id": kennung, "wiederverwendet": True}


def test_zwei_von_drei_auto_richtungen_nehmen_die_grundbilder(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage(tmp_path, attrappen,
                         cameras_auto={"richtungen": ["s", "e", "w"]})
    blender_vorher = len(protokoll["multipass"])

    ordner = _mit_kameras(_ordner(tmp_path, "teil", vis={"grundlage": kennung}),
                          cameras_auto={"richtungen": ["w", "s"]})
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher
    assert len(protokoll["render"]) == 2
    assert _vertrag(ordner)["grundlage"]["wiederverwendet"] is True


@pytest.mark.parametrize("neu", [
    [dict(DREI[0], position=[0, -31, 1.7]), DREI[1]],          # verschoben
    [DREI[0], dict(DREI[1], name="d")],                         # neue Kennung
    [DREI[0], dict(DREI[1], fov=40)],                           # andere Brennweite
])
def test_eine_neue_oder_verschobene_kamera_passt_weiter_nicht(tmp_path, neu):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage(tmp_path, attrappen, cameras=DREI)
    blender_vorher = len(protokoll["multipass"])

    ordner = _mit_kameras(_ordner(tmp_path, "anders", vis={"grundlage": kennung}),
                          cameras=neu)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "passt nicht" in antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher


def test_auto_mit_anderer_richtung_oder_anderem_wert_passt_nicht(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage(tmp_path, attrappen, cameras_auto={"richtungen": ["s", "e", "w"]})
    for i, auto in enumerate(({"richtungen": ["s", "n"]},
                              {"richtungen": ["s"], "brennweite_mm": 24})):
        ordner = _mit_kameras(_ordner(tmp_path, f"anders{i}", vis={"grundlage": kennung}),
                              cameras_auto=auto)
        antwort = _lauf(tmp_path, ordner, attrappen)
        assert antwort["tat"] != abholer.TAT_VERARBEITET
        assert "passt nicht" in antwort["grund"]


# ====================================================================== beim Anlegen (409)

def _grundlage_auftrag(ablage, kennung, **szene):
    erster = knotenweg.lege_an(ablage, dict({"geometry": {"format": "glb"}, "render": {},
                                             "vis": {}}, **szene),
                               b"glTF-erstes-modell", "m.glb", kennung="vis-1792500000-aaaaaa")
    (ablage / erster["job_id"] / bruecke.DATEI_ERGEBNIS).write_text(
        json.dumps({"grundlage": {"id": kennung, "wiederverwendet": False}}), encoding="utf-8")


def test_beim_anlegen_passt_eine_teilmenge_und_kein_fremder(tmp_path):
    kennung = "gl-0123456789abcd01"
    _grundlage_auftrag(tmp_path, kennung, cameras=DREI)
    teil = {"cameras": [DREI[1], DREI[0]], "vis": {"grundlage": kennung}}
    assert knotenweg.grundlage_passt_nicht(tmp_path, teil) is None
    fremd = {"cameras": [DREI[0], dict(DREI[1], target=[1, 0, 5.5])],
             "vis": {"grundlage": kennung}}
    satz = knotenweg.grundlage_passt_nicht(tmp_path, fremd)
    assert satz and "Kameras" in satz


def test_beim_anlegen_auto_teilmenge(tmp_path):
    kennung = "gl-0123456789abcd02"
    _grundlage_auftrag(tmp_path, kennung, cameras="auto",
                       cameras_auto={"richtungen": ["s", "e", "w"]})
    teil = {"cameras": "auto", "cameras_auto": {"richtungen": ["e", "w"]},
            "vis": {"grundlage": kennung}}
    assert knotenweg.grundlage_passt_nicht(tmp_path, teil) is None
    mehr = {"cameras": "auto", "cameras_auto": {"richtungen": ["e", "n"]},
            "vis": {"grundlage": kennung}}
    assert "Kamera" in (knotenweg.grundlage_passt_nicht(tmp_path, mehr) or "")


def test_kameras_passen_als_regel():
    a = abholer._vergleichbar({"kameras": [{"kuerzel": "a", "auge": [0, 1, 2]},
                                           {"kuerzel": "b", "auge": [3, 4, 5]}],
                               "kameras_auto": None})
    assert abholer.kameras_weichen_ab(a, dict(a, kameras=a["kameras"][1:])) == []
    assert abholer.kameras_weichen_ab(a, dict(a, kameras=[])) == ["kameras"]
    # ohne Kennung keine Zuordnung — dann nur das Ganze
    ohne = abholer._vergleichbar({"kameras": [{"kuerzel": None, "auge": [0, 1, 2]},
                                              {"kuerzel": None, "auge": [3, 4, 5]}],
                                  "kameras_auto": None})
    assert abholer.kameras_weichen_ab(ohne, dict(ohne, kameras=ohne["kameras"][:1])) \
        == ["kameras"]
