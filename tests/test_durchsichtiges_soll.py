"""Der Riegel auf die SOLL-Karte — der Fall vom 03.09.2026 als Probe.

**Der Anlass.** In Demolauf 17 kam erstmals Glas im Modell an (750 Primitive mit
``alphaMode: BLEND``). Der Bildwert fiel daraufhin von 0.2015 auf **0.000**, die
Rangkorrelation von 0.7995 auf 0.6480 — bei einem Modell, das BESSER geworden war.

Die Ursache lag nicht im Bild und nicht in der Messkette (beide Läufe rechnen mit dem
heutigen Code auf vier Stellen genau nach), sondern in der **Referenz**: Der Tiefenpass
lief mit Transparenz-Bounces und schrieb hinter jeder Scheibe, was dahinter liegt. Der
Material-ID-Pass war nicht betroffen — er läuft mit ``transparent_max_bounces = 0``.
Zwei Durchgänge desselben Renders widersprachen sich, und keine Zahl sagte es.

**Was diese Datei festhält.** Der Widerspruch ist aus Soll und Maske allein feststellbar,
ohne Bild, ohne Schätzung, ohne GPU. Und er muss dort feuern, wo er auftritt, und
schweigen, wo er es nicht tut — sonst wäre es keine Probe, sondern eine Meldung.

Alle Karten sind synthetisch und hier erzeugt (Regel 3): kein EXR, kein Blender, keine
GPU. Die echten Zahlen der beiden Demoläufe stehen im Docstring von
``geometrie_qa.durchsichtiges_soll``, nicht in einer Datei im Repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import geometrie_qa, tiefenschaetzer  # noqa: E402

BREITE, HOEHE = 20, 20
HINTERGRUND = 1.0e10


def _szene(durchsichtige_punkte: set[tuple[int, int]] = frozenset()):
    """Ein Quader in der Bildmitte. ``durchsichtige_punkte`` sind Scheiben, durch die der
    Tiefenpass bis in den Hintergrund schaut — die Maske hält sie trotzdem für Bauwerk,
    weil der Material-ID-Pass die Scheibe sehr wohl getroffen hat."""
    soll, maske = [], []
    for y in range(HOEHE):
        for x in range(BREITE):
            drin = 5 <= x < 15 and 5 <= y < 15
            maske.append(drin)
            if not drin:
                soll.append(HINTERGRUND)
            elif (x, y) in durchsichtige_punkte:
                soll.append(HINTERGRUND)          # der Strahl ging durch und wieder hinaus
            else:
                soll.append(100.0 + 0.5 * x)      # Fassade mit sanftem Verlauf
    return soll, maske


def test_dichte_szene_ist_nicht_durchsichtig():
    """Der gesunde Fall — und zugleich der Beleg, dass die Nachsicht von einem Promille
    im Normalbetrieb gar nicht gebraucht wird. Demolauf 16 erreichte hier exakt 0."""
    befund = geometrie_qa.durchsichtiges_soll(*_szene())
    assert befund["n_durchsicht"] == 0
    assert befund["anteil"] == 0.0
    assert befund["durchsichtig"] is False
    assert befund["warnungen"] == []


def test_glas_im_soll_wird_gefunden_und_benannt():
    """Der Fall vom 03.09.2026, im Kleinen."""
    scheiben = {(x, y) for x in range(6, 9) for y in range(6, 9)}   # 9 von 100
    befund = geometrie_qa.durchsichtiges_soll(*_szene(scheiben))
    assert befund["n_durchsicht"] == 9
    assert befund["n_maske"] == 100
    assert befund["anteil"] == pytest.approx(0.09)
    assert befund["durchsichtig"] is True
    assert len(befund["warnungen"]) == 1
    warnung = befund["warnungen"][0]
    assert "durchsichtig" in warnung
    assert "ZU NIEDRIG" in warnung, "der Vorbehalt muss die RICHTUNG des Fehlers nennen"


def test_ein_loch_NEBEN_der_maske_feuert_nicht():
    """**Die Probe, die den Riegel von einem Fehlalarm trennt.**

    Ein Torbogen, ein Durchblick unter einem Vordach, der Himmel neben dem Haus: Dort
    steht im Soll auch Hintergrund. Es ist aber kein Defekt, weil schon der
    Material-ID-Pass nichts getroffen hat und der Punkt darum gar nicht in der Maske
    liegt. Würde der Riegel hier feuern, wäre er bei jeder Szene rot und damit wertlos.
    """
    soll, maske = _szene()
    for i, drin in enumerate(maske):
        assert not drin or soll[i] < geometrie_qa.HINTERGRUND_SCHWELLE_M
    aussen = [i for i, drin in enumerate(maske) if not drin]
    assert len(aussen) == 300, "es gibt reichlich Hintergrund ausserhalb der Maske"
    befund = geometrie_qa.durchsichtiges_soll(soll, maske)
    assert befund["durchsichtig"] is False


def test_ein_einzelnes_randpixel_bleibt_unter_der_nachsicht():
    """Material-ID und Tiefe entstehen in zwei Durchgängen mit verschiedenem
    Rekonstruktionsfilter. Ein Pixel Versatz an der Silhouette ist kein Befund."""
    gross = 40 * 40
    soll = [100.0] * gross
    maske = [True] * gross
    soll[0] = HINTERGRUND                       # 1 von 1600 = 0.06 %, unter dem Promille
    befund = geometrie_qa.durchsichtiges_soll(soll, maske)
    assert befund["anteil"] == pytest.approx(1 / gross)
    assert befund["anteil"] < geometrie_qa.MAX_DURCHSICHT_ANTEIL
    assert befund["durchsichtig"] is False


def test_verschieden_lange_karten_sind_ein_fehler_und_keine_null():
    with pytest.raises(geometrie_qa.QaError, match="verschieden lang"):
        geometrie_qa.durchsichtiges_soll([1.0, 2.0], [True])


def test_der_riegel_faengt_genau_den_rueckschritt_der_wie_ein_schlechtes_bild_aussieht():
    """**Der eigentliche Nachweis.** Dieselbe Ist-Schätzung, dieselbe Maske, dasselbe
    Bauwerk — nur einmal mit dichtem und einmal mit durchsichtigem Soll. Der Score fällt,
    ohne dass am Bild etwas schlechter geworden wäre. Genau dieser Fall lief am
    03.09.2026 als «Bildwert 0.000» durch, und niemand konnte ihn benennen.

    Die Probe kann widersprechen: Fiele der Score nicht, gäbe es nichts zu riegeln — und
    schwiege der Riegel beim durchsichtigen Soll, fände er den Fall nicht.
    """
    dicht, maske = _szene()
    scheiben = {(x, y) for x in range(6, 14) for y in range(6, 10)}
    loechrig, _ = _szene(scheiben)

    # Die Ist-Karte ist aus dem DICHTEN Soll abgeleitet — sie zeigt die Fassade, so wie
    # das erzeugte Bild sie zeigt. Sie ist in beiden Durchgängen dieselbe.
    ist = [None if w >= geometrie_qa.HINTERGRUND_SCHWELLE_M else 3.0 * w + 7.0
           for w in dicht]
    ist = [HINTERGRUND if w is None else w for w in ist]

    score_dicht = geometrie_qa.geometrie_score(
        dicht, ist, polaritaet=geometrie_qa.POLARITAET_TIEFE)["score"]
    score_loechrig = geometrie_qa.geometrie_score(
        loechrig, ist, polaritaet=geometrie_qa.POLARITAET_TIEFE)["score"]

    assert score_loechrig < score_dicht, (
        "das durchsichtige Soll muss den Score druecken — sonst gaebe es nichts zu riegeln")
    assert geometrie_qa.durchsichtiges_soll(dicht, maske)["durchsichtig"] is False
    assert geometrie_qa.durchsichtiges_soll(loechrig, maske)["durchsichtig"] is True


def test_der_vorbehalt_steht_OBEN_im_urteil_und_nicht_nur_im_unterwoerterbuch():
    """Wer nur ``score`` liest, muss den Vorbehalt trotzdem sehen. Am 03.09.2026 stand
    oben auf dem Schirm eine 0.000 und sonst nichts."""
    scheiben = {(x, y) for x in range(6, 12) for y in range(6, 12)}
    soll, maske = _szene(scheiben)
    ist = [1.0 / (1.0 + w) for w in soll]

    ergebnis = tiefenschaetzer.qa_gegen_soll(
        __file__, soll, schaetzer="depth-anything-v2-small",
        modell=lambda p: {"tiefen": ist, "breite": BREITE, "hoehe": HOEHE},
        breite=BREITE, hoehe=HOEHE, maske=maske,
        hintergrund_strategie=tiefenschaetzer.HG_WIE_SOLL,
    )
    assert ergebnis["soll_durchsichtig"]["durchsichtig"] is True
    assert any("SOLL-Karte ist durchsichtig" in w for w in ergebnis["warnungen"]), (
        "der Vorbehalt gehoert in die Warnungen des Laufs, nicht nur in ein Unterfeld")


def test_ohne_maske_bleibt_der_riegel_ungemessen_und_meldet_nicht_in_ordnung():
    """``None`` heisst in diesem Projekt *nicht gemessen* und nicht *in Ordnung*."""
    soll, _ = _szene()
    ist = [1.0 / (1.0 + w) for w in soll]
    ergebnis = tiefenschaetzer.qa_gegen_soll(
        __file__, soll, schaetzer="depth-anything-v2-small",
        modell=lambda p: {"tiefen": ist, "breite": BREITE, "hoehe": HOEHE},
        breite=BREITE, hoehe=HOEHE, maske=None,
    )
    assert ergebnis["soll_durchsichtig"] is None
