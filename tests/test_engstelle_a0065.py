"""A0065 · EINE Engstelle am letzten Schritt vor dem Bild (Owner-Entscheid 31.10.2026 «Immer vom Render»).

Kein Lauf liefert ``status: ok``, wenn der Beauty-Render derselben Kamera nicht im Modellaufruf
angekommen ist — für **alle** Modelle und **alle** Wege (Knoten, Nachrender, Bildstufe, Bibliothek,
Homeworker). Die Regel steht an einer Stelle, in :func:`aiimaging.render.rendere`: geliefert wird nur,
wenn ein Grundbild bestellt war (``beauty_png``) und das Modell genau den bestellten Modus mit
Grundbild meldet (``modus_gerechnet == modus_bestellt``; ``None`` — unbelegt — zählt nicht).

Dazu die Mängel 1–3 der Gegenlese G-A0051 Runde 4:

1. Der Nachrender rechnet auf einem beliebigen Bild (Bildquelle, früheres KI-Bild), nicht auf dem
   Beauty-Render derselben Kamera — er wird ausser für Skizzen abgewiesen, vor jedem Modellaufruf.
2. (a) Ein Lauf mit ``beauty_png`` als ``image_edit``, dessen Bild nicht ankommt, und (b) ein Lauf,
   dessen Naht keinen Modus meldet, liefern kein Bild.
3. Alte Treffer im Speicher der Mappe umgehen die Sperren nicht: Die Fassungen von ``render`` und
   ``nachrender`` sind hochgezählt.

Und der Befund Messweg: ``tools/homeworker.py`` (art «render») rechnet nur noch vom Beauty-Render mit
Bildeingang und prüft V0 (darf das Modell rechnen?) und V1 (kennt der Lader seine Pipeline?) vor
Blender.

Ohne GPU, ohne Gewichte, ohne Blender; alles synthetisch (Regel 3).
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import pytest

from conftest import MINI_PNG, REPO

from aiimaging import backbone, kette, kosmo_szene, render
from aiimaging.graph import FASSUNG_ANFANG, ArtefaktCache, Knoten


def _pngs(tmp_path):
    tiefe, schoen = tmp_path / "tiefe.png", tmp_path / "beauty.png"
    tiefe.write_bytes(MINI_PNG)
    schoen.write_bytes(MINI_PNG)
    return str(tiefe), str(schoen)


#: Kein Modus in der Antwort — wie ein Modell als Pfad oder eine fremde Naht.
OHNE_MODUS = object()


class _Modell:
    """Bildmodell-Attrappe: schreibt ein Bild und meldet einen Modus (oder keinen)."""

    def __init__(self, tmp_path, gerechnet=None, *, nur_pfad=False):
        self.parameter = []
        self.ziel = tmp_path / "ki.png"
        self.gerechnet = gerechnet
        self.nur_pfad = nur_pfad

    def __call__(self, parameter):
        self.parameter.append(parameter)
        self.ziel.write_bytes(MINI_PNG)
        if self.nur_pfad:
            return str(self.ziel)
        antwort = {"bild_png": str(self.ziel), "modus_bestellt": parameter["modus"]}
        if self.gerechnet is not OHNE_MODUS:
            antwort["modus_gerechnet"] = self.gerechnet or parameter["modus"]
        return antwort


def _kein_bild(erg, modell=None):
    """Kein Bild. Wurde das Modell gerufen, sagt der Grund MASSTREUE; sonst lehnte schon die
    Prüfung vor dem Laden ab (z. B. Regel 1 bei flux1-dev) — auch das ist kein Bild."""
    assert erg["status"] != render.STATUS_OK, erg
    assert not erg.get("bild_png"), erg
    if modell is None or modell.parameter:
        assert kosmo_szene.SATZ_MASSTREUE in str(erg.get("error") or erg.get("maengel")), erg


# ====================================================================== die Engstelle (alle Modelle)

ALLE_MODELLE = sorted(backbone.BACKBONES)


@pytest.mark.parametrize("bb", ALLE_MODELLE)
def test_ohne_beauty_render_liefert_kein_modell_ein_bild(tmp_path, bb):
    """Ein Lauf ohne Grundbild (``txt2img``) wird vor jedem Modellaufruf abgewiesen."""
    tiefe, _ = _pngs(tmp_path)
    modell = _Modell(tmp_path)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, prompt="Haus", backbone=bb,
                                              schritte=8), modell=modell)
    _kein_bild(erg)
    assert modell.parameter == [], "kein Modellaufruf ohne Beauty-Render"


@pytest.mark.parametrize("bb", ALLE_MODELLE)
@pytest.mark.parametrize("gerechnet", [render.MODUS_TXT2IMG, render.MODUS_TIEFE_ALS_BILD,
                                       OHNE_MODUS])
def test_nicht_angekommenes_grundbild_liefert_bei_keinem_modell_ein_bild(tmp_path, bb, gerechnet):
    """Mit Grundbild bestellt, aber das Modell meldet einen anderen Modus (oder keinen)."""
    tiefe, schoen = _pngs(tmp_path)
    modell = _Modell(tmp_path, gerechnet)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              backbone=bb, schritte=8), modell=modell)
    _kein_bild(erg, modell)


@pytest.mark.parametrize("bb", ALLE_MODELLE)
def test_ein_modell_das_nur_einen_pfad_liefert_ist_kein_beleg(tmp_path, bb):
    tiefe, schoen = _pngs(tmp_path)
    modell = _Modell(tmp_path, nur_pfad=True)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              backbone=bb, schritte=8), modell=modell)
    _kein_bild(erg, modell)


def test_gegenprobe_angekommenes_grundbild_liefert(tmp_path):
    """Der Weg bleibt offen: Vorgabemodell mit eigenem Start, Modus wie bestellt."""
    tiefe, schoen = _pngs(tmp_path)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              schritte=8, bildeingang_staerke=0.5),
                         modell=_Modell(tmp_path))
    assert erg["status"] == render.STATUS_OK, erg.get("error") or erg.get("maengel")
    assert erg["modus_gerechnet"] == erg["modus_bestellt"] == render.MODUS_BILD_UND_TIEFE


def test_gegenprobe_bearbeitungsmodell_mit_angekommenem_bild_liefert(tmp_path):
    tiefe, schoen = _pngs(tmp_path)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              backbone="qwen-image-edit-2511", schritte=8),
                         modell=_Modell(tmp_path))
    assert erg["status"] == render.STATUS_OK, erg.get("error") or erg.get("maengel")
    assert erg["modus_gerechnet"] == render.MODUS_IMAGE_EDIT


# ====================================================================== Mangel 2 (a) und (b)

def test_mangel_2a_image_edit_am_vorgabemodell_ohne_ankunft_liefert_kein_bild(tmp_path):
    """G-A0051 R4 (2a): RenderAuftrag(beauty_png, z-image-turbo) mit Attrappe txt2img."""
    tiefe, schoen = _pngs(tmp_path)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              backbone="z-image-turbo", schritte=8),
                         modell=_Modell(tmp_path, render.MODUS_TXT2IMG))
    _kein_bild(erg)
    assert erg["modus_gerechnet"] == render.MODUS_TXT2IMG


def test_mangel_2b_bild_und_tiefe_ohne_gemeldeten_modus_liefert_kein_bild(tmp_path):
    """G-A0051 R4 (2b): None ≠ bestellt — ein unbelegter Lauf gilt nicht als vom Render."""
    tiefe, schoen = _pngs(tmp_path)
    erg = render.rendere(render.RenderAuftrag(depth_png=tiefe, beauty_png=schoen, prompt="Haus",
                                              schritte=8, bildeingang_staerke=0.5),
                         modell=_Modell(tmp_path, OHNE_MODUS))
    _kein_bild(erg)
    assert erg["modus_gerechnet"] is None


# ====================================================================== Mangel 1: der Nachrender

def _nachrender_knoten(backbone="z-image-turbo", **mehr):
    return Knoten(id="n", art=kette.ART_NACHRENDER, eingaenge=("m", "b"), params={
        "prompt": "heller", "negativ_prompt": "", "backbone": backbone, "seed": 0,
        "schritte": 8, "controlnet_staerke": 0.8, "denoise": 0.6, **mehr})


@pytest.mark.parametrize("bb", ["z-image-turbo", "qwen-image-edit-2511", "sdxl-juggernaut"])
@pytest.mark.parametrize("denoise", [0.6, 1.0])
def test_mangel_1_der_nachrender_auf_einem_fremden_bild_ruft_kein_modell(tmp_path, bb, denoise):
    """Bildquelle oder früheres KI-Bild ist nicht der Beauty-Render derselben Kamera."""
    tiefe, fremd = _pngs(tmp_path)
    modell = _Modell(tmp_path, render.MODUS_TXT2IMG)
    erg = kette.nachrender_ausfuehrer(modell=modell)(
        knoten=_nachrender_knoten(bb, denoise=denoise),
        eingaben=[{"status": "ok", "depth_png": tiefe}, {"status": "ok", "bild_png": fremd}],
        out_dir=tmp_path)
    assert erg["status"] != "ok" and not erg.get("bild_png")
    assert kosmo_szene.SATZ_MASSTREUE in str(erg.get("error"))
    assert modell.parameter == [], "kein Modellaufruf"


def test_mangel_1_auch_mit_bildeingang_staerke_kein_nachrender_ausser_skizze(tmp_path):
    tiefe, fremd = _pngs(tmp_path)
    modell = _Modell(tmp_path)
    erg = kette.nachrender_ausfuehrer(modell=modell)(
        knoten=_nachrender_knoten(bildeingang_staerke=0.55),
        eingaben=[{"status": "ok", "depth_png": tiefe}, {"status": "ok", "bild_png": fremd}],
        out_dir=tmp_path)
    assert erg["status"] != "ok"
    assert modell.parameter == []


def test_mangel_1_der_bibliotheksweg_kette_liefert_aus_dem_nachrender_kein_bild(tmp_path):
    """haenge_nachrender_an steht in __all__; fuehre_aus führt ihn — ohne Skizze kein Bild."""
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCH", encoding="utf-8")
    graph = kette.haenge_nachrender_an(kette.baue_kette(ifc_path=str(ifc), prompt="Haus"),
                                       prompt="heller")
    tiefe, schoen = _pngs(tmp_path)
    modell = _Modell(tmp_path)

    def geometrie(*, knoten, eingaben, out_dir):
        glb = out_dir / "m.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [1, 1, 1]]}

    def multipass(*, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": tiefe, "beauty_png": schoen}

    tabelle = dict(kette.AUSFUEHRER, **{
        kette.ART_GEOMETRIE: geometrie, kette.ART_MULTIPASS: multipass,
        kette.ART_RENDER: kette.render_ausfuehrer(modell=modell),
        kette.ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell),
        kette.ART_QA: lambda **_: {"status": "ok", "bestanden": True}})
    lauf = kette.fuehre_aus(graph, ausfuehrer=tabelle, out_dir=tmp_path / "out")
    nach = [k for k in graph.knoten.values() if k.art == kette.ART_NACHRENDER]
    assert nach
    for k in nach:
        ergebnis = lauf["knoten"][k.id]
        assert ergebnis.get("status") != "ok" and not ergebnis.get("bild_png"), ergebnis


def test_gegenprobe_die_skizze_bleibt_ausgenommen(tmp_path):
    """Owner-Punkt offen (R3 H5): die Skizze bringt ihr eigenes Bild mit — und es muss ankommen."""
    tiefe, skizze = _pngs(tmp_path)
    modell = _Modell(tmp_path)
    erg = kette.nachrender_ausfuehrer(modell=modell)(
        knoten=_nachrender_knoten(bildeingang_staerke=0.55, skizze=True),
        eingaben=[{"status": "ok", "depth_png": tiefe}, {"status": "ok", "bild_png": skizze}],
        out_dir=tmp_path)
    assert erg["status"] == "ok", erg.get("error")
    assert modell.parameter[0]["modus"] == render.MODUS_BILD_UND_TIEFE


def test_die_skizze_liefert_kein_bild_wenn_sie_nicht_ankommt(tmp_path):
    """Auch die Skizze geht durch die Engstelle: kommt sie nicht an, wäre es ein Bild aus Text."""
    tiefe, skizze = _pngs(tmp_path)
    erg = kette.nachrender_ausfuehrer(modell=_Modell(tmp_path, render.MODUS_TXT2IMG))(
        knoten=_nachrender_knoten(skizze=True),
        eingaben=[{"status": "ok", "depth_png": tiefe}, {"status": "ok", "bild_png": skizze}],
        out_dir=tmp_path)
    assert erg["status"] != "ok" and not erg.get("bild_png")


def test_haenge_nachrender_an_traegt_die_skizze_nur_wenn_gesagt(tmp_path):
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCH", encoding="utf-8")
    grund = kette.baue_kette(ifc_path=str(ifc), prompt="Haus")
    ohne = kette.haenge_nachrender_an(grund, prompt="heller")
    mit = kette.haenge_nachrender_an(grund, prompt="heller", eingangsbild=str(ifc), skizze=True)
    params_ohne = [k.params for k in ohne.knoten.values() if k.art == kette.ART_NACHRENDER][0]
    params_mit = [k.params for k in mit.knoten.values() if k.art == kette.ART_NACHRENDER][0]
    assert "skizze" not in params_ohne
    assert params_mit["skizze"] is True


def test_der_skizzenweg_der_mappe_sagt_skizze(tmp_path, monkeypatch):
    """arbeitsgang._skizzengraph ist der einzige Weg der Oberfläche zum Nachrender."""
    from aiimaging import arbeitsgang  # noqa: PLC0415
    gesehen = {}
    echt = kette.haenge_nachrender_an

    def merke(*a, **kw):
        gesehen.update(kw)
        return echt(*a, **kw)

    monkeypatch.setattr(kette, "haenge_nachrender_an", merke)
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCH", encoding="utf-8")
    grund = kette.baue_kette(ifc_path=str(ifc), prompt="Haus")
    monkeypatch.setattr(arbeitsgang, "_baue_grundgraph", lambda *a, **k: grund)
    arbeitsgang._skizzengraph("m.glb", {}, {}, pfad=ifc, anweisung="heller")
    assert gesehen.get("skizze") is True


# ====================================================================== Mangel 3: alte Treffer im Speicher

def test_mangel_3_render_und_nachrender_sind_hochgezaehlt():
    assert kette.FASSUNGEN[kette.ART_RENDER] > FASSUNG_ANFANG
    assert kette.FASSUNGEN[kette.ART_NACHRENDER] > FASSUNG_ANFANG


def test_mangel_3_alter_treffer_an_einem_abgewiesenen_modell_wird_nicht_geliefert(tmp_path,
                                                                                 monkeypatch):
    """Ein früher (vor A0051b) gerechneter Render-Knoten an sdxl lag im Speicher der Mappe."""
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCH", encoding="utf-8")
    graph = kette.baue_kette(ifc_path=str(ifc), prompt="Haus", backbone="sdxl-juggernaut")
    tiefe, schoen = _pngs(tmp_path)
    cache = ArtefaktCache(tmp_path / "cache")

    def geometrie(*, knoten, eingaben, out_dir):
        glb = out_dir / "m.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [1, 1, 1]]}

    def multipass(*, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": tiefe, "beauty_png": schoen}

    def alter_render(*, knoten, eingaben, out_dir):
        bild = out_dir / "bild.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "modus_gerechnet": "txt2img"}

    def tabelle(render_stufe):
        return dict(kette.AUSFUEHRER, **{
            kette.ART_GEOMETRIE: geometrie, kette.ART_MULTIPASS: multipass,
            kette.ART_RENDER: render_stufe,
            kette.ART_QA: lambda **_: {"status": "ok", "bestanden": True}})

    # Der alte Stand: alle Arten auf der Anfangsfassung, der alte Render lieferte.
    with monkeypatch.context() as alt:
        for art in list(kette.FASSUNGEN):
            alt.setitem(kette.FASSUNGEN, art, FASSUNG_ANFANG)
        erst = kette.fuehre_aus(graph, cache=cache, ausfuehrer=tabelle(alter_render),
                                out_dir=tmp_path / "out")
    assert erst["knoten"][kette.KNOTEN_RENDER]["status"] == "ok"

    modell = _Modell(tmp_path)
    jetzt = kette.fuehre_aus(graph, cache=cache,
                             ausfuehrer=tabelle(kette.render_ausfuehrer(modell=modell)),
                             out_dir=tmp_path / "out")
    knoten = jetzt["knoten"][kette.KNOTEN_RENDER]
    assert knoten.get("aus_cache") is not True, "alter Treffer geliefert"
    assert knoten.get("status") != "ok" and not knoten.get("bild_png"), knoten


# ====================================================================== Befund Messweg: tools/homeworker.py

def _lade_homeworker():
    pfad = REPO / "tools" / "homeworker.py"
    spec = importlib.util.spec_from_file_location("homeworker", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("homeworker", modul)
    spec.loader.exec_module(modul)
    return modul


hw = _lade_homeworker()


def _bericht(tmp_path):
    tiefe, schoen = _pngs(tmp_path)
    return {"depth_png": tiefe, "beauty_png": schoen, "depth_exr": None,
            "depth_png_fehler": None}


def _rufe(tmp_path, params, modell):
    return hw._render_und_qa(
        {"auftrag_id": "auf-20261031-999", "art": "render", "params": params},
        _bericht(tmp_path), {"status": "ok", "glb_path": "/x.glb", "up_axis": "Y"},
        tmp_path, params, time.monotonic(), _render_modell=modell,
        _tiefen_modell=lambda p: [0.0])


def test_der_messweg_rechnet_am_vorgabemodell_mit_bildeingang_vom_render(tmp_path):
    modell = _Modell(tmp_path)
    erg = _rufe(tmp_path, {"prompt": "Haus", "schritte": 8}, modell)
    assert modell.parameter, erg
    p = modell.parameter[0]
    assert p["beauty_png"].endswith("beauty.png")
    assert p["modus"] == render.MODUS_BILD_UND_TIEFE
    assert p["bildeingang_staerke"] == kosmo_szene.BILDEINGANG_VORGABE
    assert erg["messwerte"]["render"]["modus_gerechnet"] == render.MODUS_BILD_UND_TIEFE


def test_der_messweg_gibt_eine_bestellte_staerke_weiter(tmp_path):
    modell = _Modell(tmp_path)
    _rufe(tmp_path, {"prompt": "Haus", "schritte": 8, "bildeingang_staerke": 0.7}, modell)
    assert modell.parameter[0]["bildeingang_staerke"] == 0.7


def test_der_messweg_ohne_beauty_rechnet_nicht(tmp_path):
    modell = _Modell(tmp_path)
    erg = _rufe(tmp_path, {"prompt": "Haus", "schritte": 8, "mit_beauty": False}, modell)
    assert erg["status"] == "fehler"
    assert kosmo_szene.SATZ_MASSTREUE in str(erg["fehler"])
    assert modell.parameter == []


def test_der_messweg_liefert_nicht_wenn_das_grundbild_nicht_ankam(tmp_path):
    erg = _rufe(tmp_path, {"prompt": "Haus", "schritte": 8},
                _Modell(tmp_path, render.MODUS_TXT2IMG))
    assert erg["status"] == "fehler"
    assert erg["messwerte"]["render"]["status"] != "ok"
    assert erg["messwerte"]["render"]["bild"] is None


@pytest.mark.parametrize("params, kennwort", [
    ({"prompt": "Haus", "backbone": "flux1-dev"}, "V0"),
    ({"prompt": "Haus", "schritte": ["eins", "zwei"]}, "V0"),
    ({"prompt": "Haus", "backbone": "sdxl-juggernaut"}, "V0"),
    ({"prompt": "Haus", "bildeingang_staerke": 0.9}, "V0"),
])
def test_v0_wird_vor_blender_geprueft(tmp_path, monkeypatch, params, kennwort):
    """Ein Auftrag, der nicht vom Render rechnen kann, kostet keinen Blender-Lauf."""
    def verboten(*a, **k):
        raise AssertionError("Blender/Geometrie hätte nicht laufen dürfen")

    monkeypatch.setattr(hw, "_geometrie_bereitstellen", verboten)
    erg = hw.fuehre_aus({"auftrag_id": "auf-20261031-998", "art": "render",
                         "geometrie": {"synthetisch": True}, "params": params}, tmp_path,
                        _render_modell=_Modell(tmp_path))
    assert erg["status"] == "fehler"
    assert erg["urteil"]["vorpruefung"] == kennwort, erg


def test_v1_der_lader_ohne_pipeline_wird_vor_blender_gemeldet(tmp_path, monkeypatch):
    def verboten(*a, **k):
        raise AssertionError("Blender/Geometrie hätte nicht laufen dürfen")

    monkeypatch.setattr(hw, "_geometrie_bereitstellen", verboten)
    monkeypatch.setattr(render, "pipeline_lage", lambda name, **k: {
        "rechenbar": False, "satz": "PIPELINE FEHLT: Ersatz"})
    erg = hw.fuehre_aus({"auftrag_id": "auf-20261031-997", "art": "render",
                         "geometrie": {"synthetisch": True}, "params": {"prompt": "Haus"}},
                        tmp_path)
    assert erg["status"] == "fehler"
    assert erg["urteil"]["vorpruefung"] == "V1"
    assert "PIPELINE FEHLT" in erg["fehler"]


def test_v1_wird_mit_eigener_naht_nicht_gefragt(tmp_path, monkeypatch):
    """Mit übergebenem Modell lädt niemand etwas — V1 ist dann keine Frage."""
    monkeypatch.setattr(render, "pipeline_lage", lambda name, **k: {
        "rechenbar": False, "satz": "PIPELINE FEHLT"})
    assert hw._vorpruefung_render({"prompt": "Haus"}, mit_naht=True) is None
