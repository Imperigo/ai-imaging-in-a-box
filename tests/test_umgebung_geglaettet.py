"""Die Umgebung wird im Tiefenbild geglättet (Owner-Entscheid 77, 08.10.2026).

Am echten Splat (``auf-20261008-271``) malte Z-Image in allen 18 Bildern Kreisscheiben
(«Konfetti»): Die Aufnahme ist lückig, im Tiefenbild standen einzelne Scheiben. Der Owner
hat «Glätten» gewählt: Lücken der Umgebung schliessen — nur auf Hintergrund — und ihre Tiefe
über ein Fenster mitteln. Das Bauwerk bleibt Punkt für Punkt, wie es war.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import kontext

INF = math.inf


def _bild(zeilen):
    return [c == "u" for z in zeilen for c in z], [c == "." for z in zeilen for c in z]


def test_der_radius_waechst_mit_der_bildbreite():
    assert kontext.glaette_radius(512) == 4
    assert kontext.glaette_radius(1024) == 8
    assert kontext.glaette_radius(64) == kontext.GLAETTE_MIN_PX


def test_eine_luecke_zwischen_punkten_wird_geschlossen():
    zeilen = ["u.u.u",
              ".....",
              "u.u.u"]
    umgebung, frei = _bild(zeilen)
    zu = kontext.schliesse_umgebung(umgebung, frei, 5, 3, radius=1)
    assert all(zu), zu                              # alles zwischen den Punkten gefüllt


def test_das_bauwerk_wird_nie_umgebung():
    zeilen = ["u.b.u",
              "ubbbu",
              "u.b.u"]
    umgebung, frei = _bild(zeilen)
    zu = kontext.schliesse_umgebung(umgebung, frei, 5, 3, radius=2)
    bauwerk = [c == "b" for z in zeilen for c in z]
    assert not any(z and b for z, b in zip(zu, bauwerk))


def test_die_aussenkante_bleibt():
    """Schliessen, nicht dehnen: Was ausserhalb der Umgebung liegt, wird nicht Umgebung."""
    zeilen = ["uu.......",
              "uu.......",
              "........."]
    umgebung, frei = _bild(zeilen)
    zu = kontext.schliesse_umgebung(umgebung, frei, 9, 3, radius=2)
    assert zu == umgebung


def test_gefuellte_punkte_bekommen_die_tiefe_ihrer_nachbarn():
    umgebung = [True] * 3
    tiefe, befund = kontext.glaette_tiefe([20.0, INF, 30.0], umgebung, 3, 1, radius=1)
    assert tiefe[1] == pytest.approx(25.0)
    assert befund["n_gefuellt"] == 1


def test_das_bauwerk_behaelt_seine_tiefe():
    umgebung = [True, False, True]
    tiefe, _ = kontext.glaette_tiefe([20.0, 7.0, 30.0], umgebung, 3, 1, radius=1)
    assert tiefe[1] == 7.0
    assert tiefe[0] == pytest.approx(20.0) and tiefe[2] == pytest.approx(30.0)


def test_die_tiefe_wird_gemittelt():
    umgebung = [True] * 5
    tiefe, _ = kontext.glaette_tiefe([10.0, 30.0, 10.0, 30.0, 10.0], umgebung, 5, 1, radius=1)
    assert tiefe[2] == pytest.approx(70.0 / 3)


def test_falsche_masse_werden_abgewiesen():
    with pytest.raises(kontext.KontextError):
        kontext.schliesse_umgebung([True], [True, True], 2, 1)
    with pytest.raises(kontext.KontextError):
        kontext.glaette_tiefe([1.0], [True, True], 2, 1)


def test_mit_umgebung_hat_das_modell_das_mittlere_band_und_die_ordnung_bleibt():
    from aiimaging import bildschreiben as bs
    #          Umgebung nah, Modell 10–12 m,      Umgebung fern
    tiefe = [5.0, 8.0, 10.0, 11.0, 12.0, 20.0, 40.0]
    umgebung = [True, True, False, False, False, True, True]
    grau, n = bs.normalisiere_tiefe(tiefe, umgebung=umgebung)
    unten, oben = bs.MODELL_BAND
    assert grau[2] == pytest.approx(oben) and grau[4] == pytest.approx(unten)
    assert grau == sorted(grau, reverse=True)                 # nah = hell, überall
    assert grau[0] == pytest.approx(1.0) and grau[-1] == pytest.approx(bs.GEKLEMMT_MINDESTGRAU)
    assert min(grau) > bs.HINTERGRUND_GRAUWERT                # Geometrie ≠ Hintergrund
    assert n["umgebung"]["band_modell"] == [unten, oben]


def test_ohne_umgebung_bleibt_die_normierung_dieselbe():
    from aiimaging import bildschreiben as bs
    tiefe = [5.0, 8.0, 10.0, INF]
    a = bs.normalisiere_tiefe(tiefe)
    assert "umgebung" not in a[1]
    assert a[0][0] == pytest.approx(1.0)
