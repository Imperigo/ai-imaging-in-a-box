"""Befunde aus auf-20261021-298 (Licht ins KI-Bild, Entscheid 117) — was danach gebaut ist.

* **B3 · Speicher:** Der Lauf mit Bildeingang braucht +3880 MiB (27 436 → 31 316 MiB). Die
  Ladeentscheidung rechnet mit Bildeingang an dieser Messung, weist bei einem fremden Modell auf
  der Karte oder zu wenig Platz ab und weicht nie auf die Auslagerung aus.
* **B1 · Sichtbar am Ergebnis:** ``verdict.hinweise`` und ``angewandt`` sagen, dass ein
  Messschalter gerechnet hat — additiv, kein Vertragsfeld geändert.
* **B2 · Schrittzahl:** Der Satz rechnet beim Bildeingang mit der Stärke, nicht mit ``denoise``.
* **Farbabgleich:** ``geom_iou_gleich`` mit begründeter Toleranz und der Abweichung als Zahl.
* Der Messauftrag auf-20261021-300.

Attrappen statt Karte und Gewichte (Regel 2), Bilder synthetisch (Regel 3).
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, auftrag, backbone, bildschreiben, bruecke, kosmo_szene, render

WURZEL = Path(__file__).resolve().parents[1]

#: Gemessen in auf-20261021-298: Karte 32 607 MiB, vor dem Lauf 1241 belegt.
FREI_LEER = 32607 - 1241


# ====================================================================== B3 · Speicher

def test_die_messung_steht_am_vorgabemodell():
    eintrag = backbone.hole("z-image-turbo")
    # Seit auf-20261021-309 (E2n, no_grad): 27116 gemessen + 1000 Rand fuer mehrere Kameras.
    assert eintrag.vram_bildeingang_spitze_mib == 28116
    assert eintrag.vram_bildeingang_grundlast_mib == 1241
    assert "auf-20261021-309" in eintrag.vram_bildeingang_beleg
    bedarf = render.bildeingang_bedarf("z-image-turbo")
    assert bedarf["lauf_mib"] == 26875
    assert bedarf["verlangt_frei_mib"] == 26875 + render.BILDEINGANG_RESERVE_MIB == 27387
    # Bis 309 lag die alte Rechnung (vram_gb x Zuschlag) 1,8 GB darunter — das war der Befund
    # von 298. Seit no_grad liegt der gemessene Bedarf mit Rand unter ihr.
    alt = int(eintrag.vram_gb * 1024 * render.MESSUNG_ZUSCHLAG)
    assert alt == 28272 and bedarf["verlangt_frei_mib"] < alt


def test_ohne_messung_kein_bedarf_und_kein_riegel():
    assert render.bildeingang_bedarf("qwen-image-edit-2511") is None
    lage = render.pruefe_bildeingang_karte("qwen-image-edit-2511", frei_mib=100)
    assert lage["reicht"] is None and "nicht geprueft" in lage["satz"]


@pytest.mark.parametrize("kw", [
    {"vram_bildeingang_spitze_mib": 31316},                                   # eine Zahl allein
    {"vram_bildeingang_spitze_mib": 31316, "vram_bildeingang_grundlast_mib": 1241,
     "vram_bildeingang_beleg": "ohne Kennung"},
    {"vram_bildeingang_spitze_mib": 1000, "vram_bildeingang_grundlast_mib": 1241,
     "vram_bildeingang_beleg": "auf-20261021-298"},                            # Spitze < Grundlast
])
def test_eine_halbe_messung_kommt_nicht_ins_register(kw):
    eintrag = dataclasses.replace(backbone.hole("z-image-turbo"), name="probe-298",
                                  vram_bildeingang_spitze_mib=None,
                                  vram_bildeingang_grundlast_mib=None,
                                  vram_bildeingang_beleg=None)
    with pytest.raises(backbone.BackboneError, match="vram_bildeingang"):
        backbone._eintrag(dataclasses.replace(eintrag, **kw))
    assert "probe-298" not in backbone.BACKBONES


def test_leere_karte_reicht():
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=FREI_LEER, fremde_modelle=[])
    assert lage["reicht"] is True, lage["satz"]


def test_ein_fremdes_modell_wird_abgewiesen_und_genannt():
    """Die Nacht von 298: ein 17-GB-Modell von Ollama lag auf der Karte."""
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=FREI_LEER - 17000,
                                           fremde_modelle=["kosmo-qwen3.6:35b-a3b"])
    assert lage["reicht"] is False
    assert lage["satz"].startswith("ABGEWIESEN")
    # Seit Entscheid 127 (22.10.2026) nicht mehr «nie entladen»: freigegeben wird vor dem Auftrag.
    assert "kosmo-qwen3.6:35b-a3b" in lage["satz"] and "Entscheid 127" in lage["satz"]
    # Auch wenn der Speicher reichte: ein fremdes Modell genuegt.
    assert render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=FREI_LEER,
                                           fremde_modelle=["gpt-oss:20b"])["reicht"] is False


def test_zu_wenig_platz_wird_abgewiesen_auch_wo_die_alte_rechnung_lud():
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=26000, fremde_modelle=[])
    assert lage["reicht"] is False
    assert "Auslagerung" in lage["satz"] and "27387" in lage["satz"]


def test_eigener_speicher_zaehlt_mit():
    """Haelt dieser Prozess das Bildmodell schon, ist der belegte Speicher unserer."""
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=6000, eigen_mib=25000,
                                           fremde_modelle=None)
    assert lage["reicht"] is True


def test_unbekannter_speicher_sperrt_nicht():
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=None, fremde_modelle=[])
    assert lage["reicht"] is None


def _ersatz_torch(frei_mib):
    cuda = types.SimpleNamespace(is_available=lambda: True,
                                 mem_get_info=lambda: (frei_mib * 2**20, 32607 * 2**20))
    return types.SimpleNamespace(bfloat16="bf16", cuda=cuda)


def _wurzel(tmp_path):
    wurzel = tmp_path / "z-image-turbo"
    for teil in ("transformer", "vae", "text_encoder", "tokenizer"):
        (wurzel / teil).mkdir(parents=True)
    (wurzel / "model_index.json").write_text("{}")
    return wurzel


def test_lade_modell_weist_mit_bildeingang_vor_den_gewichten_ab(tmp_path, monkeypatch):
    gerufen = []
    modul = types.ModuleType("diffusers")
    modul.__version__ = "0.41.0.dev0"
    for name in ("ZImageControlNetModel", "ZImageControlNetPipeline"):
        setattr(modul, name, type(name, (), {}))

    class _Pipeline:
        @classmethod
        def from_pretrained(cls, *a, **k):
            gerufen.append(a)
            raise AssertionError("darf nicht laden")

    modul.DiffusionPipeline = _Pipeline
    monkeypatch.setitem(sys.modules, "diffusers", modul)
    monkeypatch.setitem(sys.modules, "torch", _ersatz_torch(26000))
    monkeypatch.setattr(render, "_lade_mit_controlnet",
                        lambda *a, **k: gerufen.append("controlnet") or (_ for _ in ()).throw(
                            AssertionError("darf nicht laden")))
    with pytest.raises(render.RenderError, match="ABGEWIESEN: Bildeingang"):
        render.lade_modell("z-image-turbo", modell_wurzel=_wurzel(tmp_path), bildeingang=True)
    assert gerufen == []


def _render_auftrag(tmp_path, **kw):
    tiefe = bildschreiben.schreibe_graustufen_png(tmp_path / "t.png", [0.5] * 4, 2, 2)
    beauty = bildschreiben.schreibe_farb_png(tmp_path / "b.png", [(1, 2, 3)] * 4, 2, 2)
    return render.RenderAuftrag(depth_png=str(tiefe), beauty_png=str(beauty), prompt="a house",
                                ausgabe_png=str(tmp_path / "aus.png"),
                                modell_wurzel=str(tmp_path), **kw)


@pytest.mark.parametrize("staerke, erwartet", [(None, {}), (0.55, {"bildeingang": True})])
def test_rendere_sagt_dem_lader_ob_mit_bildeingang(tmp_path, monkeypatch, staerke, erwartet):
    gesehen = {}

    def lader(name, wurzel, **kw):
        gesehen.update(kw)

        def modell(parameter):
            Path(parameter["ausgabe_png"]).write_bytes(Path(parameter["depth_png"]).read_bytes())
            return parameter["ausgabe_png"]
        return modell

    monkeypatch.setattr(render, "lade_modell", lader)
    erg = render.rendere(_render_auftrag(tmp_path, bildeingang_staerke=staerke))
    assert erg["status"] == "ok", erg
    assert gesehen == erwartet


def test_einmal_geladen_reicht_den_bildeingang_an_den_lader():
    pfad = WURZEL / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_b298", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    aufrufe = []

    def lader(name, wurzel, **kw):
        aufrufe.append(kw)
        return lambda parameter: "bild.png"

    mit = modul.EinmalGeladen(lader, "backbone", "modell_wurzel")
    mit({"backbone": "z-image-turbo", "bildeingang_staerke": 0.8})
    ohne = modul.EinmalGeladen(lader, "backbone", "modell_wurzel")
    ohne({"backbone": "z-image-turbo"})
    schaetzer = modul.EinmalGeladen(lader, "schaetzer")
    schaetzer({"schaetzer": "s", "bildeingang_staerke": 0.8})
    assert aufrufe == [{"bildeingang": True}, {}, {}]


# ====================================================================== B3 im Abholer

def _ordner(tmp_path, **vis):
    from test_kettenlauf_26august import _auftragsordner
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def _verarbeiter(tmp_path, protokoll_modus=True):
    from test_kettenlauf_26august import _kette
    protokoll, attrappen = _kette(tmp_path / "k")
    alt = attrappen["_rendere"]

    def rendere(a, **kw):
        erg = alt(a, **kw)
        if a.bildeingang_staerke is not None and protokoll_modus:
            erg = dict(erg, backbone="z-image-turbo",
                       parameter={"schritte": 20, "bildeingang_weg": "eigener_start"},
                       modus_bestellt=render.MODUS_BILD_UND_TIEFE,
                       modus_gerechnet=render.MODUS_BILD_UND_TIEFE, modus_abweichung=False,
                       schritte_gerechnet=render.bildeingang_schritte(20, a.bildeingang_staerke),
                       hinweise=("BILD UND TIEFE (Messschalter, Entscheid 117): eigener Start",
                                 "ein anderer Satz"))
        return erg

    attrappen = dict(attrappen, _rendere=rendere)
    return protokoll, abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                          **attrappen)


def test_fremdes_modell_mit_bildeingang_endet_mit_satz_und_rechnet_nichts(tmp_path):
    ordner = _ordner(tmp_path, bildeingang=0.8)
    protokoll, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        bildeingang_karte=lambda: {"frei_mib": 14000, "eigen_mib": 0,
                                   "fremde_modelle": ["kosmo-qwen3.6:35b-a3b"]})
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert antwort["grund"].startswith("ABGEWIESEN: Bildeingang")
    assert protokoll["render"] == [] and protokoll["multipass"] == []
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    assert "kosmo-qwen3.6:35b-a3b" in ergebnis["lieferstatus_grund"]


def test_ohne_schalter_fragt_der_abholer_die_karte_nicht(tmp_path):
    ordner = _ordner(tmp_path)
    _p, verarbeite = _verarbeiter(tmp_path)

    def karte():
        raise AssertionError("ohne vis.bildeingang nicht gefragt")

    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                                 bildeingang_karte=karte)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]


# ====================================================================== B1 · am Ergebnis

def _gerechnet(tmp_path, **vis):
    ordner = _ordner(tmp_path, **vis)
    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        bildeingang_karte=lambda: {"frei_mib": FREI_LEER, "eigen_mib": 0, "fremde_modelle": []})
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8")), antwort


def test_der_bildeingang_steht_am_ergebnis_der_bruecke(tmp_path):
    ergebnis, antwort = _gerechnet(tmp_path, bildeingang=0.8)
    saetze = [h for h in ergebnis["qa"]["verdict"].get("hinweise", [])
              if h.startswith(kosmo_szene.SATZ_BILDEINGANG)]
    assert saetze, ergebnis["qa"]["verdict"]
    assert all("'bild_und_tiefe'" in h and "16 von 20 Schritten" in h for h in saetze)
    bi = ergebnis["angewandt"]["bildeingang"]
    assert bi["staerke"] == 0.8 and bi["modus"] == render.MODUS_BILD_UND_TIEFE
    assert bi["weg"] == "eigener_start" and bi["kameras"]
    assert "Bildeingang:" in (antwort.get("karte") or "")
    # Am Kameraurteil im Befund: der Vermerk mit den Saetzen des Bildmodells.
    kameras = [k for k in abholer.lies_befund(Path(antwort["verzeichnis"]))["kameras"]
               if not k.get("doppelt_von")]
    vermerk = kameras[0][abholer.URTEIL_BILDEINGANG]
    assert vermerk["hinweise"] == ["BILD UND TIEFE (Messschalter, Entscheid 117): eigener Start"]


def test_ohne_schalter_nichts_neues_am_ergebnis(tmp_path):
    # Seit Entscheid 138 ist der Bildeingang Vorgabe; seit der Masstreue (A0051) gibt es kein
    # «aus» mehr — «ohne Schalter» heisst darum mit der Vorgabe, als solche gekennzeichnet.
    ergebnis, _a = _gerechnet(tmp_path)
    text = json.dumps(ergebnis)
    assert ergebnis["angewandt"]["messschalter"]["bildeingang"] == {
        "wert": kosmo_szene.BILDEINGANG_VORGABE, "herkunft": "vorgabe"}
    assert "farbabgleich" not in text


def test_die_vertragsfassung_behaelt_die_auskunft():
    ergebnis = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"kamera": "sSE", abholer.URTEIL_BILDEINGANG: {
            "staerke": 0.9, "weg": "eigener_start", "modus_bestellt": "bild_und_tiefe",
            "modus_gerechnet": "txt2img", "modus_abweichung": True}},
        angewandt={"bildeingang": {"staerke": 0.9}})
    aus = kosmo_szene.nur_vertragsfelder(ergebnis)
    assert aus["angewandt"]["bildeingang"]["staerke"] == 0.9
    satz = [h for h in aus["qa"]["verdict"]["hinweise"]
            if h.startswith(kosmo_szene.SATZ_BILDEINGANG)]
    assert satz and "NICHT angekommen" in satz[0]


# ====================================================================== B2 · Schrittzahl

@pytest.mark.parametrize("staerke, schritte", [(0.4, 8), (0.55, 11), (0.7, 14), (0.8, 16),
                                               (0.9, 18), (0.95, 19), (1.0, 20)])
def test_schritte_des_eigenen_starts_wie_gemessen(staerke, schritte):
    assert render.bildeingang_schritte(20, staerke) == schritte


def test_der_schrittsatz_rechnet_mit_der_staerke():
    satz = render.schrittsatz(11, {"schritte": 20, "denoise": 0.6, "bildeingang_staerke": 0.55,
                                   "modus": render.MODUS_BILD_UND_TIEFE})
    assert "Staerke 0.55 → 11" in satz and "x 0.6" not in satz
    alt = render.schrittsatz(12, {"schritte": 20, "denoise": 0.6, "modus": "image_edit"})
    assert "20 x 0.6 = 12" in alt


# ====================================================================== Farbabgleich

@pytest.mark.parametrize("nachher, gleich", [(0.5163, True), (0.676 + 0.0, False)])
def test_geom_iou_gleich_mit_toleranz(tmp_path, nachher, gleich):
    farben = [(10 * (i % 20), 120, 200 - (i % 50)) for i in range(64 * 40)]
    ki = bildschreiben.schreibe_farb_png(tmp_path / "ki.png", farben, 64, 40)
    cy = bildschreiben.schreibe_farb_png(tmp_path / "cy.png", [(c[2], c[1], c[0]) for c in farben],
                                         64, 40)
    vorher = 0.5163 + 0.023 if gleich else 0.716
    vermerk = abholer.farbabgleich_der_kamera(
        ki, cy, tmp_path, urteil_vorher={"geom_iou": vorher},
        messen=lambda png: {"geom_iou": nachher})
    assert vermerk["geom_iou_toleranz"] == abholer.GEOM_IOU_TOLERANZ_FARBABGLEICH == 0.03
    assert vermerk["geom_iou_abweichung"] == pytest.approx(abs(vorher - nachher))
    assert vermerk["geom_iou_gleich"] is gleich


# ====================================================================== der Messauftrag 300

def test_der_messauftrag_300_ist_gueltig_und_vollstaendig():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-300.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa"
    vorher = json.loads((WURZEL / "auftraege" / "offen" / "auf-20261021-299.json")
                        .read_text(encoding="utf-8"))
    assert daten["rang"] == vorher["rang"] + 1
    assert daten["params"]["folgt_auf"] == "auf-20261021-299"
    assert daten["params"]["staerken"] == [0.8, 0.9, 0.95]
    assert daten["params"]["stimmungen"] == ["morgen", "abend", "bedeckt"]
    assert daten["auflagen"]["leistungsgrenze_w"] == 400
    text = daten["anweisung"]
    for stichwort in ("vis.bildeingang", "vis.farbabgleich", "0.8", "0.9", "0.95",
                      "Sichtbeton", "geom_iou", "Dachaufbau", "VRAM", "31316", "fremd",
                      "ABGEWIESEN", "angewandt", "verdict.hinweise", "960", "Tafel",
                      "WAS AM HEIM-PC JETZT ANDERS RECHNET", "EINBAU", "NICHT:", "nach 299",
                      "Apache-2.0", "FLUX"):
        assert stichwort in text, stichwort
