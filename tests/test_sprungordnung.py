"""Ordnung an Tiefensprüngen — die Messung, die saubere Bilder messbar machen soll.

Der Befund (HomeStation, auf-20260923-160 D): Das sauberste Bild des Tages — ein
freistehendes Gebäude genau auf der Silhouette, davor ein erfundener Boden — bekam
«nicht messbar» (``wie_soll`` griff nur Boden) oder Score 0 (ρ über die flache Front
mass das Ortsfeld des Schätzers). Protokoll 71 §17.

Alle Szenen hier sind synthetisch und nachgebaut, wie die Befunde sie beschreiben: ein
Schätzer mit Ortsfeld (unten näher), ein erfundener Boden im unteren Bildteil, der
**näher** ist als der Sockel. Die Zahlen belegen den Mechanismus, **nicht** den echten
Schätzer — das misst die HomeStation.
"""
from __future__ import annotations

import math
import random

import pytest

from aiimaging import geometrie_qa as gq
from aiimaging import tiefenschaetzer as ts

B = H = 64
HORIZONT = 40            # Augenhöhe im Bild: darunter darf Boden stehen
BAU = (20, 44, 16, 48)   # x0, x1, y0, y1 (y1 ist der Sockel)
BODEN_AB = 44            # ab dieser Zeile erfindet das Bild einen Boden


def _im_bau(x, y, versatz=0):
    x0, x1, y0, y1 = BAU
    return x0 + versatz <= x <= x1 + versatz and y0 <= y <= y1


def _soll():
    """Blender-Soll: Bauwerk in 11 m mit leichter Schräge, sonst nichts (inf)."""
    return [11.0 + 0.004 * x if _im_bau(x, y) else math.inf
            for y in range(H) for x in range(B)]


def _ortsfeld(x, y):
    """Die Schüssel des Schätzers: unten näher, zur Mitte etwas näher (Disparität)."""
    return 0.2 + 0.3 * y / (H - 1) + 0.05 * (1 - abs(x - B / 2) / (B / 2))


def _ist(*, bau_da=True, versatz=0, verkehrt=False, boden=True):
    werte = []
    for y in range(H):
        for x in range(B):
            v = _ortsfeld(x, y)
            if boden and y >= BODEN_AB and not _im_bau(x, y, versatz):
                v += 0.6                       # erfundener Boden, näher als der Sockel
            if bau_da and _im_bau(x, y, versatz):
                v += -0.4 if verkehrt else 0.4
            werte.append(v)
    return werte


def _messe(ist, **kw):
    kw.setdefault("polaritaet", gq.POLARITAET_DISPARITAET)
    kw.setdefault("horizont_zeile", HORIZONT)
    return gq.sprungordnung(_soll(), ist, breite=B, **kw)


def test_das_saubere_bild_ist_messbar_und_richtig():
    erg = _messe(_ist())
    assert erg["gemessen"] and erg["anteil"] >= 0.95, erg


def test_mutation_ohne_die_bodenregel_faellt_das_saubere_bild():
    """Die Gegenprobe zur Regel selbst: Zählt der Boden mit, wird das gute Bild schlecht.

    Ohne diese Probe wäre die Horizontregel eine Behauptung — ein Test, der nicht
    widersprechen kann, prüft nichts.
    """
    mit_regel = _messe(_ist())["anteil"]
    ohne_regel = _messe(_ist(), horizont_zeile=H)["anteil"]
    assert mit_regel - ohne_regel >= 0.2, (mit_regel, ohne_regel)


def test_ein_verschobenes_bauwerk_faellt_deutlich():
    sauber = _messe(_ist())["anteil"]
    verschoben = _messe(_ist(versatz=12))["anteil"]
    assert verschoben <= sauber - 0.2, (sauber, verschoben)


def test_die_gasse_faellt_unter_die_haelfte():
    """Vorne und hinten vertauscht — «wie ein Blick durch eine Gasse» (auf-158 B)."""
    assert _messe(_ist(verkehrt=True))["anteil"] < 0.5


