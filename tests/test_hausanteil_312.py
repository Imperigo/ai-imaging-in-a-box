"""auf-20261021-312, B1 und B2: der Hausanteil am KI-Bild unterschätzt, der an der Grundlage zählt
die Platte mit.

**B1 (gemessen):** Malt die KI das Haus grösser als bestellt, blieb ``haus_im_bild`` bei
0,15–0,18 hängen (nachgezählt 0,31–0,47); nur bei gleichem Ausschnitt (Seed 11: 0,108 gegen
0,129) passte es. Grund: Gezählt wurde nur, was im engen Nähe-Band des Soll-Umrisses lag — die
Flügel eines breiten Hauses reichen vor und zurück und fielen heraus.

**B2 (gemessen):** ``qa.haus_anteil_grundlage`` = ``anteil_soll`` zählt die Platte mit (60 m:
77016 = 66293 Haus + 10723 Platte, 13,4 % statt 11,6 %).

Nachgestellt an einer synthetischen Szene mit Lochkamera (Regel 3): Horizont, ebener Boden
(Nähe wächst linear unter dem Horizont), Himmel bei null, ein Haus auf dem Boden. Die beiden
Fälle aus 312: gleicher Ausschnitt (Seed 11) und ein breites, näheres Haus mit
zurückweichenden Flügeln und einer Hecke davor (482913 / normal).
"""
from __future__ import annotations

import pytest

from aiimaging import baumasse, kosmo_szene

B, H = 320, 200
HORIZONT = 80
G = 0.01            # Nähe je Zeile unter dem Horizont (Disparität des Bodens)


def _boden(y: int) -> float:
    return G * (y - HORIZONT) if y > HORIZONT else -0.01


def _grundlage():
    """Soll: Haus Spalten 140–179, Zeilen 90–139 (Fuss 140), Platte Zeilen 140–147, 110–209."""
    haus = [140 <= x <= 179 and 90 <= y <= 139 for y in range(H) for x in range(B)]
    platte = [110 <= x <= 209 and 140 <= y <= 147 for y in range(H) for x in range(B)]
    soll = [a or p for a, p in zip(haus, platte)]
    return soll, haus


def _ki_bild(*, breit: bool):
    """Die Nähe des KI-Bilds und die wahre Hausfläche darin.

    ``breit=False``: das Haus wie bestellt (Seed 11). ``breit=True``: Spalten 30–289, Zeilen
    70–149 (Fuss 150, also näher), Mitte 100–219 frontal, die Flügel weichen nach aussen auf
    0,7 der Nähe zurück; davor eine Hecke (Zeilen 150–169, deutlich näher, mit Sprung).
    """
    naehe, wahr = [], 0
    for y in range(H):
        for x in range(B):
            if breit:
                fuss = 150
                im_haus = 30 <= x <= 289 and 70 <= y < fuss
                mitte = _boden(fuss)
                if x < 100:
                    w = mitte * (1.0 - 0.3 * (100 - x) / 70)
                elif x > 219:
                    w = mitte * (1.0 - 0.3 * (x - 219) / 70)
                else:
                    w = mitte
                hecke = 60 <= x <= 259 and 150 <= y <= 169
            else:
                fuss = 140
                im_haus = 140 <= x <= 179 and 90 <= y < fuss
                w = _boden(fuss)
                hecke = False
            if im_haus:
                naehe.append(w)
                wahr += 1
            elif hecke:
                naehe.append(_boden(y) * 1.25)
            else:
                naehe.append(_boden(y))
    return naehe, wahr


def test_b2_die_grundlage_zaehlt_mit_maske_das_haus_ohne_platte():
    soll, haus = _grundlage()
    naehe, _ = _ki_bild(breit=False)
    mit = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    ohne = baumasse.haus_im_bild(naehe, soll, B, H)
    assert mit["grundlage_aus"] == "bauwerksmaske" and mit["n_soll"] == sum(haus)
    assert ohne["grundlage_aus"] == "soll_silhouette" and ohne["n_soll"] == sum(soll)
    assert mit["anteil_grundlage"] < ohne["anteil_grundlage"]


def test_b2_im_ergebnis_steht_der_hausanteil_ohne_platte():
    urteil = {"kamera": "sSE", "anteil_soll": 0.1337,
              "haus_im_bild": {"anteil": 0.43, "anteil_grundlage": 0.1151,
                               "grundlage_aus": "bauwerksmaske"}}
    assert kosmo_szene.hausanteil_des_urteils(urteil) == (0.1151, 0.43)
    alt = dict(urteil, haus_im_bild={"anteil": 0.43, "anteil_grundlage": 0.1337})
    assert kosmo_szene.hausanteil_des_urteils(alt) == (0.1337, 0.43)


def test_b1_gleicher_ausschnitt_trifft_wie_seed_11():
    soll, haus = _grundlage()
    naehe, wahr = _ki_bild(breit=False)
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    assert aus["n_bild"] == pytest.approx(wahr, rel=0.10)
    assert baumasse.rahmt_anders(aus["anteil_grundlage"], aus["anteil"]) is False


def test_b1_das_breite_haus_zaehlt_ganz_und_die_alte_zahl_nicht():
    soll, haus = _grundlage()
    naehe, wahr = _ki_bild(breit=True)
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    # Gewachsen: auf ein Zehntel genau (Hecke und Boden nicht dabei, die Flügel schon).
    assert aus["n_bild"] == pytest.approx(wahr, rel=0.10)
    # Das enge Band (bis 312) schneidet die Flügel ab — dieselbe Lücke wie gemessen.
    assert aus["n_band"] < 0.6 * wahr
    assert baumasse.rahmt_anders(aus["anteil_grundlage"], aus["anteil"]) is True


def test_der_boden_zaehlt_nicht_mit():
    """Ein Haus, dessen Fuss stetig in den Boden übergeht: Der Boden wächst nicht mit."""
    soll, haus = _grundlage()
    naehe, wahr = _ki_bild(breit=False)
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    boden_unter_dem_haus = B * (H - 141)
    assert aus["n_bild"] < wahr + 0.05 * boden_unter_dem_haus


@pytest.mark.parametrize("grundlage, nachgezaehlt, erwartet", [
    # Die Nachzählung aus 312 gegen das Haus der Grundlage ohne Platte (11,6 % / 10,1 %):
    (0.1158, 0.4348, True), (0.1158, 0.3054, True), (0.1158, 0.1290, False),
    (0.1010, 0.4743, True),
])
def test_die_rahmungsschwelle_trennt_die_laeufe_aus_312(grundlage, nachgezaehlt, erwartet):
    assert baumasse.rahmt_anders(grundlage, nachgezaehlt) is erwartet
