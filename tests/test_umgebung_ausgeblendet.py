"""Die Umgebung (Splat) zählt in der Prüfung nicht als Bauwerk (``auf-20261008-271``).

Am echten Splat zählte ``anteil_soll`` die Punkte der Umgebung mit: 23–31 % statt 3,7–4,4 %.
Damit griff die 20-%-Regel (Entscheid 70) nicht, und ein Bild mit einem Bauwerk auf 2–3 %
galt als «durchgefallen» statt «nicht beurteilbar». Seither blendet
``qa_gegen_soll(ausblenden=…)`` die Umgebung auf beiden Seiten aus.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import abholer
from aiimaging import tiefenschaetzer as ts
from test_pruefung_ohne_boden import B, _szene, bild  # noqa: F401 — Fixture
from test_tiefenschaetzer import attrappe


def _mit_umgebung(seite: int, streifen: int):
    """Ein kleines Haus mittig und ``streifen`` volle Zeilen Umgebung oben im Bild."""
    soll, ist, maske = _szene(seite)
    umgebung = [i < streifen * B for i in range(B * B)]
    for i, u in enumerate(umgebung):
        if u:
            soll[i] = 40.0          # weit weg, aber endlich: so sieht ein Splat im Soll aus
            ist[i] = 1.0 / 40.0
    return soll, ist, maske, umgebung


def test_ohne_ausblendung_zaehlt_die_umgebung_als_geometrie(bild):
    soll, ist, maske, _u = _mit_umgebung(12, 10)            # 14 % Haus, 31 % Umgebung
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist), breite=B, hoehe=B, maske=maske)
    assert urteil["anteil_soll"] > 0.4
    assert urteil["gesamtwert_anwendbar"] is True              # der Fehler aus 271
    assert urteil["n_ausgeblendet"] is None


def test_mit_ausblendung_ist_das_kleine_haus_nicht_beurteilbar(bild):
    soll, ist, maske, umgebung = _mit_umgebung(12, 10)
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist), breite=B, hoehe=B, maske=maske,
                              ausblenden=umgebung)
    assert urteil["anteil_soll"] == pytest.approx(144 / 1024)
    assert urteil["gesamtwert_anwendbar"] is False
    assert urteil["bestanden"] is None
    assert urteil["n_ausgeblendet"] == 10 * B


def test_ausgeblendet_ist_dasselbe_wie_dort_himmel(bild):
    """Die Gegenprobe: ausgeblendete Umgebung misst wie dieselbe Szene ohne Umgebung."""
    soll, ist, maske, umgebung = _mit_umgebung(16, 6)
    mit = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist), breite=B, hoehe=B, maske=maske,
                           ausblenden=umgebung)
    soll0, ist0, maske0 = _szene(16)
    ohne = ts.qa_gegen_soll(bild, soll0, modell=attrappe(ist0), breite=B, hoehe=B, maske=maske0)
    for feld in ("anteil_soll", "score", "spearman", "geom_iou", "bestanden"):
        assert mit[feld] == ohne[feld], feld


def test_eine_falsch_lange_ausblendung_wird_abgewiesen(bild):
    soll, ist, maske, _u = _mit_umgebung(12, 2)
    with pytest.raises(ts.TiefenschaetzerError, match="geraten wird nicht"):
        ts.qa_gegen_soll(bild, soll, modell=attrappe(ist), breite=B, hoehe=B, maske=maske,
                         ausblenden=[True] * 3)


def test_der_umriss_der_seedwahl_ist_der_des_bauwerks():
    assert abholer._ohne_umgebung([1.0, 2.0, 3.0], [False, True, False]) == [1.0, math.inf, 3.0]
    assert abholer._ohne_umgebung([[1.0, 2.0], [3.0, 4.0]], [True, False, False, True]) == \
        [[math.inf, 2.0], [3.0, math.inf]]
    assert abholer._ohne_umgebung([1.0], [True, True]) == [1.0]       # geraten wird nicht


def test_die_maske_traegt_die_umgebung_je_bildpunkt_nur_mit_splat():
    from aiimaging import maske
    haus = {"name": "Haus", "farbe_srgb_8bit": [10, 20, 30], "quelle": "objekt"}
    baum = {"name": "Splat", "farbe_srgb_8bit": [200, 100, 50], "quelle": maske.QUELLE_KONTEXT}
    farben = [(10, 20, 30), (200, 100, 50), maske.HINTERGRUND_FARBE]
    mit = maske.bauwerksmaske(farben, [haus, baum], gelaende_erwartet=False)
    assert mit["kontext_pixel"] == [False, True, False]
    assert mit["maske"] == [True, False, False]
    ohne = maske.bauwerksmaske([farben[0], farben[2]], [haus], gelaende_erwartet=False)
    assert ohne["kontext_pixel"] is None
