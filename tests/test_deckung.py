"""Deckungsgleich = gleiche Grundlage UND gleiche Form (Video-Befund L4-1, 21.10.2026), synthetisch."""
from __future__ import annotations

import pytest

from aiimaging import bildschreiben, varianten as v


def test_vier_urteile():
    assert v.deckung(True, 0.5)["urteil"] == v.DECKUNGSGLEICH
    d = v.deckung(True, 0.05)
    assert d["urteil"] == v.FORM_WEICHT_AB and d["warnung"] is True
    assert d["satz"] == "gleiche Grundlage, Form weicht ab"
    assert v.deckung(True, None)["urteil"] == v.DECKUNG_UNGEMESSEN
    assert v.deckung(False, 0.99)["urteil"] == v.ANDERE_GRUNDLAGE
    assert v.deckung(True, v.DECKUNG_KANTEN_IOU_SCHWELLE)["urteil"] == v.DECKUNGSGLEICH


def test_die_schwelle_ist_als_setzung_gekennzeichnet():
    d = v.deckung(True, 0.4)
    assert d["schwelle"] == 0.10 and "gesetzt aus auf-20261021-317 (vier Läufe" in d["herkunft"]
    assert "nicht gemessen" not in d["herkunft"]
    with pytest.raises(ValueError):
        v.deckung(True, 0.4, schwelle=1.5)


def test_die_schwelle_trennt_die_vier_laeufe_aus_317():
    """auf-20261021-317: K Form nein 0,033; M2, BI55, BI40 Form ja 0,197 / 0,635 / 0,739.

    Die alte Setzung 0,30 stufte M2 als «Form weicht ab» ein, obwohl Hauptbau, Anbau und
    Dachaufbau an derselben Stelle stehen (Augenurteil ja). Die neue trennt alle vier richtig.
    """
    augenurteil = {0.033: False, 0.1969: True, 0.6347: True, 0.7387: True}
    for iou, form_ja in augenurteil.items():
        assert (v.deckung(True, iou)["urteil"] == v.DECKUNGSGLEICH) is form_ja, iou
    assert v.deckung(True, 0.1969, schwelle=0.30)["urteil"] == v.FORM_WEICHT_AB   # der alte Fehler
    assert 0.033 < v.DECKUNG_KANTEN_IOU_SCHWELLE < 0.1969


def _bild(pfad, kante_bei):
    farben = [(255, 255, 255) if x < kante_bei else (0, 0, 0) for _ in range(16) for x in range(16)]
    bildschreiben.schreibe_farb_png(pfad, farben, 16, 16)
    return pfad


def test_aus_bildern_gleiche_form_und_versetzte_form(tmp_path):
    grund = _bild(tmp_path / "g.png", 8)
    assert v.deckung_aus_bildern(_bild(tmp_path / "a.png", 8), grund, True)["urteil"] == v.DECKUNGSGLEICH
    weit = v.deckung_aus_bildern(_bild(tmp_path / "b.png", 3), grund, True)
    assert weit["urteil"] == v.FORM_WEICHT_AB and weit["kanten_iou"] < v.DECKUNG_KANTEN_IOU_SCHWELLE


def test_ohne_grundbild_oder_mit_anderer_groesse_nicht_gemessen(tmp_path):
    ki = _bild(tmp_path / "a.png", 8)
    assert v.deckung_aus_bildern(ki, None, True)["urteil"] == v.DECKUNG_UNGEMESSEN
    klein = tmp_path / "k.png"
    bildschreiben.schreibe_farb_png(klein, [(0, 0, 0)] * 4, 2, 2)
    d = v.deckung_aus_bildern(ki, klein, True)
    assert d["urteil"] == v.DECKUNG_UNGEMESSEN and "ungleiche Masse" in d["grund"]


def test_abholer_misst_die_deckung_nur_mit_beiden_bildern(tmp_path):
    from aiimaging import abholer
    grund = _bild(tmp_path / "g.png", 8)
    d = abholer.deckung_der_kamera(_bild(tmp_path / "a.png", 3), grund)
    assert d["urteil"] == v.FORM_WEICHT_AB and 0.0 <= d["kanten_iou"] < v.DECKUNG_KANTEN_IOU_SCHWELLE
    assert abholer.deckung_der_kamera(tmp_path / "a.png", None) is None
    assert abholer.deckung_der_kamera(None, grund) is None
    klein = tmp_path / "k.png"
    bildschreiben.schreibe_farb_png(klein, [(0, 0, 0)] * 4, 2, 2)
    assert abholer.deckung_der_kamera(klein, grund) is None      # ungleiche Masse: kein Feld


def test_im_ergebnis_je_kamera_und_nur_wenn_gemessen():
    from aiimaging import abholer, kosmo_szene
    u = {"kamera": "s", "score": 0.7, "bestanden": True, "geom_iou": 0.6}
    kameras = [dict(u, geometrie_urteil=u, deckung={"kanten_iou": 0.4213}),
               dict(u, kamera="n", geometrie_urteil=dict(u, kamera="n"))]
    je = abholer._je_kamera_mit_lieferung(kameras)
    assert [e.get("deckung") for e in je] == [0.4213, None]
    aus = kosmo_szene.als_ergebnis("vis-1", ["s.png", "n.png"], geometrie_urteil=u, je_kamera=je)
    assert [k.get("deckung") for k in aus["qa_je_kamera"]] == [0.4213, None]
    assert "deckung" not in aus["qa"]
    # Ein Wert ausserhalb 0..1 oder ein Wahrheitswert reist nicht.
    schief = kosmo_szene.als_ergebnis("vis-1", ["s.png"], geometrie_urteil=u,
                                      je_kamera=[dict(je[0], deckung=1.5)])
    assert "deckung" not in schief["qa_je_kamera"][0]
