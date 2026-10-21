"""Deckungsgleich = gleiche Grundlage UND gleiche Form (Video-Befund L4-1, 21.10.2026), synthetisch."""
from __future__ import annotations

import pytest

from aiimaging import bildschreiben, varianten as v


def test_vier_urteile():
    assert v.deckung(True, 0.5)["urteil"] == v.DECKUNGSGLEICH
    d = v.deckung(True, 0.2)
    assert d["urteil"] == v.FORM_WEICHT_AB and d["warnung"] is True
    assert d["satz"] == "gleiche Grundlage, Form weicht ab"
    assert v.deckung(True, None)["urteil"] == v.DECKUNG_UNGEMESSEN
    assert v.deckung(False, 0.99)["urteil"] == v.ANDERE_GRUNDLAGE
    assert v.deckung(True, v.DECKUNG_KANTEN_IOU_SCHWELLE)["urteil"] == v.DECKUNGSGLEICH


def test_die_schwelle_ist_als_setzung_gekennzeichnet():
    d = v.deckung(True, 0.4)
    assert d["schwelle"] == 0.30 and "gesetzt, nicht gemessen" in d["herkunft"]
    with pytest.raises(ValueError):
        v.deckung(True, 0.4, schwelle=1.5)


def _bild(pfad, kante_bei):
    farben = [(255, 255, 255) if x < kante_bei else (0, 0, 0) for _ in range(16) for x in range(16)]
    bildschreiben.schreibe_farb_png(pfad, farben, 16, 16)
    return pfad


def test_aus_bildern_gleiche_form_und_versetzte_form(tmp_path):
    grund = _bild(tmp_path / "g.png", 8)
    assert v.deckung_aus_bildern(_bild(tmp_path / "a.png", 8), grund, True)["urteil"] == v.DECKUNGSGLEICH
    weit = v.deckung_aus_bildern(_bild(tmp_path / "b.png", 3), grund, True)
    assert weit["urteil"] == v.FORM_WEICHT_AB and weit["kanten_iou"] < 0.30


def test_ohne_grundbild_oder_mit_anderer_groesse_nicht_gemessen(tmp_path):
    ki = _bild(tmp_path / "a.png", 8)
    assert v.deckung_aus_bildern(ki, None, True)["urteil"] == v.DECKUNG_UNGEMESSEN
    klein = tmp_path / "k.png"
    bildschreiben.schreibe_farb_png(klein, [(0, 0, 0)] * 4, 2, 2)
    d = v.deckung_aus_bildern(ki, klein, True)
    assert d["urteil"] == v.DECKUNG_UNGEMESSEN and "ungleiche Masse" in d["grund"]
