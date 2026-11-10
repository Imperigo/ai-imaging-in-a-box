"""A0291 Runde 2: die Zielfunktion der Steuerung vom 10.11.2026, 12:15 UTC, am Eichsatz der Runde 2.

Der Eichsatz (``tests/fenster_paare2.py``, 1045 Paare) baut die Paare des unabhängigen Gegenlesens
nach und legt Reihen quer über jede Schwelle der Prüfung. Verlangt ist:

* 0 Fehlalarme in allen Gegenfällen, auch bei dunklem Glas an dunkler Fassade; wo der Kontrast für
  ein Urteil nicht reicht, «nicht messbar» mit Grund, nie «uebermalt».
* einzeln übermalte Fenster zu mindestens 90 % der messbaren Fälle erkannt, auch mit Versatz bis
  vier Bildpunkte; zwei bis drei benachbarte zu mindestens 80 %.
* «nicht messbar» unter den übermalten Fällen höchstens 15 %.
* Das Urteil der Prüfung je Band bleibt Feld für Feld gleich.
"""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import fenster_paare2  # noqa: E402
from aiimaging import fenster_bauteile, varianten  # noqa: E402


@pytest.fixture(scope="module")
def messung():
    """Alle 1045 Paare einmal durch ``varianten.fenster_gehalten`` (auf vier Kernen rund eine Minute)."""
    return fenster_paare2.miss()


def test_der_satz_hat_mindestens_sechshundert_paare_und_jede_reihe(messung):
    assert messung["paare"] >= 600
    assert set(messung["gruppen"]) == {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                                       "s1", "s2", "s3", "s4", "s5"}
    assert messung["klassen"]["gegenfall"]["paare"] >= 400
    assert messung["klassen"]["einzeln"]["paare"] >= 300
    assert messung["klassen"]["benachbart"]["paare"] >= 80
    assert len({fenster_paare2.name_von(f) for f in fenster_paare2.faelle()}) == messung["paare"]


def test_der_erzeuger_ist_fest_gesaet():
    fall = fenster_paare2.faelle()[1]
    a, b = fenster_paare2.paar(fall), fenster_paare2.paar(fall)
    assert a["ki"] == b["ki"] and a["grund"] == b["grund"] and a["kennung"] == b["kennung"]


def test_null_fehlalarme_in_allen_paaren(messung):
    assert messung["fehlalarme"] == 0, messung["falsch"][:20]


@pytest.mark.parametrize("gruppe", ["a", "d", "e", "h", "s1"])
def test_kein_gegenfall_der_gruppe_meldet_etwas(messung, gruppe):
    assert messung["gruppen"][gruppe]["fehlalarme"] == 0


def test_einzeln_uebermalt_mindestens_neunzig_prozent_der_messbaren(messung):
    zeile = messung["klassen"]["einzeln"]
    assert zeile["rate"] >= 0.9, (zeile["erkannt"], zeile["paare"], zeile["verfehlt"][:20])


def test_benachbart_uebermalt_mindestens_achtzig_prozent(messung):
    zeile = messung["klassen"]["benachbart"]
    assert zeile["rate"] >= 0.8, (zeile["erkannt"], zeile["paare"], zeile["verfehlt"][:20])


def test_nicht_messbar_unter_den_uebermalten_hoechstens_fuenfzehn_prozent(messung):
    uebermalt = [messung["klassen"][k] for k in ("einzeln", "benachbart")]
    anteil = sum(z["nicht_messbar"] for z in uebermalt) / sum(z["paare"] for z in uebermalt)
    assert anteil <= 0.15, anteil


def test_versatz_bis_vier_bildpunkte_einzeln_mindestens_neunzig_prozent(messung):
    """Die Reihe s2: Versatz 0 bis 4 waagrecht und drei schräge, je Übermalungsart und Wand."""
    reihe = [e for e in messung["ergebnisse"].values() if e["gruppe"] == "s2" and e["klasse"] == "einzeln"]
    messbar = [e for e in reihe if not e["wert"]["nicht_messbar"]]
    assert len(reihe) >= 100
    assert sum(bool(e["wert"]["erkannt"]) for e in messbar) / len(messbar) >= 0.9


