"""Video-Befund L4-2 (21.10.2026): der Hausanteil an Grundlage UND KI-Bild, und was «0.0» misst.

Die Prüfung meldete «Das Haus fuellt nur 2.9 %» und «Geometrie 0.0 gegen 0.65» neben einem
KI-Bild mit sichtbar grossem Haus. Gemessen war nur die Grundlage; die KI hatte den Ausschnitt
näher gewählt. Und jede 0.0 in den Heim-PC-Ergebnissen 290/296/297/298 ist ein bei null
abgeschnittener Wert (Rangkorrelation mit falschem Vorzeichen), kein Messfehler.

Testdaten synthetisch (Regel 3), reine Funktionen (Regel 4).
"""
from __future__ import annotations

import math

import pytest

from aiimaging import baumasse, kosmo_szene
from aiimaging import tiefenschaetzer as ts

B, H = 40, 30


def _szene(*, ki_naeher=False, baum=False, boden_nah=True):
    """Soll: Haus Spalten 18–21, Zeilen 12–15 (16 von 1200 Punkten, 1,3 %).

    KI-Bild (Nähe, Disparität): Himmel 0,02; Haus 1,0–1,1. ``ki_naeher``: die KI malt das
    Haus grösser, Spalten 12–27, Zeilen 6–17 (192 Punkte, 16 %) — sonst genau wie das Soll.
    ``baum``: ein Fleck in Hausnähe, aber nicht am Haus (Spalten 2–5, Zeilen 4–7).
    ``boden_nah``: Zeilen ab 24 sind Vordergrund, deutlich näher (2,0).
    """
    soll, naehe = [], []
    for y in range(H):
        for x in range(B):
            soll.append(18 <= x <= 21 and 12 <= y <= 15)
            im_ki = (12 <= x <= 27 and 6 <= y <= 17) if ki_naeher else soll[-1]
            if im_ki:
                naehe.append(1.0 + 0.1 * (y % 2))
            elif baum and 2 <= x <= 5 and 4 <= y <= 7:
                naehe.append(1.02)
            elif boden_nah and y >= 24:
                naehe.append(2.0)
            else:
                naehe.append(0.02)
    return naehe, soll


def test_folgt_die_ki_der_grundlage_sind_beide_zahlen_gleich():
    naehe, soll = _szene()
    aus = baumasse.haus_im_bild(naehe, soll, B, H)
    assert aus["anteil_grundlage"] == pytest.approx(16 / 1200, abs=1e-4)
    assert aus["anteil"] == aus["anteil_grundlage"] and not aus["grund"]
    assert aus["verfahren"] == baumasse.VERFAHREN_HAUS_IM_BILD
    assert baumasse.rahmt_anders(aus["anteil_grundlage"], aus["anteil"]) is False


def test_naeher_gerahmt_misst_das_ki_bild_das_grosse_haus():
    naehe, soll = _szene(ki_naeher=True, baum=True)
    aus = baumasse.haus_im_bild(naehe, soll, B, H)
    # Das grosse Haus zählt ganz, der Baum (gleich nah, aber nicht am Haus) und der nahe
    # Vordergrund nicht.
    assert aus["n_bild"] == 16 * 12
    assert aus["anteil"] == pytest.approx(0.16, abs=1e-4)
    assert baumasse.rahmt_anders(aus["anteil_grundlage"], aus["anteil"]) is True


