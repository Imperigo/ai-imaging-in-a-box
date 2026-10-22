"""Der Boden bis zum Horizont so hell und so gefärbt wie die Platte — Ergebnis ``auf-20261022-335``.

**Befund 335 (Heim-PC, Visbox 0.3.40):** Der Boden unter dem Horizont wirkte (B1), aber

* der Mittag-Kontrast fiel von −27,7 (334) auf −13,9 — Warnung «HAUS KAUM SICHTBAR»: der
  dunkle Weltboden neben dem Haus zog das Mittel des Hintergrunds zum Haus hin;
* zwischen Platte (Grau 113 mittag, 101 abend) und Weltboden stand eine Naht (Unterkante
  −31,5 bzw. −74,4 Grauwerte);
* der Boden war ein ebenes dunkles Blaugrau (mittag RGB 34/48/62) und las sich wie Wasser.

**Ursache:** Albedo × mittlerer Himmel ist nur das Fülllicht, in der Farbe des Himmels — die
Platte bekommt dazu die Sonne (mittags gut vier Fünftel ihres Lichts). Und die Farbe hing am
Faktor der Vorprobe, die den sichtbaren Himmel stellt, nicht das Licht auf dem Boden.

**Fix:** Der Boden ist die Platte in der Ferne — Albedo × (Fülllicht + Sonne) / π, gestellt
auf die Stärke des Fülllichts; nach der Vorprobe höchstens so hell wie die Platte
(``stimmung.boden_zum_faktor``). Nur der Kamerastrahl der Welt: Licht, Masken, Tiefe und
ID-Pass bleiben.

Ohne GPU und ohne Blender (Regel 2); alle Zahlen sind Messwerte aus 294/334/335 oder
synthetisch (Regel 3).
"""
from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest

from aiimaging import abholer, stimmung

from test_boden_bis_horizont_auf334 import (_bauen, _farbe, _szene)
from test_heimfehler_auf292 import RUNNER, _runner

L = stimmung.leuchtdichte

# ============================================================ die Messwerte aus 294 und 335
#
# mittag: Lampe 3,769152 bei 43,591° (294), sonnen_staerke 3,0 → e_himmel_h = 1,256;
#         fuell 0,45, staerke 1,0; Vorprobe-Faktor 2,2222 (335); Belichtung −1,0.
# abend:  Lampe 11,906489 bei 4,22° (294), sonnen_staerke 3,5 → e_himmel_h = 3,402;
#         fuell 0,3, staerke 1,0; Vorprobe-Faktor 0,5, Kamerastrahl 0,15 (335); Belichtung −0,5.
# Horizontfarbe und alter Boden (= 0,3 × mittlerer Himmel, getönt) stehen im Bericht von 335.

MESSUNG = {
    "mittag": {"horizont": [0.308451, 0.433655, 0.614276],
               "boden_335": [0.064291, 0.091915, 0.137931],
               "energie": 3.769152, "hoehe": 43.591, "sonnen_staerke": 3.0, "fuell": 0.45,
               "faktor": 2.2222, "k_kamera": 1.0, "belichtung_ev": -1.0,
               "platte_grau": 113.2, "boden_grau_335": 45.4, "dunst_grau_335": 84.1,
               "kontrast_335": -13.9},
    "abend": {"horizont": [1.064987, 0.702654, 0.701873],
              "boden_335": [0.315293, 0.236634, 0.271458],
              "energie": 11.906489, "hoehe": 4.22, "sonnen_staerke": 3.5, "fuell": 0.3,
              "faktor": 0.5, "k_kamera": 0.15, "belichtung_ev": -0.5,
              "platte_grau": 101.0, "boden_grau_335": 31.0, "dunst_grau_335": 49.7,
              "kontrast_335": 35.7},
}