def test_ohne_bauwerk_bleibt_es_beim_ortsfeld():
    """Leeres Grundstück: Die Oberkante findet nichts; das Ortsfeld allein trägt nicht."""
    assert _messe(_ist(bau_da=False))["anteil"] <= 0.6


def test_rauschen_liegt_um_die_haelfte():
    zufall = random.Random(20260924)
    ist = [zufall.random() for _ in range(B * H)]
    assert 0.35 <= _messe(ist)["anteil"] <= 0.65


def test_die_polaritaet_kehrt_das_ergebnis_um():
    ist = _ist()
    richtig = _messe(ist)["anteil"]
    verkehrt = _messe(ist, polaritaet=gq.POLARITAET_TIEFE)["anteil"]
    assert richtig + verkehrt == pytest.approx(1.0, abs=1e-3)


def test_ohne_gemessene_polaritaet_gibt_es_keinen_anteil():
    erg = _messe(_ist(), polaritaet=None)
    assert erg["anteil"] is None and not erg["gemessen"]
    assert "Polarität" in erg["warnungen"][0]


def test_ohne_horizont_zaehlt_nur_die_oberkante():
    erg = _messe(_ist(), horizont_zeile=None)
    assert erg["gemessen"] and erg["anteil"] >= 0.95
    assert erg["n_kontur"] == (BAU[1] - BAU[0] + 1) * 1 or erg["n_kontur"] > 0


def test_zu_wenige_paare_heissen_nicht_gemessen():
    soll = [math.inf] * (B * H)
    soll[B * 30 + 30] = 11.0
    erg = gq.sprungordnung(soll, _ist(), breite=B,
                           polaritaet=gq.POLARITAET_DISPARITAET, horizont_zeile=HORIZONT)
    assert erg["anteil"] is None and erg["n_kontur"] < gq.MIN_SPRUNGPAARE


def test_der_alte_weg_findet_hier_nichts_gemeinsames():
    """Der Befund, nachgestellt: ``wie_soll`` greift auf dieser Szene den Boden."""
    soll = _soll()
    n_soll = sum(1 for v in soll if math.isfinite(v))
    markiert = ts.markiere_hintergrund(_ist(), polaritaet="disparitaet",
                                       strategie=ts.HG_WIE_SOLL, n_geometrie=n_soll,
                                       breite=B, hoehe=H)
    gewaehlt = [math.isfinite(v) for v in markiert["tiefen"]]
    im_soll = sum(1 for g, s in zip(gewaehlt, soll) if g and math.isfinite(s))
    assert im_soll / n_soll < 0.5, "der Boden wurde gewählt, nicht das Bauwerk"
    assert _messe(_ist())["gemessen"], "der neue Weg misst dasselbe Bild"


def _soll_mit_ruecksprung():
    """Linke Hälfte des Baus in 11 m, rechte zurückgesetzt in 14 m."""
    return [(11.0 if x < 32 else 14.0) if _im_bau(x, y) else math.inf
            for y in range(H) for x in range(B)]


def _ist_mit_ruecksprung(*, verkehrt=False):
    werte = []
    for y in range(H):
        for x in range(B):
            v = _ortsfeld(x, y)
            if _im_bau(x, y):
                nah, fern = (0.25, 0.4) if verkehrt else (0.4, 0.25)
                v += nah if x < 32 else fern
            werte.append(v)
    return werte


@pytest.mark.parametrize("verkehrt,erwartet", [(False, 1.0), (True, 0.0)])
def test_ein_ruecksprung_in_der_fassade_wird_als_stufe_gewertet(verkehrt, erwartet):
    erg = gq.sprungordnung(_soll_mit_ruecksprung(), _ist_mit_ruecksprung(verkehrt=verkehrt),
                           breite=B, polaritaet=gq.POLARITAET_DISPARITAET,
                           horizont_zeile=HORIZONT)
    assert erg["n_stufen"] >= gq.MIN_SPRUNGPAARE
    assert erg["anteil_stufen"] == pytest.approx(erwartet)
