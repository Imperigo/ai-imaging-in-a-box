"""A0291 Runde 2 (M4 des Gegenlesens): Der Hinweis je Bauteil steht in der Satzliste des Ergebnisses.

Bis dahin stand er nur im Befund ``fenster`` der Kamera, also in einer Ablage-Datei. Gerade der
Fall, für den die Prüfung je Bauteil gebaut ist (das Band hält, ein Fenster ist übermalt), kam bei
keinem Menschen an: ``kosmo_szene._fenster_eintragen`` schrieb nur bei ``gehalten is False``.
"""
from __future__ import annotations

import fenster_paare
from aiimaging import fenster_bauteile, kosmo_szene, varianten

HINWEIS = (f"{fenster_bauteile.SATZ_BAUTEIL_UEBERMALT} (Hinweis, kein Urteil): 1 von 12 gemessenen "
           f"Glasbauteilen sehen im KI-Bild nicht mehr aus wie Glas — Bauteil 4 (oben links, Bildpunkte "
           f"x 30 bis 52, y 20 bis 48: wie die Wand daneben). Am Bild pruefen.")


def _urteil(kamera, fenster):
    return {"kamera": kamera, "score": 0.7, "bestanden": True, "geom_iou": 0.6,
            kosmo_szene.URTEIL_FENSTER: fenster}


def _eintrag(kamera, fenster):
    return {"kamera": kamera, "geometrie_urteil": _urteil(kamera, fenster)}


def test_gehalten_mit_uebermaltem_einzelfenster_gibt_einen_satz_mit_kamera():
    je_kamera = [_eintrag("sSE", {"anteil": 0.83, "gehalten": True, "schwelle": 0.5,
                                  "bauteil_hinweis": HINWEIS}),
                 _eintrag("nNW", {"anteil": 0.9, "gehalten": True, "schwelle": 0.5,
                                  "bauteil_hinweis": None})]
    hinweise = []
    kosmo_szene._fenster_eintragen(None, je_kamera, hinweise)
    kosmo_szene._fenster_eintragen(None, je_kamera, hinweise)
    assert len(hinweise) == 1, "ein Satz je Kamera, nicht doppelt, nichts ohne Fund"
    assert hinweise[0].startswith(f"{fenster_bauteile.SATZ_BAUTEIL_UEBERMALT}, Kamera 'sSE'")
    assert "Bauteil 4 (oben links" in hinweise[0] and "Hinweis, kein Urteil" in hinweise[0]
    assert chr(0x2013) not in hinweise[0]


def test_nicht_gehalten_behaelt_seinen_satz_und_bekommt_den_zweiten_dazu():
    """Der bestehende Satz bleibt Wort für Wort; der Hinweis je Bauteil steht danach."""
    nur_alt, beide = [], []
    alt = {"anteil": 0.12, "gehalten": False, "schwelle": 0.5}
    kosmo_szene._fenster_eintragen(None, [_eintrag("sSE", alt)], nur_alt)
    kosmo_szene._fenster_eintragen(None, [_eintrag("sSE", dict(alt, bauteil_hinweis=HINWEIS))], beide)
    assert len(nur_alt) == 1 and nur_alt[0].startswith(varianten.SATZ_FENSTER_NICHT_GEHALTEN)
    assert beide[0] == nur_alt[0] and len(beide) == 2
    assert beide[1].startswith(f"{fenster_bauteile.SATZ_BAUTEIL_UEBERMALT}, Kamera 'sSE'")


def test_ein_befund_ohne_das_feld_oder_mit_unsinn_darin_schweigt():
    hinweise = []
    kosmo_szene._fenster_eintragen(None, [
        _eintrag("a", {"anteil": 0.9, "gehalten": True, "schwelle": 0.5}),
        _eintrag("b", {"anteil": 0.9, "gehalten": True, "schwelle": 0.5, "bauteil_hinweis": ""}),
        _eintrag("c", {"anteil": 0.9, "gehalten": True, "schwelle": 0.5, "bauteil_hinweis": 7}),
        _eintrag("d", {"anteil": None, "gehalten": None, "grund": "Zu wenig Glas"})], hinweise)
    assert hinweise == []


def test_der_hinweis_steht_im_ergebnis_und_bestanden_bleibt():
    """Von ``kosmo_szene`` bis ``ergebnis.hinweise`` — und ``passed`` ist mit und ohne gleich."""
    def ergebnis(fenster):
        return kosmo_szene.als_ergebnis("vis-1-abcdef", ["s.png"],
                                        geometrie_urteil=_urteil("sSE", fenster),
                                        je_kamera=[_eintrag("sSE", fenster)])
    ohne = ergebnis({"anteil": 0.83, "gehalten": True, "schwelle": 0.5})
    mit = ergebnis({"anteil": 0.83, "gehalten": True, "schwelle": 0.5, "bauteil_hinweis": HINWEIS})
    satz = [h for h in mit["hinweise"] if h.startswith(fenster_bauteile.SATZ_BAUTEIL_UEBERMALT)]
    assert len(satz) == 1 and "Kamera 'sSE'" in satz[0]
    assert satz[0] in mit["qa"]["verdict"]["hinweise"]
    assert not [h for h in ohne["hinweise"] if fenster_bauteile.SATZ_BAUTEIL_UEBERMALT in h]
    assert mit["qa"]["verdict"]["passed"] is ohne["qa"]["verdict"]["passed"] is True
    assert mit["qa"]["verdict"]["reason"] == ohne["qa"]["verdict"]["reason"]
    assert [h for h in mit["hinweise"] if h not in satz] == list(ohne["hinweise"])


def test_vom_bildpaar_bis_ins_ergebnis():
    """Der ganze Weg: ein Paar des Eichsatzes mit einem übermalten Fenster, das Band hält."""
    paar = fenster_paare._paar(1, 0, "fassade", 1)
    fenster = varianten.fenster_gehalten(
        paar["ki"], paar["grund"], paar["kennung"], varianten.glasfarben(paar["tabelle"]),
        ausser=varianten.nicht_fassade_farben(paar["tabelle"]), breite=paar["breite"])
    assert fenster["gehalten"] is True and fenster["bauteil_hinweis"]
    aus = kosmo_szene.als_ergebnis("vis-1-abcdef", ["s.png"], geometrie_urteil=_urteil("sSE", fenster),
                                   je_kamera=[_eintrag("sSE", fenster)])
    satz = [h for h in aus["hinweise"] if h.startswith(fenster_bauteile.SATZ_BAUTEIL_UEBERMALT)]
    assert len(satz) == 1 and "Kamera 'sSE'" in satz[0] and "Bildpunkte x" in satz[0]
    assert not [h for h in aus["hinweise"] if h.startswith(varianten.SATZ_FENSTER_NICHT_GEHALTEN)]
