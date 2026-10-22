"""Befund 337 — eine Stoff-Variante ersetzt die Materialwahl der Fassade und rechnet ihr Grundbild neu.

**Anlass (Ergebnis auf-20261022-337):** Die Variante «Fassade aus Sichtbeton» kam in keinem Lauf
— weder ohne Grundbild (txt2img) noch mit Bildeingang 0,65. Der Prompt begann mit «monolithic
spruce timber battens building …»: «Material vorne» (Entscheid 126) nahm den Stoff der
Materialwahl (Fassade Holzlattung, mit der Grundlage bestellt), und das Grundbild trug die
Holztextur. Seither (``kosmo_szene.material_der_variante``): Nennt der Prompt einer Variante
genau einen Fassadenstoff, der nicht der gewählten Fassade entspricht, wird die Wahl der
Fassade ersetzt und die Grundlage neu gerechnet — wie bei der Stimmung (N6). Dach, Fenster,
Boden bleiben. Für Glas und Metall (kein Material der Bibliothek) folgt nur der Prompt.

Regel 3: alles synthetisch. Kein Netz, keine GPU.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene, materialwahl, sprache, stimmung

from test_grundlage_varianten import _mit_schoenbild
from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_knoten_material import _texturen

KENNUNG = "gl-0123456789abcdef"
MITTAG_DE = "Mittagslicht, hohe Sonne, klarer Himmel"
PROMPT_337 = f"{MITTAG_DE}, ein Haus am Hang"
PROMPT_337_S = f"{PROMPT_337}, Fassade aus Sichtbeton"
HOLZ = {"fassade": {"id": "holzlattung-fichte"}, "dach": {"id": "klinker"}}


def _alle_himmel(tmp_path, monkeypatch):
    ordner = tmp_path / "himmel"
    ordner.mkdir(exist_ok=True)
    for p, e in stimmung.STIMMUNGEN.items():
        for a in ("2k", "4k"):
            (ordner / stimmung.dateiname(p, e["hdri"], a)).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))


@pytest.fixture
def dateien(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    _texturen(tmp_path, monkeypatch)


def _szene(prompt, materialien=HOLZ, environment=None, **vis):
    render = {"samples": 8, "environment": environment or {"preset": "mittag"}}
    if materialien is not None:
        render["materialien"] = materialien
    return {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
            "render": render, "style": {"prompt": prompt}, "vis": vis}


def _lies(prompt, materialien=HOLZ, environment=None, **vis):
    return kosmo_szene.lies_szene(_szene(prompt, materialien, environment, **vis), streng=False)


def _en(text):
    return sprache.uebersetze(text)["uebersetzt"]


# ====================================================================== die Wortliste

@pytest.mark.parametrize("deutsch, kennung", [
    ("Fassade aus Sichtbeton", "sichtbeton-schalungsglatt"),
    ("Betonfassade", "sichtbeton-schalungsglatt"),
    ("Fassade aus Backstein", "backstein"),
    ("Klinkerfassade", "klinker"),
    ("Natursteinfassade", "sandstein"),
    ("verputzte Fassade", "verputz-weiss-glatt"),
    ("Putzfassade", "verputz-weiss-glatt"),
    ("Holzfassade", "holzlattung-fichte"),
    ("Sichtbeton mit Holzfenstern", "sichtbeton-schalungsglatt"),
])
def test_der_fassadenstoff_wird_erkannt(deutsch, kennung):
    wunsch = materialwahl.stoff_wunsch(_en(deutsch))
    assert [w["id"] for w in wunsch] == [kennung]


@pytest.mark.parametrize("englisch, familie", [
    ("facade of glass", "glas"), ("metal facade", "metall")])
def test_glas_und_metall_ohne_material_der_bibliothek(englisch, familie):
    assert materialwahl.stoff_wunsch(englisch) == [
        {"wort": englisch.split()[-1] if "of" in englisch else englisch.split()[0],
         "familie": familie, "id": None}]


@pytest.mark.parametrize("englisch", [
    "photorealistic architectural render of a house",   # «render» ist hier ein Rendering
    "house with large glass windows",                    # Glas der Fenster
    "zinc roof", "roof of zinc",                         # Stoff des Dachs
    "wood window, concrete plinth",                      # Fenster und Sockel
    "a quiet house",
])
def test_was_nicht_wand_ist_zaehlt_nicht(englisch):
    assert materialwahl.stoff_wunsch(englisch) == []


def test_jede_id_hat_eine_familie():
    assert set(materialwahl.FAMILIE) == set(materialwahl.BIBLIOTHEK)
    for familie, kennung, _ in materialwahl.STOFF_WUNSCH.values():
        assert kennung is None or materialwahl.FAMILIE[kennung] == familie


# ====================================================================== die Regel (lies_szene)

def test_sichtbeton_ersetzt_die_holzlattung_der_fassade(dateien):
    """Der Fall aus 337 (K-S): Grundlage mit Holzlattung, Prompt «Fassade aus Sichtbeton»."""
    s = _lies(PROMPT_337_S, grundlage=KENNUNG, seed=7)

    assert not s["maengel"], s["maengel"]
    assert s["materialien"]["fassade"]["id"] == "sichtbeton-schalungsglatt"
    assert s["materialien"]["dach"]["id"] == "klinker", "was nicht Wand ist, bleibt"
    assert s["grundlage"] is None and s["grundlage_verworfen"] == KENNUNG
    assert s["seed"] == 7
    assert s["materialien_dateien"]["fassade"]["asset"] == "Concrete002", \
        "Blender bekommt die Betontextur fuer das neue Grundbild"
    assert s["prompt"].startswith("monolithic smooth fair-faced concrete building")
    assert "spruce" not in s["prompt"] and "timber" not in s["prompt"]
    wunsch = s["material_der_variante"]
    assert wunsch["wunsch"] == "exposed concrete" and wunsch["vorher"] == "holzlattung-fichte"
    assert wunsch["ersetzung"] == kosmo_szene.ERSETZUNG_MATERIALWAHL
    satz = next(w for w in s["warnungen"]
                if w.startswith(kosmo_szene.SATZ_MATERIAL_DER_VARIANTE))
    assert "Holzlattung Fichte" in satz and KENNUNG in satz


def test_ohne_stoffwunsch_bleibt_alles_wie_337(dateien):
    """K in 337: derselbe Prompt ohne Stoff — die Grundlage passt, der Prompt beginnt mit Holz."""
    s = _lies(PROMPT_337, grundlage=KENNUNG, seed=7)
    assert s["material_der_variante"] is None
    assert s["grundlage"] == KENNUNG and s["grundlage_verworfen"] is None
    assert s["materialien"]["fassade"]["id"] == "holzlattung-fichte"
    assert s["prompt"].startswith("monolithic spruce timber battens building")


def test_ohne_materialwahl_bekommt_die_variante_eine(dateien):
    """Grundlage mit dem Material der Datei: die Fassade bekommt das Wunschmaterial."""
    s = _lies(PROMPT_337_S, materialien=None, grundlage=KENNUNG)
    assert s["materialien"] == {"fassade": dict(id="sichtbeton-schalungsglatt",
                                                massstab_m=1.0, drehungGrad=0.0, relief=0.6,
                                                toenung=None)}
    assert s["grundlage_verworfen"] == KENNUNG
    assert s["material_der_variante"]["vorher"] is None


def test_glas_nur_im_prompt(dateien):
    s = _lies(f"{PROMPT_337}, Fassade aus Glas", grundlage=KENNUNG)
    wunsch = s["material_der_variante"]
    assert wunsch["ersetzung"] == kosmo_szene.ERSETZUNG_NUR_PROMPT
    assert s["grundlage"] == KENNUNG, "kein Material der Bibliothek — das Grundbild bleibt"
    assert s["materialien"]["fassade"]["id"] == "holzlattung-fichte"
    assert s["prompt"].startswith("monolithic glass building")
    assert "spruce" not in s["prompt"]
    fassade = next(z for z in s["prompt_zusaetze"] if z.get("bauteil_art") == "fassade")
    assert fassade["weggelassen"] == "material_der_variante"
    assert any("kein Material der Bibliothek" in w for w in s["warnungen"])


@pytest.mark.parametrize("prompt, materialien, vis, environment", [
    # derselbe Stoff wie gewaehlt — die Grundlage passt
    (f"{PROMPT_337}, Holzfassade", HOLZ, {"grundlage": KENNUNG}, None),
    # zwei Stoffe — welcher gilt, wird nicht geraten
    (f"{PROMPT_337}, Fassade aus Sichtbeton und Backstein", HOLZ, {"grundlage": KENNUNG}, None),
    # keine Variante: ohne Grundlage gilt die Materialwahl (Material-Knoten)
    (PROMPT_337_S, HOLZ, {}, None),
    # «nur Grundlage» rechnet kein KI-Bild
    (PROMPT_337_S, HOLZ, {"skip": True}, None),
])
def test_sonst_bleibt_die_materialwahl(dateien, prompt, materialien, vis, environment):
    s = _lies(prompt, materialien, environment, **vis)
    assert s["materialien"]["fassade"]["id"] == "holzlattung-fichte"
    assert s["grundlage"] == vis.get("grundlage")
    assert s["grundlage_verworfen"] is None
    wunsch = s["material_der_variante"]
    assert wunsch is None or wunsch["ersetzung"] is None


def test_mehrere_stoffe_mit_satz(dateien):
    s = _lies(f"{PROMPT_337}, Fassade aus Sichtbeton und Backstein", grundlage=KENNUNG)
    assert "mehrere" in s["material_der_variante"]["grund"]
    assert any(w.startswith(kosmo_szene.SATZ_MATERIAL_DER_VARIANTE) for w in s["warnungen"])


def test_das_feld_ist_erklaert():
    assert "material_der_variante" in kosmo_szene.DURCHGEREICHT


# ====================================================================== der Lauf

def _in_ablage(tmp_path, job_id, *, prompt, vis=None, mit_modell=True, materialien=HOLZ):
    zwischen = _auftragsordner(tmp_path / f"_{job_id}")
    ziel = tmp_path / "ablage" / job_id
    ziel.parent.mkdir(exist_ok=True)
    shutil.move(str(zwischen), ziel)
    zettel = json.loads((ziel / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    zettel["job_id"] = job_id
    (ziel / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel), encoding="utf-8")
    szene = json.loads((ziel / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
    szene["render"]["environment"] = {"preset": "mittag"}
    szene["render"]["materialien"] = materialien
    szene["style"]["prompt"] = prompt
    szene["vis"].update(vis or {})
    if mit_modell:
        szene["geometry"]["path"] = str(ziel / bruecke.DATEI_MODELL)
    else:
        szene["geometry"] = {"path": "", "format": "glb"}
        (ziel / bruecke.DATEI_MODELL).unlink()
    (ziel / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    return ziel


def _grundlage_holz(tmp_path, attrappen):
    ordner = _in_ablage(tmp_path, "vis-1-aaaaaa", prompt=PROMPT_337, vis={"skip": True})
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return antwort["ergebnis"]["grundlage"]["id"]


def test_variante_sichtbeton_rechnet_eine_eigene_grundlage(tmp_path, monkeypatch, dateien):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_holz(tmp_path, attrappen)
    blender_vorher = len(protokoll["multipass"])
    ablage = tmp_path / "ablage"

    # Wie die Mac-Seite: Variante ohne Modelldatei, mit Kennung, Startwert und der Wahl der
    # Grundlage (sonst wiese der Heim-PC sie als «Materialien weichen ab» ab).
    roh = _szene(PROMPT_337_S, grundlage=kennung, seed=7)
    assert knotenweg.grundlage_passt_nicht(ablage, roh) is None, "die Tuer weist nicht ab"
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", prompt=PROMPT_337_S,
                        vis={"grundlage": kennung, "seed": 7}, mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    neu = protokoll["multipass"][blender_vorher:]
    assert neu, "Blender rechnet das Grundbild mit Sichtbeton neu"
    wahl = json.loads(Path(neu[0]["materialien_json"]).read_text(encoding="utf-8"))
    assert wahl["arten"]["fassade"]["id"] == "sichtbeton-schalungsglatt"
    assert wahl["arten"]["dach"]["id"] == "klinker"
    ergebnis = antwort["ergebnis"]
    assert ergebnis["grundlage"]["wiederverwendet"] is False
    assert ergebnis["grundlage"]["id"] != kennung
    angewandt = ergebnis["angewandt"]
    assert angewandt["materialien"]["fassade"]["label"] == "Sichtbeton, schalungsglatt"
    wunsch = angewandt["variante"]["material_wunsch"]
    assert wunsch == {"wunsch": "exposed concrete", "familie": "beton",
                      "id": "sichtbeton-schalungsglatt", "vorher": "holzlattung-fichte",
                      "ersetzung": "materialwahl", "grundlage_verworfen": kennung,
                      "grund": None}
    assert all(a.prompt.startswith("monolithic smooth fair-faced concrete")
               for a in protokoll["render"][-1:])
    assert {a.seed for a in protokoll["render"]} >= {7}


def test_variante_ohne_stoff_bleibt_schnell(tmp_path, monkeypatch, dateien):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_holz(tmp_path, attrappen)
    blender_vorher = len(protokoll["multipass"])
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", prompt=PROMPT_337,
                        vis={"grundlage": kennung, "seed": 7}, mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert antwort["ergebnis"]["grundlage"] == {"id": kennung, "wiederverwendet": True}
    assert "variante" not in antwort["ergebnis"]["angewandt"]