def test_dunkles_glas_quer_ueber_die_schwelle_ist_nie_uebermalt(messung):
    """Reihe s1: 25 Helligkeiten vor jeder Wand. Wo Glas und Wand nicht zu trennen sind, «nicht messbar»."""
    reihe = [e for e in messung["ergebnisse"].values() if e["gruppe"] == "s1"]
    assert len(reihe) == 125
    unklar = 0
    for e in reihe:
        assert not [b for b in e["bauteile"] if b["urteil"] == fenster_bauteile.UEBERMALT], e["name"]
        for b in e["bauteile"]:
            if b["urteil"] == fenster_bauteile.NICHT_MESSBAR:
                unklar += 1
                assert b.get("grund"), e["name"]
    assert unklar, "die Reihe muss die Zone «nicht messbar» treffen, sonst liegt die Schwelle in einer Lücke"


def test_dunkles_glas_in_dunkler_holzschalung_der_minimalfall_des_gegenlesens(messung):
    """M1: Holz 96,74,56, alle Scheiben dunkel v 60 und 75, nichts übermalt — kein Fenster ist übermalt."""
    for v in (60, 75):
        for e in messung["ergebnisse"].values():
            if e["gruppe"] == "s1" and e["fall"]["wand"] == 4 and e["fall"]["stile"][1] == v:
                assert not [b for b in e["bauteile"] if b["urteil"] == fenster_bauteile.UEBERMALT]


def test_zwei_und_drei_benachbarte_graue_im_band_werden_gefunden(messung):
    """M2: Die grauen Felder dürfen sich nicht gegenseitig als Geschwister decken."""
    reihe = [e for e in messung["ergebnisse"].values()
             if e["klasse"] == "benachbart" and e["fall"]["anordnung"] == "band"
             and e["fall"]["art"] == "grau"]
    assert len(reihe) >= 15
    assert sum(bool(e["wert"]["erkannt"]) for e in reihe) / len(reihe) >= 0.8


def test_warm_mit_dichter_fuge_und_versatz_drei_und_vier(messung):
    """M3: Fuge jede siebte Spalte, Versatz 3 und 4 Bildpunkte."""
    reihe = [e for e in messung["ergebnisse"].values()
             if e["gruppe"] == "s2" and e["klasse"] == "einzeln" and e["fall"]["art"] == "warm"
             and e["fall"]["aenderung"] in ("versatz-3-0", "versatz-4-0", "versatz-3-3", "versatz--4--2")]
    assert len(reihe) >= 15
    assert sum(bool(e["wert"]["erkannt"]) for e in reihe) / len(reihe) >= 0.9


def test_das_urteil_je_band_bleibt_feld_fuer_feld_gleich(monkeypatch):
    """Jedes dreissigste Paar mit und ohne die Prüfung je Bauteil: alle alten Felder gleich."""
    faelle = fenster_paare2.faelle()[::30]
    glas = varianten.glasfarben(fenster_paare2.TABELLE)
    ausser = varianten.nicht_fassade_farben(fenster_paare2.TABELLE)
    paare = [fenster_paare2.paar(f) for f in faelle]
    mit = [varianten.fenster_gehalten(p["ki"], p["grund"], p["kennung"], glas, ausser=ausser,
                                      breite=p["breite"]) for p in paare]

    def kaputt(*a, **k):
        raise RuntimeError("abgeschaltet")
    monkeypatch.setattr(fenster_bauteile, "pruefe_indizes", kaputt)
    neu = {"bauteile", "bauteil_uebermalt", "bauteil_hinweis", "methode_bauteile", "bauteil_grund"}
    for p, befund in zip(paare, mit):
        ohne = varianten.fenster_gehalten(p["ki"], p["grund"], p["kennung"], glas, ausser=ausser,
                                          breite=p["breite"])
        assert {k: v for k, v in ohne.items() if k not in neu} == \
            {k: v for k, v in befund.items() if k not in neu}, p["name"]
