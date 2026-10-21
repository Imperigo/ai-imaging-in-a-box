"""Befunde aus auf-20261021-302 und -303 — was danach gebaut ist (Strang Kern, 21.10.2026).

* **303 B1:** Mit ``vis.umriss_halten: "nachher"`` kommen «KI BAUT UEBER DEN UMRISS HINAUS» und
  «HAUS IM KI-BILD NICHT WIEDERZUERKENNEN» vom gehaltenen, gelieferten Bild; das Urteil von
  vorher bleibt im Vermerk und im Satz «UMRISS HALTEN …».
* **303 B2:** Der Satz des Bildmodells («Hintergrund im Fahrplan festgehalten …») steht auch im
  Ergebnis — in ``qa.verdict.hinweise`` und unter ``angewandt.umriss_halten``.
* **303 B3:** Mit ``vis.material_vorne`` steht der Stoff höchstens dreimal im Prompt; der Satz
  des Material-Knotens hinten fällt weg, wenn vorne derselbe Stoff steht.
* **303 Nebenbefund:** ``render._eigener_start`` kodiert das Cycles-Bild unter ``no_grad``.
* **302 B1:** Ein vorhandener, aber leerer oder unvollständiger Gewichtsordner des
  Tiefenschätzers endet mit einem klaren Satz statt «Unrecognized model … model_type».
* **302 B2:** Die Zeilen «Im Prozess …» stehen im Journal unter ihrem Auftrag, nach der
  Vorprüfung, nicht mehr vor der Zusammenfassung des Durchgangs.

Attrappen statt Karte, Gewichte und torch; Pfade synthetisch unter ``tmp_path`` (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, auftrag, kosmo_szene, materialwahl, render, umrisshalt
from aiimaging import tiefenschaetzer as ts

WURZEL = Path(__file__).resolve().parents[1]


# ====================================================================== 303 B1 · nachher

#: Das Urteil von U1 aus auf-20261021-303 (vor dem Halten) und die Nachmessung (nach dem Halten).
VORHER = {"kamera": "sSE", "geom_iou": 0.5163, "n_ist": 121300, "n_soll": 67541,
          "n_gemeinsam": 58000, "score": 0.4, "anteil_soll": 0.12, "breite": 960, "hoehe": 600,
          "ausserhalb_umriss": {"anteil_haus": 2.1868}}
NACHHER = {"geom_iou": 0.7893, "n_ist": 70000, "n_soll": 67541, "n_gemeinsam": 60000,
           "score": 0.5, "anteil_soll": 0.12, "breite": 960, "hoehe": 600,
           "ausserhalb_umriss": {"anteil_haus": 0.0599}, "rho_maske": {"gross": "nicht im Satz"}}


def _saetze(urteil):
    hinweise = []
    kosmo_szene._ausserhalb_eintragen({}, None, [{"kamera": "sSE", "geometrie_urteil": urteil}],
                                      hinweise)
    kosmo_szene._wiedererkennung_eintragen(None, [{"kamera": "sSE", "geometrie_urteil": urteil}],
                                           hinweise)
    kosmo_szene._messschalter_eintragen(None, [{"kamera": "sSE", "geometrie_urteil": urteil}],
                                        hinweise)
    return hinweise


def test_ohne_halten_tragen_die_saetze_das_urteil_des_ki_bilds():
    hinweise = _saetze(dict(VORHER))
    assert any(h.startswith(kosmo_szene.SATZ_AUSSERHALB) for h in hinweise)
    assert any(h.startswith(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN) for h in hinweise)


def test_kamera_nachher_legt_das_urteil_des_gehaltenen_bilds_in_den_vermerk(tmp_path):
    from test_material_und_umriss import B, H, _bilder
    ki, grund, maske = _bilder(tmp_path)
    v = abholer.umriss_halten_der_kamera(ki, grund, maske, B, H, tmp_path,
                                         urteil_vorher=VORHER, messen=lambda png: dict(NACHHER))
    assert v["urteil_nachher"]["geom_iou"] == 0.7893
    assert v["urteil_nachher"]["ausserhalb_umriss"] == {"anteil_haus": 0.0599}
    # Nur die Felder der Saetze — das ganze Urteil gehoert nicht in den Vermerk.
    assert set(v["urteil_nachher"]) <= set(abholer.UMRISS_NACHHER_SATZFELDER)
    assert (v["geom_iou_vorher"], v["ausserhalb_vorher"]) == (0.5163, 2.1868)


def test_nachher_die_saetze_kommen_vom_gehaltenen_bild_das_vorher_steht_im_vermerk(tmp_path):
    from test_material_und_umriss import B, H, _bilder
    ki, grund, maske = _bilder(tmp_path)
    v = abholer.umriss_halten_der_kamera(ki, grund, maske, B, H, tmp_path,
                                         urteil_vorher=VORHER, messen=lambda png: dict(NACHHER))
    urteil = dict(VORHER, **{abholer.URTEIL_UMRISS_HALTEN: v})
    hinweise = _saetze(urteil)
    assert not any(h.startswith(kosmo_szene.SATZ_AUSSERHALB) for h in hinweise), hinweise
    assert not any(h.startswith(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN) for h in hinweise)
    halten = [h for h in hinweise if h.startswith(umrisshalt.SATZ)]
    assert len(halten) == 1
    assert "nach dem Halten geom_iou 0.7893" in halten[0]
    assert "vor dem Halten geom_iou 0.5163" in halten[0] and "2.1868" in halten[0]
    assert "gehaltenen Bild" in halten[0]
    # Das Kameraurteil selbst bleibt das von vorher.
    assert urteil["geom_iou"] == 0.5163
    qa = {}
    kosmo_szene._ausserhalb_eintragen(qa, None, [{"kamera": "sSE", "geometrie_urteil": urteil}],
                                      [])
    assert qa[kosmo_szene.FELD_AUSSERHALB] == 0.0599


def test_nachher_ohne_nachmessung_bleibt_es_beim_urteil_von_vorher():
    urteil = dict(VORHER, **{abholer.URTEIL_UMRISS_HALTEN: {
        "angewandt": True, "art": "nachher", "rand_px": 19, "geom_iou_nachher": None}})
    hinweise = _saetze(urteil)
    assert any(h.startswith(kosmo_szene.SATZ_AUSSERHALB) for h in hinweise)
    assert any("VOR dem Halten (nicht nachgemessen)" in h for h in hinweise)


def test_im_lauf_aendert_das_urteil_der_saetze_nicht():
    urteil = dict(VORHER, **{abholer.URTEIL_UMRISS_HALTEN: {
        "angewandt": True, "art": "im_lauf", "rand_px": 19, "urteil_nachher": NACHHER}})
    assert kosmo_szene.urteil_fuer_umrisssaetze(urteil) is urteil


# ====================================================================== 303 B2 · der Fahrplan-Satz

FAHRPLAN = (f"{umrisshalt.SATZ}: Hintergrund im Fahrplan festgehalten (Art 'im_lauf'), frei "
            f"fuer die KI 14 % der Zellen 128 x 80. Grafikspeicher gemessen wie ohne Schalter.")


def _im_lauf_urteil(kamera):
    erg = {"parameter": {"umriss_halten_schritte": 20}, "hinweise": (FAHRPLAN, "anderes")}
    vermerk = abholer.umriss_halten_vermerk_im_lauf(erg, {"rand_px": 19, "anteil_frei": 0.1377,
                                                          "methode": "x"})
    return dict(VORHER, kamera=kamera, **{abholer.URTEIL_UMRISS_HALTEN: vermerk})


def test_der_satz_des_bildmodells_steht_in_den_hinweisen_einmal():
    hinweise = []
    kosmo_szene._messschalter_eintragen(None, [
        {"kamera": "sSE", "geometrie_urteil": _im_lauf_urteil("sSE")},
        {"kamera": "nNW", "geometrie_urteil": _im_lauf_urteil("nNW")}], hinweise)
    assert hinweise.count(FAHRPLAN) == 1
    assert sum(h.startswith(f"{umrisshalt.SATZ}, Kamera") for h in hinweise) == 2


def test_der_satz_steht_im_ergebnis_unter_qa_verdict_hinweise():
    erg = kosmo_szene.als_ergebnis("job-1", [], geometrie_urteil=_im_lauf_urteil("sSE"))
    assert FAHRPLAN in erg["qa"]["verdict"]["hinweise"]


def test_angewandt_traegt_umriss_halten_additiv():
    ohne = abholer.angewandt_mit_messschaltern({"environment": {"preset": "mittag"}}, [VORHER])
    assert ohne == {"environment": {"preset": "mittag"}}
    mit = abholer.angewandt_mit_messschaltern({"environment": {"preset": "mittag"}},
                                              [_im_lauf_urteil("sSE"), _im_lauf_urteil("nNW")])
    assert mit["environment"] == {"preset": "mittag"}
    uh = mit["umriss_halten"]
    assert uh["art"] == "im_lauf" and set(uh["kameras"]) == {"sSE", "nNW"}
    assert uh["kameras"]["sSE"]["hinweise"] == [FAHRPLAN]
    assert uh["kameras"]["sSE"]["schritte"] == 20 and uh["kameras"]["sSE"]["angewandt"] is True
    # Keine Pfade, kein ganzes Urteil im Ergebnis.
    assert "urteil_nachher" not in json.dumps(uh) and "png" not in json.dumps(uh)


def test_der_satz_des_bildmodells_nennt_die_messung():
    satz = render._umriss_halten_satz({"anteil_frei": 0.1377, "zellen": (80, 128)}, True)
    assert "Ungemessen" not in satz and "auf-20261021-303" in satz


# ====================================================================== 303 B3 · Stoff im Prompt

def _szene(prompt, render_block=None, **vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": dict({"samples": 8}, **(render_block or {})),
            "style": {"prompt": prompt}, "vis": vis}


STANDARD = ("contemporary residential building, exposed concrete, architectural photography, "
            "no people")
MATERIAL = {"materialien": {"fassade": {"id": "sichtbeton-schalungsglatt"}}}


def test_e3_der_stoff_steht_hoechstens_dreimal_und_ohne_doppelten_satz():
    szene = kosmo_szene.lies_szene(_szene(STANDARD, MATERIAL, material_vorne=True,
                                          umriss_halten="im_lauf"), streng=False)
    prompt = szene["prompt"]
    stoff = materialwahl.BIBLIOTHEK["sichtbeton-schalungsglatt"]["prompt_en"]
    assert prompt.startswith(f"monolithic {stoff} building, made entirely of {stoff}, "
                             f"contemporary residential building")
    assert kosmo_szene.stoff_nennungen(prompt, stoff) == 3, prompt
    assert "exterior surfaces of" not in prompt
    material = [z for z in szene["prompt_zusaetze"] if z["art"] == "material"]
    assert material and material[0]["weggelassen"] == "material_vorne"
    # Der Prompt des Bestellers bleibt Wort fuer Wort.
    assert STANDARD in prompt


def test_e1_ohne_material_vorne_bleibt_der_satz_hinten():
    szene = kosmo_szene.lies_szene(_szene(STANDARD, MATERIAL), streng=False)
    assert szene["prompt"].endswith("exterior surfaces of smooth fair-faced concrete")
    assert not any(z.get("weggelassen") for z in szene["prompt_zusaetze"])


def test_ohne_stoff_im_prompt_bleiben_drei_nennungen_vorne():
    satz, _ = kosmo_szene.material_vorne_satz("a house", ["smooth fair-faced concrete"])
    assert satz.count("smooth fair-faced concrete") == 3


def test_vorne_bleibt_mindestens_eine_nennung():
    text = "concrete house, concrete roof, concrete wall, concrete plinth"
    satz, _ = kosmo_szene.material_vorne_satz(text)
    assert satz == "monolithic concrete building"


@pytest.mark.parametrize("text, stoff, zahl", [
    ("exposed concrete, smooth fair-faced concrete", "concrete", 2),
    ("red brick masonry villa", "red brick masonry", 1),
    ("a timber house", "spruce timber battens", 1),
    ("a house", "concrete", 0),
])
def test_nennungen_werden_an_den_kopfwoertern_gezaehlt(text, stoff, zahl):
    assert kosmo_szene.stoff_nennungen(text, stoff) == zahl


# ====================================================================== 303 · no_grad

class _Wert:
    """Ein Zahlenersatz, der Rechnungen mitmacht und weiss, ob ``no_grad`` galt."""

    def __init__(self, unter_no_grad):
        self.unter_no_grad = unter_no_grad
        self.shape = (1, 16, 80, 128)
        self.device = "cpu"

    def _neu(self, *_):
        return self

    __sub__ = __rsub__ = __mul__ = __rmul__ = __add__ = __radd__ = _neu

    def to(self, *a, **k):
        return self


def _attrappen(monkeypatch):
    zustand = {"no_grad": False, "encode_unter_no_grad": None}

    class _KeinGrad:
        def __enter__(self):
            zustand["no_grad"] = True

        def __exit__(self, *a):
            zustand["no_grad"] = False

    torch = types.SimpleNamespace(no_grad=_KeinGrad, float32="f32")
    zmod = types.ModuleType("diffusers.pipelines.z_image.pipeline_z_image_controlnet")
    zmod.get_default_z_image_sigmas = lambda n: [1.0 - i / n for i in range(n)]
    zmod.calculate_shift = lambda *a: 1.0
    zmod.retrieve_latents = lambda wert, **k: wert
    utils = types.ModuleType("diffusers.utils.torch_utils")
    utils.randn_tensor = lambda shape, **k: _Wert(zustand["no_grad"])
    for name in ("diffusers", "diffusers.pipelines", "diffusers.pipelines.z_image",
                 "diffusers.utils"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, zmod.__name__, zmod)
    monkeypatch.setitem(sys.modules, utils.__name__, utils)

    def encode(eingang):
        zustand["encode_unter_no_grad"] = zustand["no_grad"]
        return _Wert(zustand["no_grad"])

    vae = types.SimpleNamespace(encode=encode, dtype="bf16",
                                config=types.SimpleNamespace(shift_factor=0.1,
                                                             scaling_factor=0.3))
    scheduler = types.SimpleNamespace(config={}, sigmas=[0.6, 0.3, 0.0],
                                      set_timesteps=lambda **k: None)
    pipeline = types.SimpleNamespace(
        vae_scale_factor=8, scheduler=scheduler, _execution_device="cpu", vae=vae,
        image_processor=types.SimpleNamespace(preprocess=lambda b, **k: _Wert(False)))
    return torch, pipeline, zustand


def test_eigener_start_kodiert_das_cycles_bild_unter_no_grad(monkeypatch):
    torch, pipeline, zustand = _attrappen(monkeypatch)
    start, satz = render._eigener_start(pipeline, torch, "bild", breite=1024, hoehe=640,
                                        schritte=20, staerke=0.8, generator=None)
    assert zustand["encode_unter_no_grad"] is True
    assert zustand["no_grad"] is False          # danach wieder wie vorher
    assert "latents" in start and satz.startswith("BILD UND TIEFE")


def test_der_bedarf_des_bildeingangs_bleibt_bis_zur_neuen_messung():
    """Gesenkt wird erst nach der Messung von auf-20261021-308 — nicht hier."""
    from aiimaging import backbone
    eintrag = backbone.BACKBONES["z-image-turbo"]
    assert eintrag.vram_bildeingang_spitze_mib == 31316
    assert "auf-20261021-298" in eintrag.vram_bildeingang_beleg


# ====================================================================== 302 B1 · leerer Ordner

def test_ein_leerer_ordner_sagt_leer_und_nicht_unrecognized(tmp_path):
    with pytest.raises(ts.TiefenschaetzerError) as fehler:
        ts.lade_modell(ts.VORGABE_TIEFENSCHAETZER, tmp_path)
    text = str(fehler.value)
    assert "leer oder unvollstaendig" in text and "ist da, aber leer" in text
    assert "nie aus dem Netz" in text and "Unrecognized" not in text


@pytest.mark.parametrize("dateien, stichwort", [
    ({"README.md": "x"}, "ohne config.json"),
    ({"config.json": "{kaputt"}, "unlesbar"),
    ({"config.json": "{}"}, "kein 'model_type'"),
    ({"config.json": '{"model_type": "depth_anything"}'}, "ohne Gewichtsdatei"),
])
def test_ein_unvollstaendiger_ordner_sagt_was_fehlt(tmp_path, dateien, stichwort):
    for name, inhalt in dateien.items():
        (tmp_path / name).write_text(inhalt, encoding="utf-8")
    assert stichwort in ts.ordner_unvollstaendig(tmp_path)
    with pytest.raises(ts.TiefenschaetzerError, match="leer oder unvollstaendig"):
        ts.lade_modell(ts.VORGABE_TIEFENSCHAETZER, tmp_path)


def test_ein_vollstaendiger_ordner_geht_weiter(tmp_path):
    (tmp_path / "config.json").write_text('{"model_type": "depth_anything"}', encoding="utf-8")
    (tmp_path / "model.safetensors").write_bytes(b"")
    assert ts.ordner_unvollstaendig(tmp_path) is None


# ====================================================================== 302 B2 · Journal

def _abholen(name):
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / "abholen.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def test_im_prozess_steht_unter_seinem_auftrag_nach_der_vorpruefung(capsys):
    modul = _abholen("abholen_b302_b2")
    journal = []

    def lader(name, wurzel, **kw):
        def modell(parameter):
            return "bild.png"
        modell.bildeingang_pruefung = "Bildeingang: 30862 MiB verfuegbar (30364 frei + 498 eigene)."
        return modell

    modul.EinmalGeladen(lader, "backbone", "modell_wurzel", journal=journal)(
        {"backbone": "z-image-turbo", "bildeingang_staerke": 0.8})
    assert capsys.readouterr().out == ""            # nichts sofort hinaus
    assert journal == ["Im Prozess Bildeingang: 30862 MiB verfuegbar (30364 frei + 498 eigene)."]
    bericht = {"verarbeitet": 1, "ergebnisse": [
        {"job_id": "vis-1", "tat": "erledigt", "grund": "", "karte": "Karte: entladen.",
         "bildeingang": "Bildeingang: 30868 MiB verfuegbar.", "wache": None}]}
    modul._berichte(bericht, im_prozess={"vis-1": list(journal)})
    aus = capsys.readouterr().out
    zusammenfassung = aus.index('"verarbeitet"')
    karte, vor, im = (aus.index("Karte: Karte"), aus.index("Vorpruefung Bildeingang"),
                      aus.index("Im Prozess Bildeingang"))
    assert zusammenfassung < karte < vor < im


def test_ohne_zuordnung_geht_die_zeile_nicht_verloren(capsys):
    modul = _abholen("abholen_b302_b2b")
    modul._berichte({"ergebnisse": []}, im_prozess={"vis-9": ["Im Prozess X"]})
    assert "vis-9 (ohne Zeile im Bericht): Im Prozess X" in capsys.readouterr().out


# ====================================================================== der Messauftrag 308

def _messauftrag_308():
    treffer = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((WURZEL / "auftraege" / "offen").glob("auf-2026102*-*.json"))]
    treffer = [d for d in treffer if "Strang Kern" in d.get("beschreibung", "")]
    assert len(treffer) == 1, [t.get("auftrag_id") for t in treffer]
    return treffer[0]


def test_der_messauftrag_ist_gueltig_und_vollstaendig():
    daten = _messauftrag_308()
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa"
    text = daten["anweisung"]
    for stichwort in ("Kontrolle", "sSE", "nNW", "morgen", "abend", "bedeckt", "Seeds",
                      "Sichtbeton?", "Form wie Modell?", "Rundturm", "Naht?", "Tafel",
                      "no_grad", "VRAM", "Himmel", "EINBAU", "Vertragsfeld", "Knotenteil",
                      "NICHT", "WAS AM HEIM-PC JETZT ANDERS RECHNET", "bildpunktgleich",
                      "vis.umriss_halten", "vis.material_vorne"):
        assert stichwort in text, stichwort
    assert "FLUX.1-dev" in text
