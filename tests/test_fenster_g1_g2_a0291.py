"""A0291 Teil (a), Nachbau: die Fälle G1 und G2 des dritten Gegenlesens (Steuerung 11.11.2026, 18:15 UTC).

* **G1** Spiegelung eines Hauses in EINEM (bis drei) von zwölf Fenstern, alle anderen mit
  Glaston, nichts übermalt: kein Vorwurf. Die Regel «Spiegelung ohne Glaston» griff bis dahin nur,
  wenn die Mehrheit der Scheiben spiegelt; jetzt greift sie je Scheibe, wenn die Scheibe
  gleichmässig farblos bis warm ist und ihr Rahmen erhalten ist.
* **G2** Ein breiter Steg aus Wand teilt jedes Fenster in Scheiben von 8 Bildpunkten Breite; mit
  waagrechtem Versatz 4 hiess eine Scheibe «wie die Wand daneben». Ein Glasstück, höchstens
  zweimal so breit wie der Versatz (2 x 4), trägt diesen Vorwurf nicht mehr.

Beides nimmt nur zurück («uebermalt» wird «nicht messbar»), nie umgekehrt. Am Kopf eaa819301
waren 29 der 55 Proben rot: G1 an jeder Wand mit Fund, G2 an Anthrazit und Dunkelholz, die Gegenproben
dort, wo die spiegelnde Nachbarscheibe einen Fehlalarm gab. Die Szene baut ``tests/fenster_paare4.py``
nach den Massen der Meldung des Gegenlesens nach.
"""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import fenster_paare4  # noqa: E402
from aiimaging import fenster_bauteile  # noqa: E402

P = fenster_paare4
_SZENE: dict = {}


@pytest.fixture(scope="module")
def szene():
    """Alle Paare der Szene einmal (auf vier Kernen unter einer Minute)."""
    if "m" not in _SZENE:
        _SZENE["m"] = P.miss()
    return _SZENE["m"]


def _ergebnis(szene, **f):
    return szene["ergebnisse"][P.name_von(P.fall(**f))]


def _vorwuerfe(e: dict) -> list:
    return [b for b in e["bauteile"] or () if b["urteil"] == fenster_bauteile.UEBERMALT]


# --- G1 · ein Fenster spiegelt ein Haus gegenüber --------------------------------------------

@pytest.mark.parametrize("wand", [P.ANTHRAZIT, P.KLINKER, P.DUNKELGRUEN, P.DUNKELHOLZ])
def test_g1_minimalfall_eine_spiegelnde_scheibe_ist_kein_vorwurf(szene, wand):
    e = _ergebnis(szene, gruppe="g1", wand=wand, spiegelt=(1,))
    assert _vorwuerfe(e) == [], [(b["art"], b["ort"]) for b in _vorwuerfe(e)]
    assert e["hinweis"] is None
    scheibe = next(b for b in e["bauteile"] if b["ort"]["x0"] == 82 and b["ort"]["y0"] == 50)
    assert scheibe["urteil"] == fenster_bauteile.NICHT_MESSBAR
    assert scheibe["grund"] == fenster_bauteile.GRUND_SPIEGELUNG_EINZELN


@pytest.mark.parametrize("wand", range(len(P.WAENDE)))
@pytest.mark.parametrize("variante", [{"spiegelt": (1, 3)}, {"spiegelt": (4, 7, 10)},
                                      {"spiegelt": (1,), "versatz": (2, 1)},
                                      {"spiegelt": (1,), "spiegel_stil": "spieg_oben"}])
def test_g1_zwei_drei_scheiben_und_versatz_ohne_vorwurf(szene, wand, variante):
    e = _ergebnis(szene, gruppe="g1", wand=wand, **variante)
    assert _vorwuerfe(e) == [], [(b["art"], b["ort"]) for b in _vorwuerfe(e)]


def test_g1_im_band_ohne_rahmen_ist_eine_benannte_grenze(szene):
    """Ohne eigenen Rahmen trennt nichts die Spiegelung vom Anstrich; dort bleibt das Urteil.

    Gezählt, nicht verschwiegen: Die Probe hält fest, wie viele Band-Fälle es heute sind, damit
    eine Änderung auffällt (in beide Richtungen).
    """
    assert len(szene["grenze"]) == 4, szene["grenze"]
    assert all("/band/" in n for n in szene["grenze"])


# --- G2 · breiter Steg aus Wand, schmale Scheiben, Versatz 4 ---------------------------------

@pytest.mark.parametrize("wand", range(len(P.WAENDE)))
@pytest.mark.parametrize("versatz", [(-4, 0), (4, 0)])
def test_g2_schmale_scheibe_mit_versatz_ist_nicht_wie_die_wand(szene, wand, versatz):
    e = _ergebnis(szene, gruppe="g2", wand=wand, steg=6, versatz=versatz)
    assert _vorwuerfe(e) == [], [(b["art"], b["ort"]) for b in _vorwuerfe(e)]


def test_g2_schmales_glasstueck_traegt_nur_noch_nicht_messbar():
    """Am Modul selbst: Ein Glasstück von 8 Bildpunkten Breite (2 x 4) gehört zu den schmalen."""
    assert fenster_bauteile.SCHMAL_VERSATZ == 4
    assert "{versatz}" in fenster_bauteile.GRUND_SCHMAL


# --- die Szene im Ganzen: kein Fehlalarm, die Erkennung bleibt --------------------------------

def test_szene_ohne_fehlalarm_und_erkennung_bleibt(szene):
    assert szene["fehlalarme"] == 0, szene["falsch"]
    ok = szene["gruppen"]["ok"]
    assert ok["erkannt"] == ok["uebermalt"] == 54, ok


@pytest.mark.parametrize("wand", range(len(P.WAENDE)))
@pytest.mark.parametrize("art", ["grau", "warm"])
def test_uebermalt_samt_rahmen_neben_spiegelung_bleibt_ein_fund(szene, wand, art):
    """Gegenprobe zu G1: Ein Anstrich nimmt den Rahmen mit und bleibt «uebermalt», auch neben einer Spiegelung."""
    k = ("grau", "fassade", "warm").index(art)
    ziel = (2 + 5 * k + wand) % 12
    e = _ergebnis(szene, gruppe="ok", klasse="einzeln", wand=wand, art=art, uebermalt=(ziel,),
                  spiegelt=((ziel + 1) % 12,))
    assert e["wert"]["erkannt"], [(b["urteil"], b.get("grund")) for b in e["bauteile"]][:4]
    assert e["wert"]["fehlalarme"] == 0
