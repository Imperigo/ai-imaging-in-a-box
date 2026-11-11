"""A0291 Teil (a): die vorsichtige Ausgabe der Fensterprüfung je Bauteil (Steuerung 11.11.2026, 16:30 UTC).

Das zweite Gegenlesen fand an einer Szene, die der Bau nicht kannte, Fehlalarme und stille
Fehlurteile (Mängel M5 bis M8). Teil (a) baut keine bessere Erkennung, sondern eine vorsichtige
Ausgabe: Wo die Prüfung nicht sicher ist, heisst das Bauteil «nicht messbar» mit Grund, nie
«uebermalt», und ein verändertes Fenster bleibt nicht still «gehalten».

* M5 Spiegelung eines Nachbarhauses gilt nicht als Übermalung.
* M6 Sprossenfenster (auch mit Versatz) werfen nichts vor.
* M7 ein graues Fenster zwischen hellen, fast farblosen Scheiben heisst «nicht messbar», nicht still.
* M8 nur der untere Teil übermalt heisst «nicht messbar», nicht still.

Jede dieser Proben war am Kopf 281fb450f rot. Die Szene baut ``tests/fenster_paare3.py`` nach
den Massen der Meldung des Gegenlesens nach.
"""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import fenster_paare2  # noqa: E402
import fenster_paare3  # noqa: E402
from aiimaging import fenster_bauteile, varianten  # noqa: E402

ANTHRAZIT, DUNKELGRUEN, ROTHOLZ, BLECH, HELLGRAU, OCKER = 2, 3, 4, 5, 0, 6


def _fall(**f) -> dict:
    return dict({"gruppe": "probe", "klasse": "gegenfall", "anordnung": "einzel"}, **f)


def _pruefe(f: dict) -> dict:
    return fenster_paare3.pruefe(f)


def _vorwuerfe(e: dict) -> list:
    return [b for b in e["bauteile"] or () if b["urteil"] == fenster_bauteile.UEBERMALT]


@pytest.fixture(scope="module")
def szene():
    """Alle Paare der Szene des Gegenlesens einmal (auf vier Kernen rund eine Minute)."""
    return fenster_paare3.miss()


# --- M5 · Spiegelung eines Nachbarhauses -------------------------------------------------------

@pytest.mark.parametrize("wand", [ANTHRAZIT, DUNKELGRUEN, BLECH])
def test_m5_ein_haus_gegenueber_im_glas_ist_kein_vorwurf(wand):
    e = _pruefe(_fall(wand=wand, stile="spiegelung-haus"))
    assert _vorwuerfe(e) == [], [(b["art"], b["ort"]) for b in _vorwuerfe(e)][:3]
    assert e["hinweis"] is None


@pytest.mark.parametrize("wand", [ANTHRAZIT, BLECH])
def test_m5_auch_im_band_kein_vorwurf(wand):
    e = _pruefe(_fall(wand=wand, anordnung="band", stile="spiegelung-haus"))
    assert _vorwuerfe(e) == []


@pytest.mark.parametrize("wand", [ANTHRAZIT, DUNKELGRUEN, ROTHOLZ, OCKER])
def test_m5_spiegelung_unten_in_sprossenfenstern_kein_vorwurf(wand):
    e = _pruefe(_fall(wand=wand, sprossen=True, stile="sprossen-mix"))
    assert _vorwuerfe(e) == []


def test_m5_der_grund_steht_beim_bauteil():
    e = _pruefe(_fall(wand=ANTHRAZIT, stile="spiegelung-haus"))
    gruende = {b.get("grund") for b in e["bauteile"] if b["urteil"] == fenster_bauteile.NICHT_MESSBAR}
    assert fenster_bauteile.GRUND_SPIEGELUNG in gruende


# --- M6 · Sprossenfenster ------------------------------------------------------------------------

@pytest.mark.parametrize("versatz", [None, (-4, 1), (-4, -1), (3, 2), (2, 0)])
@pytest.mark.parametrize("wand", [ANTHRAZIT, DUNKELGRUEN, BLECH])
def test_m6_sprossenfenster_werfen_nichts_vor(wand, versatz):
    mehr = {"aenderung_schritte": (("versatz",) + versatz,), "aenderung": str(versatz)} if versatz else {}
    e = _pruefe(_fall(wand=wand, sprossen=True, **mehr))
    assert _vorwuerfe(e) == [], [(b["art"], b["ort"]) for b in _vorwuerfe(e)][:3]


def test_m6_die_scheiben_sind_als_sprossen_erkannt():
    e = _pruefe(_fall(wand=ANTHRAZIT, sprossen=True))
    scheiben = [b for b in e["bauteile"] if not b["feld"]]
    assert len(scheiben) == 4 * 21
    assert all(b.get("sprossen") for b in scheiben)


def test_m6_uebermalt_im_sprossenfenster_heisst_nicht_messbar_nicht_still():
    f = _fall(wand=ANTHRAZIT, sprossen=True, art="warm", uebermalt=(9,), klasse="einzeln")
    e = _pruefe(f)
    assert _vorwuerfe(e) == []
    assert e["wert"]["nicht_messbar"] is True
    ziel = e["ziele"][0]
    im_ziel = [b for b in e["bauteile"] if b["ort"]["x0"] >= ziel["x0"] - 2 and b["ort"]["x1"] <= ziel["x1"] + 2
               and b["ort"]["y0"] >= ziel["y0"] - 2 and b["ort"]["y1"] <= ziel["y1"] + 2]
    assert im_ziel and all(b["grund"] == fenster_bauteile.GRUND_SPROSSEN for b in im_ziel)