def _boden_neu(preset):
    m = MESSUNG[preset]
    mittel = [b / 0.3 for b in m["boden_335"]]             # getönter mittlerer Himmel
    zenit = [2 * x - h for x, h in zip(mittel, m["horizont"])]
    e_h = m["energie"] / m["sonnen_staerke"]
    lampe = {"energie": m["energie"], "hoehe_grad": m["hoehe"], "farbe": [1.0, 1.0, 1.0]}
    return stimmung.boden_bis_horizont(m["horizont"], zenit, albedo=[0.3] * 3, lampe=lampe,
                                       e_himmel_h=e_h, staerke=1.0, fuell_staerke=m["fuell"])


def _platte(preset):
    """Leuchtdichte der unbeschatteten Platte: Albedo × (Füll + Sonne × sin h) / π."""
    m = MESSUNG[preset]
    e_h = m["energie"] / m["sonnen_staerke"]
    e = e_h * m["fuell"] + m["energie"] * math.sin(math.radians(m["hoehe"]))
    return 0.3 * e / math.pi


# ============================================================ 1 · die Bodenfarbe, reine Rechnung


def test_der_boden_hat_das_licht_der_platte():
    """Mit der Stärke des Fülllichts multipliziert: genau die Leuchtdichte der Platte."""
    for preset, m in MESSUNG.items():
        boden = _boden_neu(preset)
        assert boden["weg"] == "platte" and boden["fassung"] == stimmung.BODEN_FASSUNG
        assert L(boden["boden"]) * 1.0 * m["fuell"] == pytest.approx(_platte(preset), rel=1e-4)
        assert boden["albedo"] == [0.3] * 3
    # Mittags traegt die Sonne den Grossteil, abends knapp die Haelfte.
    assert _boden_neu("mittag")["anteil_sonne"] == pytest.approx(0.82, abs=0.01)
    assert _boden_neu("abend")["anteil_sonne"] == pytest.approx(0.46, abs=0.01)


def test_der_boden_ist_nicht_mehr_himmelsgetoent():
    """335: mittag RGB 34/48/62 (Blau 1,8 × Rot). Jetzt fast neutral wie die Platte."""
    alt = MESSUNG["mittag"]["boden_335"]
    neu = _boden_neu("mittag")["boden"]
    assert alt[2] / alt[0] > 2.0
    assert neu[2] / neu[0] < 1.2


def test_ohne_licht_bleibt_der_boden_von_334():
    """Rueckfall (keine Sonnenanalyse): Albedo × mittlerer Himmel × Toenung, Wort fuer Wort."""
    aus = stimmung.boden_bis_horizont([0.4, 0.5, 0.6], [0.2, 0.3, 0.8], albedo=[0.3] * 3,
                                      toenung=[1.0, 0.9, 0.8])
    assert aus["weg"] == "himmel"
    assert aus["boden"] == [pytest.approx(0.09), pytest.approx(0.108), pytest.approx(0.168)]
    for kaputt in ({"lampe": {"energie": 1.0}}, {"lampe": None, "e_himmel_h": 1.0},
                   {"lampe": {"energie": 1.0, "hoehe_grad": 30, "farbe": [1, 1, 1]},
                    "e_himmel_h": 1.0, "staerke": 1.0, "fuell_staerke": 0.0}):
        assert stimmung.boden_bis_horizont([0.4] * 3, [0.2] * 3, **kaputt)["weg"] == "himmel"


def test_der_faktor_der_vorprobe_macht_den_boden_nie_heller_als_die_platte():
    assert stimmung.boden_zum_faktor([0.6, 0.6, 0.6], 2.0) == [0.3, 0.3, 0.3]
    assert stimmung.boden_zum_faktor([0.6, 0.6, 0.6], 0.5) == [0.6, 0.6, 0.6]
    assert stimmung.boden_zum_faktor([0.6, 0.6, 0.6], None) == [0.6, 0.6, 0.6]
    for preset, m in MESSUNG.items():
        farbe = stimmung.boden_zum_faktor(_boden_neu(preset)["boden"], m["faktor"])
        sichtbar = L(farbe) * m["fuell"] * m["faktor"]       # Farbe × Staerke nachher
        assert sichtbar == pytest.approx(_platte(preset) * min(1.0, m["faktor"]), rel=1e-4)


# ============================================================ 2 · die Rechnung mit 335

