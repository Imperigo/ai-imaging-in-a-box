"""Befund 340 — die Variante «Licht abend» auf der Mittag-Grundlage wird nicht mehr abgewiesen.

**Anlass (Ergebnis auf-20261022-340, ROT, demo-kritisch):** Der Mac bestellte eine Variante mit
``render.environment.preset`` «abend» und dem Prompt «Abendstimmung, warmes Licht, …» auf einer
Grundlage, die mit Mittag gerechnet war. Die Visbox-Tür antwortete 409 «Stimmung weicht ab», es
entstand kein Auftrag. N6 (``kosmo_szene.stimmung_der_variante``) half nicht: Es erkannte die
Stimmung nur am GANZEN Satz der Tabelle, und nur, wenn sie vom bestellten Licht abwich — hier
war das bestellte Licht selbst das abweichende.

Seither:

* ``kosmo_szene.licht_der_variante`` — weicht das bestellte Licht von dem der Grundlage ab, wird
  die Grundlage verworfen und mit dem bestellten Licht neu gerechnet (gleiches Modell, gleiche
  Kamera), statt 409. Die Stimmung der Grundlage kennen die Tür
  (``knotenweg.grundlage_passt_nicht``) und die Brücke (``bruecke.lies_auftrag``) aus dem
  Auftrag, der die Grundlage gerechnet hat.
* Das Stimmungswort zählt bei einer Variante (``stimmung.stimmungen_im_text``): «Abendstimmung»
  allein, «evening mood».
* ``angewandt.variante.stimmung`` und der Satz «STIMMUNG DER VARIANTE» im Ergebnis.
* Der Satz des Rückfalls bei ``vis.bildeingang: false`` sagt, dass der Bildeingang abgeschaltet
  wurde (nicht «bestellt image_edit (denoise 0.6)»).

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene, stimmung

from test_grundlage_varianten import _mit_schoenbild
from test_kettenlauf_26august import _kette, _lauf
from test_n6_stimmung_der_variante import _alle_himmel, _in_ablage, _szene

KENNUNG = "gl-0123456789abcdef"
MITTAG_DE = "Mittagslicht, hohe Sonne, klarer Himmel"
MAC_PROMPT = "Abendstimmung, warmes Licht, ein Haus am Hang"


def _lies(prompt, environment=None, **wie):
    vis = wie.pop("vis", {})
    return kosmo_szene.lies_szene(_szene(prompt, environment, **vis), streng=False, **wie)


def _mittag_gelesen():
    return kosmo_szene.umgebung_aus_szene({"preset": "mittag"}, grundlage=KENNUNG)["umgebung"]


# ====================================================================== das Stimmungswort

@pytest.mark.parametrize("en, de, erwartet", [
    ("evening mood, warm light, a house", None, ("abend",)),
    ("a house in the afternoon", None, ()),                  # «afternoon» ist nicht «noon»
    ("a misty valley", None, ("nebel",)),
    ("blue hour, a house", None, ("blaue-stunde",)),
    ("snowy roofs", None, ("winter",)),
    ("a house", "ein Haus abends", ("abend",)),             # deutsch, wo das Glossar fehlt
    ("a house", "ein Haus am Nachmittag", ()),               # «Nachmittag» ist nicht «Mittag»
    ("midday, evening", None, ("mittag", "abend")),          # zwei: nicht eindeutig
    ("white plaster study model", None, ()),                 # das Gipsmodell nie aus einem Wort
])
def test_stimmungswoerter(en, de, erwartet):
    assert stimmung.stimmungen_im_text(en, de) == erwartet


def test_das_wort_zaehlt_bei_einer_variante(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("Abendstimmung, ein Haus", {"preset": "mittag"}, vis={"grundlage": KENNUNG})
    v = s["stimmung_der_variante"]
    assert v["preset"] == "abend" and v["quelle"] == kosmo_szene.STIMMUNG_QUELLE_WORT
    assert s["grundlage"] is None and s["grundlage_verworfen"] == KENNUNG
    assert s["umgebung"]["preset"] == "abend"
    assert s["umgebung_datei"] is not None, "Blender bekommt das Himmelsbild von Abend"


def test_evening_mood_auf_mittag(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("evening mood", {"preset": "mittag"}, vis={"grundlage": KENNUNG})
    assert s["umgebung"]["preset"] == "abend" and s["grundlage_verworfen"] == KENNUNG


def test_ohne_bestelltes_licht_zaehlt_das_wort_nicht(tmp_path, monkeypatch):
    """«overcast sky» in einem freien Prompt auf einer Grundlage ohne Stimmung ist ein Wort,
    keine Bestellung — sonst rechneten viele Varianten still ein neues Grundbild."""
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("overcast sky, no people", None, vis={"grundlage": KENNUNG})
    assert s["stimmung_der_variante"] is None and s["grundlage"] == KENNUNG


def test_ohne_grundlage_zaehlt_das_wort_nicht(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("Abendstimmung, ein Haus", {"preset": "mittag"})
    assert s["stimmung_der_variante"] is None and s["umgebung"]["preset"] == "mittag"


# ====================================================================== das Licht der Variante

def test_licht_abend_auf_mittag_grundlage_verwirft_sie(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(MAC_PROMPT, {"preset": "abend"}, vis={"grundlage": KENNUNG, "seed": 7},
              umgebung_der_grundlage=_mittag_gelesen())
    v = s["stimmung_der_variante"]
    assert v["quelle"] == kosmo_szene.STIMMUNG_QUELLE_LICHT
    assert v["preset"] == "abend" and v["licht_der_grundlage"] == "mittag"
    assert s["grundlage"] is None and s["grundlage_verworfen"] == KENNUNG
    assert s["seed"] == 7
    assert s["umgebung"]["preset"] == "abend" and s["umgebung_datei"] is not None
    satz = next(w for w in s["warnungen"]
                if w.startswith(kosmo_szene.SATZ_STIMMUNG_DER_VARIANTE))
    assert "«Abendstimmung»" in satz and "«Mittag»" in satz and KENNUNG in satz
    assert not s["maengel"]


@pytest.mark.parametrize("umgebung", ["gleich", kosmo_szene.UMGEBUNG_UNBEKANNT])
def test_gleiches_oder_unbekanntes_licht_behaelt_die_grundlage(tmp_path, monkeypatch, umgebung):
    _alle_himmel(tmp_path, monkeypatch)
    if umgebung == "gleich":
        umgebung = _mittag_gelesen()
    s = _lies(f"{MITTAG_DE}, ein Haus", {"preset": "mittag"}, vis={"grundlage": KENNUNG},
              umgebung_der_grundlage=umgebung)
    assert s["grundlage"] == KENNUNG and s["stimmung_der_variante"] is None


def test_variante_ohne_licht_bleibt_wie_sie_war(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies("ein Haus", None, vis={"grundlage": KENNUNG},
              umgebung_der_grundlage=_mittag_gelesen())
    assert s["grundlage"] == KENNUNG and s["stimmung_der_variante"] is None


# ====================================================================== Tür und Lauf

def _grundlage_mittag(tmp_path, attrappen):
    ordner = _in_ablage(tmp_path, "vis-1-aaaaaa", environment={"preset": "mittag"},
                        prompt=f"{MITTAG_DE}, ein Haus", vis={"skip": True})
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return antwort["ergebnis"]["grundlage"]["id"]


def test_die_tuer_nimmt_die_mac_variante_an(tmp_path, monkeypatch):
    """GEGEN ALT ROT: Bis Befund 340 war das 409 «Stimmung weicht ab»."""
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    kennung = _grundlage_mittag(tmp_path, _mit_schoenbild(attrappen))
    ablage = tmp_path / "ablage"
    mac = _szene(MAC_PROMPT, {"preset": "abend"}, grundlage=kennung, seed=7)
    assert knotenweg.grundlage_passt_nicht(ablage, mac) is None
    zettel = knotenweg.lege_an(ablage, mac, None, kennung="vis-1792500100-bbbbbb")
    assert zettel["status"] == bruecke.STATUS_AWAITING
    # Eine echte Abweichung bleibt eine: andere Samples bei derselben Stimmung.
    anders = _szene(f"{MITTAG_DE}, ein Haus", {"preset": "mittag"}, grundlage=kennung)
    anders["render"]["samples"] = 64
    assert "Samples" in knotenweg.grundlage_passt_nicht(ablage, anders)


def test_lauf_licht_abend_rechnet_eine_eigene_grundlage(tmp_path, monkeypatch):
    himmel = _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_mittag(tmp_path, attrappen)
    blender_vorher = len(protokoll["multipass"])

    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "abend"},
                        prompt=MAC_PROMPT, vis={"grundlage": kennung, "seed": 7},
                        mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    neu = protokoll["multipass"][blender_vorher:]
    assert neu, "Blender rechnet die Grundlage fuer Abend neu"
    assert {Path(kw["umgebung_hdr"]).name for kw in neu} == \
        {stimmung.dateiname("abend", stimmung.STIMMUNGEN["abend"]["hdri"], "4k")}
    assert all(Path(kw["umgebung_hdr"]).parent == himmel for kw in neu)
    ergebnis = antwort["ergebnis"]
    assert ergebnis["grundlage"]["wiederverwendet"] is False
    assert ergebnis["grundlage"]["id"] != kennung
    assert ergebnis["angewandt"]["environment"]["preset"] == "abend"
    variante = ergebnis["angewandt"]["variante"]
    assert variante["stimmung"]["quelle"] == kosmo_szene.STIMMUNG_QUELLE_LICHT
    assert variante["stimmung"]["grundlage_verworfen"] == kennung
    assert variante["satz"].startswith(kosmo_szene.SATZ_STIMMUNG_DER_VARIANTE)
    hinweise = ergebnis["qa"]["verdict"].get("hinweise", [])
    assert any(h.startswith(kosmo_szene.SATZ_STIMMUNG_DER_VARIANTE) for h in hinweise), \
        "der Satz steht im Ergebnis, nicht nur in befund.json"
    assert {a.seed for a in protokoll["render"]} >= {7}


def test_lauf_mittag_mit_evening_mood(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_mittag(tmp_path, attrappen)
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "mittag"},
                        prompt="evening mood", vis={"grundlage": kennung, "seed": 7},
                        mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = antwort["ergebnis"]
    assert ergebnis["grundlage"]["wiederverwendet"] is False
    assert ergebnis["angewandt"]["environment"]["preset"] == "abend"
    assert ergebnis["angewandt"]["variante"]["stimmung"]["quelle"] == \
        kosmo_szene.STIMMUNG_QUELLE_WORT


def test_gegenprobe_gleiche_stimmung_nimmt_die_grundlage(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_mittag(tmp_path, attrappen)
    blender_vorher = len(protokoll["multipass"])
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "mittag"},
                        prompt=f"{MITTAG_DE}, ein Haus", vis={"grundlage": kennung, "seed": 7},
                        mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert antwort["ergebnis"]["grundlage"] == {"id": kennung, "wiederverwendet": True}
    assert "variante" not in antwort["ergebnis"]["angewandt"]


# ====================================================================== der Satz des Rückfalls

def test_rueckfall_satz_nennt_den_abgeschalteten_bildeingang():
    erg = {"modus_bestellt": "image_edit", "modus_gerechnet": "txt2img",
           "parameter": {"denoise": 0.6}}
    alt = abholer.ki_vermerk(erg)
    assert "bestellt 'image_edit' (denoise 0.6)" in alt["warnung"]
    neu = abholer.ki_vermerk(erg, bildeingang_abgeschaltet=True)
    assert neu["warnung"].startswith(abholer.SATZ_KI_RUECKFALL)
    assert "Bildeingang ist abgeschaltet" in neu["warnung"]
    assert "image_edit" not in neu["warnung"] and "0.6" not in neu["warnung"]
    assert neu["denoise_bestellt"] == 0.6, "die Zahlen bleiben, nur der Satz aendert sich"


def test_abgeschaltet_nur_wenn_false_bestellt():
    bestellt = {"messschalter": {"bildeingang": {"herkunft": kosmo_szene.HERKUNFT_BESTELLT}},
                "bildeingang": None}
    assert abholer._bildeingang_abgeschaltet(bestellt) is True
    assert abholer._bildeingang_abgeschaltet(dict(bestellt, bildeingang=0.5)) is False
    vorgabe = {"messschalter": {"bildeingang": {"herkunft": "vorgabe"}}, "bildeingang": 0.5}
    assert abholer._bildeingang_abgeschaltet(vorgabe) is False
    assert abholer._bildeingang_abgeschaltet({}) is False


def test_satz_der_szene_traegt_beide():
    angewandt = {"variante": {"satz": "MATERIAL DER VARIANTE: x",
                              "stimmung": {"satz": "STIMMUNG DER VARIANTE: y"}}}
    assert kosmo_szene.ergebnis_saetze_der_szene(angewandt) == [
        "MATERIAL DER VARIANTE: x", "STIMMUNG DER VARIANTE: y"]
    json.dumps(angewandt)
