"""«1 Kamera», nicht «1 Kameras» — die Sätze des Kerns bei genau einem Stück.

Anlass (Kleinauftrag «1 Bilder», 24.10.2026, Protokoll 74 §276)
---------------------------------------------------------------
Die Sätze des Kerns setzten eine Zahl vor ein festes Mehrzahlwort. Bei einer Kamera — in
der Demo der häufigste Fall, ein Standpunkt «Eingang» — hiess es «Komposition, alle 1
Kameras», «schlechteste von 1 Kameras», «Keine der 1 Kameras», «0 von 1 Kameras
geliefert, 0 von 1 Bildern», auf der Visbox-Seite «1 Bilder eingetragen, 1 Varianten nicht
begonnen». Drei Proben hatten den falschen Wortlaut sogar festgeschrieben
(``test_befund``, ``test_abholen_cli``, ``test_flaeche_fuer_die_app``).

Gegen den Stand vor dem Fix sind 17 von 18 Proben rot; grün bleibt die Gegenprobe mit drei
Kameras — die Mehrzahl-Fälle halten die Grenze: Bei mehr als einem bleibt alles, wie es war.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, komposition, kosmo_szene, sprache, varianten

WURZEL = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("n, wort", [
    (0, "Kameras"), (1, "Kamera"), ("1", "Kamera"), (1.0, "Kamera"), (2, "Kameras"),
    (None, "Kameras"), ("unbekannt", "Kameras"), (True, "Kameras"),
])
def test_das_zaehlwort_ist_nur_bei_eins_einzahl(n, wort):
    assert sprache.zaehlwort(n, "Kamera", "Kameras") == wort


def test_anzahl_setzt_zahl_und_wort():
    assert sprache.anzahl(1, "Bild", "Bildern") == "1 Bild"
    assert sprache.anzahl(3, "Bild", "Bildern") == "3 Bildern"


def test_komposition_bei_einer_kamera():
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "komposition": {"beurteilt": True, "warnungen": ["Neigung …"]}}]})
    assert zeilen == ("Komposition, die einzige Kamera: Neigung",)
    assert not any("1 Kameras" in z for z in zeilen)


def test_geometrie_bei_einer_gemessenen_kamera():
    zeilen = abholer.befund_kurz({"geometrie_urteil": {"kameraspanne": {
        "n_gemessen": 1, "schlechtester": 0.7, "bester": 0.7}}})
    assert zeilen == ("Geometrie: 0.7000 (einzige gemessene Kamera)",)


def test_geometrie_bei_drei_kameras_bleibt():
    zeilen = abholer.befund_kurz({"geometrie_urteil": {"kameraspanne": {
        "n_gemessen": 3, "schlechtester": 0.66, "bester": 0.81}}})
    assert zeilen == ("Geometrie: 0.6600 (schlechteste von 3 Kameras, beste 0.8100)",)


def test_kameraspanne_einer_ungemessenen_kamera():
    hinweis = abholer._kameraspanne([{"kamera": "s", "score": None}])["hinweis"]
    assert hinweis.startswith("Die einzige Kamera ist nicht gemessen — weder Score")
    hinweis3 = abholer._kameraspanne(
        [{"kamera": k, "score": None} for k in ("s", "sSE", "nNW")])["hinweis"]
    assert hinweis3.startswith("Keine der 3 Kameras ist gemessen — weder Score")


def test_lieferstatus_einer_kamera():
    status, grund = kosmo_szene._lieferstatus_des_auftrags(
        [{"kamera": "s", "lieferstatus": "fehlgeschlagen", "lieferstatus_grund": "x",
          "bilder_soll": 1, "bilder_ist": 0}], uebersprungen=False, anzahl_bilder=0)
    assert status == "fehlgeschlagen"
    assert grund.startswith("0 von 1 Kamera geliefert, 0 von 1 Bild — "), grund


def test_lieferstatus_ohne_meldung_einer_kamera():
    _, grund = kosmo_szene._lieferstatus_des_auftrags(
        [{"kamera": "s"}], uebersprungen=False, anzahl_bilder=0)
    assert grund.startswith("NICHT FESTGESTELLT: 0 von 1 Kamera melden"), grund


def test_varianten_eine_ungemessene():
    satz = varianten.waehle([{"score": None}], schwelle=0.5)["begruendung"]
    assert satz.startswith("Die einzige Variante ist nicht gemessen"), satz
    satz3 = varianten.waehle([{"score": None}] * 3, schwelle=0.5)["begruendung"]
    assert satz3.startswith("Keine der 3 Varianten ist gemessen"), satz3


def test_komposition_neigung_einer_kamera():
    """Ein Satz aus einer Kamera ohne Neigungsangabe: «1 von 1 Kamera»."""
    from test_bezug_und_rollwinkel import _block, _satz
    satz = komposition.beurteile_kamerasatz(_satz(_block(kuerzel="nNW")))
    assert satz["alle_waagrecht_grund"].endswith("(1 von 1 Kamera)."), satz
    drei = komposition.beurteile_kamerasatz(_satz(
        _block(neigung_grad=0.0, shift_mm=0.0), _block(kuerzel="nNW")))
    assert drei["alle_waagrecht_grund"].endswith("(1 von 2 Kameras)."), drei


def test_die_visbox_seite_beugt_bild_und_variante():
    seite = (WURZEL / "oberflaeche" / "seite.html").read_text(encoding="utf-8")
    assert "`${e.vermerkt} Bilder eingetragen`" not in seite
    assert 'e.vermerkt === 1 ? "Bild" : "Bilder"' in seite
    assert 'e.varianten_nicht_begonnen === 1 ? "Variante" : "Varianten"' in seite
