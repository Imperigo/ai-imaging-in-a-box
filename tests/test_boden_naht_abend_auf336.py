"""Die Abend-Naht an der Plattenunterkante — Ergebnis ``auf-20261022-336``, Auftrag 338.

**Befund 336 (Heim-PC, Visbox 0.3.41):** Boden wie die Platte wirkt — mittags Naht +0,9,
Kontrast −30,3, keine Warnung. **Rot blieb N2 abends:** Naht an der Plattenunterkante −57,8
Grauwerte (Grenze 45; 335: −74,4; erwartet etwa −35). Abend-Kontrast 27,9 (Schwelle 20).

**Ursache:** Abends dunkelt die Vorprobe den Hintergrund mit Faktor 0,5 — der ganze Weltboden
stand eine Blende unter der Platte. Die Unterkante liegt bei dieser Kamera rund 3,8° unter dem
Horizont, mitten im Dunstband (von 335 auf 336 stieg die Welt an der Kante um 16,6, das
Dunstband im Mittel um 15,5, der tiefe Boden um 28,5 — die Kante folgt dem Dunstband).

**Fix (Fassung ``platte-338``):** Der Boden hat zwei Enden. Bis :data:`stimmung.BODEN_FERN_GRAD`
(12°) unter dem Horizont geht der nahe, dämmrige Boden in den fernen über, der so hell ist wie
die Platte (``stimmung.boden_fern_zum_faktor``). Mittags (Faktor > 1) sind beide gleich.
Platte, Licht, Tiefe, ID-Pass und Masken bleiben; nur der Kamerastrahl der Welt.

Ohne GPU und ohne Blender (Regel 2); alle Zahlen sind Messwerte aus 335/336 oder synthetisch
(Regel 3).
"""
from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest

from aiimaging import abholer, stimmung

from test_boden_bis_horizont_auf334 import _bauen, _farbe, _szene
from test_boden_wie_platte_auf335 import _boden_neu
from test_heimfehler_auf292 import _runner

L = stimmung.leuchtdichte
GRENZE_NAHT = 45.0

# ============================================================ die Messwerte aus 335 und 336 (abend)
#
# Leuchtdichte nach Stärke und Belichtung (Rec. 709, linear):
#   Boden 336 = L(0,8246/0,55/0,4681) × 0,15 × 2^−0,5 = 0,0639  → Grau 59,5 (tiefer als 6°)
#   Boden 335 = L(0,3153/0,2366/0,2715) × 0,15 × 2^−0,5 = 0,0271 → Grau 31,0
#   Dunst    = L(1,065/0,7027/0,7019) × 0,15 × 2^−0,5 = 0,0825 (Horizontfarbe, in beiden gleich)
# Dunstband 336 Grau 65,2. Naht an der Unterkante 335 −74,4, 336 −57,8; Kontrast 336 27,9.
# Pixel: Dunstband 47 716, Boden tiefer als 6° 145 920; Horizont Zeile 349,6 von 600;
# Brennweite 24 mm bei 960 px Breite = 640 px (6° = 67 px, wie 335 gemessen).

B_336, B_335, DUNST = 0.0639, 0.0271, 0.0825
GRAU_B_336 = 59.5
F_PX, ZEILEN_UNTER_HORIZONT = 640.0, 600 - 349.6
KONTRAST_336, NAHT_336, NAHT_335 = 27.9, -57.8, -74.4

#: Die Tonwertkurve am Heim-PC abends, als Potenz um den Boden von 336: Grau ∝ L^γ.
#: γ = 0,76 aus Boden 335 → 336 (31,0 → 59,5; trifft auch das Dunstband: 65,9 statt 65,2);
#: γ = 0,973, falls die Platte (Grau 101) unbeschattet bei 0,110 läge (Probe 335). Beide
#: Kurven werden gerechnet — die flachere ist für die Naht ungünstig, die steilere für den
#: Kontrast.
GAMMAS = (0.76, 0.973)

#: Der Anteil des Dunsts an der Kante: so, dass 335 → 336 die Kante um 16,6 steigt.
T_KANTE = 0.37


def _grau(lum, g=0.76):
    return GRAU_B_336 * (lum / B_336) ** g