def test_m6_sprossen_nur_wo_der_rahmen_trennt_nicht_die_wand():
    """Zwei Glasstücke mit Rahmen dazwischen sind Scheiben; mit Wand dazwischen zwei Fenster."""
    breite = 30
    glas, rahmen, wand = (10, 200, 30), (10, 30, 200), (200, 10, 10)
    links = {y: sum(1 << x for x in range(2, 12)) for y in range(2, 14)}
    rechts = {y: sum(1 << x for x in range(14, 24)) for y in range(2, 14)}
    for steg, erwartet in ((rahmen, {0, 1}), (wand, set())):
        kennung = [wand] * (breite * 16)
        for y in range(2, 14):
            for x in range(2, 24):
                kennung[y * breite + x] = glas if not 12 <= x <= 13 else steg
        assert fenster_bauteile.sprossen_scheiben([links, rechts], kennung, breite, wand) == erwartet


# --- M7 · grau zwischen hellen Scheiben -----------------------------------------------------------

@pytest.mark.parametrize("anordnung", ["einzel", "band"])
@pytest.mark.parametrize("wand", [HELLGRAU, OCKER])
def test_m7_grau_zwischen_hellen_scheiben_ist_nie_still(wand, anordnung):
    e = _pruefe(_fall(wand=wand, anordnung=anordnung, stile="hell", art="grau", uebermalt=(9,),
                      klasse="einzeln"))
    assert e["wert"]["erkannt"] or e["wert"]["nicht_messbar"], "still gehalten"
    assert e["wert"]["fehlalarme"] == 0


@pytest.mark.parametrize("wand", [HELLGRAU, OCKER])
def test_m7_helle_scheiben_ohne_uebermalung_bleiben_ohne_vorwurf(wand):
    assert _vorwuerfe(_pruefe(_fall(wand=wand, stile="hell"))) == []


# --- M8 · nur der untere Teil übermalt -----------------------------------------------------------

@pytest.mark.parametrize("art", ["grau", "warm"])
@pytest.mark.parametrize("anordnung", ["einzel", "band"])
@pytest.mark.parametrize("wand", [HELLGRAU, ANTHRAZIT, OCKER])
def test_m8_nur_unten_uebermalt_ist_nie_still(wand, anordnung, art):
    e = _pruefe(_fall(wand=wand, anordnung=anordnung, art=art, teil="unten", uebermalt=(8,), klasse="teil"))
    assert not e["wert"]["still"], "still gehalten"
    assert e["wert"]["fehlalarme"] == 0


def test_m8_der_grund_nennt_den_teil():
    e = _pruefe(_fall(wand=HELLGRAU, art="warm", teil="unten", uebermalt=(8,), klasse="teil"))
    gruende = " ".join(b.get("grund", "") for b in e["bauteile"])
    assert "untere Teil" in gruende or e["wert"]["erkannt"]


# --- Zielwert (a) an der ganzen Szene und am Bau-Satz der Runde 2 --------------------------------

def test_null_fehlalarme_an_der_szene_des_gegenlesens(szene):
    assert szene["paare"] >= 700
    assert szene["fehlalarme"] == 0, szene["falsch"][:20]


@pytest.mark.parametrize("gruppe", ["m6", "m7", "m8"])
def test_kein_veraendertes_fenster_der_maengel_bleibt_still(szene, gruppe):
    assert szene["gruppen"][gruppe]["still"] == 0, [n for n in szene["still"] if n.startswith(gruppe)]


def test_auch_der_zufallssatz_ohne_fehlalarm(szene):
    assert szene["gruppen"]["z"]["paare"] == fenster_paare3.ZUFALL_PAARE
    assert szene["gruppen"]["z"]["fehlalarme"] == 0


def test_die_erkennung_der_runde_zwei_bleibt():
    """Einzeln 377 von 380 und benachbart 100 von 100, wie an 281fb450f; 0 Fehlalarme."""
    m = fenster_paare2.miss()
    assert m["fehlalarme"] == 0
    assert m["klassen"]["einzeln"]["erkannt"] >= 377
    assert m["klassen"]["benachbart"]["erkannt"] == m["klassen"]["benachbart"]["paare"] == 100


def test_ein_urteil_uebermalt_wird_nur_zurueckgenommen_nie_gesetzt():
    """Die vorsichtige Ausgabe setzt kein neues «uebermalt»: Ein Fenster, das sonst gehalten ist, bleibt es."""
    p = fenster_paare3.paar(_fall(wand=HELLGRAU))
    befund = varianten.fenster_gehalten(p["ki"], p["grund"], p["kennung"], varianten.glasfarben(p["tabelle"]),
                                        ausser=varianten.nicht_fassade_farben(p["tabelle"]), breite=p["breite"])
    assert befund["bauteil_uebermalt"] == []
    assert befund["bauteil_hinweis"] is None
