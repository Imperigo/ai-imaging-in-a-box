"""Eine Blender-Grundlage, mehrere deckungsgleiche Varianten — Owner-Grundsatz Nr. 85.

Aus dem Demolauf vom 16.10.2026 (Fehlerprotokoll Nr. 81, 83, 84, 85) und dem Vertrag mit
dem Integrator vom 20.10.2026:

* **Nr. 83 — «nur Cycles» rechnet.** ``vis.skip`` heisst «nur Grundlage»: Blender und
  Ebenen, kein Bildmodell; das Cycles-Bild ist das gelieferte Bild (Auflage 3). Vom
  26.08. bis 20.10.2026 hiess es bei uns «gar nichts rechnen».
* **Nr. 85 — die Grundlage wird wiederverwendet.** Jeder Lauf, der Blender rechnet, meldet
  ``grundlage {id, wiederverwendet: false}``; ein Auftrag mit ``vis.grundlage`` rechnet
  kein Blender und keine Auto-Kamera neu.
* **Auflage 4 — eine Grundlage, die nicht passt, wird laut abgelehnt** (Aufloesung,
  Samples, Kameras), weil ueber ``vis_render`` ohne Knoten bestellt werden kann.
* **Nr. 84 — ein fester Startwert.** ``vis.seed`` rechnet genau diesen einen statt der
  Auswahl aus drei; gemeldet wird er je Kamera, mit der gerechneten Pose.

Regel 3: alle Modelle und Kameras synthetisch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, kosmo_szene

from test_kettenlauf_26august import MINI_PNG, _auftragsordner, _kette, _lauf


def _mit_schoenbild(attrappen):
    """Der Multipass der Attrappe schreibt auch das Schoenbild, wie der echte Runner."""
    echt = attrappen["_multipass"]

    def multipass(glb, aus, **kw):
        bericht = echt(glb, aus, **kw)
        schoen = Path(aus) / "beauty_.png"
        schoen.write_bytes(MINI_PNG)
        return dict(bericht, beauty_png=str(schoen))

    return dict(attrappen, _multipass=multipass)


def _ordner(tmp_path, name, *, skip=False, vis=None, render=None):
    """Ein Auftragsordner; ``vis``/``render`` werden in die Szene gemischt."""
    basis = tmp_path / "auftraege" / name
    basis.mkdir(parents=True)
    ordner = _auftragsordner(basis, skip=skip)
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis or {})
    szene["render"].update(render or {})
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def _vertrag(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def _grundlage_rechnen(tmp_path, protokoll, attrappen, *, skip=True):
    ordner = _ordner(tmp_path, "erster", skip=skip)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return _vertrag(ordner)


# ======================================================================================
# Nr. 83 — «nur Cycles» liefert das Cycles-Bild
# ======================================================================================

def test_nur_grundlage_rechnet_blender_und_kein_bildmodell(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    vertrag = _grundlage_rechnen(tmp_path, protokoll, _mit_schoenbild(attrappen))

    assert len(protokoll["multipass"]) == 3, "Blender rechnet je Kamera"
    assert protokoll["render"] == [], "kein Bildmodell"
    assert len(vertrag["images"]) == 3
    assert vertrag["lieferstatus"] == kosmo_szene.LIEFERSTATUS_GELIEFERT
    assert vertrag["engine_used"] == "cycles"
    assert "engine_license" not in vertrag
    assert vertrag["qa"]["verdict"]["reason"].startswith("NUR GRUNDLAGE")


def test_nur_grundlage_meldet_eine_neue_grundlage(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    vertrag = _grundlage_rechnen(tmp_path, protokoll, _mit_schoenbild(attrappen))

    grundlage = vertrag["grundlage"]
    assert kosmo_szene.GRUNDLAGE_KENNUNG.match(grundlage["id"])
    assert grundlage["wiederverwendet"] is False
    abgelegt = tmp_path / "aus" / abholer.GRUNDLAGEN_ORDNER / f"{grundlage['id']}.json"
    assert abgelegt.is_file()


def test_nur_grundlage_ohne_schoenbild_ist_laut(tmp_path):
    """Ohne Cycles-Bild gibt es nichts zu liefern — kein stilles leeres Ergebnis."""
    protokoll, attrappen = _kette(tmp_path)
    ordner = _ordner(tmp_path, "ohne", skip=True)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "beauty_png" in antwort["grund"]


def test_je_kamera_steht_die_gerechnete_pose_in_blenders_achse(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    vertrag = _grundlage_rechnen(tmp_path, protokoll, _mit_schoenbild(attrappen))

    pose = vertrag["qa_je_kamera"][0]["pose"]
    assert pose["position"] == [0.0, -30.0, 1.7]
    assert pose["target"] == [0.0, 0.0, 5.5]
    assert pose["up_axis"] == "z"
    # Die Pose kommt als feste Kamera unveraendert zurueck (Nr. 68).
    kamera = kosmo_szene.spec_zu_kamera(dict(pose, name="s"))
    assert list(kamera["auge"]) == pose["position"]


# ======================================================================================
# Nr. 85 — die Variante aus der Grundlage
# ======================================================================================

def test_eine_variante_aus_der_grundlage_rechnet_kein_blender(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_rechnen(tmp_path, protokoll, attrappen)["grundlage"]["id"]
    blender_vorher = len(protokoll["multipass"])

    ordner = _ordner(tmp_path, "abend", vis={"grundlage": kennung, "seed": 7})
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert len(protokoll["render"]) == 3, "je Kamera genau ein KI-Lauf"
    vertrag = _vertrag(ordner)
    assert vertrag["grundlage"] == {"id": kennung, "wiederverwendet": True}


def test_zwei_varianten_derselben_grundlage_haben_dieselbe_tiefe(tmp_path):
    """Deckungsgleich heisst: dieselbe Tiefenkarte fuehrt beide Bilder."""
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_rechnen(tmp_path, protokoll, attrappen)["grundlage"]["id"]

    for name in ("morgen", "abend"):
        ordner = _ordner(tmp_path, name, vis={"grundlage": kennung, "seed": 3})
        assert _lauf(tmp_path, ordner, attrappen)["tat"] == abholer.TAT_VERARBEITET

    tiefen = [a.depth_png for a in protokoll["render"]]
    assert tiefen[:3] == tiefen[3:]


def test_eine_unbekannte_grundlage_wird_laut_abgelehnt(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    ordner = _ordner(tmp_path, "fremd", vis={"grundlage": "gl-0123456789abcdef"})

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "nicht bekannt" in antwort["grund"]
    assert protokoll["multipass"] == [], "nicht still neu gerechnet"


@pytest.mark.parametrize("render", [{"samples": 64}, {"resolution": [800, 600]}])
def test_eine_grundlage_die_nicht_passt_wird_laut_abgelehnt(tmp_path, render):
    """Auflage 4 des Integrators: Wer ueber vis_render bestellt, sieht kein «veraltet»."""
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_rechnen(tmp_path, protokoll, attrappen)["grundlage"]["id"]
    blender_vorher = len(protokoll["multipass"])

    ordner = _ordner(tmp_path, "anders", vis={"grundlage": kennung}, render=render)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "passt nicht" in antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher


def test_eine_grundlage_mit_fehlender_datei_wird_laut_abgelehnt(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_rechnen(tmp_path, protokoll, attrappen)["grundlage"]["id"]
    for tiefe in (tmp_path / "aus").rglob("tiefe_norm.png"):
        tiefe.unlink()

    ordner = _ordner(tmp_path, "weg", vis={"grundlage": kennung})
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "fehlt auf der Platte" in antwort["grund"]


def test_ein_lauf_mit_ki_legt_ebenfalls_eine_grundlage_ab(tmp_path):
    """Auch ein gewoehnlicher Lauf ist eine Grundlage — der erste Klick muss nicht
    «Grundlage rendern» heissen, damit Varianten deckungsgleich werden."""
    protokoll, attrappen = _kette(tmp_path)
    vertrag = _grundlage_rechnen(tmp_path, protokoll, _mit_schoenbild(attrappen), skip=False)

    assert vertrag["grundlage"]["wiederverwendet"] is False
    assert len(protokoll["render"]) >= 3


# ======================================================================================
# Nr. 84 — ein fester Startwert
# ======================================================================================

def test_ein_fester_seed_rechnet_genau_diesen_einen(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    ordner = _ordner(tmp_path, "fest", vis={"seed": 42})

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert {a.seed for a in protokoll["render"]} == {42}
    assert len(protokoll["render"]) == 3
    assert {e["seed"] for e in _vertrag(ordner)["qa_je_kamera"]} == {42}


# ======================================================================================
# Die Lesung im Vertrag
# ======================================================================================

def _szene(**vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"samples": 8}, "style": {"prompt": "a house"}, "vis": vis}


def test_grundlage_und_seed_werden_gelesen():
    szene = kosmo_szene.lies_szene(_szene(grundlage="gl-0123456789abcdef", seed=0),
                                   streng=False)
    assert szene["grundlage"] == "gl-0123456789abcdef"
    assert szene["seed"] == 0
    assert not szene["maengel"]


@pytest.mark.parametrize("vis, wort", [
    ({"grundlage": "vis-1-abcdef"}, "vis.grundlage"),
    ({"seed": -1}, "vis.seed"),
    ({"seed": 2147483648}, "vis.seed"),
    ({"seed": True}, "vis.seed"),
    ({"seed": 1.0}, "vis.seed"),
    ({"grundlage": "gl-0123456789abcdef", "skip": True}, "zugleich"),
])
def test_was_nicht_stimmt_ist_ein_mangel(vis, wort):
    szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
    assert any(wort in m for m in szene["maengel"]), szene["maengel"]


def test_ohne_die_felder_bleibt_alles_wie_bisher():
    szene = kosmo_szene.lies_szene(_szene(), streng=False)
    assert szene["grundlage"] is None and szene["seed"] is None
