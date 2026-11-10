"""Der reine Strahlentest an Körpern (``aiimaging.sichtstrahl``, A0306).

Er steht in den Proben an der Stelle, an der im Betrieb der Strahlenschuss des Runners
steht. Ein Fehler hier machte jede Aussage über «freie Sicht» wertlos; darum wird er
dreifach geprüft: an Fällen zum Nachrechnen, gegen den zweiten Strahlentest des Prüfmasses
(``sichtszenen.strahl_trifft``, anderer Rechenweg) und gegen blosses Abtasten der Strecke.
"""
from __future__ import annotations

import random

import pytest

import sichtszenen as sz
from aiimaging import sichtstrahl

WUERFEL = [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]]


def test_eine_strecke_durch_den_koerper_trifft_an_der_vorderwand():
    assert sichtstrahl.strecke_trifft((-10.0, 5.0, 5.0), (30.0, 5.0, 5.0), WUERFEL) == 0.25


def test_eine_strecke_daran_vorbei_trifft_nicht():
    assert sichtstrahl.strecke_trifft((-10.0, 11.0, 5.0), (30.0, 11.0, 5.0), WUERFEL) is None
    assert sichtstrahl.strecke_trifft((-10.0, 5.0, 12.0), (30.0, 5.0, 12.0), WUERFEL) is None


def test_eine_strecke_die_vor_dem_koerper_endet_trifft_nicht():
    assert sichtstrahl.strecke_trifft((-10.0, 5.0, 5.0), (-1.0, 5.0, 5.0), WUERFEL) is None


def test_ueber_einen_niedrigen_bau_hinweg_ist_die_sicht_frei():
    niedrig = sichtstrahl.quader((5.0, 5.0), 10.0, 10.0, 3.0)
    assert sichtstrahl.strecke_trifft((-10.0, 5.0, 1.7), (30.0, 5.0, 20.0), niedrig) is None
    assert sichtstrahl.strecke_trifft((-10.0, 5.0, 1.7), (30.0, 5.0, 1.7), niedrig) is not None


def test_wer_im_bau_steht_sieht_nichts():
    assert sichtstrahl.strecke_trifft((5.0, 5.0, 5.0), (30.0, 5.0, 5.0), WUERFEL) == 0.0
    assert sichtstrahl.punkt_im_koerper((5.0, 5.0, 5.0), WUERFEL)
    assert not sichtstrahl.punkt_im_koerper((5.0, 5.0, 10.5), WUERFEL)


def test_eine_streifende_sichtlinie_gilt_als_verdeckt():
    """Die vorsichtige Seite: lieber einen Schritt weiter als an der Hauskante entlang."""
    assert sichtstrahl.strecke_trifft((-10.0, 10.0, 5.0), (30.0, 10.0, 5.0), WUERFEL) is not None


def test_ein_gedrehter_bau_wird_als_gedrehter_getroffen():
    """Ein schmaler Riegel, um 90° gedreht: Was vorher daran vorbeiging, trifft jetzt."""
    riegel = sichtstrahl.quader((0.0, 0.0), 20.0, 2.0, 5.0)
    gedreht = sichtstrahl.quader((0.0, 0.0), 20.0, 2.0, 5.0, drehung_grad=90.0)
    strecke = ((-5.0, 8.0, 1.0), (5.0, 8.0, 1.0))
    assert sichtstrahl.strecke_trifft(*strecke, riegel) is None
    assert sichtstrahl.strecke_trifft(*strecke, gedreht) is not None


def test_die_antwort_nennt_den_ersten_verdecker_und_seinen_abstand():
    vorn = sichtstrahl.quader((10.0, 0.0), 2.0, 6.0, 8.0, name="vorn")
    hinten = sichtstrahl.quader((20.0, 0.0), 2.0, 6.0, 8.0, name="hinten")
    antwort = sichtstrahl.sicht_frei((0.0, 0.0, 1.7), (30.0, 0.0, 1.7), [hinten, vorn])
    assert antwort["frei"] is False and antwort["getroffen"] is True
    assert antwort["objekt"] == "vorn"
    assert antwort["abstand_treffer_m"] == pytest.approx(9.0)
    assert antwort["abstand_ziel_m"] == pytest.approx(30.0)
    assert "vorn" in antwort["grund"]


