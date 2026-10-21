"""Befunde aus auf-20261021-299 und -300 — was danach gebaut ist (Protokoll 74 §171, C99).

* **N1 (BLOCKER aus 300):** Über die Brücke wurde jeder Bildeingang abgewiesen, auch bei leerer
  Karte. Die Vorprüfung im Abholer sah 30 868 MiB frei, ``render.lade_modell`` im eigenen Prozess
  30 364 — der eigene CUDA-Kontext zählte dort als fremd. Jetzt fragen beide
  ``render.eigener_grafikspeicher_mib`` und rechnen ``frei + eigen``.
* **N2:** Bei dieser Abweisung im Prozess gibt es ein Ergebnis mit dem Satz.
* **N3:** Der Abweis-Satz nennt jedes Modell einmal und das eigene als «eigenes Assistenzmodell».
* **Auslöser aus 299:** ``n_ist/n_soll > 1,2`` UND ``ausserhalb > 1,5`` ab 960 px — an allen
  14 Bildern aus 295–297 gegen das Augenurteil.
* Der Messauftrag auf-20261021-301.

Attrappen statt Karte und Gewichte (Regel 2), Bilder synthetisch (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, auftrag, bruecke, kosmo_szene, render, umriss

WURZEL = Path(__file__).resolve().parents[1]

#: auf-20261021-300, 3a: vor dem Lauf frei laut nvidia-smi; im Prozess laut mem_get_info.
FREI_VORHER = 30868
FREI_IM_PROZESS = 30364
#: Seit auf-20261021-309 aus dem Register (28116 - 1241 + 512).
VERLANGT = render.bildeingang_bedarf("z-image-turbo")["verlangt_frei_mib"]


def _torch(*, angelegt=True, reserviert_mib=0, frei_mib=FREI_IM_PROZESS):
    cuda = types.SimpleNamespace(
        is_available=lambda: True, is_initialized=lambda: angelegt,
        memory_reserved=lambda: reserviert_mib * 2**20,
        mem_get_info=lambda: (frei_mib * 2**20, 32607 * 2**20))
    return types.SimpleNamespace(bfloat16="bf16", cuda=cuda)


# ====================================================================== N1 · eine Rechnung

def test_ohne_torch_haelt_der_prozess_nichts(monkeypatch):
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    assert render.eigener_grafikspeicher_mib(_prozesse={}) == 0


def test_ohne_cuda_kontext_haelt_der_prozess_nichts(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", _torch(angelegt=False))
    assert render.eigener_grafikspeicher_mib(_prozesse={4711: 9999}, _pid=4711) == 0


def test_nvidia_smi_nennt_den_prozess(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", _torch())
    assert render.eigener_grafikspeicher_mib(_prozesse={4711: 512, 1: 9000}, _pid=4711) == 512


def test_ohne_nennung_der_gemessene_kontext(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", _torch(reserviert_mib=100))
    assert render.CUDA_KONTEXT_MIB == FREI_VORHER - FREI_IM_PROZESS == 504
    assert render.eigener_grafikspeicher_mib(_prozesse={}, _pid=4711) == 100 + 504


def test_vorpruefung_und_prozess_rechnen_dasselbe(monkeypatch):
    """Der Fall aus 300: vor dem Lauf kein Kontext, im Prozess 504 MiB Kontext."""
    vorher = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=FREI_VORHER, eigen_mib=0,
                                             fremde_modelle=[])
    monkeypatch.setitem(sys.modules, "torch", _torch())
    eigen = render.eigener_grafikspeicher_mib(_prozesse={}, _pid=4711)
    im_prozess = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=FREI_IM_PROZESS,
                                                 eigen_mib=eigen)
    assert vorher["verfuegbar_mib"] == im_prozess["verfuegbar_mib"] == FREI_VORHER
    assert vorher["reicht"] is True and im_prozess["reicht"] is True
    # Der Fehler von 0.3.13 — ohne eigen — bleibt als Gegenprobe abgewiesen.
    # Seit 309 reicht 30364 auch ohne; die Gegenprobe darum knapp unter dem Bedarf.
    knapp = VERLANGT - 200
    alt = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=knapp)
    assert alt["reicht"] is False and str(VERLANGT) in alt["satz"]
    neu = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=knapp, eigen_mib=504)
    assert neu["reicht"] is True


class _Geladen(Exception):
    pass


def _diffusers(monkeypatch):
    modul = types.ModuleType("diffusers")
    modul.__version__ = "0.41.0.dev0"
    for name in ("ZImageControlNetModel", "ZImageControlNetPipeline"):
        setattr(modul, name, type(name, (), {}))
    modul.DiffusionPipeline = type("DiffusionPipeline", (), {})
    monkeypatch.setitem(sys.modules, "diffusers", modul)


def _wurzel(tmp_path):
    wurzel = tmp_path / "z-image-turbo"
    for teil in ("transformer", "vae", "text_encoder", "tokenizer"):
        (wurzel / teil).mkdir(parents=True)
    (wurzel / "model_index.json").write_text("{}")
    return wurzel


def test_lade_modell_laedt_bei_leerer_karte_mit_eigenem_kontext(tmp_path, monkeypatch):
    """Der Blocker aus 300: 30 364 frei im Prozess + 504 Kontext — jetzt wird geladen."""
    _diffusers(monkeypatch)
    monkeypatch.setitem(sys.modules, "torch", _torch())
    monkeypatch.setattr(render, "_prozesse_auf_der_karte", lambda: {})

    def laden(*a, **k):
        raise _Geladen

    monkeypatch.setattr(render, "_lade_mit_controlnet", laden)
    with pytest.raises(_Geladen):
        render.lade_modell("z-image-turbo", modell_wurzel=_wurzel(tmp_path), bildeingang=True)


def test_lade_modell_weist_bei_wirklich_zu_wenig_weiter_ab(tmp_path, monkeypatch):
    _diffusers(monkeypatch)
    monkeypatch.setitem(sys.modules, "torch", _torch(frei_mib=26000))
    monkeypatch.setattr(render, "_prozesse_auf_der_karte", lambda: {})
    monkeypatch.setattr(render, "_lade_mit_controlnet",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("darf nicht laden")))
    with pytest.raises(render.RenderError, match="26000 frei \\+ 504 eigene"):
        render.lade_modell("z-image-turbo", modell_wurzel=_wurzel(tmp_path), bildeingang=True)


def test_der_abholer_fragt_dieselbe_stelle(monkeypatch):
    pfad = WURZEL / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_b300", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    monkeypatch.setattr(modul.render, "eigener_grafikspeicher_mib", lambda: 777)
    monkeypatch.setattr(modul, "speicher_frei_mib", lambda: 1234)
    monkeypatch.setattr(modul.assistent.Ollama, "geladene", lambda self: [])
    assert modul.bildeingang_karte() == {"frei_mib": 1234, "eigen_mib": 777,
                                         "fremde_modelle": []}


# ====================================================================== N2 · Ergebnis mit Satz

def _ordner(tmp_path, **vis):
    from test_kettenlauf_26august import _auftragsordner
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def test_abweisung_im_prozess_gibt_ein_ergebnis_mit_dem_satz(tmp_path):
    from test_kettenlauf_26august import _kette
    satz = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=26000)["satz"]
    _p, attrappen = _kette(tmp_path / "k")

    def rendere(a, **kw):
        return {"status": "fehler", "error": f"RenderError: {satz}"}

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **dict(attrappen, _rendere=rendere))
    ordner = _ordner(tmp_path, bildeingang=0.55)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        bildeingang_karte=lambda: {"frei_mib": FREI_VORHER, "eigen_mib": 0, "fremde_modelle": []})
    assert antwort["tat"] == abholer.TAT_FEHLER
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    assert ergebnis["lieferstatus_grund"] == satz
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert zettel[bruecke.FELD_MELDUNG] == satz
    assert render.ABWEIS_BILDEINGANG in zettel["error"]


def test_ein_anderer_fehler_schreibt_kein_abweis_ergebnis():
    assert render.bildeingang_abweisung_in("RenderError: CUDA out of memory") is None
    assert render.bildeingang_abweisung_in(
        "Kamera 'sSE', seed 1: Render fehler — RenderError: ABGEWIESEN: Bildeingang x"
    ) == "ABGEWIESEN: Bildeingang x"


# ====================================================================== N3 · der Satz

def test_eigenes_modell_einmal_und_nicht_fremd():
    """Wörtlich aus 300 3b: «… dort liegt qwen3:14b, qwen3:14b. qwen3:14b ist das Modell …»."""
    lage = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=15000,
                                           fremde_modelle=["qwen3:14b", "qwen3:14b"])
    satz = lage["satz"]
    assert lage["reicht"] is False and satz.startswith(render.ABWEIS_BILDEINGANG)
    assert "qwen3:14b, qwen3:14b" not in satz
    assert satz.count("qwen3:14b (eigenes Assistenzmodell)") == 1
    assert satz.count("ist das eigene Assistenzmodell") == 1
    assert "fremdes Modell" not in satz
    assert "idle_window_only" in satz


def test_latest_ist_dasselbe_modell():
    satz = render.pruefe_bildeingang_karte(
        "z-image-turbo", frei_mib=15000,
        fremde_modelle=["qwen3:14b:latest", "qwen3:14b"])["satz"]
    assert satz.count("(eigenes Assistenzmodell)") == 1


def test_ein_kosmo_modell_bleibt_fremd_und_wird_nie_entladen():
    satz = render.pruefe_bildeingang_karte(
        "z-image-turbo", frei_mib=15000,
        fremde_modelle=["kosmo-qwen3.6:35b-a3b", "kosmo-qwen3.6:35b-a3b", "qwen3:14b"])["satz"]
    assert satz.count("kosmo-qwen3.6:35b-a3b (fremdes Modell)") == 1
    assert "qwen3:14b (eigenes Assistenzmodell)" in satz and "nie" in satz


def test_mit_idle_window_only_entlaedt_der_abholer_das_eigene_vor_der_pruefung(tmp_path):
    """Beschrieben, nicht umgebaut: Der Weg 106d (Owner-Auflage) gilt auch mit Bildeingang.

    Mit ``idle_window_only`` (Vorgabe der Brücke) fragt der Abholer zuerst die Karte; hält nur
    das eigene Sprachmodell sie, wird es entladen — und erst danach sieht die Bildeingang-
    Prüfung eine leere Karte. Ohne ``idle_window_only`` (300 3b) wird nicht entladen.
    """
    from test_befunde_298 import _verarbeiter
    ordner = _ordner(tmp_path, bildeingang=0.55)
    zettel = ordner / bruecke.DATEI_LAUFZETTEL
    daten = json.loads(zettel.read_text(encoding="utf-8"))
    daten["idle_window_only"] = True
    zettel.write_text(json.dumps(daten), encoding="utf-8")
    geladen = ["qwen3:14b"]
    folge = []

    def karte():
        folge.append("karte")
        return (not geladen), ("frei" if not geladen else "17330 MiB belegt")

    def entladen():
        folge.append("entladen")
        geladen.clear()
        return {"entladen": True, "satz": "Entladen: qwen3:14b."}

    def bildeingang():
        folge.append("bildeingang")
        return {"frei_mib": FREI_VORHER, "eigen_mib": 0, "fremde_modelle": list(geladen)}

    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
        darf_rechnen=abholer.karte_oder_eigenes_entladen(karte, entladen, _warte=lambda s: None),
        bildeingang_karte=bildeingang)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert folge.index("entladen") < folge.index("bildeingang")


# ====================================================================== Auslöser aus 299

#: Die 14 KI-Bilder aus 295–297, gemessen an 960 px (auf-20261021-299, Teil 2):
#: (name, n_ist/n_soll, ausserhalb_umriss_anteil, geom_iou, Augenurteil «Haus wiederzuerkennen»).
BILDER_299 = [
    ("297 1 Strasse", 2.457, 3.2146, 0.197, "nein"),
    ("297 3a", 1.142, 2.0763, 0.491, "teilweise"),
    ("297 3b", 1.162, 1.9373, 0.393, "teilweise"),
    ("297 3c", 1.796, 2.1868, 0.516, "nein"),
    ("297 3d", 1.283, 2.0940, 0.607, "nein"),
    ("297 4 weiss", 1.145, 0.0, 0.867, "ja"),
    ("297 4z weiss", 1.250, 0.1946, 0.719, "ja"),
    ("296 4a weiss", 1.146, 0.0, 0.870, "ja"),
    ("295/296 abend voll", 1.274, 4.2660, 0.005, "nein"),
    ("295/296 abend vorschau", 1.136, 2.1100, 0.384, "teilweise"),
    ("295 mittag vorschau", 1.081, 2.0645, 0.452, "teilweise"),
    ("295 winter vorschau", 1.137, 2.2095, 0.451, "teilweise"),
    ("295 winter voll", 2.045, 2.2638, 0.457, "nein"),
    ("295 mittag englisch vorschau", 1.163, 2.0300, 0.443, "teilweise"),
]
N_SOLL = 67541


def _befund(verhaeltnis, ausserhalb, iou, seite):
    return umriss.wiedererkennung(iou, n_ist=round(verhaeltnis * N_SOLL), n_soll=N_SOLL,
                                  ausserhalb_anteil=ausserhalb, lange_seite=seite)


def test_vierzehn_bilder_wie_von_auge():
    """«teilweise» gilt als erkennbar (§167); der Satz trifft genau die «nein»."""
    assert len(BILDER_299) == 14
    falsch = [name for name, v, a, i, auge in BILDER_299
              if _befund(v, a, i, 960)["gilt"] is not (auge != "nein")]
    assert falsch == []


@pytest.mark.parametrize("name, verhaeltnis, ausserhalb, iou, auge", BILDER_299)
def test_der_neue_ausloeser_je_bild(name, verhaeltnis, ausserhalb, iou, auge):
    befund = _befund(verhaeltnis, ausserhalb, iou, 960)
    neu = umriss.AUSLOESER_VERHAELTNIS_AUSSERHALB in befund["ausloeser"]
    assert neu is (verhaeltnis > 1.2 and ausserhalb > 1.5)
    # Ohne den neuen Ausloeser fielen 3c und 3d durch — dafuer ist er da.
    if name in ("297 3c", "297 3d"):
        assert befund["ausloeser"] == [umriss.AUSLOESER_VERHAELTNIS_AUSSERHALB]


def test_unter_960_px_kein_neuer_ausloeser():
    """An 480 px liegt das Verhaeltnis 0,01–0,08 hoeher (299: winter vorschau 1,213)."""
    befund = _befund(1.213, 2.10, 0.451, 480)
    assert befund["gilt"] is True
    assert umriss.AUSLOESER_VERHAELTNIS_AUSSERHALB not in _befund(1.283, 2.09, 0.607, 480)[
        "ausloeser"]
    assert _befund(1.283, 2.09, 0.607, None)["gilt"] is True


def test_der_satz_steht_am_ergebnis_und_ist_kein_tor():
    urteil = {"geom_iou": 0.607, "n_ist": 86637, "n_soll": N_SOLL, "n_gemeinsam": 60000,
              "breite": 960, "hoehe": 600, "kamera": "sSE",
              "ausserhalb_umriss": {"anteil_haus": 2.094}}
    hinweise = []
    kosmo_szene._wiedererkennung_eintragen(urteil, [], hinweise)
    assert len(hinweise) == 1 and hinweise[0].startswith(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN)
    assert "1.28" in hinweise[0] and "960 px" in hinweise[0]
    klein = dict(urteil, breite=480, hoehe=300)
    hinweise = []
    kosmo_szene._wiedererkennung_eintragen(klein, [], hinweise)
    assert hinweise == []


def test_die_schalter_bleiben_messschalter_vorgabe_aus():
    from aiimaging import backbone
    assert backbone.hole("z-image-turbo").bildeingang_traegt is False
    m, e = [], []
    assert kosmo_szene.lies_farbabgleich({}, skip=False, maengel=m, endgueltig=e) is False
    assert kosmo_szene.lies_bildeingang({}, skip=False, guete=None, backbone_name="z-image-turbo",
                                        maengel=m, endgueltig=e) is None
    assert m == [] and e == []


# ====================================================================== der Messauftrag 301

def test_der_messauftrag_301_ist_gueltig_und_vollstaendig():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-301.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa"
    vorher = json.loads((WURZEL / "auftraege" / "offen" / "auf-20261021-300.json")
                        .read_text(encoding="utf-8"))
    assert daten["rang"] == vorher["rang"] + 1
    assert daten["params"]["folgt_auf"] == "auf-20261021-300"
    assert daten["auflagen"]["leistungsgrenze_w"] == 400
    text = daten["anweisung"]
    for stichwort in ("vis.bildeingang", "vis.farbabgleich", "0.55", "0.9", "abend",
                      "angewandt.bildeingang", "angewandt.farbabgleich", "qwen3:14b",
                      "eigenes Assistenzmodell", "fremdes Modell", "idle_window_only",
                      "1,2", "1,5", "960", "OHNE NEUEN KI-LAUF", "eigener_grafikspeicher_mib",
                      "render-result.json", "WAS AM HEIM-PC JETZT ANDERS RECHNET", "EINBAU",
                      "NICHT:", "Apache-2.0", "FLUX", "400 W"):
        assert stichwort in text, stichwort
