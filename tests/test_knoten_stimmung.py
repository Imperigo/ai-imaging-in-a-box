"""Knoten «Stimmung», Heim-PC-Teil (H1, 20.10.2026): ``render.environment`` mit Himmelsbild.

Vertrag mit dem Integrator (nach dem v0.1.9-Schnitt): ``render.environment {preset,
hdri?, intensitaet?, rotationGrad?}`` — alles ohne Default; der Heim-PC setzt die Vorgaben
und nennt sie im Ergebnis (``angewandt.environment``). Entscheid 113: Fehlt das Himmelsbild
am Rechner, wird der Auftrag mit Satz abgewiesen, und derselbe Satz steht im Ergebnis unter
``lieferstatus_grund``.

Regel 3: Die Himmelsbilder sind hier erzeugte Mini-Dateien in ``tmp_path``; der Ordner kommt
nur über ``AIIMAGING_HIMMEL_ORDNER``. Regel 2: Der Runner wird mit einer Attrappe für ``bpy``
geladen, nie mit Blender.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import abholer, bruecke, heimstand, kosmo_szene, prompts, seams, stimmung

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")


def _himmel(tmp_path, monkeypatch, *namen):
    """Ein Ordner mit Mini-Himmelsbildern, eingestellt über die Umgebungsvariable."""
    ordner = tmp_path / "himmel"
    ordner.mkdir(exist_ok=True)
    for name in namen:
        (ordner / name).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))
    return ordner


def _alle_himmel(tmp_path, monkeypatch):
    return _himmel(tmp_path, monkeypatch, *[
        stimmung.dateiname(p, e["hdri"], a)
        for p, e in stimmung.STIMMUNGEN.items() for a in ("2k", "4k")])


def _szene(environment, **mehr):
    s = {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
         "render": {"environment": environment}, "style": {"prompt": "a quiet house"},
         "vis": {}}
    for k, v in mehr.items():
        s[k] = v
    return s


# ====================================================================== die Tabelle

def test_acht_stimmungen_wie_der_vertrag():
    assert stimmung.PRESETS == ("morgen", "mittag", "abend", "blaue-stunde", "bedeckt",
                                "nebel", "winter", "weiss")
    assert set(stimmung.STIMMUNGEN) == set(stimmung.PRESETS)
    assert stimmung.STIMMUNGEN["mittag"]["hdri"] == "kloofendal_43d_clear_puresky"
    # Getauscht am 20.10.2026 abends (HomeStation; die alten Dateien bleiben liegen).
    assert stimmung.STIMMUNGEN["weiss"]["hdri"] == "studio_small_08"
    for preset, e in stimmung.STIMMUNGEN.items():
        assert stimmung.HDRI_MUSTER.match(e["hdri"]), preset
        assert e["prompt_de"] and e["prompt_en"] and e["merkmale"]
        # Der englische Satz wird nach dem Bauteilwaechter angefuegt — er nennt kein Bauteil.
        assert not prompts.bauteilwaechter(e["prompt_en"])["gefunden"], preset
        # Er traegt sein eigenes Merkmal, sonst stuende er beim naechsten Lauf doppelt da.
        assert stimmung.prompt_satz(preset, e["prompt_en"]) == (None, True), preset


def test_die_tabelle_traegt_keine_pfade():
    text = Path(stimmung.__file__).read_text(encoding="utf-8")
    assert "/home/" not in text and "C:\\" not in text
    assert stimmung.HERKUNFT["lizenz"] == "CC0-1.0"


def test_dateiname_und_aufloesung():
    assert stimmung.dateiname("mittag", "kloofendal_43d_clear_puresky", "4k") == \
        "mittag__kloofendal_43d_clear_puresky_4k.hdr"
    assert stimmung.aufloesung_fuer("vorschau") == "2k"
    assert stimmung.aufloesung_fuer("voll") == "4k"
    assert stimmung.aufloesung_fuer(None) == "4k"


# ====================================================================== lies_szene

def test_die_stimmung_wird_gelesen_mit_vorgaben(tmp_path, monkeypatch):
    ordner = _alle_himmel(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene({"preset": "mittag"}))
    assert s["maengel"] == ()
    assert s["umgebung"] == {"preset": "mittag", "hdri": "kloofendal_43d_clear_puresky",
                             "intensitaet": 1.0, "rotationGrad": 0.0}
    assert set(s["umgebung_vorgaben"]) == {"hdri", "intensitaet", "rotationGrad"}
    assert Path(s["umgebung_datei"]["pfad"]) == \
        ordner / "mittag__kloofendal_43d_clear_puresky_4k.hdr"
    # Nicht mehr abgewiesen (bis 20.10.2026 in ABGEWIESENE_FELDER).
    assert "render.environment" not in kosmo_szene.ABGEWIESENE_FELDER


def test_die_vorschau_nimmt_das_2k_bild(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene({"preset": "abend", "intensitaet": 2.5,
                                       "rotationGrad": 90}, vis={"guete": "vorschau"}))
    assert s["maengel"] == ()
    assert s["umgebung_datei"]["aufloesung"] == "2k"
    assert s["umgebung"]["intensitaet"] == 2.5 and s["umgebung"]["rotationGrad"] == 90.0
    assert s["umgebung_vorgaben"] == ("hdri",)


def test_ein_fehlendes_himmelsbild_weist_mit_namen_ab(tmp_path, monkeypatch):
    _himmel(tmp_path, monkeypatch)       # Ordner leer
    s = kosmo_szene.lies_szene(_szene({"preset": "mittag"}))
    satz = "Himmelsbild 'kloofendal_43d_clear_puresky' (4k) fehlt am Rechner."
    assert satz in s["maengel"]
    assert satz in s["maengel_endgueltig"], "Warten heilt das nicht — Satz und Ende"
    assert s["fehlende_dateien"] == (satz,)
    assert "/" not in satz.replace("(4k)", ""), "kein Pfad im Satz (Regel 3)"


def test_ohne_eingestellten_ordner_ebenso(monkeypatch):
    monkeypatch.delenv(stimmung.HIMMEL_ORDNER_ENV, raising=False)
    s = kosmo_szene.lies_szene(_szene({"preset": "nebel", "hdri": "kloppenheim_04"}))
    assert any("kloppenheim_04" in m and stimmung.HIMMEL_ORDNER_ENV in m
               for m in s["maengel_endgueltig"])


def test_mit_grundlage_wird_kein_bild_gebraucht(monkeypatch):
    monkeypatch.delenv(stimmung.HIMMEL_ORDNER_ENV, raising=False)
    s = kosmo_szene.lies_szene(_szene({"preset": "winter"},
                                      vis={"grundlage": "gl-0123456789abcdef", "seed": 3}))
    assert s["maengel"] == ()
    assert s["umgebung"]["preset"] == "winter" and s["umgebung_datei"] is None


@pytest.mark.parametrize("env, wort", [
    ({"preset": "sturm"}, "preset"),
    ({"preset": "mittag", "hdri": "../himmel/x"}, "hdri"),
    ({"preset": "mittag", "hdri": "Gross"}, "hdri"),
    ({"preset": "mittag", "intensitaet": 11}, "intensitaet"),
    ({"preset": "mittag", "rotationGrad": -1}, "rotationGrad"),
    ({"preset": "mittag", "farbe": "rot"}, "farbe"),
    ("mittag", "kein Block"),
])
def test_falsche_stimmungen_sind_maengel(tmp_path, monkeypatch, env, wort):
    _alle_himmel(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene(env))
    assert any(wort in m for m in s["maengel"]), s["maengel"]


def test_der_satz_der_stimmung_kommt_nur_einmal_in_den_prompt(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    ohne = kosmo_szene.lies_szene(_szene({"preset": "bedeckt"}))
    assert ohne["prompt"].endswith(stimmung.STIMMUNGEN["bedeckt"]["prompt_en"])
    # Seit auf-20261021-306 (B2) gilt der Satz des Heim-PC IMMER, und einmal: Der Satz des
    # Knotens wird herausgenommen; eigene Worte des Bestellers bleiben stehen. Bis dahin hielt
    # ein `merkmal` den Satz zurueck — auch dann, wenn es in einem halb uebersetzten Satz stand.
    satz = stimmung.STIMMUNGEN["bedeckt"]["prompt_en"]
    mit = _szene({"preset": "bedeckt"})
    mit["style"]["prompt"] = f"a quiet house under an overcast sky, {satz}"
    mit = kosmo_szene.lies_szene(mit)
    assert mit["prompt"] == f"a quiet house under an overcast sky, {satz}"
    assert mit["prompt"].count(satz) == 1
    assert mit["prompt_zusaetze"][0]["schon_im_prompt"] is False
    assert mit["prompt_zusaetze"][0]["herausgenommen"] == ["bedeckt"]


def test_jedes_gelesene_feld_steht_in_der_durchreichung(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = kosmo_szene.lies_szene(_szene({"preset": "mittag"}))
    for feld in ("umgebung", "umgebung_datei", "umgebung_vorgaben", "prompt_zusaetze",
                 "fehlende_dateien"):
        assert feld in s and feld in kosmo_szene.DURCHGEREICHT, feld


# ====================================================================== die Naht

def test_seams_reicht_das_himmelsbild_nur_durch_wenn_bestellt():
    from aiimaging.seams import _multipass_argumente
    basis = dict(drehen=False, aufloesung=512, samples=8, beauty=True, material_id=True)
    ohne = _multipass_argumente("/t/a.glb", "/t/aus", **basis)
    assert not any(a.startswith("--umgebung") for a in ohne)
    mit = _multipass_argumente("/t/a.glb", "/t/aus", **basis, umgebung_hdr="/t/h.hdr",
                               umgebung_staerke=2.0, umgebung_drehung=-45.0,
                               umgebung_weiss=True)
    i = mit.index("--umgebung-hdr")
    assert mit[i + 1] == "/t/h.hdr"
    assert "--umgebung-staerke=2.0" in mit and "--umgebung-drehung=-45.0" in mit
    assert "--umgebung-weiss" in mit


def test_ein_fehlendes_himmelsbild_startet_kein_blender(tmp_path):
    with pytest.raises(seams.SeamError, match="Himmelsbild"):
        seams.glb_zu_multipass(tmp_path / "a.glb", tmp_path / "aus", up_axis="Y",
                               umgebung_hdr=tmp_path / "fehlt.hdr",
                               _starte=lambda *a, **k: None)


def _mit_stimmung(ordner, environment, **vis):
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["render"]["environment"] = environment
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")


def test_der_abholer_gibt_das_himmelsbild_an_blender(tmp_path, monkeypatch):
    himmel = _alle_himmel(tmp_path, monkeypatch)
    ordner = _auftragsordner(tmp_path / "a")
    _mit_stimmung(ordner, {"preset": "abend", "rotationGrad": 30})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kw = protokoll["multipass"][0]
    assert Path(kw["umgebung_hdr"]) == himmel / "abend__belfast_sunset_puresky_4k.hdr"
    assert kw["umgebung_staerke"] == 1.0 and kw["umgebung_drehung"] == 30.0
    # Belichtung und Toenung je Stimmung (auf-20261020-292).
    assert kw["umgebung_belichtung"] == stimmung.STIMMUNGEN["abend"]["belichtung_ev"]
    assert kw["umgebung_toenung"] == tuple(stimmung.toenung_fuer(
        stimmung.STIMMUNGEN["abend"]["kelvin"]))
    assert "umgebung_weiss" not in kw
    angewandt = antwort["ergebnis"]["angewandt"]["environment"]
    assert angewandt["preset"] == "abend" and angewandt["hdri"] == "belfast_sunset_puresky"
    assert angewandt["aufloesung"] == "4k" and angewandt["sonnenlampe"] is False
    assert set(angewandt["vorgaben"]) == {"hdri", "intensitaet"}
    assert str(tmp_path) not in json.dumps(antwort["ergebnis"]), "kein Pfad (Regel 3)"


def test_weiss_macht_das_gipsmodell(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    ordner = _auftragsordner(tmp_path / "a")
    _mit_stimmung(ordner, {"preset": "weiss"})
    protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"][0]["umgebung_weiss"] is True
    assert antwort["ergebnis"]["angewandt"]["environment"]["gipsmodell"] is True


def test_die_stimmung_gehoert_zur_grundlage():
    assert "umgebung" in abholer.GRUNDLAGE_MUSS_PASSEN


def test_eine_fehlende_datei_ergibt_ein_ergebnis_mit_grund(tmp_path, monkeypatch):
    """Entscheid 113: abweisen mit Satz — am Laufzettel UND im Ergebnis."""
    _himmel(tmp_path, monkeypatch)
    ordner = _auftragsordner(tmp_path / "a")
    _mit_stimmung(ordner, {"preset": "mittag"})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert protokoll["multipass"] == [], "kein Blender"
    laufzettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert laufzettel["status"] == bruecke.STATUS_ERROR
    assert "kloofendal_43d_clear_puresky" in laufzettel["error"]
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["images"] == []
    assert ergebnis["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    assert ergebnis["lieferstatus_grund"] == \
        "Himmelsbild 'kloofendal_43d_clear_puresky' (4k) fehlt am Rechner."
    assert ergebnis["qa"]["verdict"]["passed"] is False
    assert ergebnis["angewandt"]["environment"]["preset"] == "mittag"


# ====================================================================== der Heim-PC-Stand

def test_heimstand_zaehlt_die_himmelsbilder(tmp_path, monkeypatch):
    _himmel(tmp_path, monkeypatch, "mittag__kloofendal_43d_clear_puresky_2k.hdr",
            "mittag__kloofendal_43d_clear_puresky_4k.hdr",
            "abend__belfast_sunset_puresky_2k.hdr")
    stand = stimmung.himmelsbilder_stand()
    assert stand["da"] == 1 and stand["von"] == 8
    assert "abend" in stand["fehlend"] and stand["satz"].startswith("Himmelsbilder 1/8")
    monkeypatch.setattr(heimstand, "grafikkarte", lambda: {"frei_gb": None, "satz": "x"})
    monkeypatch.setattr(heimstand.assistent, "stand",
                        lambda **k: {"stand": "aus", "modell": None, "satz": "aus"})
    h = heimstand.heimstand()
    assert h["himmelsbilder"]["da"] == 1 and "Himmelsbilder 1/8" in h["satz"]
    assert str(tmp_path) not in json.dumps(h), "kein Pfad (Regel 3)"


# ====================================================================== der Runner

class _Objekte(list):
    def new(self, name, daten):
        o = SimpleNamespace(name=name, data=daten, location=None, rotation_euler=None)
        self.append(o)
        return o


def _runner(monkeypatch):
    bpy = mock.MagicMock()
    bpy.data.objects = _Objekte()
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_stimmung", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul, bpy


def test_der_runner_kennt_die_drei_schalter(monkeypatch):
    modul, _ = _runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["blender", "--", "--glb", "a.glb", "--out", "aus",
                                      "--umgebung-hdr", "h.hdr", "--umgebung-staerke=2",
                                      "--umgebung-drehung=-30", "--umgebung-weiss"])
    a = modul._argumente()
    assert (a.umgebung_hdr, a.umgebung_staerke, a.umgebung_drehung, a.umgebung_weiss) == \
        ("h.hdr", 2.0, -30.0, True)


def test_mit_himmelsbild_keine_sonnenlampe_ausser_bestellt(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    a = SimpleNamespace(umgebung_hdr="h.hdr", sonne_hoehe=None, sonne_azimut=None,
                        sonne_staerke=None, sonne_kelvin=None, sonne_winkel=None)
    objekt, befund = modul._sonne_setzen([0, 0, 0], 10.0, a)
    assert objekt is None and befund["weg"] == "himmelsbild"
    assert not bpy.data.lights.new.called
    # Eine bestellte Sonne bleibt (Entscheid 110).
    a.sonne_hoehe = 30.0
    _, befund = modul._sonne_setzen([0, 0, 0], 10.0, a)
    assert befund["weg"] != "himmelsbild" and bpy.data.lights.new.called


def test_die_welt_aus_dem_himmelsbild(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    befund = modul._welt_setzen((0.5, 0.5, 0.5), 1.5, hdr="/irgendwo/mittag__x_4k.hdr",
                                drehung_grad=90.0)
    baum = bpy.data.worlds.new.return_value.node_tree
    arten = [c.args[0] for c in baum.nodes.new.call_args_list]
    assert arten[:3] == ["ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeTexEnvironment"]
    # Seit auf-20261020-292 (B2): Kamerastrahlen sehen einen ruhigen Verlauf, nicht das Bild.
    assert "ShaderNodeLightPath" in arten and "ShaderNodeMixShader" in arten
    assert befund["hintergrund"]["kamerastrahl"] == "ruhig"
    assert befund["datei"] == "mittag__x_4k.hdr", "nur der Name, kein Pfad"
    assert befund["staerke"] == 1.5 and befund["drehung_grad"] == 90.0
    # Ohne Himmelsbild bleibt es die gleichmaessige Welt.
    assert modul._welt_setzen((0.0, 0.0, 0.0), 0.0) is None


def test_der_id_pass_bleibt_schwarz():
    quelle = RUNNER.read_text(encoding="utf-8")
    assert "_welt_setzen((0.0, 0.0, 0.0), 0.0)" in quelle
    assert quelle.index("_alles_weiss()") < quelle.index("bpy.ops.render.render(write_still=not")