def _welt(sin_tiefe, boden_nah, boden_fern, fern_grad):
    """Leuchtdichte der Welt bei sin(Blicktiefe) — dieselbe Kette wie der Welt-Shader."""
    u = min(1.0, sin_tiefe / math.sin(math.radians(stimmung.BODEN_DUNST_GRAD)))
    t = 1.0 - u
    s = max(0.0, 1.0 - sin_tiefe / math.sin(math.radians(fern_grad))) if fern_grad else 0.0
    erde = boden_nah + s * (boden_fern - boden_nah)
    return (1.0 - t) * erde + t * DUNST


SIN_KANTE = (1.0 - T_KANTE) * math.sin(math.radians(stimmung.BODEN_DUNST_GRAD))


def _zeilen(von, bis):
    for r in range(int(von), int(bis)):
        yield math.sin(math.atan((r + 0.5) / F_PX))


def _rechne(boden_nah, boden_fern, fern_grad, g):
    """Kante, Dunstband und tiefer Boden: Anstieg gegen 336 in Grauwerten."""
    r6 = F_PX * math.tan(math.radians(stimmung.BODEN_DUNST_GRAD))
    def anstieg(z):
        return (_grau(_welt(z, boden_nah, boden_fern, fern_grad), g)
                - _grau(_welt(z, B_336, B_336, 0.0), g))
    kante = anstieg(SIN_KANTE)
    band = [anstieg(z) for z in _zeilen(0, r6)]
    tief = [anstieg(z) for z in _zeilen(r6, ZEILEN_UNTER_HORIZONT)]
    return kante, sum(band) / len(band), sum(tief) / len(tief)


def _platte_kante():
    """Grau der Platte an der Unterkante: Welt an der Kante (336) minus Naht."""
    return _grau(_welt(SIN_KANTE, B_336, B_336, 0.0)) - NAHT_336


def _kontraste(band, tief):
    """Abend-Kontrast nach drei Gewichtungen des Hintergrunds neben dem Haus.

    * ``mittel``: 13,8/38,2 je Grauwert des Weltbodens unter dem Horizont (335, Mittag);
    * ``fit``: Dunstband 0,136, tiefer Boden 0,20 je Grauwert — gelöst aus 335 → 336 abend
      (+15,5/+28,5 → −7,8) und mittag (+31,3/+60,8 → −16,4);
    * ``schlimm``: Dunstband 0,31, tiefer Boden 0,105 — das Ende des Bereichs, den die
      Rundung der Kontraste auf 0,1 zulässt.
    """
    unten = (47716 * band + 145920 * tief) / 193636
    return {"mittel": KONTRAST_336 - 13.8 / 38.2 * unten,
            "fit": KONTRAST_336 - 0.136 * band - 0.20 * tief,
            "schlimm": KONTRAST_336 - 0.31 * band - 0.105 * tief}


# ============================================================ 1 · die Rechnung mit 335/336


def test_das_modell_trifft_335_und_336():
    """Die Kante liegt im Dunstband: Mit T_KANTE steigt sie 335 → 336 wie gemessen."""
    k335 = _grau(_welt(SIN_KANTE, B_335, B_335, 0.0))
    k336 = _grau(_welt(SIN_KANTE, B_336, B_336, 0.0))
    assert k336 - k335 == pytest.approx(16.6, abs=1.0)
    assert k335 - _platte_kante() == pytest.approx(NAHT_335, abs=3.0)
    assert math.degrees(math.asin(SIN_KANTE)) == pytest.approx(3.8, abs=0.1)
    # Das Dunstband (Mittel aus Boden und Horizontfarbe) trifft die Messung 65,2.
    assert _grau((B_336 + DUNST) / 2) == pytest.approx(65.2, abs=1.0)


@pytest.mark.parametrize("g", GAMMAS)
def test_option_a_halbe_blende_reicht_nicht_sicher(g):
    """(a) Der ganze Boden ½ Blende heller: die Kante steigt nur um rund die Hälfte, weil sie
    im Dunstband liegt; dafür steigt der ganze Vordergrund — der Kontrast fällt Richtung 20."""
    nah = B_336 * 2 ** 0.5
    kante, band, tief = _rechne(nah, nah, 0.0, g)
    naht = NAHT_336 + kante
    k = _kontraste(band, tief)
    unsicher = naht < -(GRENZE_NAHT - 3) or min(k.values()) < 22.0
    assert unsicher, (naht, k)


