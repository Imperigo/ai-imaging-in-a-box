"""A0159: Morgen zeigt lange Schatten auch auf Augenhöhe, Winter hat kahle oder verschneite Bäume.

Reine Prüfung der Vorgaben und des Runners als Text (Blender läuft hier nicht). Die Bilder und die
Kennzahlen stehen in der Meldung zum Auftrag.
"""
from pathlib import Path

from aiimaging import stimmung

RUNNER = Path(stimmung.__file__).parent / "runners" / "blender_depth_stage.py"


def test_die_morgensonne_setzt_sich_gegen_den_himmel_durch():
    """Bei 12° trifft nur ein Fünftel der Sonne den Boden: sonst bleibt der Schatten unlesbar."""
    morgen = stimmung.licht_der_stimmung("morgen")
    assert morgen["sonne_hoehe_hoechstens_grad"] <= 12.0
    assert morgen["sonnen_staerke"] / morgen["fuell_staerke"] >= 25.0
    mittag = stimmung.licht_der_stimmung("mittag")
    assert morgen["sonnen_staerke"] / morgen["fuell_staerke"] \
        > mittag["sonnen_staerke"] / mittag["fuell_staerke"]


def test_die_morgensonne_steht_knapp_hinter_der_seite():
    """Bei 70° fielen die Schatten hinter das Haus, vor der Kamera steht bewusst nichts."""
    assert stimmung.licht_der_stimmung("morgen")["sonne_seitlich_grad"] > 90.0


def test_der_winterhimmel_ist_nicht_grau_neutral():
    rot, _gruen, blau = stimmung.WINTER_HIMMEL_TOENUNG
    assert blau > rot + 0.3
    text = RUNNER.read_text(encoding="utf-8")
    assert 'himmel_sichtbar and licht.get("schnee")' in text and "WINTER_HIMMEL_TOENUNG" in text
    assert "himmel_farbe=himmel_kamera if himmel_sichtbar" in text


def test_der_morgensatz_nennt_den_schatten_auf_dem_boden():
    assert "across the ground" in stimmung.STIMMUNGEN["morgen"]["prompt_en"]


def test_der_wintersatz_nennt_himmel_und_baeume():
    satz = stimmung.STIMMUNGEN["winter"]["prompt_en"]
    assert "blue winter sky" in satz
    assert "snow-covered trees" in satz


def test_die_anderen_stimmungen_bleiben():
    assert stimmung.licht_der_stimmung("mittag")["sonnen_staerke"] == 3.0
    assert stimmung.licht_der_stimmung("abend")["sonnen_staerke"] == 3.5
    assert "snow" not in stimmung.STIMMUNGEN["mittag"]["prompt_en"]


def test_der_runner_legt_schnee_auf_baeume_und_bueche_nicht_auf_die_wiese():
    text = RUNNER.read_text(encoding="utf-8")
    assert "def _schnee_auf_vegetation(" in text
    rumpf = text[text.index("def _schnee_auf_vegetation("):]
    rumpf = rumpf[:rumpf.index("\n\n\n")]
    assert "_Umfeld_baeume_" in rumpf and "_Umfeld_buesche_" in rumpf
    assert "_Umfeld_wiese_" not in rumpf
    assert "_schnee_auf_vegetation(" in text[text.index('umgebung_befund["schnee"]'):]
