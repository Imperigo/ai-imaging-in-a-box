"""Umrisstreue aus den Bildkanten — die Nullproben zuerst (Owner-Entscheid «b», 30.09.2026).

Jeder neue Kandidat muss zuerst gegen die graue Fläche und gegen Rauschen bestehen: Die
«Ordnung an Tiefensprüngen» gab einer grauen Fläche die Bestnote 1,0 (auf-20260924-172),
und niemand hatte es vorher geprüft. Die eigentliche Frage — trennt es an erzeugten
Bildern? — beantwortet erst die HomeStation.
"""
from __future__ import annotations

import random

import pytest

from aiimaging import umriss

B, H = 64, 48
HG = 1.0e10


def _soll(x0=20, y0=12, x1=44, y1=36, tiefe=10.0, stufe=None):
    """Ein Quader vor Hintergrund; optional eine zurückspringende Stufe rechts."""
    werte = []
    for y in range(H):
        for x in range(B):
            if x0 <= x < x1 and y0 <= y < y1:
                werte.append(tiefe + (2.0 if stufe is not None and x >= stufe else 0.0))
            else:
                werte.append(HG)
    return werte


def _bild(x0=20, y0=12, x1=44, y1=36, hell=0.8, dunkel=0.2):
    return [hell if (x0 <= x < x1 and y0 <= y < y1) else dunkel
            for y in range(H) for x in range(B)]


def test_ein_passendes_bild_hebt_sich_deutlich_ab():
    aus = umriss.umriss_treue(_bild(), _soll(), B, H)
    assert aus["status"] == "ok" and aus["urteilt"] is False
    assert aus["trefferquote"] > 0.9
    assert aus["abhebung"] > 3.0


def test_die_graue_flaeche_bekommt_null_nicht_die_bestnote():
    aus = umriss.umriss_treue([0.5] * (B * H), _soll(), B, H)
    assert aus["status"] == "keine_bildkanten"
    assert aus["trefferquote"] == 0.0 and aus["abhebung"] == 0.0


def test_rauschen_ist_nicht_besser_als_zufall():
    rnd = random.Random(7)
    aus = umriss.umriss_treue([rnd.random() for _ in range(B * H)], _soll(), B, H)
    assert 0.5 < aus["abhebung"] < 1.6, aus


def test_ein_verschobener_bau_trifft_deutlich_schlechter():
    richtig = umriss.umriss_treue(_bild(), _soll(), B, H)
    daneben = umriss.umriss_treue(_bild(x0=30, x1=54), _soll(), B, H)
    assert daneben["trefferquote"] < 0.6 * richtig["trefferquote"]
    assert daneben["abhebung"] < richtig["abhebung"]


def test_dasselbe_bild_passt_zur_richtigen_referenz_besser_als_zur_falschen():
    """Die paarweise Frage, die 175 nahelegt: gleiches Bild, richtige gegen falsche Soll-Karte."""
    bild = _bild()
    richtig = umriss.umriss_treue(bild, _soll(), B, H)["abhebung"]
    fremd = umriss.umriss_treue(bild, _soll(x0=8, y0=4, x1=30, y1=44), B, H)["abhebung"]
    assert richtig > fremd


def test_eine_tiefenstufe_ist_auch_eine_sollkante():
    kanten = umriss.sprungkanten(_soll(stufe=32), B, H)
    assert kanten[20 * B + 31] or kanten[20 * B + 32], "die Stufe in der Fassade fehlt"


def test_ohne_geometrie_gibt_es_nichts_zu_treffen():
    aus = umriss.umriss_treue(_bild(), [HG] * (B * H), B, H)
    assert aus["status"] == "keine_soll_kanten" and aus["abhebung"] is None


def test_falsche_laenge_ist_ein_fehler():
    with pytest.raises(ValueError):
        umriss.umriss_treue([0.5] * 10, _soll(), B, H)


def test_urteilt_nicht():
    """Bis eine Messung eine Schwelle trägt, ist die Zahl Auskunft (Owner-Entscheid «a»)."""
    assert umriss.umriss_treue(_bild(), _soll(), B, H)["urteilt"] is False
