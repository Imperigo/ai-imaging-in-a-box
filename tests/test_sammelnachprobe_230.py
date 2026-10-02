"""Befunde der Sammel-Nachprobe am echten KosmoOrbit v0.1.6 (``auf-20261001-230``).

Je Befund eine Probe, jede zuerst rot gegen den Stand vor der Behebung:

* **F1** — ein aufgehaltener Auftrag verstopfte mit ``--hoechstens 1`` die Schlange.
* **F2** — eine Kamera über dem Dach wird gerechnet und trägt einen Hinweis (E67).
* **F3** — ein Bildmodell, dessen Pipeline-Klasse die installierte diffusers nicht kennt,
  wird früh und mit Satz abgewiesen, ohne Ladeversuch.
* **F4** — ``guidance_applied`` steht, wo es belegt ist.
* **F5** — Innenkamera: Bildauftrag ohne Aussenwörter; ``geom_iou`` einer randlosen
  Soll-Silhouette ist nicht anwendbar statt 1.0.

Regel 3: alles synthetisch, keine Projektdaten.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, kosmo_szene, render

import test_kettenlauf_26august as _kl
import test_runde12_fuehrung as _r12
from conftest import MINI_PNG
from test_abholer import _auftrag, _erfolg
from test_runde12_fuehrung import pil  # noqa: F401 — die Pillow-Attrappe als Fixture


# ======================================================================================
# F1 · Ein aufgehaltener Auftrag verstopft die Schlange nicht
# ======================================================================================

def _szene_mit_fremdem_schluessel() -> dict:
    """Wie B3 der Nachprobe: ein fremder Schlüssel in ``cameras[]`` hält mit Satz auf."""
    return {
        "schema": bruecke.kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [{"name": "Eingang", "position": [10, 2, 1.6], "target": [0, 0, 1.6],
                     "fov": 50, "up_axis": "z", "unbekannt": 1}],
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus", "mode": "none"},
        "vis": {"backbone": "qwen"},
    }


def test_ein_aufgehaltener_auftrag_blockiert_die_schlange_nicht(tmp_path):
    """Der erste Auftrag hat Mängel und bleibt ``queued``; mit ``hoechstens=1`` wird der
    zweite trotzdem im selben Durchgang verarbeitet — und beim nächsten nicht wieder
    vom ersten verdrängt."""
    erster = _auftrag(tmp_path, "vis-1787123001-aaaaaa", szene=_szene_mit_fremdem_schluessel())
    zweiter = _auftrag(tmp_path, "vis-1787123002-bbbbbb")

    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                fremde_freigabe_gilt=True, hoechstens=1)

    taten = {e["job_id"]: e["tat"] for e in bericht["ergebnisse"]}
    assert taten["vis-1787123001-aaaaaa"] == abholer.TAT_LIEGENGELASSEN
    assert taten.get("vis-1787123002-bbbbbb") == abholer.TAT_VERARBEITET, taten
    # Der Aufgehaltene bleibt im Sinn ihres Vertrags: queued, mit Grund am Laufzettel.
    zettel = json.loads((erster / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_QUEUED
    assert "cameras[0].unbekannt" in str(zettel.get(bruecke.FELD_MELDUNG))
    zettel2 = json.loads((zweiter / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel2["status"] == bruecke.STATUS_DONE


def test_hoechstens_zaehlt_laeufe_und_nicht_aufgehaltene(tmp_path):
    """Zwei aufgehaltene vorn, drei rechenbare dahinter, ``hoechstens=2``: genau zwei
    Läufe, der dritte rechenbare wartet auf den nächsten Durchgang."""
    for i in (1, 2):
        _auftrag(tmp_path, f"vis-178712300{i}-aaaaa{i}", szene=_szene_mit_fremdem_schluessel())
    for i in (3, 4, 5):
        _auftrag(tmp_path, f"vis-178712300{i}-bbbbb{i}")
    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                fremde_freigabe_gilt=True, hoechstens=2)
    assert (bericht["verarbeitet"], bericht["liegengelassen"]) == (2, 2)
    assert bericht["gesehen"] == 4
    naechster = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                  fremde_freigabe_gilt=True, hoechstens=2)
    assert naechster["verarbeitet"] == 1


def test_hoechstens_null_rechnet_weiterhin_nichts(tmp_path):
    _auftrag(tmp_path)
    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                fremde_freigabe_gilt=True, hoechstens=0)
    assert bericht["gesehen"] == 0 and bericht["verarbeitet"] == 0


# ======================================================================================
# F2 · Über dem Dach wird gerechnet, mit Hinweis (Owner-Entscheid 67)
# ======================================================================================

#: Die Lage aus der Nachprobe: KosmoOrbits Auto-Kamera «Übersicht» 16,3 m hoch, das
#: Gebaeude 6 m. Dazu eine Augenhoehe-Kamera «Eingang».
KOSMO_AUTO_KAMERAS = [
    {"name": "Eingang", "position": [0.0, -20.0, 1.6], "target": [0.0, 0.0, 3.0],
     "fov": 50, "up_axis": "z"},
    {"name": "Übersicht", "position": [0.0, -25.0, 16.3], "target": [0.0, 0.0, 3.0],
     "fov": 50, "up_axis": "z"},
]


def _kosmo_ordner(tmp_path, *, kameras=None, prompt="house, plaster, clear sky",
                  interior=None, backbone=None):
    ordner = tmp_path / "vis-1790872543-598864"
    ordner.mkdir(parents=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": ordner.name, "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "deadbeef"}), encoding="utf-8")
    szene = {"geometry": {"path": str(ordner / "model.glb"), "format": "glb"},
             "cameras": kameras or KOSMO_AUTO_KAMERAS,
             "render": {"samples": 8, "faithful": 0.8},
             "style": {"prompt": prompt},
             "vis": {"skip": False, **({"backbone": backbone} if backbone else {})}}
    if interior is not None:
        szene["interior"] = interior
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    (ordner / bruecke.DATEI_MODELL).write_bytes(_kl._minimale_glb())
    return ordner


def _kette_gebaeude_6m(*, soll=None, qa=None):
    """Multipass- und Render-Attrappen; das Gebaeude ist 6 m hoch, Gelaende bei 0."""
    protokoll = {"multipass": [], "render": []}
    karten = iter([[[float(i)]] for i in range(1, 30)])

    def multipass(glb, aus, **kw):
        protokoll["multipass"].append(kw)
        Path(aus).mkdir(parents=True, exist_ok=True)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        kamera = {"weg": "vorgegeben", "auge": kw["auge"], "blick_auf": kw["blick_auf"],
                  "abstand_m": 20.0, "brennweite_mm": 35.0, "seitenverhaeltnis": 1.6,
                  "gelaende_z": 0.0, "gelaende_bezug": "gesetzt", "gebaeudehoehe_m": 6.0}
        return {"depth_png": str(tiefe), "kamera": kamera,
                "bbox": [[-6.0, -4.0, 0.0], [6.0, 4.0, 6.5]],
                "bbox_bauwerk": [[-5.0, -3.0, 0.0], [5.0, 3.0, 6.0]],
                "sonne": {"weg": "vorgabe", "konvention": "von_norden"}}

    def rendere(a, **kw):
        protokoll["render"].append(a)
        Path(a.ausgabe_png).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ausgabe_png).write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": a.ausgabe_png, "hinweise": ()}

    return protokoll, {
        "_multipass": multipass, "_rendere": rendere,
        "_qa": qa or (lambda *a, **k: {"score": 0.81, "bestanden": True, "status": "ok"}),
        "_soll": soll or (lambda *a, **k: (next(karten), 1, 1)),
    }


def _vertrag(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def test_ein_auto_auftrag_mit_uebersicht_ueber_dem_dach_wird_gerechnet(tmp_path):
    """**E67 am Produktweg.** Übersicht 16,3 m bei 6 m Gebaeude: gerechnet, der Hinweis
    steht in ``qa.verdict.hinweise`` (nicht im Grund), und der Auftrag ist geliefert."""
    ordner = _kosmo_ordner(tmp_path)
    protokoll, attrappen = _kette_gebaeude_6m()
    antwort = _kl._lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    vertrag = _vertrag(ordner)
    assert len(protokoll["render"]) == 2, "beide Kameras gerechnet"
    assert vertrag["lieferstatus"] != kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    je = {e["kamera"]: e for e in vertrag["qa_je_kamera"]}
    assert je["Übersicht"]["lieferstatus"] == kosmo_szene.LIEFERSTATUS_GELIEFERT
    satz = ("AUFSICHT: Die Kamera Übersicht steht über dem Dach — gerechnet, aber nicht "
            "nach den Regeln für Architekturaufnahmen in Augenhöhe beurteilt. "
            "Die Prüfung gegen die Geometrie gilt für sie weiter.")
    assert satz in vertrag["qa"]["verdict"]["hinweise"]
    assert "AUFSICHT" not in vertrag["qa"]["verdict"]["reason"]
    assert "ueber dem Dach" not in vertrag["qa"]["verdict"]["reason"]
    # Nur die Aufsicht bekommt den Satz — die Augenhoehe-Kamera nicht.
    assert not any("Eingang steht über dem Dach" in h
                   for h in vertrag["qa"]["verdict"]["hinweise"])


def test_eine_augenhoehe_kamera_wird_wie_bisher_beurteilt(tmp_path):
    """Die Gegenprobe: Eingang (1,6 m) bekommt das volle Regelwerk und keinen Vermerk."""
    ordner = _kosmo_ordner(tmp_path, kameras=KOSMO_AUTO_KAMERAS[:1])
    _protokoll, attrappen = _kette_gebaeude_6m()
    _kl._lauf(tmp_path, ordner, attrappen)

    kamera = abholer.lies_befund(ordner)["kameras"][0]
    assert kamera["komposition"].get("aufsicht") is None
    assert kamera["komposition"]["beurteilt"] is True
    assert kamera["komposition"]["abbruch"] is False
    assert kamera.get(kosmo_szene.URTEIL_AUFSICHT) is None
    assert "hinweise" not in _vertrag(ordner)["qa"]["verdict"]


def test_der_kurzbefund_nennt_die_aufsicht_als_nicht_angewandt():
    zeilen = abholer._kompositionszeilen([
        {"kamera": "Übersicht", "komposition": {"beurteilt": False, "aufsicht": {"x": 1}}},
        {"kamera": "kaputt", "komposition": {"beurteilt": False, "aufsicht": None}}])
    assert zeilen[0].startswith("Komposition nicht angewandt (Aufsicht")
    assert "Übersicht" in zeilen[0]
    assert zeilen[1] == "Komposition NICHT beurteilbar: kaputt"


# ======================================================================================
# F3 · Ein Bildmodell, das diese diffusers nicht kennt, wird früh abgewiesen
# ======================================================================================

def _ersatz_diffusers(*namen, fassung="0.39.0"):
    """Ein diffusers wie in ``.venv-render``: bekannte Klassen als Namen, sonst nichts."""
    modul = types.ModuleType("diffusers")
    modul.__version__ = fassung
    for name in namen:
        setattr(modul, name, type(name, (), {}))
    return modul


DIFFUSERS_0390 = ("DiffusionPipeline", "ZImageControlNetModel", "ZImageControlNetPipeline",
                  "QwenImageEditPlusPipeline")


def test_die_pipeline_lage_nennt_die_fehlende_klasse_mit_fassung():
    lage = render.pipeline_lage("qwen-image-2.1",
                                diffusers_modul=_ersatz_diffusers(*DIFFUSERS_0390))
    assert lage["rechenbar"] is False
    assert lage["satz"] == ("In der Render-Umgebung fehlt QwenImage21Pipeline (diffusers "
                            "0.39.0) — dieses Bildmodell ist hier nicht rechenbar.")
    # Das Vorgabemodell bleibt in derselben Umgebung rechenbar.
    assert render.pipeline_lage(
        "z-image-turbo", diffusers_modul=_ersatz_diffusers(*DIFFUSERS_0390))["rechenbar"]


def test_eine_diffusers_mit_der_klasse_ist_rechenbar():
    modul = _ersatz_diffusers(*DIFFUSERS_0390, "QwenImage21Pipeline", fassung="0.40.0.dev0")
    assert render.pipeline_lage("qwen-image-2.1", diffusers_modul=modul)["rechenbar"] is True


def test_ohne_diffusers_ist_die_frage_ungeprueft_und_haelt_nichts_an(monkeypatch):
    monkeypatch.setattr(render, "_diffusers_ohne_gewichte", lambda: None)
    lage = render.pipeline_lage("qwen-image-2.1")
    assert lage["rechenbar"] is None and lage["satz"].startswith("NICHT GEPRUEFT")


def test_qwen21_wird_vor_blender_und_ohne_ladeversuch_abgewiesen(tmp_path):
    """**Der Fall aus B2 der Nachprobe.** qwen-image-2.1 über KosmoOrbit bestellt, die
    Umgebung hat diffusers 0.39.0: kein Blender-Lauf, kein Bildmodell, sondern ein
    Ergebnis mit ``lieferstatus: fehlgeschlagen`` und dem Satz je Kamera."""
    ordner = _kosmo_ordner(tmp_path, backbone="qwen-image-2.1")
    protokoll, attrappen = _kette_gebaeude_6m()
    modul = _ersatz_diffusers(*DIFFUSERS_0390)
    antwort = _kl._lauf(tmp_path, ordner, attrappen,
                        _pipeline_lage=lambda n: render.pipeline_lage(
                            n, diffusers_modul=modul))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"] == [] and protokoll["render"] == [], (
        "weder Blender noch Bildmodell")

    vertrag = _vertrag(ordner)
    satz = ("In der Render-Umgebung fehlt QwenImage21Pipeline (diffusers 0.39.0) — dieses "
            "Bildmodell ist hier nicht rechenbar.")
    assert vertrag["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    assert satz in vertrag["lieferstatus_grund"]
    for e in vertrag["qa_je_kamera"]:
        assert e["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
        assert (e["bilder_soll"], e["bilder_ist"]) == (1, 0)
        assert e["lieferstatus_grund"] == f"NICHT GERECHNET (Bildmodell), {e['kamera']}: {satz}"
    assert satz in vertrag["qa"]["verdict"]["reason"]
    assert vertrag["images"] == []


def test_lade_modell_weist_vor_from_pretrained_ab(tmp_path, monkeypatch):
    """Derselbe Satz am Ladeweg selbst — für jeden Aufrufer, nicht nur den Abholer."""
    gerufen = []
    modul = _ersatz_diffusers(*DIFFUSERS_0390)

    class _Pipeline:
        @classmethod
        def from_pretrained(cls, *a, **k):
            gerufen.append(a)
            raise AssertionError("darf nicht laden")

    modul.DiffusionPipeline = _Pipeline
    monkeypatch.setitem(sys.modules, "diffusers", modul)
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(bfloat16="bf16"))
    wurzel = tmp_path / "qwen-image-2.1"
    for teil in ("transformer", "vae", "text_encoder", "processor"):
        (wurzel / teil).mkdir(parents=True)
    (wurzel / "model_index.json").write_text("{}")
    with pytest.raises(render.RenderError, match="fehlt QwenImage21Pipeline"):
        render.lade_modell("qwen-image-2.1", modell_wurzel=wurzel)
    assert gerufen == []


def test_ohne_registereintrag_gilt_die_klasse_aus_der_model_index(tmp_path):
    """Die Rückfallquelle: ``_class_name`` der Gewichte, wie ``from_pretrained`` sie liest."""
    (tmp_path / "model_index.json").write_text(json.dumps({"_class_name": "GibtsNicht"}))
    eintrag = kosmo_szene._backbone.BACKBONES["qwen-image-2.1"]
    klassen, quelle = render._pipeline_klassen(
        dataclasses.replace(eintrag, pipeline_klasse=None), tmp_path)
    assert (klassen, quelle) == (("GibtsNicht",), "model_index.json")


# ======================================================================================
# F4 · guidance_applied, wo es belegt ist
# ======================================================================================

def _engine_felder_nach_lauf(tmp_path, name, pipeline):
    tmp_path.mkdir(parents=True, exist_ok=True)
    _r12._dateien(tmp_path)
    ergebnis = render.rendere(_r12._auftrag_fuer(tmp_path, name), _lader=_r12._lader(pipeline))
    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    return ergebnis, kosmo_szene.engine_felder(abholer._engine_aus(ergebnis))


def test_die_vorgabe_z_image_meldet_guidance_applied_false(tmp_path, pil):
    """**C35.** z-image-turbo rechnet mit ``guidance_scale`` 0.0 — ohne Führung, belegt."""
    ergebnis, felder = _engine_felder_nach_lauf(tmp_path, "z-image-turbo", _r12.NimmtAlles())
    assert ergebnis["parameter"]["fuehrung_angewandt"] is False
    assert felder["guidance_applied"] is False
    assert felder["engine_used"] == "z-image-turbo"


def test_qwen_edit_mit_true_cfg_meldet_guidance_applied_true(tmp_path, pil):
    _ergebnis, felder = _engine_felder_nach_lauf(tmp_path, _r12.QWEN_EDIT, _r12.QwenEditPlus())
    assert felder["guidance_applied"] is True


def test_unbelegt_bleibt_das_feld_weg_und_nie_null(tmp_path, pil):
    """Nahm die Pipeline den Regler nicht, oder setzt das Register keine Führung
    (qwen-image-2.1: Vorgabe der Pipeline), ist es nicht belegt — das Feld fehlt."""
    _e, felder = _engine_felder_nach_lauf(tmp_path, _r12.QWEN_EDIT, _r12.OhneTrueCfg())
    assert "guidance_applied" not in felder
    _e, felder = _engine_felder_nach_lauf(tmp_path / "q21", "qwen-image-2.1",
                                          _r12.NimmtAlles())
    assert "guidance_applied" not in felder


def test_die_regel_an_der_funktion():
    eintrag = kosmo_szene._backbone.hole("z-image-turbo")
    leer = {"fuehrung_regler": None, "fuehrung_regler_wert": None}
    assert render.fuehrung_angewandt(eintrag, leer, {"guidance_scale": 0.0}) is False
    assert render.fuehrung_angewandt(eintrag, leer, {"guidance_scale": 1.0}) is False
    assert render.fuehrung_angewandt(eintrag, leer, {"guidance_scale": 5.0}) is None
    assert render.fuehrung_angewandt(eintrag, leer, {"guidance_scale": None}) is None
    assert render.fuehrung_angewandt(eintrag, leer, {}) is None
    regler = {"fuehrung_regler": "true_cfg_scale", "fuehrung_regler_wert": 4.0}
    assert render.fuehrung_angewandt(
        eintrag, regler, {"true_cfg_scale": 4.0, "negative_prompt": " "}) is True
    assert render.fuehrung_angewandt(
        eintrag, regler, {"true_cfg_scale": 4.0, "negative_prompt": None}) is False
    assert render.fuehrung_angewandt(eintrag, regler, {"negative_prompt": " "}) is None


# ======================================================================================
# F5 · Innenkamera: Bildauftrag ohne Aussenwörter; geom_iou einer randlosen Silhouette
# ======================================================================================

INF = float("inf")

#: Wie C19 der Nachprobe: eine Aussen-, eine Innenkamera, ``interior`` bestellt, ein
#: Prompt für beide mit «klarer Himmel».
KAMERAS_INNEN_AUSSEN = [
    {"name": "Eingang", "position": [0.0, -20.0, 1.6], "target": [0.0, 0.0, 3.0],
     "fov": 50, "up_axis": "z"},
    {"name": "Innenraum", "position": [0.0, 0.0, 1.6], "target": [2.0, 1.0, 1.6],
     "fov": 60, "up_axis": "z"},
]
PROMPT_C19 = "Wohnhaus, heller Putz, Holzfenster, Tageslicht, klarer Himmel"


def _ist_innen(bericht) -> bool:
    return abs(float(bericht["kamera"]["auge"][1])) < 1.0


def _soll_innen_aussen(bericht):
    """Innen: Geometrie in jedem Bildpunkt. Aussen: Himmel (inf) daneben."""
    if _ist_innen(bericht):
        return [[1.0, 2.0], [3.0, 4.0]], 2, 2
    return [[5.0, INF], [6.0, INF]], 2, 2


def _qa_innen_aussen(png, soll, **_kw):
    """Die Innenkamera meldet, was der echte Lauf meldete: geom_iou 1.0 über eine
    randlose Soll-Silhouette — und sie ist die schlechtere Kamera."""
    if any(w == INF for zeile in soll for w in zeile):
        return {"score": 0.81, "bestanden": True, "status": "ok", "geom_iou": 0.6,
                "anteil_soll": 0.5, "spearman": 0.9}
    return {"score": 0.7, "bestanden": True, "status": "ok", "geom_iou": 1.0,
            "anteil_soll": 1.0, "spearman": 0.49}


def _lauf_innen_aussen(tmp_path, *, interior={"rooms": "auto"}):
    ordner = _kosmo_ordner(tmp_path, kameras=KAMERAS_INNEN_AUSSEN, prompt=PROMPT_C19,
                           interior=interior)
    protokoll, attrappen = _kette_gebaeude_6m(soll=_soll_innen_aussen, qa=_qa_innen_aussen)
    antwort = _kl._lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    prompts = {Path(a.ausgabe_png).parent.name: a.prompt for a in protokoll["render"]}
    return ordner, prompts


def test_die_innenkamera_bekommt_einen_bildauftrag_ohne_himmel(tmp_path):
    ordner, prompts = _lauf_innen_aussen(tmp_path)

    innen, aussen = prompts["Innenraum"], prompts["Eingang"]
    assert innen.startswith(abholer.INNEN_VORSATZ + ", ")
    assert "sky" not in innen.lower()
    assert "sky" in aussen.lower(), "die Aussenkamera behaelt den bestellten Text"
    assert not aussen.startswith(abholer.INNEN_VORSATZ)

    kamera = {k["kamera"]: k for k in abholer.lies_befund(ordner)["kameras"]}
    vermerk = kamera["Innenraum"][kosmo_szene.URTEIL_BILDAUFTRAG]
    assert vermerk["gerechnet"] == innen and vermerk["entfernt"] == ["clear sky"]
    assert kamera["Eingang"][kosmo_szene.URTEIL_BILDAUFTRAG] is None
    hinweise = _vertrag(ordner)["qa"]["verdict"]["hinweise"]
    assert any(h.startswith("INNENKAMERA Innenraum: Bildauftrag angepasst") for h in hinweise)


def test_ohne_bestelltes_interior_wird_nichts_umgeschrieben(tmp_path):
    """Eine randlose Karte allein macht noch keine Innenkamera — bestellt muss es sein."""
    _ordner, prompts = _lauf_innen_aussen(tmp_path, interior=None)
    assert not prompts["Innenraum"].startswith(abholer.INNEN_VORSATZ)
    assert "sky" in prompts["Innenraum"].lower()


def test_geom_iou_einer_randlosen_silhouette_ist_nicht_anwendbar(tmp_path):
    """**geom_iou 1.0 bei der Innenkamera** (Nachprobe): leer statt 1.0, im Tor
    ``not_applicable``, und der Grund steht in ``verdict.reason``."""
    ordner, _prompts = _lauf_innen_aussen(tmp_path)
    vertrag = _vertrag(ordner)

    je = {e["kamera"]: e for e in vertrag["qa_je_kamera"]}
    assert je["Innenraum"]["geometry"]["geom_iou"] is None
    assert je["Eingang"]["geometry"]["geom_iou"] == 0.6, "die Aussenkamera bleibt gemessen"
    assert vertrag["qa"]["geometry"]["geom_iou"] is None, "der qa-Block ist die Innenkamera"
    tore = vertrag["geometry_gates"]
    assert tore["camera"] == "Innenraum"
    assert tore["geom_iou_status"] == "not_applicable"
    assert "geom_iou" not in tore
    assert "geom_iou_nicht_anwendbar" in tore["fail_reasons"]
    assert "GEOM_IOU NICHT ANWENDBAR, Innenraum:" in vertrag["qa"]["verdict"]["reason"]
    assert "Eingang" not in vertrag["qa"]["verdict"]["reason"].split(
        "GEOM_IOU NICHT ANWENDBAR")[1].split(":")[0]


def test_die_randlos_regel_an_der_funktion():
    assert kosmo_szene.soll_silhouette_randlos({"anteil_soll": 1.0}) is True
    assert kosmo_szene.soll_silhouette_randlos({"anteil_soll": 0.999}) is False
    assert kosmo_szene.soll_silhouette_randlos({}) is False
    assert kosmo_szene.soll_silhouette_randlos({"anteil_soll": True}) is False


# --------------------------------------------------------------------------------------
# Nachgang auf-20261001-235: A6 griff am echten Lauf nicht
# --------------------------------------------------------------------------------------
#
# Die Proben oben setzen ``anteil_soll`` von Hand ins Kameraurteil. Am Heim-PC kam das Feld
# nie an: ``tiefenschaetzer.qa_gegen_soll`` reichte es aus ``geometrie_score`` nicht
# weiter, und die Innenkamera meldete weiter geom_iou 1.0 «measured». Diese Probe geht den
# echten Weg — Urteil aus dem Schätzer, dann die Regel — und setzt nichts von Hand.

def _qa_echt(tmp_path, soll, ist):
    from aiimaging import tiefenschaetzer as ts

    bild = tmp_path / "innen.png"
    bild.write_bytes(b"\x89PNG\r\n\x1a\n")
    return ts.qa_gegen_soll(bild, soll, modell=lambda _p: list(ist), breite=4, hoehe=4,
                            hintergrund_strategie=ts.HG_KEINE)


def test_das_kameraurteil_traegt_anteil_soll_bis_zur_randlos_regel(tmp_path):
    soll = [float(1 + i % 5) for i in range(16)]           # jeder Bildpunkt Geometrie
    urteil = _qa_echt(tmp_path, soll, [1.0 / x for x in soll])

    assert urteil["anteil_soll"] == 1.0
    assert kosmo_szene.soll_silhouette_randlos(urteil) is True


def test_gegenprobe_eine_aussenkamera_bleibt_nicht_randlos(tmp_path):
    soll = [10.0, 10.0, 1e10, 1e10] * 4                     # halb Himmel
    urteil = _qa_echt(tmp_path, soll, [1.0, 1.0, 0.01, 0.01] * 4)

    assert urteil["anteil_soll"] == 0.5
    assert kosmo_szene.soll_silhouette_randlos(urteil) is False


def test_ein_urteil_ohne_messung_fuehrt_das_feld_leer():
    from aiimaging import tiefenschaetzer as ts

    leer = ts._qa_ohne_messung(ts.STATUS_FEHLER, {}, error="x", dauer_s=0.0)
    assert "anteil_soll" in leer and leer["anteil_soll"] is None


# Die kleineren Befunde aus 235 ---------------------------------------------------------

def test_eine_wendung_mit_geschuetztem_leerzeichen_wird_ganz_uebersetzt():
    """«klarer\xa0Himmel» (so schickte es KosmoOrbit) ergab «klarer sky»."""
    from aiimaging import sprache

    for zwischen in (" ", "\xa0", "  ", "\u202f"):
        aus = sprache.glossar_uebersetzung(f"Wohnhaus, klarer{zwischen}Himmel")
        assert aus["text"] == "residential building, clear sky", (repr(zwischen), aus)


def test_der_innenkamera_satz_ist_ein_satz_fuer_menschen():
    satz = kosmo_szene.bildauftrag_satz({
        "kamera": "Innenraum", "vorsatz": abholer.INNEN_VORSATZ,
        "entfernt": ("klarer\xa0sky",), "grund": "die Kamera steht innen"})
    assert "\\xa0" not in satz and "\xa0" not in satz
    assert "«klarer sky»" in satz
    assert f"«{abholer.INNEN_VORSATZ}»" in satz


def test_die_mitgesandte_innenansicht_widerspricht_der_innenkamera_nicht():
    satz = kosmo_szene.innenansicht_satz(
        {"standpunkt": kosmo_szene.INNEN_STANDPUNKT_MITGESANDT, "bestellt": "auto"},
        gerendert=True)
    assert satz.startswith("INNENANSICHT BESTELLT")
    assert "prueft diese Seite nicht" not in satz