@pytest.mark.parametrize("g", GAMMAS)
def test_option_b_verlauf_zur_fernen_erde(g):
    """(b) Der gewählte Fix: nah dämmrig, fern auf Plattenhöhe, Verlauf bis 12°."""
    kante, band, tief = _rechne(B_336, B_336 / 0.5, stimmung.BODEN_FERN_GRAD, g)
    naht = NAHT_336 + kante
    assert naht > -40.5, "mindestens 4,5 Grauwerte unter der Grenze 45"
    k = _kontraste(band, tief)
    assert k["mittel"] > 23.0 and k["fit"] > 23.0, k
    assert k["schlimm"] > stimmung.KONTRAST_SCHWELLE + 1.0, k
    # Der Vordergrund bleibt dämmrig: tief unten steigt der Boden weit weniger als die Kante.
    assert tief < kante / 2


def test_der_verlauf_ist_pro_kontrastpunkt_doppelt_so_wirksam():
    """Naht gewonnen je Kontrast verloren (Gewichtung «fit», flache Kurve)."""
    def wirkung(nah, fern, grad):
        kante, band, tief = _rechne(nah, fern, grad, 0.76)
        return kante / (KONTRAST_336 - _kontraste(band, tief)["fit"])
    assert wirkung(B_336, 2 * B_336, stimmung.BODEN_FERN_GRAD) > 1.8 * wirkung(
        B_336 * 2 ** 0.5, B_336 * 2 ** 0.5, 0.0)


# ============================================================ 2 · die Farben, reine Rechnung


def test_der_ferne_boden_ist_immer_auf_plattenhoehe():
    boden = [0.8246, 0.55, 0.4681]
    assert stimmung.boden_fern_zum_faktor(boden, 0.5) == [1.6492, 1.1, 0.9362]
    # Mittags dieselbe Farbe wie der nahe — kein Pixel ändert sich.
    for f in (2.2222, 1.0, None):
        assert stimmung.boden_fern_zum_faktor(boden, f) == stimmung.boden_zum_faktor(boden, f)
    for kaputt in (0.0, -1.0, "x", float("inf")):
        assert stimmung.boden_fern_zum_faktor(boden, kaputt) == boden
    # Sichtbar (× Stärke 0,3 × 0,5) genau die Platte (× 0,3 vor der Vorprobe).
    weit = stimmung.boden_fern_zum_faktor(boden, 0.5)
    assert L(weit) * 0.3 * 0.5 == pytest.approx(L(boden) * 0.3, rel=1e-5)


def test_der_verlauf_reist_nur_mit_dem_licht_der_platte():
    assert _boden_neu("abend")["fern_grad"] == stimmung.BODEN_FERN_GRAD == 12.0
    ohne = stimmung.boden_bis_horizont([0.4] * 3, [0.2] * 3)
    assert ohne["weg"] == "himmel" and "fern_grad" not in ohne


# ============================================================ 3 · der Knotenbaum, ausgewertet


def _welt_mit(baum):
    namen = {k.name: k for k in baum.knoten}
    return SimpleNamespace(node_tree=SimpleNamespace(nodes=SimpleNamespace(get=namen.get)))


def _z(grad):
    return -math.sin(math.radians(grad))


def test_abends_nah_daemmrig_fern_wie_die_platte(monkeypatch):
    boden = _boden_neu("abend")
    modul, baum, grund, _ = _bauen(monkeypatch, boden)
    befund = modul._boden_nachstellen(_welt_mit(baum), stimmung, 0.5)
    assert befund["boden_nach_vorprobe"] == pytest.approx(boden["boden"])
    weit = befund["boden_fern_nach_vorprobe"]
    assert weit == pytest.approx([c / 0.5 for c in boden["boden"]], abs=1e-6)
    # Tief unten (unter 12°): der nahe Boden, wie 336.
    assert _farbe(baum, grund, _z(20)) == pytest.approx(boden["boden"], abs=1e-6)
    assert _farbe(baum, grund, -1.0) == pytest.approx(boden["boden"], abs=1e-6)
    # Bei 6° (Ende des Dunsts) ist die Erde halb im Verlauf: heller als nah, dunkler als fern.
    mitte = _farbe(baum, grund, _z(6))
    for m, n, w in zip(mitte, boden["boden"], weit):
        assert n < m < w
    # An der Unterkante (3,8°) heller als 336 — dort, wo die Naht stand.
    ohne = {k: v for k, v in boden.items() if k != "fern_grad"}
    _, baum_336, grund_336, _ = _bauen(monkeypatch, ohne)
    modul._boden_nachstellen(_welt_mit(baum_336), stimmung, 0.5)
    assert L(_farbe(baum, grund, _z(3.8))) > 1.2 * L(_farbe(baum_336, grund_336, _z(3.8)))
    # Am Horizont selbst: der Dunst, unverändert.
    assert _farbe(baum, grund, -1e-7) == pytest.approx(boden["dunst"], abs=1e-4)


