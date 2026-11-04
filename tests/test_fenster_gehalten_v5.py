"""Fenster-Pruefung v5 (A0158): ein grau uebermaltes Fensterband faellt auf, auch wenn ein anderes haelt.

Ausschnitt aus zwei echten Laeufen des Testhauses (Auftrag auf-20261023-346), 240 x 290 Bildpunkte:
«voll» zeigt die Fenster, in der «vorschau» ist das Obergeschoss grau uebermalt und das Erdgeschoss
warm. Die Kennzahlen aller 12 Bilder des Eichsatzes von A0092 stehen in ``kennzahlen.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

from aiimaging import bildlesen, varianten

ORDNER = Path(__file__).parent / "fixtures" / "glas-v5"
AUSSCHNITT = json.loads((ORDNER / "ausschnitt.json").read_text(encoding="utf-8"))
KENNZAHLEN = json.loads((ORDNER / "kennzahlen.json").read_text(encoding="utf-8"))["laeufe"]


def _bild(name):
    punkte, breite, hoehe = bildlesen.lies_png_farben(ORDNER / f"{name}.png")
    return list(punkte), breite, hoehe


def _miss(ki):
    grund, breite, _ = _bild("grund")
    kennung, _, _ = _bild("kennung")
    return varianten.fenster_gehalten(ki, grund, kennung, varianten.glasfarben(AUSSCHNITT["tabelle"]),
                                      breite=breite)


def _zusammen(oben, unten, grenze):
    """Oben die Zeilen des einen Bilds, unten die des anderen."""
    a, breite, _ = _bild(oben)
    b, _, _ = _bild(unten)
    return a[:grenze * breite] + b[grenze * breite:]


def test_die_vorschau_faellt_am_obergeschoss_durch():
    befund = _miss(_bild("ki_vorschau")[0])
    assert befund["gehalten"] is False
    assert 0 in befund["band_nicht_gehalten"]


def test_nur_das_obergeschoss_uebermalt_faellt_auf_obwohl_die_gesamtzahl_haelt():
    """Der Kern des Befunds: Obergeschoss aus der Vorschau, Erdgeschoss aus dem vollen Lauf."""
    befund = _miss(_zusammen("ki_vorschau", "ki_voll", AUSSCHNITT["grenze_og_eg"]))
    assert befund["anteil"] >= varianten.FENSTER_GEHALTEN_SCHWELLE, befund
    assert befund["gehalten"] is False
    assert befund["band_nicht_gehalten"] == [0]


def test_der_volle_lauf_ist_gehalten():
    befund = _miss(_bild("ki_voll")[0])
    assert befund["gehalten"] is True
    assert befund["band_nicht_gehalten"] == []


def test_fenster_aus_bildern_urteilt_je_band():
    befund = varianten.fenster_aus_bildern(
        ORDNER / "ki_vorschau.png", ORDNER / "grund.png", ORDNER / "kennung.png", AUSSCHNITT["tabelle"])
    assert befund["gehalten"] is False and 0 in befund["band_nicht_gehalten"]


def test_ohne_breite_urteilt_allein_der_gesamtanteil():
    grund, _, _ = _bild("grund")
    kennung, _, _ = _bild("kennung")
    befund = varianten.fenster_gehalten(_zusammen("ki_vorschau", "ki_voll", AUSSCHNITT["grenze_og_eg"]),
                                        grund, kennung, varianten.glasfarben(AUSSCHNITT["tabelle"]))
    assert "baender" not in befund and befund["gehalten"] is True


def test_der_eichsatz_bleibt_zwoelf_von_zwoelf():
    assert len(KENNZAHLEN) == 12
    for lauf in KENNZAHLEN:
        assert lauf["gehalten"] is (not lauf["name"].startswith("vorschau-")), lauf["name"]


def test_die_vorschau_ist_am_obergeschoss_durchgefallen_nicht_am_erdgeschoss():
    lauf = next(z for z in KENNZAHLEN if z["name"].startswith("vorschau-"))
    assert lauf["band_nicht_gehalten"] == [0]
    assert lauf["baender"][0]["anteil"] >= varianten.FENSTER_GEHALTEN_SCHWELLE


def test_die_schwelle_liegt_klar_zwischen_uebermalt_und_sichtbar():
    kontraste = [b["kontrast"] for z in KENNZAHLEN for b in z["baender"]]
    uebermalt = [b["kontrast"] for z in KENNZAHLEN if z["name"].startswith("vorschau-") for b in z["baender"][:1]]
    sichtbar = sorted(kontraste)[1:]
    assert max(uebermalt) * 3 < varianten.FENSTER_BAND_KONTRAST_ANTEIL < min(sichtbar) * 0.8


def test_bilder_im_repo_sind_nur_ausschnitte():
    for name in ("ki_voll", "ki_vorschau", "grund", "kennung"):
        _, breite, hoehe = _bild(name)
        assert (breite, hoehe) == (240, 290)
