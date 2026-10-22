"""N6 — eine Variante mit anderer Stimmung hält Himmel und Boden ihrer Grundlage nicht fest.

**Anlass (Mac-Demolauf 22.10.2026, Fund N6):** Die Variante «Mittag» rechnete auf dem
Abend-Grundbild (``vis.grundlage`` + ``vis.seed``, seit Protokoll 74 §229) und kam als blaue
Nachtstimmung zurück. «Umriss halten» (M2, Entscheid 126) hält ausserhalb des Hauses das
Cycles-Bild der Grundlage — Himmel und Boden der ANDEREN Stimmung —, und wo die Bestellung ein
Licht trägt, ersetzte der Heim-PC den Satz der Variante still durch den des Lichts.

Seither (``kosmo_szene.stimmung_der_variante``): Trägt der Prompt genau den Satz EINER anderen
Stimmung als das Licht, folgt das Licht der Variante, und eine bestellte Grundlage wird nicht
wiederverwendet, sondern für diese Stimmung neu gerechnet — auf dem Modell der alten.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, knotenweg, kosmo_szene, stimmung

from test_grundlage_varianten import _mit_schoenbild
from test_kettenlauf_26august import _auftragsordner, _kette, _lauf

KENNUNG = "gl-0123456789abcdef"
MITTAG_DE = "Mittagslicht, hohe Sonne, klarer Himmel"
ABEND_DE = "Abendstimmung, warmes Licht, leuchtende Fenster"


def _alle_himmel(tmp_path, monkeypatch):
    ordner = tmp_path / "himmel"
    ordner.mkdir(exist_ok=True)
    for p, e in stimmung.STIMMUNGEN.items():
        for a in ("2k", "4k"):
            (ordner / stimmung.dateiname(p, e["hdri"], a)).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))
    return ordner


def _szene(prompt, environment=None, **vis):
    render = {"samples": 8}
    if environment is not None:
        render["environment"] = environment
    return {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
            "render": render, "style": {"prompt": prompt}, "vis": vis}


def _lies(prompt, environment=None, **vis):
    return kosmo_szene.lies_szene(_szene(prompt, environment, **vis), streng=False)


# ====================================================================== die Regel

def test_mittag_auf_der_abend_grundlage_bekommt_eine_eigene(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(f"{MITTAG_DE}, ein Haus", {"preset": "abend"}, grundlage=KENNUNG, seed=7)

    assert s["umgebung"]["preset"] == "mittag"
    assert s["umgebung"]["hdri"] == stimmung.STIMMUNGEN["mittag"]["hdri"]
    assert s["grundlage"] is None, "die Abend-Grundlage wird nicht wiederverwendet"
    assert s["grundlage_verworfen"] == KENNUNG
    assert s["seed"] == 7, "der Startwert der Serie bleibt"
    assert s["umgebung_datei"] is not None, "Blender bekommt das Himmelsbild von Mittag"
    satz = next(w for w in s["warnungen"] if w.startswith(kosmo_szene.SATZ_STIMMUNG_DER_VARIANTE))
    assert "«Mittag»" in satz and "«Abendstimmung»" in satz and KENNUNG in satz
    zusatz = next(z for z in s["prompt_zusaetze"] if z["art"] == "stimmung")
    assert zusatz["preset"] == "mittag"
    assert "midday" in s["prompt"] and "evening" not in s["prompt"]
    assert not s["maengel"]


def test_ohne_grundlage_wird_die_variante_nicht_still_zum_licht(tmp_path, monkeypatch):
    """Bis N6 nahm der Heim-PC den Satz «Mittag» heraus und setzte den des Lichts (Abend)."""
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(f"{MITTAG_DE}, ein Haus", {"preset": "abend"})
    assert s["umgebung"]["preset"] == "mittag"
    assert s["grundlage_verworfen"] is None
    assert "midday" in s["prompt"]


def test_grundlage_ohne_licht_und_variante_mit_stimmung(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(f"{MITTAG_DE}, ein Haus", None, grundlage=KENNUNG)
    assert s["umgebung"]["preset"] == "mittag"
    assert s["grundlage"] is None and s["grundlage_verworfen"] == KENNUNG
    assert any("«ohne Stimmung»" in w for w in s["warnungen"])


def test_nur_die_drehung_bleibt(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(f"{MITTAG_DE}, ein Haus",
              {"preset": "abend", "hdri": "eigener_himmel", "intensitaet": 3.0,
               "rotationGrad": 40})
    assert s["umgebung"] == {"preset": "mittag", "hdri": stimmung.STIMMUNGEN["mittag"]["hdri"],
                             "intensitaet": stimmung.vorgabe_staerke("mittag"),
                             "rotationGrad": 40.0}


@pytest.mark.parametrize("prompt, environment, vis", [
    # dieselbe Stimmung — die Grundlage passt, wie seit §229
    (f"{ABEND_DE}, ein Haus", {"preset": "abend"}, {"grundlage": KENNUNG}),
    # ohne Licht und ohne Grundlage: das eigene Cycles-Bild, wie bisher
    (f"{MITTAG_DE}, ein Haus", None, {}),
    # kein ganzer Satz einer Stimmung und keine Grundlage — das Wort zaehlt nur bei einer
    # Variante (seit Befund 340, siehe test_licht_der_variante_340.py)
    ("ein Haus am Abend, evening", {"preset": "mittag"}, {}),
    # zwei Saetze — welcher gilt, wird nicht geraten
    (f"{MITTAG_DE}, {ABEND_DE}, ein Haus", {"preset": "morgen"}, {"grundlage": KENNUNG}),
    # «nur Grundlage» rechnet kein KI-Bild
    (f"{MITTAG_DE}, ein Haus", {"preset": "abend"}, {"skip": True}),
    # das Gipsmodell ist keine Lichtstimmung — nicht still dahin wechseln
    ("Weissmodell, neutrales Studiolicht, keine Materialien, ein Haus", {"preset": "abend"},
     {"grundlage": KENNUNG}),
])
def test_sonst_bleibt_alles_wie_bisher(tmp_path, monkeypatch, prompt, environment, vis):
    _alle_himmel(tmp_path, monkeypatch)
    s = _lies(prompt, environment, **vis)
    assert s["stimmung_der_variante"] is None
    assert s["grundlage_verworfen"] is None
    assert s["grundlage"] == vis.get("grundlage")
    if environment is not None:
        assert s["umgebung"]["preset"] == environment["preset"]
    assert not any(w.startswith(kosmo_szene.SATZ_STIMMUNG_DER_VARIANTE) for w in s["warnungen"])


def test_die_felder_sind_erklaert():
    for feld in ("grundlage_verworfen", "stimmung_der_variante"):
        assert feld in kosmo_szene.DURCHGEREICHT


# ====================================================================== der Lauf

def _in_ablage(tmp_path, job_id, *, environment, prompt, vis=None, mit_modell=True):
    """Ein Auftragsordner ``ablage/<job_id>`` — beide Auftraege in DERSELBEN Ablage."""
    zwischen = _auftragsordner(tmp_path / f"_{job_id}")
    ziel = tmp_path / "ablage" / job_id
    ziel.parent.mkdir(exist_ok=True)
    shutil.move(str(zwischen), ziel)
    zettel = json.loads((ziel / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    zettel["job_id"] = job_id
    (ziel / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel), encoding="utf-8")
    szene = json.loads((ziel / bruecke.DATEI_SZENE).read_text(encoding="utf-8"))
    szene["render"]["environment"] = environment
    szene["style"]["prompt"] = prompt
    szene["vis"].update(vis or {})
    if mit_modell:
        szene["geometry"]["path"] = str(ziel / bruecke.DATEI_MODELL)
    else:
        szene["geometry"] = {"path": "", "format": "glb"}
        (ziel / bruecke.DATEI_MODELL).unlink()
    (ziel / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    return ziel


def _grundlage_abend(tmp_path, protokoll, attrappen):
    ordner = _in_ablage(tmp_path, "vis-1-aaaaaa", environment={"preset": "abend"},
                        prompt=f"{ABEND_DE}, ein Haus", vis={"skip": True})
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return antwort["ergebnis"]["grundlage"]["id"]


def test_variante_mittag_rechnet_eine_eigene_grundlage(tmp_path, monkeypatch):
    himmel = _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_abend(tmp_path, protokoll, attrappen)
    blender_vorher = len(protokoll["multipass"])

    # Wie die Mac-Seite: Variante ohne Modelldatei, mit Kennung und EINEM Startwert.
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "abend"},
                        prompt=f"{MITTAG_DE}, ein Haus",
                        vis={"grundlage": kennung, "seed": 7}, mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    neu = protokoll["multipass"][blender_vorher:]
    assert neu, "Blender rechnet die Grundlage fuer Mittag neu"
    assert {Path(kw["umgebung_hdr"]).name for kw in neu} == \
        {stimmung.dateiname("mittag", stimmung.STIMMUNGEN["mittag"]["hdri"], "4k")}
    assert all(Path(kw["umgebung_hdr"]).parent == himmel for kw in neu)
    ergebnis = antwort["ergebnis"]
    assert ergebnis["grundlage"]["wiederverwendet"] is False
    assert ergebnis["grundlage"]["id"] != kennung
    assert ergebnis["angewandt"]["environment"]["preset"] == "mittag"
    assert {a.seed for a in protokoll["render"]} == {7}


def test_variante_abend_auf_der_abend_grundlage_bleibt_schnell(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_abend(tmp_path, protokoll, attrappen)
    blender_vorher = len(protokoll["multipass"])

    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "abend"},
                        prompt=f"{ABEND_DE}, ein Haus",
                        vis={"grundlage": kennung, "seed": 7}, mit_modell=False)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert antwort["ergebnis"]["grundlage"] == {"id": kennung, "wiederverwendet": True}


def test_ohne_modell_der_grundlage_endet_die_variante_mit_satz(tmp_path, monkeypatch):
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    ordner = _in_ablage(tmp_path, "vis-2-bbbbbb", environment={"preset": "abend"},
                        prompt=f"{MITTAG_DE}, ein Haus",
                        vis={"grundlage": KENNUNG}, mit_modell=False)
    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "eigene" in antwort["grund"] and "Grundlage rendern" in antwort["grund"]
    assert protokoll["multipass"] == []


def test_die_tuer_weist_die_variante_nicht_ab(tmp_path, monkeypatch):
    """Die Visbox-Tuer prueft «passt die Grundlage?» schon beim Anlegen (409). Eine Variante,
    der der Heim-PC eine eigene Grundlage rechnet, ist kein Widerspruch."""
    _alle_himmel(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    kennung = _grundlage_abend(tmp_path, protokoll, attrappen)
    ablage = tmp_path / "ablage"

    mittag = _szene(f"{MITTAG_DE}, ein Haus", {"preset": "abend"}, grundlage=kennung)
    assert knotenweg.grundlage_passt_nicht(ablage, mittag) is None
    # Eine echte Abweichung bleibt eine: andere Samples bei derselben Stimmung.
    anders = _szene(f"{ABEND_DE}, ein Haus", {"preset": "abend"}, grundlage=kennung)
    anders["render"]["samples"] = 64
    assert knotenweg.grundlage_passt_nicht(ablage, anders) is not None
