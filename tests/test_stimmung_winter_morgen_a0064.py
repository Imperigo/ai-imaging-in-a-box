"""Auftrag A0064: «Winter» zeigt Winter, «Morgen» tiefes Morgenlicht mit langen Schatten.

**Anlass (Demolauf 31.10.2026, Variante A, Südost, Vollautomatik):** Beide Stimmungen waren
massstabtreu (Geometrie-Wert 0,972–0,974), aber nicht zu erkennen. (1) «Winter» ohne Schnee,
grüner Rasen, grauer Himmel. (2) «Morgen» dunkel und wolkig wie Abend, keine langen Schatten,
obwohl der Prompt «long shadows» sagte. Das KI-Bild startet vom Render (Owner 31.10. «Immer vom
Render») und hält mit bild_und_tiefe, was die Grundlage zeigt — eine grüne Wiese im Render bleibt
grün, eine hohe Sonne gibt kurze Schatten. Darum sitzt die Abhilfe in der **Grundlage**, nicht
im Prompt:

* **Morgen:** Die Sonne steht höchstens :data:`stimmung.STIMMUNGEN` ``sonne_hoehe_hoechstens_grad``
  hoch (Richtung aus dem Himmelsbild, nur tiefer), warm getönt, der sichtbare Himmel hell.
* **Winter:** Schnee — die Geländeplatte und die Wiese werden Schnee, waagrechte und flach
  geneigte Flächen des Hauses unter freiem Himmel (Dach, Vordach) bekommen eine Schneeschicht im
  Material, keine neue Geometrie. Die Sonne steht tief wie im Winter.

Reine Funktionen und der Runner mit Attrappen bzw. per Quelltext (Regel 2: kein ``bpy`` im
Produkt-venv). Testdaten synthetisch (Regel 3).
"""
from __future__ import annotations

import json
import math
from unittest import mock

from aiimaging import abholer, stimmung

from test_heimfehler_auf292 import RUNNER, _runner


def _hoch(grad):
    """Eine Sonnenscheibe in ``grad`` Höhe, Azimut 30°."""
    e, a = math.radians(grad), math.radians(30.0)
    return {"gefunden": True, "richtung_bild": [math.cos(e) * math.cos(a),
                                                math.cos(e) * math.sin(a), math.sin(e)],
            "farbe": [1.0, 1.0, 1.0], "e_himmel_h": 1.0}


# ====================================================================== Morgen

def _lampe(analyse, licht):
    """Wie der Runner: erst die Sonne der Stimmung, dann die Lampe."""
    return stimmung.lampe_aus_himmel(stimmung.sonne_der_stimmung(analyse, licht), licht)


def test_die_morgensonne_steht_tief_und_wirft_lange_schatten():
    licht = stimmung.licht_der_stimmung("morgen")
    grenze = licht["sonne_hoehe_hoechstens_grad"]
    assert grenze <= 15.0
    # Schattenlänge = Höhe / tan(Sonnenhöhe): mindestens das Dreieinhalbfache der Höhe.
    assert 1.0 / math.tan(math.radians(grenze)) >= 3.5
    sonne = stimmung.sonne_der_stimmung(_hoch(45.0), licht)
    assert sonne["hoehe_weg"] == "begrenzt" and sonne["hoehe_himmelsbild_grad"] == 45.0
    lampe = _lampe(_hoch(45.0), licht)
    assert lampe["art"] == "sonne"
    assert lampe["hoehe_grad"] == grenze
    assert lampe["azimut_welt_grad"] == 30.0, "die Richtung bleibt die des Himmelsbilds"
    # Eine Sonne, die schon tief steht, bleibt, wo sie ist.
    assert _lampe(_hoch(6.0), licht)["hoehe_grad"] == 6.0
    assert stimmung.sonne_der_stimmung(_hoch(6.0), licht)["hoehe_weg"] == "himmelsbild"


def test_ohne_sonnenscheibe_wird_die_morgensonne_trotzdem_hart():
    """Demolauf 31.10.: Das Morgen-Himmelsbild hat keine Scheibe — weiche Lampe, 25°, 23° hoch."""
    licht = stimmung.licht_der_stimmung("morgen")
    ohne = dict(_hoch(23.184), gefunden=False, weg="hellster_bereich",
                farbe=[1.07, 0.99, 0.86])
    # Die Lampe allein bleibt, wie sie war (Probe 294): weich.
    assert stimmung.lampe_aus_himmel(ohne, licht)["art"] == "weich"
    # Mit der Sonne der Stimmung: hart, tief, warm (Farbe des hellsten Bereichs).
    lampe = _lampe(ohne, licht)
    assert lampe["art"] == "sonne" and lampe["winkel_grad"] <= 2.0
    assert lampe["hoehe_grad"] == licht["sonne_hoehe_hoechstens_grad"]
    assert lampe["weg"] == "hellster_bereich_als_sonne"
    assert lampe["farbe"][0] > lampe["farbe"][2], "warmes Morgenlicht"


def test_der_morgenhimmel_wird_nicht_mehr_abgedunkelt():
    assert stimmung.STIMMUNGEN["morgen"]["hintergrund_richtung"] == "heller"


def test_der_morgensatz_nennt_tiefe_sonne_und_hellen_himmel():
    satz = stimmung.STIMMUNGEN["morgen"]["prompt_en"]
    assert "low" in satz and "long shadows" in satz and "bright" in satz
    assert "morning" in satz