def test_mittags_aendert_sich_kein_pixel(monkeypatch):
    """Faktor 2,22: nah und fern gleich — jede Blickhöhe wie mit dem Boden von 336."""
    boden = _boden_neu("mittag")
    modul, baum, grund, _ = _bauen(monkeypatch, boden)
    befund = modul._boden_nachstellen(_welt_mit(baum), stimmung, 2.2222)
    assert befund["boden_fern_nach_vorprobe"] == befund["boden_nach_vorprobe"]
    ohne = {k: v for k, v in boden.items() if k != "fern_grad"}
    _, baum_336, grund_336, _ = _bauen(monkeypatch, ohne)
    modul._boden_nachstellen(_welt_mit(baum_336), stimmung, 2.2222)
    for grad in (0.01, 1, 3.8, 6, 9, 12, 20, 60, 90):
        assert _farbe(baum, grund, _z(grad)) == pytest.approx(
            _farbe(baum_336, grund_336, _z(grad)), abs=1e-9)
    assert not any(k.name == modul.BODEN_FERN for k in baum_336.knoten)


def test_ueber_dem_horizont_bleibt_der_himmel(monkeypatch):
    from test_boden_bis_horizont_auf334 import HIMMEL
    modul, baum, grund, _ = _bauen(monkeypatch, _boden_neu("abend"))
    modul._boden_nachstellen(_welt_mit(baum), stimmung, 0.5)
    assert _farbe(baum, grund, 0.001) == pytest.approx(HIMMEL)


def test_ein_aelteres_modul_laesst_den_fernen_wie_den_nahen(monkeypatch):
    boden = _boden_neu("abend")
    modul, baum, grund, _ = _bauen(monkeypatch, boden)
    alt = SimpleNamespace(boden_zum_faktor=stimmung.boden_zum_faktor)
    befund = modul._boden_nachstellen(_welt_mit(baum), alt, 0.5)
    assert befund["boden_fern_nach_vorprobe"] == befund["boden_nach_vorprobe"]
    ohne = {k: v for k, v in boden.items() if k != "fern_grad"}
    _, baum_336, grund_336, _ = _bauen(monkeypatch, ohne)
    modul._boden_nachstellen(_welt_mit(baum_336), alt, 0.5)
    for grad in (1, 3.8, 9):
        assert _farbe(baum, grund, _z(grad)) == pytest.approx(
            _farbe(baum_336, grund_336, _z(grad)), abs=1e-9)


def test_ohne_fernen_knoten_bleibt_der_bericht_von_336(monkeypatch):
    modul, _ = _runner(monkeypatch)
    nah = SimpleNamespace(outputs={"Color": SimpleNamespace(default_value=(0.4, 0.4, 0.4, 1))})
    welt = SimpleNamespace(node_tree=SimpleNamespace(nodes=SimpleNamespace(
        get=lambda n: nah if n == modul.BODEN_FARBE else None)))
    assert modul._boden_nachstellen(welt, stimmung, 0.5) == {"boden_nach_vorprobe": [0.4] * 3}


# ============================================================ 4 · neues Lichtdatum


def test_die_fassung_338_reist_als_lichtdatum(tmp_path):
    """Neue Fassung = neue Grundlage: kein Zwischenspeicher-Treffer mit dem Abend von 336."""
    for preset in ("mittag", "abend"):
        mit = json.loads(abholer.umgebung_einstellungen(
            dict(_szene(tmp_path, preset), himmel_sichtbar=True))["umgebung_licht"])
        assert mit["boden_fassung"] == stimmung.BODEN_FASSUNG == "platte-338"