def test_gedachter_boden_und_ausgeblendetes_zaehlen_nie():
    naehe, soll = _szene(ki_naeher=True)
    unten = [i // B >= 16 for i in range(B * H)]          # die zwei untersten Hauszeilen
    aus = baumasse.haus_im_bild(naehe, soll, B, H, trennhilfe=unten)
    assert aus["n_bild"] == 16 * 10
    aus = baumasse.haus_im_bild(naehe, soll, B, H, ausgeblendet=unten)
    assert aus["n_bild"] == 16 * 10


def test_nie_eine_ausnahme():
    assert baumasse.haus_im_bild([1.0], [True], B, H)["anteil"] is None
    leer = baumasse.haus_im_bild([0.0] * (B * H), [False] * (B * H), B, H)
    assert leer["anteil"] is None and leer["grund"] and leer["anteil_grundlage"] == 0.0
    naehe, soll = _szene()
    assert baumasse.haus_im_bild(naehe, soll, B, H, trennhilfe=[True])["grund"]


@pytest.mark.parametrize("g, b, erwartet", [
    (0.029, 0.17, True), (0.17, 0.029, True), (0.30, 0.33, False),
    (0.01, 0.025, False),                 # doppelt, aber unter fünf Punkten
    (None, 0.2, None), (0.2, True, None),
])
def test_rahmt_anders(g, b, erwartet):
    assert baumasse.rahmt_anders(g, b) is erwartet


def test_die_zahl_kommt_aus_der_geometrie_qa(tmp_path):
    from test_tiefenschaetzer import attrappe
    pfad = tmp_path / "bild.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    naehe, soll = _szene(ki_naeher=True)
    soll_m = [20.0 if s else math.inf for s in soll]
    aus = ts.qa_gegen_soll(pfad, soll_m, modell=attrappe(naehe), breite=B, hoehe=H)
    assert aus["haus_im_bild"]["anteil"] == pytest.approx(0.16, abs=1e-4)
    assert aus["haus_im_bild"]["anteil_grundlage"] == pytest.approx(aus["anteil_soll"],
                                                                    abs=1e-4)


def _urteil(kamera, grundlage, bild, **mehr):
    return dict({"kamera": kamera, "score": 0.7, "bestanden": True, "geom_iou": 0.5,
                 "spearman": -0.4, "n_gemeinsam": 10, "n_soll": 12, "n_ist": 12,
                 "anteil_soll": grundlage},
                **({"haus_im_bild": {"anteil": bild}} if bild is not None else {}), **mehr)


def test_im_ergebnis_beide_zahlen_je_kamera_mit_satz_und_der_vertrag_bleibt():
    je = [{"kamera": "s", "geometrie_urteil": _urteil("s", 0.029, 0.17)},
          {"kamera": "nNW", "geometrie_urteil": _urteil("nNW", 0.31, 0.33)}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)
    assert e["qa"][kosmo_szene.FELD_HAUS_GRUNDLAGE] == 0.029
    assert e["qa"][kosmo_szene.FELD_HAUS_BILD] == 0.17
    assert [(k.get(kosmo_szene.FELD_HAUS_GRUNDLAGE), k.get(kosmo_szene.FELD_HAUS_BILD))
            for k in e["qa_je_kamera"]] == [(0.029, 0.17), (0.31, 0.33)]
    saetze = [h for h in e["qa"]["verdict"].get("hinweise") or ()
              if h.startswith(kosmo_szene.SATZ_RAHMT_ANDERS)]
    assert len(saetze) == 1 and "'s'" in saetze[0] and "17.0 %" in saetze[0] \
        and "2.9 %" in saetze[0] and "naeher" in saetze[0]
    # Ohne die neue Messung: kein Feld fürs Bild (kein null), die Grundlage bleibt.
    alt = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                   geometrie_urteil=_urteil("s", 0.029, None))
    assert kosmo_szene.FELD_HAUS_BILD not in alt["qa"]
    assert alt["qa"][kosmo_szene.FELD_HAUS_GRUNDLAGE] == 0.029
    assert alt["qa"]["geometry"] == e["qa"]["geometry"]


def test_randlos_innen_traegt_keinen_hausanteil():
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                 geometrie_urteil=_urteil("innen", 1.0, 0.9))
    assert kosmo_szene.FELD_HAUS_GRUNDLAGE not in e["qa"]
    assert kosmo_szene.FELD_HAUS_BILD not in e["qa"]


def test_die_null_sagt_was_sie_misst():
    """Der Fall aus dem Video: unter 20 %, Score 0 aus einer Rangkorrelation +0,50 bei
    Disparität (Heim-PC 296, Kamera 3b: spearman +0.5047, geometry_fidelity 0.0)."""
    urteil = {"gesamtwert_anwendbar": False, "polaritaet_zeichen": -1, "spearman": 0.5047,
              "geom_iou": 0.197}
    satz = kosmo_szene.geometrie_satz(0.0, 0.65, urteil)
    assert satz.startswith("Geometrie 0.0 gegen 0.65 — ")
    assert "nur Auskunft, nicht anwendbar" in satz
    assert "KI-Bild weicht von der Geometrie ab" in satz and "+0.50" in satz
    assert "kein Messfehler" in satz
    # Ohne Ueberdeckung: der zweite Grund.
    assert "Umrisse decken sich nicht" in kosmo_szene.geometrie_satz(
        0.0, 0.65, {"polaritaet_zeichen": None, "geom_iou": 0.0})
    # Eine echte Zahl bleibt wortgleich.
    assert kosmo_szene.geometrie_satz(0.7, 0.65, {"gesamtwert_anwendbar": True,
                                                  "polaritaet_zeichen": -1,
                                                  "spearman": -0.4}) == "Geometrie 0.7 gegen 0.65"


def test_der_satz_steht_im_grund_des_ergebnisses():
    u = _urteil("s", 0.029, 0.17, score=0.0, bestanden=None, spearman=0.5047,
                polaritaet_zeichen=-1, gesamtwert_anwendbar=False)
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=u)
    grund = e["qa"]["verdict"]["reason"]
    assert "NICHT BEURTEILBAR (Gebaeudeanteil)" in grund
    assert "Geometrie 0.0 gegen 0.65 — nur Auskunft" in grund
    assert "KI-Bild weicht von der Geometrie ab" in grund