def test_mittag_und_abend_behalten_die_sonne_des_himmelsbilds():
    for preset in ("mittag", "abend", "blaue-stunde", "bedeckt", "nebel", "weiss"):
        licht = stimmung.licht_der_stimmung(preset)
        assert "sonne_hoehe_hoechstens_grad" not in licht, preset
        assert "schnee" not in licht, preset
        lampe = stimmung.lampe_aus_himmel(_hoch(45.0), licht)
        assert lampe["hoehe_grad"] >= 15.0, preset


# ====================================================================== Winter

def test_winter_bestellt_schnee_und_eine_tiefe_wintersonne():
    licht = stimmung.licht_der_stimmung("winter")
    assert licht["schnee"] is True
    assert licht["gelaende_grau"] == list(stimmung.SCHNEE_FARBE)
    assert stimmung.leuchtdichte(stimmung.SCHNEE_FARBE) >= 0.7, "Schnee ist hell"
    assert stimmung.SCHNEE_FARBE[2] >= stimmung.SCHNEE_FARBE[0], "kühl, nicht gelblich"
    assert licht["sonne_hoehe_hoechstens_grad"] <= 20.0
    assert licht["kelvin"] > stimmung.NEUTRAL_KELVIN, "kaltes Licht"
    lampe = _lampe(dict(_hoch(34.677), gefunden=False), licht)
    assert lampe["art"] == "sonne", "Demolauf 31.10.: auch hier keine Scheibe im Himmelsbild"
    assert lampe["hoehe_grad"] == licht["sonne_hoehe_hoechstens_grad"]


def test_die_dachgrenze_ist_eine_neigung():
    unten, oben = stimmung.SCHNEE_NEIGUNG_GRAD
    assert 0.0 < unten < oben < 90.0
    # Ein steiles Satteldach (45°) trägt Schnee voll, eine Wand (90°) nie.
    assert 45.0 <= unten


def test_schnee_und_sonnenhoehe_reisen_als_lichtdaten(tmp_path):
    def szene(preset):
        return {"umgebung": {"preset": preset, "intensitaet": 1.0, "rotationGrad": 0.0},
                "umgebung_datei": {"pfad": tmp_path / f"{preset}.hdr"}}
    winter = json.loads(abholer.umgebung_einstellungen(szene("winter"))["umgebung_licht"])
    assert winter["schnee"] is True
    assert winter["gelaende_grau"] == list(stimmung.SCHNEE_FARBE)
    assert winter["sonne_hoehe_hoechstens_grad"] == \
        stimmung.STIMMUNGEN["winter"]["sonne_hoehe_hoechstens_grad"]
    morgen = json.loads(abholer.umgebung_einstellungen(szene("morgen"))["umgebung_licht"])
    assert "schnee" not in morgen and morgen["sonne_hoehe_hoechstens_grad"] <= 15.0
    # Abend Wort für Wort wie vorher: keine neuen Schlüssel.
    abend = json.loads(abholer.umgebung_einstellungen(szene("abend"))["umgebung_licht"])
    assert set(abend) == set(abholer.LICHT_AN_BLENDER)


def test_die_platte_wird_schnee_mit_marke(monkeypatch):
    modul, bpy = _runner(monkeypatch)

    def objekt(name):
        o = mock.MagicMock()
        o.name, o.type, o.parent = name, "MESH", None
        o.material_slots = []
        o.get.return_value = None
        return o

    platte, wand = objekt("IfcSlab_Gelaende_a64p"), objekt("IfcWall_Hauptbau_a64w")
    bpy.data.objects = [platte, wand]
    befund = modul._gelaende_grau(stimmung.SCHNEE_FARBE, schnee=True)
    assert befund["objekte"] == 1 and befund["schnee"] is True
    assert platte.data.materials.append.called and not wand.data.materials.append.called


def test_der_runner_legt_schnee_aufs_dach_und_laesst_die_wiese_weg():
    quelle = RUNNER.read_text(encoding="utf-8")
    haupt = quelle[quelle.index("def main() -> int:"):]
    # Schnee nach Materialwahl und Glas, vor der Vorprobe (die misst das Haus mit Schnee).
    assert haupt.index("_materialien_setzen(a,") < haupt.index("_schnee_aufs_haus(")
    assert haupt.index("_schnee_aufs_haus(") < haupt.index("_hintergrund_abstimmen(")
    assert "schnee=" in haupt[haupt.index("_umfeld_laden(a,"):][:300]
    laden = quelle[quelle.index("def _umfeld_laden("):quelle.index("def _kontext_laden(")]
    assert "Schnee statt Wiese" in laden
    dach = quelle[quelle.index("def _schnee_aufs_haus("):]
    dach = dach[:dach.index("\ndef ")]
    # Nur unter freiem Himmel (AO), nur flach genug (Normale), nie Glas, Gelände oder Umfeld.
    assert "ShaderNodeAmbientOcclusion" in dach and "ShaderNodeNewGeometry" in dach
    assert "_ist_glas(" in dach and "_ist_umfeld_objekt(" in dach
    assert "_ist_gelaende_objekt(" in dach and "_ist_kontext(" in dach
    assert "URSPRUNG_MARKE" in dach, "der ID-Pass sieht den alten Namen"