def test_ohne_koerper_ist_die_sicht_frei_und_das_steht_da():
    antwort = sichtstrahl.sicht_frei((0.0, 0.0, 1.7), (30.0, 0.0, 1.7), [])
    assert antwort == {"frei": True, "getroffen": False, "abstand_ziel_m": 30.0,
                       "abstand_treffer_m": None, "objekt": None, "grund": ""}


def test_auge_im_ziel_ist_nicht_gemessen_und_nicht_frei():
    antwort = sichtstrahl.sicht_frei((1.0, 2.0, 3.0), (1.0, 2.0, 3.0), [WUERFEL])
    assert antwort["frei"] is None and "NICHT GEMESSEN" in antwort["grund"]


def test_der_pruefer_ist_die_sichtpruefung_einer_festen_szene():
    pruefe = sichtstrahl.pruefer([WUERFEL])
    assert pruefe((-10.0, 5.0, 5.0), (30.0, 5.0, 5.0))["frei"] is False
    assert pruefe((-10.0, 15.0, 5.0), (30.0, 15.0, 5.0))["frei"] is True


@pytest.mark.parametrize("unsinn", [None, "haus", [[0, 0, 0]], [[0, 0, 0], [1, 1, float("nan")]]])
def test_ein_unlesbarer_koerper_wird_abgewiesen(unsinn):
    with pytest.raises(ValueError):
        sichtstrahl.strecke_trifft((0, 0, 0), (1, 1, 1), unsinn)


@pytest.mark.parametrize("masse", [(0.0, 5.0, 5.0), (5.0, -1.0, 5.0), (5.0, 5.0, float("inf"))])
def test_ein_quader_ohne_ausdehnung_wird_abgewiesen(masse):
    with pytest.raises(ValueError):
        sichtstrahl.quader((0.0, 0.0), *masse)


def _zufallsfall(r: random.Random):
    koerper = sichtstrahl.quader((r.uniform(-10, 10), r.uniform(-10, 10)), r.uniform(1, 12),
                                 r.uniform(1, 12), r.uniform(1, 15), fuss_z=r.uniform(-2, 2),
                                 drehung_grad=r.choice((0.0, 0.0, 17.0, 45.0, 90.0, 133.0)))
    von = (r.uniform(-25, 25), r.uniform(-25, 25), r.uniform(0, 20))
    nach = (r.uniform(-25, 25), r.uniform(-25, 25), r.uniform(0, 20))
    return von, nach, koerper


def test_zwei_rechenwege_ein_urteil():
    """3000 Zufallsstrecken: Der Strahlentest der Bibliothek (im Achsensystem des Quaders)
    und der des Prüfmasses (an den Wandebenen im Weltsystem) urteilen gleich."""
    r = random.Random(1306)
    treffer = 0
    for _ in range(3000):
        von, nach, koerper = _zufallsfall(r)
        hier = sichtstrahl.strecke_trifft(von, nach, koerper) is not None
        assert hier == sz.strahl_trifft(von, nach, koerper), (von, nach, koerper)
        treffer += hier
    assert 150 < treffer < 2850, "Die Stichprobe prüft nur noch eine der zwei Antworten."


def test_abgetastet_kommt_dasselbe_heraus():
    """Die dritte Meinung braucht keine Formel: die Strecke in 2-cm-Schritten abgehen und
    fragen, ob ein Punkt im Körper liegt. Abtasten kann einen Streifschuss übersehen, nie
    einen erfinden; darum gilt nur diese Richtung streng."""
    r = random.Random(2306)
    uebersehen = 0
    for _ in range(300):
        von, nach, koerper = _zufallsfall(r)
        laenge = sum((nach[i] - von[i]) ** 2 for i in range(3)) ** 0.5
        n = max(2, int(laenge / 0.02))
        abgetastet = any(
            sichtstrahl.punkt_im_koerper(
                tuple(von[i] + (nach[i] - von[i]) * j / n for i in range(3)), koerper)
            for j in range(n + 1))
        gerechnet = sichtstrahl.strecke_trifft(von, nach, koerper) is not None
        if abgetastet:
            assert gerechnet, (von, nach, koerper)
        uebersehen += gerechnet and not abgetastet
    assert uebersehen <= 6, "Gerechnet wird öfter getroffen, als Streifschüsse erklären."
