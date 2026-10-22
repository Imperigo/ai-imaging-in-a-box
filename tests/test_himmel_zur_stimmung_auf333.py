"""Der sichtbare Himmel passt zur Stimmung — und vier Kleinigkeiten aus ``auf-20261022-333``.

**Hauptbefund (demo-relevant):** In 333 blieb der Himmel der Variante «Mittag» dunkles
Nachtblau, und das schon im Cycles-Mittagsbild; in 331 war er bei «abend» fast schwarz
(Faktor 0,26, Stärke 0,30 → 0,079). Die Regel ``hintergrund_abstand`` «dunkler» stellt das
hellste Ende des Hintergrunds eine Blende unter das Haus — gebaut für den Verlauf (293/295);
mit «Himmel sichtbar» (Entscheid 126) wirkt sie auf das echte Himmelsbild. Jetzt: dämmrig
höchstens eine Blende dunkler (Faktor ≥ 0,5), hell nie unter die Stärke der Stimmung.

Kleinigkeiten: (a) ``glas_klar`` zählt 0,0500000007 nicht mehr als «gesetzt»; (b) die
Wortregel kennt «gelaendeflaeche»; (c) Öffnungen ohne ``kind`` werden am Namen Fenster;
(d) «Hang» wird übersetzt.

Ohne GPU und ohne Blender: reine Funktionen, der Runner mit Attrappen (Regel 2), die
Messwerte nachgestellt aus 331 (Regel 3: alles synthetisch).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from aiimaging import abholer, maske, materialwahl, sprache, stimmung

from test_heimfehler_auf292 import _runner
from test_heimfehler_auf295 import _Knoten

# ============================================================ Die Grenze, reine Rechnung

#: Aus Ergebnis 331, sSE, abend mit Himmel sichtbar: Faktor der Regel und Stärke davor.
FAKTOR_331 = 0.264261
STAERKE_VORHER_331 = 0.30000001192092896


def _abstand(faktor, *, vorher=0.796):
    return {"faktor": faktor, "richtung": "dunkler", "abstand_ev": 1.0,
            "abstand_ev_vorher": vorher,
            "abstand_ev_nachher": round(vorher + math.log2(faktor), 3),
            "haus": 0.5, "horizont": [0.2 * faktor] * 3, "zenit": [0.3 * faktor] * 3,
            "grund": ""}


def test_helle_und_daemmrige_stimmungen_sind_benannt():
    assert stimmung.HIMMEL_FAKTOR_MIN == 0.5, "eine Blende, wie der Abstand der Regel"
    assert stimmung.HINTERGRUND_ABSTAND_EV == 1.0
    for hell in ("mittag", "bedeckt", "nebel", "winter"):
        assert stimmung.himmel_untergrenze(hell) == {"art": "staerke"}
    for daemmrig in ("morgen", "abend", "blaue-stunde", "weiss", "unbekannt", None):
        assert stimmung.himmel_untergrenze(daemmrig) == {"art": "faktor", "faktor": 0.5}
    assert set(stimmung.HELLE_HIMMEL) <= set(stimmung.PRESETS)


def test_abend_331_wird_hoechstens_eine_blende_dunkler():
    """331: Faktor 0,26 (−1,9 Blenden) — jetzt 0,5, Stärke 0,15 statt 0,079."""
    aus = stimmung.himmel_begrenzen(_abstand(FAKTOR_331),
                                    stimmung.himmel_untergrenze("abend"),
                                    staerke_vorher=STAERKE_VORHER_331, staerke_stimmung=1.0)
    assert aus["faktor"] == 0.5 and aus["faktor_regel"] == FAKTOR_331
    assert aus["himmel_grenze"] == {"art": "faktor", "faktor_min": 0.5, "begrenzt": True}
    assert STAERKE_VORHER_331 * aus["faktor"] == pytest.approx(0.15)
    # Bericht nachgezogen: Abstand und Farben gehoeren zum neuen Faktor.
    assert aus["abstand_ev_nachher"] == pytest.approx(0.796 - 1.0, abs=1e-3)
    assert aus["horizont"] == [pytest.approx(0.1)] * 3
    assert aus["zenit"] == [pytest.approx(0.15)] * 3


def test_will_die_regel_weniger_abdunkeln_bleibt_ihr_faktor():
    """309: abend 0,72 — innerhalb der Grenze, nichts aendert sich."""
    aus = stimmung.himmel_begrenzen(_abstand(0.72), {"art": "faktor", "faktor": 0.5},
                                    staerke_vorher=0.3, staerke_stimmung=1.0)
    assert aus["faktor"] == 0.72 and aus["himmel_grenze"]["begrenzt"] is False
    assert aus["horizont"] == _abstand(0.72)["horizont"]


def test_mittag_steht_nie_unter_der_staerke_der_stimmung():
    """333: Mittag 0,45 (Staerke 1,0 × Fuelllicht 0,45), die Regel wollte dunkler —
    jetzt steht der Himmel bei der Staerke der Stimmung, so hell wie fotografiert."""
    fuell = stimmung.STIMMUNGEN["mittag"]["fuell_staerke"]
    vorher = 1.0 * fuell
    aus = stimmung.himmel_begrenzen(_abstand(0.5), stimmung.himmel_untergrenze("mittag"),
                                    staerke_vorher=vorher, staerke_stimmung=1.0)
    assert vorher * aus["faktor"] == pytest.approx(1.0, abs=1e-5)
    assert aus["faktor"] == pytest.approx(1.0 / fuell, abs=1e-5) and aus["faktor"] > 1.0
    assert aus["himmel_grenze"]["art"] == "staerke" and aus["himmel_grenze"]["begrenzt"]
    # Mit bestellter Intensitaet gilt die bestellte.
    halb = stimmung.himmel_begrenzen(_abstand(0.5), {"art": "staerke"},
                                     staerke_vorher=0.5 * fuell, staerke_stimmung=0.5)
    assert 0.5 * fuell * halb["faktor"] == pytest.approx(0.5, abs=1e-5)


def test_bedeckt_darf_heller_bleiben():
    """Die Regel «heller» (309: bedeckt 3,2) bleibt — die Grenze ist nur nach unten."""
    vorher = stimmung.STIMMUNGEN["bedeckt"]["fuell_staerke"]
    aus = stimmung.himmel_begrenzen(dict(_abstand(3.2), richtung="heller"),
                                    {"art": "staerke"}, staerke_vorher=vorher,
                                    staerke_stimmung=1.0)
    assert aus["faktor"] == 3.2 and aus["himmel_grenze"]["begrenzt"] is False


def test_ohne_untergrenze_bleibt_alles_wie_es_war():
    ab = _abstand(FAKTOR_331)
    assert stimmung.himmel_begrenzen(ab, None, staerke_vorher=0.3, staerke_stimmung=1.0) == ab


# ============================================================ Der Weg bis Blender

def _szene(tmp_path, preset):
    return {"umgebung": {"preset": preset, "intensitaet": 1.0, "rotationGrad": 0.0},
            "umgebung_datei": {"pfad": tmp_path / f"{preset}.hdr"}}


def test_die_untergrenze_reist_nur_mit_himmel_sichtbar(tmp_path):
    """Neue Lichtdaten = neue Grundlage: Ein alter, zu dunkler Himmel wird nicht
    wiederverwendet. Ohne Schalter bleibt der Text Wort fuer Wort (Verlauf unveraendert)."""
    for preset, erwartet in (("mittag", {"art": "staerke"}),
                             ("abend", {"art": "faktor", "faktor": 0.5})):
        ohne = json.loads(abholer.umgebung_einstellungen(_szene(tmp_path, preset))
                          ["umgebung_licht"])
        assert "himmel_untergrenze" not in ohne
        mit = json.loads(abholer.umgebung_einstellungen(
            dict(_szene(tmp_path, preset), himmel_sichtbar=True))["umgebung_licht"])
        assert mit["himmel_untergrenze"] == erwartet and mit["himmel_sichtbar"] is True


def _vorprobe(monkeypatch, tmp_path, licht, *, staerke_vorher, staerke_stimmung=1.0,
              haus=0.4, himmel=0.6):
    """Die Vorprobe mit Attrappen: ein gleichmaessiges Haus, ein Himmel heller als es."""
    modul, bpy = _runner(monkeypatch)
    bpy.data.objects = []
    grund = _Knoten(staerke_vorher)
    bpy.context.scene.world.node_tree.nodes.get = lambda name: (
        grund if name == modul.RUHIGER_GRUND else None)
    szene = SimpleNamespace(
        render=SimpleNamespace(resolution_percentage=100, film_transparent=False,
                               filepath="/x/beauty_",
                               image_settings=SimpleNamespace(file_format="PNG",
                                                              color_depth="8",
                                                              color_mode="RGBA")),
        cycles=SimpleNamespace(samples=64, use_denoising=True))

    def rendern(write_still=True):
        Path(szene.render.filepath + ".exr").write_bytes(b"exr")

    bpy.ops.render.render = rendern
    bpy.data.images.load = lambda pfad: SimpleNamespace(pixels=[haus, haus, haus, 1.0] * 50,
                                                        channels=4)
    # `himmel` ist, was die Kamera sieht; die Vorprobe rechnet Farbe × Staerke davor.
    farbe = himmel / staerke_vorher
    umgebung = {"toenung": None, "staerke": staerke_stimmung,
                "hintergrund": {"horizont": [farbe] * 3, "zenit": [farbe] * 3}}
    return modul._hintergrund_abstimmen(szene, tmp_path, licht, umgebung), grund


def _licht(preset, *, himmel):
    licht = stimmung.licht_der_stimmung(preset)
    if himmel:
        licht = dict(licht, himmel_sichtbar=True,
                     himmel_untergrenze=stimmung.himmel_untergrenze(preset))
    return licht


def test_der_runner_dunkelt_den_sichtbaren_abendhimmel_hoechstens_eine_blende(monkeypatch,
                                                                             tmp_path):
    # Himmel 1,5 Blenden ueber dem Haus: die Regel will 2,5 Blenden runter (Faktor ~0,18).
    befund, grund = _vorprobe(monkeypatch, tmp_path, _licht("abend", himmel=True),
                              staerke_vorher=0.3, haus=0.2, himmel=0.2 * 2 ** 1.5)
    assert befund["faktor_regel"] < 0.5 and befund["faktor"] == 0.5
    assert befund["himmel_grenze"]["begrenzt"] is True
    assert grund.inputs["Strength"].default_value == pytest.approx(0.15)
    assert befund["staerke_nachher"] == pytest.approx(0.15)
    # Mit dem VERLAUF (ohne Schalter) wirkt die Regel wie bisher, ungebremst.
    alt, grund_alt = _vorprobe(monkeypatch, tmp_path, _licht("abend", himmel=False),
                               staerke_vorher=0.3, haus=0.2, himmel=0.2 * 2 ** 1.5)
    assert "faktor_regel" not in alt and alt["faktor"] < 0.5
    assert grund_alt.inputs["Strength"].default_value == pytest.approx(0.3 * alt["faktor"])


def test_der_runner_laesst_den_mittagshimmel_hell(monkeypatch, tmp_path):
    fuell = stimmung.STIMMUNGEN["mittag"]["fuell_staerke"]
    befund, grund = _vorprobe(monkeypatch, tmp_path, _licht("mittag", himmel=True),
                              staerke_vorher=fuell, haus=0.2, himmel=0.2 * 2 ** 1.5)
    assert befund["faktor_regel"] < 1.0
    assert grund.inputs["Strength"].default_value == pytest.approx(1.0, abs=1e-5)
    assert befund["himmel_grenze"]["art"] == "staerke"


def test_die_grenze_greift_nur_mit_dem_schalter_in_den_lichtdaten(monkeypatch, tmp_path):
    """Eine Untergrenze ohne `himmel_sichtbar` (Verlauf) bleibt wirkungslos."""
    licht = dict(stimmung.licht_der_stimmung("abend"),
                 himmel_untergrenze=stimmung.himmel_untergrenze("abend"))
    befund, _ = _vorprobe(monkeypatch, tmp_path, licht, staerke_vorher=0.3, haus=0.2,
                          himmel=0.2 * 2 ** 1.5)
    assert "himmel_grenze" not in befund and befund["faktor"] < 0.5


# ============================================================ (a) Glas mit Toleranz

def _principled(durchlass, rauheit):
    return SimpleNamespace(type="BSDF_PRINCIPLED", inputs={
        "Transmission Weight": SimpleNamespace(default_value=durchlass),
        "Roughness": SimpleNamespace(default_value=rauheit, is_linked=False)})


def test_glas_mit_0_05_in_einfacher_genauigkeit_zaehlt_nicht_als_gesetzt(monkeypatch):
    modul, _ = _runner(monkeypatch)
    schon = _principled(0.7, 0.05000000074505806)        # so liest Blender 0,05 (333)
    rau = _principled(0.7, 1.0)
    befund = modul._glas_klar([SimpleNamespace(node_tree=SimpleNamespace(nodes=[schon])),
                               SimpleNamespace(node_tree=SimpleNamespace(nodes=[rau]))])
    assert befund == {"materialien": 1, "rauheit": 0.05}
    assert schon.inputs["Roughness"].default_value == 0.05000000074505806
    assert rau.inputs["Roughness"].default_value == 0.05


# ============================================================ (b) Gelaendeflaeche

def test_die_gelaendeflaeche_von_kosmodraw_gilt_als_gelaende():
    assert maske.ist_gelaende("gelaendeflaeche gewachsen [njjq9m]") is True
    assert maske.ist_gelaende("Gelaendeflaeche_1") is True
    assert maske.ist_gelaende("Gelaender Balkon") is False
    assert maske.ist_gelaende("Geländer_Treppe") is False


# ============================================================ (c) Oeffnungen am Namen

@pytest.mark.parametrize("name", ["Oeffnung 12", "Öffnung Süd", "Opening 3", "Fenster 1"])
def test_oeffnungen_ohne_kind_werden_fenster(name):
    assert materialwahl.art_und_herkunft(name) == ("fenster", materialwahl.HERKUNFT_NAME)


@pytest.mark.parametrize("name", ["Tueroeffnung 2", "Türöffnung", "Door opening"])
def test_eine_tueroeffnung_bleibt_ohne_art(name):
    """Eine Tür ist «uebrige» (Entscheid 113); die Namensregel sagt nichts — Material bleibt."""
    assert materialwahl.art_und_herkunft(name) == ("uebrige",
                                                   materialwahl.HERKUNFT_UNBESTIMMT)


def test_kind_hat_vorrang_vor_dem_namen():
    assert materialwahl.art_von("Oeffnung 4", kind="opening", opening_type="tuer") == "uebrige"


# ============================================================ (d) Hang

@pytest.mark.parametrize("deutsch, englisch", [
    ("Haus am Hang", "house on a hillside"),
    ("steiler Hang", "steep slope"),
    ("Hanghaus mit Garten", "hillside house with garden"),
])
def test_hang_wird_uebersetzt(deutsch, englisch):
    r = sprache.uebersetze(deutsch)
    assert r["uebersetzt"] == englisch and not r["unbekannt"]