#: Die Tonwertkurve am Heim-PC, abgelesen an fünf Messpunkten aus 335 (Leuchtdichte nach
#: Belichtung → Grauwert): Weltboden abend/mittag, Platte abend/mittag (Platte mit ihrem
#: Schattenanteil, 294: 11 %), Himmel am Horizont mittag. Dazwischen linear in Blenden.
TONWERT = [(0.0272, 31.0), (0.0447, 45.4), (0.110, 101.0), (0.137, 113.2), (0.210, 131.0)]


def _grau(lum):
    pkt = [(math.log2(x), g) for x, g in TONWERT]
    e = math.log2(lum)
    for (e0, g0), (e1, g1) in zip(pkt, pkt[1:]):
        if e <= e1 or (e1, g1) == pkt[-1]:
            return g0 + (e - e0) / (e1 - e0) * (g1 - g0)
    return pkt[-1][1]


#: Anteil des Weltbodens am Hintergrund neben dem Haus — aus 334 → 335 mittag:
#: Kontrast −27,7 → −13,9 (+13,8) bei Weltboden unter dem Horizont 93,1 → 54,9 (−38,2).
ANTEIL_BODEN = 13.8 / 38.2


def _kontrast_neu(preset):
    m = MESSUNG[preset]
    farbe = stimmung.boden_zum_faktor(_boden_neu(preset)["boden"], m["faktor"])
    sichtbar = L(farbe) * m["fuell"] * m["faktor"] * 2.0 ** m["belichtung_ev"]
    boden = _grau(sichtbar)
    dunst = m["dunst_grau_335"] + (boden - m["boden_grau_335"]) / 2   # halber Weg im Band
    unten = (145920 * boden + 47716 * dunst) / 193636                  # Pixel aus 335
    unten_335 = (145920 * m["boden_grau_335"] + 47716 * m["dunst_grau_335"]) / 193636
    return m["kontrast_335"] - ANTEIL_BODEN * (unten - unten_335), boden


def test_der_mittag_kontrast_steigt_wieder_ueber_die_schwelle():
    """Hintergrund heller → weiter weg vom (dunkleren) Haus: −13,9 → rund −37."""
    kontrast, boden = _kontrast_neu("mittag")
    assert boden == pytest.approx(MESSUNG["mittag"]["platte_grau"], abs=6), "Naht ~0"
    assert kontrast < -stimmung.KONTRAST_SCHWELLE - 10
    assert kontrast < -27.7, "auch weiter vom Haus als 334"


def test_abends_bleibt_der_boden_daemmrig_und_das_haus_sichtbar():
    """Abends eine Blende unter der Platte: Naht etwa halbiert, Kontrast bleibt ueber 20."""
    kontrast, boden = _kontrast_neu("abend")
    m = MESSUNG["abend"]
    assert m["boden_grau_335"] + 25 < boden < m["platte_grau"] - 25
    naht_335 = 74.4
    assert m["platte_grau"] - boden < naht_335 * 0.6
    assert kontrast > stimmung.KONTRAST_SCHWELLE
    # Gegenprobe: der Boden auf Plattenhoehe haette den Abend unter die Schwelle gedrueckt.
    platte_sichtbar = _platte("abend") * 2.0 ** m["belichtung_ev"]
    dunst = m["dunst_grau_335"] + (_grau(platte_sichtbar) - m["boden_grau_335"]) / 2
    unten = (145920 * _grau(platte_sichtbar) + 47716 * dunst) / 193636
    unten_335 = (145920 * m["boden_grau_335"] + 47716 * m["dunst_grau_335"]) / 193636
    assert m["kontrast_335"] - ANTEIL_BODEN * (unten - unten_335) < stimmung.KONTRAST_SCHWELLE


# ============================================================ 3 · Knotenbaum und Vorprobe


