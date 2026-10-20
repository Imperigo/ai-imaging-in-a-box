"""Die Befunde aus ``auf-20261020-293`` (HomeStation, 20.10.2026): Stimmungen milchig und flach.

Der Owner hat die Bilder angesehen: Alle Stimmungen wirken milchig, das Haus hebt sich kaum vom
Hintergrund ab (Winter: praktisch unsichtbar), es gibt keine Schatten, Abend ohne Streiflicht,
Blaue Stunde pastell. Dazu drei Fehler am Heim-PC (Messung bei «nur Grundlage», Vorschau auf
kleiner Grundlage ohne Haus, ``geom_iou`` der Vorschau leer). Je Punkt eine Probe — reine
Funktionen mit echten kleinen Bildern, der Runner mit Attrappen und per Quelltext (Regel 2:
kein ``bpy`` im Produkt-venv). Testdaten synthetisch (Regel 3).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import (abholer, backbone, belichtung, bildschreiben, kosmo_szene, seams,
                       stimmung)
from aiimaging import tiefenschaetzer as ts

from test_heimfehler_auf292 import RUNNER, _runner

MIT_SONNE = ("morgen", "mittag", "abend", "winter")
OHNE_SONNE = ("bedeckt", "nebel", "weiss", "blaue-stunde")


def _himmel_mit_scheibe(b, h, *, hoehe_grad, azimut_grad, himmel=0.5, scheibe=2000.0,
                        radius_grad=3.0):
    """Ein equirektangulärer Himmel in Blenders Reihenfolge (Zeile 0 unten) mit heller Scheibe."""
    e, a = math.radians(hoehe_grad), math.radians(azimut_grad)
    ziel = (math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))
    grenze = math.cos(math.radians(radius_grad))
    px = []
    for z in range(h):
        for x in range(b):
            d = stimmung.richtung_im_bild(x, z, b, h)
            if scheibe and sum(p * q for p, q in zip(d, ziel)) > grenze:
                px += [scheibe, scheibe * 0.9, scheibe * 0.75, 1.0]
            else:
                v = himmel if d[2] > 0 else 0.1
                px += [v * 0.8, v, v * 1.2, 1.0]
    return px


# ====================================================================== 1 · Kontrast

def test_der_hintergrund_wird_dunkler_mit_festem_abstand_und_behaelt_den_farbton():
    """Winter aus 293: Verlauf so hell wie das Haus. «dunkler»: das hellste Ende höchstens
    eine Blendenstufe unter dem Haus — der Farbton (Verhältnis der Kanäle) bleibt."""
    horizont, zenit = [0.40, 0.45, 0.55], [0.30, 0.38, 0.60]
    haus = stimmung.leuchtdichte([0.44, 0.44, 0.44])
    aus = stimmung.hintergrund_mit_abstand(horizont, zenit, haus, richtung="dunkler")
    assert aus["richtung"] == "dunkler" and aus["faktor"] < 1.0
    hellstes = max(stimmung.leuchtdichte(aus["horizont"]), stimmung.leuchtdichte(aus["zenit"]))
    assert hellstes <= haus / 2.0 + 1e-6
    for neu, alt in ((aus["horizont"], horizont), (aus["zenit"], zenit)):
        assert [n / neu[0] for n in neu] == pytest.approx([a / alt[0] for a in alt], rel=1e-4)
    assert aus["abstand_ev_nachher"] < aus["abstand_ev_vorher"] < 0.5


def test_heller_und_auto_und_mindestens_nicht_genau():
    haus = 0.5
    heller = stimmung.hintergrund_mit_abstand([0.6] * 3, [1.2] * 3, haus, richtung="heller")
    assert min(stimmung.leuchtdichte(heller["horizont"]),
               stimmung.leuchtdichte(heller["zenit"])) >= 2 * haus - 1e-6
    # auto: die Seite, auf der der Verlauf schon liegt.
    assert stimmung.hintergrund_mit_abstand([0.6] * 3, [0.8] * 3, haus)["richtung"] == "heller"
    assert stimmung.hintergrund_mit_abstand([0.3] * 3, [0.4] * 3, haus)["richtung"] == "dunkler"
    # Schon weit genug weg: bleibt (sonst naehme die Regel Kontrast weg).
    weit = stimmung.hintergrund_mit_abstand([0.05] * 3, [0.08] * 3, haus, richtung="dunkler")
    assert weit["faktor"] == 1.0
    with pytest.raises(ValueError):
        stimmung.hintergrund_mit_abstand([0.5] * 3, [0.5] * 3, haus, richtung="seitwaerts")
    leer = stimmung.hintergrund_mit_abstand([0.5] * 3, [0.5] * 3, 0.0)
    assert leer["faktor"] == 1.0 and leer["grund"]


def test_die_staerke_verschiebt_den_abstand_in_stufen_nicht():
    """Der Kern des Befunds: Stärke 0,5 / 1 / 2 skaliert Haus und Grund gleich (293). In
    Blendenstufen bleibt der Abstand stehen — darum rechnet die Regel in Stufen."""
    werte = [stimmung.hintergrund_mit_abstand([0.4 * k] * 3, [0.5 * k] * 3, 0.45 * k,
                                              richtung="dunkler")["abstand_ev_nachher"]
             for k in (0.5, 1.0, 2.0)]
    assert werte == pytest.approx([werte[0]] * 3)


def test_die_hausfarbe_der_vorprobe_zaehlt_nur_deckende_punkte():
    px = [0.5, 0.5, 0.5, 1.0] * 3 + [9.0, 9.0, 9.0, 0.0] * 5 + [0.2, 0.2, 0.2, 0.5]
    aus = stimmung.haus_leuchtdichte(px)
    assert aus["n"] == 3 and aus["leuchtdichte"] == pytest.approx(0.5)
    assert stimmung.haus_leuchtdichte([0.1, 0.1, 0.1, 0.0])["leuchtdichte"] is None


def _bilder(tmp_path, *, haus=150, himmel=145, ecke=0):
    """20 x 20: Haus (Zeilen 8–15, Spalten 8–11), Platte (16–17), Himmel; eine ferne Ecke anders."""
    b = h = 20
    schoen, kennung, maske = [], [], []
    for y in range(h):
        for x in range(b):
            ist_haus = 8 <= y <= 15 and 8 <= x <= 11
            platte = y in (16, 17)
            if ist_haus:
                schoen.append((haus, haus, haus))
                kennung.append((200, 10, 10))
            elif platte:
                schoen.append((90, 90, 90))
                kennung.append((10, 200, 10))
            else:
                wert = ecke if (x < 2 and y < 2) else himmel
                schoen.append((wert, wert, wert))
                kennung.append((0, 0, 0))
            maske.append(ist_haus)
    bildschreiben.schreibe_farb_png(tmp_path / "beauty_.png", schoen, b, h)
    bildschreiben.schreibe_farb_png(tmp_path / "material_id.png", kennung, b, h)
    return tmp_path / "beauty_.png", tmp_path / "material_id.png", maske


def test_der_kontrast_misst_haus_gegen_den_himmel_daneben(tmp_path):
    schoen, kennung, maske = _bilder(tmp_path, haus=150, himmel=145, ecke=0)
    aus = belichtung.kontrast_aus_pngs(schoen, kennung, maske=maske)
    # Die schwarze Ecke liegt nicht «daneben» und zaehlt nicht; die Platte ist kein Himmel.
    assert aus["kontrast"] == pytest.approx(5.0, abs=0.2)
    assert aus["kaum_sichtbar"] is True and aus["schwelle"] == belichtung.KONTRAST_SCHWELLE
    gut = belichtung.kontrast_aus_pngs(*_bilder(tmp_path, haus=150, himmel=100)[:2],
                                       maske=maske)
    assert gut["kontrast"] == pytest.approx(50.0, abs=0.2) and gut["kaum_sichtbar"] is False
    # Nie eine Ausnahme.
    assert belichtung.kontrast_aus_pngs(None, kennung, maske=maske)["kontrast"] is None
    assert belichtung.kontrast_aus_pngs(schoen, None, maske=maske)["grund"]
    assert belichtung.kontrast_aus_pngs(schoen, kennung, maske=[True])["kontrast"] is None
    assert belichtung.kontrast_haus_hintergrund(
        [(1, 1, 1)] * 4, 2, 2, haus=[False] * 4, hintergrund=[True] * 4)["grund"]


def test_die_schwelle_steht_an_zwei_stellen_gleich():
    assert belichtung.KONTRAST_SCHWELLE == stimmung.KONTRAST_SCHWELLE == 20.0


def test_der_kontrast_steht_im_ergebnis_mit_satz():
    je = [{"kamera": "s", "geometrie_urteil": {"kamera": "s", "score": None, "bestanden": None,
                                              "kontrast": {"kontrast": 42.0}}},
          {"kamera": "sSE", "geometrie_urteil": {"kamera": "sSE", "score": None,
                                                "bestanden": None,
                                                "kontrast": {"kontrast": -3.5}}}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)
    assert e["qa"]["kontrast_haus_hintergrund"] == -3.5, "der kleinste Betrag"
    assert [k.get("kontrast_haus_hintergrund") for k in e["qa_je_kamera"]] == [42.0, -3.5]
    assert any(h.startswith("HAUS KAUM SICHTBAR") and "'sSE'" in h for h in e["hinweise"])
    ohne = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                    geometrie_urteil={"score": 0.8, "bestanden": True})
    assert "kontrast_haus_hintergrund" not in ohne["qa"], "kein null (ihr .optional())"


class _Knoten:
    def __init__(self, staerke):
        self.inputs = {"Strength": SimpleNamespace(default_value=staerke)}


def test_die_vorprobe_stellt_nur_den_hintergrund_nach(monkeypatch, tmp_path):
    """Die Vorprobe misst das Haus (deckende Punkte) und stellt NUR die Stärke des ruhigen
    Grunds nach; danach stehen Film, Grösse, Samples und Sichtbarkeit wie vorher."""
    modul, bpy = _runner(monkeypatch)
    platte = mock.MagicMock()
    platte.name, platte.type, platte.parent = "IfcSlab_Gelaende_293p", "MESH", None
    platte.material_slots, platte.visible_camera = [], True
    platte.get.return_value = None
    bpy.data.objects = [platte]
    grund = _Knoten(0.5)
    bpy.context.scene.world.node_tree.nodes.get = lambda name: (
        grund if name == modul.RUHIGER_GRUND else None)
    szene = SimpleNamespace(
        render=SimpleNamespace(resolution_percentage=100, film_transparent=False,
                               filepath="/x/beauty_",
                               image_settings=SimpleNamespace(file_format="PNG",
                                                              color_depth="8",
                                                              color_mode="RGBA")),
        cycles=SimpleNamespace(samples=64, use_denoising=True))
    waehrend = {}

    def rendern(write_still=True):
        waehrend.update(film=szene.render.film_transparent, sichtbar=platte.visible_camera,
                        prozent=szene.render.resolution_percentage)
        Path(szene.render.filepath + ".exr").write_bytes(b"exr")

    bpy.ops.render.render = rendern
    bpy.data.images.load = lambda pfad: SimpleNamespace(
        pixels=[0.5, 0.5, 0.5, 1.0] * 4 + [0.0, 0.0, 0.0, 0.0] * 4, channels=4)
    umgebung = {"toenung": None, "hintergrund": {"horizont": [0.6] * 3, "zenit": [0.6] * 3}}
    licht = stimmung.licht_der_stimmung("winter") | {"hintergrund_richtung": "dunkler"}

    befund = modul._hintergrund_abstimmen(szene, tmp_path, licht, umgebung)

    assert waehrend == {"film": True, "sichtbar": False, "prozent": modul.VORPROBE_PROZENT}
    # Haus 0,5, Grund 0,6 x 0,5 = 0,3: dunkler um mindestens eine Stufe -> hoechstens 0,25.
    assert befund["weg"] == "vorprobe" and befund["richtung"] == "dunkler"
    assert 0.6 * grund.inputs["Strength"].default_value == pytest.approx(0.25)
    assert szene.render.film_transparent is False and platte.visible_camera is True
    assert (szene.render.resolution_percentage, szene.cycles.samples,
            szene.cycles.use_denoising) == (100, 64, True)
    assert szene.render.image_settings.file_format == "PNG"
    assert szene.render.filepath == "/x/beauty_"
    assert not (tmp_path / modul.VORPROBE_ORDNER).exists(), "die Vorprobe raeumt auf"


def test_misslingt_die_vorprobe_bleibt_der_verlauf_und_der_grund_steht_da(monkeypatch,
                                                                          tmp_path):
    modul, bpy = _runner(monkeypatch)
    bpy.data.objects = []
    grund = _Knoten(0.5)
    bpy.context.scene.world.node_tree.nodes.get = lambda name: grund
    szene = mock.MagicMock()
    szene.render.film_transparent = False
    bpy.ops.render.render = lambda **k: None               # schreibt nichts
    befund = modul._hintergrund_abstimmen(szene, tmp_path, stimmung.licht_der_stimmung("nebel"),
                                          {"hintergrund": {"horizont": [1] * 3, "zenit": [1] * 3}})
    assert befund["weg"] == "ohne" and "Vorprobe" in befund["grund"]
    assert grund.inputs["Strength"].default_value == 0.5
    assert szene.render.film_transparent is False


def test_die_vorprobe_laeuft_vor_dem_schoenbild():
    quelle = RUNNER.read_text(encoding="utf-8")
    haupt = quelle[quelle.index("def main()"):]
    assert haupt.index("_hintergrund_abstimmen(") < haupt.index("_compositor_auf_tiefe(out_dir)")
    assert haupt.index("_gelaende_grau(") < haupt.index("_hintergrund_abstimmen(")


# ====================================================================== 2 · Licht mit Schatten

def test_die_sonne_wird_im_himmelsbild_gefunden():
    b, h = 128, 64
    px = _himmel_mit_scheibe(b, h, hoehe_grad=12.0, azimut_grad=-70.0)
    aus = stimmung.sonne_aus_himmel(px, b, h)
    assert aus["gefunden"] is True and aus["weg"] == "sonnenscheibe"
    assert aus["hoehe_grad"] == pytest.approx(12.0, abs=2.0)
    assert aus["azimut_bild_grad"] == pytest.approx(-70.0, abs=2.0)
    assert aus["farbe"][0] > aus["farbe"][2], "die Farbe der Scheibe (warm)"
    assert stimmung.leuchtdichte(aus["farbe"]) == pytest.approx(1.0, abs=1e-4)
    assert aus["relativ"] > 1.0 and aus["e_himmel_h"] > 0


def test_ohne_scheibe_der_hellste_bereich():
    b, h = 64, 32
    px = _himmel_mit_scheibe(b, h, hoehe_grad=40.0, azimut_grad=20.0, scheibe=0.0)
    # Ein heller, breiter Fleck (bedeckter Himmel): 3x, nicht 20x der Median.
    for z in range(h):
        for x in range(b):
            d = stimmung.richtung_im_bild(x, z, b, h)
            if d[2] > 0.6:
                i = (z * b + x) * 4
                px[i:i + 3] = [1.5, 1.5, 1.5]
    aus = stimmung.sonne_aus_himmel(px, b, h)
    assert aus["gefunden"] is False and aus["weg"] == "hellster_bereich"
    assert aus["hoehe_grad"] > 40.0


def test_die_lampe_kommt_aus_der_richtung_der_sonne_gedreht_wie_das_bild():
    analyse = {"gefunden": True, "richtung_bild": list(stimmung.richtung_im_bild(10, 40, 128,
                                                                                    64)),
               "farbe": [1.1, 1.0, 0.8], "e_himmel_h": 1.5, "weg": "sonnenscheibe"}
    hoch_bild = math.degrees(math.asin(analyse["richtung_bild"][2]))
    azimut_bild = math.degrees(math.atan2(analyse["richtung_bild"][1],
                                          analyse["richtung_bild"][0]))
    licht = stimmung.licht_der_stimmung("abend")
    lampe = stimmung.lampe_aus_himmel(analyse, licht, drehung_grad=30.0, staerke=2.0)
    assert lampe["art"] == "sonne" and lampe["winkel_grad"] <= 2.0
    assert lampe["hoehe_grad"] == pytest.approx(hoch_bild, abs=1e-3)
    assert ((lampe["azimut_welt_grad"] - (azimut_bild - 30.0) + 180) % 360 - 180) == \
        pytest.approx(0.0, abs=1e-3)
    assert lampe["energie"] == pytest.approx(licht["sonnen_staerke"] * 1.5 * 2.0)
    assert "gesetzt, nicht gemessen" in lampe["herkunft"]


def test_tiefe_sonne_gibt_streiflicht_und_ohne_sonne_eine_weiche_lampe():
    tief = {"gefunden": True, "richtung_bild": [1.0, 0.0, -0.05], "e_himmel_h": 1.0}
    lampe = stimmung.lampe_aus_himmel(tief, stimmung.licht_der_stimmung("morgen"))
    assert lampe["art"] == "sonne" and lampe["hoehe_grad"] == stimmung.SONNE_MIN_HOEHE_GRAD
    weich = stimmung.lampe_aus_himmel({"gefunden": False, "richtung_bild": [1, 0, 0.1],
                                       "e_himmel_h": 1.0},
                                      stimmung.licht_der_stimmung("bedeckt"))
    assert weich["art"] == "weich" and weich["winkel_grad"] >= 20.0
    assert weich["hoehe_grad"] >= stimmung.WEICH_MIN_HOEHE_GRAD
    # Sonne bestellt, aber keine Scheibe im Bild: weich, und der Satz sagt es.
    ohne = stimmung.lampe_aus_himmel({"gefunden": False, "richtung_bild": [0, 1, 0.5]},
                                     stimmung.licht_der_stimmung("winter"))
    assert ohne["art"] == "weich" and "Keine Sonnenscheibe" in ohne["grund"]


def test_die_drehung_der_lampe_zeigt_zur_sonne():
    for richtung in ([0.8, 0.45, 0.34], [-0.2, -0.9, 0.38], [0.0, 0.0, 1.0]):
        ax, ay, az = stimmung.euler_fuer_richtung(richtung)
        x, y, z = 0.0, 0.0, 1.0
        y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
        x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
        x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
        n = math.sqrt(sum(c * c for c in richtung))
        assert (x, y, z) == pytest.approx([c / n for c in richtung], abs=1e-9)


def test_das_licht_steht_als_daten_je_stimmung_mit_herkunft():
    for preset in stimmung.PRESETS:
        licht = stimmung.licht_der_stimmung(preset)
        assert licht["sonne"] is (preset in MIT_SONNE), preset
        assert licht["fuell_staerke"] < 1.0, "das Himmelsbild ist nur noch Fuelllicht"
        if licht["sonne"]:
            assert licht["winkel_grad"] <= 2.0, "harte Schattenkante"
        else:
            assert licht["winkel_grad"] >= 20.0, "weiche Schatten"
        assert licht["herkunft_licht"] == stimmung.LICHT_HERKUNFT
        assert licht["hintergrund_richtung"] in stimmung.HINTERGRUND_RICHTUNGEN
    assert "gesetzt, nicht gemessen" in stimmung.LICHT_HERKUNFT
    # Unbekannte Stimmung: das Licht von vor 293 (keine Lampe, kein Grau).
    assert "sonne" not in stimmung.licht_der_stimmung("gibt-es-nicht")


def test_der_runner_stellt_die_lampe_aus_dem_himmelsbild(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    licht = stimmung.licht_der_stimmung("abend")
    a = SimpleNamespace(umgebung_hdr="h.hdr", sonne_hoehe=None, sonne_azimut=None,
                        sonne_staerke=None, sonne_kelvin=None, sonne_winkel=None,
                        umgebung_licht=json.dumps(licht))
    analyse = {"gefunden": True, "richtung_bild": [0.9, 0.3, 0.3], "farbe": [1.1, 1.0, 0.8],
               "e_himmel_h": 2.0, "weg": "sonnenscheibe"}
    umgebung = {"himmel_sonne": analyse, "staerke": 1.0, "drehung_grad": 0.0,
                "toenung": None}
    objekt, befund = modul._sonne_setzen([0, 0, 0], 10.0, a, umgebung=umgebung)
    daten = bpy.data.lights.new.return_value
    assert bpy.data.lights.new.call_args.kwargs.get("type") == "SUN"
    assert befund["weg"] == "himmelsbild_sonne"
    assert daten.energy == pytest.approx(licht["sonnen_staerke"] * 2.0)
    assert daten.angle == pytest.approx(math.radians(licht["winkel_grad"]))
    assert tuple(objekt.rotation_euler) == pytest.approx(
        stimmung.euler_fuer_richtung(befund["lampe"]["richtung_welt"]))
    # Ohne Lichtdaten: wie vor 293 keine Lampe (Entscheid 110).
    bpy.data.lights.new.reset_mock()
    a.umgebung_licht = None
    objekt, befund = modul._sonne_setzen([0, 0, 0], 10.0, a)
    assert objekt is None and befund["weg"] == "himmelsbild"
    assert not bpy.data.lights.new.called


def test_die_welt_kappt_die_sonnenscheibe_und_wird_fuelllicht(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    monkeypatch.setattr(modul, "_himmelsfarben", lambda bild: {
        "horizont": [0.6] * 3, "zenit": [0.4] * 3, "weg": "himmelsbild", "grund": "",
        "sonne": {"gefunden": True, "kappung": 9.5, "richtung_bild": [1, 0, 0.3]}})
    licht = stimmung.licht_der_stimmung("mittag")
    befund = modul._welt_setzen((0.5, 0.5, 0.5), 2.0, hdr="/x/mittag__y_4k.hdr", licht=licht)
    baum = bpy.data.worlds.new.return_value.node_tree
    assert baum.nodes.new.return_value.operation == "MINIMUM"
    assert befund["licht"]["sonnenscheibe_gekappt"] is True
    assert befund["licht"]["staerke_fuelllicht"] == pytest.approx(2.0 * licht["fuell_staerke"])
    assert befund["himmel_sonne"]["gefunden"] is True
    # Ohne Sonne (bedeckt): nicht gekappt.
    befund = modul._welt_setzen((0.5, 0.5, 0.5), 1.0, hdr="/x/bedeckt__y_4k.hdr",
                                licht=stimmung.licht_der_stimmung("bedeckt"))
    assert befund["licht"]["sonnenscheibe_gekappt"] is False


def test_die_lichtdaten_gehen_bis_blender(tmp_path):
    szene = {"umgebung": {"preset": "abend", "intensitaet": 1.0, "rotationGrad": 0.0},
             "umgebung_datei": {"pfad": tmp_path / "abend.hdr"}}
    aus = abholer.umgebung_einstellungen(szene)
    licht = json.loads(aus["umgebung_licht"])
    assert licht["sonne"] is True and licht["look"] == "Medium High Contrast"
    assert set(licht) == set(abholer.LICHT_AN_BLENDER)
    cmd = seams._multipass_argumente("a.glb", tmp_path, drehen=False, aufloesung=64,
                                     samples=4, beauty=True, material_id=True,
                                     umgebung_hdr=tmp_path / "abend.hdr",
                                     umgebung_licht=aus["umgebung_licht"])
    arg = next(c for c in cmd if c.startswith("--umgebung-licht="))
    assert json.loads(arg.split("=", 1)[1]) == licht
    # Ohne Himmelsbild geht nichts davon mit.
    assert not any(c.startswith("--umgebung-licht") for c in seams._multipass_argumente(
        "a.glb", tmp_path, drehen=False, aufloesung=64, samples=4, beauty=True,
        material_id=True, umgebung_licht=aus["umgebung_licht"]))


def test_der_runner_kennt_den_schalter(monkeypatch):
    import sys
    modul, _ = _runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["blender", "--", "--glb", "a.glb", "--out", "aus",
                                      "--umgebung-hdr", "h.hdr",
                                      '--umgebung-licht={"sonne": true}'])
    a = modul._argumente()
    assert modul._licht_der_stimmung(a) == {"sonne": True}
    a.umgebung_licht = "kein json"
    with pytest.raises(RuntimeError):
        modul._licht_der_stimmung(a)


# ====================================================================== 3 · Platte

def test_die_platte_wird_grau_und_nur_die_platte(monkeypatch):
    modul, bpy = _runner(monkeypatch)

    def objekt(name):
        o = mock.MagicMock()
        o.name, o.type, o.parent = name, "MESH", None
        o.material_slots = []
        o.get.return_value = None
        return o

    platte, wand = objekt("IfcSlab_Gelaende_293p"), objekt("IfcWall_Hauptbau_293a")
    bpy.data.objects = [platte, wand]
    befund = modul._gelaende_grau(stimmung.GELAENDE_GRAU)
    assert befund == {"objekte": 1, "farbe_linear": list(stimmung.GELAENDE_GRAU)}
    assert platte.data.materials.append.called and not wand.data.materials.append.called


def test_das_grau_ist_dunkler_und_bei_weiss_heller():
    assert stimmung.licht_der_stimmung("mittag")["gelaende_grau"] == list(stimmung.GELAENDE_GRAU)
    assert stimmung.licht_der_stimmung("weiss")["gelaende_grau"] == \
        list(stimmung.GELAENDE_GRAU_WEISS)
    gips = 0.79                                       # GIPS_FARBE des Runners (Rotkanal 0,80)
    assert stimmung.GELAENDE_GRAU[0] < stimmung.GELAENDE_GRAU_WEISS[0] < gips
    assert "GIPS_FARBE = (0.80, 0.79, 0.77)" in RUNNER.read_text(encoding="utf-8")


# ====================================================================== 4 · Tonwerte

def test_der_look_wird_je_fassung_gesucht_mit_rueckfall(monkeypatch):
    modul, _bpy = _runner(monkeypatch)

    class Ansicht:
        def __init__(self, kennt):
            self._kennt, self._look = kennt, "None"
            self.view_transform, self.exposure = "Standard", 0.0

        @property
        def look(self):
            return self._look

        @look.setter
        def look(self, wert):
            if wert != "None" and wert not in self._kennt:
                raise TypeError(f"enum {wert!r} not found")
            self._look = wert

    neu = SimpleNamespace(view_settings=Ansicht({"Medium High Contrast"}))
    befund = modul._tonwerte_setzen(neu, -0.5, look="Medium High Contrast")
    assert (befund["tonwerte"], befund["look"]) == ("AgX", "Medium High Contrast")
    alt = SimpleNamespace(view_settings=Ansicht({"AgX - Medium High Contrast"}))
    assert modul._tonwerte_setzen(alt, 0.0, look="Medium High Contrast")["look"] == \
        "AgX - Medium High Contrast"
    keiner = SimpleNamespace(view_settings=Ansicht(set()))
    befund = modul._tonwerte_setzen(keiner, 0.0, look="Medium High Contrast")
    assert befund["look"] == "None" and "nicht vorhanden" in befund["look_grund"]
    # Ohne Look bleibt der Bericht der von 292.
    assert set(modul._tonwerte_setzen(neu, 0.0)) == {"tonwerte", "belichtung_ev", "grund"}


# ====================================================================== 5 · Blaue Stunde

def test_die_blaue_stunde_ist_tiefer_und_kuehler():
    eintrag = stimmung.STIMMUNGEN["blaue-stunde"]
    assert eintrag["belichtung_ev"] < 0.0 and eintrag["kelvin"] == 9000.0
    toenung = stimmung.toenung_fuer(eintrag["kelvin"])
    assert toenung[2] > toenung[0]
    assert eintrag["hintergrund_richtung"] == "dunkler", "tiefblau, nicht pastell"


# ====================================================================== 6 · Messung bei «nur Grundlage»

def test_nur_grundlage_misst_ueberstrahlung_und_kontrast(tmp_path, monkeypatch):
    from test_grundlage_varianten import _mit_schoenbild, _ordner, _vertrag
    from test_kettenlauf_26august import _kette, _lauf
    from test_knoten_stimmung import _alle_himmel, _mit_stimmung
    _alle_himmel(tmp_path, monkeypatch)
    ordner = _ordner(tmp_path, "grundlage", skip=True)
    _mit_stimmung(ordner, {"preset": "winter"})
    monkeypatch.setattr(abholer._belichtung_modul, "kontrast_aus_pngs",
                        lambda *a, **k: {"kontrast": -0.5, "grund": ""})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["render"] == [], "kein Bildmodell"
    vertrag = _vertrag(ordner)
    assert "ueberstrahlt_anteil" in vertrag["qa"]
    assert vertrag["qa"]["kontrast_haus_hintergrund"] == -0.5
    assert all("kontrast_haus_hintergrund" in k for k in vertrag["qa_je_kamera"])
    assert any(h.startswith("HAUS KAUM SICHTBAR")
               for h in vertrag["qa"]["verdict"].get("hinweise") or ())


def test_eine_stelle_fuer_beide_zweige():
    quelle = Path(abholer.__file__).read_text(encoding="utf-8")
    assert quelle.count("_stimmungsmessung(szene, bericht,") == 2
    assert "urteil[\"ueberstrahlt\"] = _belichtung_modul" not in quelle
    assert abholer._stimmungsmessung({}, {"beauty_png": "x.png"}, None) == {}


# ====================================================================== 7 · Untergrenze im KI-Schritt

def test_die_untergrenze_steht_im_register():
    eintrag = backbone.hole("z-image-turbo")
    assert eintrag.ki_mindest_lange_seite == 1024 and "293" in eintrag.ki_mindest_lange_seite_beleg
    assert abholer.ki_mindest_lange_seite("z-image-turbo") == 1024
    assert backbone.ki_mindest_lange_seite_fuer("gibt-es-nicht") is None
    quelle = Path(abholer.__file__).read_text(encoding="utf-8")
    assert "mindest_lange_seite=ki_mindest_lange_seite(backbone_name)" in quelle


def test_kleine_grundlage_wird_fuer_den_ki_schritt_hochgerechnet():
    # Genau der Fall aus 293: 480 x 300 -> vorher 480 x 288, jetzt 1024 x 640.
    assert backbone.ki_groesse(480, 300, vorschau=True) == (480, 288)
    assert backbone.ki_groesse(480, 300, vorschau=True, mindest=1024) == (1024, 640)
    assert backbone.ki_groesse(960, 600, vorschau=False, mindest=1024) == (1024, 640)
    # Gross genug: wie bisher.
    assert backbone.ki_groesse(1600, 1000, vorschau=True, mindest=1024) == (1024, 640)
    assert backbone.ki_groesse(1600, 1000, vorschau=False, mindest=1024) == (1600, 992)
    assert backbone.ki_groesse(300, 480, vorschau=True, mindest=1024) == (640, 1024)


def test_die_steuerbilder_gehen_hoch_und_das_bild_zurueck(tmp_path, monkeypatch):
    pytest.importorskip("PIL")
    from test_grundlage_varianten import _vertrag
    from test_vorschau_guete import GRUNDLAGE_B, GRUNDLAGE_H, _attrappen, _rechne
    monkeypatch.setattr(abholer, "ki_mindest_lange_seite", lambda _name: 256)
    for guete in ("vorschau", "voll"):
        protokoll, attrappen = _attrappen(tmp_path / guete)
        ordner, antwort = _rechne(tmp_path / guete, attrappen, guete, guete=guete)
        assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
        for a in protokoll["render"]:
            assert bildschreiben.png_masse(a.depth_png) == (256, 160), guete
            assert bildschreiben.png_masse(a.beauty_png) == (256, 160), guete
        # Gepruefte und gelieferte Bilder in der Groesse der Grundlage.
        assert set(protokoll["qa"]) == {(GRUNDLAGE_B, GRUNDLAGE_H)}
        for name in _vertrag(ordner)["images"]:
            assert bildschreiben.png_masse(ordner / name) == (GRUNDLAGE_B, GRUNDLAGE_H)


def test_der_vermerk_sagt_hochgerechnet():
    steuer = {"hochgerechnet": True, "ki_groesse": [1024, 640], "grundlage_groesse": [480, 300],
              "verkleinert": True}
    vermerk = abholer._guete_vermerk({"guete": "vorschau"}, "z-image-turbo", 8, None, steuer)
    assert vermerk["hochgerechnet"] is True
    assert any("480x300" in h and "1024x640" in h for h in vermerk["hinweise"])
    assert "hochgerechnet" not in abholer._guete_vermerk({"guete": "vorschau"},
                                                         "z-image-turbo", 8, None, None)


# ====================================================================== 8 · geom_iou der Vorschau

KAMERA = {"auge": [0.0, -20.0, 1.7], "blick_auf": [0.0, 0.0, 1.7], "brennweite_mm": 35.0,
          "sensor_breite_mm": 36.0, "shift_y": 0.0, "gelaende_z": 0.0}


@pytest.fixture()
def bild(tmp_path) -> Path:
    pfad = tmp_path / "bild.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


def _haus_auf_endlicher_platte(b=40, h=40):
    """Der Fall aus 293: Haus (Zeilen 14–19), eine schmale Platte darunter (Zeile 20), davor
    Himmel in der Soll-Karte — und im Bild gemalter Boden bis an den unteren Rand."""
    from aiimaging import messboden
    soll = [30.0 + 0.05 * x if 14 <= y < 20 else (25.0 if y == 20 else math.inf)
            for y in range(h) for x in range(b)]
    maske = [14 <= i // b < 20 for i in range(b * h)]
    mit, _ = messboden.mit_messboden(soll, b, h, KAMERA)
    ist_bild = [1.0 / w if math.isfinite(w) else 0.001 for w in mit]     # das Bild hat Boden
    return soll, maske, ist_bild, b, h


def test_gleiche_zahl_null_gemeinsam_ist_der_gemalte_vordergrund(bild):
    """Genau die Zaehlung aus 293: ``n_soll == n_ist`` und ``n_gemeinsam == 0``. Kein Versatz
    und keine Groesse — die Auswahl «die n naechsten Punkte» nimmt den gemalten Boden VOR der
    endlichen Platte. Mit der Trennhilfe auch neben erkanntem Gelaende misst die Pruefung."""
    soll, maske, ist_bild, b, h = _haus_auf_endlicher_platte()
    ohne = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist_bild), breite=b, hoehe=h,
                            maske=maske)
    assert ohne["n_soll"] == ohne["n_ist"] > 0 and ohne["n_gemeinsam"] == 0
    _soll, trennhilfe, befund = abholer._mit_messboden(
        soll, b, h, {"kamera": KAMERA}, {"gemessen": True, "gelaende_erkannt": True})
    assert befund["angewandt"] is True and befund["neben_gelaende"] is True
    # Die Platte selbst bleibt Geometrie — die Trennhilfe liegt nur auf Hintergrund.
    assert not any(t and math.isfinite(s) for t, s in zip(trennhilfe, soll))
    mit = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist_bild), breite=b, hoehe=h,
                           maske=maske, trennhilfe=trennhilfe)
    assert mit["n_gemeinsam"] > 0 and mit["geom_iou"] > 0.9
    assert not kosmo_szene.keine_gemeinsame_silhouette(mit)


def test_eine_andere_groesse_wird_abgewiesen_nicht_still_gezaehlt(bild):
    """Die Gegenprobe zur Vermutung «Groessenfehler»: Ein Ist in anderer Groesse kommt gar
    nicht bis zur Zaehlung — es wird abgewiesen."""
    soll, maske, ist_bild, b, h = _haus_auf_endlicher_platte()
    klein = ist_bild[: (b * h) // 4]
    aus = ts.qa_gegen_soll(bild, soll, modell=attrappe(klein), breite=b, hoehe=h, maske=maske)
    assert aus["status"] != ts.STATUS_OK and aus.get("n_gemeinsam") is None


def attrappe(werte):
    from test_tiefenschaetzer import attrappe as _a
    return _a(werte)
