"""Einstellbar ist ein Versprechen, das man an der NAHT prüft — nicht am Modul.

**Der Anlass sind zwei Fehler desselben Tages** (23.08.2026). Die Brennweite war im Kern
längst ein Parameter und kam an der Aussenkante trotzdem nicht durch: zwei fest verdrahtete
`28.0` standen im Weg, eine davon in einem Test. Der Geländestand dasselbe. Beide Male
hiess es «einstellbar», und beide Male stimmte das im Modul und nicht im Betrieb.

Diese Datei prüft die Umkehrung: **Jedes Feld, das aus der Bestellung gelesen wird, steht
in genau einer der beiden Listen** — es kommt an, oder es bleibt stehen und der Grund
steht dabei. Ein neues Feld im fremden Vertrag kann damit nicht mehr stillschweigend ins
Leere laufen.

Die Prüfung ist bewusst **nicht** «alles kommt an». Fünf Felder tun es heute nicht, und
das ist ein Befund und kein Fehler dieser Datei — er gehört gemeldet, nicht wegdefiniert.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, kosmo_szene
from aiimaging.kosmo_szene import DURCHGEREICHT, STEHENGEBLIEBEN, SzenenError

BESTELLUNG = {"geometry": {"path": "/irgendwo/bau.glb", "format": "glb"}}


def _szene(**fremd):
    return kosmo_szene.lies_szene({**BESTELLUNG, **fremd})


# --------------------------------------------------------------------------------------
# 1 · Die Tabelle ist vollständig — das ist der eigentliche Wächter
# --------------------------------------------------------------------------------------

def test_jedes_gelesene_feld_steht_in_genau_einer_der_beiden_listen():
    """**Der Test, um dessentwillen es die Tabelle gibt.**

    Wer dem fremden Vertrag ein Feld hinzufügt und es in `lies_szene` ausliest, muss hier
    Farbe bekennen: Kommt es an, oder bleibt es stehen? Ohne diesen Test ist die dritte
    Möglichkeit die bequemste — es steht nirgends und läuft ins Leere.
    """
    gelesen = set(_szene())
    erklaert = set(DURCHGEREICHT) | set(STEHENGEBLIEBEN)

    assert gelesen - erklaert == set(), (
        "Diese Felder liest `lies_szene`, und niemand sagt, wohin sie gehen")
    assert erklaert - gelesen == set(), (
        "Diese Felder stehen in der Tabelle und werden gar nicht mehr gelesen — "
        "eine Tabelle, die Felder behauptet, die es nicht gibt, macht die Lücke "
        "unauffindbar")


def test_kein_feld_steht_in_beiden_listen():
    """«Kommt an» und «bleibt stehen» zugleich ist keine Auskunft, sondern zwei."""
    assert set(DURCHGEREICHT) & set(STEHENGEBLIEBEN) == set()


@pytest.mark.parametrize("feld", sorted(STEHENGEBLIEBEN))
def test_jeder_stehengebliebene_eintrag_sagt_auch_was_fehlt(feld):
    """Ein «wird nicht unterstützt» ohne den nächsten Schritt ist eine Sackgasse.

    Mit ihm ist es eine Aufgabe. Der Unterschied kostet zwei Sätze und entscheidet, ob
    jemand die Lücke je schliesst.
    """
    eintrag = STEHENGEBLIEBEN[feld]
    assert set(eintrag) == {"neutral", "grund", "noetig"}
    assert len(eintrag["grund"]) > 40, "ein Halbsatz erklärt nichts"
    assert len(eintrag["noetig"]) > 30, "was fehlt, gehört benannt"


# --------------------------------------------------------------------------------------
# 2 · Gemeldet wird nur, was wirklich bestellt wurde
# --------------------------------------------------------------------------------------

def test_eine_leere_bestellung_meldet_nichts():
    """**Sonst wäre es die nächste Dauerwarnung.**

    Am selben Tag gemessen: Ohne Geländestand trug jede von zwölf Kameras dieselben zwei
    Warnungen. Eine Warnung, die immer erscheint, ist kein Signal mehr — es ist dasselbe
    Versagen wie ein Wächter, der nie greift, nur von der anderen Seite.
    """
    assert kosmo_szene.stehengebliebene_felder(_szene()) == ()


def test_ein_gesetzter_sonnenstand_wird_gemeldet():
    """Der gefährlichste der fünf: Das Bild sieht danach richtig aus.

    Die Sonne steht im Blender-Runner fest auf 50°/35°. Wer einen Abendstand bestellt,
    bekommt ein sauberes, gut belichtetes, **falsches** Bild — und nichts daran sieht nach
    einem Fehler aus.
    """
    offen = kosmo_szene.stehengebliebene_felder(
        _szene(render={"sun": {"elevation": 8, "azimuth": 250}}))

    assert [e["feld"] for e in offen] == ["sonne"]
    assert offen[0]["wert"] == {"elevation": 8, "azimuth": 250}


def test_ein_abbestellter_auftrag_laeuft_trotzdem_und_sagt_es_wenigstens():
    """`skip: true` wird gelesen und nicht beachtet.

    Das ist die unangenehmste der fünf: Wer etwas ABBESTELLT, bekommt es geliefert. Bis
    entschieden ist, was Überspringen bedeuten soll, ist die Meldung das Mindeste — sie
    ist ausdrücklich **kein Ersatz** für die Umsetzung.
    """
    offen = kosmo_szene.stehengebliebene_felder(_szene(vis={"skip": True}))

    assert [e["feld"] for e in offen] == ["ueberspringen"]


def test_mehrere_zugleich_kommen_alle_und_in_der_reihenfolge_der_tabelle():
    offen = kosmo_szene.stehengebliebene_felder(
        _szene(render={"sun": {"elevation": 8}}, vis={"skip": True, "upscale": True},
               style={"mode": "referenz"}))
    felder = [e["feld"] for e in offen]

    assert felder == [f for f in STEHENGEBLIEBEN if f in felder]
    assert set(felder) == {"sonne", "hochskalieren", "ueberspringen", "stil_modus"}


def test_ein_stil_modus_none_ist_keine_bestellung():
    """Der einzige der fünf, dessen neutraler Wert kein `False` und kein `None` ist.

    Ohne den Tabelleneintrag `neutral` wäre `"none"` ein gesetzter Wert — und jede
    Bestellung ohne Stil trüge eine Meldung.
    """
    assert _szene()["stil_modus"] == "none"
    assert kosmo_szene.stehengebliebene_felder(_szene(style={"mode": "none"})) == ()


def test_keine_szene_kein_urteil():
    with pytest.raises(SzenenError, match="kein Wörterbuch"):
        kosmo_szene.stehengebliebene_felder(["sonne"])


# --------------------------------------------------------------------------------------
# 3 · Und es erreicht den Menschen am Terminal
# --------------------------------------------------------------------------------------
#
# Eine Tabelle, die niemand sieht, ist die naechste tote Kante. Dieses Projekt hat diese
# Fehlerart am 23.08.2026 dreimal an einem Tag gefunden.

def test_der_kurzbefund_nennt_was_bestellt_und_nicht_ausgefuehrt_wurde():
    befund = {"kameras": [], "stehengeblieben": [
        {"feld": "sonne", "wert": {"elevation": 8},
         "grund": "Die Sonne steht im Runner fest.", "noetig": "…"}]}

    zeilen = abholer.befund_kurz(befund)

    treffer = [z for z in zeilen if "BESTELLT UND NICHT AUSGEFUEHRT" in z]
    assert len(treffer) == 1
    assert "sonne" in treffer[0]
    assert "Die Sonne steht im Runner fest." in treffer[0], (
        "der Grund gehoert in dieselbe Zeile — wer nur den Feldnamen liest, "
        "haelt es fuer einen Tippfehler")


def test_gegenprobe_ohne_offene_bestellung_steht_die_zeile_nicht_da():
    assert not [z for z in abholer.befund_kurz({"kameras": []})
                if "BESTELLT UND NICHT AUSGEFUEHRT" in z]