def test_die_bodenfarbe_steht_in_einem_eigenen_knoten(monkeypatch):
    boden = _boden_neu("mittag")
    modul, baum, grund, _ = _bauen(monkeypatch, boden)
    knoten = next(k for k in baum.knoten if k.name == modul.BODEN_FARBE)
    assert knoten.art == "ShaderNodeRGB"
    assert _farbe(baum, grund, -0.5) == pytest.approx(boden["boden"])
    # Die Vorprobe stellt ihn nach — der Kamerastrahl folgt.
    welt = SimpleNamespace(node_tree=SimpleNamespace(nodes=SimpleNamespace(
        get=lambda name: knoten if name == modul.BODEN_FARBE else None)))
    befund = modul._boden_nachstellen(welt, stimmung, 2.0)
    assert befund["boden_nach_vorprobe"] == pytest.approx([c / 2 for c in boden["boden"]], abs=1e-6)
    assert _farbe(baum, grund, -0.5) == pytest.approx([c / 2 for c in boden["boden"]], abs=1e-6)
    assert modul._boden_nachstellen(welt, stimmung, 0.5)["boden_nach_vorprobe"] == \
        pytest.approx([c / 2 for c in boden["boden"]], abs=1e-6), "abends: unveraendert"


def test_ohne_bodenknoten_stellt_die_vorprobe_nichts(monkeypatch):
    modul, _ = _runner(monkeypatch)
    leer = SimpleNamespace(node_tree=SimpleNamespace(nodes=SimpleNamespace(get=lambda n: None)))
    assert modul._boden_nachstellen(leer, stimmung, 2.0) == {}
    assert modul._boden_nachstellen(SimpleNamespace(), stimmung, 2.0) == {}


def test_die_vorprobe_ruft_den_boden_nach_der_staerke():
    quelle = RUNNER.read_text(encoding="utf-8")
    vorprobe = quelle[quelle.index("def _hintergrund_abstimmen"):]
    vorprobe = vorprobe[:vorprobe.index("\ndef ")]
    assert (vorprobe.index('grund.inputs["Strength"].default_value = staerke * abstand')
            < vorprobe.index("_boden_nachstellen(welt, modul, abstand[\"faktor\"])"))


def test_der_runner_nimmt_die_lampe_der_stimmung(monkeypatch):
    modul, _ = _runner(monkeypatch)
    licht = dict(stimmung.licht_der_stimmung("mittag"), himmel_sichtbar=True,
                 boden_bis_horizont=True)
    sonne = {"gefunden": True, "richtung_bild": [0.5, -0.5, math.sin(math.radians(43.591))],
             "farbe": [1.0, 1.0, 1.0], "e_himmel_h": 1.256384}
    farben = {"horizont": [0.3, 0.4, 0.6], "zenit": [0.1, 0.2, 0.3], "sonne": sonne}
    boden = modul._boden_der_welt(farben, None, licht, 1.0)
    lampe = stimmung.lampe_aus_himmel(sonne, licht, staerke=1.0)
    erwartet = stimmung.boden_bis_horizont(
        farben["horizont"], farben["zenit"], albedo=licht["gelaende_grau"], lampe=lampe,
        e_himmel_h=1.256384, staerke=1.0, fuell_staerke=licht["fuell_staerke"])
    assert boden == erwartet and boden["weg"] == "platte"
    # Ohne Sonnenanalyse (Rueckfall des Himmelsbilds): der Boden von 334.
    assert modul._boden_der_welt(dict(farben, sonne={}), None, licht, 1.0)["weg"] == "himmel"


# ============================================================ 4 · neues Lichtdatum


def test_die_fassung_reist_als_lichtdatum(tmp_path):
    """Neues Lichtdatum = neue Grundlage, kein Zwischenspeicher-Treffer mit dem Boden von 335."""
    for preset in ("mittag", "abend"):
        ohne = json.loads(abholer.umgebung_einstellungen(_szene(tmp_path, preset))
                          ["umgebung_licht"])
        assert "boden_fassung" not in ohne
        mit = json.loads(abholer.umgebung_einstellungen(
            dict(_szene(tmp_path, preset), himmel_sichtbar=True))["umgebung_licht"])
        # Seit 338 (Ergebnis 336) die naechste Fassung — tests/test_boden_naht_abend_auf336.py.
        assert mit["boden_fassung"] == stimmung.BODEN_FASSUNG != "platte-336"
