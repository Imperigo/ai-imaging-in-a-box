"""``gelaende_z`` — der Schalter, der die Kamera aus dem Keller holt.

Was am 28.08.2026 gemessen wurde
--------------------------------
Der Lauf setzte ``gelaende_z`` nicht. Als Boden galt darum die Unterkante der Hüllbox, und
die lag bei einem Bauwerk **mit Untergeschoss** im Erdreich: Die Kamera stand **3,238 m
unter dem Erdgeschossfussboden und 12 mm über dem Kellerboden**. Der Kamerablock des
Berichts meldete ``warnungen: []``.

Was daran NICHT stimmte — und die erste Vermutung war falsch
------------------------------------------------------------
Die naheliegende Erklärung wäre: die Warnung fehlt. Nachgemessen stimmt sie nicht.
``komposition.BEZUGSPUNKTE`` führt ``huellbox_unterkante`` mit ``verlaesslich: False``,
und ``komposition.beurteile_bericht`` — die der Abholer wirklich aufruft — **meldet den
Vorbehalt auf genau diesem Bericht**. Die Auskunft war da, sie war richtig, und die Kamera
stand trotzdem im Keller.

Was fehlte, war nicht die Warnung, sondern ihr **Ort**: ein Urteil über das fertige Bild,
eine Modulgrenze von der Zahl entfernt, die es betrifft. Diese Datei hält beides fest —
dass die alte Auskunft weiter besteht, und dass die neue an der Quelle steht.
"""
from __future__ import annotations

import pytest

from aiimaging import kameras, komposition

#: Ein Bauwerk mit zwei Untergeschossen: Fuss der Hüllbox 6 m unter dem Gelände.
#:
#: Dieselbe Lage wie am 28.08.2026, auf runde Zahlen gebracht (Regel 3 — die echten
#: Landeskoordinaten gehören nicht ins Repo). ``gelaende_z`` ist hier bekannt: 0,0.
MIT_ZWEI_UG = [[0.0, 0.0, -6.0], [40.0, 25.0, 18.0]]


# --------------------------------------------------------------------------------------
# 1 · Ohne Angabe: der Fall faellt auf
# --------------------------------------------------------------------------------------

def test_ohne_gelaende_z_meldet_der_kamerasatz_den_unbekannten_bezugspunkt():
    """Bis zum 01.09.2026 war ``warnungen`` hier leer — genau das ist die Aenderung."""
    satz = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",))
    treffer = [w for w in satz["warnungen"] if "GELAENDESTAND NICHT FESTSTELLBAR" in w]
    assert treffer, satz["warnungen"]


def test_die_warnung_nennt_die_zahlen_und_nicht_nur_die_gefahr():
    """„Kann schiefgehen" laesst sich ueberlesen; drei Zahlen schwerer.

    Die Warnung muss sagen, WELCHE Kante genommen wurde und WO die Kamera dadurch steht.
    Ohne diese beiden Zahlen waere sie eine Wiederholung dessen, was ``komposition``
    ohnehin sagt — und dann waere sie ueberfluessig.
    """
    satz = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",))
    warnung = next(w for w in satz["warnungen"] if "GELAENDESTAND" in w)
    assert "-6.000" in warnung, warnung                      # die genommene Hüllbox-Unterkante
    assert "-4.300" in warnung, warnung                      # der Standort der Kamera
    assert "Untergeschoss" in warnung


def test_die_kamera_steht_ohne_angabe_wirklich_im_keller():
    """Der Befund selbst, nicht nur seine Meldung.

    Ohne ``gelaende_z`` steht die Kamera 1,70 m ueber der Hüllbox-Unterkante — bei zwei
    Untergeschossen also **4,30 m unter dem Gelaende**. Mit Angabe steht sie 1,70 m
    darueber. Der Unterschied betraegt genau die Tiefe der Untergeschosse.
    """
    ohne = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",))
    mit = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",), gelaende_z=0.0)

    assert ohne["kameras"][0]["auge"][2] == pytest.approx(-4.30)
    assert mit["kameras"][0]["auge"][2] == pytest.approx(1.70)
    assert mit["kameras"][0]["auge"][2] - ohne["kameras"][0]["auge"][2] == pytest.approx(6.0)


# --------------------------------------------------------------------------------------
# 2 · Mit Angabe: die Warnung verschwindet
# --------------------------------------------------------------------------------------

def test_mit_gelaende_z_ist_die_warnung_weg():
    """Eine Warnung, die auch bei richtiger Angabe kommt, ist Rauschen und wird ueberlesen."""
    satz = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",), gelaende_z=0.0)
    assert not any("GELAENDESTAND" in w for w in satz["warnungen"]), satz["warnungen"]
    assert satz["gelaende_bezug"] == "terrain_an_kamera"


# --------------------------------------------------------------------------------------
# 3 · Wo die Warnung steht — und wo nicht
# --------------------------------------------------------------------------------------

def test_der_stehende_vorbehalt_verdraengt_den_dringenden_befund_nicht():
    """Vorn stehen die Befunde ueber DIESEN Satz, nicht der Vorbehalt, der immer gilt.

    ``kamerasatz`` stellt „die Hüllbox hat keine Höhe" bewusst an die erste Stelle. Der
    Geländestand ist etwas anderes: ein Vorbehalt, der bei **jedem** Satz ohne
    ``gelaende_z`` zutrifft. Vorn haette er den dringenden Befund verdraengt — und genau
    darauf bestehen ``test_leere_szene`` und ``test_multipass``.
    """
    flach = [[0.0, 0.0, 0.0], [30.0, 30.0, 0.0]]             # ohne Höhe
    satz = kameras.kamerasatz(flach, kuerzel=("sSE",))
    assert "GELAENDESTAND" not in satz["warnungen"][0], satz["warnungen"][0]
    assert any("GELAENDESTAND" in w for w in satz["warnungen"]), satz["warnungen"]


def test_die_alte_auskunft_besteht_weiter():
    """Die Gegenprobe zur eigenen Fehlannahme.

    Die neue Warnung ersetzt nichts. ``komposition`` beurteilt den Bezugspunkt weiterhin,
    und wer diesen Weg geht, bekommt dieselbe Auskunft wie bisher. *Waere die alte
    Meldung beim Umbau verschwunden, haette diese Sitzung eine funktionierende Warnung
    gegen eine neue getauscht und das fuer Fortschritt gehalten.*
    """
    urteil = komposition.kamerahoehe(kameras.AUGENHOEHE_M, bezugspunkt="huellbox_unterkante")
    assert urteil["warnungen"], urteil
    assert komposition.BEZUGSPUNKTE["huellbox_unterkante"]["verlaesslich"] is False


def test_die_beiden_warnungen_sagen_nicht_dasselbe():
    """Sonst waere die neue eine Verdopplung statt einer Ergaenzung.

    ``komposition`` sagt, dass der Bezugspunkt unzuverlaessig IST. ``kamerasatz`` sagt,
    WELCHE Zahl deswegen gilt und wo die Kamera dadurch steht.
    """
    satz = kameras.kamerasatz(MIT_ZWEI_UG, kuerzel=("sSE",))
    neu = next(w for w in satz["warnungen"] if "GELAENDESTAND" in w)
    alt = komposition.kamerahoehe(kameras.AUGENHOEHE_M,
                                  bezugspunkt="huellbox_unterkante")["warnungen"][0]
    assert "-4.300" in neu and "-4.300" not in alt
    assert "gelaende_z" in neu and "gelaende_z" not in alt
