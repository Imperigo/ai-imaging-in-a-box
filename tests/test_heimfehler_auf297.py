"""Die Befunde aus ``auf-20261021-297`` (HomeStation, 21.10.2026): ``ausserhalb_umriss_anteil`` geeicht.

**N2** — die Zahl zählte breite Zeilen viel zu klein (3d: 0,30 gemeldet, nachgezählt 2,22). Sie
zählte nur, was der Tiefenschätzer «so nah wie das Haus» sah; die Nähe auf dem Haus liegt eng
beisammen, und eine Zeile wenig dahinter fiel durch. Seit der Eichung zählt alles, was im
Soll-Hintergrund **nicht Himmel** ist; ohne Himmel im Bild (Gipsmodell vor Fels- oder Studiowand)
gilt die alte Zählung als Rückfall.

**N1** folgt daraus nicht: Mit der geeichten Zahl liegen alle Aussenbilder bei 2,0–2,3, und die
Zahl trennt «teilweise erkennbar» nicht von «nicht erkennbar». Der Auslöser bleibt, wie er ist
(Protokoll 74 §169, Tabelle).

Reine Funktionen, synthetische Karten (Regel 3); die Zahlen der Bilder sind die aus 295–297, im
Container mit Depth Anything V2 Small an den Bildern im Repo nachgerechnet.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from aiimaging import auftrag, baumasse, kosmo_szene, umriss

WURZEL = Path(__file__).resolve().parents[1]
B, H = 40, 30


def _szene(*, hinten=None, himmel=0.0, wand=None):
    """Haus 10 x 14 in der Mitte (Nähe 2,0–2,4 wie 297 3d), Platte, Boden; daneben wahlweise
    eine Zeile ``hinten`` (Nähe), sonst Himmel — oder überall eine ``wand`` (Nähe je Spalte)."""
    naehe, soll, haus, boden = [], [], [], []
    for y in range(H):
        for x in range(B):
            ist_haus = 15 <= x <= 24 and 8 <= y <= 21
            platte = y == 22
            soll.append(ist_haus or platte)
            haus.append(ist_haus)
            boden.append(y > 22)
            if ist_haus:
                naehe.append(2.0 + 0.4 * (x - 15) / 9)
            elif platte or y > 22:
                naehe.append(3.0)
            elif wand is not None:
                naehe.append(wand(x, y))
            elif hinten is not None and 10 <= y <= 21:
                naehe.append(hinten)                   # Zeile ueber die ganze Breite
            else:
                naehe.append(himmel)
    return naehe, soll, haus, boden


# ====================================================================== N2 · die Eichung

def test_die_zeile_hinter_dem_haus_zaehlt_jetzt():
    naehe, soll, haus, boden = _szene(hinten=1.9)        # knapp hinter dem fernen Fuenftel
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    assert aus["verfahren"] == baumasse.VERFAHREN and not aus["verfahren_grund"]
    assert aus["n_nah"] == 0 and aus["anteil_haus_nah"] == 0.0, "die alte Zaehlung sah nichts"
    assert aus["n_neu"] > 0 and aus["anteil_haus"] > 1.0
    assert 0.0 < aus["himmel_anteil"] < 1.0 and not aus["grund"]
    # Zwischen nah und neu liegt genau die Zeile; der Himmel zaehlt nicht.
    naehe_leer, *_ = _szene()
    leer = baumasse.ausserhalb_umriss(naehe_leer, soll, B, H, haus=haus, trennhilfe=boden)
    assert leer["n_neu"] == 0 and leer["himmel_anteil"] == 1.0


def test_himmel_bei_null_und_darunter_und_unendlich_fern():
    for himmel in (0.0, -0.3, 0.09, -math.inf):
        naehe, soll, haus, boden = _szene(himmel=himmel)
        aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
        assert aus["n_neu"] == 0 and aus["verfahren"] == baumasse.VERFAHREN, himmel
    # Ueber einem Zwanzigstel der Hausgrenze ist es ferne Struktur (Huegel, Baum): zaehlt.
    naehe, soll, haus, boden = _szene(hinten=0.3)
    assert baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)["n_neu"] > 0


def test_ohne_himmel_gilt_die_alte_zaehlung():
    """Das Gipsmodell vor einer Fels- oder Studiowand: «nicht Himmel» waere alles."""
    wand = lambda x, y: 0.8 + 0.03 * x                   # noqa: E731  — rechts naeher (bis 2,0)
    naehe, soll, haus, boden = _szene(wand=wand)
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    assert aus["himmel_anteil"] == 0.0
    assert aus["verfahren"] == baumasse.VERFAHREN_RUECKFALL
    assert "Kein Himmel" in aus["verfahren_grund"] and not aus["grund"]
    assert aus["n_neu"] == aus["n_nah"] and aus["anteil_haus"] == aus["anteil_haus_nah"]
    assert aus["anteil_haus"] < baumasse.SCHWELLE_ANTEIL_HAUS


def test_der_rueckfall_greift_unter_zwei_prozent_himmel():
    naehe, soll, haus, boden = _szene(wand=lambda x, y: 1.0)
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    bereich = aus["n_bereich"]
    # Ein Fleck Himmel knapp unter / knapp ueber der Grenze
    for anteil, erwartet in ((0.015, baumasse.VERFAHREN_RUECKFALL), (0.03, baumasse.VERFAHREN)):
        neu = list(naehe)
        frei = [i for i in range(B * H) if i // B < 5]  # oberste Zeilen liegen im Bereich
        for i in frei[:math.ceil(anteil * bereich)]:
            neu[i] = 0.0
        assert baumasse.ausserhalb_umriss(neu, soll, B, H, haus=haus,
                                          trennhilfe=boden)["verfahren"] == erwartet, anteil


def test_ohne_positive_hausgrenze_kein_himmel_und_rueckfall():
    naehe, soll, haus, boden = _szene(hinten=-1.0)
    naehe = [-3.0 if h else v for v, h in zip(naehe, haus)]
    aus = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    assert aus["himmel_grenze"] is None and aus["verfahren"] == baumasse.VERFAHREN_RUECKFALL
    assert aus["verfahren_grund"]


def test_die_werte_sind_benannt_und_die_schwellen_bleiben():
    assert baumasse.HIMMEL_NAEHE_ANTEIL == 0.05
    assert baumasse.MINDEST_HIMMEL_ANTEIL == 0.02
    assert baumasse.SCHWELLE_ANTEIL_HAUS == 0.25
    assert baumasse.HAUS_QUANTIL == 0.20
    assert "auf-20261021-297" in baumasse.HERKUNFT and "gesetzt" in baumasse.HERKUNFT
    assert umriss.WIEDERERKENNUNG_AUSSERHALB_ANTEIL == 1.5
    assert umriss.WIEDERERKENNUNG_GEOM_IOU_BEI_AUSSERHALB == 0.3
    assert umriss.WIEDERERKENNUNG_FLAECHE_VERHAELTNIS == 2.0
    doc = baumasse.__doc__
    assert "nicht Himmel" in doc and "Rückfall" in doc and "§169" in doc


def test_nur_die_zahl_geht_in_den_vertrag():
    """Die neuen Felder stehen im Befund, ins ``qa`` geht weiter nur ``anteil_haus``."""
    naehe, soll, haus, boden = _szene(hinten=1.9)
    befund = baumasse.ausserhalb_umriss(naehe, soll, B, H, haus=haus, trennhilfe=boden)
    qa, hinweise = {}, []
    kosmo_szene._ausserhalb_eintragen(
        qa, None, [{"kamera": "sSE", "geometrie_urteil": {"ausserhalb_umriss": befund}}], hinweise)
    assert qa == {kosmo_szene.FELD_AUSSERHALB: befund["anteil_haus"]}
    assert len(hinweise) == 1 and kosmo_szene.SATZ_AUSSERHALB in hinweise[0]


# ====================================================================== N1 · der Ausloeser bleibt

N_SOLL = 67541
#: Die KI-Bilder aus 295–297: (geom_iou, n_ist/n_soll, ausserhalb alt, ausserhalb neu (Container),
#: Haus von Auge erkannt). «teilweise» gilt als erkannt (so in 296 entschieden).
BILDER = {
    "297_1_strasse": (0.197, 2.457, 2.1481, 3.228, False),
    "297_3a_mittag_f10": (0.491, 1.142, 1.0077, 2.094, True),          # teilweise
    "297_3b_mittag_f10_leer": (0.393, 1.162, 0.8636, 1.956, True),     # teilweise
    "297_3c_mittag_std": (0.516, 1.796, 0.7674, 2.204, False),
    "297_3d_mittag_std_leer": (0.607, 1.283, 0.2959, 2.112, False),
    "297_4_weiss_f10": (0.867, 1.145, 0.0, 0.0, True),
    "297_4z_weiss_std": (0.719, 1.250, 0.1946, 0.198, True),
    "296_4a_weiss_f10": (0.870, 1.146, 0.0, 0.0, True),
    "296_abend_voll": (0.005, 1.274, 2.0855, 4.287, False),
    "295_abend_vorschau": (0.384, 1.136, 1.9185, 2.111, True),         # teilweise
}


@pytest.mark.parametrize("name", sorted(BILDER))
def test_mit_der_geeichten_zahl_entscheidet_die_regel_wie_bisher(name):
    """Kein Urteil ändert sich durch die Eichung — auch nicht die zwei bekannten Fehlurteile."""
    iou, verhaeltnis, alt, neu, _ = BILDER[name]
    n_ist = round(verhaeltnis * N_SOLL)
    vorher = umriss.umriss_gilt(iou, n_ist=n_ist, n_soll=N_SOLL, ausserhalb_anteil=alt)
    nachher = umriss.umriss_gilt(iou, n_ist=n_ist, n_soll=N_SOLL, ausserhalb_anteil=neu)
    assert vorher is nachher, name


def test_3c_und_3d_bleiben_ein_offener_befund():
    """Dokumentiert, nicht behoben: die Zahl trennt «teilweise» nicht von «nicht erkennbar»."""
    for name in ("297_3c_mittag_std", "297_3d_mittag_std_leer"):
        iou, verhaeltnis, _, neu, erkannt = BILDER[name]
        assert erkannt is False
        assert umriss.umriss_gilt(iou, n_ist=round(verhaeltnis * N_SOLL), n_soll=N_SOLL,
                                  ausserhalb_anteil=neu) is True
    teilweise = [BILDER[n][3] for n in ("297_3a_mittag_f10", "295_abend_vorschau")]
    nicht = [BILDER[n][3] for n in ("297_3c_mittag_std", "297_3d_mittag_std_leer")]
    assert max(teilweise) >= min(nicht) - 0.01, "kein Schnitt in der Zahl allein"


# ====================================================================== der Messauftrag 299

def test_der_messauftrag_299_ist_gueltig_und_fragt_alle_punkte():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-299.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa" and daten["rang"] == 86
    assert daten["params"]["folgt_auf"] == "auf-20261021-297"
    assert daten["params"]["neue_laeufe"] == 1
    text = daten["anweisung"]
    for stichwort in ("WAS AM HEIM-PC JETZT ANDERS RECHNET", "nicht_himmel_aus_tiefe_im_soll_hintergrund",
                      "RUECKFALL", "anteil_haus_nah", "himmel_anteil", "OHNE NEUEN KI-LAUF",
                      "KONTROLLLAUF mittag Standard", "bildpunktgleich", "wiederzuerkennen",
                      "leerer_hintergrund", "25-%-Quantil", "no people", "NICHT TUN"):
        assert stichwort in text, stichwort
