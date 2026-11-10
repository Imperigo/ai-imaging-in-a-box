"""A0289, Runde 2: der Beweis an der Oberseite, Stück für Stück.

``gelaendeform.oberseite`` liest die Oberseite eines Körpers aus seinen Dreiecken,
``gelaendeform.beweis`` fragt sie in fester Reihenfolge ab, ``glbbox.Dreiecksquelle`` holt die
Dreiecke aus der Datei. Jede Frage steht hier an ihrer Schwelle; was nicht lesbar ist, wird nicht
geraten. Die Fälle über ganze Modelle stehen in ``tests/test_glbbox_formregel_gemeinsam.py``.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import struct
from pathlib import Path

import pytest

from aiimaging import gelaendeform as gf
from aiimaging import glbbox

WURZEL = Path(__file__).resolve().parents[1]


def _werkzeug():
    spez = importlib.util.spec_from_file_location("glbbox_proben", WURZEL / "tools" / "glbbox_proben.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


EBEN = [((0, 0, 0), (0, 0, 10), (10, 0, 10)), ((0, 0, 0), (10, 0, 10), (10, 0, 0))]


def _schraeg(steigung):
    h = 10 * steigung
    return [((0, 0, 0), (0, h, 10), (10, h, 10)), ((0, 0, 0), (10, h, 10), (10, 0, 0))]


# ---------------------------------------------------------------- oberseite


def test_eine_waagrechte_flaeche_ist_oben_und_nicht_geneigt():
    f = gf.oberseite(EBEN)
    assert f["oben"] == pytest.approx(100.0) and f["geneigt"] == 0.0
    assert f["richtungen"] == 0 and f["tief"] == 0 and f["wand"] == 0.0 and f["dreiecke"] == 2


def test_der_umlaufsinn_entscheidet_was_oben_ist():
    unten = [(a, c, b) for a, b, c in EBEN]
    assert gf.oberseite(unten)["oben"] == 0.0 and gf.oberseite(unten)["tief"] is None
    assert gf.oberseite(unten, gespiegelt=True)["oben"] == pytest.approx(100.0)
    assert gf.oberseite(EBEN, gespiegelt=True)["oben"] == 0.0


@pytest.mark.parametrize("steigung, geneigt", [
    (0.0, False), (0.02, False), (0.03, False), (0.039, False), (0.0399, False),
    (0.0401, True), (0.041, True), (0.05, True), (0.3, True), (0.99, True), (0.999, True)])
def test_geneigt_ab_vier_prozent(steigung, geneigt):
    f = gf.oberseite(_schraeg(steigung))
    assert f["oben"] == pytest.approx(100.0)
    assert (f["geneigt"] > 0) is geneigt
    assert f["richtungen"] == (1 if geneigt else 0)


@pytest.mark.parametrize("steigung", [1.001, 1.01, 1.5, 5.0, 1000.0])
def test_steiler_als_45_grad_ist_wand_und_keine_oberseite(steigung):
    f = gf.oberseite(_schraeg(steigung))
    assert f["oben"] == 0.0 and f["steil"] > 0 and f["tief"] is None


def test_eine_lotrechte_wand_am_rand_zaehlt_nicht_im_inneren_schon():
    rand = EBEN + [((0, 0, 0), (0, 3, 0), (0, 3, 10))]
    assert gf.oberseite(rand)["wand"] == 0.0
    innen = EBEN + [((5, 0, 0), (5, 3, 0), (5, 3, 10))]
    assert gf.oberseite(innen)["wand"] == 3.0
    # Eine schiefe Randfläche (nicht alle Ecken auf der Randlinie) zählt als innen.
    schief = EBEN + [((0, 0, 0), (0.5, 3, 0), (0, 3, 10))]
    assert gf.oberseite(schief)["wand"] == 3.0


def test_richtungen_zaehlen_felder_nicht_dreiecke():
    viele_gleiche = _schraeg(0.1) * 50
    assert gf.oberseite(viele_gleiche)["richtungen"] == 1
    verschieden = [d for s in (0.05, 0.06, 0.07, 0.08, 0.09, 0.10) for d in _schraeg(s)]
    assert gf.oberseite(verschieden)["richtungen"] == 6
    # Zwei Ebenen im selben Feld von 1 %: eine Richtung.
    nah = _schraeg(0.101) + _schraeg(0.103)
    assert gf.oberseite(nah)["richtungen"] == 1


def test_entartete_dreiecke_zaehlen_nichts():
    f = gf.oberseite([((0, 0, 0), (0, 0, 0), (0, 0, 0)), ((0, 0, 0), (1, 0, 0), (2, 0, 0))])
    assert f["oben"] == 0.0 and f["steil"] == 0.0 and f["tief"] is None and f["dreiecke"] == 2
    leer = gf.oberseite([])
    assert leer["oben"] == 0.0 and leer["dreiecke"] == 0


def test_hoch_zwei_rechnet_wie_hoch_eins():
    z_oben = [tuple((x, -z, y) for x, y, z in d) for d in _schraeg(0.1)]
    f = gf.oberseite(z_oben, hoch=2)
    assert f["oben"] == pytest.approx(100.0) and f["geneigt"] == pytest.approx(100.0)


# ---------------------------------------------------------------- beweis und unterbauung

GELAENDE = ("g", [-30, 0, -25], [30, 4, 25])
HAUS = ("h", [-6, 2, -5], [6, 14, 5])


def _flaeche(**anders):
    # Die Oberseite liegt ueberall auf 4 m (fuer die Fussprobe).
    f = {"oben": 3000.0, "geneigt": 3000.0, "steil": 0.0, "wand": 0.0, "tief": 0.0, "richtungen": 40,
         "raster": {"lo": (-30.0, -25.0), "hi": (30.0, 25.0), "hoehen": [4.0] * 256}}
    f.update(anders)
    return f


@pytest.mark.parametrize("anders, kurz", [
    ({}, ""),
    ({"oben": 1500.0, "geneigt": 1500.0}, ""), ({"oben": 1499.9, "geneigt": 1499.9}, gf.GRUND_DECKUNG),
    ({"oben": 0.0, "geneigt": 0.0}, gf.GRUND_DECKUNG),
    ({"oben": 3750.0, "geneigt": 3750.0}, ""), ({"oben": 3750.1, "geneigt": 3750.1}, gf.GRUND_LAGEN),
    ({"geneigt": 1500.0}, ""), ({"geneigt": 1499.9}, gf.GRUND_EBEN), ({"geneigt": 0.0}, gf.GRUND_EBEN),
    ({"richtungen": 6}, ""), ({"richtungen": 5}, gf.GRUND_EINE_EBENE), ({"richtungen": 1}, gf.GRUND_EINE_EBENE),
    ({"wand": 2.0}, ""), ({"wand": 2.01}, gf.GRUND_WAND),
    ({"tief": 1.5}, ""), ({"tief": 1.51}, gf.GRUND_SOCKEL), ({"tief": None}, gf.GRUND_SOCKEL),
])
def test_beweis_an_jeder_schwelle(anders, kurz):
    b = gf.beweis(0, [GELAENDE, HAUS], _flaeche(**anders))
    assert b["kurz"] == kurz
    assert b["urteil"] == (gf.GELAENDE if kurz == "" else gf.NICHT_ENTSCHEIDBAR)
    assert b["grund"]


def test_beweis_ohne_lesbare_dreiecke_ist_nie_gelaende():
    b = gf.beweis(0, [GELAENDE, HAUS], None)
    assert b["urteil"] == gf.NICHT_ENTSCHEIDBAR and b["kurz"] == gf.GRUND_NICHT_LESBAR


def test_die_reihenfolge_der_fragen_steht_fest():
    """Trifft mehreres zu, nennt der Beweis das Erste: Deckung vor Lagen vor eben vor uneben vor Wand
    vor Sockel vor unterbaut. Heim-PC und Mac nennen so denselben Grund."""
    garage = ("u", [-30, -3, -25], [30, 0, 25])
    alle = [GELAENDE, HAUS, garage]
    alles_falsch = _flaeche(geneigt=0.0, richtungen=0, wand=9.0, tief=9.0)
    assert gf.beweis(0, alle, alles_falsch)["kurz"] == gf.GRUND_EBEN
    assert gf.beweis(0, alle, _flaeche(richtungen=0, wand=9.0, tief=9.0))["kurz"] == gf.GRUND_EINE_EBENE
    assert gf.beweis(0, alle, _flaeche(wand=9.0, tief=9.0))["kurz"] == gf.GRUND_WAND
    assert gf.beweis(0, alle, _flaeche(tief=9.0))["kurz"] == gf.GRUND_SOCKEL
    assert gf.beweis(0, alle, _flaeche())["kurz"] == gf.GRUND_UNTERBAUT


@pytest.mark.parametrize("anderer, anteil", [
    (("k", [-30, -3, -25], [-15, 0, 25]), 0.25),          # ein Streifen, genau ein Viertel
    (("k", [-6, -3, -5], [6, 9, 5]), 120.0 / 3000.0),      # Keller unter dem Haus
    (("k", [-30, -0.1, -25], [30, 0, 25]), 0.0),           # genau 0,1 m tiefer zählt noch nicht
    (("k", [-30, -0.11, -25], [30, 0, 25]), 1.0),
    (("k", [40, -3, -25], [50, 0, 25]), 0.0),              # daneben, nicht darunter
    (("k", [-30, 1, -25], [30, 2, 25]), 0.0),              # nicht tiefer
])
def test_unterbauung(anderer, anteil):
    assert gf.unterbauung(0, [GELAENDE, anderer]) == pytest.approx(anteil)


def test_unterbauung_misst_die_huelle_nicht_die_summe():
    stuetzen = [("s", [x, -4, z], [x + 0.5, 0, z + 0.5]) for x in (-30, 29.5) for z in (-25, 24.5)]
    assert gf.unterbauung(0, [GELAENDE, *stuetzen]) == pytest.approx(1.0)
    assert gf.beweis(0, [GELAENDE, *stuetzen], _flaeche())["kurz"] == gf.GRUND_UNTERBAUT


def test_ohne_oberseiten_gilt_das_alte_urteil_weiter():
    """Andere Aufrufer (der Blender-Lauf) fragen ``gelaende_knoten`` ohne Oberseiten: unverändert."""
    platte = ("p", [-30, -0.5, -25], [30, 0, 25])
    haus = ("h", [-6, 0, -5], [6, 9, 5])
    alt = gf.gelaende_knoten([platte, haus])
    assert alt["gelaende"] == ("p",) and alt["gelaende_stellen"] == (0,)
    neu = gf.gelaende_knoten([platte, haus], oberseiten=lambda stelle: None)
    assert neu["gelaende"] == () and neu["unklar_stellen"] == (0,)
    assert neu["urteile"][0]["kurz"] == gf.GRUND_NICHT_LESBAR


def test_oberseiten_werden_nur_fuer_kandidaten_gefragt():
    gefragt = []

    def frage(stelle):
        gefragt.append(stelle)
        return _flaeche()

    turm = ("t", [-6, 2, -5], [6, 60, 5])
    klein = ("k", [10, 0, 10], [12, 1, 12])
    aus = gf.gelaende_knoten([GELAENDE, turm, klein], oberseiten=frage)
    assert gefragt == [0]
    assert aus["gelaende_stellen"] == (0,)


# ---------------------------------------------------------------- Dreiecksquelle: was nicht lesbar ist


def _hang_glb(tmp_path, aendern=None, binaerblock=False, name="x.glb"):
    w = _werkzeug()
    b = w._Bau()
    b.flaeche("Flaeche", -30, -25, 30, 25, 12, 10, w._hang(0.1, "z"))
    b.haus(-6, -5, 12, 10, 12, y=-0.5)
    js = b.kopf()
    if aendern is not None:
        aendern(js)
    p = tmp_path / name
    w.schreibe_glb(js, p, binaerblock)
    return p, js


def test_der_lesbare_hang_wird_abgetrennt(tmp_path):
    for binaer in (False, True):
        p, _ = _hang_glb(tmp_path, binaerblock=binaer)
        aus = glbbox.bauwerksbox(p)
        assert aus["entschieden_durch"] == "form" and aus["n_gelaende"] == 1
        assert aus["gelaende_namen"] == ("Flaeche",)
        assert "gelaende_stellen" not in aus, "das Hilfsfeld bleibt im Befund, nicht im Ergebnis"
        assert aus["form_befund"]["gelaende_stellen"] == (0,)


def _ohne_puffer(js):
    del js["buffers"]


def _fremde_datei(js):
    js["buffers"][0]["uri"] = "gelaende.bin"


def _kaputtes_base64(js):
    js["buffers"][0]["uri"] = "data:application/octet-stream;base64,@@@@"


def _puffer_zu_kurz(js):
    roh = base64.b64decode(js["buffers"][0]["uri"].split(";base64,", 1)[1])
    js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(roh[:100]).decode()


def _zeichenart_streifen(js):
    js["meshes"][0]["primitives"][0]["mode"] = 5


def _gepackt(js):
    js["meshes"][0]["primitives"][0]["extensions"] = {"KHR_draco_mesh_compression": {"bufferView": 0}}


def _duenn_besetzt(js):
    js["accessors"][0]["sparse"] = {"count": 1}


def _quantisiert(js):
    js["accessors"][0]["componentType"] = 5123


def _ohne_sicht(js):
    del js["accessors"][0]["bufferView"]


def _index_ueber_die_ecken(js):
    js["accessors"][0]["count"] = 5


def _sicht_zu_kurz(js):
    js["bufferViews"][0]["byteLength"] = 24


def _sicht_gepackt(js):
    js["bufferViews"][0]["extensions"] = {"EXT_meshopt_compression": {}}


def _indexformat_fremd(js):
    js["accessors"][1]["componentType"] = 5126


@pytest.mark.parametrize("aendern", [
    _ohne_puffer, _fremde_datei, _kaputtes_base64, _puffer_zu_kurz, _zeichenart_streifen, _gepackt,
    _duenn_besetzt, _quantisiert, _ohne_sicht, _index_ueber_die_ecken, _sicht_zu_kurz, _sicht_gepackt,
    _indexformat_fremd], ids=lambda f: f.__name__.strip("_"))
def test_was_nicht_lesbar_ist_wird_nicht_geraten(tmp_path, aendern):
    p, _ = _hang_glb(tmp_path, aendern)
    aus = glbbox.bauwerksbox(p)
    assert aus["entschieden_durch"] == "keine"
    assert aus["bbox_bauwerk"] == aus["bbox_szene"]
    assert aus["form_befund"]["gruende"] == (gf.GRUND_NICHT_LESBAR,)
    assert "NICHT ENTSCHEIDBAR" in aus["note"] and gf.GRUND_NICHT_LESBAR in aus["note"]


def test_ein_abgeschnittener_binaerblock_ist_nicht_lesbar(tmp_path):
    p, _ = _hang_glb(tmp_path, binaerblock=True)
    roh = p.read_bytes()
    kopf = 20 + struct.unpack_from("<I", roh, 12)[0]
    for ende in (kopf, kopf + 4, kopf + 8, kopf + 8 + 40):
        q = tmp_path / f"kurz{ende}.glb"
        q.write_bytes(roh[:ende])
        aus = glbbox.bauwerksbox(q)
        assert aus["entschieden_durch"] == "keine", ende
        assert aus["form_befund"]["gruende"] == (gf.GRUND_NICHT_LESBAR,), ende


def test_eine_gltf_mit_puffer_im_kopf_ist_lesbar(tmp_path):
    p, js = _hang_glb(tmp_path)
    q = tmp_path / "x.gltf"
    q.write_text(json.dumps(js), encoding="utf-8")
    assert glbbox.bauwerksbox(q)["entschieden_durch"] == "form"


def test_zu_viele_dreiecke_werden_nicht_gelesen(tmp_path, monkeypatch):
    p, _ = _hang_glb(tmp_path)
    monkeypatch.setattr(glbbox, "DREIECKE_HOECHSTENS", 239)
    assert glbbox.bauwerksbox(p)["form_befund"]["gruende"] == (gf.GRUND_NICHT_LESBAR,)
    monkeypatch.setattr(glbbox, "DREIECKE_HOECHSTENS", 240)
    assert glbbox.bauwerksbox(p)["entschieden_durch"] == "form"


def test_die_form_liest_nur_wenn_die_namen_nichts_trennen(tmp_path, monkeypatch):
    """Wo die Namensregel wirkt, wird kein einziges Dreieck angefasst (der Weg bleibt so schnell wie er war)."""
    w = _werkzeug()
    b = w._Bau()
    b.flaeche("Terrain", -60, -50, 60, 50, 12, 10, w._hang(0.1, "z"))
    b.haus(-6, -5, 12, 10, 12, y=-0.5)
    p = tmp_path / "n.glb"
    w.schreibe_glb(b.kopf(), p)

    def verboten(self, herkunft):
        raise AssertionError("die Dreiecke wurden gelesen, obwohl der Name getrennt hat")
    monkeypatch.setattr(glbbox.Dreiecksquelle, "oberseite", verboten)
    aus = glbbox.bauwerksbox(p)
    assert aus["entschieden_durch"] == "name" and aus["form_befund"] is None


# ---------------------------------------------------------------- Gelände trägt (Gegenprobe 10.11.2026)


@pytest.mark.parametrize("anderer, ja", [
    (("h", [-6, 2, -5], [6, 14, 5]), True),               # das Haus steht darauf
    (("t", [40, 0, -5], [50, 60, 5]), False),             # der Turm steht daneben
    (("t", [30, 0, -5], [40, 60, 5]), False),             # stumpf am Rand: berührt, steht nicht darauf
    (("h", [24, 0, -5], [36, 20, 5]), True),              # genau die Hälfte darauf
    (("h", [24.1, 0, -5], [36.1, 20, 5]), False),         # knapp weniger als die Hälfte
    (("m", [0, 0, 0], [0.25, 20, 0.25]), False),          # ein Mast ist kein Haus
    (("r", [0, 0, 0], [2, 20, 2]), True),                 # genau 4 m2
    (("r", [0, 0, 0], [2, 20, 1.99]), False),
    (("n", [0, 0, 0], [10, 3.9, 10]), False),             # überragt das Gelände nicht
])
def test_gelaende_traegt_was_die_szene_ueberragt(anderer, ja):
    assert gf.traegt([0], [GELAENDE, anderer]) is ja


def test_traegt_misst_gegen_die_gemeinsame_huelle_aller_gelaendekoerper():
    links = ("g1", [-30, 0, -25], [0, 4, 25])
    rechts = ("g2", [0, 0, -25], [30, 4, 25])
    haus = ("h", [-6, 2, -5], [6, 14, 5])
    assert gf.traegt([0, 1], [links, rechts, haus])
    assert not gf.traegt([], [links, rechts, haus])


def test_eine_schale_neben_einem_turm_wird_nicht_abgetrennt():
    """Der Beweis an der Oberseite gelingt, aber das Hohe steht daneben: nicht entscheidbar."""
    turm = ("t", [40, 0, -5], [50, 60, 5])
    aus = gf.gelaende_knoten([GELAENDE, turm], oberseiten=lambda stelle: _flaeche())
    assert aus["gelaende_stellen"] == () and aus["unklar_stellen"] == (0,)
    assert aus["urteile"][0]["kurz"] == gf.GRUND_TRAEGT_NICHT


def test_eine_box_die_keine_endliche_zahl_ist_gibt_keine_auskunft(tmp_path):
    def unendlich(js):
        js["accessors"][0]["max"][0] = 1e400
    p, _ = _hang_glb(tmp_path, unendlich)
    with pytest.raises(glbbox.GlbError):
        glbbox.bauwerksbox(p)


def test_die_fussprobe_ein_turm_der_durch_die_schale_stoesst_steht_nicht_darauf():
    schale = _flaeche()
    schale["raster"]["hoehen"] = [6.0] * 256
    turm = ("t", [-5, 0, -5], [5, 60, 5])
    assert gf.traegt([0], [GELAENDE, turm]) is True, "ohne Oberseiten gibt es keine Fussprobe"
    assert gf.traegt([0], [GELAENDE, turm], flaechen={0: schale}) is False
    aufgesetzt = ("h", [-5, 2.5, -5], [5, 60, 5])
    assert gf.traegt([0], [GELAENDE, aufgesetzt], flaechen={0: schale}) is True, "genau 3,5 m darunter"
    knapp = ("h", [-5, 2.49, -5], [5, 60, 5])
    assert gf.traegt([0], [GELAENDE, knapp], flaechen={0: schale}) is False
    assert gf.oberkante_bei(schale, 0, 1, 0, 1) == 6.0
    assert gf.oberkante_bei(schale, 40, 50, 0, 1) is None
    assert gf.oberkante_bei(None, 0, 1, 0, 1) is None


def test_das_raster_traegt_je_feld_die_hoechste_ecke():
    f = gf.oberseite(_schraeg(0.1))
    hoehen = f["raster"]["hoehen"]
    assert len(hoehen) == gf.RASTER_FELDER ** 2 and max(hoehen) == 1.0
    assert f["raster"]["lo"] == (0, 0) and f["raster"]["hi"] == (10, 10)
    assert gf.oberseite([])["raster"]["hoehen"] == [None] * gf.RASTER_FELDER ** 2


def test_ecken_jenseits_jeder_baugroesse_sind_nicht_lesbar(tmp_path):
    def riesig(js):
        js["nodes"][0]["scale"] = [1e150, 1e150, 1e150]
        for k in js["nodes"][1:]:
            k["scale"] = [1e150, 1e150, 1e150]
    p, _ = _hang_glb(tmp_path, riesig)
    aus = glbbox.bauwerksbox(p)
    assert aus["entschieden_durch"] == "keine"
    assert aus["form_befund"]["gruende"] == (gf.GRUND_NICHT_LESBAR,)
